import cv2

# 打开默认摄像头（参数 0 表示第一个摄像头；外接摄像头可试 1、2...）
cap = cv2.VideoCapture(0)

# 循环读取每一帧画面
while True:
    # cap.read() 返回两个值：
    #   ret  : 布尔值，True 表示成功读到一帧，False 表示失败（如摄像头断开）
    #   frame: 这一帧的图像数据
    ret, frame = cap.read()

    # 如果读帧失败，跳出循环
    if not ret:
        print("无法读取摄像头画面")
        break

    # 显示画面
    cv2.imshow("摄像头实时画面", frame)

    # 每 1 毫秒检测一次按键；按 q 键（ASCII 码 113）退出循环
    # 注意：这里不能用 waitKey(0)，否则画面会卡住不动
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 释放摄像头（养成好习惯，否则可能占用设备）
cap.release()
cv2.destroyAllWindows()
