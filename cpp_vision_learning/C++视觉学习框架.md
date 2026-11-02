# C++ 视觉与目标检测学习框架

## 纯 C++ 路线：OpenCV + ROS2 + LibTorch + TinyYOLO

> **写给谁**：已经学会 ROS2 通信（节点、话题、QoS、参数、launch、colcon），但编程语言只学过 C++ 的学生。
>
> **核心约束**：训练、评估、推理、ROS2 部署全部使用 C++。不调用 Ultralytics，不使用 pip/conda，不要求会 Python。
>
> **最终成果**：用 C++ 从零写出一套可训练、可评估、可推理的 TinyYOLO 训练框架，并把它接入 ROS2 图像节点，输出检测框和目标偏移。
>
> **建议周期**：12 周，每周 10～15 小时。C++ 基础较弱就延长到 16 周，不要跳过训练循环和损失函数。

---

## 0. 先说清楚：纯 C++ 训练意味着什么

这条路和“用 Ultralytics 跑 YOLOv8”完全不同，必须先建立正确预期。

| 项目 | 纯 C++ 路线（本文） | Python + Ultralytics 路线（不使用） |
| --- | --- | --- |
| 训练语言 | C++ / LibTorch | Python |
| 模型 | 自建 TinyYOLO（YOLO 风格单阶段检测器） | 官方 YOLOv8 / YOLO11 |
| 预训练权重 | 默认从零训练 | 可直接加载 COCO 预训练权重 |
| 训练代码 | 自己写数据、模型、损失、训练循环、mAP | 框架封装，命令调用 |
| 部署 | C++ 加载同一套 LibTorch 模型 | 通常导出 ONNX/TensorRT |
| 优点 | 全链路可控、纯 C++、真正理解 YOLO 内部 | 上手快、精度高、生态成熟 |
| 代价 | 工作量大、精度上限取决于自己实现 | 需要 Python 工具链 |

### 必须接受的三个事实

1. **不是复刻 YOLOv8**。本文训练的是一个教学用的 YOLO 风格检测器 `TinyYOLO`，目的是把数据、网格、目标分配、损失、NMS、mAP 全部搞懂。它不是 Ultralytics 的权重兼容实现。
2. **没有现成的 COCO 预训练权重可以直接拿来微调**。你要在自己的数据集上从零训练。当前数据集只有两类、约两千张图，规模适合教学，但精度不会一上来就很高。
3. **纯 C++ 训练不是“更高级”，而是“更底层”**。如果你只是要最快得到一个高精度 YOLO，纯 C++ 不是最短路径；如果你要掌握训练框架本身，这条路才成立。

> 本框架选择 **LibTorch**。OpenCV DNN 只能做推理，不能训练；TensorRT 也不是训练框架。C++ 里能同时完成“自动求导 + 优化器 + GPU 训练”的成熟方案，首选 LibTorch。

拿到真正可训练的 YOLO 风格模型，需要你亲手实现：

```text
数据集与标签
  → 图像预处理 / 数据增强
  → Tensor 组 batch
  → CNN 前向
  → 网格目标分配
  → 损失函数
  → 反向传播 + 优化器
  → 验证 / mAP
  → 保存 LibTorch checkpoint
  → C++ 推理 + ROS2 节点
```

### 🎥 主推荐视频（优先最新纯 C++ 版）

**[《实践才是学OpenCV图像处理的最好方法，练完这套完整版OpenCV C++实战案例比看100套教程强！》— B 站](https://www.bilibili.com/video/BV1CT2QBYEbv/)**

- **发布于 2025-12-09**，共 **91 P**，总时长约 **40 小时 40 分钟**。在本次检索范围内，这是截至 2026-11-02 能确认的、较新的完整 **C++ OpenCV** 课程。
- 内容是 C++：源码编译、`Mat` 内存布局/深浅拷贝、`ptr/at/迭代器` 遍历与性能测试、ROI、颜色转换、阈值、resize、`VideoCapture`/`VideoWriter` 源码分析、Qt 视频编辑器。
- 建议只看 **001～037** 的核心部分；**038～068** 是 Qt 视频编辑器（ROS2 路线可跳过）；**069～091** 是后附的深度学习理论，按需看。它**不教 ROS2 和 YOLO 训练**，这两块看本文和 LibTorch 文档。
- 注意：这是第三方合集上传，不是 OpenCV 官方账号，播放量也不高。代码以 OpenCV 官方文档和你自己的编译结果为准；如果视频失效，用下面的备选。
- **备选（更老但更精炼）**：[《OpenCV4 C++ 快速入门视频30讲 - 系列合集》— OpenCV学堂，31 P，约 9 小时 39 分钟](https://www.bilibili.com/video/BV1i54y1m7tw/)。2020 年发布，首集后来更新到 2023，版本不如上面新，但胜在体系清晰、口碑更好。

> **选课避坑**：B 站不少标着“2025/2026 最新 OpenCV 天花板”的高播放合集，前几集是 C++ 环境配置，后面从 `Numpy`、`pip`、`YOLOv5` 开始就是 Python 内容。纯 C++ 路线选课前，先翻目录：出现大量 Numpy/Python 章节的，不要当作 C++ 课。

> 纯 C++ 的 YOLO 训练没有同等质量的中文视频课。训练部分以 LibTorch 官方 C++ API、源码示例和本文的工程骨架为主，不要拿 Python 训练视频硬套。

---

## 目录

1. [学习目标与最终作品](#1-学习目标与最终作品)
2. [环境：ROS2 Humble + OpenCV + LibTorch](#2-环境ros2-humble--opencv--libtorch)
3. [12 周路线总览](#3-12-周路线总览)
4. [阶段 0：LibTorch 训练原语](#4-阶段-0libtorch-训练原语)
5. [阶段 1：OpenCV 预处理与数据审计](#5-阶段-1opencv-预处理与数据审计)
6. [阶段 2：C++ 数据管道](#6-阶段-2c-数据管道)
7. [阶段 3：TinyYOLO 模型](#7-阶段-3tinyyolo-模型)
8. [阶段 4：目标分配、损失与训练循环](#8-阶段-4目标分配损失与训练循环)
9. [阶段 5：评估、NMS 与推理程序](#9-阶段-5评估nms-与推理程序)
10. [阶段 6：接入 ROS2](#10-阶段-6接入-ros2)
11. [阶段 7：性能、稳定性与毕业项目](#11-阶段-7性能稳定性与毕业项目)
12. [本仓库资料与数据现状](#12-本仓库资料与数据现状)
13. [常见坑与 FAQ](#13-常见坑与-faq)
14. [资源与最终检查清单](#14-资源与最终检查清单)

---

## 1. 学习目标与最终作品

### 1.1 学完应该具备的能力

| 能力 | 可验证的表现 |
| --- | --- |
| LibTorch 工程 | 能用 CMake 链接 LibTorch，能解释 Tensor 的 shape/dtype/device |
| 自动求导 | 能手写 `forward → loss → backward → step`，知道 `zero_grad` 和 `NoGradGuard` |
| 数据处理 | 能用 C++ 读 YOLO 标签，做 letterbox、归一化、数据增强和 batch |
| 模型搭建 | 能用 `torch::nn::Module` 搭 CNN，输出 `[B,S,S,5+C]` |
| 目标分配 | 能把检测框分配到网格单元，并构造分类/置信度/坐标目标 |
| 损失函数 | 能解释并实现目标置信度损失、类别损失、坐标损失 |
| 训练调试 | 能先过拟合 16 张图，再扩大训练；能定位 loss 不降、NaN、全背景预测 |
| 评估 | 能实现按类别 NMS、IoU、Precision/Recall、mAP@0.5 |
| 部署 | 能把 C++ 模型加载进 ROS2 节点，保持实时性和时间戳 |
| 工程化 | 能保存/恢复 checkpoint，记录配置、指标、硬件和延迟 |

### 1.2 最终作品

你最终要交付四个 C++ 可执行程序：

```text
cpp_vision_learning/
├── vision_audit     # 数据审计：图片/标签一一对应、类别统计、非法框
├── vision_train     # 训练：读 JSON 配置，训练 TinyYOLO，保存 best checkpoint
├── vision_eval      # 评估：在 val 集上算 mAP50 / P / R
├── vision_infer     # 单图/视频推理：画框，验证训练结果
└── vision_node      # ROS2 节点：订阅图像，推理，发布带框图像和检测结果
```

一个完整闭环：

```text
相机 / rosbag
      │ sensor_msgs/Image
      ▼
/raw/image 或 /camera/image_raw
      │
      ▼
cv_bridge → cv::Mat → RGB Tensor → TinyYOLO
      │
      ├─ /vision/annotated：画框图像
      └─ /vision/detections：类别 + 置信度 + dx/dy
```

交付要求：

- 训练和推理使用**同一套**预处理、类别顺序、归一化、letterbox 参数。
- `vision_train` 不需要 Python 参与。
- 训练配置、类别名、输入尺寸、checkpoint 必须能对应上；换模型不能靠猜。
- ROS2 节点连续运行 30 分钟不崩溃、不持续涨内存。
- 用 rosbag 可复现，记录硬件、模型、分辨率、延迟和 FPS。

### 1.3 暂不追求

- 不复刻 YOLOv8/v11 的完整结构和官方精度。
- 不实现分布式训练、混合精度、量化、剪枝、TensorRT。
- 不做多机训练、复杂数据增强库、自动超参数搜索。
- 不深入反向传播的数学证明，但要理解每个 loss 在惩罚什么。
- 不覆盖 SLAM、三维视觉、相机标定。

这些都可以在完成本文的 TinyYOLO 之后继续扩展。

---

## 2. 环境：ROS2 Humble + OpenCV + LibTorch

### 2.1 推荐配置

| 项目 | 推荐值 | 说明 |
| --- | --- | --- |
| 系统 | Ubuntu 22.04 LTS | 与 ROS2 Humble 对齐 |
| ROS2 | Humble | 你已经会通信，本阶段只补图像链路 |
| 编译器 | GCC 11 | Ubuntu 22.04 默认，C++17 |
| 构建 | CMake ≥ 3.22 + `colcon` | 独立训练程序用 CMake，ROS2 节点用 `ament_cmake` |
| OpenCV | apt 的 4.5.4 | 与 `cv_bridge` 保持一致，不要随意源码覆盖 |
| 训练库 | LibTorch C++ | 必须选 **cxx11 ABI** 版本 |
| 配置解析 | `nlohmann/json` | 纯 C++ 头文件库，用于训练配置 |
| GPU | NVIDIA + 对应 CUDA 版 LibTorch（可选） | 没有 GPU 也能学，只是训练慢 |
| 语言标准 | C++17 | 使用 `std::filesystem`、`std::optional`、`std::chrono` |

### 2.2 安装 OpenCV 与 ROS2 视觉依赖

```bash
sudo apt update
sudo apt install -y \
  build-essential cmake git pkg-config \
  libopencv-dev \
  nlohmann-json3-dev \
  ros-humble-cv-bridge ros-humble-image-transport \
  ros-humble-rviz2 ros-humble-rqt-image-view

source /opt/ros/humble/setup.bash

pkg-config --modversion opencv4
ros2 pkg prefix cv_bridge
```

### 2.3 安装 LibTorch

从 PyTorch 官网的 LibTorch 下载页选择：

1. **LibTorch**（不是 Python 包）
2. Linux
3. CPU 或与你驱动匹配的 CUDA 版本
4. **cxx11 ABI** 版本

下载页：<https://pytorch.org/get-started/locally/>

解压到固定目录：

```bash
sudo mkdir -p /opt/libtorch
sudo unzip libtorch-*.zip -d /opt
# 确保存在:
ls /opt/libtorch/share/cmake/Torch/TorchConfig.cmake
```

> 解压后的顶层目录通常就叫 `libtorch`。如果你的路径是 `/opt/libtorch/libtorch`，后续 CMake 的 `CMAKE_PREFIX_PATH` 要指向真正包含 `share/cmake/Torch` 的那一层。

### 2.4 为什么必须选 cxx11 ABI

ROS2 Humble 在 Ubuntu 22.04 上用 GCC 11 构建，默认使用 `_GLIBCXX_USE_CXX11_ABI=1`。如果你拿的是 pre-cxx11 ABI 的 LibTorch，链接时会出现类似：

```text
undefined reference to std::__cxx11::basic_string<...>
```

不要通过随意加 `-D_GLIBCXX_USE_CXX11_ABI=0` 来“压住”错误，这会污染 ROS2 侧。处理原则：

- 优先下载 **cxx11 ABI** 的 LibTorch。
- 训练程序和 ROS2 节点使用同一个 LibTorch 包。
- Debug/Release 也要一致；LibTorch 的 Debug 和 Release ABI 不兼容。
- 实在需要源码编译 LibTorch，就用和 ROS2 相同的 ABI 配置编译，并留出足够磁盘和时间。

### 2.5 CMake 最小验证：LibTorch + OpenCV

`CMakeLists.txt`：

```cmake
cmake_minimum_required(VERSION 3.22)
project(cpp_vision_learning LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs highgui)
find_package(Torch REQUIRED)
find_package(nlohmann_json 3.10 REQUIRED)

# LibTorch 可能通过该变量传递 ABI/编译选项，必须在创建 target 前加上
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${TORCH_CXX_FLAGS}")

add_executable(torch_opencv_check apps/torch_opencv_check.cpp)
target_include_directories(torch_opencv_check PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(torch_opencv_check PRIVATE
  ${TORCH_LIBRARIES}
  ${OpenCV_LIBS}
  nlohmann_json::nlohmann_json
)
```

`apps/torch_opencv_check.cpp`：

```cpp
#include <iostream>
#include <opencv2/core.hpp>
#include <torch/torch.h>

int main() {
  std::cout << "OpenCV: " << CV_VERSION << '\n';
  std::cout << "LibTorch: " << TORCH_VERSION << '\n';
  std::cout << "CUDA available: " << torch::cuda::is_available() << '\n';

  auto x = torch::rand({2, 3});
  std::cout << x << '\n';
  return 0;
}
```

构建：

```bash
cmake -S . -B build \
  -DCMAKE_PREFIX_PATH=/opt/libtorch \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
./build/torch_opencv_check
```

如果这一关过不了，不要开始写 YOLO。先解决工具链。

### 2.6 环境验收

- [ ] `opencv4` 和 LibTorch 版本都能打印。
- [ ] CMake 能找到 `/opt/libtorch/share/cmake/Torch/TorchConfig.cmake`。
- [ ] Release 构建通过，运行不报符号错误。
- [ ] 知道自己的 LibTorch 是 CPU 还是 CUDA 版、是 cxx11 ABI 还是 pre-cxx11 ABI。
- [ ] `nvidia-smi` 能看到显卡（如果有 GPU），并确认驱动版本能支持所选 LibTorch 的 CUDA 版本。

---

## 3. 12 周路线总览

> 每周 10～15 小时。你已经会 ROS2 通信，所以 ROS2 只占约两周；主要时间花在 C++ 训练框架上。

| 周 | 主题 | 本周产出 | 验收 |
| --- | --- | --- | --- |
| 1 | LibTorch、Tensor、CMake、MLP 训练 | 能跑通一个 C++ 二分类小网络 | loss 下降，能解释 `backward/step` |
| 2 | OpenCV 预处理、数据审计工具 | 能统计图片/标签、画框检查数据 | 能说清当前数据集缺什么、类别是什么 |
| 3 | Dataset、letterbox、目标编码 | 一个 batch 能变成 `[B,3,416,416]` 和 `[B,26,26,5+C]` | 可视化目标单元和框，坐标不偏 |
| 4 | TinyYOLO 模型 | 前向输出 shape 正确 | 随机输入能跑，参数量可控 |
| 5 | 损失函数、过拟合小数据集 | 16 张图能明显过拟合 | loss 下降，输出框接近 GT |
| 6 | 完整训练、增强、checkpoint | 训练日志和 best checkpoint | 验证 loss 可复现，能加载 best 复现结果 |
| 7 | NMS、mAP、推理程序 | `vision_eval`、`vision_infer` | mAP 能算，画框正确 |
| 8 | ROS2 图像链路、`cv_bridge` | 能订阅图像并发布处理结果 | RViz2/rqt 能看到图 |
| 9 | LibTorch ROS2 节点 | 节点内置模型推理 | 单帧推理，参数可配 |
| 10 | 性能、稳定性、rosbag | 延迟表、30 分钟稳定性 | 不崩溃、不涨内存 |
| 11 | 毕业项目、错误分析、文档 | 完整 README 和指标报告 | 他人能按文档复现 |
| 12 | 缓冲/进阶：anchor、CIoU、多尺度 | 选做 | 能解释改进是否有效 |

### 每周固定节奏

```text
读文档 / 读源码        30%
手写 C++ + 调试        50%
记录实验与失败原因      10%
复盘 + git 提交        10%
```

每个模块必须有一个“可运行证据”：

- 一个可执行文件
- 一次 shape 检查
- 一张可视化结果
- 一条可复现的命令
- 一条实验记录

不要用“我看懂了”作为验收。

---

## 4. 阶段 0：LibTorch 训练原语

### 4.1 需要建立的 C++ 深度学习概念

| 概念 | 在 LibTorch 中的表现 | 你要会做什么 |
| --- | --- | --- |
| Tensor | `torch::Tensor` | 创建、reshape、切片、拼接、打印 shape |
| dtype | `torch::kFloat32`、`torch::kInt64` | 输入统一 float32，标签类别用 int64 |
| device | CPU / CUDA | 模型和数据必须在同一个 device |
| 自动求导 | `loss.backward()` | 理解计算图和梯度累积 |
| 优化器 | `torch::optim::AdamW` | `zero_grad` → `backward` → `step` |
| 模块 | `torch::nn::Module` | 用 `register_module` 注册层 |
| 训练/推理 | `train()` / `eval()` | 推理必须配合 `torch::NoGradGuard` |
| 保存 | `torch::save` / `torch::load` | 保存参数，不保存 Python 状态 |

### 4.2 先写一个可训练的最小网络

不要一上来写 YOLO。先用一个 MLP 验证整个训练闭环：

```cpp
#include <iostream>
#include <torch/torch.h>

struct NetImpl : torch::nn::Module {
  NetImpl() {
    fc1 = register_module("fc1", torch::nn::Linear(2, 16));
    fc2 = register_module("fc2", torch::nn::Linear(16, 1));
  }

  torch::Tensor forward(torch::Tensor x) {
    x = torch::relu(fc1->forward(x));
    return torch::sigmoid(fc2->forward(x));
  }

  torch::nn::Linear fc1{nullptr}, fc2{nullptr};
};
TORCH_MODULE(Net);

int main() {
  torch::manual_seed(42);
  auto model = Net();

  torch::optim::Adam optimizer(
      model->parameters(),
      torch::optim::AdamOptions(1e-2));

  // 简单的二维线性可分数据
  auto x = torch::rand({128, 2});
  auto y = (x.select(1, 0) + x.select(1, 1) > 1.0)
               .to(torch::kFloat32)
               .unsqueeze(1);

  for (int step = 0; step < 500; ++step) {
    optimizer.zero_grad();
    auto pred = model->forward(x);
    auto loss = torch::binary_cross_entropy(pred, y);
    loss.backward();
    optimizer.step();

    if (step % 50 == 0) {
      std::cout << "step=" << step
                << " loss=" << loss.item<float>() << '\n';
    }
  }
  return 0;
}
```

要亲手改三个参数看结果：

1. 学习率改成 `1e-5`：loss 会怎样？
2. 把 `zero_grad()` 注释掉：梯度会怎样累积？
3. 推理时不加 `NoGradGuard`：显存/内存是否持续增长？

### 4.3 训练循环的固定骨架

以后所有训练器都是这个结构：

```text
for epoch:
    model->train()
    for batch:
        optimizer.zero_grad()
        pred = model->forward(input)
        loss = criterion(pred, target)
        loss.backward()
        optimizer.step()
    model->eval()
    with NoGradGuard:
        validate()
    save_best_if_needed()
```

### 4.4 阶段验收

- [ ] 能说清 `Tensor` 的 shape、dtype、device。
- [ ] 能解释 `loss.backward()` 和 `optimizer.step()` 分别做什么。
- [ ] 能解释为什么要 `zero_grad()`，以及训练/验证模式区别。
- [ ] MLP 的 loss 能从初始值明显下降。
- [ ] 能用 `torch::save` 保存并在另一个进程加载。

---

## 5. 阶段 1：OpenCV 预处理与数据审计

### 5.1 本阶段只学机器人视觉需要的 OpenCV

你已经会 C++，不需要把 OpenCV 所有函数背下来。先掌握：

| 目的 | 函数 | 关键点 |
| --- | --- | --- |
| 读图 | `cv::imread` | 失败返回空 `Mat`，必须检查 `.empty()` |
| 颜色 | `cv::cvtColor` | OpenCV 默认 BGR；YOLO 输入要 RGB |
| 缩放 | `cv::resize` | 缩小优先 `INTER_AREA`，放大 `INTER_LINEAR` |
| 填充 | `cv::copyMakeBorder` | letterbox 保持宽高比，常用灰边 114 |
| 归一化 | `cv::Mat::convertTo` | 转 `CV_32FC3` 并乘 `1/255.0` |
| 画图 | `rectangle`、`circle`、`putText` | 颜色是 BGR，坐标整数 |
| 滤波/边缘 | `GaussianBlur`、`Canny` | 调试和传统视觉仍会用到 |
| 轮廓 | `findContours` | 处理颜色目标、数据检查辅助 |
| 视频 | `VideoCapture`、`VideoWriter` | RAII 释放，检查 `isOpened()` |
| 显示 | `imshow`、`waitKey` | 无 GUI 环境不要调用 |

### 5.2 从 `cv::Mat` 到 `torch::Tensor`

这是训练和推理共用的关键函数，必须只写一份：

```cpp
torch::Tensor mat_to_tensor(const cv::Mat& rgb) {
  CV_Assert(rgb.type() == CV_32FC3);
  CV_Assert(rgb.isContinuous());

  // from_blob 不拥有像素内存，clone 后才能脱离 cv::Mat 生命周期
  return torch::from_blob(
             rgb.data,
             {rgb.rows, rgb.cols, 3},
             torch::kFloat32)
      .permute({2, 0, 1})     // HWC -> CHW
      .contiguous()
      .clone();
}
```

颜色转换顺序：

```cpp
cv::Mat rgb;
cv::cvtColor(bgr, rgb, cv::COLOR_BGR2RGB);

cv::Mat rgb_f32;
rgb.convertTo(rgb_f32, CV_32FC3, 1.0 / 255.0);

auto tensor = mat_to_tensor(rgb_f32);  // [3,H,W]
```

> 训练、评估、ROS2 推理必须使用完全相同的颜色、缩放、归一化顺序。这里差一步，模型就会“训练正常、部署乱框”。

### 5.3 先审计数据，不要急着训练

当前仓库的数据在：

```text
../data/
├── dataset/
│   ├── images/train/    # 当前 1435 张
│   ├── images/val/      # 当前 771 张
│   ├── labels/train/    # 当前 1440 个 .txt（含 classes.txt）
│   └── labels/val/      # 当前 770 个 .txt
└── ../data.yaml
```

已检查到的现状（以你开始训练时的目录为准）：

- `labels/train/classes.txt` 写的是 `stone`、`spear`。它是类别名单，**不是 YOLO 标签文件**，放在 labels 目录里会干扰工具。
- 有效数值标签中只出现了 class `0` 和 `1`，共约 1430 个目标。
- 每个有效标签文件里目前基本只有 1 个目标；另有 9 个文件没有有效目标（背景图）。
- train 图片 1435 张，但 train 下有 1440 个 `.txt`（含 `classes.txt`）；val 图片 771 张，标签 770 个。图片和标签没有严格一一对应。
- 标签目录里还有 `.bak` 文件。
- 当前 `../data.yaml` 写的是 3 类（`red_block / blue_block / obstacle`），与标签中的 2 类不一致。

**结论：不要直接拿现有 `data.yaml` 去训练。先写 C++ 审计工具，确认类别映射、清理目录、建立图片和标签的一一对应关系。**

### 5.4 数据审计工具的职责

写一个 `vision_audit`，输入数据集根目录，输出：

- 图片数量、标签数量、缺失标签的图片、无图片的标签。
- 非法标签行（字段不为 5、类别越界、坐标不在 `[0,1]`）。
- 空标签（背景图）数量和文件名。
- 每个类别的目标数量。
- 图片尺寸分布。
- 被误放进 labels 的非标注文件（`classes.txt`、`.bak`）。
- 一个 CSV 或 JSON 报告，供训练前复核。

建议接口：

```bash
./build/vision_audit \
  --images ../data/dataset/images \
  --labels ../data/dataset/labels \
  --classes stone,spear \
  --output ../runs/audit.json
```

C++ 实现只需要：

- `std::filesystem::directory_iterator`
- `std::ifstream` 读 `.txt`
- `cv::imread` 读图，检查尺寸
- `std::map` / `std::unordered_map` 统计
- `nlohmann::json` 输出报告

### 5.5 建立你自己的训练配置

LibTorch 训练器不需要 `data.yaml`。确认类别后写 `configs/dataset.json`：

```json
{
  "data_root": "../data/dataset",
  "train_images": "images/train",
  "train_labels": "labels/train",
  "val_images": "images/val",
  "val_labels": "labels/val",
  "classes": ["stone", "spear"],
  "input_size": 416,
  "num_classes": 2
}
```

注意：

- `classes` 的顺序就是网络输出类别的顺序，必须和标签 id 一致。
- 不要同时保留“3 类配置”和“2 类标签”。
- 9 张背景图不能删掉；它们能帮助模型学习“没有目标”的情况。前提是训练器正确处理空标签。
- 如果后续增加类别，必须从 checkpoint 开始重训或至少重建分类头，不能直接换配置加载旧权重。

### 5.6 阶段验收

- [ ] 能说清 `BGR → RGB → HWC → CHW → 归一化` 的顺序。
- [ ] 能解释 `from_blob` 为什么要 `clone()`。
- [ ] `vision_audit` 能输出图片/标签对应关系、类别统计、非法标签。
- [ ] 能画出 20 张训练图及 GT 框，用肉眼确认框和类别正确。
- [ ] `configs/dataset.json` 的类别数与标签一致。

---

## 6. 阶段 2：C++ 数据管道

### 6.1 统一的数据结构

```cpp
struct Box {
  float cx;   // 归一化中心 x，相对输入图
  float cy;
  float w;    // 归一化宽
  float h;
  int cls;
};

struct Sample {
  torch::Tensor image;   // [3,416,416], float32, 0~1
  torch::Tensor target;  // [26,26,5+C], float32
};
```

所有坐标统一使用 **相对输入图归一化的 `cx,cy,w,h`**。不要让一部分代码用像素、一部分用归一化，这是检测项目最常见的 bug 来源。

### 6.2 letterbox：保持比例再填充

```cpp
struct LetterboxResult {
  cv::Mat image;
  float scale;
  int pad_x;
  int pad_y;
};

LetterboxResult letterbox(const cv::Mat& src, int dst_size) {
  const float scale = std::min(
      dst_size / static_cast<float>(src.cols),
      dst_size / static_cast<float>(src.rows));

  const int new_w = cvRound(src.cols * scale);
  const int new_h = cvRound(src.rows * scale);

  cv::Mat resized;
  cv::resize(src, resized, cv::Size(new_w, new_h), 0, 0,
             scale < 1.0F ? cv::INTER_AREA : cv::INTER_LINEAR);

  const int pad_x = (dst_size - new_w) / 2;
  const int pad_y = (dst_size - new_h) / 2;

  cv::Mat out;
  cv::copyMakeBorder(resized, out,
                     pad_y, dst_size - new_h - pad_y,
                     pad_x, dst_size - new_w - pad_x,
                     cv::BORDER_CONSTANT, cv::Scalar(114, 114, 114));
  return {out, scale, pad_x, pad_y};
}
```

假设原图 `540×960`，输入 `416×416`：

- `scale = min(416/540, 416/960) = 0.4333`
- 缩放后约 `234×416`
- 左右各补约 `91` 像素

目标框必须做同样的变换：

```text
原图像素坐标 → 乘 scale → 加 pad → 除以 416 → 归一化
```

### 6.3 标签解析和增强

标签一行格式：

```text
class cx cy w h
```

解析时检查：

- 正好 5 个字段。
- `class` 在 `[0, C)`。
- `cx,cy,w,h` 在 `[0,1]`。
- 框面积大于 0。

数据增强第一版只做**水平翻转**：

```cpp
if (flip) {
  cv::flip(bgr, bgr, 1);
  for (auto& box : boxes) {
    box.cx = 1.0F - box.cx;
  }
}
```

先不要加旋转、马赛克、MixUp。增强越复杂，越难判断是数据问题还是训练问题。

后续可以加：

- 随机亮度/对比度
- 小范围缩放和平移（同步变换框）
- 随机 HSV 扰动

每一次增强都要可视化检查：框是否还贴着目标。

### 6.4 目标张量：单个网格单元

本文的 TinyYOLO 采用**每个网格单元预测一个框**的简化设计：

- 输入 `416×416`
- 总下采样 stride = 16
- 网格 `S = 26`
- 每个 cell 输出 `5 + C` 个值：
  - `tx, ty`：cell 内偏移，推理时用 sigmoid
  - `tw, th`：目标宽高的平方根，推理时平方还原
  - `obj`：有目标的 logit
  - `cls[0..C-1]`：类别 logits

目标张量 `[S,S,5+C]` 的编码：

```cpp
torch::Tensor encode_target(const std::vector<Box>& boxes,
                            int S, int C) {
  auto target = torch::zeros({S, S, 5 + C}, torch::kFloat32);
  auto acc = target.accessor<float, 3>();

  for (const auto& b : boxes) {
    int gx = std::clamp(static_cast<int>(b.cx * S), 0, S - 1);
    int gy = std::clamp(static_cast<int>(b.cy * S), 0, S - 1);

    // 简化模型每个 cell 只放一个目标；本数据集当前正好是单目标
    if (acc[gy][gx][4] > 0.5F) continue;

    acc[gy][gx][0] = b.cx * S - gx;  // [0,1)
    acc[gy][gx][1] = b.cy * S - gy;
    acc[gy][gx][2] = std::sqrt(std::max(b.w, 1e-6F));
    acc[gy][gx][3] = std::sqrt(std::max(b.h, 1e-6F));
    acc[gy][gx][4] = 1.0F;           // objectness
    acc[gy][gx][5 + b.cls] = 1.0F;   // class
  }
  return target;
}
```

限制：

- 两个目标中心落到同一个 cell 时，这个简化模型只能保留一个。当前数据集基本是单目标，可以这样教学。
- 想做通用检测，需要每个 cell 多个 anchor/多个预测，或使用 anchor-free 的多层特征。放到毕业项目进阶。

### 6.5 Batch 组装

训练循环可以不用 `torch::data` 的模板，直接手写更直观：

```cpp
auto sample = dataset.get(index);
images.push_back(sample.image);
targets.push_back(sample.target);

auto image_batch = torch::stack(images).to(device);
auto target_batch = torch::stack(targets).to(device);
```

要求：

- 所有图片经过 letterbox 后尺寸一致。
- `target` 的 `S`、`C` 与模型一致。
- 训练时打乱索引；验证时固定顺序。
- 最后一个 batch 如果只有 1 张，使用 BatchNorm 时可能报错。可以丢弃最后不足 2 张的 batch，或把模型里的 BatchNorm 改为 GroupNorm。

### 6.6 阶段验收

- [ ] 能正确读取并校验所有标签。
- [ ] 能输出一个 batch 的 `images` shape `[B,3,416,416]`。
- [ ] 能输出 `target` shape `[B,26,26,5+C]`。
- [ ] 把 GT 框和正样本 cell 可视化，确认没有整体偏移。
- [ ] 随机翻转后，框仍与目标对齐。
- [ ] 空标签图片会生成全零 target，训练不会崩溃。

---

## 7. 阶段 3：TinyYOLO 模型

### 7.1 设计目标

这是一个**教学用、可训练、可部署**的单阶段检测器，不追求 SOTA：

| 项目 | 选择 |
| --- | --- |
| 输入 | `416×416×3`，RGB，0～1 |
| Backbone | 5 个卷积块，stride 16 下采样 |
| 特征图 | `26×26` |
| 每个 cell | 1 个框 + 1 个 objectness + C 个类别 |
| 输出 | `[B,26,26,5+C]` |
| 参数量 | 小，适合从零训练和 CPU 调试 |
| 能力 | 单目标、规则场景、教学数据 |
| 局限 | 多目标重叠、小目标、密集场景表现有限 |

### 7.2 网络结构

```text
Input [B,3,416,416]
  → Conv 3→16, stride 2, BN, LeakyReLU      [B,16,208,208]
  → Conv 16→32, stride 2, BN, LeakyReLU     [B,32,104,104]
  → Conv 32→64, stride 2, BN, LeakyReLU     [B,64,52,52]
  → Conv 64→128, stride 2, BN, LeakyReLU    [B,128,26,26]
  → Conv 128→128, stride 1, BN, LeakyReLU   [B,128,26,26]
  → Conv 128→(5+C), 1×1                     [B,5+C,26,26]
  → permute                                 [B,26,26,5+C]
```

### 7.3 模型代码骨架

```cpp
struct ConvBlockImpl : torch::nn::Module {
  ConvBlockImpl(int in_ch, int out_ch, int stride = 1) {
    conv = register_module("conv", torch::nn::Conv2d(
        torch::nn::Conv2dOptions(in_ch, out_ch, 3)
            .stride(stride)
            .padding(1)
            .bias(false)));
    bn = register_module("bn", torch::nn::BatchNorm2d(
        torch::nn::BatchNorm2dOptions(out_ch)));
  }

  torch::Tensor forward(torch::Tensor x) {
    return torch::leaky_relu(bn->forward(conv->forward(x)), 0.1);
  }

  torch::nn::Conv2d conv{nullptr};
  torch::nn::BatchNorm2d bn{nullptr};
};
TORCH_MODULE(ConvBlock);

struct TinyYOLOImpl : torch::nn::Module {
  explicit TinyYOLOImpl(int num_classes)
      : num_classes_(num_classes) {
    conv1 = register_module("conv1", ConvBlock(3, 16, 2));
    conv2 = register_module("conv2", ConvBlock(16, 32, 2));
    conv3 = register_module("conv3", ConvBlock(32, 64, 2));
    conv4 = register_module("conv4", ConvBlock(64, 128, 2));
    conv5 = register_module("conv5", ConvBlock(128, 128, 1));

    head = register_module("head", torch::nn::Conv2d(
        torch::nn::Conv2dOptions(128, 5 + num_classes, 1)));
  }

  torch::Tensor forward(torch::Tensor x) {
    x = conv1->forward(x);
    x = conv2->forward(x);
    x = conv3->forward(x);
    x = conv4->forward(x);
    x = conv5->forward(x);
    x = head->forward(x);          // [B,5+C,S,S]
    return x.permute({0, 2, 3, 1}); // [B,S,S,5+C]
  }

  int num_classes_;
  ConvBlock conv1{nullptr}, conv2{nullptr}, conv3{nullptr};
  ConvBlock conv4{nullptr}, conv5{nullptr};
  torch::nn::Conv2d head{nullptr};
};
TORCH_MODULE(TinyYOLO);
```

### 7.4 shape 单元测试

每改一次网络，都先做 shape 检查：

```cpp
auto model = TinyYOLO(2);
auto input = torch::rand({4, 3, 416, 416});
auto output = model->forward(input);

TORCH_CHECK(output.dim() == 4);
TORCH_CHECK(output.size(0) == 4);
TORCH_CHECK(output.size(1) == 26);
TORCH_CHECK(output.size(2) == 26);
TORCH_CHECK(output.size(3) == 5 + 2);

std::cout << output.sizes() << '\n';
```

还要检查：

- CPU 输入能跑，CUDA 输入能跑（如有 GPU）。
- batch=1 和 batch>1 都能跑。
- 模型参数数量不要突然爆炸。
- 训练和推理输出 shape 一致。

### 7.5 初始化建议

目标检测的 objectness 初始输出如果太“自信”，会产生大量正样本误报。可以在训练开始前把 objectness 的 bias 设为负值：

```cpp
torch::NoGradGuard no_grad;
head->bias.narrow(0, 4, 1).fill_(-4.0);
```

这只是稳定训练的工程技巧，不是必须。先跑通，再比较加与不加的效果。

### 7.6 阶段验收

- [ ] 能画出网络结构和每层输出 shape。
- [ ] 随机输入输出 `[B,26,26,5+C]`。
- [ ] 能解释为什么要 `permute` 成 NHWC 与 target 对齐。
- [ ] 能解释每个 cell 的 5+C 个值分别是什么。
- [ ] 能在 CPU 上完成一次前向，不出现 shape 错误。

---

## 8. 阶段 4：目标分配、损失与训练循环

### 8.1 目标分配

对一个 GT 框：

1. 计算中心 `cx,cy`（已归一化到输入图）。
2. 网格坐标 `gx = floor(cx*S)`，`gy = floor(cy*S)`。
3. 该 cell 的 objectness 目标 = 1。
4. 该 cell 的类别目标 = 对应 one-hot。
5. 该 cell 的坐标目标：
   - `tx_target = cx*S - gx`
   - `ty_target = cy*S - gy`
   - `tw_target = sqrt(w)`
   - `th_target = sqrt(h)`

推理时反向还原：

```text
cx = (gx + sigmoid(tx)) / S
cy = (gy + sigmoid(ty)) / S
w  = clamp(tw, 0, 1)^2
h  = clamp(th, 0, 1)^2
```

### 8.2 损失函数

本文使用一个可解释的混合损失：

```text
总损失 = 5 × 坐标损失 + 置信度损失 + 类别损失
```

- **坐标损失**：只对正样本 cell 计算。
  - `tx,ty` 用 sigmoid 后与目标偏移做 MSE。
  - `tw,th` 直接与 `sqrt(w), sqrt(h)` 做 MSE。
- **置信度损失**：对所有 cell 计算 BCEWithLogits。
  - 正样本极少，负样本极多，需要 `pos_weight` 或 focal loss。
- **类别损失**：只对正样本 cell 计算交叉熵。

关键片段：

```cpp
struct LossResult {
  torch::Tensor total;
  torch::Tensor box;
  torch::Tensor obj;
  torch::Tensor cls;
};

LossResult yolo_loss(const torch::Tensor& pred,
                     const torch::Tensor& target,
                     int num_classes,
                     float obj_pos_weight = 10.0F) {
  auto pos = target.select(-1, 4).gt(0.5);  // [B,S,S]
  const bool has_pos = pos.any().item<bool>();

  auto zero = torch::zeros({}, pred.options());

  torch::Tensor box_loss = zero;
  torch::Tensor cls_loss = zero;

  if (has_pos) {
    auto pred_xy = torch::sigmoid(pred.slice(-1, 0, 2));
    auto target_xy = target.slice(-1, 0, 2);
    auto xy_mask = pos.unsqueeze(-1).expand_as(pred_xy);
    auto loss_xy = torch::mse_loss(
        pred_xy.masked_select(xy_mask),
        target_xy.masked_select(xy_mask));

    auto pred_wh = pred.slice(-1, 2, 4);
    auto target_wh = target.slice(-1, 2, 4);
    auto wh_mask = pos.unsqueeze(-1).expand_as(pred_wh);
    auto loss_wh = torch::mse_loss(
        pred_wh.masked_select(wh_mask),
        target_wh.masked_select(wh_mask));

    box_loss = loss_xy + loss_wh;

    auto cls_logits = pred.slice(-1, 5, 5 + num_classes);
    auto cls_target = target.slice(-1, 5, 5 + num_classes);
    auto cls_mask = pos.unsqueeze(-1).expand_as(cls_logits);
    auto logits_pos = cls_logits.masked_select(cls_mask)
                          .view({-1, num_classes});
    auto target_pos = cls_target.masked_select(cls_mask)
                          .view({-1, num_classes});
    cls_loss = torch::binary_cross_entropy_with_logits(
        logits_pos, target_pos);
  }

  auto obj_target = target.select(-1, 4);
  auto obj_loss = torch::binary_cross_entropy_with_logits(
      pred.select(-1, 4), obj_target,
      /*weight=*/torch::Tensor(),
      /*reduction=*/torch::Reduction::Mean,
      /*pos_weight=*/torch::tensor({obj_pos_weight}, pred.options()));

  auto total = 5.0 * box_loss + obj_loss + cls_loss;
  return {total, box_loss, obj_loss, cls_loss};
}
```

> 先确认这段代码能跑，再考虑 focal loss、CIoU、标签平滑。不要在第一次训练就同时改五个东西。

### 8.3 一个容易忽略的问题：正负样本极度不平衡

`26×26 = 676` 个 cell，一张图通常只有 1 个正样本。初始时网络会把所有 cell 预测为背景，loss 看起来下降，但一个框也检测不到。

对策：

1. 先确认 objectness 目标的编码正确。
2. 使用 `pos_weight`（例如 10～30）或 focal loss。
3. 观察每个 batch 的正样本数。
4. 先过拟合 16 张图，确认模型有能力学到正样本。
5. 训练时打印 `pos_count`，不要只看总 loss。

### 8.4 训练循环

```cpp
torch::Device device = torch::cuda::is_available()
                           ? torch::Device(torch::kCUDA)
                           : torch::Device(torch::kCPU);

auto model = TinyYOLO(cfg.num_classes);
model->to(device);

torch::optim::AdamW optimizer(
    model->parameters(),
    torch::optim::AdamWOptions(cfg.learning_rate)
        .weight_decay(cfg.weight_decay));

for (int epoch = 0; epoch < cfg.epochs; ++epoch) {
  model->train();
  std::shuffle(order.begin(), order.end(), rng);

  double running_loss = 0.0;
  int batches = 0;

  for (size_t start = 0; start < order.size();
       start += cfg.batch_size) {
    std::vector<torch::Tensor> images;
    std::vector<torch::Tensor> targets;

    const size_t end = std::min(order.size(), start + cfg.batch_size);
    for (size_t i = start; i < end; ++i) {
      auto sample = dataset.get(order[i], /*train=*/true);
      images.push_back(sample.image);
      targets.push_back(sample.target);
    }

    // BatchNorm 在训练模式下不适合 batch=1
    if (images.size() < 2) continue;

    auto image_batch = torch::stack(images).to(device);
    auto target_batch = torch::stack(targets).to(device);

    optimizer.zero_grad();
    auto pred = model->forward(image_batch);
    auto loss = yolo_loss(pred, target_batch, cfg.num_classes);

    if (!torch::isfinite(loss.total).item<bool>()) {
      throw std::runtime_error("loss is not finite");
    }

    loss.total.backward();
    optimizer.step();

    running_loss += loss.total.item<float>();
    ++batches;
  }

  // 每个 epoch 结束做验证，固定使用 eval 模式
  model->eval();
  double val_loss = validate(model, val_dataset, device, cfg);

  std::cout << "epoch=" << epoch
            << " train_loss=" << running_loss / std::max(1, batches)
            << " val_loss=" << val_loss << '\n';

  // 简化的学习率衰减：每 40 轮乘 0.5
  if ((epoch + 1) % 40 == 0) {
    for (auto& group : optimizer.param_groups()) {
      group.options().set_lr(group.options().get_lr() * 0.5);
    }
  }

  if (val_loss < best_val_loss) {
    best_val_loss = val_loss;
    torch::save(model, "models/tinyyolo_best.pt");
  }
}
```

> 上面是骨架，不是完整可编译工程。`dataset.get`、`validate`、配置结构需要你自己实现。重点是训练顺序和状态管理：`train()` → 前向/反向 → `eval()` + `NoGradGuard` → 保存。

### 8.5 训练前必须做的过拟合测试

不要直接训练 100 个 epoch。先：

1. 取 16 张训练图（确保包含两类目标，并混入 2～3 张背景图）。
2. 固定这 16 张，不做增强。
3. 训练 100～300 个 step。
4. 观察训练 loss 是否明显下降。
5. 用 `vision_infer` 或训练脚本里的可视化检查框是否贴近 GT。

如果 16 张图都过拟合不了，问题在：

- 标签坐标变换
- 目标分配
- 损失函数
- 学习率
- 输入归一化
- 类别映射

不要用“数据太少”解释，因为过拟合测试的目的就是排除数据规模问题。

### 8.6 保存和恢复

```cpp
// 保存
torch::save(model, "models/tinyyolo_best.pt");

// 加载
TinyYOLO model(2);
torch::load(model, "models/tinyyolo_best.pt");
model->to(device);
model->eval();
```

必须同时保存一个 `models/tinyyolo_best.json`：

```json
{
  "model": "tinyyolo",
  "input_size": 416,
  "grid_size": 26,
  "num_classes": 2,
  "classes": ["stone", "spear"],
  "normalize": "rgb_0_1",
  "letterbox_pad": 114
}
```

否则换一次配置，checkpoint 就可能加载到错误类别数上。

> 这个 `.pt` 是 **LibTorch C++ 模型的参数文件**，不是 Ultralytics 的 `.pt`，两者不能互换。不要试图让 `YOLO("tinyyolo_best.pt")` 读取它。

当前训练骨架只保存模型权重。要做到严格的“断点续训”，还需要额外保存优化器状态、epoch、随机数状态和 best 指标；第一版先把 best checkpoint 的保存、加载和结果复现做好，再考虑完整续训。

### 8.7 阶段验收

- [ ] 16 张图能明显过拟合，框接近 GT。
- [ ] loss 各分项都能打印，知道是哪一项在下降/爆炸。
- [ ] 能解释为什么要 `pos_weight`。
- [ ] 训练和验证的 `model->train()/eval()` 没有写反。
- [ ] 保存后换一个进程能加载并得到同样输出。
- [ ] 配置文件与 checkpoint 的类别数、输入尺寸一致。

---

## 9. 阶段 5：评估、NMS 与推理程序

### 9.1 解码预测

对每个 cell：

```cpp
const float obj = torch::sigmoid(pred[..., 4]).item<float>();
if (obj < conf_threshold) continue;

const int cls = pred[..., 5].argmax().item<int>();
const float cls_prob = softmax(pred[..., 5...]).max().item<float>();
const float score = obj * cls_prob;

const float cx = (gx + sigmoid(tx)) / S;
const float cy = (gy + sigmoid(ty)) / S;
const float w = std::pow(std::clamp(tw, 0.0F, 1.0F), 2);
const float h = std::pow(std::clamp(th, 0.0F, 1.0F), 2);
```

然后映射回原图：

```text
输入图像素坐标 = (归一化坐标 × input_size)
原图坐标 = (输入图像素坐标 - pad) / scale
```

最后裁剪到原图边界。

### 9.2 按类别 NMS

NMS 不能对所有类别混在一起做。否则“stone”和“spear”框重叠时，一个类别会把另一个类别压掉。

```text
for each class c:
  收集预测类别为 c 的框和分数
  cv::dnn::NMSBoxes(boxes, scores, conf, nms_iou, keep)
  把 keep 映射回全局检测结果
```

可以用 OpenCV 的 `cv::dnn::NMSBoxes`，不必自己重写。注意它本身是类无关的，所以外层必须按类别循环。

### 9.3 实现 mAP@0.5

评估流程：

1. 对 val 集每张图做推理，得到 `{box, score, cls}`。
2. 按类别分别处理。
3. 对每个类别，把该类的所有检测按 score 从高到低排序。
4. 逐一匹配 GT：IoU ≥ 0.5 且该 GT 未匹配，则 TP；否则 FP。
5. 累计 precision/recall，计算 all-point AP。
6. 对类别求平均，得到 mAP@0.5。

IoU：

```text
inter = max(0, min(x2a,x2b) - max(x1a,x1b)) *
        max(0, min(y2a,y2b) - max(y1a,y1b))
union = areaA + areaB - inter
IoU = inter / union
```

必须同时报告：

- 每类 AP
- mAP@0.5
- Precision / Recall
- 总检测数、TP/FP/FN
- 推理耗时

不要只贴一个 mAP 数字。

### 9.4 `vision_infer`

输入单张图片或视频，输出：

- 画框图片
- 终端打印：类别、置信度、`xyxy`、中心相对画面中心 `dx/dy`
- 可选：保存为视频

这个程序和 ROS2 节点应该共享 `preprocess()`、`decode()`、`nms()`，不要复制两份。

### 9.5 阶段验收

- [ ] 单张图片的画框位置正确，没有整体偏移。
- [ ] 按类别 NMS 生效，不会跨类压制。
- [ ] 能输出 `mAP@0.5` 和每类 AP。
- [ ] 推理结果与训练时的验证结果一致。
- [ ] 能对一段视频连续推理，速度可接受。

---

## 10. 阶段 6：接入 ROS2

> 你已经会 ROS2 通信，这里不重复节点、话题、QoS 的基础语法。本阶段只关注视觉链路。

### 10.1 架构

```text
相机驱动 / rosbag
      │ sensor_msgs/Image
      ▼
/raw/image 或 /camera/image_raw
      ▼
cpp_vision_node
      ├─ cv_bridge：Image → cv::Mat
      ├─ preprocess：BGR → RGB → letterbox → Tensor
      ├─ TinyYOLO：forward
      ├─ decode + NMS
      ├─ /vision/annotated：sensor_msgs/Image
      └─ /vision/detections：class + conf + dx/dy
```

话题契约：

| 方向 | 话题 | 类型 | 说明 |
| --- | --- | --- | --- |
| 订阅 | `/camera/image_raw` 或 `/raw/image` | `sensor_msgs/Image` | 使用 `SensorDataQoS().keep_last(1)` |
| 发布 | `/vision/annotated` | `sensor_msgs/Image` | 与输入 QoS 一致，便于可视化 |
| 发布 | `/vision/detections` | `vision_msgs/Detection2DArray` | 推荐；或兼容旧接口用 `Float32MultiArray` |
| 兼容旧接口 | `/vision/results_matrix` | `std_msgs/Float32MultiArray` | `n×3: [class, dx, dy]` |

海康相机链路参考现有 ROS2 教程中的 `/raw/image`；普通 USB 相机通常是 `/camera/image_raw`。先 `ros2 topic list` 确认真实话题。

### 10.2 节点核心代码

```cpp
#include <torch/torch.h>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/imgproc.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/image_encodings.hpp>
#include <sensor_msgs/msg/image.hpp>

#include <memory>

class VisionNode final : public rclcpp::Node {
 public:
  VisionNode() : Node("cpp_vision_node") {
    declare_parameter<std::string>("model_path", "");
    declare_parameter<int>("num_classes", 2);
    declare_parameter<double>("conf_threshold", 0.35);
    declare_parameter<double>("nms_threshold", 0.45);

    model_path_ = get_parameter("model_path").as_string();
    num_classes_ = get_parameter("num_classes").as_int();
    conf_threshold_ = get_parameter("conf_threshold").as_double();
    nms_threshold_ = get_parameter("nms_threshold").as_double();

    model_ = std::make_shared<TinyYOLO>(num_classes_);
    torch::load(*model_, model_path_);
    model_->to(device_);
    model_->eval();

    const auto qos = rclcpp::SensorDataQoS().keep_last(1);
    sub_ = create_subscription<sensor_msgs::msg::Image>(
        "/camera/image_raw", qos,
        std::bind(&VisionNode::on_image, this, std::placeholders::_1));

    pub_ = create_publisher<sensor_msgs::msg::Image>(
        "/vision/annotated", qos);

    RCLCPP_INFO(get_logger(), "TinyYOLO node ready, model=%s",
                model_path_.c_str());
  }

 private:
  void on_image(const sensor_msgs::msg::Image::ConstSharedPtr msg) {
    cv_bridge::CvImagePtr cv_ptr;
    try {
      cv_ptr = cv_bridge::toCvCopy(
          msg, sensor_msgs::image_encodings::BGR8);
    } catch (const cv_bridge::Exception& e) {
      RCLCPP_ERROR_THROTTLE(get_logger(), *get_clock(), 2000,
                            "cv_bridge failed: %s", e.what());
      return;
    }

    auto input = preprocess(cv_ptr->image);  // [1,3,416,416] CPU
    torch::NoGradGuard no_grad;
    auto pred = model_->forward(input.to(device_)).cpu();
    auto detections = decode_and_nms(
        pred, cv_ptr->image.size(), conf_threshold_, nms_threshold_);

    auto annotated = draw(cv_ptr->image, detections);

    cv_bridge::CvImage out;
    out.header = msg->header;  // 保留时间戳和坐标系
    out.encoding = sensor_msgs::image_encodings::BGR8;
    out.image = annotated;
    auto out_msg = out.toImageMsg();
    pub_->publish(*out_msg);
  }

  std::shared_ptr<TinyYOLO> model_;
  torch::Device device_{torch::kCPU};
  std::string model_path_;
  int num_classes_{2};
  double conf_threshold_{0.35};
  double nms_threshold_{0.45};
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_;
};
```

这里的 `preprocess`、`decode_and_nms`、`draw` 必须来自与训练共享的 `vision_core` 库。节点只负责 ROS2 适配，不重新实现一套预处理。

### 10.3 ROS2 包的 CMake

```cmake
cmake_minimum_required(VERSION 3.22)
project(cpp_vision_node LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)
find_package(Torch REQUIRED)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${TORCH_CXX_FLAGS}")

add_executable(vision_node src/vision_node.cpp)
target_include_directories(vision_node PRIVATE
  include
  ${OpenCV_INCLUDE_DIRS}
)
ament_target_dependencies(vision_node rclcpp sensor_msgs cv_bridge)
target_link_libraries(vision_node PRIVATE
  ${TORCH_LIBRARIES}
  ${OpenCV_LIBS}
)

install(TARGETS vision_node DESTINATION lib/${PROJECT_NAME})
ament_package()
```

构建：

```bash
cd ~/ros2_ws
colcon build --packages-select cpp_vision_node \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH=/opt/libtorch
source install/setup.bash
```

> `CMAKE_PREFIX_PATH` 必须包含 LibTorch；`colcon` 下不要用 Debug 构建链接 Release LibTorch。

### 10.4 运行与验证

```bash
# 输入频率
ros2 topic hz /camera/image_raw

# 启动节点
ros2 run cpp_vision_node vision_node --ros-args \
  -p model_path:=/home/user/models/tinyyolo_best.pt \
  -p num_classes:=2 \
  -p conf_threshold:=0.35 \
  -p nms_threshold:=0.45

# 输出频率
ros2 topic hz /vision/annotated

# 可视化
rviz2
# Add -> By topic -> /vision/annotated -> Image
```

没有相机时，用 rosbag：

```bash
ros2 bag record /camera/image_raw -o vision_test_bag
ros2 bag play vision_test_bag
```

### 10.5 性能与线程

- LibTorch 前向必须放在 `torch::NoGradGuard` 下。
- 单线程 executor 会让推理阻塞回调；实时系统要控制队列，`keep_last(1)`，宁可丢旧帧。
- 多线程 executor 下，`TinyYOLO` 实例不是线程安全的；用一个 mutually exclusive callback group，或每个线程一个模型实例。
- 模型只在构造函数加载一次，不能每帧 `torch::load`。
- 不要在回调里 `imshow`；用 RViz2/rqt，或发布调试图像。
- 保留 `header`，下游融合、TF 查询和时间同步都依赖它。
- GPU 推理要注意 device 一致：输入 `.to(device)`，模型也在同一 device。

### 10.6 阶段验收

- [ ] 节点能订阅图像并发布带框图像。
- [ ] RViz2/rqt 能看到稳定结果。
- [ ] `ros2 topic hz` 正常，输入/输出时间戳对应。
- [ ] 相机缺失、模型路径错误、空帧都有明确日志，不崩溃。
- [ ] 连续运行 30 分钟，内存不持续增长。
- [ ] 单帧端到端延迟可测，不是只看模型前向。

---

## 11. 阶段 7：性能、稳定性与毕业项目

### 11.1 性能记录模板

| 项目 | 数值 |
| --- | --- |
| 硬件 | CPU / GPU 型号 |
| LibTorch 版本 / ABI | 例如 2.x cxx11 ABI |
| 模型 | TinyYOLO, input 416 |
| 设备 | CPU / CUDA |
| 预处理耗时 | 中位数 / P95 |
| 前向耗时 | 中位数 / P95 |
| NMS + 后处理耗时 | 中位数 / P95 |
| 端到端延迟 | 中位数 / P95 |
| FPS | 稳定运行值 |
| 显存/内存 | 峰值 |

GPU 计时要在合适位置同步：

```cpp
if (device.is_cuda()) {
  torch::cuda::synchronize();
}
```

否则测到的是“把任务丢给 GPU 的时间”，不是实际完成时间。

### 11.2 稳定性

- 连续跑 30 分钟。
- 反复停止/启动节点，确认相机和显存释放。
- 输入错误尺寸、空图、损坏 bag、模型文件缺失，都要有处理。
- 用 `valgrind`/ASan 检查明显内存错误；GPU 显存用 `nvidia-smi` 观察。
- 修复所有“只在一台机器上能跑”的硬编码路径。

### 11.3 毕业项目要求

**ROS2 实时目标检测与偏移发布**

- 训练：`vision_train` 在现有数据集上训练 TinyYOLO，保存 checkpoint。
- 评估：`vision_eval` 输出每类 AP、mAP@0.5、P/R。
- 推理：`vision_infer` 可对单张图/视频画框。
- ROS2：`vision_node` 订阅真实相机或 bag，发布 `/vision/annotated` 和 `/vision/detections`。
- 参数：`model_path`、`input_topic`、`conf_threshold`、`nms_threshold`、`num_classes`。
- 文档：数据审计结果、训练配置、指标、硬件、延迟、失败案例。
- 复现：另一个同学按 README 能从头训练和运行。

### 11.4 验收标准

| 项目 | 合格标准 |
| --- | --- |
| 数据 | 图片/标签一一对应，类别一致，无非法行 |
| 训练 | 16 张图能过拟合；完整训练 loss 正常收敛 |
| 评估 | 能算每类 AP 和 mAP@0.5，结果可复现 |
| 推理 | 单图/视频画框正确，坐标无系统偏移 |
| ROS2 | 图像话题稳定，时间戳保留，参数化 |
| 稳定性 | 连续 30 分钟无崩溃、无持续内存增长 |
| 性能 | 有端到端延迟表，知道瓶颈在预处理/前向/NMS 哪一段 |
| 文档 | 他人可按 README 复现 |

mAP 的具体数值取决于数据和训练，不要伪造。报告要能解释“为什么这个数字合理”，而不是只追求好看。

### 11.5 可选进阶

完成基础版本后，按顺序选一个：

1. **CIoU/GIoU 损失**：替换坐标 MSE，比较收敛和框质量。
2. **Anchor + 多尺度**：向 YOLOv3-tiny 靠近，学习 anchor 分配和 FPN。
3. **更强 backbone**：残差块、更多通道，但先确认数据量支撑得住。
4. **LibTorch 推理优化**：CPU 线程、GPU FP16、批处理（批处理会增加延迟，不一定适合实时）。
5. **C++ 参考实现对照**：阅读第三方 LibTorch YOLO 训练代码，理解自己的实现差异，不直接照抄。

不要一开始就上 TensorRT。它是推理优化工具，不解决你的训练代码和标签问题；先把 C++ 训练闭环跑通。

---

## 12. 本仓库资料与数据现状

### 12.1 Python 文件只作为行为参考

本仓库已有 Python 教程和节点。既然你的路线是纯 C++：

- **不要运行 Python 训练脚本**。
- **不要依赖 Ultralytics 的 `.pt`**。
- 可以阅读 Python 代码来对照“话题名、结果格式、dx/dy 定义”，但实现必须自己写 C++。

| 现有文件 | 仅作为什么参考 | 你的 C++ 任务 |
| --- | --- | --- |
| [`../2_1_read_show_image.py`](../2_1_read_show_image.py) | 图像读写流程 | `vision_infer` 的读图/显示 |
| [`../2_2_camera_display.py`](../2_2_camera_display.py) | 摄像头循环 | `VideoCapture` RAII |
| [`../2_3_image_processing.py`](../2_3_image_processing.py) | 预处理顺序 | `preprocess.cpp` |
| [`../2_4_color_detection.py`](../2_4_color_detection.py) | HSV/轮廓思路 | 数据检查/可视化辅助 |
| [`../ros2_2_5_cv_bridge_convert.py`](../ros2_2_5_cv_bridge_convert.py) | 图像消息转换 | C++ `cv_bridge` 节点 |
| [`../ros2_3_2_yolo_node.py`](../ros2_3_2_yolo_node.py) | 话题/发布流程 | `vision_node` |
| [`../ros2_3_3_yolo_hik_cam_node.py`](../ros2_3_3_yolo_hik_cam_node.py) | `/raw/image`、`dx/dy` 格式 | 海康版节点 |
| [`../3_3_train_model.py`](../3_3_train_model.py) | 训练流程概念 | **用 LibTorch 重写训练器** |
| [`../3_4_yolo_inference.py`](../3_4_yolo_inference.py) | 推理后处理 | C++ decode/NMS |
| [`../data.yaml`](../data.yaml) | 旧配置，仅供参考 | 审计后写 `dataset.json` |
| [`../CV与YOLO目标检测入门教程.md`](../CV与YOLO目标检测入门教程.md) | YOLO 概念 | 不作为训练实现 |
| [`../基于ROS2的CV与YOLO目标检测使用教程.md`](../基于ROS2的CV与YOLO目标检测使用教程.md) | ROS2 话题/海康链路 | C++ 节点参考 |

### 12.2 数据现状必须处理

- 当前 `data.yaml` 和真实标签类别不一致。
- `classes.txt` 不是标签文件，应该移出 `labels/`。
- `.bak` 文件应该清理。
- 图片与标签数量不完全对应，必须做 stem 匹配审计。
- 现有有效标签只有 class 0/1，约 1430 个目标；有 9 个空标签文件。

具体处理：

1. 备份 `data/`。
2. 清理标签目录中的非标注文件。
3. 用 `vision_audit` 输出缺失/多余/非法项。
4. 根据 `classes.txt` 和可视化结果确认 `0=stone, 1=spear`（以实际图片为准）。
5. 写 `configs/dataset.json`，不要继续使用错误的 3 类配置。
6. 从 16 张图的过拟合测试开始，成功后再全量训练。

### 12.3 海康相机

现有 ROS2 教程记录：

- C++ 驱动节点：`hikvision_ros2_driver_node`
- 图像话题：`/raw/image`（`sensor_msgs/Image`）
- 启动文件：`hikvision_camera.launch.py`

你的 `vision_node` 把输入话题改为 `/raw/image` 即可。若输出 Bayer 格式，先在驱动端设 RGB8/BGR8，或在 C++ 中显式做 Bayer 转换，不要假设 `cv_bridge` 自动处理。

---

## 13. 常见坑与 FAQ

| 现象 | 常见原因 | 处理 |
| --- | --- | --- |
| CMake 找不到 Torch | `CMAKE_PREFIX_PATH` 没指向 LibTorch | 指向包含 `share/cmake/Torch` 的目录 |
| 链接报 `std::__cxx11` 符号错误 | LibTorch 与 ROS2 ABI 不一致 | 换 cxx11 ABI LibTorch；不要单方面改 ABI 宏 |
| Debug 能编译，Release 崩溃 | LibTorch 与项目构建类型不一致 | 统一 Release；LibTorch Debug 用 Debug 版本 |
| `torch::from_blob` 后图像乱 | Mat 提前析构/非连续/类型不对 | `CV_32FC3` + `isContinuous` + `clone()` |
| 输入 Tensor shape 错 | 忘了 CHW 或 batch 维 | 打印 `sizes()`，应为 `[1,3,416,416]` |
| loss 一直降但检测不到框 | 全部预测背景，正负样本不平衡 | 查正样本数、`pos_weight`/focal loss |
| loss 变 NaN | lr 太大、空正样本 MSE、除零 | 先过拟合小数据；检查空 batch；加有限性检查 |
| 框整体偏移 | letterbox 的 pad/scale 未还原 | 训练和推理共用同一个变换函数 |
| 框大小不对 | 平方/平方根弄反 | 训练目标 `sqrt(w)`，推理 `w=tw²` |
| 所有类别都预测同一类 | 类别映射错/类别损失没算 | 查 `classes` 顺序和 target 的 one-hot |
| 训练集指标高，验证集差 | 过拟合/数据泄漏 | 按场景划分，早停，增强 |
| 验证集 mAP 为 0 | 解码/NMS/坐标还原错 | 先看单图原始输出和 GT |
| 换模型后加载失败 | 类别数/结构不一致 | checkpoint 旁保存 JSON，加载前校验 |
| ROS2 节点一启动就崩溃 | LibTorch ABI、CUDA 版本、模型路径 | 先跑独立 `vision_infer`，再进 ROS2 |
| 节点内存持续上涨 | 忘了 `NoGradGuard`，保存了计算图 | 推理加 `torch::NoGradGuard` |
| GPU 显存爆 | batch 太大/模型没释放 | 降 batch，检查是否有残留引用 |
| 训练很慢 | CPU 训练、分辨率大、数据加载瓶颈 | 用 GPU、降输入、先测数据加载耗时 |
| 相机打不开 | 设备被占用/权限 | `fuser /dev/video0`，检查 RAII 释放 |
| 图像颜色不对 | BGR/RGB 混了 | OpenCV BGR；进网络前转 RGB |
| 时间戳对不上 | 发布时用了当前时间 | 继承输入 `msg->header` |

### 三个最容易忽略的点

1. **训练和推理必须共用同一套预处理/解码代码**。复制两份，迟早漂移。
2. **正负样本比例**。检测训练不是分类训练，objectness 的类别不平衡会直接决定你能不能学到框。
3. **先过拟合，再泛化**。16 张图都学不会，不要怪数据量。

---

## 14. 资源与最终检查清单

### 14.1 视频与文档

**OpenCV / C++ 基础视频（按新旧排序）：**

1. **首选（最新纯 C++）**：[实践才是学OpenCV图像处理的最好方法（B 站，2025-12-09，91 P，约 40 小时 40 分钟）](https://www.bilibili.com/video/BV1CT2QBYEbv/)
   - 核心看 `001～037`；Qt 项目 `038～068` 可跳过；深度学习理论 `069～091` 按需。
   - 第三方合集，非官方账号；以官方文档和实际编译结果为准。
2. **备选（更老、更精炼）**：[OpenCV4 C++ 快速入门视频30讲 - 系列合集（B 站，OpenCV学堂，31 P，约 9 小时 39 分钟）](https://www.bilibili.com/video/BV1i54y1m7tw/)
   - 重点看：环境、读写、色彩空间、`Mat`、像素、绘制、缩放旋转、视频、卷积。
   - 2020 年发布，首集后来更新到 2023；不覆盖训练。
3. **不建议作为主课**：标题带“2025/2026 最新”但目录含大量 `Numpy`、`pip`、`YOLOv5` 的合集。它们通常是 C++ 环境配置 + Python 主体，不符合本框架的纯 C++ 约束。

无论选哪套，都只用来补 OpenCV/`cv::Mat`；训练部分看下面的 LibTorch 文档和本文的 TinyYOLO 章节。

**LibTorch / C++ 训练：**

- [PyTorch C++ API 文档](https://docs.pytorch.org/cppdocs/)
- [Installing C++ Distributions of PyTorch](https://docs.pytorch.org/cppdocs/installing.html)
- [官方 C++ MNIST 训练示例](https://github.com/pytorch/examples/tree/main/cpp/mnist)
- [LibtorchTutorials（第三方 C++ 训练教程，含 YOLOv4/v4-tiny，版本较旧，仅作结构参考）](https://github.com/AllentDan/LibtorchTutorials)
- [Libtorch_YOLOv3_train_demo（第三方 YOLOv3 C++ 训练示例，版本较旧）](https://github.com/ciderpark/Libtorch_YOLOv3_train_demo)

**YOLO 论文/概念：**

- [You Only Look Once: Unified, Real-Time Object Detection](https://arxiv.org/abs/1506.02640)
- [YOLOv3: An Incremental Improvement](https://arxiv.org/abs/1804.02767)
- [Ultralytics YOLO Docs](https://docs.ultralytics.com/)：只看概念和模型演进，**不用于本路线训练**。

**ROS2 视觉：**

- [ROS2 Humble Tutorials](https://docs.ros.org/en/humble/Tutorials.html)
- [cv_bridge 文档](https://docs.ros.org/en/humble/p/cv_bridge/)

**本仓库：**

- [CV 与 YOLO 目标检测入门教程](../CV与YOLO目标检测入门教程.md)
- [基于 ROS2 的 CV 与 YOLO 目标检测使用教程](../基于ROS2的CV与YOLO目标检测使用教程.md)
- [data.yaml](../data.yaml)
- [数据集目录](../data/dataset/)

### 14.2 最终检查清单

#### C++ / LibTorch

- [ ] 能用 CMake 链接 LibTorch 和 OpenCV。
- [ ] 能解释 Tensor 的 shape/dtype/device。
- [ ] 能写训练循环并让 MLP 收敛。
- [ ] 能保存/加载 LibTorch checkpoint。
- [ ] 能解决 cxx11 ABI 链接问题。

#### 数据与训练

- [ ] 数据审计通过，类别与标签一致。
- [ ] 能输出 `[B,3,416,416]` 和 `[B,26,26,5+C]`。
- [ ] 16 张图能过拟合。
- [ ] 完整训练 loss 正常，能保存 best。
- [ ] 能解释正负样本不平衡和 objectness 损失。
- [ ] 能用 C++ 计算 mAP@0.5。

#### ROS2

- [ ] 节点能订阅图像、发布带框图像。
- [ ] 模型只加载一次。
- [ ] 推理在 `NoGradGuard` 下。
- [ ] 保留输入 `header`。
- [ ] 参数化模型路径、阈值、类别数。
- [ ] 连续运行 30 分钟稳定。

#### 工程

- [ ] README、配置、checkpoint 说明齐全。
- [ ] 模型和数据集大文件不进 git。
- [ ] 延迟表有硬件和测试方法。
- [ ] 他人能按文档复现。

### 14.3 今天就能开始的三步

1. 下载 **cxx11 ABI** 的 LibTorch，跑通 `torch_opencv_check`。
2. 写 `vision_audit`，把 `data/dataset` 的图片/标签/类别问题查清楚。
3. 不要写 YOLO。先写一个 C++ MLP，确认 `zero_grad → forward → loss → backward → step` 这一套真的会训练。

> 纯 C++ 训练慢、坑多，但每一步都看得见。把 TinyYOLO 训练闭环打通后，你得到的不只是一个模型，而是一套可以自己改、自己调、自己部署的视觉训练框架。

---

*最后更新：2026-11-02。本文按“已掌握 ROS2 通信、只学习 C++、要求纯 C++ 训练”的前提重写，训练路线为 LibTorch + 自建 TinyYOLO，不依赖 Python / Ultralytics。*
