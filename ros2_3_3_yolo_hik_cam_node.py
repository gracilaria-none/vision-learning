#!/usr/bin/env python3
# ROS2 海康相机 YOLO 检测节点
# 订阅海康相机节点(hikvision_ros2_driver_node)发布的图像话题 /raw/image，推理后发布标注图像和检测结果矩阵。
# 只做推理，不训练。参考仓库：robocon26-sues 的 weapon-yolo 分支 yolo_detector/yolo_hik_cam_node.py

import os
import json
import time

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray, MultiArrayDimension
from cv_bridge import CvBridge
from ultralytics import YOLO


class YoloHikCamNode(Node):
    def __init__(self):
        super().__init__('yolo_hik_detection_node')  # 节点名称

        # 1. 读取配置文件（默认放在运行目录下），内含模型路径与相机话题
        config_path = 'yolo_hik_cam_node.json'
        # 默认值：与参考仓库保持一致（海康相机节点发布在 /raw/image）
        model_path = 'weights/best.pt'
        camera_topic = '/raw/image'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                model_path = config.get('model_path', model_path)
                camera_topic = config.get('camera_topic', camera_topic)
                self.get_logger().info(f'已从 {config_path} 加载参数')
            except Exception as e:
                self.get_logger().warn(f'读取配置文件失败，使用默认值: {e}')
        else:
            self.get_logger().warn(f'配置文件 {config_path} 不存在，使用默认值')

        # 2. 加载 YOLO 模型（只推理，不训练）
        self.get_logger().info(f'正在加载 YOLO 模型: {model_path}')
        self.model = YOLO(model_path)

        # 3. CvBridge 与发布者
        self.bridge = CvBridge()
        # 发布带框图像，供 Rviz2 调试查看
        self.image_pub = self.create_publisher(Image, 'yolo_detection/image_annotated', 10)
        # 发布检测结果矩阵（n 行 3 列：cls, dx, dy）
        self.matrix_pub = self.create_publisher(Float32MultiArray, 'yolo_detection/results_matrix', 10)

        # 4. 订阅海康相机节点发布的图像话题
        self.get_logger().info(f'正在订阅海康相机话题: {camera_topic}')
        self.image_sub = self.create_subscription(Image, camera_topic, self.image_callback, 10)

        self.prev_time = time.time()
        self.get_logger().info('海康相机 YOLO 检测节点已启动！')

    def image_callback(self, msg):
        # 1. ROS2 Image -> OpenCV
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'图像转换失败: {e}')
            return

        # 2. 图像中心（作为参考点，用于计算目标相对画面的偏移量 dx, dy）
        img_height, img_width = frame.shape[:2]
        cam_cx, cam_cy = img_width // 2, img_height // 2

        # 3. YOLO 推理
        results = self.model(frame)
        annotated = frame.copy()

        flat_matrix_data = []  # 展平结果: [cls1, dx1, dy1, cls2, dx2, dy2, ...]
        target_count = 0

        for r in results:
            annotated = r.plot()
            for box in r.boxes:
                # 边界框中心
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                box_cx, box_cy = (x1 + x2) // 2, (y1 + y2) // 2
                # 类别 ID 与相对偏移
                cls_id = float(box.cls[0])
                dx = float(box_cx - cam_cx)
                dy = float(box_cy - cam_cy)
                flat_matrix_data.extend([cls_id, dx, dy])
                target_count += 1

                # 调试画点画线：红点=画面中心，蓝点=目标中心
                cv2.circle(annotated, (cam_cx, cam_cy), 5, (0, 0, 255), -1)
                cv2.circle(annotated, (box_cx, box_cy), 5, (255, 0, 0), -1)
                cv2.line(annotated, (cam_cx, cam_cy), (box_cx, box_cy), (255, 255, 0), 2)

        # 4. 封装成 Float32MultiArray（n 行 x 3 列）
        mat_msg = Float32MultiArray()
        dim_rows = MultiArrayDimension()
        dim_rows.label = 'rows_objects'
        dim_rows.size = target_count
        dim_rows.stride = target_count * 3
        dim_cols = MultiArrayDimension()
        dim_cols.label = 'columns_features'
        dim_cols.size = 3
        dim_cols.stride = 3
        mat_msg.layout.dim = [dim_rows, dim_cols]
        mat_msg.data = flat_matrix_data
        self.matrix_pub.publish(mat_msg)
        self.get_logger().info(f'识别到 {target_count} 个物体，矩阵大小 {target_count}x3')

        # 5. 计算 FPS 并发布标注图像
        current_time = time.time()
        fps = 1.0 / (current_time - self.prev_time) if (current_time - self.prev_time) > 0 else 0.0
        self.prev_time = current_time
        cv2.putText(annotated, f'FPS: {int(fps)} Count: {target_count}', (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        try:
            ros_image = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            self.image_pub.publish(ros_image)
        except Exception as e:
            self.get_logger().error(f'图像发布失败: {e}')

        # 6. 本地预览窗口（调试用，不需要时删除这两行）
        cv2.imshow('YOLO HikRobot Detection', annotated)
        cv2.waitKey(1)

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = YoloHikCamNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('检测到 Ctrl+C，正在退出...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
