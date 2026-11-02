import cv2  # 导入 OpenCV 库，习惯上简写为 cv2

# 读取图片（把路径换成你自己电脑上的图片路径，Ubuntu 下例如 "/home/用户名/Pictures/test.jpg"）
# 返回的 img 是一个 NumPy 数组，形状是 (高, 宽, 通道数)
img = cv2.imread("test.jpg")

# 检查图片是否读取成功（路径错误时会返回 None）
if img is None:
    print("读取图片失败，请检查路径！")
else:
    # 打开一个窗口显示图片
    cv2.imshow("图片窗口", img)

    # waitKey(0) 表示等待用户按任意键才继续；参数是等待的毫秒数，0 表示无限等待
    cv2.waitKey(0)

    # 关闭所有 OpenCV 创建的窗口，释放资源
    cv2.destroyAllWindows()
