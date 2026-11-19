---
type: Guide
title: MNIST自动迁移验收：设备替换、AMP与检查点边界
description: 以固定A2教程区分transfer_to_npu映射、前反向精度步骤及本卡检查点证据，避免把训练结束当识别效果或性能验收。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/quick_start.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/quick_start.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/illustration.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/illustration.png
  role: constraint
created_at: '2026-11-09T16:42:20Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
---

# MNIST自动迁移验收：设备替换、AMP与检查点边界

## 版本与场景

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的中英文快速入门，具体模型例子为Atlas800T A2。卡片只登记A2，不据AMP段提到A3/950DT就声称完整教程已在其他产品验证；不是26.0/PyTorch2.8的整套配方。本卡只审阅，没有下载MNIST、训练或保存/加载检查点。

## 数据和设备准备

先匹配驱动/固件、CANN、PyTorch/TorchNPU和torchvision；英文特别说明CPU版torchvision。联网首次download=True把数据放到工作目录mnist/MNIST/raw，离线则先在可联网环境准备完整mnist目录、复制到实际运行目录并改download=False。目录存在不证明数据完整，旧数据和本卡输出要区分。

原GPU脚本device为cuda:0。import torch_npu和from torch_npu.contrib import transfer_to_npu必须放在第一次构造该device前，导入迁移模块后该示例的CUDA调用才映射到NPU；保留cuda字符串不表示真实CUDA执行。仅安装torch_npu或自动注册不等价于启用此迁移patch，也不保证所有第三方CUDA语义都可映射。若采用手工迁移，按具体接口改设备并独立验证，外部迁移指南内容未自动入库。

## 训练和AMP的顺序

CNN为两组卷积/池化、Flatten和两层线性层，样本ToTensor，batch64、CrossEntropyLoss、SGD(lr=0.1)、默认10轮；这些是演示参数，不是最优调参建议。可先改1轮检查通路，不能据此断言完整训练收敛。

普通路径每步迁移图像/标签、前向和loss、zero_grad、backward、optimizer.step。AMP路径在循环前创建amp.GradScaler，把前向与loss放autocast内部，在其外部scale(loss).backward，再scaler.step和update；非有限梯度可能跳过参数更新，不能把每次循环数直接等同优化器成功更新次数。教程不要求每个batch的loss递减，nan/inf须检查数据、学习率和精度配置。

教程说明旧Atlas训练产品需开启AMP，A2/A3/950DT可选；这是该页适用说明，不是所有模型都可在任意dtype运行。autocast不自动改所有参数和状态类型，也不将CUDA AMP弃用提示直接替换成CUDA设备字符串。接口细节见[Autocast与自定义autograd](torch_npu_autocast_and_custom_autograd.md)。

## 检查点能证明什么

脚本保存epoch、模型state_dict和optimizer状态至checkpoint.pth.tar；AMP替换段保留同一保存代码，**没有保存GradScaler状态**，因此它不是完整AMP断点恢复演示。教程也没有恢复、测试集评估或吞吐测量。

每100batch及每轮最后batch输出当前batch loss，默认示意938步/轮的日志和0.0732等数值不是本卡结果。训练正常结束、保存提示与文件修改时间应来自同一次运行；历史截图仅显示123023字节的旧checkpoint文件，不能代替这些证据，也不能仅凭文件名/存在判断训练成功。分类效果需独立测试集，性能需去除额外同步/日志影响后按同负载比较。

diff中的+/-/...是修改标记，不属于可执行脚本。教程指向的MindSpeed Core/LLM/MM和veRL是进阶外部入口，不由此宣称这些仓的并行配置已摄取。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/quick_start.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/quick_start.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/illustration.png)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/illustration.png)（constraint）
