import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from neato2_interfaces.msg import Bump
import time
from sensor_msgs.msg import LaserScan

class FiniteStateController(Node):
    ideal_closeness = 10
    error_to_velocity = 1

    def __init__(self):
        self.e_stop = False
        self.laser_mad = False
        super().__init__("finite_state_controller")
        timer_period = .01
        self.timer = self.create_timer(timer_period, self.run_loop)
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
        print("laser_mad:", self.laser_mad)

        for i in range(360):
            if abs(laser_eyes[i]-laser_eyes[i+1]) > 5:
                possible_person.append(laser_eyes(i))

    def avoid_collision(self):
        twist_msg = Twist()
        twist_msg.angular.z = .2
        self.publisher.publish(twist_msg)

    def run_loop(self):
        if self.e_stop:
            # print("stopping due to bump")
            twist_msg = Twist()
            self.publisher.publish(twist_msg)
        elif self.laser_mad:
            # print("avoiding collision")
            self.avoid_collision()
        else:
            # self.square()
            self.forward() # adding this temporarily to test collision avoidance

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
    
    def person_follow():
        if len(possible_person) > 0
        



    def wall_follow(self):
        """
        Make the Neato balance driving toward the nearest wall
        in front of it and keeping a safe distance from it.
        """
        # Take in the laser range data from the left and right
        # side of the front quarter of the Neato.
        left_laser = self.laser_eyes[1:46]
        right_laser = self.laser_eyes[315:360]

        # Make a weighted sum of all ranges on each side
        # that scales with how close the ranges are
        # by summing the reciprocals of the distances.
        closeness = (sum([1 / dist for dist in left_laser]),
            sum([1 / dist for dist in right_laser]))
            # closeness = (left, right)

        # Choose which side has the closest wall.
        closeness_index = int(left_closeness - right_closeness < 0)

        # Find the error from the ideal closeness
        error = closeness[wall_on_right] - self.ideal_closeness
        

def main(args = None):
    rclpy.init(args=args)      
    node = FiniteStateController()
    rclpy.spin(node)
    rclpy.shutdown()    


if __name__ == '__main__':
    main()

