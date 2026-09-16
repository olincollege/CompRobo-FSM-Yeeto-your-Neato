import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from neato2_interfaces.msg import Bump
import time
from sensor_msgs.msg import LaserScan

class FiniteStateController(Node):
    def __init__(self):
        self.e_stop = False
        self.laser_mad = False
        super().__init__("finite_state_controller")
        timer_period = .01
        self.timer = self.create_timer(timer_period, self.run_loop)
        self.publisher = self.create_publisher(Twist,'cmd_vel', 10)
        self.sub_bump = self.create_subscription(Bump, "bump", self.process_bump, 10)
        self.sub_scan = self.create_subscription(LaserScan, "scan", self.stop_now, 10)
        self.time_started = time.time()
        self.move_time = (4,8)
        self.twist_direction = (Twist(), Twist())
        self.twist_direction[0].linear.x = .25
        self.twist_direction[1].angular.z = .197

    
    def process_bump(self, msg):
        self.e_stop = msg.left_front or msg.left_side or msg.right_front or msg.right_side

    def process_scan(self, msg):
        self.laser_eyes = msg.ranges
        neato_eyes = self.laser_eyes[-45:45]
        if any(distance>.5 for distance in neato_eyes):
            self.laser_mad = True

    def avoid_collision(self):
            twist_msg = Twist()
            twist_msg.angular.z = .2
            self.publisher.publish(twist_msg)
    

    def run_loop(self):
        if self.e_stop
            twist_msg = Twist()
            self.publisher.publish(twist_msg)

        elif self.laser_mad
            self.avoid_collision()
        else:
            self.square

            
     
        
    def square(self):
        elapsed_time = time.time() - self.time_started
        i = self.what_doin % 2
        if elapsed_time >= self.move_time[i]:
            self.what_doin += 1
            self.time_started = time.time()
        else:
            self.publisher.publish(self.twist_direction[i])

    def wall_follow(self,msg)
        pass


def main(args = None):
    rclpy.init(args=args)      
    node = FiniteStateController()
    rclpy.spin(node)
    rclpy.shutdown()    



if __name__ == '__main__':
    main()

