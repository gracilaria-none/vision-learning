# C++ 视觉学习框架（OpenCV 4 + ROS2 + YOLO）

> **定位**：把本仓库已有的 Python 视觉教程，升级为一条可落地的 **C++ 机器人视觉学习路线**。
>
> **适用场景**：Ubuntu 22.04 + ROS2 Humble 的机器人项目，需要实时读图、预处理、做目标检测，并把结果发布给控制节点。
>
> **建议周期**：8 周，每周 8～10 小时；C++ 基础薄弱就加 2 周，不要压缩。
>
> **最终作品**：一个 ROS2 C++ 节点，订阅相机图像，完成 OpenCV 预处理 + YOLO 推理，发布带框图像和结构化检测结果，并给出可复现的延迟/FPS 数据。

---

## 0. 先看结论

- **主线只有一条**：`C++/CMake → cv::Mat → OpenCV 预处理 → 视频流 → ROS2 节点 → YOLO 训练/导出 → C++ 推理 → 联调与性能`。
- **训练和部署分开**：YOLO 训练用 Python（Ultralytics 生态最成熟），部署用 C++（ONNX / ONNX Runtime / TensorRT）。不要一开始就用 C++ 重写训练框架。
- **ROS2 里最重要的三件事**：`cv_bridge` 转图像、QoS 对齐、图像 `header` 时间戳不能丢。
- **版本策略**：ROS2 Humble 机器上优先使用 `apt` 安装的 OpenCV 和 `cv_bridge`，不要随意源码安装另一版 OpenCV 造成 ABI 冲突。
- **验收方式**：每一阶段都必须有一个能运行的程序 + 一项可测量结果，不能只看完视频。

### 🎥 主推荐视频

**[《OpenCV4 C++ 快速入门视频30讲 - 系列合集》— OpenCV学堂（B 站）](https://www.bilibili.com/video/BV1i54y1m7tw/)**

- 共 **31 P**，总时长约 **9 小时 39 分钟**，C++ 主讲，不是 Python 课。
- 内容覆盖：OpenCV 4.8 + VS2017 环境、图像读写、色彩空间、`Mat`、像素读写、滚动条/键盘交互、通道分离、绘制、归一化、缩放旋转、视频/摄像头、直方图、卷积与高斯模糊，最后一集是实时人脸检测小案例。
- 课程资料（UP 主简介中提供）：<https://gitee.com/opencv_ai/opencv_tutorial_data>
- **注意**：课程环境是 Windows + VS2017，不要照抄环境配置。Ubuntu 下用 CMake + `apt` 的 OpenCV，代码思路完全一致。课程没有系统讲 Canny、形态学、轮廓、ROS2、YOLO，这些由本框架补齐。

---

## 目录

1. [学习目标与边界](#1-学习目标与边界)
2. [环境与技术栈](#2-环境与技术栈)
3. [8 周路线总览](#3-8-周路线总览)
4. [阶段 0：C++ 工程与 CMake](#4-阶段-0c-工程与-cmake)
5. [阶段 1：图像 I/O 与 cv::Mat](#5-阶段-1图像-io-与-cvmat)
6. [阶段 2：OpenCV 预处理](#6-阶段-2opencv-预处理)
7. [阶段 3：视频流与工程化](#7-阶段-3视频流与工程化)
8. [阶段 4：ROS2 C++ 视觉节点](#8-阶段-4ros2-c-视觉节点)
9. [阶段 5：YOLO 基础、训练与导出](#9-阶段-5yolo-基础训练与导出)
10. [阶段 6：C++ 推理与 ROS2 集成](#10-阶段-6c-推理与-ros2-集成)
11. [毕业项目与验收标准](#11-毕业项目与验收标准)
12. [本仓库现有资料如何复用](#12-本仓库现有资料如何复用)
13. [常见坑与 FAQ](#13-常见坑与-faq)
14. [学习资源与最终检查清单](#14-学习资源与最终检查清单)

---

## 1. 学习目标与边界

### 1.1 学完应该具备的能力

| 能力 | 可验证的表现 |
| --- | --- |
| C++ 工程能力 | 能用 CMake 从零组织多文件项目，能使用 RAII、STL、智能指针和 `std::chrono` |
| OpenCV 预处理 | 能独立完成读取、缩放、灰度/HSV、滤波、二值化、形态学、边缘、轮廓、ROI、绘制 |
| 视频工程 | 能稳定读取 USB 相机/视频文件，处理断流、释放资源、统计 FPS 和分段耗时 |
| ROS2 集成 | 能创建 `ament_cmake` 包，写 C++ 订阅/发布节点，正确设置 QoS、参数、launch 和日志 |
| 图像桥接 | 理解 `sensor_msgs/Image`、`cv_bridge`、BGR/RGB、编码与 `header` 的生命周期 |
| YOLO 基础 | 能解释 bbox、confidence、IoU、NMS、mAP，能训练/评估/导出 ONNX |
| C++ 部署 | 能完成 letterbox、blob、前向推理、解码、按类别 NMS、坐标还原和结果发布 |
| 性能意识 | 能测预处理/推理/总延迟，能定位拷贝、分辨率、后端和显示窗口造成的瓶颈 |

### 1.2 最终作品

做一个 **“ROS2 实时目标检测与目标偏移发布”** 节点：

```text
相机驱动 / rosbag
      │  sensor_msgs/Image
      ▼
/raw/image 或 /camera/image_raw
      │
      ▼
cpp_vision_node
      ├─ cv_bridge：Image → cv::Mat
      ├─ OpenCV：缩放/去噪/颜色/ROI
      ├─ YOLO：检测 + NMS
      ├─ 发布 /vision/annotated（sensor_msgs/Image）
      └─ 发布 /vision/detections（类别 + 置信度 + dx/dy）
```

交付要求：

- 输入、输出话题写在 README 里，节点参数用 YAML 配置。
- 缺失相机、模型路径错误、空帧、编码异常时不能崩溃。
- 连续运行 30 分钟内存稳定，`ros2 topic hz` 正常。
- 在真实硬件上记录分辨率、模型、后端、预处理耗时、推理耗时、端到端 FPS。
- 至少用一段 rosbag 复现实验，避免“只有你的电脑能跑”。

### 1.3 本阶段不追求

- 不系统推导深度学习反向传播和 YOLO 损失函数。
- 不从零实现 C++ 训练框架；训练使用 Python。
- 不覆盖 SLAM、三维重建、多传感器标定；这些放到下一阶段。
- 不追求“所有 OpenCV 函数都学一遍”，以机器人视觉常用链路为主。

---

## 2. 环境与技术栈

### 2.1 推荐配置

| 项目 | 推荐值 | 说明 |
| --- | --- | --- |
| 操作系统 | Ubuntu 22.04 LTS | 与 ROS2 Humble 对齐 |
| ROS2 | Humble Hawksbill | 官方长期支持版本 |
| 编译器 | GCC 11 | Ubuntu 22.04 默认，支持 C++17 |
| 构建 | CMake ≥ 3.22 + `colcon` | ROS2 包用 `ament_cmake` |
| 语言标准 | C++17 | 不要用 C++98 风格写新项目 |
| OpenCV | apt 版 4.5.4（Humble 环境） | **优先与 `cv_bridge` 保持一致** |
| 训练环境 | Python 3.10 + Ultralytics | 训练和导出 ONNX，不做实时部署 |
| 推理后端 | OpenCV DNN 起步，ONNX Runtime 进阶，TensorRT 可选 | 见阶段 6 对比 |

> **ABI 警告**：ROS2 Humble 的 `cv_bridge` 依赖系统 OpenCV。若你源码安装 OpenCV 4.10 并覆盖系统库，可能出现“能编译、运行时崩溃/符号错乱”。要么统一用 apt 版，要么同时重新编译 `vision_opencv/cv_bridge`，不要混用。

### 2.2 Ubuntu 安装

```bash
sudo apt update
sudo apt install -y \
  build-essential cmake git pkg-config \
  libopencv-dev \
  ros-humble-cv-bridge ros-humble-image-transport \
  ros-humble-rviz2 ros-humble-rqt-image-view

source /opt/ros/humble/setup.bash
```

验证：

```bash
pkg-config --modversion opencv4
ros2 pkg prefix cv_bridge
ros2 run demo_nodes_cpp talker
```

`pkg-config` 能输出版本号、`talker` 能持续打印，说明基础环境 OK。

### 2.3 Windows（可选，仅做 OpenCV 练习）

如果当前只有 Windows，也可以先完成阶段 0～3：

1. 安装 Visual Studio 2022（勾选“使用 C++ 的桌面开发”）。
2. 安装 OpenCV Windows 预编译包，配置 `OpenCV_DIR`。
3. 把 `%OpenCV_DIR%\x64\vc16\bin` 加入 `PATH`。
4. 用 CMake 或 VS 工程链接 `opencv_world4xx.lib`。
5. ROS2 阶段仍建议回到 Ubuntu 22.04；Windows 上的 ROS2 不是本框架主线。

### 2.4 第一个 OpenCV C++ 程序

`src/00_env_check.cpp`：

```cpp
#include <iostream>
#include <opencv2/core.hpp>

int main() {
  std::cout << "OpenCV: " << CV_VERSION << '\n';
  std::cout << "Build:  " << cv::getBuildInformation().substr(0, 200) << "...\n";
  return 0;
}
```

```bash
g++ -std=c++17 src/00_env_check.cpp \
  $(pkg-config --cflags --libs opencv4) \
  -o build/00_env_check
./build/00_env_check
```

---

## 3. 8 周路线总览

> 假设每周 8～10 小时。时间可以拉长，但**顺序不要乱**：先 C++ / OpenCV，再 ROS2，最后 YOLO 部署。

| 周 | 主题 | 本周产出 | 验收 |
| --- | --- | --- | --- |
| 1 | 环境、CMake、图像 I/O、`Mat` | 能读取/显示/保存图片，解释 `Mat` 浅拷贝 | 不看教程独立写出 2 个程序 |
| 2 | 预处理：灰度、HSV、滤波、二值化、形态学 | 颜色目标检测器，输出掩膜和目标中心 | 能调参并解释每个参数作用 |
| 3 | 边缘、轮廓、视频/摄像头、性能计时 | 实时颜色检测 + FPS + 10 秒录像 | 连续运行 10 分钟不崩溃、不涨内存 |
| 4 | ROS2 基础、包结构、话题、QoS | `ament_cmake` 包 + 最小 C++ 图像转发节点 | `ros2 topic hz` 正常，RViz2 能看到图 |
| 5 | `cv_bridge`、参数、launch、rosbag 调试 | 完整预处理节点，参数可配置 | 用 bag 回放可复现，header 时间戳保留 |
| 6 | YOLO 概念、数据检查、训练、评估、ONNX 导出 | 训练报告 + `best.pt` + `best.onnx` | 验证集指标可解释，导出前后结果一致 |
| 7 | C++ 前处理、解码、NMS、坐标还原 | 单张图片 C++ 推理程序 | 与 Python 结果框位置基本一致 |
| 8 | ROS2 集成、性能优化、文档 | 毕业项目 + 基准测试 + README | 30 分钟稳定性 + 端到端指标 |

**总投入参考**：约 70～85 小时。低于 60 小时通常只能“跑通”，达不到能改、能调、能排错的程度。

### 每周固定节奏

```text
看视频 / 文档        30%
手写 C++ 代码        50%
记录问题与参数       10%
复盘 + 提交 git      10%
```

每个程序都按“四问”收尾：

1. 输入是什么类型？`cv::Mat` 的尺寸、通道、深度是什么？
2. 每一步输出什么？有没有不必要的 `clone()`？
3. 参数变化会怎样？边界条件是什么？
4. 失败时程序怎么表现？会崩溃、黑屏，还是能优雅退出？

---

## 4. 阶段 0：C++ 工程与 CMake

### 4.1 只学够用的 C++

不要先花两个月啃完《C++ Primer》。本阶段够用的知识：

- 编译/链接、头文件、声明与定义、`#include` 保护。
- 引用与 `const`、值传递 vs 引用传递。
- `std::vector`、`std::string`、`std::array`。
- RAII：资源在析构函数释放，例如 `cv::VideoCapture`。
- `std::unique_ptr` / `std::shared_ptr`，知道“优先 `unique_ptr`”。
- lambda、`std::bind`、`std::function`（ROS2 回调会用到）。
- `std::chrono` 计时、异常、日志。
- CMake：`add_executable`、`target_link_libraries`、`target_include_directories`。

暂时可以跳过：模板元编程、手写 allocator、复杂多重继承。

### 4.2 项目骨架

```text
cpp_vision_learning/
├── C++视觉学习框架.md          # 本文
├── CMakeLists.txt              # 后续添加
├── include/vision/             # 公共头文件
├── src/
│   ├── 00_env_check.cpp
│   ├── 01_read_image.cpp
│   ├── 02_preprocess.cpp
│   ├── 03_color_detect.cpp
│   ├── 04_video.cpp
│   └── 05_yolo_infer.cpp
├── config/                     # YAML 参数
├── models/                     # .onnx / .engine，加入 .gitignore
├── test/
├── docs/
└── ros2_ws/
    └── src/cpp_vision_node/    # ROS2 包
```

> 数据集不要复制进这个目录，继续使用工作区的 `../data` 和 `../data.yaml`，避免仓库体积翻倍。

### 4.3 CMake 起步模板

```cmake
cmake_minimum_required(VERSION 3.22)
project(cpp_vision_learning LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(OpenCV 4 REQUIRED COMPONENTS
  core imgproc imgcodecs highgui videoio dnn)

add_executable(00_env_check src/00_env_check.cpp)
target_link_libraries(00_env_check PRIVATE ${OpenCV_LIBS})

add_executable(01_read_image src/01_read_image.cpp)
target_link_libraries(01_read_image PRIVATE ${OpenCV_LIBS})

# 之后的每个 demo 都按这个模式追加
```

```bash
cmake -S cpp_vision_learning -B cpp_vision_learning/build -DCMAKE_BUILD_TYPE=Release
cmake --build cpp_vision_learning/build -j
```

### 4.4 阶段验收

- [ ] 能从空的 `build/` 目录重新配置并编译成功。
- [ ] 能解释“编译错误”和“链接错误”的区别。
- [ ] 能说明为什么头文件里尽量不写 `using namespace cv;`。
- [ ] 能使用 `gdb` 或 VS Code 调试器停在断点，查看一个 `cv::Mat` 的尺寸。

---

## 5. 阶段 1：图像 I/O 与 cv::Mat

### 5.1 必须理解 `cv::Mat`

```cpp
cv::Mat a = cv::imread("test.jpg");
cv::Mat b = a;            // 浅拷贝：共享像素数据，引用计数 +1
cv::Mat c = a.clone();    // 深拷贝：独立数据
cv::Mat roi = a(cv::Rect(0, 0, 100, 100)); // ROI 仍指向原图数据
```

要记住：

- `cv::Mat = 矩阵头 + 像素数据指针`；赋值默认不复制像素。
- 修改 `b` 会影响 `a`；修改 `roi` 会影响 `a`。
- 函数参数尽量用 `const cv::Mat&` 表示只读，返回新图时直接返回 `cv::Mat`。
- OpenCV 默认读入是 **BGR**，不是 RGB。
- 类型如 `CV_8UC3` = 8 位无符号、3 通道；YOLO 输入通常是 `CV_32F`。

### 5.2 最小可运行模板

```cpp
#include <iostream>
#include <opencv2/opencv.hpp>

int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "用法: " << argv[0] << " <图片路径>\n";
    return 1;
  }

  cv::Mat bgr = cv::imread(argv[1], cv::IMREAD_COLOR);
  if (bgr.empty()) {
    std::cerr << "读取失败，请检查路径/文件权限: " << argv[1] << '\n';
    return 2;
  }

  std::cout << "尺寸: " << bgr.cols << "x" << bgr.rows
            << " 通道: " << bgr.channels()
            << " 类型: " << bgr.type() << '\n';

  cv::Mat gray;
  cv::cvtColor(bgr, gray, cv::COLOR_BGR2GRAY);
  cv::imwrite("gray.png", gray);

  cv::imshow("image", bgr);
  cv::waitKey(0);            // 0 = 无限等待，必须有
  cv::destroyAllWindows();
  return 0;
}
```

### 5.3 Windows 中文路径

`cv::imread` 在部分 Windows/OpenCV 组合下不能正确处理中文路径。稳妥做法是二进制读取后解码：

```cpp
std::ifstream ifs(path, std::ios::binary);
std::vector<uchar> buf((std::istreambuf_iterator<char>(ifs)),
                       std::istreambuf_iterator<char>());
cv::Mat img = cv::imdecode(buf, cv::IMREAD_COLOR);
```

Linux 下路径用 UTF-8，通常不需要这一步。

### 5.4 阶段验收

- [ ] 能打印任意图片的宽、高、通道数、`type()`。
- [ ] 能说明 `a=b`、`a.clone()`、ROI 三种情况的内存关系。
- [ ] 能解释为什么 `imshow` 后必须 `waitKey`，以及 `waitKey(0)` 和 `waitKey(1)` 的区别。
- [ ] 能把彩色图转灰度并保存，输出路径错误时不会崩溃。

对应本仓库参考：`../2_1_read_show_image.py`（Python 版）。

---

## 6. 阶段 2：OpenCV 预处理

机器人视觉里 80% 的代码在预处理。不要堆函数，按“目的”记：

| 目的 | 常用函数 | 关键点 |
| --- | --- | --- |
| 尺寸统一 | `cv::resize` | 缩小用 `INTER_AREA`，放大用 `INTER_LINEAR` |
| 去噪 | `cv::GaussianBlur`、`cv::medianBlur` | 核大小必须是奇数；越大越慢越糊 |
| 颜色分离 | `cv::cvtColor` | BGR↔GRAY、BGR↔HSV；HSV 的 H 范围是 0～179 |
| 阈值分割 | `cv::threshold`、`cv::adaptiveThreshold` | 光照均匀用固定/Otsu，光照不均用自适应 |
| 形态学 | `cv::morphologyEx` | 开运算去小白点，闭运算补小黑洞 |
| 边缘 | `cv::Canny` | 先模糊再边缘；双阈值不要照抄 100/200 |
| 轮廓 | `cv::findContours` | 配合 `boundingRect`、`minAreaRect`、`contourArea` |
| 画图 | `rectangle`、`circle`、`putText` | 颜色顺序是 BGR，坐标必须是整数 |
| 提取目标 | ROI / mask | ROI 是浅拷贝，注意生命周期 |

### 6.1 标准预处理链

```cpp
cv::Mat gray, blurred, edges, binary;

cv::cvtColor(bgr, gray, cv::COLOR_BGR2GRAY);
cv::GaussianBlur(gray, blurred, cv::Size(5, 5), 0.0);
cv::Canny(blurred, edges, 80, 160);
cv::threshold(blurred, binary, 0, 255,
              cv::THRESH_BINARY | cv::THRESH_OTSU);
```

调参顺序建议：

1. 先看原图/灰度图，确认曝光和清晰度。
2. 再调模糊核，目标边缘不能被抹掉。
3. 再调阈值/Canny，追求“目标完整、背景干净”。
4. 最后用形态学清理噪点，不要用形态学掩盖前期问题。

### 6.2 颜色目标检测（HSV）

红色在 HSV 色环跨 0°，需要两段掩膜：

```cpp
cv::Mat hsv, mask1, mask2, mask;
cv::cvtColor(bgr, hsv, cv::COLOR_BGR2HSV);

cv::inRange(hsv, cv::Scalar(0, 120, 70),   cv::Scalar(10, 255, 255), mask1);
cv::inRange(hsv, cv::Scalar(170, 120, 70), cv::Scalar(180, 255, 255), mask2);
cv::bitwise_or(mask1, mask2, mask);

cv::morphologyEx(
    mask, mask, cv::MORPH_OPEN,
    cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(5, 5)));
```

找到目标中心：

```cpp
std::vector<std::vector<cv::Point>> contours;
cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);

for (const auto& contour : contours) {
  if (cv::contourArea(contour) < 300.0) continue;  // 过滤小噪点

  cv::Rect box = cv::boundingRect(contour);
  cv::Moments m = cv::moments(contour);
  if (m.m00 == 0.0) continue;

  cv::Point2f center(
      static_cast<float>(m.m10 / m.m00),
      static_cast<float>(m.m01 / m.m00));

  cv::rectangle(bgr, box, cv::Scalar(0, 255, 0), 2);
  cv::circle(bgr, center, 4, cv::Scalar(0, 0, 255), -1);
}
```

> HSV 阈值不是固定真理。不同相机、曝光、灯光下要重新标定；做一个小工具用 `createTrackbar` 实时调 H/S/V 上下限，调好后把数值写入 YAML。

### 6.3 阶段实作

1. **图像预处理页**：同一张图输出原图、灰度、模糊、Canny、Otsu 二值化六个窗口。
2. **颜色检测器**：摄像头实时检测红色/蓝色目标，输出 mask、框、中心像素坐标、相对画面中心的 `dx/dy`。
3. **轮廓统计**：按面积从大到小排序，只保留前 3 个目标，打印每个目标的面积和中心。
4. **参数实验**：记录 5 组不同阈值下的误检/漏检情况，写进 `docs/preprocess-log.md`。

### 6.4 阶段验收

- [ ] 能解释 `cvtColor` 后数据为什么从 BGR 变为 HSV，H 为什么只到 179。
- [ ] 能根据场景选择固定阈值、Otsu 或自适应阈值，并说明理由。
- [ ] 能过滤面积过小的轮廓，不把噪点当目标。
- [ ] 能计算目标中心相对画面中心的偏移，并画出中心连线。
- [ ] 能在 1280×720 输入下处理速度达到自己设定的目标（先测基线，再优化）。

对应本仓库参考：`../2_3_image_processing.py`、`../2_4_color_detection.py`。

---

## 7. 阶段 3：视频流与工程化

### 7.1 摄像头读取

```cpp
cv::VideoCapture cap(0, cv::CAP_V4L2);  // Linux USB 相机
cap.set(cv::CAP_PROP_FRAME_WIDTH, 1280);
cap.set(cv::CAP_PROP_FRAME_HEIGHT, 720);
cap.set(cv::CAP_PROP_FPS, 30);

if (!cap.isOpened()) {
  std::cerr << "无法打开相机 /dev/video0\n";
  return 1;
}

cv::Mat frame;
while (cap.read(frame)) {
  if (frame.empty()) continue;

  // 处理 frame ...

  if (cv::waitKey(1) == 27) break;  // ESC 退出；无 GUI 时删掉这段
}
// VideoCapture 析构会自动 release；显式 cap.release() 也可以
```

常见后端：

- `cv::CAP_V4L2`：Linux USB 相机。
- `cv::CAP_GSTREAMER`：需要 GStreamer 管线，海康/工业相机可用。
- 默认 `cv::VideoCapture(0)` 让 OpenCV 自选，便于先跑通。

### 7.2 视频文件与录像

```cpp
cv::VideoCapture cap("input.mp4");
cv::VideoWriter writer(
    "output.mp4",
    cv::VideoWriter::fourcc('m', 'p', '4', 'v'),
    30.0,
    frame.size());

if (!writer.isOpened()) {
  std::cerr << "VideoWriter 打开失败，检查编码器/路径\n";
}
```

`mp4v` 不一定在所有平台可用；失败时尝试 `avc1` 或用 `ffmpeg` 后处理。不要假设写出的文件一定能播放，写完要实际打开验证。

### 7.3 用 RAII 管理相机

```cpp
class Camera {
 public:
  explicit Camera(int index)
      : cap_(index, cv::CAP_V4L2) {
    if (!cap_.isOpened()) {
      throw std::runtime_error("camera open failed");
    }
  }

  bool read(cv::Mat& frame) { return cap_.read(frame); }

 private:
  cv::VideoCapture cap_;
};
```

好处：无论正常退出还是抛异常，`cap_` 都会释放设备，避免“相机被占用”。

### 7.4 性能计时

```cpp
#include <chrono>

const auto t0 = std::chrono::steady_clock::now();
// ... 预处理或推理 ...
const auto t1 = std::chrono::steady_clock::now();
const double ms =
    std::chrono::duration<double, std::milli>(t1 - t0).count();
```

或者处理整段视频时用：

```cpp
cv::TickMeter tm;
tm.start();
// ... 循环 ...
tm.stop();
std::cout << "FPS=" << tm.getFPS() << " 平均=" << tm.getTimeMilli() << " ms\n";
```

要分段记录：**读帧、预处理、推理、绘制、发布**，否则不知道瓶颈在哪。

### 7.5 阶段实作

- 摄像头实时预览 + `q`/ESC 退出。
- 在画面上叠加 FPS、分辨率、处理耗时。
- 按 `s` 保存当前帧，按 `r` 开始/停止录像。
- 连续运行 10 分钟，观察内存和相机是否掉线。
- 无 GUI 环境下不要调用 `imshow`，改成保存图片或用 ROS2 发布。

### 7.6 阶段验收

- [ ] 摄像头打不开时给出明确错误，不崩溃。
- [ ] 能解释 `waitKey(0)` 为什么会让视频卡住。
- [ ] 能统计并打印端到端 FPS。
- [ ] 能保存一段可播放的视频和单帧图片。
- [ ] 拔掉相机/读到坏帧时，程序能安全退出。

对应本仓库参考：`../2_2_camera_display.py`。

---

## 8. 阶段 4：ROS2 C++ 视觉节点

### 8.1 先补 ROS2 基础

必须会：

- `ros2 node list`、`ros2 topic list/info/hz/echo`。
- Publisher/Subscriber、消息类型、`ament_cmake` 包。
- QoS：`SensorDataQoS`（best effort）与 reliable 的兼容性。
- 参数 `declare_parameter/get_parameter`，YAML 参数文件。
- launch 文件、`ros2 bag record/play`。
- RViz2 的 Image display 或 `rqt_image_view`。

不必在视觉阶段深入：自定义 action、生命周期节点、复杂 TF 树。掌握基本节点后先跑通图像链路。

### 8.2 话题契约先定好

| 方向 | 话题 | 类型 | QoS 建议 |
| --- | --- | --- | --- |
| 订阅 | `/camera/image_raw` 或 `/raw/image` | `sensor_msgs/Image` | `SensorDataQoS().keep_last(1)` |
| 发布 | `/vision/annotated` | `sensor_msgs/Image` | 与订阅端一致，best effort |
| 发布 | `/vision/detections` | `vision_msgs/Detection2DArray` | reliable 或 best effort，按下游需求 |
| 兼容旧接口 | `/vision/results_matrix` | `std_msgs/Float32MultiArray` | `n×3: [class, dx, dy]` |

> 海康相机驱动发布的是 `/raw/image`，普通 USB 相机常用 `/camera/image_raw`。**先用 `ros2 topic list` 查真实话题，不要猜。**

### 8.3 创建 C++ 包

```bash
cd ~/ros2_ws/src
ros2 pkg create cpp_vision_node \
  --build-type ament_cmake \
  --dependencies rclcpp sensor_msgs cv_bridge image_transport

cd ~/ros2_ws
colcon build --packages-select cpp_vision_node \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

### 8.4 最小可用的 C++ 图像节点

`src/vision_node.cpp`：

```cpp
#include <cv_bridge/cv_bridge.h>
#include <opencv2/imgproc.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/image_encodings.hpp>
#include <sensor_msgs/msg/image.hpp>

#include <functional>
#include <memory>

class VisionNode final : public rclcpp::Node {
 public:
  VisionNode() : Node("cpp_vision_node") {
    const auto qos = rclcpp::SensorDataQoS().keep_last(1);

    sub_ = create_subscription<sensor_msgs::msg::Image>(
        "/camera/image_raw", qos,
        std::bind(&VisionNode::on_image, this, std::placeholders::_1));

    pub_ = create_publisher<sensor_msgs::msg::Image>(
        "/vision/annotated", qos);

    RCLCPP_INFO(get_logger(), "cpp_vision_node ready");
  }

 private:
  void on_image(const sensor_msgs::msg::Image::ConstSharedPtr msg) {
    cv_bridge::CvImagePtr cv_ptr;
    try {
      cv_ptr = cv_bridge::toCvCopy(
          msg, sensor_msgs::image_encodings::BGR8);
    } catch (const cv_bridge::Exception& e) {
      RCLCPP_ERROR_THROTTLE(get_logger(), *get_clock(), 2000,
                            "cv_bridge 转换失败: %s", e.what());
      return;
    }

    cv::Mat out = cv_ptr->image;
    cv::putText(out, "C++ vision", {20, 40},
                cv::FONT_HERSHEY_SIMPLEX, 1.0,
                cv::Scalar(0, 255, 0), 2);

    cv_bridge::CvImage bridge;
    bridge.header = msg->header;  // 必须继承原时间戳/坐标系
    bridge.encoding = sensor_msgs::image_encodings::BGR8;
    bridge.image = out;

    auto out_msg = bridge.toImageMsg();
    pub_->publish(*out_msg);
  }

  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<VisionNode>());
  rclcpp::shutdown();
  return 0;
}
```

`CMakeLists.txt` 关键片段：

```cmake
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)

add_executable(vision_node src/vision_node.cpp)
target_include_directories(vision_node PRIVATE ${OpenCV_INCLUDE_DIRS})
ament_target_dependencies(vision_node rclcpp sensor_msgs cv_bridge)
target_link_libraries(vision_node PRIVATE ${OpenCV_LIBS})

install(TARGETS vision_node DESTINATION lib/${PROJECT_NAME})
ament_package()
```

`package.xml` 至少包含：

```xml
<depend>rclcpp</depend>
<depend>sensor_msgs</depend>
<depend>cv_bridge</depend>
<depend>libopencv-dev</depend>
```

### 8.5 `cv_bridge` 的 C++ 要点

**ROS2 → OpenCV**：

```cpp
auto cv_ptr = cv_bridge::toCvCopy(
    msg, sensor_msgs::image_encodings::BGR8);
cv::Mat bgr = cv_ptr->image;
```

- `toCvCopy`：复制一份，安全，推荐默认使用。
- `toCvShare`：与消息共享图像内存，性能更好；使用期间原消息必须存活，不能把图像指针长期缓存，且编码不匹配时仍可能发生转换。
- 目标编码写 `"bgr8"`，不是 `"rgb8"`，除非你明确要 RGB。
- 海康相机可能输出 Bayer 格式；`cv_bridge` 不一定自动转 BGR。应在驱动端设 RGB8/BGR8，或用 `cv::cvtColor` 的 Bayer 转换（如 `COLOR_BayerRG2BGR`）。

**OpenCV → ROS2**：

```cpp
cv_bridge::CvImage out;
out.header = msg->header;
out.encoding = sensor_msgs::image_encodings::BGR8;
out.image = annotated;
auto out_msg = out.toImageMsg();
pub_->publish(*out_msg);
```

必须保留 `header`，后续多传感器融合、时间同步、TF 查询都依赖它。

### 8.6 调试命令

```bash
# 终端 1：查看输入是否在发
ros2 topic hz /camera/image_raw

# 终端 2：运行节点
ros2 run cpp_vision_node vision_node

# 终端 3：查看输出
ros2 topic hz /vision/annotated
ros2 topic echo /vision/annotated --once

# 可视化
rviz2   # Add -> By topic -> /vision/annotated -> Image
# 或
rqt_image_view /vision/annotated
```

录一段 bag，后续没有相机也能调试：

```bash
ros2 bag record /camera/image_raw -o vision_test_bag
ros2 bag play vision_test_bag
```

### 8.7 阶段验收

- [ ] 节点启动后能在 RViz2 / rqt 中看到处理后的图像（文字或框）。
- [ ] `ros2 topic hz /camera/image_raw` 和 `/vision/annotated` 都有稳定频率。
- [ ] 订阅端 QoS 与相机端兼容；不因为 reliable/best effort 不匹配而“收不到图”。
- [ ] 发布图像 `header.stamp` 与输入一致。
- [ ] 图像转换异常只打印限流日志，不崩溃。
- [ ] 连续运行 10 分钟无内存持续增长。

对应本仓库参考：`../ros2_2_5_cv_bridge_convert.py`、`../ros2_3_2_yolo_node.py`。

---

## 9. 阶段 5：YOLO 基础、训练与导出

### 9.1 先建立正确概念

YOLO 是单阶段目标检测器：一次前向就输出候选框、类别和置信度。

```text
图像 → 预处理 → 神经网络 → 解码 → 置信度过滤 → NMS → 检测框
```

必须能解释：

| 概念 | 含义 | 部署时的影响 |
| --- | --- | --- |
| bbox | 检测框，常见 `xyxy` 或 `cx,cy,w,h` | 画框和计算偏移用 |
| confidence | 该框包含目标的把握，0～1 | 阈值越低召回高、误检多 |
| IoU | 两框交集/并集 | NMS 和 mAP 的基础 |
| NMS | 去掉重叠的重复框 | 必须按类别做，否则相邻类别互相压制 |
| Precision | 检出的框中多少是对的 | 误检代价高时关注 |
| Recall | 真实目标中被找到多少 | 漏检代价高时关注 |
| mAP50 | IoU=0.5 时的平均精度 | 常用汇报指标 |
| mAP50-95 | IoU 0.5～0.95 的平均 | 更严格，看定位质量 |

> 本框架以 **YOLOv8** 为例；YOLO11 等后续版本的训练/导出命令相近，但输出布局和算子支持要以实际 ONNX 为准，**不要盲目复用解码代码**。

### 9.2 训练为什么用 Python

C++ 生态里没有像 Ultralytics 一样成熟的“训练 + 数据增强 + 评估 + 导出”一条龙工具。工业界常见分工：

```text
Python：数据检查 → 训练 → 评估 → 导出 ONNX
C++：加载 ONNX/TensorRT → 实时推理 → 发布 ROS2 结果
```

这不是“C++ 不完整”，而是正确的工程分层。

### 9.3 先审计本仓库的数据（重要）

本仓库已有：

```text
../data/
├── dataset/
│   ├── images/train/    # 当前 1435 张
│   ├── images/val/      # 当前 771 张
│   ├── labels/train/    # 当前 1440 个 .txt（含 classes.txt）
│   └── labels/val/      # 当前 770 个 .txt
└── ../data.yaml
```

当前 `../data.yaml` 写的是 3 类（`red_block / blue_block / obstacle`），但已检查到：

- `labels/train/classes.txt` 里写的是 `stone`、`spear`，它只是类别名单，**不是 YOLO 标注文件**，放在标注目录里会污染数据，部分工具或自写校验脚本可能把它误当标签。
- 数值标注中实际出现的 class id 目前只有 `0` 和 `1`。
- 图片和标签数量不完全一一对应（train 1435 图 vs 1440 个 txt；val 771 图 vs 770 个 txt）。
- 标签目录里还有 `.bak` 文件，训练前应清理或移到单独目录。

**结论：训练前必须先统一“真实类别映射 + 干净的 labels 目录 + 一一对应的文件 stem”，否则指标没有意义。**

建议流程：

1. 备份 `data/`。
2. 把 `classes.txt`、`.bak` 移出 `labels/`。
3. 用脚本检查每个 `images/xxx.jpg` 是否有同名 `labels/xxx.txt`，列出多余/缺失。
4. 确认真实类别名后重写 `data.yaml`（建议用绝对路径或相对当前工作目录的路径）。
5. 先只训练 5 个 epoch，确认 loss/验证图正常，再跑完整训练。

`data.yaml` 的路径是相对**运行训练命令时的当前目录**解析的。当前文件里写的是 `./dataset/...`，所以要在 `data/` 目录下运行，或把路径改成正确的相对/绝对路径。

### 9.4 训练与评估

在 Python 训练环境（本仓库教程使用的是 Conda 环境 `cv`）中：

```bash
cd D:\project\vision_learning\data    # Windows 示例
yolo detect train \
  model=yolov8n.pt \
  data=data.yaml \
  epochs=100 \
  imgsz=640 \
  batch=8 \
  project=runs \
  name=cpp_baseline
```

评估：

```bash
yolo detect val \
  model=runs/detect/cpp_baseline/weights/best.pt \
  data=data.yaml \
  imgsz=640
```

训练报告至少记录：

- 每类的 P / R / mAP50 / mAP50-95。
- 混淆矩阵，确认类别是否被系统性混淆。
- 20 张验证集可视化结果，逐张看漏检/误检场景。
- 数据划分是否把同一段视频的相邻帧同时放进 train/val（会造成虚高指标）。

### 9.5 导出 ONNX

```bash
yolo export \
  model=runs/detect/cpp_baseline/weights/best.pt \
  format=onnx \
  imgsz=640 \
  opset=12 \
  dynamic=False \
  simplify=True
```

导出后做两件事：

1. 用 Python 对同一张图跑 `.pt` 和 `.onnx`，比较类别、置信度、框坐标。
2. 打印 ONNX 输出形状，记到部署笔记里。YOLOv8 默认静态 640 导出通常是 `[1, 4+nc, 8400]`；若你的模型是 `[1, 8400, 4+nc]`，解码时要转置。**以实际输出为准。**

### 9.6 阶段验收

- [ ] 能解释 confidence、IoU、NMS、mAP50 的区别。
- [ ] 数据审计通过，`data.yaml` 类别与标签一致。
- [ ] 训练完成并有完整的验证指标和可视化。
- [ ] 导出的 ONNX 与 `.pt` 在测试图上的结果基本一致。
- [ ] 知道模型输入是 RGB、归一化到 0～1、尺寸 640×640（以你的导出配置为准）。

对应本仓库参考：`../3_3_train_model.py`、`../3_4_yolo_inference.py`、`../data.yaml`、`../CV与YOLO目标检测入门教程.md`。

---

## 10. 阶段 6：C++ 推理与 ROS2 集成

### 10.1 推理后端怎么选

| 方案 | 优点 | 缺点 | 适用 |
| --- | --- | --- | --- |
| OpenCV DNN | 已有 OpenCV 依赖，API 简单，最快跑通 | 算子支持有限，性能一般，模型兼容性看版本 | 学习、CPU 基线、快速验证 |
| ONNX Runtime | 算子覆盖好，CPU/GPU 都可，C++ API 成熟 | 多一个依赖，需管理库和 provider | 通用生产部署，推荐进阶首选 |
| TensorRT | NVIDIA 上性能最好，可 FP16/INT8 | 与 GPU/驱动/版本强绑定，engine 不通用 | Jetson/RTX 实时项目 |

学习顺序：**OpenCV DNN 跑通 → ONNX Runtime 稳定部署 → 有明确性能需求再 TensorRT**。

### 10.2 完整推理流水线

```text
读图/收图
  → letterbox 到 640×640（保持比例，灰边填充 114）
  → BGR → RGB, /255.0
  → blob [1,3,640,640]
  → forward
  → 输出转置/解码
  → 置信度过滤
  → 按类别 NMS
  → 坐标还原（去 padding、除 scale）
  → 裁剪到原图范围
  → 画框 / 发布结构化结果
```

### 10.3 letterbox（不要直接拉伸）

```cpp
cv::Mat letterbox(const cv::Mat& src, const cv::Size& dst,
                  const cv::Scalar& color,
                  float& scale, int& pad_x, int& pad_y) {
  scale = std::min(dst.width / static_cast<float>(src.cols),
                   dst.height / static_cast<float>(src.rows));

  const int new_w = cvRound(src.cols * scale);
  const int new_h = cvRound(src.rows * scale);

  cv::Mat resized;
  cv::resize(src, resized, cv::Size(new_w, new_h), 0, 0,
             scale < 1.0F ? cv::INTER_AREA : cv::INTER_LINEAR);

  pad_x = (dst.width - new_w) / 2;
  pad_y = (dst.height - new_h) / 2;

  cv::Mat out;
  cv::copyMakeBorder(resized, out,
                     pad_y, dst.height - new_h - pad_y,
                     pad_x, dst.width - new_w - pad_x,
                     cv::BORDER_CONSTANT, color);
  return out;
}
```

```cpp
float scale = 1.0F;
int pad_x = 0, pad_y = 0;
cv::Mat input = letterbox(bgr, cv::Size(640, 640),
                          cv::Scalar(114, 114, 114),
                          scale, pad_x, pad_y);

cv::Mat blob;
cv::dnn::blobFromImage(input, blob, 1.0 / 255.0,
                       cv::Size(640, 640), cv::Scalar(),
                       /*swapRB=*/true,   // BGR → RGB
                       /*crop=*/false);   // 已 letterbox，不要再裁剪

net.setInput(blob);
cv::Mat output = net.forward();  // 先打印 shape，不要假设
```

### 10.4 解码与按类别 NMS

```cpp
// 以输出 [1, 4+nc, 8400] 为例
const int rows = output.size[1];
const int cols = output.size[2];
cv::Mat pred = output.reshape(1, rows);  // [4+nc, 8400]

std::vector<cv::Rect> boxes;
std::vector<float> scores;
std::vector<int> class_ids;

for (int i = 0; i < cols; ++i) {
  const float cx = pred.at<float>(0, i);
  const float cy = pred.at<float>(1, i);
  const float w  = pred.at<float>(2, i);
  const float h  = pred.at<float>(3, i);

  int best_cls = -1;
  float best_score = 0.0F;
  for (int c = 0; c < rows - 4; ++c) {
    const float s = pred.at<float>(4 + c, i);
    if (s > best_score) {
      best_score = s;
      best_cls = c;
    }
  }

  if (best_score < conf_threshold) continue;

  // 还原到原图坐标
  const int left = static_cast<int>((cx - 0.5F * w - pad_x) / scale);
  const int top  = static_cast<int>((cy - 0.5F * h - pad_y) / scale);
  const int width  = static_cast<int>(w / scale);
  const int height = static_cast<int>(h / scale);

  boxes.emplace_back(left, top, width, height);
  scores.push_back(best_score);
  class_ids.push_back(best_cls);
}
```

**NMS 必须按类别做**。`cv::dnn::NMSBoxes` 本身是类无关的；简单做法是：

```text
for each class c:
  收集 class_ids == c 的框和分数
  cv::dnn::NMSBoxes(..., conf_threshold, nms_threshold, keep)
  把 keep 映射回全局索引
```

最后对框做 `cv::Rect` 裁剪，避免负坐标/越界导致画图异常。

### 10.5 集成到 ROS2 节点

在 ROS2 节点里新增：

```cpp
declare_parameter<std::string>("model_path", "");
declare_parameter<double>("conf_threshold", 0.35);
declare_parameter<double>("nms_threshold", 0.45);

model_path_ = get_parameter("model_path").as_string();
conf_threshold_ = get_parameter("conf_threshold").as_double();
nms_threshold_ = get_parameter("nms_threshold").as_double();

net_ = cv::dnn::readNetFromONNX(model_path_);
net_.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
net_.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
```

结构建议：

- 模型只在构造函数加载一次，绝不能在每帧回调里 `readNetFromONNX`。
- 推理放在订阅回调，单线程执行器下天然串行；若使用多线程执行器，给推理回调加互斥或独立的 mutually exclusive callback group，因为 `cv::dnn::Net` 不是线程安全的。
- 队列只留 1 帧（`keep_last(1)`），实时系统宁可丢旧帧，也不要积压延迟。
- 发布检测结果时带回 `header`；`dx/dy = 框中心 - 画面中心`，与已有 Python 节点一致。
- 生产环境不要在回调里 `cv::imshow`；使用 RViz2 / rqt_image_view，或把调试图像单独发布。

启动示例：

```bash
ros2 run cpp_vision_node vision_node --ros-args \
  -p model_path:=/home/user/models/best.onnx \
  -p conf_threshold:=0.35 \
  -p nms_threshold:=0.45
```

### 10.6 与 Python 结果对齐

同一张图、同一模型、同一组阈值，按以下顺序排查：

1. 输入尺寸和 letterbox 是否一致。
2. BGR/RGB 是否交换正确。
3. 归一化是否是 `/255.0`，有没有均值/方差。
4. 输出是否需要转置。
5. 坐标是否忘了减 padding、除 scale。
6. 置信度阈值和 NMS 阈值是否一致。
7. NMS 是否按类别做。

验收标准：类别和数量一致，框坐标误差在几个像素内；不是“看起来差不多”。

### 10.7 本仓库海康相机链路

现有 ROS2 教程记录的海康相机 C++ 驱动：

- 节点：`hikvision_ros2_driver_node`
- 图像话题：`/raw/image`（`sensor_msgs/Image`）
- 启动文件：`hikvision_camera.launch.py`

把本文节点的输入话题改为 `/raw/image` 即可复用。若图像是 Bayer 格式，先在驱动端设为 RGB8/BGR8，或在 C++ 中显式做去马赛克；不要假设 `cv_bridge` 一定自动处理。

对应本仓库参考：`../ros2_3_2_yolo_node.py`、`../ros2_3_3_yolo_hik_cam_node.py`、`../基于ROS2的CV与YOLO目标检测使用教程.md`。

---

## 11. 毕业项目与验收标准

### 11.1 项目任务

**ROS2 实时目标检测与目标偏移发布**

- 输入：`/raw/image`（海康）或 `/camera/image_raw`（USB/bag）。
- 输出：
  - `/vision/annotated`：画框、类别、置信度、FPS 的图像。
  - `/vision/detections`：`vision_msgs/Detection2DArray`（推荐），或兼容旧接口的 `Float32MultiArray`，每行 `[class, dx, dy]`。
- 参数：`model_path`、`input_topic`、`conf_threshold`、`nms_threshold`、`publish_debug_image`。
- 配置：YAML + launch 文件。
- 日志：启动时打印模型路径、输入话题、OpenCV 版本、推理后端；异常限流。

### 11.2 必做验收

- [ ] `colcon build --packages-select cpp_vision_node --cmake-args -DCMAKE_BUILD_TYPE=Release` 一次通过。
- [ ] 用 bag 回放能稳定输出，不依赖某个特定相机。
- [ ] 连续运行 30 分钟，内存无持续增长，无崩溃。
- [ ] 无相机/无模型/空帧/错误编码都有明确日志和处理。
- [ ] 输入与输出 `header.stamp` 一致。
- [ ] 与 Python 基线在同一测试集上的类别、数量、框位置基本一致。
- [ ] 记录至少 300 帧的端到端延迟中位数和 P95。

### 11.3 性能记录模板

| 硬件 | 模型 | 输入 | 后端 | 预处理 ms | 推理 ms | 总延迟 ms | FPS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 例：i7-12700 / 无独显 | yolov8n.onnx | 640×640 | OpenCV DNN CPU | 3.2 | 45.0 | 52.0 | 19 |
| 例：RTX 3060 | yolov8n.onnx | 640×640 | ONNX Runtime CUDA | 2.8 | 8.0 | 12.0 | 80+ |

数字必须来自你自己的机器。不要用“理论上能到 60 FPS”写报告。

### 11.4 加分项（按需）

- ONNX Runtime CUDA / TensorRT FP16 加速，给出两种后端对比。
- 加入 ByteTrack/BoT-SORT 做目标 ID 跟踪。
- 相机标定 + 深度图/像素坐标转相机坐标，发布 3D 目标点。
- 使用 ROS2 component 与零拷贝（intra-process）降低大图传输开销。
- 增加单元测试：letterbox、坐标还原、NMS 过滤的纯函数测试。

---

## 12. 本仓库现有资料如何复用

| 现有文件 | C++ 对应任务 | 关键差异 |
| --- | --- | --- |
| [`../2_1_read_show_image.py`](../2_1_read_show_image.py) | `01_read_image.cpp` | `None` 检查改成 `.empty()`；`waitKey` 返回值处理 |
| [`../2_2_camera_display.py`](../2_2_camera_display.py) | `02_video.cpp` | RAII 管理 `VideoCapture`；区分相机与文件 |
| [`../2_3_image_processing.py`](../2_3_image_processing.py) | `03_preprocess.cpp` | numpy 数组 → `cv::Mat`；`clone()` 与 ROI 语义 |
| [`../2_4_color_detection.py`](../2_4_color_detection.py) | `04_color_detect.cpp` | `np.array` 阈值 → `cv::Scalar`；增加轮廓/中心 |
| [`../ros2_2_5_cv_bridge_convert.py`](../ros2_2_5_cv_bridge_convert.py) | 阶段 4 C++ 节点 | `CvBridge` → `cv_bridge`；`CvImage` 发布 |
| [`../ros2_3_2_yolo_node.py`](../ros2_3_2_yolo_node.py) | `06_yolo_node.cpp` | Ultralytics Python → ONNX C++ 推理 |
| [`../ros2_3_3_yolo_hik_cam_node.py`](../ros2_3_3_yolo_hik_cam_node.py) | 海康版本 C++ 节点 | 保留 `/raw/image`、`dx/dy` 结果矩阵 |
| [`../3_3_train_model.py`](../3_3_train_model.py) | Python 训练，不转 C++ | 训练仍用 Python；导出 ONNX |
| [`../3_4_yolo_inference.py`](../3_4_yolo_inference.py) | Python 基线 | 用来和 C++ 结果对齐 |
| [`../data.yaml`](../data.yaml) | 训练配置 | **当前类别与标签不一致，先审计** |
| [`../CV与YOLO目标检测入门教程.md`](../CV与YOLO目标检测入门教程.md) | 理论/YOLO 流程参考 | 原教程以 Python 为主 |
| [`../基于ROS2的CV与YOLO目标检测使用教程.md`](../基于ROS2的CV与YOLO目标检测使用教程.md) | ROS2 话题/海康链路参考 | 原教程以 Python 节点为例 |

### 建议的 C++ 练习顺序

```text
01_read_image      → 02_preprocess     → 03_color_detect
       → 04_video  → 05_cv_bridge_demo → 06_ros2_node
       → 07_yolo_single_image → 08_yolo_ros2_node
```

每完成一个，就在 `docs/progress.md` 记录：日期、运行命令、输入、输出、遇到的问题、耗时。

---

## 13. 常见坑与 FAQ

| 现象 | 常见原因 | 处理 |
| --- | --- | --- |
| `pkg-config: opencv4 not found` | 没装 `libopencv-dev` 或 PKG_CONFIG_PATH 不对 | `sudo apt install libopencv-dev`，`pkg-config --modversion opencv4` |
| 编译通过，运行报 OpenCV 符号错误 | 源码版 OpenCV 与 apt 版 `cv_bridge` ABI 冲突 | 统一用 apt 版，或重编译 `cv_bridge`；不要混用 |
| `imread` 返回空 | 路径错/权限/中文路径/工作目录不是你以为的目录 | 打印绝对路径；Windows 用 `imdecode` |
| `imshow` 崩溃或报 Qt 错 | 无显示器/无 GUI、SSH 环境 | 不要 `imshow`；改保存图片或 ROS2 发布 |
| 画面卡住 | `waitKey(0)` 放在视频循环里 | 实时循环用 `waitKey(1)` |
| ROS2 订阅收不到图 | QoS 不兼容、话题名错、相机没启动 | `ros2 topic info -v`；改用 `SensorDataQoS`；先 `ros2 topic hz` |
| `cv_bridge` 抛异常 | 编码不支持、step/通道数不匹配 | 指定 `bgr8`；确认相机输出格式；Bayer 显式转换 |
| 发布图像颜色不对 | RGB/BGR 混淆 | OpenCV 内部用 BGR；YOLO 输入才 `swapRB=true` |
| YOLO 框全错/偏移 | letterbox padding 未还原、输出未转置、坐标缩放错 | 按 10.6 顺序逐项对齐 |
| 检测框大量重复 | 没做 NMS 或没按类别做 | 按类别执行 NMS，调整 `nms_threshold` |
| 训练报 `Dataset not found` | `data.yaml` 路径相对当前工作目录 | 在 `data/` 下运行，或改成绝对路径 |
| 训练指标虚高 | 相邻视频帧泄漏到 val、类别映射错 | 按视频/场景划分，审计标签和类别 |
| FPS 很低 | 分辨率大、模型大、拷贝多、日志/绘图在回调里 | 降分辨率、换轻量模型、减少 clone、关闭调试显示 |
| 运行久了内存上涨 | 缓存帧、发布队列积压、Mat 生命周期错误 | QoS depth=1；不要在回调存 `toCvShare` 的图；用 valgrind/ASan |
| 相机占用打不开 | 另一个进程没释放 | `fuser /dev/video0`；确保 RAII/`release()` |
| `ros2 run` 找不到包 | 没 source 或没编译 | `source install/setup.bash`，重新 `colcon build` |

### 三个最容易被忽略的点

1. **时间戳**：视觉结果给控制/融合时，`header.stamp` 比“当前系统时间”重要。
2. **颜色顺序**：OpenCV BGR、YOLO RGB、ROS `rgb8/bgr8`，每一层都要确认。
3. **拷贝成本**：1280×720×3 一帧约 2.7 MB，多个 `clone()` 和高频发布会让延迟迅速上升。

---

## 14. 学习资源与最终检查清单

### 14.1 视频与文档

**主视频（C++ / OpenCV）：**

- [OpenCV4 C++ 快速入门视频30讲 - 系列合集（B 站，OpenCV学堂）](https://www.bilibili.com/video/BV1i54y1m7tw/)
  - 31 P，约 9 小时 39 分钟。
  - 建议观看顺序：`000-003` 环境/读写/色彩/Mat → `004-012` 像素操作/通道 → `013-022` 统计/绘制/缩放旋转/视频 → `023-029` 视频保存/直方图/卷积/模糊 → `030` 实时人脸检测。
  - 课程资料：<https://gitee.com/opencv_ai/opencv_tutorial_data>
  - 课程未覆盖：Canny、形态学、轮廓、ROS2、YOLO，按本文阶段 2/4/5/6 补齐。

**官方文档：**

- [OpenCV 4.x Tutorials](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html)
- [ROS2 Humble Tutorials](https://docs.ros.org/en/humble/Tutorials.html)
- [cv_bridge 包文档](https://docs.ros.org/en/humble/p/cv_bridge/)
- [Ultralytics YOLO Docs](https://docs.ultralytics.com/)
- [ONNX Runtime C++ API](https://onnxruntime.ai/docs/api/c/)

**本仓库配套：**

- [CV 与 YOLO 目标检测入门教程](../CV与YOLO目标检测入门教程.md)
- [基于 ROS2 的 CV 与 YOLO 目标检测使用教程](../基于ROS2的CV与YOLO目标检测使用教程.md)
- [数据集配置 data.yaml](../data.yaml)
- [数据集目录](../data/dataset/)

### 14.2 最终检查清单

#### 基础

- [ ] 能用 CMake 从空目录构建项目。
- [ ] 能解释 `cv::Mat` 浅拷贝、深拷贝、ROI。
- [ ] 能独立完成读取、灰度/HSV、滤波、边缘、二值化、形态学、轮廓。
- [ ] 能写 RAII 相机类，处理断流和退出。

#### ROS2

- [ ] 能创建 `ament_cmake` 包并 `colcon build`。
- [ ] 能写 C++ 图像订阅/发布节点，QoS 正确。
- [ ] 能用 `cv_bridge` 双向转换并保留 `header`。
- [ ] 能用参数、launch、rosbag 调试。
- [ ] 能在 RViz2 / rqt 中看到结果。

#### YOLO

- [ ] 能解释检测指标和 NMS。
- [ ] 完成数据审计，训练/验证集干净。
- [ ] 训练、评估、导出 ONNX 全流程走通。
- [ ] Python 和 C++ 对同一输入结果基本一致。

#### 工程

- [ ] C++ 节点连续运行 30 分钟稳定。
- [ ] 端到端延迟有数据、有硬件说明。
- [ ] README、参数、启动命令、话题契约齐全。
- [ ] 代码提交到 git，模型和大文件不进仓库。

### 14.3 今天就可以开始的三步

1. 安装环境，运行 `pkg-config --modversion opencv4`。
2. 打开主视频第 `000` 集，同时在 Ubuntu 上创建自己的 CMake 工程，不照抄 VS2017 步骤。
3. 完成 `01_read_image.cpp`：读一张图，打印尺寸/类型，转灰度保存，再用 `imshow` 显示。

> **记住**：这份框架的价值不在“看完”，而在你亲手写出的节点、测出的延迟、踩过并修好的坑。每学一个知识点，就把它变成 `cpp_vision_learning/src/` 里一个能运行的文件。

---

*最后更新：2026-11-02。参考当前工作区的 Python 教程、ROS2 教程、数据集与 `data.yaml`，并结合 ROS2 Humble / OpenCV 4.x / YOLOv8 的常见工程实践整理。*
