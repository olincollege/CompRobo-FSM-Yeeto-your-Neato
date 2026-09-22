"""
Contains and runs the FiniteStateController Node.
"""

import time
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from neato2_interfaces.msg import Bump
from sensor_msgs.msg import LaserScan

class FiniteStateController(Node):
    """
    Control the velocity of a Neato based on LiDAR and bump sensor inputs.
    Make it run into the closest free-standing object to it,
    if none are detected by the LiDAR follow the nearest wall,
    if there is an object that the Neato will run into make it turn away,
    if the Neato runs into something make it stop moving.

    Attributes:
        ideal_closeness (int, 1/m): The ideal closeness value used in the
        PD loop for wall_follow.
        error_to_velocity (float, rad*m/s): rotational velocity divided
        by error, used in the PD loop for wall_follow.
        de_dt_to_velocity (float, rad*m): rotational velocity divided by the
        time derivative of error, used in the PD loop for wall_follow.
        e_stop (boolean): Has the bump sensor been triggered?
        timer_period (float, s): The amount of time between iterations of
        the loop.
        publisher (Publisher): Controls the Neato's velocity.
        sub_bump (Subscription): Takes in information from
        the Neato's bump sensor.
        sub_scan (Subscription): Takes in information from
        the Neato's LiDAR scanner.
        time_started (float, s): The time the Neato started the last
        line or angle while driving in a square (not used in the FSM).
        what_doin (int): The step of the process of driving in a square
        the Neato is on, 0 for first side, 1 for first corner, 2 for
        second side, 3 for second corner, etc. (not used in the FSM)
        move_time ((int, float), (s, s)): The time spent driving in
        a line and rotating respectively while driving in a square
        (not used in the FSM)
        twist_direction ((Twist, Twist), (m, rad)): The velocities
        for driving in a straight line and turning respectively
        for driving in a square (not used in the FSM).
        possible_person ([(int, float), ...], [(deg, m), ...]):
        all the places there could be a free-standing object,
        the angle from the Neato to it and the distance between
        them respectively.
        laser_eyes ([float, ...], [m, ...]): The distance data from the
        Neato's LiDAR, each index ([0, 360]) is an angle in degrees.
        laser_mad (boolean): Is there something in front that is closer
        than 0.5 meters?
        last_error (float, 1/m): The error value calculated in the previous
        frame while wall following, or None.
        last_time (float, s): The time the last frame ran, used for tuning
        timer period.

        All other attributes are inherited from Node
    """
    def __init__(self):
        """
        Initialize all instance attributes, start the timer,
        and initialize the publisher and subscribers.
        """
        self.ideal_closeness = 90
        self.error_to_velocity = 0.02
        self.de_dt_to_velocity = 0.1
        self.e_stop = False
        self.laser_mad = False
        super().__init__("finite_state_controller")
        self.timer_period = .01
        self.timer = self.create_timer(self.timer_period, self.run_loop)
        self.publisher = self.create_publisher(Twist,'cmd_vel', 10)
        self.sub_bump = self.create_subscription(
            Bump, "bump", self.process_bump, 10)
        self.sub_scan = self.create_subscription(
            LaserScan, "scan", self.process_scan, 10)
        self.time_started = time.time()
        self.what_doin = 0
        self.move_time = (4, 1.57)
        self.twist_direction = (Twist(), Twist())
        self.twist_direction[0].linear.x = .25
        self.twist_direction[1].angular.z = 1.0
        self.possible_person = []
        self.laser_eyes = None
        self.laser_mad = False
        self.last_error = None
        self.last_time = time.time()

    def process_bump(self, msg):
        """
        Take in the bump sensor data and update e_stop.

        Args:
            msg (Bump): The bump sensor data from the Neato.
        """
        self.e_stop = (
            msg.left_front or
            msg.left_side or
            msg.right_front or
            msg.right_side
        )
        print("e_stop:", self.e_stop)

    def process_scan(self, msg):
        """
        Take in the LiDar data and update laser_eyes, laser_mad,
        and possible person.

        Args:
            msg (LaserScan): The LiDAR data from the Neato.
        """
        # Update laser_eyes to match the distance readings from the scan.
        self.laser_eyes = msg.ranges

        # Update laser_mad by checking if there is anything closer than
        # 0.5 meters in the front quarter of the Neato's LiDAR scan.
        neato_eyes = self.laser_eyes[-45:-1] + self.laser_eyes[0:45]
        if any(distance<0.5 for distance in neato_eyes):
            self.laser_mad = True
        else:
            self.laser_mad = False
        print("laser_mad:", self.laser_mad)

        # Update possible_person
        self.possible_person = []
        # Look at each pair of adjacent LiDAR readings:
        for i in range(360):
            # If their distance differs by more than a meter they could
            # be a free-standing object.
            if abs(self.laser_eyes[i]-self.laser_eyes[i+1]) > 1:
                # Append the closer of the two distances to
                # possible_person if it is closer than 4 meters.
                if(self.laser_eyes[i] < self.laser_eyes[i+1]
                     and self.laser_eyes[i] < 4):
                    self.possible_person.append((i, self.laser_eyes[i]))
                elif self.laser_eyes[i+1] < 4:
                    self.possible_person.append((i+1, self.laser_eyes[i+1]))
        print(self.possible_person)


    def avoid_collision(self):
        """
        If there is something in front of the Neato that is closer
        than 0.5 meters, turn to the left.
        """
        twist_msg = Twist()
        twist_msg.angular.z = .2
        self.publisher.publish(twist_msg)

    def run_loop(self):
        """
        Make the Neato run into the closest free-standing object to it,
        if none are detected by the LiDAR, follow the nearest wall,
        if there is an object that the Neato will run into, make it turn away,
        if the Neato runs into something, make it stop moving.
        """
        # Make sure the timer period is long enough
        if self.last_time + self.timer_period > time.time():
            print("self.timer_period is too long!")
            self.last_time = time.time()

        # Check for and run the current state
        if self.e_stop:
            print("stopping due to bump")
            twist_msg = Twist()
            self.publisher.publish(twist_msg)
            self.last_error = None
        elif len(self.possible_person) > 0:
            self.person_follow()
            self.last_error = None
        elif self.laser_mad:
            print("avoiding collision")
            self.avoid_collision()
            self.last_error = None
        else:
            print("wall following")
            self.wall_follow()

    def forward(self):
        """
        Make the Neato drive forward.
        """
        twist_msg = Twist()
        twist_msg.linear.x = .4
        self.publisher.publish(twist_msg)

    def square(self):
        """
        Make the Neato drive in a square.
        """
        # Calculate the time since the Neato started the current action.
        elapsed_time = time.time() - self.time_started

        # If what_doin is even, drive straight, if it's odd, rotate.
        i = self.what_doin % 2
        if elapsed_time >= self.move_time[i]:
            self.what_doin += 1
            self.time_started = time.time()
        else:
            self.publisher.publish(self.twist_direction[i])

    def person_follow(self):
        """
        Uses stored list of "possible person" points to determine a point to 
        follow, then move towards that point in an arc.
        """
        # Sort "possible person" list by distance
        # to get the closest point in the list
        self.possible_person.sort(key = lambda element: element[1])
        theta = self.possible_person[0][0]
        theta_rad = (theta if theta<180 else theta-360) * math.pi / 180
        distance = self.possible_person[0][1]

        # Use angle and distance to point to calculate ideal angular velocity
        arc_length = (distance * theta_rad) / math.sin(theta_rad/2)
        drive_time = arc_length / 0.1
        angular_vel = 2 * theta_rad / drive_time
        angular_vel = max(angular_vel, -1.0)
        angular_vel = min(angular_vel, 1.0)
        print(self.possible_person[0][0], distance, arc_length, angular_vel)

        # Send a message to cmd_vel using calculated angular velocity
        twist_msg = Twist()
        twist_msg.linear.x = 0.1
        twist_msg.angular.z = angular_vel
        self.publisher.publish(twist_msg)

    def wall_follow(self):
        """
        Make the Neato balance driving toward the nearest wall
        in front of it and keeping a safe distance from it.
        """
        # If no laser scan has been taken, go forward.
        if self.laser_eyes is None:
            self.forward()
            return

        # Take in the laser range data from the left and right
        # side of the front three quarters of the Neato.
        left_laser = self.laser_eyes[1:91]
        right_laser = self.laser_eyes[270:360]

        # Make a weighted sum of all ranges on each side
        # that scales with how close the ranges are
        # by summing the reciprocals of the distances.
        closeness = (sum([1 / dist for dist in left_laser]),
            sum([1 / dist for dist in right_laser]))
            # closeness = (left, right)

        # Choose which side has the closest wall.
        closeness_index = int(closeness[0] - closeness[1] < 0)

        # Find the error from the ideal closeness
        print(f"closeness = {closeness[closeness_index]}")
        error = closeness[closeness_index] - self.ideal_closeness
        print(f"{error = }")

        # Turn based on that error and the previous error
        wall_side_sign = closeness_index * 2 - 1
        angular_vel = error * self.error_to_velocity * wall_side_sign
        if self.last_error is not None:
            # Calculate how much the rate of change of error
            # should effect the angular velocity
            delta_error = error - self.last_error
            de_dt = self.timer_period * delta_error
            angular_vel += de_dt * self.de_dt_to_velocity

        # Clamp the angular velocity so it doesn't exceed its maximum.
        print(f"Unclamped angular velocity = {angular_vel}")
        angular_vel = max(angular_vel, -1.0)
        angular_vel = min(angular_vel, 1.0)
        print(f"Clamped angular velocity = {angular_vel}")

        # Set the Neato's velocity based on the constant
        # linear velocity and the calculated angular velocity.
        twist_msg = Twist()
        twist_msg.linear.x = 0.15
        twist_msg.angular.z = angular_vel
        self.publisher.publish(twist_msg)

        # Set last_error
        self.last_error = error


def main(args = None):
    """
    Run the FiniteStateController Node.

    Args:
        args: anything that could be passed to a generic
        Node's initializer.
    """
    rclpy.init(args=args)
    node = FiniteStateController()
    rclpy.spin(node)
    rclpy.shutdown()


# Run main() if this file is run.
if __name__ == '__main__':
    main()
