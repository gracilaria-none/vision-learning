import cv2

img = cv2.imread("test.jpg")
if img is None:
    raise FileNotFoundError("找不到图片，请检查路径")

# 1. 调整尺寸：缩放到 640x480
#    cv2.resize(原图, (宽, 高))
img_resized = cv2.resize(img, (640, 480))

# 2. 灰度化：彩色图转灰度图（很多算法只需要灰度图，且更快）
#    注意 OpenCV 默认是 BGR 通道顺序，不是常见的 RGB
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 3. 高斯模糊：降噪，让画面更平滑
#    (5, 5) 是卷积核大小（必须是奇数），越大越模糊
blurred = cv2.GaussianBlur(img, (5, 5), 0)

# 4. 边缘检测：Canny 算法，突出物体轮廓
#    100 和 200 是两个阈值，值越低检测到的边缘越多
edges = cv2.Canny(gray, 100, 200)

# 5. 二值化：把灰度图变成只有黑白两色
#    127 是阈值：像素值 > 127 变白(255)，否则变黑(0)
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

# 6. 画一个矩形框在图上（目标检测结果常用）
#    (50, 50) 是左上角坐标，(200, 200) 是右下角坐标
#    (0, 255, 0) 是颜色（BGR 顺序，这里是绿色），2 是线宽
cv2.rectangle(img, (50, 50), (200, 200), (0, 255, 0), 2)

# 7. 写一行文字在图上
#    (10, 30) 是文字左下角起点，0.8 是字号，FONT_HERSHEY_SIMPLEX 是字体
cv2.putText(img, "Hello CV", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

# 分别显示处理结果
cv2.imshow("原图", img)
cv2.imshow("缩放", img_resized)
cv2.imshow("灰度", gray)
cv2.imshow("模糊", blurred)
cv2.imshow("边缘", edges)
cv2.imshow("二值化", binary)

cv2.waitKey(0)
cv2.destroyAllWindows()
