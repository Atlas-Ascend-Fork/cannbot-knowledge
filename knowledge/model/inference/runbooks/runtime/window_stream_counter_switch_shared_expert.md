---
{
  "type": "Runbook",
  "title": "ge_graph+SuperKernel decode 的流拓扑与 op 形状签名剖析方法（两段串行图段、共享专家流零重叠）",
  "description": "框架/执行模式：自研推理 executor，ge_graph 图模式 + cache_compile（prefill/decode 图拆分），decode 用 SuperKernel 聚合（MIX_AIC/AIV）与 MC2；Hy3-preview 295B bf16，16 die Atlas A3。",
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

# ge_graph+SuperKernel decode 的流拓扑与 op 形状签名剖析方法（两段串行图段、共享专家流零重叠）

## 适用场景

- 平台范围依据：source 0 seq 27的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 框架/执行模式：自研推理 executor，ge_graph 图模式 + cache_compile（prefill/decode 图拆分），decode 用 SuperKernel 聚合（MIX_AIC/AIV）与 MC2；Hy3-preview 295B bf16，16 die Atlas A3。
- 目标：对 SuperKernel 聚合不透明、GQA/MoE 同流交错的 decode profile 做 GQA/Dense/MoE 组件拆解，并判定 decode 多流的真实并发关系。
- 适用于 kernel_details.csv（Level1+PipeUtilization）类 NPU profiler 输出的离线解析。

## 触发与观测

触发一：decode 流×算子交叉统计显示两条计算流都承载主计算（source 0 seq 62）：stream 125 {MatMul 186, SuperKernel 185, ...}、stream 129 {MatMul 294, SuperKernel 294, ...}、stream 128 {SuperKernel 80}，易被误判为并发多流。

触发二：CSV 的 Name 列每算子唯一（distinct Name count step5: 1623，含 `trans_Cast_1`、`aclnnInplaceOne_OnesLikeAiCore_OnesLike` 等），规范化名在 Type 列（source 0 seq 89）。

流 span 逐字输出（source 0 seq 65）：

```text
s125: span=[1782275652339811,1782275652349407] window=9596us busy=8722us occ=91%
s128: span=[1782275652324312,1782275652349186] window=24874us busy=556us occ=2%
s129: span=[1782275652323725,1782275652339808] window=16084us busy=14596us occ=91%
STEP window = 30159us
```

层归属逐字输出（source 0 seq 68）：

```text
QKV proj by stream: Counter({'129': 50, '125': 30})
stream switch at layer 50: s129 -> s125 (qkv idx 1047)

s128 (shared expert stream) sample: first 3 start/dur
  idx98 t=1782275652324311.8 +32.1 in=1,1,4096;4096
  idx132 t=1782275652324994.0 +9.5 in=1,4096
  idx151 t=1782275652325348.0 +5.2 in=1,4096
  s128[0] overlaps 0 s129 ops: []
```

## 探针与操作

- 并发判定探针（source 0 seq 64）：按 stream_id 求 [min(start), max(start+dur)] span、busy、occupancy；s129 span 结束 1782275652339808 与 s125 span 开始 1782275652339811 仅差 3us → 串行。
- 层归属探针（source 0 seq 67）：用 QKV proj MatMul out='4,2560' 作层锚点按流计数，定位切换层。
- 形状签名分桶（source 0 seq 79，实际执行的 classify 代码节选）：

```python
    n=o['normalized_name']; osh=o.get('output_shapes',''); ish=str(o.get('input_shapes',''))
    if n in ('HcomAllReduce','HcomAllGather','hcom_allReduce_'): return ('comm','comm')
    # GQA bucket
    if n=='MatMul' and osh=='4,2560': return ('GQA','qkv_proj')
    if n=='SplitVD' and '2560' in ish: return ('GQA','qkv_split')
    if n=='SuperKernel' and osh in ('4,1,2048;4,1,256',) : return ('GQA','qknorm_rope')
    if n=='SuperKernel' and osh=='4,2048': return ('GQA','attn_core')
    if n=='MatMul' and osh=='4,4096' and '256,128,16,16' in ish: return ('GQA','o_proj')
    if n=='SuperKernel' and osh=='1,4096;1,1,4096': return ('GQA','post_norm')  # post-attn add_rmsnorm
    # MoE router
    if n=='MatMul' and osh=='1,192': return ('MoE','router_gate')
    # MoE big GMM+dispatch+combine SuperKernel (12,3072,4096 ...)
    if n=='SuperKernel' and '12,3072,4096' in ish: return ('MoE','moe_dispatch_gmm_combine')
    # shared expert: MatMul out 1,384 (gate/up 1536/4), SuperKernel 1,384 act, MatMul 1,4096 from 1,384, s128 SK
    if n=='MatMul' and osh=='1,384': return ('MoE','shared_gate_up')
```

层起点锚：input_layernorm SuperKernel out='4,4096;1,1,4096'（79 个）+ layer0 起点 op98；MoE GMM 以 in 含 '12,3072,4096' 识别（79 个）；Dense L0 以 out='1,3328' 识别。

## 机制与判别

- 单 decode step 被切成两段串行 graph segment：s129 = layers 0-49、s125 = layers 50-79（切换点 layer 50），非并发；Agent 解释为两次图捕获/cache_compile 拆分（source 0 seq 66，推断）。
- 共享专家副流 s128（80 ops，每层 1 个）busy 556us、occ 2%，与主计算流 0 重叠——模型中已实现的 shared-expert 二级流在该配置下退化为串行，与 progress.md「多流退化/flag 关闭」记录一致（source 0 seq 69 叙述）。
- stream-sample 组件检测失效的判别依据：组件实例需 one primary stream，而 GQA/MoE 在同一流内逐层交错且跨两段流；形状签名分桶可完整复现 80/79/80 计数（QKV 80、MoE GMM 79、router 79、FA core 80，source 0 seq 53）并与 op_statistic 百分比勾稽。
- 未验证推断：s128 零重叠的根因（调度依赖 vs flag 关闭）本轨迹未区分。

## 验证信号

- tool_observed：流 span/occ、QKV 按流计数与切换层、s128 overlap 计数、Name/Type 列实测、形状签名分桶执行结果（decode 组件求和 100.0%）。
- 本轨迹为单次 profile 的结构观测；不包含对多流改造效果的验证。

## 适用与失效边界

- 流 ID（125/128/129/46）与层切分（50/30）是本次运行的具体值，其他版本/配置会变化；方法（span 串行判定 + 层锚 + 形状签名）可迁移，签名数值随 batch/TP/EP 变化。
- 形状签名依赖 ge_graph 聚合后的固定 shape；batch 改变后 '4,2560' 等需重推导（Q=4,2560 中 2560=2048Q+256K+256V per rank）。
- Name/Type 语义（Name 唯一、Type 规范化）为该框架 profiler 输出的实测约定，版本升级可能改变。
- 不能据 s128 occ 2% 直接断言共享专家多流优化无效——零重叠根因未定位，需在读流依赖/开关 flag 后复测。

## 附：断言存档

- ge_graph+SuperKernel decode（cache_compile 拆分 prefill/decode 图）下，单 decode step 的主计算被切成两段串行 graph segment：s129 覆盖 layers 0-49（QKV proj 计数 50）、s125 覆盖 layers 50-79（计数 30），s129 span 结束（…339808）与 s125 span 开始（…339811）仅差 3us——两段各自 occupancy 91% 但互相串行，不是并发多流。
