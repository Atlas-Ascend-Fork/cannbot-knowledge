---
type: Optimization
title: "Grouped 量化 matmul 的 ND-int32 路由 + 行块批处理 epilogue（GroupedMatmulSwigluQuantV2）"
description: "分组 int8 matmul + fp32 域 SwiGLU + per-token requant 的 CV 融合算子，两级结构性改造叠加：把 Cube 输出 C 由 NZ 路由为 ND int32，消除 NZ 碎片重组与逐行小 burst DataCopyPad；epilogue 从逐 token 行改为行块批处理，一次 2D DataCopyPad 取连续 RB 行，使 Cast/scale/Silu/Mul/Abs/Div/clamp 各只跑一次 over RB*No lanes，显著降低每行向量指令数。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.quantization
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X87: Grouped 量化 matmul 的 ND-int32 路由 + 行块批处理 epilogue

## 核心思路
分组量化 matmul（grouped int8 matmul → fp32 dequant → SwiGLU → per-token int8 requant）这类
「Cube 主干 + 重向量 epilogue」的算子上，加速来自**两级结构改造**，而不是调 tiling 常数：

1. **C 输出路由 ND int32（承接 X11/canonical D3）**：把 `MatmulType<GM, CubeFormat::NZ, int32_t>` 改为
   `CubeFormat::ND`。基线在 NZ 下要对每个 token 行发 `2*n1` 个 **64 B** 的 `DataCopyPad`
   （`blockCount=n1, blockLen=64, srcStride=(16*aM-16)*4`，stride 可达很大的跨度），ND 之后同一行是连续的，
   NZ 碎片重组代码可整体删除。注意 host 的 `SetCType` 必须与 kernel 模板 C 一致（混配即 507015）。
2. **epilogue 行块批处理**：epilogue 的成本不是算力而是**向量指令条数**。
   基线每条 token 行发十余条向量指令（每条后面还跟一个 `PipeBarrier<PIPE_V>`），
   行数大时每 AIV 核的指令数极高 → 指令延迟受限。
   改为 RB 行成块：一次 2D `DataCopyPad` 取连续 RB 行（两半各一次），
   其后 Cast / weight_scale / x_scale / Silu / Mul / Abs / Div / clamp / Cast / store
   **各只跑一次 over RB*No lanes**，每行指令数随 RB 摊薄。
   absmax 折叠同时改成行数无关（chunk-split `Max`，`mask=64`，`repeatTimes=RB`，`repStride=No/8`，再 mask 32/16/8）。

## 适用场景
- grouped/deep-K 量化 matmul + 逐行（per-token）向量后处理（dequant / 激活 / requant）的 CV 融合算子。
- 判定前置：task_time 显示 AIV epilogue 是 AIC matmul 的数倍，
  且 epilogue 的瓶颈是**指令条数/行**而非算力；`No_`（每行有效列数）不太大时行块批处理的 RB 可以取大。
- 规模边界：`No_` 很大时算子转为 **cube-bound**，行块批处理收益趋零，剩余空间只在 cube 侧
  （baseN、L1 IBShare、L2 tile sizing）。

## 实现要点
- `blockCount=RB, blockLen=No*4, srcStride=(N-No)*4, dstStride=0`：**两半分开取**是让批处理可表达的关键
  （缓冲内半行 stride 非均匀，无法一次取整行）。
- `DataCopyPad` UB→GM 的 `srcStride` 单位是 **32 B 而不是字节**。
- absmax 折叠需要 32 B 对齐偏移；把行宽 pad 到 2 的幂会浪费大量 UB，pad 到 align-64 更优
  （RB 可取得更大、fold 工作量下降）。
- 取数必须用 **expert 内行偏移**（`r = i - sg[g]`），不是全局 token 行。
- VEC 前缀运算在 sub-32B 元素数上会 507015 崩溃（这也是 absmax 尾部停在 8 lane 标量读的原因）。
- host 守卫（如 `M <= aiv*1024`）常常是**某个 UB 缓冲尺寸 bug 的绕过**：若 staging 缓冲按固定长度分配、
  而行循环写入 `ceil(M/nb)` 个元素，M 增大即越界。修法是分段 flush 让 UB 占用与 M 解耦，而不是维持守卫。

## 追加：Cube 侧「让框架自导 L1 计划」而不是 pin singleCoreM/N
当 epilogue 被压到原语下限后，剩余空间在 cube 侧。**不要**沿用「GetTiling 之后手工 pin singleCoreM/singleCoreN」的写法
（那会冻结 L1 窗口）。改为在 host 侧：
`SetShape(singleM, singleN, K)` + `SetOrgShape(...)` + `SetFixSplit(baseM, baseN, baseK)` + `SetBufferSpace(512KB, 128KB)`，
让 `MatmulApiTiling` 自己推导 L1 计划，再做合法性校验（被拒则回退旧 builder）。
最优默认通常落在 `singleM = baseM = 128, singleN = 512` ⇒ 框架把 **A 的整条 K 轴钉在 L1**
（K 较大时 `stepKa/depthA1` 随之增大），A 的重读次数从 `N/256` 降到 `N/512`。
kernel 侧同步把 `singleCoreN` 从编译期常量改为读 `tiling->singleCoreN`，
并把 expert plane 的行 pad 一起抬到最大 tile M，以免多 N-tile 时越界。
**指纹**：per-K 的 asc 增益随 K 单调上升，这是 A 命中 L1 的特征。
**边界（均已证伪）**：`singleM > baseM`（如 1024/512）会让 `GetTiling` 把 L1 K 窗口退回 `depthA1=2`
并串行多个 base tile ⇒ 大幅回退；int32 acc 在 128KB L0C 下 `M_eff·N_eff ≤ 32768`，纯 base 形状调优空间有限；
int32 下 `baseN=512` 不可行（会逼 `baseM` 过小，反而增加重载）。

## 判定纪律：先用 op_summary 的 pipe 比值定位，再决定改哪条管
`msprof --quick --quick-batch` 的 `op_summary` **是带 pipe 比值列的**（不要以为 quick 模式没有）：
`aic_mac_ratio / aic_mte2_ratio / aiv_vec_ratio / aiv_scalar_ratio / aiv_mte2_ratio`。
判读方式：
- 若 AIV epilogue 的 **`aiv_scalar_ratio` 高、`aiv_mte2_ratio` 低** ⇒ **epilogue 是标量管受限，不是 DMA 受限**；
  靶点是「折叠后的向量结果 `GetValue` 出来 + 多段标量 max 链」的 per-token absmax
  （`scalar_reduce_after_vector`）。
- 若 AIC 的 `aic_mte2_ratio` 高、`aic_mac_ratio` 低 ⇒ MTE2 受限（L1 重载）。
三个只动向量管/DMA 的候选（去行内 `PipeBarrier<PIPE_V>`、requant 改倒数乘、同 stream 分块交错）
往往都不过增益阈值——**先读 pipe 比值再动手，可以省掉若干轮**。
另：双 ACL stream + event 的真并发会破坏 quick-batch 的 `stream_id → 样本` 归因并引发跨样本竞态；
任何 overlap 方案必须是**单个 MIX kernel**。

## 验证方法

- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- 行块批处理与格式路由类改动额外覆盖小 M、大 M、No_ 非 32B 对齐与 No_ 很大（cube-bound）四类形状。
