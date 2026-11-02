import cv2                       # 用于读取摄像头和画框
from ultralytics import YOLO     # 用于加载模型做检测

# 加载训练好的模型（换成你自己的 best.pt 路径）
model = YOLO("runs/detect/train/weights/best.pt")

# 打开摄像头
cap = cv2.VideoCapture(0)

# 实时检测循环
while True:
    ret, frame = cap.read()      # 读取一帧画面
    if not ret:
        break

    # 用模型对当前帧做推理
    #   conf=0.5 表示置信度阈值：只保留置信度 ≥ 0.5 的检测结果
    #   置信度可以理解为「模型有多确定这个位置有这个物体」，范围 0~1
    results = model(frame, conf=0.5)

    # results 是一个列表，遍历每一个检测结果
    for r in results:
        # r.boxes 里是这一帧检测到的所有框
        for box in r.boxes:
            # 取出检测框的坐标（左上角和右下角）
            # xyxy 表示 (x1, y1, x2, y2) 格式，tolist() 转成普通列表
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # 取出类别编号（如 0、1、2）并转成整数
            cls = int(box.cls[0])

            # 取出置信度并转成浮点数
            conf = float(box.conf[0])

            # 根据类别编号拿到类别名称（model.names 是 {编号: 名称} 的字典）
            name = model.names[cls]

            # 打印检测结果
            # .0f 表示保留 0 位小数，.2f 表示保留 2 位小数
            print(f"{name}: ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) conf={conf:.2f}")

            # 在原图上画出检测框（绿色）
            # 注意：坐标要转成 int，因为画框函数只接受整数
            cv2.rectangle(frame,
                          (int(x1), int(y1)), (int(x2), int(y2)),
                          (0, 255, 0), 2)

            # 在框上方写上「类别名 置信度」文字
            label = f"{name} {conf:.2f}"
            cv2.putText(frame, label, (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 显示画好框的画面
    cv2.imshow("YOLO 实时检测", frame)

    # 按 q 键退出
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()
