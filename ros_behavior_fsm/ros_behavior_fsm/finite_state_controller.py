import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from neato2_interfaces.msg import Bump
import time
from sensor_msgs.msg import LaserScan
import math

class FiniteStateController(Node):
    ideal_closeness = 90
    error_to_velocity = 0.02
    de_dt_to_velocity = 0.1

    def __init__(self):
        self.e_stop = False
        self.laser_mad = False
        super().__init__("finite_state_controller")
        self.timer_period = .01
        self.timer = self.create_timer(self.timer_period, self.run_loop)
        self.publisher = self.create_publisher(Twist,'cmd_vel', 10)
        self.sub_bump = self.create_subscription(Bump, "bump", self.process_bump, 10)
        self.sub_scan = self.create_subscription(LaserScan, "scan", self.process_scan, 10)
        self.time_started = time.time()
        self.what_doin = 0
        self.move_time = (4, 1.57)
        self.twist_direction = (Twist(), Twist())
        self.twist_direction[0].linear.x = .25
        self.twist_direction[1].angular.z = 1.0
        self.possible_person = []
        self.laser_eyes = None
        self.last_error = None
        self.last_time = time.time()
    
    def process_bump(self, msg):
        self.e_stop = msg.left_front or msg.left_side or msg.right_front or msg.right_side
        # print("e_stop:", self.e_stop)

    def process_scan(self, msg):
        self.laser_eyes = msg.ranges
        neato_eyes = self.laser_eyes[-45:-1] + self.laser_eyes[0:45]
        if any(distance<0.5 for distance in neato_eyes):
            self.laser_mad = True
        else:
            self.laser_mad = False
        # print("laser_mad:", self.laser_mad)

        self.possible_person = []
        for i in range(360):
            if abs(self.laser_eyes[i]-self.laser_eyes[i+1]) > 5: # and self.laser_eyes[i]<10 and self.laser_eyes[i+1]<10:
                if self.laser_eyes[i] < self.laser_eyes[i+1] and self.laser_eyes[i]<4:
                    self.possible_person.append((i,self.laser_eyes[i]))
                elif self.laser_eyes[i+1]<4:
                    self.possible_person.append((i+1,self.laser_eyes[i+1]))
        print(self.possible_person)


    def avoid_collision(self):
        twist_msg = Twist()
        twist_msg.angular.z = .2
        self.publisher.publish(twist_msg)

    def run_loop(self):
        # Make sure the timer period is long enough
        if self.last_time + self.timer_period > time.time():
            print("self.timer_period is too long!")
            self.last_time = time.time()

        # Check for and run the current state
        if self.e_stop:
            # print("stopping due to bump")
            twist_msg = Twist()
            self.publisher.publish(twist_msg)
        elif self.laser_mad:
            # print("avoiding collision")
            self.avoid_collision()
        elif len(self.possible_person) > 0:
            self.person_follow()
        else:
            print("wall following")
            self.wall_follow()

    def forward(self):
        twist_msg = Twist()
        twist_msg.linear.x = .4
        self.publisher.publish(twist_msg)

    def square(self):
        elapsed_time = time.time() - self.time_started
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

        # Sort "possible person" list by distance to get the closest point in the list
        self.possible_person.sort(key = lambda element: element[1])
        theta = self.possible_person[0][0]
        theta_rad = (theta if theta<180 else theta-360) * math.pi / 180
        distance = self.possible_person[0][1]

        # Use angle and distance to point to calculate ideal angular velocity
        arc_length = (distance * theta_rad) / math.sin(theta_rad/2)
        time = arc_length / 0.1
        angular_vel = theta_rad / time
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
            self.forward
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
        # print(f"closeness = {closeness[closeness_index]}")
        error = closeness[closeness_index] - self.ideal_closeness
        # print(f"{error = }")

        # Turn based on that error and the previous error
        wall_side_sign = closeness_index * 2 - 1
        angular_vel = error * self.error_to_velocity * wall_side_sign
        if self.last_error is not None:
            # Calculate how much the rate of change of error
            # should effect the angular velocity
            delta_error = error - self.last_error
            de_dt = self.timer_period * delta_error
            angular_vel += de_dt * self.de_dt_to_velocity

        # print(f"Unclamped angular velocity = {angular_vel}")
        angular_vel = max(angular_vel, -0.5)
        angular_vel = min(angular_vel, 0.5)
        # print(f"Clamped angular velocity = {angular_vel}")
        twist_msg = Twist()
        twist_msg.linear.x = 0.15
        twist_msg.angular.z = angular_vel
        self.publisher.publish(twist_msg)

        # Set last_error
        self.last_error = error

def main(args = None):
    rclpy.init(args=args)      
    node = FiniteStateController()
    rclpy.spin(node)
    rclpy.shutdown()    


if __name__ == '__main__':
    main()

