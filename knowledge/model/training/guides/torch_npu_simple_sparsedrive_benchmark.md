---
type: Guide
title: SimpleV1SparseDrive示例：随机负载、局部编译与训练计时
description: 区分简化SparseDrive工作负载和真实任务验收，记录仅编译backbone、eager也应用分解补丁以及计时未覆盖同步的边界。
tags:
- task.optimization
- topic.performance.analysis
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/datasets/dummy_dataset.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/train.py
  role: implementation
created_at: '2026-11-09T17:03:24Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# SimpleV1SparseDrive示例：随机负载、局部编译与训练计时

## 固定来源与草稿原因

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的v1sparsedrive README、配置、dummy数据和训练入口。未给完整产品矩阵/实际运行记录，故draft、platforms为空。README说依赖“已验证可复现”属于来源陈述，本卡未构建mmcv、训练或验证设备。

## 简化模型与随机数据

README列ResNet/BatchNorm、FPN、检测/地图Sparse4DHeadLike、运动规划、DenseDepth与GridMask，说明它是SimpleV1SparseDrive工作负载，不等于完整真实SparseDrive任务。dummy dataset每次随机图像和检测框/标签、地图点/标签、24维motion及12维plan；没有真实驾驶数据或质量评价。

配置seed3407、batch2、num_workers0、length400、图像256×704、训练步上限200、AdamW(lr1e-4,weight_decay1e-4)。长度400按batch2/drop_last可形成200批，不把上限理解为任何改动配置都保证200步。max_epochs在配置里存在，但已读主训练循环没有按该字段再包epoch循环。

## 只编译backbone与eager基线补丁

--compile实际仅对model.img_backbone调用torch.compile(dynamic=False, mode=reduce-overhead)，FPN/head等未在此入口整体编译。捕获异常只围构造调用，不能保证延迟到首个forward的编译错误也会自动回eager；“enabled successfully”日志不是所有子图已编译或执行通过。

maybe_enable_compile在检查enabled之前总调用DVM分解补丁，将两个BatchNorm前/反向算子加入排除列表并可调用patch_decomp；因此eager基线也不是完全未修改的框架状态。该函数对缺模块/列表会抛错，补丁操作不在后面的compile try内；不能把任何错误都理解为安全回退。主线内部接口、DVM后端与模型BN路径需按真实版本核对，不能泛化为全模型通用优化。

训练入口无条件import torch_npu并设置确定性算法；后续虽然选NPU/CUDA/CPU，也不由device分支证明不安装NPU栈就能纯CPU运行。README的mmcv 1.x分支不是精确commit pin，不能据分支名保证永久同一依赖。

## 测量和sanity forward

主循环计时从已取出batch后开始，包含输入.to(device)、前/反向、AdamW step及prof.step，随后才取时间差；没有明确设备同步，loss.item等在取时间后用于日志，不能把打印time直接当完整同步设备训练时延或数据加载全链路时间。

Profiler默认关闭，开启则Level2、Text+Db、warmup5/active10/repeat1，shape/memory/stack等关闭。开关成本、编译首步和解析窗口分别记录；未采集时NullProfiler三方法为no-op，也不自动补同步。

训练后eval/no_grad只做一次随机批次predict并打印det/map/motion/depth/FPN结果形状；没有测试集指标、eager/compile数值断言或收敛验收。随机负载跑通和形状输出不能当真实驾驶精度或生产加速比证明。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/README.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/config.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/datasets/dummy_dataset.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/v1sparsedrive/train.py)（implementation）
