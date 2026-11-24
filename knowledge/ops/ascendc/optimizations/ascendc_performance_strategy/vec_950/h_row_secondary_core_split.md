---
type: Optimization
title: 平面轴核空闲时对输出 H 行做二次切分唤醒空闲核
description: 当平面轴 N*C < coreNum 时，对每个 plane 组的输出 H 行段做二次切分（rowSplitNum S = min(coreNum/P, hOut)），blockDim = P*S，唤醒空闲核，每核只处理连续输出行区间 [rowBegin, rowBegin+rowCount)；不触碰计算路径。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/h-row-secondary-core-split.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "硬件边界：结论采集自 ascend950（Ascend950DT, 64 AIV 核）；其他芯片需重新验证 coreNum",
      "路由边界：R0-buffer-mode0-whole-row 与 R1-buffer-mode1-ow-blocked 共享同一 ComputeSplitTiling plane-only 切分，机制对两个 BUFFER_MODE 模板均生效",
      "无硬编码硬件参数：P = min(coreNum, totalPlanes) 全部用 PlatformAscendC 动态获取的 coreNum",
      "零除法契约：host 预计算 baseRowNum/rowRemainder，kernel 仅做一次性除法/取模（每核常量，不在内层循环）",
      "case1/8 优化后进入 microkernel noise floor（17-22us < 测量分辨率），performance.stable=false 由 noise floor 判据产生，retry_recommended=false；这是测量边界不是策略缺陷"
    ],
    "excluded_conditions": [
      "N*C >= coreNum 时 S=1，退化为 plane-only 切分（case5/9/13/15/16 等已满核 case 不受影响）",
      "MTE 带宽饱和的 case（如 case15/16 64 核 MTE2-bound）不期望收益，仅作回归控制",
      "不与 2D 批量搬运策略混改，避免归因混淆",
      "不重试 round1 已证伪的向量化插值路径（rounds/001/decision.json 拒绝边界）"
    ],
    "required_conditions": [
      "主切分轴 plane 数 N*C < coreNum（存在空闲核才启用二次切分）",
      "输出可按 H 行独立切分（每输出行只依赖自己的 h0/h1 输入行，无跨行写依赖）——双线性插值天然满足",
      "host 能预计算行区间起点/长度并下发到 kernel（tiling_data 有空间扩展新字段）",
      "kernel 能从 blockIdx 派生 planeGroupIdx/rowChunkIdx 并限制行循环上界"
    ]
  },
  "classification": "validated_strategy",
  "evidence": [
    {
      "artifacts": {
        "accept": "rounds/002/accept.json",
        "baseline_performance": "baseline/performance.json",
        "build": "rounds/002/build.json",
        "comparison": "rounds/002/comparison.json",
        "decision": "rounds/002/decision.json",
        "implementation": "rounds/002/implementation.md",
        "patch": "rounds/002/patch.diff",
        "performance": "rounds/002/performance.json",
        "strategy": "rounds/002/strategy.json",
        "verify": "rounds/002/verify.json"
      },
      "commit": "e919da1dc88f72a9a92d9dd4d48b800282cfc47c",
      "operator_class": "fused-composite",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted"
    },
    {
      "comparison_sha256": "2b75b484db03b70da3fa41a18ada928087eaaf463b0d79a20c61e4dd7f19c3c3",
      "decision_sha256": "ebd7f72ef7c9727bc6347f4994f35f555a20a2aef492e7eabe871d5dc378ff56",
      "operator_class": "fused-composite",
      "performance_sha256": "9485cc32f57ea2fa865df507f200270d1d7d4e00c45e88740879790543623366",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "d992e0f48a1a007ead14f2751528903a90844c2a8fb984c7fd6045c7821cd77c",
      "verify_sha256": "09a184b01775d6ddb4a97f25ddf430a4fc5feca2ce29f3360d34b7a21f4f91e7"
    },
    {
      "case": "cases 12/15（T2 outer=14<64 欠填充，per-core 串行 chunk 循环 102/427 次）",
      "note": "机制轴一般化：二次切分轴从输出 H 行推广到 per-core 串行 chunk 循环（每 chunk CopyInIndex→Compute→CopyOut 闭合无跨 chunk 状态 ⇒ 区间切分按构造精确）；S=1 退化逐位一致由 15 个满核 T2 例 control 覆盖",
      "operator_class": "index-gather",
      "precision": "20/20 PASS",
      "round": 3,
      "run_id": "<run-id>",
      "speedup": "3.34x / 3.84x（blockDim 14→56，S=floor(64/14)=4；incremental 1.0349）",
      "status": "accepted"
    },
    {
      "comparison_sha256": "3765b2c6fd85c942234fe60bf968d63f769113543015af7f2222cdc132943668",
      "decision_sha256": "e739a910491dcbde6402f7e929a10110ad972350f2525e6025482a54096f4f76",
      "operator_class": "index-gather",
      "performance_sha256": "80d91963d53fd85a61af042da4327772d8f257a06221d5a0692f38cfa738113c",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "72776817ff55918e9db5cae85fe391b74e5b5663868e6e238335917d69797411",
      "verify_sha256": "e3617cda4f5569136710d7097ec93739b1a7ea93bffe7706d38b950919b1dc38"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "core-underutilization",
      "plane-only-tiling-axis"
    ],
    "dtypes": [
      "fp16",
      "fp32",
      "bf16"
    ],
    "pattern": "h-row-secondary-core-split",
    "structure": [
      "host-tiling",
      "blockidx-2d-decomposition",
      "row-interval-split",
      "bilinear-interpolation"
    ]
  },
  "generality": "op_class",
  "id": "RB-R2-H-ROW-SPLIT",
  "implementation_steps": [
    "在 host ComputeSplitTiling 中计算 P = min(coreNum, totalPlanes) 和 S = min(coreNum/P, hOut)，blockDim = P*S",
    "host 预计算 baseRowNum = hOut/S 与 rowRemainder = hOut%S，写入 tiling_data 新字段（planeGroupNum/rowSplitNum/baseRowNum/rowRemainder）",
    "kernel Init 做 blockIdx 二维分解：planeGroupIdx = blockIdx / rowSplitNum，rowChunkIdx = blockIdx % rowSplitNum，派生 rowBegin_/rowCount_",
    "S=1 退化路径：rowBegin_=0、rowCount_=hOut_，与原 plane-only 切分逐位一致",
    "kernel Process 外层 oh 循环上界改为 rowBegin_ + rowCount_，不触碰计算路径",
    "验证已满核 case（N*C >= 64）零回归、目标 case 中位数 >= 1.1x、精度全过"
  ],
  "intent": "消除 core-underutilization 瓶颈：plane-only 切分时 blockDim = min(coreNum, N*C)，当 N*C 远小于 64 时大量核空闲（case11 仅 3/64 核活跃、case17 仅 8/64），wall time 等于每核串行行循环长度。通过 H 行二次切分把空闲核转化为并行行处理，rows_per_core 按切分倍数近似线性下降。",
  "mechanism": "4 处同步修改契约（host tiling + kernel blockIdx 分解/行循环边界）：(1) tiling_data.h 新增 4 个 L3 切分字段 planeGroupNum / rowSplitNum / baseRowNum / rowRemainder；(2) tiling.cpp ComputeSplitTiling 扩展二次切分：P = min(coreNum, totalPlanes)，S = min(coreNum/P, hOut)，blockDim = P*S，host 预计算 baseRowNum = hOut/S 与 rowRemainder = hOut%S（R5 同式零除法分组），S=1 时退化为 plane-only（baseRowNum=hOut、rowRemainder=0）；(3) tiling_key.h ASCENDC_TPL_UI_LIST 不变（无新 tilingMode，dtype/buffer 仍是唯一编译期维度）；(4) kernel Init 做 blockIdx 二维分解 planeGroupIdx = blockIdx/S、rowChunkIdx = blockIdx%S，派生 planeStart/perCorePlaneNum + rowBegin_/rowCount_（除法/取模仅每核一次性常量计算，不在内层循环），Process 外层 oh 循环上界由 hOut_ 改为 rowBegin_+rowCount_。不触碰 VF 计算路径、CopyIn/CopyOut 描述符、dtype 处理、TQue 同步。",
  "name": "平面轴核空闲时对输出 H 行做二次切分唤醒空闲核",
  "operator_class": "index-gather",
  "operator_scope": "双线性插值类重采样 dataflow（每输出行只依赖自身 h0/h1 输入行，行间无写依赖），host tiling 按 plane 轴（N*C）分核且 totalPlanes < coreNum 时存在空闲核的场景",
  "principle": "当主切分轴（plane/N*C）无法占满核数时，若输出存在可独立的次轴（H 行），则在不改变逐元素计算语义的前提下对次轴做二次切分，把 blockDim 从 P 提升到 P*S，使空闲核转化为 wall time 减少。前提是次轴行间无写依赖（双线性插值每输出行只依赖自身 h0/h1 输入行，天然满足）。退化路径 S=1 时与原 plane-only 切分逐位一致，保证已满核 case 零回归。",
  "related_anti_patterns": [
    "tile-ub-budget-mismatch"
  ],
  "risks": [
    "行区间划分错误会导致整行错位（可定位的正确性 bug，精度门禁会立即捕获）",
    "核数趋满后 MTE 带宽竞争可能外溢（case16 控制 case 监控此风险，实测 1.00x 无外溢）",
    "case 优化后延迟低于 microkernel noise floor（<25us）时 CV/relative_mad 系统性超阈值，归类 microkernel_noise_floor、non_retryable、retry_recommended=false；这是测量边界不是策略缺陷"
  ],
  "slug": "h-row-secondary-core-split",
  "summary": "当平面轴 N*C < coreNum 时，对每个 plane 组的输出 H 行段做二次切分（rowSplitNum S = min(coreNum/P, hOut)），blockDim = P*S，唤醒空闲核，每核只处理连续输出行区间 [rowBegin, rowBegin+rowCount)；不触碰计算路径。实测 2.12x（8134->3841us），case11 17.76x、case17 7.67x、case2 3.82x，控制 case 5/9/15/16 全 1.00x 无回归，精度 20/20。",
  "verification": {
    "correctness": [
      "rounds/002/verify.json ok=true，20/20 通过，fingerprint 与 build.json kernel_hash bf607c9c422f7c87 一致",
      "S=1 退化路径与原 plane-only 切分逐位一致（case5/9/13/15/16 全 1.00x 无回归验证）"
    ],
    "performance": [
      "整体 2.12x（基线 8134.4us -> round2 3840.7us，comparison.json），远超 minimum_total_speedup 1.02x",
      "目标 case：case11 17.76x（3->48 核，512->32 行/核）、case17 7.67x（8->48 核，256->43 行/核）、case2 3.82x（16->48 核）、case1 3.39x（16->48 核）、case18 3.75x（16->48 核），全部 >>1.1x",
      "控制 case：case5 1.0001x（64 核 Vector-bound 无回归）、case16 0.9993x（64 核 MTE2-bound 无带宽竞争外溢）、case9 0.9989x、case15 1.0002x，max_regression=0.9993 >= 0.95x",
      "样本稳定：除 case1/8 microkernel_noise_floor 外全部 18 case stable（max cv 0.015967、max relative_mad 0.015908），retry_recommended=false",
      "rollback_signals 全部未触发：精度 20/20、目标 case 全部 >>1.1x、控制 case16 >= 0.95x"
    ],
    "rollback_signals": [
      "精度门禁失败 -> 回退（行区间划分错误会导致整行错位，属可定位的正确性 bug）",
      "目标 case（11/17/2/1/18）中位数 <1.1x -> 证伪（说明瓶颈非核空闲或 MTE 竞争即刻饱和）",
      "控制 case16（64 核 MTE2-bound）回归 <0.95x -> 核数增加引发的带宽竞争外溢，回退或收紧切分阈值",
      "case1/8 microkernel_noise_floor（<25us）是测量边界不是策略缺陷，retry_recommended=false 禁止重采"
    ]
  }
}
-->

# 性能优化策略：平面轴核空闲时对输出 H 行做二次切分唤醒空闲核

单一优化点：当平面轴 N*C < coreNum 时，对每个 plane 组的输出 H 行段做二次切分（rowSplitNum S = min(coreNum/P, hOut)），blockDim = P*S，唤醒空闲核，每核只处理连续输出行区间 [rowBegin, rowBegin+rowCount)；不触碰计算路径。实测 2.12x（8134->3841us），case11 17.76x、case17 7.67x、case2 3.82x，控制 case 5/9/15/16 全 1.00x 无回归，精度 20/20。

## 1. 原理

当主切分轴（plane/N*C）无法占满核数时，若输出存在可独立的次轴（H 行），则在不改变逐元素计算语义的前提下对次轴做二次切分，把 blockDim 从 P 提升到 P*S，使空闲核转化为 wall time 减少。前提是次轴行间无写依赖（双线性插值每输出行只依赖自身 h0/h1 输入行，天然满足）。退化路径 S=1 时与原 plane-only 切分逐位一致，保证已满核 case 零回归。

实现机制：4 处同步修改契约（host tiling + kernel blockIdx 分解/行循环边界）：(1) tiling_data.h 新增 4 个 L3 切分字段 planeGroupNum / rowSplitNum / baseRowNum / rowRemainder；(2) tiling.cpp ComputeSplitTiling 扩展二次切分：P = min(coreNum, totalPlanes)，S = min(coreNum/P, hOut)，blockDim = P*S，host 预计算 baseRowNum = hOut/S 与 rowRemainder = hOut%S（R5 同式零除法分组），S=1 时退化为 plane-only（baseRowNum=hOut、rowRemainder=0）；(3) tiling_key.h ASCENDC_TPL_UI_LIST 不变（无新 tilingMode，dtype/buffer 仍是唯一编译期维度）；(4) kernel Init 做 blockIdx 二维分解 planeGroupIdx = blockIdx/S、rowChunkIdx = blockIdx%S，派生 planeStart/perCorePlaneNum + rowBegin_/rowCount_（除法/取模仅每核一次性常量计算，不在内层循环），Process 外层 oh 循环上界由 hOut_ 改为 rowBegin_+rowCount_。不触碰 VF 计算路径、CopyIn/CopyOut 描述符、dtype 处理、TQue 同步。

## 2. 性能问题模式

- 优化目标：消除 core-underutilization 瓶颈：plane-only 切分时 blockDim = min(coreNum, N*C)，当 N*C 远小于 64 时大量核空闲（case11 仅 3/64 核活跃、case17 仅 8/64），wall time 等于每核串行行循环长度。通过 H 行二次切分把空闲核转化为并行行处理，rows_per_core 按切分倍数近似线性下降。
- 适用数据流：双线性插值类重采样 dataflow（每输出行只依赖自身 h0/h1 输入行，行间无写依赖），host tiling 按 plane 轴（N*C）分核且 totalPlanes < coreNum 时存在空闲核的场景
- Feature signature：`{"bottleneck": ["core-underutilization", "plane-only-tiling-axis"], "dtypes": ["fp16", "fp32", "bf16"], "pattern": "h-row-secondary-core-split", "structure": ["host-tiling", "blockidx-2d-decomposition", "row-interval-split", "bilinear-interpolation"]}`

## 3. 正确性红线

- 行区间划分错误会导致整行错位（可定位的正确性 bug，精度门禁会立即捕获）
- 核数趋满后 MTE 带宽竞争可能外溢（case16 控制 case 监控此风险，实测 1.00x 无外溢）
- case 优化后延迟低于 microkernel noise floor（<25us）时 CV/relative_mad 系统性超阈值，归类 microkernel_noise_floor、non_retryable、retry_recommended=false；这是测量边界不是策略缺陷

资源与硬件约束：

- 硬件边界：结论采集自 ascend950（Ascend950DT, 64 AIV 核）；其他芯片需重新验证 coreNum
- 路由边界：R0-buffer-mode0-whole-row 与 R1-buffer-mode1-ow-blocked 共享同一 ComputeSplitTiling plane-only 切分，机制对两个 BUFFER_MODE 模板均生效
- 无硬编码硬件参数：P = min(coreNum, totalPlanes) 全部用 PlatformAscendC 动态获取的 coreNum
- 零除法契约：host 预计算 baseRowNum/rowRemainder，kernel 仅做一次性除法/取模（每核常量，不在内层循环）
- case1/8 优化后进入 microkernel noise floor（17-22us < 测量分辨率），performance.stable=false 由 noise floor 判据产生，retry_recommended=false；这是测量边界不是策略缺陷

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- 主切分轴 plane 数 N*C < coreNum（存在空闲核才启用二次切分）
- 输出可按 H 行独立切分（每输出行只依赖自己的 h0/h1 输入行，无跨行写依赖）——双线性插值天然满足
- host 能预计算行区间起点/长度并下发到 kernel（tiling_data 有空间扩展新字段）
- kernel 能从 blockIdx 派生 planeGroupIdx/rowChunkIdx 并限制行循环上界

不适用：

- N*C >= coreNum 时 S=1，退化为 plane-only 切分（case5/9/13/15/16 等已满核 case 不受影响）
- MTE 带宽饱和的 case（如 case15/16 64 核 MTE2-bound）不期望收益，仅作回归控制
- 不与 2D 批量搬运策略混改，避免归因混淆
- 不重试 round1 已证伪的向量化插值路径（rounds/001/decision.json 拒绝边界）

## 5. 实施步骤

1. 在 host ComputeSplitTiling 中计算 P = min(coreNum, totalPlanes) 和 S = min(coreNum/P, hOut)，blockDim = P*S
2. host 预计算 baseRowNum = hOut/S 与 rowRemainder = hOut%S，写入 tiling_data 新字段（planeGroupNum/rowSplitNum/baseRowNum/rowRemainder）
3. kernel Init 做 blockIdx 二维分解：planeGroupIdx = blockIdx / rowSplitNum，rowChunkIdx = blockIdx % rowSplitNum，派生 rowBegin_/rowCount_
4. S=1 退化路径：rowBegin_=0、rowCount_=hOut_，与原 plane-only 切分逐位一致
5. kernel Process 外层 oh 循环上界改为 rowBegin_ + rowCount_，不触碰计算路径
6. 验证已满核 case（N*C >= 64）零回归、目标 case 中位数 >= 1.1x、精度全过

## 6. LLM 前置问题

- 目标实现是否满足：主切分轴 plane 数 N*C < coreNum（存在空闲核才启用二次切分）？
- 目标实现是否满足：输出可按 H 行独立切分（每输出行只依赖自己的 h0/h1 输入行，无跨行写依赖）——双线性插值天然满足？
- 目标实现是否满足：host 能预计算行区间起点/长度并下发到 kernel（tiling_data 有空间扩展新字段）？
- 是否命中排除条件：N*C >= coreNum 时 S=1，退化为 plane-only 切分（case5/9/13/15/16 等已满核 case 不受影响）？

## 7. 验收标准

正确性：

- rounds/002/verify.json ok=true，20/20 通过，fingerprint 与 build.json kernel_hash bf607c9c422f7c87 一致
- S=1 退化路径与原 plane-only 切分逐位一致（case5/9/13/15/16 全 1.00x 无回归验证）

性能：

- 整体 2.12x（基线 8134.4us -> round2 3840.7us，comparison.json），远超 minimum_total_speedup 1.02x
- 目标 case：case11 17.76x（3->48 核，512->32 行/核）、case17 7.67x（8->48 核，256->43 行/核）、case2 3.82x（16->48 核）、case1 3.39x（16->48 核）、case18 3.75x（16->48 核），全部 >>1.1x
- 控制 case：case5 1.0001x（64 核 Vector-bound 无回归）、case16 0.9993x（64 核 MTE2-bound 无带宽竞争外溢）、case9 0.9989x、case15 1.0002x，max_regression=0.9993 >= 0.95x
- 样本稳定：除 case1/8 microkernel_noise_floor 外全部 18 case stable（max cv 0.015967、max relative_mad 0.015908），retry_recommended=false
- rollback_signals 全部未触发：精度 20/20、目标 case 全部 >>1.1x、控制 case16 >= 0.95x

回滚信号：

- 精度门禁失败 -> 回退（行区间划分错误会导致整行错位，属可定位的正确性 bug）
- 目标 case（11/17/2/1/18）中位数 <1.1x -> 证伪（说明瓶颈非核空闲或 MTE 竞争即刻饱和）
- 控制 case16（64 核 MTE2-bound）回归 <0.95x -> 核数增加引发的带宽竞争外溢，回退或收紧切分阈值
- case1/8 microkernel_noise_floor（<25us）是测量边界不是策略缺陷，retry_recommended=false 禁止重采

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：tile-ub-budget-mismatch

- resize_bilinear-20260825_024131-b12642（round=2, status=accepted）
- resize_bilinear-20260825_024131-b12642（round=2, status=accepted）
- gather-20260831_113139-a1e0e0（round=3, status=accepted, case=cases 12/15（T2 outer=14<64 欠填充，per-core 串行 chunk 循环 102/427 次）, speedup=3.34x / 3.84x（blockDim 14→56，S=floor(64/14)=4；incremental 1.0349））
- gather-20260831_113139-a1e0e0（round=3, status=accepted）

## 检索卡（短卡）

动作：主 plane 轴未占满核心时，对 H 行二次切分，将 blockDim 从 P 提升到 P*S
适用：N*C<coreNum 且输出 H 行可独立切分时启用
限制：次轴行间不得有写依赖；须重新核对目标平台核心数、UB 容量及 API 支持范围
范围：index-gather 的 plane/N*C 主轴与输出 H 行
检索词：plane-only、H 行二次切分、blockDim=P*S、ComputeSplitTiling
机会：plane-only 的 blockDim=min(coreNum,N*C)，且 N*C 远小于可用核心数
代价：核数趋满后可能出现 MTE 带宽竞争
