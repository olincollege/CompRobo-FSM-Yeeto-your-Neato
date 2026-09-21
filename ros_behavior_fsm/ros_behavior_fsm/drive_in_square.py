import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from neato2_interfaces.msg import Bump
import time

class DriveInSquare(Node):
    def __init__(self):
        self.what_doin = 0
        super().__init__("drive_in_square")
        timer_period = 0.01
        self.timer = self.create_timer(timer_period, self.run_loop)
        self.publisher = self.create_publisher(Twist,'cmd_vel', 10)
        self.time_started = time.time()
        self.move_time = (4,0.785)
        self.twist_direction = (Twist(), Twist())
        self.twist_direction[0].linear.x = .25
        self.twist_direction[1].angular.z = 2.0

    def run_loop(self):
        elapsed_time = time.time() - self.time_started
        i = self.what_doin % 2
        if elapsed_time >= self.move_time[i]:
            self.what_doin += 1
            self.time_started = time.time()
        else:
            self.publisher.publish(self.twist_direction[i])


def main(args = None):
    rclpy.init(args=args)
    node = DriveInSquare()
    rclpy.spin(node)
    rclpy.shutdown()



if __name__ == '__main__':
    main()

