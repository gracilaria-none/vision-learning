#!/usr/bin/env python3
# ROS2 通用 YOLO 检测节点：订阅普通相机（USB 摄像头等）的图像话题，推理后发布画好框的图像。
# 只做推理，不训练。参考仓库：robocon26-sues 的 weapon-yolo 分支 yolo_detector/yolo_node.py

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time
from ultralytics import YOLO


class YoloNode(Node):
    def __init__(self):
        super().__init__('yolo_node')  # 节点名称

        # 1. 声明模型路径参数 model_path，通过命令行传入：
        #    ros2 run yolo_detector yolo_node --ros-args -p model_path:=/path/to/best.pt
        self.declare_parameter('model_path', '')
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        if not model_path:
            self.get_logger().error('未提供模型路径！请通过 -p model_path:=/path/to/best.pt 传入')
            raise RuntimeError('缺少必需的 model_path 参数')

        # 2. 加载 YOLO 模型（只推理，不训练）
        self.get_logger().info(f'正在加载 YOLO 模型: {model_path}')
        self.model = YOLO(model_path)

        # 3. CvBridge 用于 ROS2 图像消息与 OpenCV 图像互转
        self.bridge = CvBridge()
        self.prev_time = time.time()

        # 4. 订阅图像话题（普通 USB 相机一般发在 /camera/image_raw）
        self.image_sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)

        # 5. 发布画好框的图像话题
        self.image_pub = self.create_publisher(Image, '/yolo/image_annotated', 10)
        self.get_logger().info('YOLO ROS2 节点已启动，等待图像数据...')

    def image_callback(self, msg):
        # 1. ROS2 Image -> OpenCV
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'图像转换失败: {e}')
            return

        # 2. YOLO 推理（verbose=False 关闭控制台刷屏）
        results = self.model(frame, verbose=False)
        annotated = results[0].plot() if len(results) > 0 else frame.copy()

        # 3. 计算并绘制 FPS
        current_time = time.time()
        fps = 1.0 / (current_time - self.prev_time)
        self.prev_time = current_time
        cv2.putText(annotated, f'FPS: {int(fps)}', (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 4. OpenCV -> ROS2 Image 并发布
        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            annotated_msg.header = msg.header
            self.image_pub.publish(annotated_msg)
        except Exception as e:
            self.get_logger().warn(f'发布图像失败: {e}')

        # 5. 本地预览窗口（不需要时把 show_monitor 改成 False）
        show_monitor = True
        if show_monitor:
            cv2.imshow('YOLO ROS2 Monitor', annotated)
            cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    try:
        node = YoloNode()
        rclpy.spin(node)
    except RuntimeError as e:
        print(f'节点因错误终止: {e}')
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
