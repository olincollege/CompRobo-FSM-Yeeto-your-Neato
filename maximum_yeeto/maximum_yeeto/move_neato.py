import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class MoveNeatoNode(Node):
    def __init__(self):
        super().__init__("move_neato_node")
        timer_period = 1
        self.timer = self.create_timer(timer_period, self.run_loop)
        self.publisher = self.create_publisher("",'cmd_vel', 10)

    def run_loop ():
        twist_msg = Twist()
        twist_msg.linear.x = .5
        self.publisher.publish(twist_msg)

def main(args = None):
    rclpy.init(args=args)      
    node = MoveNeatoNode()
    rclpy.spin(node)
    rclpy.shutdown()    


if __name__ == '__main__':
    main()
