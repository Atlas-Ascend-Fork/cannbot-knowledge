---
type: "Runbook"
title: "gather 扁平偏移公式 dim 上方形状错配"
description: "AscendC gather kernel 用扁平公式 outer*x_block_+idx_val*x_inner_+inner 计算 x 偏移，outer 取自 index 坐标系却用 x 的 x_block_ 缩放；当 index 与 x 在 dim 之上某维形状不同时外层坐标错位，致该 case 大面积 mismatch，dim=0 时公式退化为正确故多用例不暴露。"
tags: ["task.debugging", "topic.precision", "topic.compute.indexing"]
status: stable
sources: []
created_at: "2026-08-18T07:38:07Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a2"]
aliases: ["x_strides"]
---

# gather 扁平偏移公式 dim 上方形状错配

## 现象

cann-bench 评测模式下完成 gather (IndexGather, L2) 算子开发后，运行 `run_evaluation.sh` 做最终精度评测，19/20 用例 MERE=0/MARE=0 通过，唯独 `level2/gather_20` 精度严重不达标。case 20 参数 `x=[4,255,2049], index=[4,127,2049], dim=2, dtype=float32+int32`：`dim=2` 即 gather 轴是末维，按 `torch.gather` 语义应有 `y[i,j,k]=x[i,j,index[i,j,k]]`；注意此处 `index.shape[1]=127` 而 `x.shape[1]=255`——两者在 dim 之上的第 1 维形状不同。当时 kernel `Compute` 用扁平公式 `x_offset = outer*x_block_ + idx_val*x_inner_ + inner` 计算读取位置，`DataCopyPad` 单元素从 GM 搬入 UB 后用 `GetValue`/`SetValue` 写出。

## 适用场景

- **工程形态**：kernel 直调（cann-bench 评测模式，`op_kernel/gather_kernel.cpp` 由 bisheng 编译，`op_plugin` 走 torch_npu `OpCommand::RunOpApi`）。
- **API 路径**：`AscendC::DataCopyPad`（GM→UB 单元素搬运）+ `LocalTensor::GetValue`/`SetValue` 标量读写 + `TQue<VECIN>` 临时 buffer。
- **验证过的平台与 CANN 版本**：Ascend 910B3 / SocVersion ASCEND910B / NpuArch DAV_2201（Atlas A2，平台词表 `a2`）；CANN 9.0.0。
- **适用粒度**：`same_operator`（gather/IndexGather 族的 N 维偏移计算；任何用"扁平外层坐标 × 外层块大小"近似 N 维偏移的 kernel）。
- **不适用或未验证场景**：dim=0 且 index 与 x 在所有非 dim 维形状相同时，原扁平公式恰好等价（不会暴露 bug）；950/A3 等其它平台未在本 trace 实测（见 `## 失效边界`）。

## 判别方法

- **触发**：cann-bench gather 评测中 `level2/gather_20`（`x=[4,255,2049], index=[4,127,2049], dim=2`）精度不达标 `MERE=6.100056, MARE=68403.352561`，其余 19 用例 MERE=0/MARE=0 通过。触发特征：仅"index 与 x 在 dim 之上某维形状不同"的用例失败，dim=0 或上下文对称的用例全过。
- **探针**：在 NPU 上用小 shape 复现——`x=torch.randn(4,8,16), index=torch.randint(0,8,(4,4,16)), dim=2`（让 index 在 dim=1 上短于 x），跑 `cann_bench.gather(x,index,dim=2)` 与 `torch.gather(x,2,index)` 对比，打印 `max_diff`、`mismatch%`，并逐元素打印 `golden=x[i,idx,k]` vs `custom`。
- **观测**：75% 元素不匹配，`max_diff=6.5`；关键观测 `y[0,0,0]`（`index=6`）custom 返回 `x[0,6,0]=96.0`（即 dim=1 语义），而期望 `x[0,0,6]=6.0`（dim=2 语义）——偏移计算把外层坐标错配到了 gather 轴。
- **判别**：kernel 把 N 维 gather 的 x 偏移简化为三段扁平公式，`outer = out_pos / idx_block_`（按 index 坐标系切分得到的外层扁平坐标），`x_offset = outer*x_block_ + idx_val*x_inner_ + inner` 却用 x 的 `x_block_` 缩放。`outer` 是 index 系下的扁平外坐标，只有当 `idx_block_==x_block_` 且 dim 之上各维 `idx_shape[d]==x_shape[d]` 时两坐标系一致、公式恰好等价；一旦 dim 之上某一维 `idx_shape[d]!=x_shape[d]`，`outer` 在 index 系与 x 系下逐维解出的坐标不同，缩放后 x 外层偏移错位 `(x_shape[d]-idx_shape[d]) * ∏_{d'>d} x_shape[d']`。dim=0 时 `outer` 恒为 0（`idx_block_` 为全维乘积），公式退化为正确，故前 19 个多用例不暴露。此为偏移公式坐标系错配，非 golden 语义错误——`torch.gather(x,2,index)` 语义复核确认 golden 正确。

## 验证信号

- cann-bench `run_evaluation.sh` 最终评测：19/20 通过，`level2/gather_20` `MERE=6.100056, MARE=68403.352561`，其余用例 MERE=0/MARE=0（来源平台:a2；证据等级:tool_observed）。
- 小 shape NPU 复现（`x=[4,8,16], index=[4,4,16], dim=2`）：75% 元素不匹配，`max_diff=6.5`；`y[0,0,0]`（`index=6`）custom=`x[0,6,0]=96.0` 而期望 `x[0,0,6]=6.0`（来源平台:a2；证据等级:tool_observed）。

## 失效边界

- **已验证**：a2（Ascend 910B3 / DAV_2201）上 case 20 的 bug 触发与小 shape 复现。
- **未验证，推断可迁移**：Ascend 950 / A3 等其它平台——`DataCopyPad` GM→UB 单元素搬运与 `GetValue`/`SetValue` 标量读写是平台无关的通用 Ascend C 机制，偏移公式的坐标系错配与平台无关，推断可迁移；但本 trace 未在这些平台实测。
- **不适用**：dim=0 且 `index.shape[d]==x.shape[d]`（`d>0`）时原公式恰好等价，不暴露 bug。

## 坏实践

- 用"扁平外层坐标 × 外层块大小"近似 N 维偏移时，未检查 `index` 与 `x` 在 `dim` 之上各维形状是否一致——该近似只在对称形状下等价，是 case 20 错位的直接原因。

<!-- cannbot:related:start -->
## 相关

- [Gather 非 last-dim 转置+索引换算预处理占比高](../performance/gather_last_dim.md)（`related`）：跑 `./scripts/run_evaluation.sh`（20 case）精度 20/20 All Pass（`max_diff=0.0`），但 dim!=last 的 4 个大 case（gather_1/3/4/10）speedup 均 < 1.0x。；case 20 参数 `x=［4,255,2049］, index=［4,127,2049］, dim=2, dtype=float32+int32`：`dim=2` 即 gather 轴是末维，按 `torch.gather` 语义应有 `y［i,j,k］=x［i,j,index［i,j,k］］`；两卡共同覆盖 Gather 末轴与非末轴实现的性能诊断和多维偏移精度验证。
- [多维 Gather 部分 case 错 — LUT 维序反了](gather_lut_coordinate_decode_must_start_from_last_dimension.md)（`related`）：`outer` 是 index 系下的扁平外坐标，只有当 `idx_block_==x_block_` 且 dim 之上各维 `idx_shape［d］==x_shape［d］` 时两坐标系一致、公式恰好等价；一旦 dim 之上某一维 `idx_shape［d］!=x_shape［d］`，`outer` 在 index 系与 x 系下逐维解出的坐标不同，缩放后 x 外层偏移错位 `(x_shape［d］-idx_shape［d］) * ∏_{d'>d} x_shape［d'］`。；C-contiguous 扁平下标的最后一维才是最低有效维，但 LUT 代码从子空间首维开始执行 `% size` / `/= size`，把首维误当成最低有效维，导致多维 `outerBase` / `innerBase` 坐标反解顺序颠倒。。两份 Runbook 都诊断多维 Gather 将扁平坐标映射到错误 GM 地址：一份修正 index 与 x 的逐维 stride 坐标系，另一份修正 C-contiguous LUT 的末维优先反解，联合阅读可完整检查外层和内层地址生成。
- [Gather 非 dim 维缩小时折叠步长错位](gather_non_axis_shape_shrink_requires_per_axis_source_strides.md)（`same_topic`）：“首版把输出的非 `dim` 多维坐标折叠成 `outer` 并以 `midSrc * innerSize` 作为源步长，隐式要求所有非 `dim` 维满足 `index.size(j) == x.size(j)`，而 `torch.gather` 只要求 `index.size(j) <= x.size(j)`，因此任一非 `dim` 维缩小时都会把输出坐标映射到错误的源地址。 机制链如下。对输出坐标 `c［0..n-1］`，正确的源元素偏移是： ```text baseSrc = Σ(j != dim) c［j］ * xstride［j］ x_off = baseSrc + index［c］ * xstride［dim］ ``` 首版则把多个 `c［j］` 压成一个按输出 extent 编码的 `outer`，再计算： ```text outerStep = x.size(dim) * Π(k > dim) x.size(k) x_off = outer * outerStep + innerLin + index［c］ * innerSize ``` 当某个非 `dim` 维缩小时，`outer` 的进位基数来自 `index.size(j)`，`outerStep` 的源布局基数却来自 `x.size(j)` 的折叠假设；两者不再是同一个坐标系统。逐维 `xstride` 不依赖 extent 相等，因而能恢复正确映射。”与“cann-bench 评测模式下完成 gather (IndexGather, L2) 算子开发后，运行 `run_evaluation.sh` 做最终精度评测，19/20 用例 MERE=0/MARE=0 通过，唯独 `level2/gather_20` 精度严重不达标。case 20 参数 `x=［4,255,2049］, index=［4,127,2049］, dim=2, dtype=float32+int32`：`dim=2` 即 gather 轴是末维，按 `torch.gather` 语义应有 `y［i,j,k］=x［i,j,index［i,j,k］］`；注意此处 `index.shape［1］=127` 而 `x.shape［1］=255`——两者在 dim 之上的第 1 维形状不同。当时 kernel `Compute` 用扁平公式 `x_offset = outer*x_block_ + idx_val*x_inner_ + inner` 计算读取位置，`DataCopyPad` 单元素从 GM 搬入 UB 后用 `GetValue`/`SetValue` 写出。”。两张 Runbook 都定位 gather 在非 dim 维 extent 不等时用折叠 outer 步长造成源地址错位。
<!-- cannbot:related:end -->
