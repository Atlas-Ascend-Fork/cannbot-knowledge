---
type: "Runbook"
title: "大归约维 fp32 golden 顺序累加致假精度失败"
description: "顺序 fp32 累加 golden 误差 O(N×eps) 大于 kernel ReduceSum 树形归约 O(log N×eps)，大归约维下 golden 偏离 kernel 触发假精度失败；golden 须用 double/pairwise。"
tags: ["task.debugging", "topic.precision", "topic.compute.reduction"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["pairwise_summation", "fp32_accumulation", "golden_oracle"]
---

# 大归约维 fp32 golden 顺序累加致假精度失败

## 现象

在 EuclideanNorm（L2 范数归约）算子 `key_group_tailR` 分支 Kernel 实现完成后，对 ST 套件跑一次端到端：

- 命令：`./build/test_aclnn_group_tailR`（先 `cmake .. && make` 重建测试二进制，`ASCEND_OPP_PATH` 指向 vendors/EuclideanNorm）。
- 首跑 **21/24 PASS，3 个 fp32 大归约维用例失败**：
  - `ararar_6d_fp32`：shape `[2,8,2,8,2,8192]`，actual=4180.35，golden=4178.68，diff=1.67；
  - `arararar_8d_fp32`：shape `[2,8,2,8,2,8,2,8192]`，actual=11824.4，golden=11817.6，diff=6.8；
  - `phase1_r_partial_fp32`：actual=4180.57，golden=4178.9，diff=1.67。
- 关键特征：**actual 略大于 golden**（不是 kernel 算小了），容差 `rtol=1e-5, atol=1e-5`，偏差远超容差。
- 归约规模：`[2,8,2,8,2,8192]` 总 4194304 元素，每个输出沿 R 轴归约 524288 个元素；对比已通过的小 shape 用例（如 `[2,3,4,5,6,7,8]` 总 40320 元素，约 1/1000），小 shape 无此失败。

当时 kernel 已用 `ReduceSum` 实现归约；golden 是测试内自定义的 CPU 朴素顺序累加。编译/链接均通过，无报错。

## 适用场景

- **工程形态**：aclnn ST（黑盒端到端，`aclnnEuclideanNorm` + workspace + stream），属测试轨而非 kernel 实现轨。
- **API 路径**：kernel 侧 `ReduceSum<float, RA, ...>(...)`（Vector 树形归约）；测试侧自定义 CPU golden `acc[outIdx] += xv * xv;`（顺序 fp32）。
- **验证过的平台与 CANN 版本**：Ascend950（dav-3510 / arch35），CANN 9.1.0。仅此平台实测。
- **适用粒度**：`operator_family`（任何使用 `ReduceSum`/树形归约且归约维 N 较大的归约类算子 ST，golden 设计都适用）。
- **路线优先级**：`recommended_fastpath`——golden 累加器升级为 `double`（或直接用 `torch.linalg.vector_norm` 的 pairwise 求和），与 DESIGN spec 一致，不是放松容差。
- **不适用或未验证场景**：归约维 N 很小（如本例的 40320 元素小 shape）时 O(N×eps) 仍低于 1e-5 容差，顺序 fp32 golden 不会假失败，无需升级；bf16/fp16 输入若 golden 已 `.to(fp32)` 计算，单步误差主导在 cast 而非累加顺序，需单独评估。a2/a3 平台未验证，推断可迁移（见 `## 失效边界`）。

## 判别方法

**触发信号（trigger）**：归约类算子 ST 在**大归约维 R 的 fp32 用例**上失败、小 shape 用例通过、actual 与 golden 偏差在 1e-2~1e2 量级（远超 1e-5 容差）、且 actual 不恒小于 golden（顺序累加既可能偏大也可能偏小）。本例：21/24 PASS，3 个 fp32 大-R 用例 diff=1.67/6.8/1.67，actual 略大于 golden。

**探针（probe）**——可执行检查（本例实际执行的命令）：

```bash
cd operators/EuclideanNorm_package/tests/aclnn && \
grep -n 'acc\[\|vector<float>\|double\|float acc\|std::vector<float> acc\|+= xv' \
  test_aclnn.cpp test_aclnn_empty.cpp test_aclnn_group_tailR.cpp | head -20
```

**观测（observation）**：
- golden 形如 `acc[outIdx] += xv * xv;` 且累加器类型为 `float`/`std::vector<float>` → golden 用顺序 fp32 累加。
- 对比 DESIGN §4.1：`grep -n 'vector_norm\|pairwise\|累加\|Golden' docs/<Op>/DESIGN.md`，若 spec 规定 `torch.linalg.vector_norm` 或 pairwise/树形语义 → golden 偏离 spec。

**判别结论（interpretation）**：

归约算子的 ST golden 用**朴素顺序 fp32 累加**（`acc[i] += xv*xv`，N 步串行），而 kernel 用 `ReduceSum` 做**树形/分块归约**。两者累加顺序不同，浮点误差阶不同：

- 顺序累加 n 个同阶量，误差阶为 `O(N × eps × |max|)`；对 524288 元素、`eps(fp32)≈1.19e-7`、`|max|` 在平方和量级（~百万），顺序 fp32 golden 自身漂移可达百级量级，远超 1e-5。
- 树形归约每层两两合并，深度 `log2(N)`，误差阶 `O(log N × eps × |max|)`（约 0.01 量级），远小于 golden 的顺序累加误差。

因此**不是 kernel 不准，而是 golden 不准**：golden 的顺序累加偏离真值更多，与更准的 kernel 输出相比超出容差，表现为 actual 略大于 golden（kernel 更接近真值）。DESIGN §4.1 已规定 fp16/bf16/fp32 的 golden = `torch.linalg.vector_norm(x.to(fp32), ord=2, dim=axes, keepdim=keep_dims)`，其内部用 pairwise summation（树形语义）；但 ST 自定义 CPU golden 没有遵循 spec，用了朴素顺序累加，**这是 golden 偏离 spec 的测试脚手架 bug，不是 kernel bug**。

判别要点：若 kernel 用 `ReduceSum`（树形归约）且 golden 用顺序 fp32、失败仅出现在大 R fp32 用例、actual 量级合理（不是全零/NaN）→ 假精度失败，根因在 golden，不在 kernel。

## 验证信号

以下信号均来自 key_group_tailR Kernel 实现子会话在 Ascend950 上的实测：先跑 `./build/test_aclnn_group_tailR` 得 21/24，3 个 fp32 大-R 用例失败（具体偏差见 `## 现象`）；随后把 golden 累加器从 `float` 升级为 `double`（DESIGN §4.1 spec 口径），重建重跑得 24/24 PASS exit 0；`./run.sh` 全分支无回归。

- 21/24 PASS，3 个 fp32 大-R 用例失败，diff=1.67/6.8/1.67，actual 略大于 golden（来源平台:Ascend950；证据等级:tool_observed）
- golden 累加器 float→double 后重跑 24/24 PASS，exit 0（来源平台:Ascend950；证据等级:tool_observed）
- 全分支 run.sh 76/76 PASS 无回归（来源平台:Ascend950；证据等级:tool_observed）

## 预防

- 归约类算子 ST 的 CPU golden 一律用 `double` 累加器或 pairwise 求和（`torch.linalg.vector_norm` / `std::reduce` 分块累加），不要用 `std::vector<float>` 顺序 `+=`；golden 的数值稳定性必须**不低于** kernel 的树形归约，否则大 N 下 golden 自身误差主导，产生假失败。
- 在 DESIGN 的 §4.1 Golden 章节显式写明累加语义（pairwise/tree），ST 实现逐行对照 spec，避免"自定义 CPU golden 默默退化成顺序累加"。
- 失败用例先判 actual 是否"量级合理且 actual ≈ golden"：若 actual 全零/NaN → kernel bug；若 actual 量级合理但略偏、仅大 N 失败 → 先查 golden 累加顺序，再查 kernel。

## 坏实践

- 见到 fp32 大 R 失败就直接放宽 `rtol/atol`（如 1e-5→1e-3）让用例过——这掩盖了 golden 自身不准，且一旦 kernel 真有精度回归也测不出。正确做法是升级 golden（更准），容差保持 1e-5 不动。`banned`：放松容差绕过 golden 精度不足。
- 改 kernel 的归约顺序去"凑"顺序 fp32 golden——本末倒置，kernel 的树形归约更准应保留。`banned`：退化 kernel 归约精度以匹配弱 golden。

## 误诊

- 初看 3 个用例失败，第一反应是 kernel 的 group 分支 Phase1/Phase2 实现有 bug（actual 略大于 golden 容易被读成"kernel 多算了一点点"）。实际 kernel 更准、golden 偏小。判别要点：actual 量级合理 + 仅大 N 失败 + golden 是顺序 fp32 → 指向 golden。

## 失效边界

- a2 与 a3 平台未在本例实测；ReduceSum 的树形归约语义在 CANN 跨平台一致，`double` golden 修正与平台无关，**未验证，推断可迁移**。若目标平台 ReduceSum 实现退化（非树形），则"kernel 比 golden 准"的前提不成立，需重新核验。
- 归约维 N 小到 `N × eps(fp32) × |max| < tol` 时（本例约 4e4 元素以下），顺序 fp32 golden 不会假失败，无需升级；临界 N 取决于 `|max|` 与容差，不要把本卡当"所有归约 ST 都必须 double"。

<!-- cannbot:related:start -->
## 相关

- [GetReduceSumMaxMinTmpSize](../../apis/simd_api/adv_api/reduction_operations/reduce_sum_interface/get_reduce_sum_max_min_tmp_size.md)（`exemplifies`）：GetReduceSumMaxMinTmpSize 与《大归约维 fp32 golden 顺序累加致假精度失败》的实质衔接是：该查询返回 ReduceSum 高阶实现所需的最大/最小临时空间；ReduceSum 入口消费这一预算，而多行、累加顺序和 binary_equal 案例给出实际归约验证边界。
- [FP16 scatter 归约逐次回写放大相消误差](low_precision_scatter_reduction_needs_fp32_accumulator.md)（`related`）：判断 FP32 accumulator 修复是否正确前，golden 自身不能用大 N 顺序 fp32 累加；候选给出 double/pairwise 基线以避免把参考误差误判为 kernel 回归。
- [bf16 边缘失败用 fair-oracle 探针判 oracle 不公](bf16_fair_oracle_oracle.md)（`related`）：该卡展示归约顺序较差的 fp32 golden 会制造假失败；与 focal 的输入量化域问题共同构成先验证 oracle 公平性、再判断 kernel 精度的诊断流程。
- [golden BF16 rstd 归约误取 post-BF16 量化值](golden_bf16_rstd_post_bf16.md)（`related`）：The fp32-golden runbook covers a different oracle artifact—host reduction order—providing the next differential check when BF16 input quantization alone does not close rstd mismatch.
- [int32 fp32累加reduce binary_equal不可达](int32_fp32_reduce_binary_equal.md)（`related`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《大归约维 fp32 golden 顺序累加致假精度失败》具体提供“顺序 fp32 累加 golden 误差 O(N×eps) 大于 kernel ReduceSum 树形归约 O(log N×eps)，大归约维下 golden 偏离 kernel 触发假精度失败；golden 须用 double/pairwise。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
<!-- cannbot:related:end -->
