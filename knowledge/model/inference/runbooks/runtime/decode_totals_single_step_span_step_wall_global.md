---
{
  "type": "Runbook",
  "title": "小 batch decode 全内存受限结构与 MoE GMM 主导抖动的诊断（Hy3-preview, 16-die Atlas A3, bf16, ge_graph）",
  "description": "模型/部署同 w27-s4-c1：Hy3-preview 295B bf16，16 die Atlas A3，ge_graph + MC2 + GMM + SuperKernel，decode 走图模式。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# 小 batch decode 全内存受限结构与 MoE GMM 主导抖动的诊断（Hy3-preview, 16-die Atlas A3, bf16, ge_graph）

## 适用场景

- 平台范围依据：source 0 seq 19的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/部署同 w27-s4-c1：Hy3-preview 295B bf16，16 die Atlas A3，ge_graph + MC2 + GMM + SuperKernel，decode 走图模式。
- 工作负载：decode 2048 输入 × batch 4（每 step 4 token），取稳态 step5（kept-op Σdur 24114us，10 step 中接近中位；source 0 seq 41）。
- 目标：判定 decode 单步组件结构与 compute/memory 受限类型，识别首要优化目标。

## 触发与观测

触发：decode 单 step 1623 kept ops，SuperKernel 559 / MatMul 480 / Cast 242 / Scatter 160（source 0 seq 44）；框架 op_statistic.csv 显示 SuperKernel MIX_AIC 55.586%、MatMul AI_CORE 22.106%、SuperKernel MIX_AIV 16.474%（source 0 seq 83）。

组件拆解逐字输出（source 0 seq 80）：

```text
=== DECODE TOTALS (single step) ===
step_span (end-to-end) = 30.16ms
step_wall (Σ all op dur) = 24.11ms
  GQA total   = 8.40ms  (34.8% of wall)
  MoE total   = 13.74ms  (57.0% of wall)
  Dense(L0)   = 0.15ms  (0.6% of wall)
  comm(global)= 0.00ms
  head(embed+mask+weightcast) = 0.66ms
  tail(finalnorm+lmhead+argmax) = 0.23ms
  other       = 0.93ms

=== MoE sub-bucket (median per MoE layer, us) ===
  MoE/moe_dispatch_gmm_combine     med=  131.4  total79= 10.55ms
```

MoE dispatch+GMM+combine 聚合 SuperKernel 单桶 10.55ms = 43.8% step_wall，为最大单桶。

## 探针与操作

受限类型探针（source 0 seq 94）：取 raw_ops_details.json 中 aic_mac_ratio / aic_mte2_ratio / aiv_vec_ratio / aiv_mte2_ratio / cube_utilization 中位数，按 `bound = MEM if mte2>mac else (CUBE if mac>0.4 else MIXED)` 分类。

逐字输出（source 0 seq 95）：

```text
bucket                         n  med_us   mac  mte2 v_vec v_mte2  cube%    bound
MoE/dispatch_gmm_combine      79   131.4  0.00  0.00  0.04   0.05   38.3    MIXED
Dense/gate_up                  2    47.0  0.09  0.93  0.00   0.00   89.5      MEM
GQA/attn_core                 80    34.2  0.00  0.02  0.01   0.10   72.8      MEM
GQA/qkv_proj                  80    18.2  0.13  0.89  0.00   0.00   89.4      MEM
GQA/o_proj                    80    16.5  0.14  0.84  0.00   0.00   88.0      MEM
GQA/qknorm_rope               80    15.2  0.00  0.00  0.11   0.02    0.0    MIXED
GQA/post_norm                 80    14.6  0.00  0.00  0.01   0.15    0.0    MIXED
MoE/router_gate               79     8.6  0.23  0.56  0.00   0.00   50.7      MEM
MoE/shared_gate_up           158     5.6  0.12  0.76  0.00   0.00   46.3      MEM
```

层间抖动探针（source 0 seq 118）：逐层 MoE GMM SuperKernel 时延统计 + IQR hi-fence outlier。

逐字输出（source 0 seq 119）：

```text
decode MoE GMM SuperKernel: n=79 min=91.4 max=180.8 med=131.4 mean=133.5 std=17.6
  IQR hi-fence=171.5 outlier MoE layers(idx,us): [(2, 178), (9, 181), (34, 175), (47, 176)]
decode attn_core: n=80 min=29.0 max=41.1 med=34.2 std=2.4
```

## 机制与判别

- batch=4 decode 下全部主桶偏内存受限（qkv/o_proj mte2 0.84-0.89、attn_core 为 KV 读、Dense gate_up mte2 0.93）——权重/KV 加载受限特征，指向权重预取类优化（如 npu_prefetch）为最高 ROI 候选。
- MoE GMM 聚合桶 mac/mte2 显示 0 系 SuperKernel 跨 MIX core 汇总所致（source 0 seq 96，agent 解释）；其 cube 38.3% + 逐层小 tile（12 expert/rank × 少量 token）仍与权重加载受限一致，该部分为 agent_narrative + 每层约 226MB 权重的推导未实测。
- 抖动集中于 MoE GMM（std 17.6us，CV≈13%，4 个 outlier 层）而 attn_core 稳定（std 2.4us），可区分解释为 EP 路由 token 负载不均（source 0 seq 120，agent 归因推断），支持 EPLB/负载均衡类方向；本轨迹未做专家计数实验区分。

## 验证信号

- tool_observed（rank0 kernel_details.csv + op_statistic.csv，本轨迹单次观测）：上述三段统计输出；op_statistic 百分比（MIX_AIC 55.586% 等）与组件拆解可互相勾稽（GMM 43.8% + GQA SK 各桶）。
- 无 baseline/candidate 对照；「权重预取可加速」未在本轨迹实施或验证。

## 适用与失效边界

- 结论限定 batch=4、2048 上下文、bf16、12 expert/rank 的该 decode 配置；batch 增大后受限类型可能转向 compute，需重测管线比率。
- op_statistic.csv 的 Total Time 为 10 step 聚合，百分比才是口径基准（source 0 seq 84 Agent 说明）。
- GMM 桶 MIXED 的比率归零是 SuperKernel 聚合的显示特性，不能据此断言该桶不受内存带宽约束。
- 抖动的 EP 负载不均归因未验证；替代解释（如 HBM 带宽波动、调度）未排除。

## 附：断言存档

- 同模型/场景 decode 单步（step5 稳态，1623 kept ops）：step_wall 24.11ms（step_span 30.16ms，差额为算子间隙+段间同步），组件拆分 MoE 57.0% / GQA 34.8% / Dense(L0) 0.6%；MoE dispatch+GMM+combine 聚合 SuperKernel 是最大单桶 10.55ms（43.8% step_wall，79 层中位 131.4us）。
