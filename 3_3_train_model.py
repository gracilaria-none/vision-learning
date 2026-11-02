from ultralytics import YOLO  # 导入 YOLO 类

# 加载预训练模型 yolov8n.pt
#   yolov8n = YOLOv8 nano，最轻量的版本
#   .pt 后缀是 PyTorch 的模型权重文件
#   预训练模型已经在大数据集上训练过，我们在它基础上「微调」会快很多
model = YOLO("yolov8n.pt")

# 开始训练
model.train(
    data="data.yaml",   # 指定数据集配置文件
    epochs=100,         # 训练 100 轮（epoch），数据少或过拟合可适当减少
    imgsz=640           # 输入图片尺寸，640x640 是 YOLOv8 的默认值
)
