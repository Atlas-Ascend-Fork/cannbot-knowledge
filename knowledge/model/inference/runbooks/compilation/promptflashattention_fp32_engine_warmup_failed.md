---
{
  "type": "Runbook",
  "title": "PromptFlashAttention 在 910_93 无 fp32 engine：融合成功但 warmup 报 Failed to SelectEngine，用 opp binList dtype 清单判别并改选 FlashAttentionScore",
  "description": "fp32 原生 ViT 图把 attention 链融合为 PromptFlashAttention 后模式匹配与建图成功，但 warmup 以 Failed to SelectEngine (Parameter invalid) 失败。探查 CANN 9.1.0 opp 的 ascend910_93 kernel config JSON 的 binList 可直接判别：PFA 的 q/k/v 仅覆盖 bfloat16/float16/int8（6 个 bin），而 FlashAttentionScore 存在 q/k/v=fp32 条目且 q/k/v 为仅有的必填输入。fp32 场景应改选 FlashAttentionScore。",
  "tags": [
    "task.debugging",
    "topic.compilation",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# PromptFlashAttention 在 910_93 无 fp32 engine：Failed to SelectEngine 的判别与 FlashAttentionScore 改选

## 适用场景

- 模型/框架：fp32 原生 onnx ViT 类模型（本例 M400 = ViT-L/14 视觉编码器，DINOv2-reg 风格，24 层，16 头，581 token），经 GE Session v2（GeSession + RunGraphAsync）以 onnx 图模式加载，GE 内存图 pass 融合 attention 链。
- 平台/版本：Ascend 910B 单卡，CANN 9.1.0（aarch64），算子 kernel config 目录 `ascend910_93`。
- 目标与工作负载：单卡推理（batch=1 串行），消除小 BMM 与 [1,16,577,577] 中间量物化（基线画像 attention 链约占 39%）。
- 缺失信息：未在 910B 以外的 SoC 目录（如 ascend910b）复核同名算子的 dtype 支持；未逐一核对其余 FA 族（incre_flash_attention、fused_infer_attention_score 的 JSON 解析在本轨迹中报错未展开）。

## 触发与观测

触发：GE 图融合 pass 将 24 层 attention 链融合为 PromptFlashAttention，模式匹配与建图成功，但 warmup 失败（事件 464）：

```
[FA-PASS] fused 24 attention block(s) into PromptFlashAttention
[ERROR] stage=Warmup obj=RunGraphAsync ret=0 reason=warmup run failed
[GE RESULT] inference failed (fail-fast)
```

plog 深挖（事件 477）给出根因层：

```
[ERROR] GE(3413786,GEsession_test_acl):2026-10-15-11:37:40.515.464 [engine_place.cc:173]3413947 Run: ErrorNo: 1343225857(Parameter invalid!)Failed to SelectEngine.
```

结论一（逐字）：

PromptFlashAttention 在 Ascend 910B（kernel config 目录 ascend910_93，CANN 9.1.0）的 binList 中 q/k/v 输入仅覆盖 bfloat16/float16/int8 三种 dtype、共 6 个 bin，不含 float32；fp32 原生图融合 PFA 后模式匹配与建图成功，但 warmup 阶段以 `Failed to SelectEngine (Parameter invalid)`（engine_place.cc:173，ErrorNo 1343225857）失败。

## 探针与操作

直接读 CANN opp 安装目录下按 SoC 分区的 kernel config JSON，枚举 binList 中前三个输入（q/k/v）的 dtype。对 PFA 的探针（事件 486，原文）：

```
python3 << 'EOF'
import json
p='/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe/kernel/config/ascend910_93/ops_transformer/prompt_flash_attention.json'
d=json.load(open(p))
print("binList count:", len(d["binList"]))
for i, b in enumerate(d["binList"]):
    qkv = [(x["name"], x["dtype"]) for x in b["inputs"][:3]]
    # find attrs in staticKey? look for layout info
    sk = b.get("simplifiedKey", [])
    print(i, "implMode:", b.get("implMode"), "qkv dtype:", [t for _, t in qkv])
EOF
```

对 FlashAttentionScore 的同类探针（事件 494，仅换 json 路径为 `ops_transformer/flash_attention_score.json` 并筛选 fp32 bin）。此外用 glob 扫描全部 `*attention*.json` 汇总各算子 qkv dtype 覆盖（事件 490/491），并读取 ops-info 中的输入/输出 paramType（事件 563/570）。

## 机制与判别

观测（事件 487）：PFA binList 共 6 个 bin，qkv dtype 分别为 bfloat16×2、float16×2、int8×2，无 float32。观测（事件 491/495）：`flash_attention_score.json` 存在 fp32 条目（bin 2），其 inputs 为 query/key/value/real_shift=float32、drop_mask=uint8、atten_mask=uint8、prefix=int64。观测（事件 499）：FAS 的 4 个输出（softmax_max/softmax_sum/softmax_out/attention_out）均为 required。

结论二（逐字）：

FlashAttentionScore 在同一 opp 目录下存在 q/k/v=fp32 的 binList 条目（bin 2：query/key/value/real_shift/padding_mask=float32），且 q/k/v 是仅有的三个必填输入；fp32 原生 ViT attention 融合应改选 FlashAttentionScore 而非 PromptFlashAttention。

可区分的解释分支与判别证据：
- 分支 A「布局（BNSD）不匹配」：被 dtype 探针否证——同一布局约束下 FAS 有可用 engine，且后续以 FAS+input_layout=BNSD 运行成功（事件 581）。
- 分支 B「fp32 无 engine」：被 PFA binList dtype 清单证实（事件 487）。
- 分支 C「换用 vit_flash_attention_score 专用算子」：其实现为 legacy tik、内部 matmul_dtype/vector_dtype 均为 float16（事件 506），不适合 fp32 原生链，排除。
- 关联假设（未在本轨迹内复核）：同仓 M200 模型同为 fp32 且 PFA 验证通过，推测其 attention 链两侧本就有 Cast 对（已是 fp16）。此为助手推断，非本轨迹信号。

## 验证信号

- 事件 464/477：PFA 融合后 warmup 失败 + `Failed to SelectEngine`（平台 Ascend 910B / CANN 9.1.0，plog 证据）。
- 事件 487：PFA binList 6 bin、qkv dtype 仅 bf16/fp16/int8（opp 安装目录 JSON 实测）。
- 事件 491/495：FA 族 dtype 扫描显示 flash_attention_score.json 含 float32；bin 2 的完整输入 dtype 表。
- 事件 499/571：FAS 输出端口 4 个 required；仅 q/k/v 为 required 输入。
- 改选 FAS 后的完整运行与门禁验证见 compilation/flashattentionscore_pass_headnum_nullptr_head_num.md（avg 11.77→9.45ms，-19.7%，单会话同口径）。

## 适用与失效边界

- 结论绑定 CANN 9.1.0 的 ascend910_93 kernel config 实测；CANN 版本或 SoC 目录变化后须重跑本探针（一条 python 命令即可）。
- 仅判别「算子库是否有对应 dtype 的 bin」，不覆盖 shape/布局/属性不匹配导致的其它 SelectEngine 失败形态。
- fp16/bf16/int8 图不受此限制，PFA 本身可用（M200 路径，助手自述）。
- 若业务接受降精度并能通过完整精度门禁，图两侧插入 Cast 后使用 PFA 可作为待测方案；FP32→FP16/BF16 会引入舍入误差，不能视为无条件等价改写，且本轨迹未实测。
