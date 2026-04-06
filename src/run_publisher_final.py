#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time
import sys
import threading

if sys.platform == 'win32':
    import msvcrt
else:
    import termios
    import tty

# ==========================================
#  角度設定區 (單位: 度 0-240)
# ==========================================

NEUTRAL_POSITIONS = {}
# 填入您指定的角度
for i in range(1, 13):
    if i==1:
        NEUTRAL_POSITIONS[i] = 39.0
    elif i==2:
        NEUTRAL_POSITIONS[i] = 200.0
    elif i==3:
        NEUTRAL_POSITIONS[i] = 31.0
    elif i==4:
        NEUTRAL_POSITIONS[i] = 200.0
    elif i==5:
        NEUTRAL_POSITIONS[i] = 39.0
    elif i==6:
        NEUTRAL_POSITIONS[i] = 200.0
    elif i==7:
        NEUTRAL_POSITIONS[i] = 35.0
    elif i==8:
        NEUTRAL_POSITIONS[i] = 177.0
    elif i==9:
        NEUTRAL_POSITIONS[i] = 32.0
    elif i==10:
        NEUTRAL_POSITIONS[i] = 200.0
    elif i==11:
        NEUTRAL_POSITIONS[i] = 105.0
    elif i==12:
        NEUTRAL_POSITIONS[i] = 187.0

# === 運動參數 ===
LIFT_OFFSET = 30.0   # 腿部抬高幅度
PAN_OFFSET  = 20.0   # 前後移動步伐大小
TURN_OFFSET = 25.0   # 轉彎時的步伐大小 (註: 3度太小，先設為25)

# ==========================================

LEG_MAPPING = {
    1: [1, 2], 2: [3, 4], 3: [5, 6],
    4: [7, 8], 5: [9, 10], 6: [11, 12]
}

NUM_SERVOS = 12

def get_key(timeout=0.1):
    if sys.platform == 'win32':
        # Windows is not handled with timeout in this version.
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8')
        return None
    else:
        # For Unix-like systems (Linux, macOS)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            import select
            if select.select([sys.stdin], [], [], timeout)[0]:
                ch = sys.stdin.read(1)
                return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return None

class HexapodController(Node):
    def __init__(self):
        super().__init__('hexapod_controller_v2')
        self.pub = self.create_publisher(JointTrajectory, '/servo_trajectory', 10)
        self.current_positions = [90.0] * NUM_SERVOS
        
        self.left_legs = [2, 3, 4]
        self.right_legs = [5, 6, 1]
        self.tripod1 = [1, 3, 5]
        self.tripod2 = [2, 4, 6]
        
        self.running = True
        self.current_action = 'stand'
        self.action_lock = threading.Lock()

        self.get_logger().info('六足控制器 V2 已啟動')
        self.get_logger().info('指令: w=前進, s=後退, a=左轉, d=右轉, [space]=停止, q=退出')

    def publish_angles(self):
        """發布計算好的角度到ROS主題"""
        msg = JointTrajectory()
        msg.joint_names = [f'servo_{i}' for i in range(1, NUM_SERVOS + 1)]
        pt = JointTrajectoryPoint()
        pt.positions = self.current_positions.copy()
        pt.time_from_start.sec = 0
        pt.time_from_start.nanosec = 500_000_000  # 250ms
        msg.points = [pt]
        self.pub.publish(msg)
        time.sleep(0.15)  # Wait for the move to complete

    def set_servo(self, servo_id, angle):
        if 1 <= servo_id <= NUM_SERVOS:
            self.current_positions[servo_id - 1] = float(angle)

    def stand(self):
        """回到指定的校正角度"""
        # self.get_logger().info('執行: 站立')
        for servo_id, angle in NEUTRAL_POSITIONS.items():
            self.set_servo(servo_id, angle)
        self.publish_angles()

    def move_leg(self, leg_id, lift_state, pan_state, offset):
        lift_servo, pan_servo = LEG_MAPPING[leg_id]
        center_lift = NEUTRAL_POSITIONS[lift_servo]
        center_pan = NEUTRAL_POSITIONS[pan_servo]
        lift_target = center_lift + (LIFT_OFFSET if lift_state == 1 else 0)
        direction = 1.0 if leg_id in self.left_legs else -1.0
        pan_target = center_pan + (offset * pan_state * direction)
        self.set_servo(lift_servo, lift_target)
        self.set_servo(pan_servo, pan_target)

    def walk(self, direction=1):
        """執行前進或後退的三角步態 (一個完整步態)"""
        log_msg = '前進' if direction == 1 else '後退'
        self.get_logger().info(f'執行: {log_msg}')
        pan_swing = direction
        pan_push = -direction
        
        # 週期 1
        for leg in self.tripod1: self.move_leg(leg, 1, 0, PAN_OFFSET)
        self.publish_angles()
        for leg in self.tripod1: self.move_leg(leg, 1, pan_swing, PAN_OFFSET)
        for leg in self.tripod2: self.move_leg(leg, 0, pan_push, PAN_OFFSET)
        self.publish_angles()
        for leg in self.tripod1: self.move_leg(leg, 0, pan_swing, PAN_OFFSET)
        self.publish_angles()

        # 週期 2
        for leg in self.tripod2: self.move_leg(leg, 1, pan_push, PAN_OFFSET)
        self.publish_angles()
        for leg in self.tripod2: self.move_leg(leg, 1, pan_swing, PAN_OFFSET)
        for leg in self.tripod1: self.move_leg(leg, 0, pan_push, PAN_OFFSET)
        self.publish_angles()
        for leg in self.tripod2: self.move_leg(leg, 0, pan_swing, PAN_OFFSET)
        self.publish_angles()

    def turn(self, turn_direction=-1):
        """執行左轉或右轉的三角步態 (一個完整步態)"""
        log_msg = '左轉' if turn_direction == -1 else '右轉'
        self.get_logger().info(f'執行: {log_msg}')
        pan_left = -turn_direction
        pan_right = turn_direction
        
        # 週期 1
        for leg in self.tripod1: self.move_leg(leg, 1, 0, TURN_OFFSET)
        self.publish_angles()
        for leg in self.tripod1: self.move_leg(leg, 1, pan_left, TURN_OFFSET)
        for leg in self.tripod2: self.move_leg(leg, 0, -pan_right, TURN_OFFSET)
        self.publish_angles()
        for leg in self.tripod1: self.move_leg(leg, 0, pan_left, TURN_OFFSET)
        self.publish_angles()

        # 週期 2
        for leg in self.tripod2: self.move_leg(leg, 1, -pan_right, TURN_OFFSET)
        self.publish_angles()
        for leg in self.tripod2: self.move_leg(leg, 1, pan_right, TURN_OFFSET)
        for leg in self.tripod1: self.move_leg(leg, 0, -pan_left, TURN_OFFSET)
        self.publish_angles()
        for leg in self.tripod2: self.move_leg(leg, 0, pan_right, TURN_OFFSET)
        self.publish_angles()

    def _keyboard_listener(self):
        """在獨立線程中監聽鍵盤輸入"""
        while rclpy.ok() and self.running:
            key = get_key()
            if key:
                key = key.lower()
                with self.action_lock:
                    if key == 'w':
                        self.current_action = 'walk'
                    elif key == 's':
                        self.current_action = 'walk_backwards'
                    elif key == 'a':
                        self.current_action = 'turn_left'
                    elif key == 'd':
                        self.current_action = 'turn_right'
                    elif key == ' ':
                        self.current_action = 'stand'
                    elif key == 'q':
                        self.running = False
                        self.current_action = 'stand' # Ensure it stands before quitting

    def _movement_loop(self):
        """主循環，根據當前狀態執行動作"""
        last_action = ''
        is_standing = False

        while rclpy.ok() and self.running:
            with self.action_lock:
                action = self.current_action
            
            if action != last_action:
                self.get_logger().info(f"改變動作 -> {action}")
                last_action = action
                is_standing = False

            if action == 'walk':
                self.walk(1)
            elif action == 'walk_backwards':
                self.walk(-1)
            elif action == 'turn_left':
                self.turn(-1)
            elif action == 'turn_right':
                self.turn(1)
            elif action == 'stand':
                if not is_standing:
                    self.stand()
                    is_standing = True
                # 在站立狀態下短暫休眠，避免CPU空轉
                time.sleep(0.1)
        
        # 退出循環後，確保機器人站立
        self.get_logger().info("程式結束，機器人站立...")
        self.stand()

    def start(self):
        """啟動鍵盤監聽和運動循環"""
        self.stand()  # 初始歸位

        listener_thread = threading.Thread(target=self._keyboard_listener, daemon=True)
        listener_thread.start()

        self._movement_loop()

def main(args=None):
    rclpy.init(args=args)
    node = HexapodController()
    try:
        node.start()
    except (KeyboardInterrupt, EOFError):
        node.get_logger().info('手動中斷程式')
    finally:
        # 清理
        node.running = False
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
