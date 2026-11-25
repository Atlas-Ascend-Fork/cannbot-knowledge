---
{
  "type": "Runbook",
  "title": "MoE ge_graph 的 torch_npu profiling 拆解：SuperKernel 语义段归属与 prefill/decode 通信暴露判别",
  "description": "模型/框架：Hy3-preview 295B MoE Transformer（Dense 层 + Sparse MoE + shared expert，80 层 = 1 Dense + 79 MoE），bf16，executor 框架 `ge_graph`（图模式 + MC2 dispatch/combine + GMM），16 die（8物理卡×2 die）的 Atlas A3",
  "tags": [
    "task.optimization",
    "topic.performance.analysis"
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

# MoE ge_graph 的 torch_npu profiling 拆解：SuperKernel 语义段归属与 prefill/decode 通信暴露判别

## 适用场景

- 平台范围依据：source 0 seq 19的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/框架：Hy3-preview 295B MoE Transformer（Dense 层 + Sparse MoE + shared expert，80 层 = 1 Dense + 79 MoE），bf16，executor 框架 `ge_graph`（图模式 + MC2 dispatch/combine + GMM），16 die（8物理卡×2 die）的 Atlas A3（Atlas A3 类，每 die HBM 64GB）。
- 工作负载：hy3_2k_4batch 基线（输入 2048 token、batch 4）；基线 prefill 1334.28ms、decode 30.42 ms/token。
- 目标：对 torch_npu profiler（A 类布局：kernel_details.csv + op_statistic.csv + step_trace_time.csv + communication.json）产物做模块级耗时拆解时，decode 阶段算子被 SuperKernel 二进制融合而不可直接区分。

## 触发与观测

- 触发：MoE ge_graph decode 的 op_statistic 中 SuperKernel(MIX_AIC) 60.3% + SuperKernel(MIX_AIV) 15.1%，约 75% decode 时间在融合二进制内，op 级拆解失效（prefill 无此现象，全部算子可见）。
- 客观输出（source 0 seq 35，decode op_statistic 前几行）：

```text
0,SuperKernel,MIX_AIC,477,49735.5,49.86,104.267,321.92,60.317
0,MatMul,AI_CORE,1440,15998.84,5.04,11.11,187.96,19.403
0,SuperKernel,MIX_AIV,1200,12433.52,1.86,10.361,94.54,15.079
```

## 探针与操作

- 探针 1（语义段解析，source 0 seq 40 逐字核心）：SuperKernel Name 形如 `sk_decode_layer_split_<id1>_<id2>_start_<OpA>_end_<OpB>`，用正则还原语义区间后按 `OpA -> OpB` 聚合 Duration：

```python
    m=re.search(r'start_(.+?)_end_(.+)', name)
    if m:
        s=re.sub(r'_\d+$','',m.group(1)); e=re.sub(r'_\d+$','',m.group(2))
        key=f"{s} -> {e}"
    else:
        key=name
    agg[key][0]+=1; agg[key][1]+=dur
```

- 样本（source 0 seq 38 逐字）：

```text
sk_decode_layer_split_1445_1452_start_MoeGatingTopK_end_MoeDistributeCombineV2,SuperKernel,MIX_AIC
sk_decode_layer_split_1387_1392_start_RmsNorm_end_HcomAllGather,SuperKernel,MIX_AIV
sk_decode_layer_split_1397_1399_start_ApplyRotaryPosEmb_end_ApplyRotaryPosEmb,SuperKernel,MIX_AIV
```

- 探针 2：step_trace_time.csv 逐 step 读 Computing / Communication(Not Overlapped) / Overlapped / Free。
- 探针 3：对全部 16 个 rank 目录的 kernel_details.csv 逐 rank 聚合 MoE SuperKernel 段、FA 段、MatMul 与总 compute，量化 EP 均衡度。
- 数据质量操作：丢弃 skip_first 后首个采集 step（边界同步污染，见下）。

## 机制与判别

- 段级归属结果（step3，source 0 seq 41）：
  - `MoeGatingTopK -> MoeDistributeCombineV2`（整块 MoE：gating + MC2 dispatch + expert GMM + MC2 combine 融合体）n=79、合计 11687.1us、avg 147.94us——decode 主导段；
  - `FusedInferAttentionScore -> FusedInferAttentionScore` n=80、4468.7us、avg 55.86us；
  - 其余为 RmsNorm/RoPE/ReduceScatter/AllGather 等小段（约 1.2-1.7ms 量级）。
  - 稳态 step4/5 复核（seq 47）：MoE 段 11410.5/13237.8us，FA 段 4459.6/4471.7us，非 SK MatMul 5.3ms。
- 通信暴露判别（step_trace，source 0 seq 38/64）：
  - prefill 单 step：Computing=589233.0us、Communication(Not Overlapped)=547237.48us、Overlapped=0.0 → EP all-to-all（hcom_alltoallv_/MC2）完全串行暴露，约占 Stage 1395258us 的 39%，是 prefill 第一优化杠杆（双流/通信隐藏）。
  - decode 稳态 step4/5：Comm-not-overlapped 仅 683.64/331.2us、Overlapped≈0.2-0.3us → 通信已被 SuperKernel 融进 MoE 段，decode 侧再做通信隐藏收益空间小。两阶段优化对象不同，不能用同一策略。
- EP 均衡判别（source 0 seq 67/70）：decode step4 16 rank MoE SK 段 (max-min)/mean=4.2%（median 11.471ms）、FA 段 4.7%、总 compute 6.7%；prefill 16 rank Stage(wall) spread 1.6%。“慢 rank 专家不均”在本 batch/seq 下不是主导瓶颈。
- 边界步污染（source 0 seq 38/88）：step3 携带一次性 graph-launch 同步 allreduce（hcom_allReduce_ 2 次 avg 约 7226us；step_trace Comm-not-overlapped 7627.56us vs 稳态 683.64/331.2us），稳态分析必须剔除该 step。
- 未验证推断：MoE 段内部 dispatch/GMM/combine 的进一步拆分在 SuperKernel 内不可分，需借助别的采集面（如 msprof 前后端联动），本轨迹未做。

## 验证信号

- tool_observed：decode/prefill op_statistic 全表（seq 35）；step_trace 三行（seq 38）；SuperKernel 语义段聚合表 step3/4/5（seq 41/47）；16-rank 逐 rank 方差统计（seq 67/70）。
- agent_narrative：step3 一次性 sync allreduce 约 14.5ms 的定性与"graph-launch sync"归因（seq 88）；MoE≈60%/GQA≈28% 的百分比组合。
- 单模型单 case 一次采集（16 rank 完整、prefill active=1、decode active=3）；基线轮无前轮对照。

## 适用与失效边界

- 适用：Ascend torch_npu profiler（ASCEND_PROFILER_OUTPUT A 类布局）+ ge_graph MoE 类模型 decode 拆解；SuperKernel Name 含 start/end 语义编码是前提。
- 失效：SuperKernel Name 不带语义区间、或需要 MoE 段内部 (dispatch vs GMM vs combine) 细分时，本探针只到段级；decode MatMul M=1~4 已近 memory-bound 下界，不适合用算子级 gap 分析。
- 停止/回退条件：采集必须弃首步（边界 sync 污染）；若 l2_cache.csv 只含辅助流算子（Hit Rate 全 N/A），不能用它推 MatMul 命中率（另一来源 0ee591d073f2 的平行观察）。
- 环境绑定：Hy3-preview 适配代码（modeling_hy_v3.py：prefill `_moe_ep_manual` 687-733 用 all_to_all_single；decode `_moe_ep_mc2_decode` 743+；expert GMM `npu_grouped_matmul` 480-489）。

## 附：断言存档

- MoE ge_graph decode 下 torch_npu profiler 的 op_statistic 无法做模块级拆解：decode op_statistic 中 SuperKernel(MIX_AIC) 占 60.3%、SuperKernel(MIX_AIV) 占 15.1%（约 75% decode 时间在二进制融合 SuperKernel 内，prefill 无此现象、全部算子可见）；但 SuperKernel 的 Name 编码 start_<op>_end_<op> 语义区间，可据此把融合段归属到 GQA/MoE/通信模块。
- 按语义段聚合后，MoE 块段 sk_decode_layer_split_*_start_MoeGatingTopK_end_MoeDistributeCombineV2（gating+MC2 dispatch+expert 计算+MC2 combine 融合体）主导 decode：step3 中 79 段合计 11687.1us（avg 147.94us），FusedInferAttentionScore 段 80 段合计 4468.7us（avg 55.86us）；step4/5 稳态分别为 11410.5/13237.8us 与 4459.6/4471.7us。
