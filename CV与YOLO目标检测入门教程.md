# 计算机视觉（CV）与 YOLO 目标检测入门教程

> **作者**：gracilaria
>
> **说明**：本文档带你从「搭建环境」到「跑通第一个 OpenCV 程序」，再到「训练并部署一个自己的 YOLO 目标检测模型」。文中所有代码都带有详细注释。
---

## 目录

1. [环境配置](#第一部分环境配置)
   - [Windows 下使用 Conda 配置环境](#11-windows-下使用-conda-配置环境)
   - [Ubuntu 22.04 下 ROS2 配置环境](#12-ubuntu-2204-下-ros2-配置环境)
2. [OpenCV 基础处理（CV 入门）](#第二部分opencv-基础处理cv-入门)
3. [YOLO 目标检测](#第三部分yolo-目标检测)
   - [YOLO 是什么](#31-yolo-是什么)
   - [数据集准备（预留 GitHub 仓库位置）](#32-数据集准备预留-github-仓库位置)
   - [训练模型](#33-训练模型)
   - [部署与推理](#34-部署与推理)
   - [TensorRT 加速（进阶，可选）](#35-tensorrt-加速进阶可选)
4. [GitHub 数据集仓库位置（预留）](#第四部分github-数据集仓库位置预留)
5. [常见问题（FAQ）](#第五部分常见问题faq)

---

# 第一部分：环境配置

> 环境配置是最容易劝退初学者的地方，请**耐心**跟着步骤一步步来。Windows 用户看 1.1，Ubuntu 22.04 用户看 1.2。

## 1.1 Windows 下使用 Conda 配置环境

### 步骤 1：安装 Miniconda（推荐）或 Anaconda

1. 打开官网下载 Miniconda 安装包（体积小、够用）：
   - 地址：https://docs.conda.io/en/latest/miniconda.html
   - 选择 **Windows 64-bit** 版本下载。
2. 双击安装包，一路「Next」，**注意**：
   - 安装路径不要有中文和空格（例如 `C:\miniconda3`）。
   - 勾选「Add Miniconda3 to my PATH environment variable」（加入环境变量）。

### 步骤 2：打开命令行工具

安装完成后，按 `Win + R`，输入 `cmd` 回车，打开命令提示符。

> 也可以使用更友好的 **Anaconda Prompt**（开始菜单里搜索），两者等价。

### 步骤 3：创建虚拟环境

虚拟环境就像给每个项目准备一个「独立的房间」，互相不干扰。在命令行输入：

```bash
# 创建一个名为 cv 的虚拟环境，指定 Python 版本为 3.10
# -n cv  : 环境名字叫 cv
# -y     : 过程中询问是否确认时自动回答 yes
conda create -n cv python=3.10 -y
```

### 步骤 4：激活环境

```bash
# 进入（激活）刚才创建的 cv 环境，之后安装的包都会装在这个环境里
conda activate cv

# 验证一下 Python 版本是否正确
python --version
# 期望输出：Python 3.10.x
```

> 激活成功后，命令行最前面会多出一个 `(cv)`，表示当前处于 cv 环境中。

### 步骤 5：安装依赖包

```bash
# 安装 OpenCV（计算机视觉库）：用于读写图片、摄像头、图像处理
pip install opencv-python

# 安装 Ultralytics：YOLOv8 的训练和推理框架
pip install ultralytics

# 安装 matplotlib（可选）：用于在程序中显示图片
pip install matplotlib
```

> **国内加速小技巧**：如果下载很慢，可以在每个 pip 命令后加上清华镜像源：
> `pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 步骤 6：验证安装是否成功

```bash
# 进入 Python 交互模式
python

# 在 >>> 提示符后输入下面两行，检查是否报错
>>> import cv2
>>> print(cv2.__version__)
# 若能正常打印版本号（如 4.10.0），说明 OpenCV 安装成功
# 按 Ctrl+Z 再回车可退出 Python 交互模式
```

---

## 1.2 Ubuntu 22.04 下 ROS2 配置环境

> Ubuntu 22.04 对应 **ROS2 Humble** 发行版（这是官方长期支持版本）。下面步骤在终端（Terminal，快捷键 `Ctrl+Alt+T`）中执行。

### 步骤 1：设置编码（locale）为 UTF-8

```bash
# 确保系统区域设置为 UTF-8，ROS2 对此有要求
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 步骤 2：启用 Ubuntu Universe 软件源

```bash
# universe 源包含 ROS2 依赖的部分软件包
sudo apt install software-properties-common
sudo add-apt-repository universe
```

### 步骤 3：添加 ROS2 仓库的密钥与地址（使用清华镜像源）

> 国内访问 ROS2 官方源（`packages.ros.org`）速度很慢，这里改用**清华大学开源软件镜像站**（Tuna）提供的 ROS2 镜像源，内容与官方完全一致，只是下载服务器不同。

```bash
# 先安装 curl（下载工具）和 lsb-release（用于获取系统版本代号）
sudo apt update && sudo apt install curl lsb-release -y

# 下载 ROS2 官方 GPG 密钥（用于验证软件包来源可信）
# 注意：密钥仍从 ROS 官方下载，因为软件包签名没变，只是下载地址换成了清华镜像
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

# 把 ROS2 软件源地址写入系统源列表（清华镜像源）
# 官方地址为 http://packages.ros.org/ros2/ubuntu ，这里替换为清华地址：
# http://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu
# $(lsb_release -cs) 会自动替换成当前系统代号（Ubuntu 22.04 对应 jammy）
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

> **可选：Ubuntu 系统源也换成清华源**
> 如果 `sudo apt update` 本身也很慢，可以把 Ubuntu 系统自带的软件源（`/etc/apt/sources.list`）也换成清华镜像，加速所有 `apt` 下载。方法参考清华镜像站说明：https://mirrors.tuna.tsinghua.edu.cn/help/ubuntu/

### 步骤 4：更新并安装 ROS2 Humble

```bash
# 更新软件包索引
sudo apt update

# 安装桌面完整版（含 RViz、demo 等图形工具，推荐初学者）
sudo apt install ros-humble-desktop -y
```

> 如果只想装精简版，可用 `ros-humble-ros-base`。教程推荐 `desktop` 版，方便可视化调试。

### 步骤 5：让 ROS2 环境变量自动生效

```bash
# 每次打开新终端都要 source 一次，才能使用 ros2 命令
source /opt/ros/humble/setup.bash

# 为避免每次手动 source，把它写进 ~/.bashrc（每次打开终端自动加载）
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 步骤 6：验证 ROS2 安装

```bash
# 打开两个终端窗口
# 终端 A：启动一个「发布者」，每秒广播一句 hello world
ros2 run demo_nodes_cpp talker

# 终端 B：启动一个「订阅者」，接收上面的消息
ros2 run demo_nodes_py listener

# 若 B 终端能持续打印 "Hello World"，说明 ROS2 安装成功
```

### 步骤 7：安装 ROS2 下的视觉相关包

```bash
# cv_bridge：ROS2 与 OpenCV 之间的「桥梁」，负责在 ROS 图像消息和 OpenCV 图像之间互相转换
sudo apt install ros-humble-cv-bridge -y

# 安装 OpenCV 的 Python 绑定
pip3 install opencv-python

# 安装 ROS2 的 Python 客户端库（写 Python 节点用）
sudo apt install python3-colcon-common-extensions -y
```

### 步骤 8：创建并编译 ROS2 工作空间（可选，进阶）

```bash
# 创建工作空间目录（名字可自定义，这里叫 ros2_ws）
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws

# 编译工作空间（colcon 是 ROS2 的构建工具）
colcon build

# 让工作空间里的包生效
source install/setup.bash
```

> **小结**：在 ROS2 里做视觉，基本套路是「摄像头/图像 → `cv_bridge` → OpenCV 处理 → `cv_bridge` → ROS 消息发布」。后面会给出示例。

---

# 第二部分：OpenCV 基础处理（CV 入门）

> OpenCV（Open Source Computer Vision Library）是最常用的开源计算机视觉库。先用几个小程序熟悉它。

## 2.1 读取并显示一张图片

```python
import cv2  # 导入 OpenCV 库，习惯上简写为 cv2

# 读取图片（把路径换成你自己电脑上的图片路径）
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
```

## 2.2 打开摄像头并实时显示画面

```python
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
```

## 2.3 常用图像处理操作

```python
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
```

## 2.4 颜色空间转换与颜色目标检测（进阶示例）

```python
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
```

> 掌握了以上内容，你就已经会用 OpenCV 做基础的图像读取、显示、处理和颜色识别了。接下来进入目标检测的重头戏 —— YOLO。

---

# 第三部分：YOLO 目标检测

## 3.1 YOLO 是什么

**YOLO（You Only Look Once）** 是一个**单阶段目标检测模型**：输入一张图像，它「只看一眼」就直接输出检测框的坐标、类别和置信度。

```
摄像头图像 → YOLO 模型 → [(x, y, w, h, class, confidence), ...]
```

它的优点是**速度快**，非常适合实时场景（比如机器人比赛、监控、自动驾驶）。

> 本教程以 **YOLOv8** 为例（`ultralytics` 库），这也是目前最流行、对新手最友好的版本。

## 3.2 数据集准备（预留 GitHub 仓库位置）

训练一个 YOLO 模型需要「喂」给它**标注好的图片**。整体流程：

1. **采集图片**：用摄像头在实际场景下拍 200~500 张照片。
2. **标注**：给每张图里的目标画框、标类别（工具：LabelImg 或 Roboflow）。
3. **组织目录**：整理成 YOLO 需要的格式（见下方）。

### 数据集目录结构

```
dataset/
├── train/                 # 训练集
│   ├── images/            # 训练图片
│   └── labels/            # 对应的标注文件（.txt）
├── val/                   # 验证集（用于评估模型好坏）
│   ├── images/
│   └── labels/
└── data.yaml              # 数据集配置文件
```

### 安装并使用标注工具 LabelImg

```bash
# 安装 LabelImg（图形化标注工具）
pip install labelimg

# 启动图形界面，框框点点即可完成标注
labelimg
```

> **LabelImg 使用小提示**：
> - 打开图片目录：点「Open Dir」选择 `images` 文件夹。
> - 设置保存目录：点「Change Save Dir」选择 `labels` 文件夹。
> - 格式选择：左侧一定要切换到 **YOLO** 格式（不是 PascalVOC）。
> - 快捷键 `w` 画框，选好类别后 `Ctrl+S` 保存。

### 编写 data.yaml 配置文件

`data.yaml` 用来告诉 YOLO「数据在哪、有几类、每类叫什么」：

```yaml
# data.yaml —— 数据集配置文件
# 训练集图片路径（改成你自己的实际路径）
train: ./dataset/train/images
# 验证集图片路径
val: ./dataset/val/images

# nc = number of classes，即类别总数，下面有 3 个类别
nc: 3

# names：类别名称列表，顺序要和标注时一致
# 这里是「红色方块 / 蓝色方块 / 障碍物」的例子
names: ['red_block', 'blue_block', 'obstacle']
```

## 3.3 训练模型

准备好数据集和 `data.yaml` 后，就可以开始训练了：

```python
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
```

> **模型怎么选？**
> `yolov8n`（nano）是最小最快的模型。如果你的场景对**速度**要求高、对精度要求一般（比如机器人比赛实时检测），用 nano 就够了。更准的还有 `yolov8s`、`yolov8m`、`yolov8l`、`yolov8x`，越大越准但也越慢。

训练完成后，权重会保存在 `runs/detect/train/weights/best.pt`（`best.pt` 是训练过程中效果最好的一轮）。

## 3.4 部署与推理

训练得到 `best.pt` 后，就可以加载它来做实时检测了：

```python
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
```

> **核心概念解释**：
> - **置信度（confidence）**：模型认为「这个框里确实有目标」的把握有多大，0~1 之间。`conf=0.5` 表示低于 50% 置信度的结果被丢弃。
> - **类别（class）**：检测到的目标属于哪一类，对应 `data.yaml` 里 `names` 的下标。
> - **xyxy**：框的左上角坐标 `(x1, y1)` 和右下角坐标 `(x2, y2)`。

## 3.5 TensorRT 加速（进阶，可选）

> 在 Jetson（英伟达嵌入式板卡）等设备上部署 YOLO 时，用 **TensorRT** 可以把推理速度提升 2~3 倍。这是进阶内容，初学者先跑通上面的流程即可。

```python
from ultralytics import YOLO

# 先加载训练好的模型
model = YOLO("runs/detect/train/weights/best.pt")

# 导出 TensorRT 引擎
#   format="engine" 指定导出为 TensorRT 格式
#   这一步会生成一个 .engine 文件，推理时直接加载它即可获得加速
model.export(format="engine")

# 之后加载导出的引擎做推理（和普通 .pt 用法一致）
# engine_model = YOLO("runs/detect/train/weights/best.engine")
```

---

# 第四部分：GitHub 数据集仓库位置（预留）

> 这里预留一个位置，用于存放**数据集实例**的 GitHub 仓库。后续将仓库创建好并上传示例数据集后，把链接和说明填在下面即可。

## 数据集仓库地址

- **仓库链接**：`https://github.com/gracilaria/【此处替换为你的仓库名】`
- **克隆命令**（把上面的链接替换后使用）：

```bash
# 克隆数据集仓库到本地
git clone https://github.com/gracilaria/【此处替换为你的仓库名】.git
```

## 仓库目录说明（规划）

```
your-dataset-repo/
├── README.md              # 数据集说明（类别、数量、来源）
├── dataset/               # 数据集本体
│   ├── train/
│   │   ├── images/        # 训练图片
│   │   └── labels/        # 训练标注
│   ├── val/
│   │   ├── images/        # 验证图片
│   │   └── labels/        # 验证标注
│   └── data.yaml          # 数据集配置
└── scripts/               # 辅助脚本（如拆分数据集、格式转换）
```

> 数据集就绪后，只需把上面的 `data.yaml` 里的 `train` / `val` 路径指向克隆下来的 `dataset/` 目录，即可直接训练。

---

# 第五部分：常见问题（FAQ）

**Q1：`cv2.imread` 返回 None？**
A：图片路径写错了，或路径里有中文/空格导致读取失败。用绝对路径再试，并确保文件存在。

**Q2：`import cv2` 报错 `No module named 'cv2'`？**
A：没装或装错了环境。先确认已 `conda activate cv`，再执行 `pip install opencv-python`。

**Q3：训练时报 `Dataset not found`？**
A：`data.yaml` 里的 `train`/`val` 路径不对。注意路径是相对你**运行命令时所在的目录**的。

**Q4：摄像头打不开（黑屏或报错）？**
A：检查摄像头是否被其他程序占用；`cv2.VideoCapture(0)` 的 `0` 换成 `1` 或 `2` 试试。

**Q5：ROS2 命令 `ros2` 找不到？**
A：没有 source 环境。执行 `source /opt/ros/humble/setup.bash`，或确认已写入 `~/.bashrc`。

**Q6：训练很慢 / 显存不足？**
A：减小 `imgsz`（如 320），或减少 `epochs`；也可以改用更轻量的 `yolov8n`。

---

> 本文档由 **gracilaria** 编写。祝你学习顺利，早日跑通自己的第一个目标检测模型！🚀
