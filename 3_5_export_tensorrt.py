from ultralytics import YOLO

# 先加载训练好的模型
model = YOLO("runs/detect/train/weights/best.pt")

# 导出 TensorRT 引擎
#   format="engine" 指定导出为 TensorRT 格式
#   这一步会生成一个 .engine 文件，推理时直接加载它即可获得加速
model.export(format="engine")

# 之后加载导出的引擎做推理（和普通 .pt 用法一致）
# engine_model = YOLO("runs/detect/train/weights/best.engine")
