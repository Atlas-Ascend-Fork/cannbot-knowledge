---
{
  "type": "Runbook",
  "title": "FA2 → npu_fused_infer_attention_score 迁移的接口映射陷阱（head_num/num_heads、GQA、LSE 形状）",
  "description": "在 Atlas A3（Ascend910_9382，torch 2.10.0+cpu + torch_npu 2.10.0）上把使用 flash_attn 2/3（FA2 `flash_attn_func` 系列）的 GPU 生成模型",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# FA2 → npu_fused_infer_attention_score 迁移的接口映射陷阱（head_num/num_heads、GQA、LSE 形状）

## 适用场景

- 平台范围依据：source 0 seq 59的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 在 Atlas A3（Ascend910_9382，torch 2.10.0+cpu + torch_npu 2.10.0）上把使用 flash_attn 2/3（FA2 `flash_attn_func` 系列）的 GPU 生成模型（本例 daVinci-MagiHuman 15B 单流 DiT，GQA 40Q/8KV 头、head_dim=128）替换为 `torch_npu.npu_fused_infer_attention_score`。
- 迁移时直接沿用 FA2 风格关键字（如 `head_num`）调用，或在 flex/ring attention 分段 LSE 合并逻辑中复用 FA2 的 LSE 形状假设。

## 触发与观测

- 触发（source 0 seq 147-148，tool_observed）：按 FA2 习惯传 `head_num=40` 直接失败，报错逐字：

```text
GQA test failed: Overloaded torch operator invoked from Python failed to match any schema:
Unknown keyword argument 'head_num' for operator 'npu::npu_fused_infer_attention_score'.
```

- 报错同时暴露完整 schema：正确关键字为 `int num_heads=1, float scale=1., str input_layout="BSH", int num_key_value_heads=0, bool softmax_lse_flag=False`（默认布局 BSH，不是 FA2 varlen 包装常用的形态）。
- 修正后观测（source 0 seq 153-154，tool_observed，设备 micro-test）：

```text
GQA BSND test passed! Output shape: torch.Size([1, 100, 40, 128]) LSE shape: torch.Size([0])
LSE flag test passed! Output shape: torch.Size([1, 100, 40, 128]) LSE shape: torch.Size([1, 40, 100, 1])
Scale test passed! Output shape: torch.Size([1, 100, 40, 128])
```

## 探针与操作

- 探针：随机张量 micro-test `q=(1,100,40,128) k/v=(1,100,8,128)` bf16 上分别验证 `num_heads=40, num_key_value_heads=8, input_layout='BSND'`、`softmax_lse_flag=True` 与 `scale=1/sqrt(128)`。
- 替换要点：`head_num` → `num_heads`；GQA 由 `num_key_value_heads` 原生表达，无需手工 `repeat_interleave` KV 头；BSND 布局 `(B,S,H,D)` 与模型侧 `.unsqueeze(0)` 后的形状直接对齐。

## 机制与判别

- 机制：torch_npu 2.10 的该算子 schema 关键字与 FA2 python API 不同名；GQA 为一等公民参数；LSE 仅在 `softmax_lse_flag=True` 时返回，形状为 `(B, num_heads, S, 1)`，而 FA2 LSE 为 `(B, num_heads, S)`——分段注意力（flex/ring）的 LSE log-sum-exp 合并逻辑必须 `squeeze(-1)` 对齐，否则合并形状不匹配。
- 判别：`Unknown keyword argument 'head_num'` 是关键字不匹配的确定性报错，可与算子未实现、shape 不支持等失败区分；修正关键字后同一输入设备端通过，证明非算子能力问题。

## 验证信号

- 两次 micro-test 均为设备执行输出（source 0 seq 148/154，tool_observed）。
- 该替换随后进入整网迁移：distill T2V 二次运行模型加载成功（28.57GB 权重无 missing/unexpected keys，VAE/audio VAE/T5 依次加载至 47.9GB），但在 `torch.random.fork_rng(devices=[torch.npu...])` 处崩溃（source 0 seq 394，tool_observed；异常尾段被截断，根因未闭合），本轨迹未完成端到端视频生成验证。

## 适用与失效边界

- 适用：torch_npu 2.10.0 / CANN 9.0 上 FA2→NPU 注意力算子替换的接口对齐；GQA（num_heads != num_key_value_heads）场景。
- 失效/停止：LSE 形状结论以本版本 `(B,H,S,1)` 为准，升级 torch_npu 需复验；端到端正确性（视频输出质量）本轨迹未验证，不能据此声称替换后生成质量达标；`fork_rng` NPU 崩溃根因因日志截断未定，另行诊断。

## 附：断言存档

- torch_npu 2.10 的 npu_fused_infer_attention_score 与 FA2 关键字不同名：head_num 报 Unknown keyword argument，正确为 num_heads + num_key_value_heads（GQA 原生支持，无需 repeat_interleave KV），input_layout 默认 BSH、传 BSND 可用
- LSE 仅在 softmax_lse_flag=True 时返回且形状为 (B, num_heads, S, 1)，FA2 为 (B, num_heads, S)；分段注意力 LSE 合并需 squeeze(-1) 对齐
