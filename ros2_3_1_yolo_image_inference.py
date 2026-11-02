#!/usr/bin/env python3
# 单张图片 YOLO 推理示例：只调用训练好的模型做检测，不训练。
# 参考仓库：robocon26-sues 的 weapon-yolo 分支（权重在 weights/best.pt）

import cv2
from ultralytics import YOLO

# 1. 加载已经训练好的模型权重（.pt 文件），这里不需要训练，直接调用即可
#    把路径换成你自己的 best.pt（参考仓库 weapon-yolo 分支的 weights/best.pt）
model = YOLO("weights/best.pt")

# 2. 读取一张待检测的图片
img = cv2.imread("test.jpg")
if img is None:
    raise FileNotFoundError("找不到图片，请检查路径")

# 3. 推理：conf 是置信度阈值（只保留置信度 >= conf 的框）
results = model(img, conf=0.5)

# 4. 画框并显示
#    results[0].plot() 会把所有检测框、类别名、置信度直接画到图上
annotated = results[0].plot()
cv2.imshow("YOLO 检测结果", annotated)
cv2.waitKey(0)
cv2.destroyAllWindows()

# 5. 打印每个目标的详细信息（供后续 ROS2 节点里解析用）
for r in results:
    for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()   # 框的左上角和右下角坐标
        cls = int(box.cls[0])                    # 类别编号
        conf = float(box.conf[0])                # 置信度
        name = model.names[cls]                  # 类别名称
        print(f"{name}: ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) conf={conf:.2f}")
