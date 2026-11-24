---
type: Optimization
title: tensor-list 单 kernel 融合 + tile 粒度全局核分配
description: 将 tensor-list 的逐张量 kernel 合为单 kernel，并按 tile 粒度分核
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-tensor-list-single-kernel-fuse-tile-granular-core-split.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：tensor-list 单 kernel 融合 + tile 粒度全局核分配

> 单一优化点：foreach 类 tensor-list 算子若 host 侧对每个张量各 launch 一个 kernel（同流串行），小张量会重复支付 launch/头开销且核利用率按单张量打折。把整个 list（N ≤ 参数表容量，如 8）融合为**一次 kernel launch**：所有张量的 tile 数求前缀和，blockIdx 在**全局 tile 索引空间**按精确比例分割领取连续区间，核内线性定位所属张量后走原 tile 流水。list 长度超额时分组或回退 per-tensor。对标原生 multi_tensor_apply 融合架构。

## 1. 原理

- **launch 与头开销随张量数线性叠加**：每次 launch 有 host enqueue + device 调度 + kernel 头（tiling 装载/流水启动）开销；list_len 个串行 kernel = N 倍开销 + N−1 个流水排空点。
- **单张量核分配打折**：per-tensor 启动时每核只在本张量内均分，张量小时（tiles < 核数）部分核空转；融合后按全局 tile 池分配，任何张量组合都能吃满全部 AIV 核。
- **精确比例分割防尾核堆积**：`start = floor(k*T/g)`（int64 乘法防溢出）保证核间 tiles 差 ≤1；ceil 均分（`k*ceil(T/g)`）会让前段核多扛 1 tile、末核少一大截，长 kernel 下可测出 ~8% 差距。
- **参数表直传指针数组**：N×(in…out 指针 + len) 平铺为核参数（宏展开生成签名），host 栈数组装配，无 GM blob（与 control-params-kernel-scalar-passthrough 配套）。
- 效果实例：P1(2×1M fp32) event 40→34.7us；P11(2×1.1M fp16) 46.2→38.7us；P20 wall 221.8→41.9us；P4(单张量大 fp32) 1014→921us（fused 连单张量也受益于核间更均衡）。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. foreach/map/list 类算子 host 侧 `for (t : list) launcher(t)` 逐张量 launch（同流串行）。
2. bench 中 list_len>1 的 case 加速比系统性低于同规模单张量 case；或 msprof 显示 N 个小 kernel 背靠背、间隙可见；加速比与 TensorList 长度强负相关（len=1 尚可，len≥2 线性劣化）。
3. 张量较小（单张量 tiles < AIV 核数）时核利用率不足（`usedCoreNum = min(cores, tiles)` 打折）。
4. 已做参数直传后，小 case wall−event 差仍随 list_len 增长（launch 次数主导）；各 case 耗时收敛于与数据量无关的固定地板（每张量摊出一倍地板）。

## 3. 正确性红线

- **前缀和定位一致**：host 侧 `tiles_i = ceil(numel_i/TILE)` 求和必须与 kernel 侧逐张量重算完全一致（同一 ceil 公式）；定位循环 `while (j+1<N && g>=pref[j+1]) ++j`。
- **未用槽位 len=0**：填充参数表的空组必须 len=0（tiles=0，不产生全局 tile），指针可传任意合法值。
- **gridDim 用 GetBlockNum()**：核内分割比例用真实 blockDim，不可假设平台核数。
- **跨张量 tile 的 buffer 复用**：每 tile 重新 `SetGlobalBuffer` 切张量（连续同张量只切一次）；UB buffer 一份复用，不 per-tensor 分配。
- **int64 比例分割**：`blockIdx*T` 在 T 数千×blockIdx 数十时仍可能逼近 int32 上限，乘法显式 int64。
- **元数据表变体红线**：张量地址必须用 `data_ptr()`（含 storage_offset），不可用 `storage().data()` + 假定 offset=0；核区间边界（blockIdx×blockLength）可落在张量中间任意元素处——边界跨段时一个核处理多段、一段被两核分摊都必须正确（前缀和扫描天然支持）；Σnumel 与单个 numel 需 < INT32_MAX（int32 索引空间上界），host 侧显式检查；空核（区间起点 ≥ totalLength）必须早退且不触碰 InitBuffer 之外的队列。

## 4. 泛化条件

- **适用**：
  - aten._foreach_* / list-map 类（同 dtype contiguous 张量列表逐元素/归约）。
  - 多输入列表（x1/x2/x3...）共享同一 list 索引的算子（参数表按组展开）。
  - 小张量批处理（每张量几百 KB 以下，launch 开销占比高）。
- **不适用**：
  - 单张量已满核且 kernel 时间远大于 launch 开销的大 case（融合收益趋零，但无回归）。
  - 张量间 dtype/shape 差异大需不同 kernel 特化（需按 dtype 分组融合）。
  - 张量间有数据依赖/顺序语义（流顺序不够，需显式同步）。
  - 需要每张量独立 tiling 复杂策略（tile 大小/dtype 特化不同）——可分组融合。
  - 参数表容量不足且不便分组的超长 list（几十+）：分组融合（每组 ≤8）收益仍存。
  - **注意**：个别 dtype×规模组合在融合路径可能小幅劣化（实例：单张量 bf16 ≥8M 元素 fused 慢 8%，机理未明）——上线前按 dtype×规模做同窗口配对回归，必要时实证分派（见 shape-adaptive-strategy-dispatch）。

## 5. 实施步骤

1. 定义 `ListArgs`（N≤8 组 GM 指针 + len + 公共标量）；kernel 类 `Init(args)` 内重算 `tiles_i/pref_i/totalTiles`，`Process` 按全局 tile 区间循环。
2. 核区间用 `start=floor(k*T/g), end=floor((k+1)*T/g)`（int64）精确比例分割。
3. 用宏展开生成 42 参数的 kernel 入口与 host `do_` 函数（`uint8_t** ptrs, int32_t* lens` 数组接口）；CMakeLists 注册新源文件。
4. host：`listSize ≤ 上限` 走融合单 launch（grid=全部 AIV 核），否则回退 per-tensor。
5. **元数据表变体**：tiling 头 `{tensorNum, totalLength, blockLength, tileLength}`；GM 元数据 buffer 布局 = header(int32×4) | `ptr[N](u64)` | `numel[N](i32)`，一次 H2D；host 一次遍历完成 contiguous/dtype/numel 检查与 Σnumel；kernel 用前缀和线性扫描张量表定位本核区间（适合参数表直传不可用或 list 较长的场景）。
6. 全量精度 + 同窗口配对 bench（list_len>1 与单张量 case 分别确认无退化）。

## 6. LLM 前置问题

- host/kernel 的 tile 计数公式完全一致吗（ceil 口径）？
- 空 len 槽位处理了吗？blockIdx 溢出路径用 int64 了吗？
- 融合后逐 dtype×规模做过配对回归吗（防实例中的 bf16 大张量劣化）？

## 7. 验收标准

- build + 精度全过；r1→r2：P1 event 40→34.7、P11 46.2→38.7、P16 66.5→50.9、P20 221.8→41.9（wall us，910B3）；全量 20/20 精度 PASS。
- 单张量大 case 同向受益：P4 event 1014→921（-9%）。
- 元数据表变体单独轮：geo +20%（0.374→0.448，超噪声），multi_launch case 2.2-2.9x，全量精度通过。

## 检索卡（短卡）

动作：将 tensor-list 的逐张量 kernel 合为单 kernel，并按 tile 粒度分核
适用：同 dtype、连续张量的 foreach/list-map 逐元素或归约；多输入列表共享索引
限制：host/kernel前缀和定位必须一致；ListArgs最多8组GM指针，并携带长度和公共标量。
范围：同 dtype 连续张量列表的逐元素或归约路径
检索词：foreach、tensor-list、单 kernel、tile、ListArgs、前缀和、totalTiles
机会：host 对列表逐张量同流串行 launch，小张量重复承担启动和头开销
代价：串行方案产生 N 倍启动开销及 N−1 个流水排空点
