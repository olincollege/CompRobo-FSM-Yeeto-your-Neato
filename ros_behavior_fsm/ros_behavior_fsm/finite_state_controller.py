import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from neato2_interfaces.msg import Bump
import time

class FiniteStateController(Node):
    def __init__(self):
        self.e_stop = False
        super().__init__("finite_state_controller")
        timer_period = .01
        self.timer = self.create_timer(timer_period, self.run_loop)
        self.publisher = self.create_publisher(Twist,'cmd_vel', 10)
        self.sub_bump = self.create_subscription(Bump, "bump", self.stop_now, 10)
        self.sub_scan = self.create_subscription(Bump, "scan", self.stop_now, 10)
    
    def stop_now(self, msg):
        self.e_stop = msg.left_front or msg.left_side or msg.right_front or msg.right_side
        print(self.e_stop)


    def run_loop(self):
        
        if not self.e_stop:
            twist_msg = Twist()
            twist_msg.linear.x = .5
            self.publisher.publish(twist_msg)
        else:
            twist_msg = Twist()
            self.publisher.publish(twist_msg)

    def wall_follow(self,msg)
        pass

        
def main(args = None):
    rclpy.init(args=args)      
    node = FiniteStateController()
    rclpy.spin(node)
    rclpy.shutdown()    



if __name__ == '__main__':
    main()

