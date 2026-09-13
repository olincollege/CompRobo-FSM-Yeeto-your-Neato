import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from neato2_interfaces.msg import Bump
import time

class DriveInSquare(Node):
    def __init__(self):
        self.what_doin = 0
        super().__init__("square_neato_node")
        timer_period = 1
        self.timer = self.create_timer(timer_period, self.run_loop)
        self.publisher = self.create_publisher(Twist,'cmd_vel', 10)
        time_started = time.time()
        move_time = (10,6)
        twist_direction = (Twist(), Twist())
        twist_direction[0].linear.x = .5
        twist_direction[1].angular.z = .5

    def run_loop(self):
        elapsed_time = time.time() - self.time_started
        self.what_doin % 2 = i
            if elapsed_time >= move_time[i]:
                what_doin += 1
                time_started = time.time()
            else:
                publish(i)
          


def main(args = None):
    rclpy.init(args=args)      
    node = MoveNeatoNode()
    rclpy.spin(node)
    rclpy.shutdown()    



if __name__ == '__main__':
    main()

