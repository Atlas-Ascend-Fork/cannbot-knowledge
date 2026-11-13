---
{
  "type": "Runbook",
  "title": "随机权重网络上融合组合整网 logits 相关性下降（eager all 0.9966、argmax 翻转）的判别：组合探针定位 + 逐层 hidden 跟踪观察 bf16 误差传播并定位待验证的组合问题",
  "description": "eager attention + 五点全融合时整网 prefill logits cos 0.996563 且 argmax 翻转，而任意单点融合均 ≥0.9999。全组合探针将下降精确定位到 {mlp_swiglu, rope} 组合；逐层 hidden cos 0.999977→0.997908 单调缓变（absmax 0.2617）无单层跳变，支持 bf16 误差传播与随机 lm_head 放大的假设，但不足以排除组合算子或实现问题；默认 Paged 路径同组合全开 cos 0.999912 且 argmax 一致，不受影响。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# 随机权重网络上融合组合整网 logits 相关性下降（eager all 0.9966、argmax 翻转）的判别：组合探针定位 + 逐层 hidden 跟踪观察 bf16 误差传播并定位待验证的组合问题

## 适用场景

- 模型/框架：HYV4 4 层固定种子随机权重（seed=1234，无 checkpoint）独立部署推理；阶段 3 五点融合（moe_experts / moe_router / rms_norm / mlp_swiglu / rope）开启后做整网精度对照。
- 平台/版本：Ascend950PR_9589 单卡、CANN 9.1.0、torch_npu 2.12.0、bf16。
- 目标：融合改造后整网 logits 相关性明显低于模块级指标（且 argmax 翻转）时，区分「真实算子错误」与「bf16 误差逐层传播 + 随机 lm_head 放大（度量放大）」，决定是否需要回退。

## 触发与观测

触发：eager attention 回退路径（`use_paged_fa=false`）+ 五点全融合时，整网 prefill logits 对照（同会话、同构建、teacher-forced；来源记录 事件 177，`fusion_network.json` eager.all，来源 reviewer 复跑得到相同汇报指标）：

```
"all": {
  "prefill_cos": 0.996563,
  "prefill_maxdiff": 0.119611,
  "prefill_argmax_match": false,
  "decode_cos_min": 0.992907
}
```

而同表 eager 单点全部 ≥0.9999（moe_experts 0.999976 / moe_router 1.000001 / rms_norm 1.000001 / mlp_swiglu 0.999905 / rope 0.999921）。默认 Paged 路径 all 为 0.999912、argmax 一致——问题只出现在 eager attention 组合。

## 探针与操作

探针一：全组合枚举（`.scratch/fusion_combo_probe.py`，来源记录 事件 177 原文；对 5 点的 1/2/3 元全部组合重跑 eager prefill 并对照 baseline）：

```
53: def rep(on):
54:     flags(on)
55:     x = eager_prefill(model, ids)
56:     cos = float(torch.nn.functional.cosine_similarity(base.reshape(-1), x.reshape(-1), dim=0))
57:     md = float((base - x).abs().max())
58:     am = int(base.argmax()) == int(x.argmax())
59:     return {"combo": list(on), "cos": round(cos, 6), "maxdiff": round(md, 6), "argmax_match": am}
60:
61:
62: out = [rep(())]
63: for r in (1, 2, 3):
64:     for combo in itertools.combinations(POINTS, r):
65:         out.append(rep(combo))
```

探针二：逐层 hidden 跟踪（`.scratch/fusion_layer_probe.py`，来源记录 事件 176 原文；forward hook 抓每层 4 路 hidden 输出，逐层对照 baseline）：

```
42: captured = []
43: handles = []
44: for i, layer in enumerate(model.model.layers):
45:     def hook(_m, _inp, out, _i=i):
46:         captured.append((_i, out[0].detach().float().cpu()))
47:     handles.append(layer.register_forward_hook(hook))
```

（`fusion_combos.json` / `fusion_layer_probe.json` 为产物；reviewer 事后读取并复核了两个探针的方法学，来源记录 事件 37/38。）

## 机制与判别

- 结论一（定位到组合对）：eager attention 路径上五点全融合整网 prefill logits cos 0.996563、argmax 翻转；组合探针将下降精确定位到 {mlp_swiglu, rope} 组合（cos 0.996574、argmax 翻转），而任意单点融合均 ≥0.9999 且 argmax 不翻转。锚点：来源记录 事件 177（触发观测）；信号：同事件 + 事件 201（组合枚举输出：`{"combo": ["mlp_swiglu", "rope"], "cos": 0.996574, "maxdiff": 0.112293, "argmax_match": false}`，且一切含该二元组的组合均 0.996574/0.996563 级别，不含该二元组的组合均 ≥0.999903）。
- 结论二（误差传播观测，根因尚未隔离）：逐层 hidden cos 0.999977→0.997908 单调缓变（base_hidden_absmax=0.2617），无单层跳变，支持 bf16 误差逐层传播经随机 lm_head 放大的解释，但不能排除系统性小误差或组合实现问题；默认 Paged 路径同组合全开 prefill cos 0.999912 且 argmax 一致。锚点：来源记录 事件 208；信号：同事件（`fusion_layer_probe.json`：mlp_swiglu+rope layer_cos {"0": 0.999977, "1": 0.999507, "2": 0.998656, "3": 0.997908}、prefill_logits_cos 0.996574、base_hidden_absmax 0.2617）+ 来源记录 事件 164（reviewer 独立复跑整网，eager all 0.996563 的汇报指标复现）。
- 判别逻辑（可区分分支）：
  - 若出现逐层离散跳变，应优先检查对应算子；未出现跳变也不能排除每层重复的小幅系统性错误。Paged 与 eager 路径不同，一条路径通过不能证明另一条路径无 bug。
  - 若为度量放大：hidden 逐层缓变、绝对幅度小（absmax 0.2617，末层误差 ~2e-3 相对量），仅经 2816→120832 的随机 lm_head 投影后在 logits 相关性上放大；与全部观测吻合。来源中的 reviewer 曾采纳“非 bug”解释，但该判断不构成排除性实验。
  - 旁证：纯回退（`use_paged_fa=false` + 全关融合）生成 token 与阶段 0 基线相同（来源记录 事件 171 `eager_all_off` token 与 paged_all_off 一致回退形态）；单算子等价性均已独立验证（见 [HYV4 五点 torch_npu 融合替换（MoE init_routing_v2→grouped_matmul→clipped_swiglu→grouped_matmul→finalize_routing 等）的模块级/整网验证与同会话 A/B 性能](../performance/hyv4_torch_npu_moe_init_routing_v2_grouped_matmul.md)）。
- 未验证推断：「随机 lm_head 放大」是当前证据下的最佳解释，未做扰动理论分析；训练后真实权重下 lm_head 放大效应是否同样主导未验证。

## 验证信号

本组来源观测轨迹内客观观测（Ascend950PR_9589 单卡、bf16、随机权重 seed=1234、13 token prompt、单次运行）：

- 触发：来源记录 事件 177（eager.all prefill_cos 0.996563 / maxdiff 0.119611 / argmax_match false / decode_cos_min 0.992907）；来源 reviewer 复跑得到相同汇报指标（来源记录 事件 164）。
- 组合枚举：来源记录 事件 201（`fusion_combos.json`，26 个组合：单点全部 ≥0.999905 且 argmax 不翻；含 {mlp_swiglu, rope} 的组合全部 0.996563–0.996574 且 argmax 翻转）。
- 逐层跟踪：来源记录 事件 208（`fusion_layer_probe.json`：四组探针的 layer_cos 均从 ~0.99998 单调降到 ~0.9972–0.9979，无跳变；prefill_logits_cos 只有 {mlp_swiglu, rope} 组合跌至 0.996574，其余 ≥0.999905）。
- 默认路径不受影响：来源记录 事件 285（paged.all prefill_cos 0.999912 / argmax_match true）；端到端 token 逐位一致（事件 250）。
- 回退旁证：来源记录 事件 171（`eager_all_off [101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480]` 与 `paged_all_on` 同 token、`eager_all_on` 不同 token——纯回退正常）。

## 适用与失效边界

- 本判别基于随机权重（未训练 lm_head）：随机 lm_head 对小 hidden 扰动的放大尤其显著，训练权重下该现象幅度可能不同；误差放大假设未被单独验证，也不外推到真实 checkpoint。
- 当前假设的旁证包括：(a) 单点融合等价性已独立验证；(b) 逐层 hidden 无跳变；(c) 纯回退生成 token 与基线相同。这些旁证均不是排除 bug 的充分条件；需要高精度逐模块参考、舍入消融和实际门禁继续判别。
- eager attention 路径在本部署中仅为回退/诊断路径（默认 `use_paged_fa=true`），其 all 组合 0.9966 不构成默认路径的精度结论；若业务以 eager attention 为主路径且精度口径 ≤1e-3 级，则该组合需按真实风险处理（例如禁用 mlp_swiglu 或 rope 其中之一）。
- argmax 翻转发生在随机权重 logits 的近并列 top-1（CPU golden prefill top1 1.3688 vs top2 1.3374，间隔 ~0.03），对幅值分布敏感；结论不外推到长 prompt/批量场景。
