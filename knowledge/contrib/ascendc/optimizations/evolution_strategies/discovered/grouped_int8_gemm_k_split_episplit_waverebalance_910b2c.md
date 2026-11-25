---
type: Optimization
title: "配方：K 跨核 2 分段 + epilogue 扇出 + 波次重整（grouped int8 GEMM）"
description: "8 专家 int8 grouped GEMM + 配对 SwiGLU + 逐行 requant 的调优配方：K 跨核分段、epilogue 扇出与波次重整，并给出 singleCoreN 必须整 slab 等硬前置。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
  - topic.tiling
status: draft
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/grouped_matmul_tuning.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_multi_core_split_k.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/grouped_int8_gemm_k_split_episplit_waverebalance_910b2c.json
    role: evidence
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 grouped-int8-gemm-ksplit-episplit-wavere）。
>
> 原始元数据：
>
> ```yaml
> id: grouped-int8-gemm-ksplit-episplit-wavere
> confidence: single_op
> op_families: [matmul, moe, quantization, cube]
> bottlenecks: [mte2_stall, tiling_imbalance, partial_overlap]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/grouped_int8_gemm_k_split_episplit_waverebalance_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/grouped_int8_gemm_k_split_episplit_waverebalance_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 配方：K 跨核 2 分段 + epilogue 扇出 + 波次重整
## 场景
8 专家 × M_g=2048、K=4096、N=8192 的 int8 grouped GEMM + 按列配对 SwiGLU + 逐行 int8 requant。

## 四段配方（按收益排序，均可叠加）
1. **K 跨核 2 分段 + baseM=128 + fp16 双 C 平面（-114us，2601.5us）**
 `SetSingleShape(curM=128, singleN=8192, singleK=2048)`，A/B 指针按 kHalf 偏移；`depthA1=16` 使 128×2048=256KB 的 A 面板
 **跨 32 个 n-tile 常驻**（msprof L2 读事务 4.362GB = B 4.295 + A 0.067 逐字节吻合）。
 B 回填 5.905→4.295GB。两个 K 段的 int32 部分和写两个 **fp16** C 平面，AIV 相加后再跑原 epilogue。
 ⚠️ **硬前置**：`singleCoreN` 必须是整个 slab（8192）。同几何改 singleCoreN=4096 会静默丢掉 A 常驻（A 被按 n-tile 重读 32 次 = 2.148GB，mte2 6.443GB，3530us）。
2. **epilogue 消费扇出 epiSplit=4（-175us，2426.5us）**
 末 slab 的 SwiGLU+requant 整块（110~225us）全压在 cube 停机之后；把每个 slab 的 128 行按 **8 行粒度**（y/y_scale 独占 32B 扇区）
 收益随 epilogue 单 slab 开销线性放大：基线几何 -69us，双平面四带 epilogue -175us。
3. **波次重整（-63us，2363.5us）——本配方最便宜的一步**
 **只把「余数那 8 个单元」沿 N 切开**（互斥列、同一对 C 平面 ⇒ **零额外 C 字节**），配 `(k*r) % nb == 0` 的分配规则，
4. **（可选）PublishUnit 的 PipeBarrier 精简**：把 flag store 两侧的 `PipeBarrier<PIPE_ALL>` 换成
 `SetFlag/WaitFlag<HardEvent::S_MTE3>` + `<HardEvent::MTE3_S>`，-5.9us（在噪声内）。

## 定量否决规则（本轮实测，可直接复用）
- **+1MB 额外 C 面写 ≈ 0.5~0.75us 墙钟**（K 三分段多一个平面 +268MB → +240us，而它只买到 67.7us 的尾波）。
- **dbL0C=2 通过 baseN=128 换取 MAC/fixpipe 重叠 = +920us**：AIC 的 GM→L1 流按 `(baseK 行 × baseN)` **描述符**计费而非按字节，baseN 减半使描述符数翻倍。
- **填充率不可通过调度回收**：L2 缺失率在多种 L1 环几何与平面布局下基本恒定；kHalf-major 单元序反而更差。
- **MAC 与 fixpipe 近似串行**（dbL0C=1）：aic_mac 1642 + aic_fixpipe 680 = 2321us ≈ 1.04 × AIC span。剩余最大结构奖在此：
 fixpipe 每次 drain 128×256 fp16 是「128 行 × 512B @ 16KB 步长」；若 C 面改成每个 (slab, n-tile) 块连续，可望带来成倍收益（未实测，属候选）。

mac(1642)+fixpipe(683) 的串行链已到硬件地板（见 F21），剩下的可提取量全在 **残差 ~136us**：
固定启停 + 尾 slab 的 epilogue。三项正交、均已用同源 digit-flip paired A/B 验证（设备共卡时
同一二进制 15 分钟漂 106us，跨窗口单样本一律无效）：

5. **协作式尾部 drain（-20~-33us）**：尾波最后 6 个 slab 改由**全部 48 AIV 以 8 行切片 round-robin**
 （96 片 / 48 = 每核 2 片 = 16 行 ≈ 21us），稳态仍用原 fan=4 映射（poll 数不变）。
 8 行是地板：`y_scale` 按 8 行/32B 扇区独占。**不要**改成全局 fan=8（已两次证伪）。
6. **rb_ 1→2（-28.7us 中位）**：每行 UB 30 → 17 B/lane 的两刀——删掉第三个 fp32 工作 tile
 （plane-1 join 改走 `bScr_` 1024-float 分块），四个 fp16 队列 depth 2→1 **但条带 join 完立即
 `FreeTensor`（先释放再发下一块）**，让下块 DMA 覆盖 ~17 条 4096 宽向量指令。
 总 180304B < 189KB 预算 ⇒ rb_=2（板上 printf 实证）。`aiv_scalar` 272.8→156.9，`Task−aiv_time` 53.4→28.9。
 ⚠ rb_=3 算术上不可能（代价 `rb×(8D+9)` B/lane，预算 36.97，rb=3 需 ≤12.3 而仅下游就要 17）。
 ⚠ 另一种「两相 C staging」式的 rb_=2 是**负的（+24.5us）**：只保留 2 条 C 条带使 K-half-1 对暴露。
7. **C 面读描述符合并 + y 批写（-37.6us）**：C 面一行就是 `2*No_` 两个半区，gate `[p0,p0+8KB)` 与
 up `[p0+8KB,p0+16KB)` 在 GM 相邻 ⇒ 每 K 平面发**一条 16KB 连续零 gap 描述符**代替两条 8KB strided
 （4→2 描述符/行）；y 攒 ***4 行 16KB*** 一次 MTE3 写出（4KB 时每行付 4.6× 自身数据时间的 issue+drain，
 16KB 时 1.7×）。`aiv_mte3` 55.9→21.3，`aiv_mte2` 199.4→189.6，`Task−aiv_time` 48.5→29.3。
8. **publish 粒度 + readiness-ordered drain（-19.6us）**：cube 的 publish 粒度无法细到 (slab,nTile)
 （一个 word 对应一次整 N 的 IterateAll，且 epilogue 需要整 4096 宽行做 absmax），实际可做的是

**已证伪、不要重试的尾残差方向**：指令拆分成两条 2048 宽链（每条额外向量指令 +17.7 cyc/行，
真实 MTE2 空闲只有 87.7us，不是 (mac+fixpipe)−mte2 的 166us）；3 深 C 预取 QD=3（硬挂 aicore timeout）；
精简 PublishUnit 的 PipeBarrier（`EpiSlab2` 末尾本来就有 `PIPE_ALL`，值 0us）。

`fixpipe ≥ 304us（L0C 读地板）+ mac 1642us + 残差` ⇒ 墙钟下界 ~2035-2100us。

## 适用条件
大 K（≥2048）、单专家 M_g 能被 baseM 整除、int8/低精度、aic_mte2 或 MAC+fixpipe 主导的 grouped / 普通 GEMM。
若 aic_mac 已贴算力地板则不适用。

## 验证状态

本卡为 `status: draft`：定量结果与运行标识见证据包 `cases/grouped_int8_gemm_k_split_episplit_waverebalance_910b2c.json`；未经独立人工复核，引用前请结合上文适用条件判断边界。
