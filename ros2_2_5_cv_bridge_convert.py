#!/usr/bin/env python3
# ROS2 图像消息与 OpenCV 图像互转示例（cv_bridge）
# 在 ROS2 中，图像以 sensor_msgs/Image 消息的形式在节点之间传递；
# 而 OpenCV 处理图像用的是 NumPy 数组。cv_bridge 就是两者之间的「翻译官」。

import cv2
from cv_bridge import CvBridge

# 创建 CvBridge 对象（一个进程里创建一个即可，可在多个回调里复用）
bridge = CvBridge()

# 用 OpenCV 读入一张图片（OpenCV 默认是 BGR 通道顺序）
img = cv2.imread("test.jpg")
if img is None:
    raise FileNotFoundError("找不到图片，请检查路径")

# ---------- 方向 1：OpenCV 图像 -> ROS2 Image 消息 ----------
# encoding 参数必须和图片的实际通道顺序一致：
#   bgr8  = BGR 顺序的 8 位 3 通道彩色图（OpenCV 读进来默认就是这个）
#   mono8 = 8 位单通道灰度图
ros_msg = bridge.cv2_to_imgmsg(img, encoding="bgr8")
print("已转成 ROS2 消息，尺寸:", ros_msg.width, "x", ros_msg.height, "编码:", ros_msg.encoding)

# ---------- 方向 2：ROS2 Image 消息 -> OpenCV 图像 ----------
# desired_encoding 表示希望转成什么格式，cv_bridge 会自动帮你做颜色空间转换
img_back = bridge.imgmsg_to_cv2(ros_msg, desired_encoding="bgr8")

# 验证转换结果与原始图片一致
print("转换回来后的形状:", img_back.shape)  # 期望 (高, 宽, 3)

# 说明：在真正的 ROS2 节点里，方向 2 用在订阅回调中（把收到的图像转成 OpenCV），
#       方向 1 用在发布前（把处理好的 OpenCV 图像转回 ROS2 消息）。见第三部分示例。
