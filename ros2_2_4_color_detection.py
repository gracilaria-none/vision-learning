import cv2
import numpy as np  # NumPy 用于数组运算，OpenCV 图像本质就是数组

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # OpenCV 默认读进来是 BGR 颜色空间，先转成 HSV（色相-饱和度-明度）
    # HSV 更适合做颜色筛选，因为「颜色」由色相 H 决定，不受光照影响那么明显
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 定义「红色」在 HSV 空间中的范围（红色在 HSV 里跨越 0 度附近，需两段）
    # 低阈值：(色相, 饱和度, 明度)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    # inRange 会把范围内像素设为白色(255)，范围外设为黑色(0)，得到「掩膜 mask」
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)  # 合并两段红色范围

    # 用掩膜把原图中的红色部分「抠」出来
    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("原图", frame)
    cv2.imshow("红色掩膜", mask)
    cv2.imshow("只保留红色", result)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
