---
type: Runbook
title: "nearest 网格采样在半整数判定前保留仿射坐标残差"
description: "FP32 反归一化会把半整数附近的坐标提前舍到中点；用高低位保留加法与乘法残差，再按两部分决定 nearest RNE 索引，限定 nearest/zeros 和已验证的有限坐标域。"
aliases: ["nearest affine residual", "grid_sample nearest wrong row half integer", "FP32 unnormalization false tie"]
tags: [task.debugging, topic.precision]
status: stable
sources: []
created_at: "2026-10-20T15:38:07Z"
updated_at: "2026-10-20T15:38:07Z"
platforms: ["950"]
---

# nearest 网格采样在半整数判定前保留仿射坐标残差

> **来源说明（2026-10-31）**：本卡为轨迹沉淀 Runbook，可消费证据为正文的触发、探针、原始观测与验证信号（车队私有实测，暂无可公开复核的外部出处）。
## 适用场景

- **工程形态**：nearest 输出在少数位置选到相邻采样点、且误差远大于输出舍入噪声时，先检查坐标到整数索引的决策——在半整数判定前保留仿射坐标残差，而不是提高采样值或最终输出的精度。
- **API 路径**：参考合同为原生 dtype 的实际输入与 grid 先无损提升到 CPU FP64，再做反归一化与 RNE；与原生 FP32 坐标路径的一致性是另一项合同。
- **验证过的平台与 CANN 版本**：Ascend950PR，SDK 9.2.0.B092，Torch NPU 2.10。
- **适用粒度**：`same_operator`——grid_sample 的 nearest/zeros 路径；保留原始输入、布局、`align_corners`、边界检查与输出 dtype。
- **路线优先级**：`recommended_fastpath`。
- **明确不适用或未验证场景**：不据此修改 border、reflection、bilinear 或 bicubic 路径。正文的差异预测来自同一冻结输入上的 CPU 算术重建，本身不是修改后的 NPU 执行结果。

## 触发与适用范围

nearest 输出在少数位置选到相邻采样点，而且误差远大于输出舍入噪声时，先检查坐标到整数索引的决策。这里的参考合同是：原生 dtype 的实际输入和 grid 先无损提升到 CPU FP64，再做反归一化和 RNE。与原生 FP32 坐标路径的一致性是另一项合同。

本配方仅验证 Ascend950PR、SDK 9.2.0.B092、Torch NPU 2.10 的 nearest/zeros 路径。保留原始输入、布局、align_corners、边界检查和输出 dtype；不据此修改 border、reflection、bilinear 或 bicubic。

## 判别探针与原始观测

当轴长为 259、align_corners=false、实际 FP32 grid 值为 0.003860950469970703 时，FP64 反归一化坐标为 129.4999930858612；直接 FP32 算法得到 129.5，RNE 因偶数规则选择 130，前者应选择 129。另一个实际坐标 85.4999994635582 被提前舍为 85.5，同样改变索引。

在同一冻结输入上重建旧算术，两个空间索引差异预测了 128 个输出元素差异，最大绝对误差 1.3377278447151184。这是 CPU 算术重建证据；本身不是修改后 NPU 执行。提高 sampled value 或最终输出的精度无法恢复已经选错的邻点。

## 修复步骤

1. 对每轴保留 g+1 的高低位，用 TwoSum 回收该加法的低位；仿射乘法用 FMA 的乘积残差继续携带低位。
2. align_corners=false 时也保留减一的残差，然后将高低位同时乘以二分之一。不要先把二者合并成一个 FP32 坐标。
3. 以高位求整数 floor，再用 ((hi-floor(hi))-0.5)+lo 判断位于半整数的哪一侧；只有实际相等时才按 floor 的奇偶性处理 tie。
4. 参考若明确使用 binary64 算术，极小 g 的 g+1 也要遵循 binary64 在 1 上下不同的间距。不能把精确实数公式自动当成所声明 FP64 程序；已测实现对此边界另行对齐。
5. 仅对 nearest/zeros 选择此分支，继续做原有越界检查。不要添加 epsilon、按样本位置修正索引、改变随机输入或降低参考精度。

这些步骤是被测实现的数值方法，不能代替浮点变换的适用域检查。要求有限坐标、有效尺寸、足够的索引位宽，并核对尺寸转 FP32 的表示性、FMA 与编译器变换；极端坐标和溢出域未获覆盖。

## 已完成验证与边界

修改前内核 SHA-256 为 6136ba48dbea3fd9545c6ef18c6251e2c13b1468ec34ce2014e581f0b87664dd；修改后为 8c02d437eeb5f0a5f5fe1332f4b7d4c30089a7237bc0d554492c2d714d974191，加载 DSO 为 7f3f5f0d919636c033900a2dbc5620aa5bfc12ec2b6e1c3cc03847dea6d4187c。同一轮冻结 50 例中，候选全部通过；原 Model 与独立调用的 ACLNN 各保留 49 通过、1 失败，未被重写。

另有 2,804,686 个 CPU 坐标/索引检查与声明的 FP64 路径一致、50 个 scalar 参考控制通过、50 个零输出坏控制被拒绝。该轮没有性能测量，也没有全输出重复执行；不得由此宣称全输入域正确、性能收益或两个参考后端算法独立。

旧选择链和本次修复都明确披露 WHITE_BOX。历史黑盒轨迹、其实际 KB 绑定及未能采用本方法的原因是 UNKNOWN。该结果不是冷黑盒知识验证；未来未接触修复源码的消费者仍需 Query、全文 Read、记录适用性决策，并以自己的源码/DSO完成同输入完整分母测量。

## 与现有知识的区别

[GridSampler3D Direct Invoke](../../operators/direct/cv/image/grid_sampler_3d_950.md) 的“计算语义”和 R-002 已说明 FP32 坐标、rintf 与边界检查；这里补充的是参考合同不同时，半整数决策前丢失的残差及其判别。通用 Cast 提升和输出舍入规则不能恢复这个离散索引选择。

## 相关卡片

- [最近邻坐标规则与数值搬移分离的契约](../../guides/nearest_resize_native_value_gather_and_coordinate_contract.md)——同一坐标判定的工程契约：区分 nearest 与 nearest-exact 分支并用 CPU 索引真值检验。
