---
type: Optimization
title: strided scatter 的向量交错展开（Gather+And 构造 [x,0] 交错 + 连续写）
description: 将固定步长的小块 strided scatter 搬运，改为通过 vecExpand 执行向量交错展开。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-strided-scatter-vector-interleave-expand.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：strided scatter 的向量交错展开（Gather+And 构造 [x,0] 交错 + 连续写）

> 单一优化点：当散射写的目标位置是**固定步长交错**（如 out[..., start::step, ...] 的 step=2 且最内连续段 inner 过小）时，逐小块 MTE 的块粒度会崩塌到远小于 32B（每块 pad 到 32B，扫描体积放大 elemSize×16/step 倍，MTE3 pipe 占比 >90%）。改为：**MTE2 连续读源段 → 向量管线构造 [x, 0] 交错流（Gather 重复 + And 位掩码）→ 连续 MTE3 写整段**，把 MTE 块粒度从 2B 提升到整段连续写。

本策略适用于任何"固定 stride 的稀疏散射/交错写"型 kernel（slice_backward / strided copy / 插值上采样 / deinterleave 写回），与具体算子无关。

## 1. 原理

**问题形态**：`out[o, start + i*step] = grad[o, i]`（inner==1 或 `inner*elemSize < 32B`）。逐块 MTE 实现（DataCopyExtParams{blockCount=len, blockLen=inner*elemSize, dstStride=step 内隙}）的每块只有 2~4B，MTE 引擎按 32B datablock 粒度处理 → 每个元素一次块描述符 + pad 放大。P4 类 shape（8192×4096 fp16 step=2）产生 33.5M 个 2B 块，实测 MTE3 pipe 占比 94.3%、扫描体积乘子 >10×（scan_volume_model 判 P0 级重切分）。

**交错展开**：目标是把"间隔写"变成"连续写 + 数据预先交错"。对 2 字节 dtype（half/bfloat16）：
1. `Gather(y, x, idx, 0, 2*cnt)`，`idx[i] = (i/2) * elemSize`（**字节偏移**）→ y = [x0,x0,x1,x1,...]
2. `And(y_i16, y_i16, mask, 2*cnt)`，mask 为 int32 全 0x0000FFFF 的 Duplicate（int16 视图即 [FFFF,0000] 交错）→ y = **[x0, 0, x1, 0, ...]**（位与不改变有效位，对 inf/NaN 安全；不可用 `Muls(0)` 代替——0×inf=NaN）
3. MTE3 一次连续写 `len*step*elemSize` 字节到 `out[o, start]` 起的整段

**多行合批**：src 行连续时一次 MTE2 读 M 行、一次 Gather/And 处理整批、MTE3 逐行写（dst 行间不连续），使调用次数与行数解耦——133K 行的 case 从 46.9ms 降到 5.5ms。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. 代码形态：scatter/交错写的 MTE 循环里 `blockLen = inner*elemSize` 且 `inner*elemSize < 32B`（inner==1 最典型），块数 = outer×len 达百万级。
2. profiling 特征：**MTE3 pipe 占比 >60%**（本例 94%），VEC 占比 ≈ 0；耗时随块数线性、与数据量不成比例。
3. `scan_volume_model.py` 扁平切分乘子 >10×。
4. 目标位置模式是**编译期已知的固定步长**（step 与 inner 是 tiling 参数，非数据相关索引）。

不适用：
- 数据相关索引的 scatter（应走 GatherMask 压缩类策略，见库内 `vector-filter-gathermask-compaction`）；
- `inner*elemSize ≥ 32B`（MTE 块粒度健康，逐块搬运本身高效）；
- step=1（纯连续拷贝，直接大块 MTE）。

## 3. 正确性红线

- **Gather 的 srcOffset 单位是字节**（相对 src 基地址），不是元素索引——写成 `i/2` 会读错且可能越界触发 vector core 异常。
- **int16→int32 的 Cast 在 dav_c220 无 intrinsic**，不要尝试位扩展路线；`Ands`（标量按位与）在该平台也无实现，用 **tensor 版 And + Duplicate 构造的常量掩码**。
- **MTE3 多块模式会把 UB 侧 src 块起点对齐到 32B**：行段 pitch（len*step*elemSize）非 32 倍数时被静默对齐 → 数据行错位（本例错 8B）；**GM 侧 dst 块 pitch 同样被粗粒度化**。跨行多块写不可靠——**staging 布局把每行段 pad 到 32B 对齐 + 逐行单块 MTE3**。
- **UB 预算**：交错 staging（2×batch×elem）+ idx（2×batch×4B）+ mask（batch×4B）+ 输入队列要一起算；与既有 tileLen 双缓冲叠加易溢出 192KB（溢出表现为 InitBuffer 后第一条 VEC 指令 UB 越界崩）。
- **idx 由标量循环写 UB、后续向量读**：`--cce-auto-sync=off` 下必须显式 `PipeBarrier<PIPE_ALL>()`。
- **相邻段写间隙（step>1 时未被覆盖的位置）依赖输出预清零**——若想省 memset 需另走全量写路径（本例尝试过：V Duplicate→MTE3 的零段链在该直编工具链上偶发丢段，回退；详见提取报告附录）。
- **caller 侧 pageable H2D 与 kernel 直读的竞速**（工具链坑，非本策略自身）：详见附录 A。

## 4. 泛化条件

- **适用**（任一）：固定步长交错写 + 最内连续段 < 32B 的任何 scatter/copy 算子；MTE 块粒度崩塌（块数百万级、MTE3 主导）且目标位置模式编译期已知。
- **不适用**（任一）：数据相关索引（→ GatherMask 压缩策略）；inner ≥ 16（2B dtype）等块粒度健康场景；源/目标无法按行连续组织。

## 5. 实施步骤

1. host 侧 tiling 增加 vecExpand 分派（`step 固定 && inner*elemSize < 32B && 2B dtype`），核间按行（或行组）切分。
2. kernel Init：构造 idx（字节偏移交错表，标量循环 + PipeBarrier）与 mask（`Duplicate<int32>(0x0000FFFF)`）。
3. 主循环按 M 行合批：MTE2 连续读 `M*len` 源元素（inQueue 事件）→ Gather+And 构造 padded 交错流（outQueue 事件）→ 逐行单块 MTE3 写 `len*step*elemSize` 到行起点。
4. rowsPerBatch = min(输入缓冲容量/len, 交错缓冲容量/对齐后行距)。

## 6. LLM 前置问题

- inner×elemSize 是否真的 <32B？MTE3 pipe 占比是否 >60%（有无 profiling 证据）？
- dtype 是否 2 字节？4 字节 dtype 的交错（uint32→uint64）无向量构造，勿套用。
- staging 行段是否 32B 对齐？跨行 MTE3 是否避免多块 stride？
- UB 总预算（含 idx/mask/双缓冲）≤ 192KB 减元数据？

## 7. 验收标准

- build + 精度全过；P4（8192×8192 fp16 step=2, inner=1）：37483us → 3457us（**10.8×**，对 torch 基线 0.32x→3.65x）；P9（363×367×373 bf16 step=2, inner=1, 133K 行）：46706us → 5501us（**8.5×**，0.98x→8.06x）；全量 20 case geo 0.488→1.205，精度 20/20（两次复测 + 120 次稳定性抽样 0 失败）。

## 检索卡（短卡）

动作：将固定步长的小块 strided scatter 搬运，改为通过 vecExpand 执行向量交错展开。
适用：固定步长交错且连续段<32B；或MTE块粒度崩塌、MTE3主导且位置模式编译期已知。
限制：Gather 的 srcOffset 必须使用相对 src 基地址的字节单位，不能用元素索引。
范围：固定步长交错写的 scatter/copy 路径。
检索词：strided scatter、固定步长交错、vecExpand、Gather、srcOffset、MTE3
机会：blockLen小于32B，MTE 块数巨大且由 MTE3 主导。
代价：所示 vecExpand 分派仅覆盖固定 step、小于32B连续段及2B dtype。
