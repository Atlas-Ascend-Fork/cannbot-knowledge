---
type: Optimization
title: "已验证方案：MLA preprocess 的 cube 调度与流水重排"
description: "面向含多个 GEMM 与向量段的 preprocess 类算子，按「cube 调度模板、核占用整除对齐、向量段重写」三个方向优化；本卡记录适用判据与已否定的路径。"
tags:
  - task.optimization
  - topic.attention
  - topic.programming_model.execution_unit.cube
  - topic.programming_model.execution_unit.vector
  - topic.data_movement.data_copy
  - topic.memory
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_mdl_template.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/best_practices/matmul_tuning_cases/matmul_tiling_strategy.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/mla_preprocess_cfg_mdl_and_core_fill_910b2c.json
    role: evidence
created_at: "2026-10-28T00:00:00Z"
updated_at: "2026-10-28T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 mla-preprocess-cfg-mdl-and-core-fill-910b2c）。
>
> 原始元数据：
>
> ```yaml
> id: mla-preprocess-cfg-mdl-and-core-fill-910b2c
> op_families: [matmul, attention, reduction, cv-mix]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/mla_preprocess_cfg_mdl_and_core_fill_910b2c.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/mla_preprocess_cfg_mdl_and_core_fill_910b2c.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# 已验证方案：MLA preprocess 的 cube 调度与流水重排

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 算子结构

```
K1 mla_gemm (AIC) qkv = hidden[T,H] @ W1^T [T, 2112] N=2112, K=H
K2 mla_vec1 (AIV) q_c 行 RMSNorm → qcn；kv_c RMSNorm → out_kv；k_pe RoPE → out_kpe
K3 mla_gemm (AIC) out_q = qcn[T,1536] @ W2^T [T,128,192] N=24576, K=1536
K4 mla_vec2 (AIV) out_q 每 head 末 64 通道就地 RoPE
```

四段同 stream 顺序 launch，段间无跨核旗语。冷启动分段（T=8192, H=5120，基线内核）：
G1 1808us / vec1 369us / G2 3840us / vec2 953us。

## 三个有效改造（按收益排序）

### 1) G2 换 cube 调度 CFG_NORM → CFG_MDL（**最大单点**，1.0982 → 1.1686）

判据：`baseM*baseN*4 = 128*256*4 = 128KB` **恰好占满 L0C** ⇒ 单累加器；`CFG_NORM` 下
K 方向累加必须整体排空后，下一个 tile 的 MMAD 才能拿到 L0C 地址 ⇒ MMAD 与排空几乎无重叠。
换 `CFG_MDL`（多数据加载 / outer-product 调度，`enUnitFlag=false`）后 G2 段 3795us → 2905us
（steady msprof）。**归因说明**：`UnitFlag` 的官方语义是 **MMAD↔FIXPIPE** 的 512B 同步，
不是 MTE1↔MMAD 的绑定开关；本处应表述为「调度模板改变 + profiling 观测」，若要声称
MTE1/MMAD 独立流水，需补 Matmul 模板或生成指令级证据。详见 **X122**。

G1 原为 `mTotal=2 × nTotal=9 = 18 < 24`（6 个 AIC 空转）；按 `mTotal·nTotal ≡ 0 (mod aicCores)`
`3×baseN` 使 `nTotal 9→3`」已被本轮后续实验否定（A 重读粒度是 baseN 而非 singleCoreN，G1 明显变慢，

### 3) 向量段重写（vec2 953→570us，vec1 369→120us）

- vec2：整行 128 个 head 的 rope 段在 GM 上是等距栅格（blockLen=128B、gap=256B），
 用**一条 2D `DataCopyPad` 搬完整行** + issue-many/wait-once + 双缓冲 +
 `Mul` level-0 `src1RepStride=0`（显式位图 mask + `BinaryRepeatParams(1,1,1,8,8,0)`）
 把 `[rope]` 的 cos/sin 一条指令广播到全部 head；标量 mask 形态会随当前 mask 状态误判，须用位图。
 DMA 往返从 2730 → 513（每核）。见 **X116 / X112**。
- vec1：把「逐行 3 次小 DMA + 每行一次 ReduceSum + 每行一次 Cos/Sin + 每行多次 PipeBarrier<PIPE_ALL>」
 改为**行块化**（2D `DataCopyPad` 一次搬 nr 行整段、块内 ReduceSum 背靠背下发后只做 1 次 V→S、
 `[rows,rope]` 一次算完 cos/sin）。见 **X116 / X112 / P94**。

## Key code change（形态，非逐行）

```cpp
// tiling 头：host/device 共享
struct MlaGemm { ... int64 mmCfg; }; // 0=CFG_NORM, 1=CFG_MDL

// kernel：模板双实例化，未命中形状执行原机器码
template <typename T, matmul::MatmulConfig CFG> __aicore__ void GemmCore(...);
GemmBody -> mmCfg==1 ? GemmCore<T, CFG_MDL>(...) : GemmCore<T, CFG_NORM>(...);

// host：只改调度，tiling 数值一律不动
g2.mmCfg = (M >= 1024 && N >= 8192 && K == 1536) ? 1 : 0;
```

## 适用条件

- **L0C 恰好被 base tile 占满**（`baseM*baseN*4 == L0C`）是关键判据；若 L0C 有余量，
 先考虑双累加器 ping-pong 而不是 MDL。

## 已实测证伪（勿重复，均在本算子上有数据）

## 该算子的测量口径警告（重要）

harness 每 case 计入一次权重初始化（≈31.4us/MB，H=5120/LoRA 配置 3050us），ref 与 asc 各付一次

## 适用边界与后续可挖点

- 换 MDL 后瓶颈已从「cube 排空气泡」转到「AIC 侧 L1 fill」：G2 的 MTE2 占用明显高于 MAC。
 只能改布局（接口固定）才能再降。
- vec1 已是向量算力主导（aiv_vec 0.62），无可压。

（device5、warm-up=3、共享 ref_cache、全 50 例）：

**内核侧四条方向全部量化否决（勿重复）**：
1. **host 固定开销无效**：计入口径只统计 `AI_CORE / AI_VECTOR_CORE / MEMCPY_ASYNC`，forward 段的
 tiling/aux H2D 与 6 次 `at::empty` 都不产生 device task ⇒ H2D 合并、workspace 复用、X24 纯核 task type
2. **G1 singleCoreN 256→768（nTotal 9→3）负向**：A 面板的 MTE2 重读粒度是 **baseN 而非 singleCoreN**
 （MDL 调度对每个 (m-base, n-base) 对重跑整条 K 循环，L1 环形缓冲只有 `depthA1=2~4` 块，跨 n 留不住长 K），
 所以 nTotal 减少不降低 A 总搬运量；代价是每核 3 块压成 1 块、失去块间重叠。用同 case 内未改动的 G2 段去偏后
4. **向量段 sync 瘦身/行块放大/环深加深在中大 T 上接近中性**，

**残余瓶颈（待验证）**：大 T 的 G2/G1 `aic_mte2≈0.82~0.88` 而 `aic_mac≈0.35~0.62`。
`aic_mte2` 对应 **GM/L2→L1（或 UB）** 方向的搬入，L1→L0 属 **MTE1**，因此该信号至多支持
「外部搬入压力高」，**不能**直接推出 L1→L0 是瓶颈。若要主张 MTE1 受限，需补 MTE1、PipeUtilization
与 L1/L0 带宽的独立证据；在证据补齐前，「绕过 MatmulImpl 手写 L1/L0 流水」只作为待验证假设，
不作为推荐方向。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/mla_preprocess_cfg_mdl_and_core_fill_910b2c.json`；引用时请结合上文适用条件与失效边界判断适用范围。

