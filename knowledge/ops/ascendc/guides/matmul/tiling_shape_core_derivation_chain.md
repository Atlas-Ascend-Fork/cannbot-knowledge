---
type: Guide
title: Matmul tiling 形状与核数推导链（SetShape/SetSingleShape/GetBaseK/GetCoreNumAic）
description: Matmul tiling 的跨 API 推导契约：平台核数查询（GetCoreNumAic）→ 总分块形状 SetShape 与单核形状 SetSingleShape 的维度区分 → GetBaseK 依赖形状先行的顺序契约 → K 分块数与尾块的模运算回退 → SetBlockDim/CalcTschBlockDim 核数落位；含 tiling 对象与 kernel 对象 SetShape 同名碰撞警示。
tags:
- task.implementation
- topic.implementation.api_layer.high_level_api
- topic.programming_model.execution_unit.cube
status: draft
sources:
- resource: cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score/op_host/arch22/flash_attention_score_tiling_general.cpp
  role: primary
- resource: cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_host/fused_linear_cross_entropy_loss_grad_tiling.cpp
  role: supporting
created_at: '2026-10-12T10:30:11Z'
updated_at: '2026-10-12T10:30:11Z'
platforms:
- '950'
- a2
- a3
---

# Matmul tiling 形状与核数推导链（SetShape/SetSingleShape/GetBaseK/GetCoreNumAic）

## 适用场景

host 侧 tiling 计算中推导 Matmul 分块与核数的场景：从平台核数出发，确定单核形状与总分块形状，再从 tiling 对象回读 baseK 推导 K 分块数与尾块，最终落位 blockDim。矩阵乘主导的算子（attention、cross entropy、grouped matmul 等）共用此推导骨架；65 个固定提交源码文件支撑（transformer 41 / cv 13 / nn 11，家族内条件率 1.00）。

## 链路骨架

提炼自 flash_attention_score 与 fused_linear_cross_entropy_loss_grad 的 tiling 实现：

```cpp
ascendcPlatform.Init();                                   // 平台信息初始化
uint32_t aicNum = ascendcPlatform.GetCoreNumAic();        // ① 平台 AIC 核数

// ② tiling 对象（官方源码以平台对象构造 MultiCoreMatmulTiling）
matmul_tiling::MultiCoreMatmulTiling mm1Tiling(ascendcPlatform);
mm1Tiling.SetDim(aicNum);                                 // 参与计算的 cube 核数
mm1Tiling.SetAType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::NZ, halfDtype);
mm1Tiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, halfDtype);
mm1Tiling.SetCType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, halfDtype);
mm1Tiling.SetBias(false);                                 // 形状配置项按具体 tiling 路线选取
mm1Tiling.SetShape(baseM, H, V);                          // ③ 总分块形状（多核协作维度）
mm1Tiling.SetOrgShape(baseM, H, V);                       // 原矩阵形状
mm1Tiling.SetSingleShape(baseM, baseN, V);                // 单核形状（单核实际维度）
mm1Tiling.SetFixSplit(baseM, baseN, baseK);               // 固定切分块

// ④ 先执行 tiling 计算并检查结果（官方接口要求计算完成后才能回读参数）
int64_t ret = mm1Tiling.GetTiling(tiling.mm1Tiling);
if (ret == -1) { OP_LOGE(context->GetNodeName(), "GetTiling failed."); return ge::GRAPH_FAILED; }

// ⑤ 同一 tiling 对象回读分块参数，推导分块数与尾块（整除时回退整块）
// 维度对应：mm1 的 SetShape(baseM, H, V) = (M, N, K)——K 是 V；M 方向按本算子输出的 BT 行计数
// （官方源码 mm1BaseMCnt 即用 BT）。mm2 的 SetShape(baseM, H, BT) 才以 BT 为 K——两条 tiling 的 K 不可混用。
uint32_t mm1BaseMCnt = (BT - 1) / mm1Tiling.GetBaseM() + 1;
uint32_t mm1TailM    = BT % mm1Tiling.GetBaseM();
if (mm1TailM == 0) { mm1TailM = mm1Tiling.GetBaseM(); }
uint32_t mm1BaseKCnt = (V - 1) / mm1Tiling.GetBaseK() + 1;   // K = V（不是 BT）
uint32_t mm1TailK    = V % mm1Tiling.GetBaseK();
if (mm1TailK == 0) { mm1TailK = mm1Tiling.GetBaseK(); }

uint32_t usedCoreNum = std::min(needCoreNum, aicNum);     // ⑥ 实际用核数截断
auto blockDim = CalcTschBlockDim(usedCoreNum, aicNum, aivNum);
context_->SetBlockDim(blockDim);                          // ⑦ 核数落位
```

## 成员职责

| 环节 | API |
|---|---|
| 平台核数 | [GetCoreNumAic](../../apis/utils_api/platform_info/platform_ascend_c/get_core_num_aic.md)（PlatformAscendC 接口） |
| tiling 形状 | [SetShape](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_shape.md)、[SetSingleShape](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_single_shape.md) |
| baseK 回读 | [GetBaseK](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/get_base_k.md)、[MatmulTiling 用法](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/matmul_tiling_usage.md) |
| 核数落位 | SetBlockDim（注册侧 context 接口，用法见 [tiling 序列化指南](../../guides/registration/msopgen_tiling_serialization_and_copy_evidence.md)）、[CalcTschBlockDim](../../apis/utils_api/platform_info/platform_ascend_c/calc_tsch_num_blocks.md) |
| kernel 对象形状 | [Matmul SetSingleShape](../../apis/simd_api/adv_api/cube_compute/matmul_kernel/set_single_shape.md)（同名区分见下） |

## 跨 API 联动约束

1. **配置 → GetTiling → 回读的顺序契约**：`GetTiling()` 依赖形状/类型配置（`SetDim`/`SetAType` 等 → `SetShape`/`SetOrgShape`/`SetSingleShape`/`SetFixSplit`）先行，且必须检查返回值（`-1` 为失败）；`GetBaseM/GetBaseN/GetBaseK` 只有在 `GetTiling` 成功后才返回当前分块参数——官方接口要求在 tiling 计算完成后读取，形状未设或计算失败时回读得到的是默认值/无效值。
2. **两个形状维度不可互替**：[SetShape](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_shape.md) 设置多核协作的总分块形状（可为完整/局部矩阵，支持 -1 按原始形状），[SetSingleShape](../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_single_shape.md) 设置单核实际形状——两者共同决定核数利用率与尾块形态；只设其一会使 baseK 与分块数推导失真。
3. **尾块模运算回退**：`tailK = T % baseK`，整除时 tailK 为 0 必须回退为 baseK（`if (tailK == 0) tailK = baseK`）——漏掉回退会把尾块当零长度处理。
4. **同名对象碰撞警示**：tiling 对象（`MatmulApiTiling mm1Tiling; mm1Tiling.SetShape(...)`，host 侧）与 kernel 对象（`Matmul<...> mm; mm.SetShape(...)`，device 侧）都有 SetShape/SetSingleShape/SetOrgShape——flash_attention 样例中两者并存（`bmm1.SetShape/SetOrgShape` 是 kernel 对象）。检索时按调用对象区分：host tiling 推导链走 matmul_tiling 目录卡，device 复用/尾块重设走 matmul_kernel 目录卡。
5. **核数截断**：实际用核数取 `min(需求核数, 平台核数)`；混合核场景经 `CalcTschBlockDim(usedCoreNum, aicNum, aivNum)` 换算调度 blockDim，AIV/AIC 比例参与（flash 样例：`coreNum / AIV_AIC_NUM_RATIO` 后再 min 上限）。

## 失效边界

- 形状设置顺序颠倒（GetBaseK 先于 SetShape/SetSingleShape）——静默返回默认值，分块数与尾块全部错位；
- 只调 SetShape 不调 SetSingleShape（或相反）——baseK 按单边维度推导，多核切分与尾块计算失真；
- 尾块为 0 未回退——尾块 K 长度按 0 处理，尾块 tile 丢失；
- kernel 对象与 tiling 对象的 SetShape 混查——同名接口不同目录卡，约束与参数单位不同。

## 验证方式

- 单一形状（M=N=K=base）对拍：分块数=1、尾块=base 的退化路径；
- 尾块专项：T % baseK ∈ {1, baseK-1} 的边界值对拍；
- 核数截断：需求核数 > 平台核数时 blockDim 回落平台核数；
- tiling 序列化后 kernel 侧回读对拍（GET_TILING_DATA 与 host 写入一致）。
- **K 维配对回归（mm1 用 V、mm2 用 BT）**：取 `BT=128, V=130, baseK=64` —— mm1 的 K 分块应为 3、尾块 2（130 拆 64+64+2）；若误用 BT 会得到 2 块、尾块 0，形状不同时差异即暴露。
