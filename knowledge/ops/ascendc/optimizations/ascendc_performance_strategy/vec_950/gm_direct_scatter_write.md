---
type: Optimization
title: 按索引空间并行的 GM 直接散射写
description: 沿索引空间分核并直接更新目标 GM，绕过目标值 UB 暂存和逐元素搬运。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/gm-direct-scatter-write.md
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
      "目标平台必须为所选 update/reduce 模式和 dtype 提供正确的 GM 直接写或原子原语",
      "host 必须按索引空间切分且保证每个更新只被一个任务处理，地址计算使用宽整数"
    ],
    "excluded_conditions": [
      "浮点 add/multiply 等无法满足原子或数值契约的模式必须走原有回退",
      "GM 访问模式不支持目标原语、索引无效处理依赖 UB 批逻辑或热点竞争吞吐恶化时不适用"
    ],
    "required_conditions": [
      "scatter 更新可直接映射为目标 GM 地址上的覆盖、min/max 或受支持原子操作",
      "更新之间独立，或同址冲突能由硬件原子语义正确解决",
      "索引空间的任务数足以提供多核并行"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-23",
  "evidence": [
    {
      "after_us": 89.9,
      "before_us": 8314.7,
      "case": "2",
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/scatter/<run-id>/phase6_apply/final_report.md",
      "speedup": 92.5,
      "status": "accepted"
    },
    {
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "round": 2,
      "run_id": "<run-id>",
      "speedup": "incremental 2.4254x; 14 improved/0 regressed; case2 41.21x, case19 38.84x",
      "status": "accepted"
    },
    {
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "round": 4,
      "run_id": "<run-id>",
      "speedup": "incremental 1.154x; case6 amax 1.543x; cumulative 1.9801",
      "status": "accepted"
    },
    {
      "operator_class": "scatter-update",
      "precision": "20/20 PASS",
      "round": 5,
      "run_id": "<run-id>",
      "speedup": "incremental 1.08x; case5 fp32-multiply 1.6557x; cumulative 2.1211",
      "status": "accepted"
    },
    {
      "comparison_sha256": "27dca93c295b42e90fa4dbc1a86f03818b84ceb0be43999d5fa505e905436fc9",
      "decision_sha256": "8ebf0970aafa935cdf01a2d66a57a91ff870df8bee70267925bf84b04b6b7566",
      "operator_class": "scatter-update",
      "performance_sha256": "e3e35db3bcb46fb5769db7fecd0eafd55ef91f430a1b17751d402923eaf63ab7",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "5c46eb2015502afaba537bb2c0313a7aa6f2c92fed01c525b88dc86494e956cf",
      "verify_sha256": "2e012cfd6622fa2255e2bcd9522f883d352a0b703fdc0413e827a29a320dc8ae"
    },
    {
      "comparison_sha256": "c5f63fea37f27610a66ca7ecc2e0e7aae32f772f3e0c69843b98c871185cffae",
      "decision_sha256": "29d29547b51067a0246ca205053ca358a0a9f6fccd9062443c996b32006d8859",
      "operator_class": "scatter-update",
      "performance_sha256": "8bdd5204fe200e17c9580fd20a8bc0b32318978ec39b9949591006cada78b905",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "965a967ff105ac09f7c3efdd534d6fd6ecafbfa08775473af3909fe0e0e959a6",
      "verify_sha256": "fb2483d705d5c6d950d504e113551b438009dca79dc77dc54c0ab7f83ea454e4"
    },
    {
      "comparison_sha256": "9d9e8caa04e916aee161a426daaa476a9e707bb6836a1a6aa5d58c238df01924",
      "decision_sha256": "ca063fc51e2655f66ad20da3cb6afa6738800afa8f40a83f595e704a2335afb8",
      "operator_class": "scatter-update",
      "performance_sha256": "c07e971c1f29be50e31fd5f73c71832bd90b3c9b1cd00eb0d3c1aae8eb7ba362",
      "round": 2,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "e67fa5bde5d46a0fb786b123f464efe88b7e95a1729dc7806d37d2a12fb23fa1",
      "verify_sha256": "c89b76545922eed300817ed3e83c2893732774c9c075f6157b8e36734187b978"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "ub-staging",
      "scalar-address-remap",
      "core-underutilization"
    ],
    "dtypes": [
      "int32",
      "int64",
      "fp16",
      "bf16",
      "fp32"
    ],
    "pattern": "gm-direct-scatter-write",
    "reduce_mode": "update-min-max-supported-add",
    "structure": [
      "direct-gm",
      "index-parallel",
      "runtime-routing"
    ]
  },
  "gain": "case_2 update 8314.7→89.9us（92.5x），case_14 101440→7.6us（约13323x），case_19 int64 update 16828→51.4us（327x）；回退 case_9 持平。",
  "generality": "op_class",
  "id": "SCATTER-GM-DIRECT",
  "implementation_steps": [
    "建立 reduce mode×dtype 的 GM-direct 支持矩阵，并明确无支持组合的回退路径",
    "将任务从输出段或 UB tile 改为索引更新空间切分，使每核处理连续更新区间",
    "直接计算每个更新的目标 GM 地址，使用普通写、min/max 或受支持原子指令提交",
    "移除不再需要的 UB 目标值暂存、逐元素搬入搬出和对应同步",
    "对热点冲突、非法索引、尾更新及全部回退组合执行正确性和性能验证"
  ],
  "intent": "消除简单 scatter 模式中为目标值建立 UB 暂存、逐元素地址重映射和低并行切分造成的固定成本。",
  "mechanism": "按 index/update 空间并行，每个任务直接形成目标 GM 地址；覆盖写和平台支持的 min/max/int32-add 走直接或原子 GM 操作，无法保证语义或精度的 fp add/multiply 等模式保持原实现。",
  "name": "按索引空间并行的 GM 直接散射写",
  "op": "scatter",
  "operator_class": "scatter-update",
  "operator_scope": "目标地址可直接计算、更新模式可由 GM 写或硬件原子表达的 scatter update/reduce 数据流",
  "principle": "当每个更新最终只对应一个 GM 地址时，把目标值搬进 UB 再写回会重复支付描述符、同步和标量重映射成本；直接在 GM 完成更新，并沿索引空间分核，可同时减少中间流量和提高并行度。",
  "provenance": {
    "source_report": "<PERF_ROOT>/AscendSearch/.ksearch-perf-strategy-extraction/scatter/<run-id>/phase6_apply/final_report.md"
  },
  "related_anti_patterns": [
    "per-row-gm-rmw",
    "dk-split-scalar-address-remap"
  ],
  "risks": [
    "对不支持的 dtype/reduce mode 误走直接路径会产生竞态或数值错误",
    "热点索引会串行化原子操作，直接写还必须满足设备 cache 与可见性规则"
  ],
  "schema_version": 2,
  "slug": "gm-direct-scatter-write",
  "source": "external_verified",
  "status": "applied",
  "summary": "沿索引空间分核并直接更新目标 GM，绕过目标值 UB 暂存和逐元素搬运。",
  "verification": {
    "correctness": [
      "覆盖 update/add/min/max/multiply、重复索引、热点冲突、非法索引和全部 dtype，确认所有回退组合生效"
    ],
    "performance": [
      "分别测量 direct 与 fallback 路径，确认 UB 目标暂存和多余搬运消失，非目标模式不回归"
    ],
    "rollback_signals": [
      "出现并发不确定性、cache 可见性错误、模式路由误判或热点分布稳定变慢时回退"
    ]
  }
}
-->

# 性能优化策略：按索引空间并行的 GM 直接散射写

单一优化点：沿索引空间分核并直接更新目标 GM，绕过目标值 UB 暂存和逐元素搬运。

## 1. 原理

当每个更新最终只对应一个 GM 地址时，把目标值搬进 UB 再写回会重复支付描述符、同步和标量重映射成本；直接在 GM 完成更新，并沿索引空间分核，可同时减少中间流量和提高并行度。

实现机制：按 index/update 空间并行，每个任务直接形成目标 GM 地址；覆盖写和平台支持的 min/max/int32-add 走直接或原子 GM 操作，无法保证语义或精度的 fp add/multiply 等模式保持原实现。

## 2. 性能问题模式

- 优化目标：消除简单 scatter 模式中为目标值建立 UB 暂存、逐元素地址重映射和低并行切分造成的固定成本。
- 适用数据流：目标地址可直接计算、更新模式可由 GM 写或硬件原子表达的 scatter update/reduce 数据流
- Feature signature：`{"bottleneck": ["ub-staging", "scalar-address-remap", "core-underutilization"], "dtypes": ["int32", "int64", "fp16", "bf16", "fp32"], "pattern": "gm-direct-scatter-write", "reduce_mode": "update-min-max-supported-add", "structure": ["direct-gm", "index-parallel", "runtime-routing"]}`

## 3. 正确性红线

- 对不支持的 dtype/reduce mode 误走直接路径会产生竞态或数值错误
- 热点索引会串行化原子操作，直接写还必须满足设备 cache 与可见性规则

资源与硬件约束：

- 目标平台必须为所选 update/reduce 模式和 dtype 提供正确的 GM 直接写或原子原语
- host 必须按索引空间切分且保证每个更新只被一个任务处理，地址计算使用宽整数

## 4. 泛化条件

- 策略作用域：op_class：scatter-update

适用：

- scatter 更新可直接映射为目标 GM 地址上的覆盖、min/max 或受支持原子操作
- 更新之间独立，或同址冲突能由硬件原子语义正确解决
- 索引空间的任务数足以提供多核并行

不适用：

- 浮点 add/multiply 等无法满足原子或数值契约的模式必须走原有回退
- GM 访问模式不支持目标原语、索引无效处理依赖 UB 批逻辑或热点竞争吞吐恶化时不适用

## 5. 实施步骤

1. 建立 reduce mode×dtype 的 GM-direct 支持矩阵，并明确无支持组合的回退路径
2. 将任务从输出段或 UB tile 改为索引更新空间切分，使每核处理连续更新区间
3. 直接计算每个更新的目标 GM 地址，使用普通写、min/max 或受支持原子指令提交
4. 移除不再需要的 UB 目标值暂存、逐元素搬入搬出和对应同步
5. 对热点冲突、非法索引、尾更新及全部回退组合执行正确性和性能验证

## 6. LLM 前置问题

- 目标实现是否满足：scatter 更新可直接映射为目标 GM 地址上的覆盖、min/max 或受支持原子操作？
- 目标实现是否满足：更新之间独立，或同址冲突能由硬件原子语义正确解决？
- 目标实现是否满足：索引空间的任务数足以提供多核并行？
- 是否命中排除条件：浮点 add/multiply 等无法满足原子或数值契约的模式必须走原有回退？

## 7. 验收标准

正确性：

- 覆盖 update/add/min/max/multiply、重复索引、热点冲突、非法索引和全部 dtype，确认所有回退组合生效

性能：

- 分别测量 direct 与 fallback 路径，确认 UB 目标暂存和多余搬运消失，非目标模式不回归

回滚信号：

- 出现并发不确定性、cache 可见性错误、模式路由误判或热点分布稳定变慢时回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：per-row-gm-rmw, dk-split-scalar-address-remap

- ksearch-scatter-<run-id>（status=accepted, case=2, speedup=92.5）
- scatter-<run-id>（round=2, status=accepted, speedup=incremental 2.4254x; 14 improved/0 regressed; case2 41.21x, case19 38.84x）
- scatter-<run-id>（round=4, status=accepted, speedup=incremental 1.154x; case6 amax 1.543x; cumulative 1.9801）
- scatter-<run-id>（round=5, status=accepted, speedup=incremental 1.08x; case5 fp32-multiply 1.6557x; cumulative 2.1211）
- scatter-<run-id>（round=2, status=accepted）
- scatter-<run-id>（round=1, status=accepted）
- scatter-<run-id>（round=2, status=accepted）

## 检索卡（短卡）

动作：将任务从输出段或 UB tile 切分改为按 index/update 空间并行，并直接形成目标 GM 地址更新。
适用：更新可映射为目标 GM 覆盖、min/max 或受支持原子操作，且更新独立或冲突可由原子语义解决。
限制：须按 reduce mode×dtype 支持矩阵选择路径，不支持的组合必须回退。
范围：scatter-reduce 的覆盖、min/max 或受支持原子更新。
检索词：GM-direct、index/update 空间、UB tile、reduce mode×dtype、scatter。
机会：简单 scatter 仍建立 UB 暂存、逐元素重映射，并采用低并行切分。
代价：热点索引会使原子操作串行化。
