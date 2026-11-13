---
{
  "type": "Runbook",
  "title": "SP 与梯度检查点重算 shape 差1：沿 all-to-all 后实际输入核对 cu_seqlens",
  "description": "重算激活shape差1，但完整sp_forward先通过all-to-all恢复QKV的全序列维，完整mask与GDR输入匹配。撤回“mask未切片根因”，按同一步前向/重算的实际输入与缓存继续排查。",
  "tags": [
    "task.debugging",
    "topic.checkpointing"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# SP 与梯度检查点重算 shape 差1：沿 all-to-all 后实际输入核对 cu_seqlens

## 适用场景

torchturbo/transformers 的 Qwen3.5-MoE MLLM SFT，启用 sequence parallel、gradient checkpointing、neat packing 与 GDR/gated delta net。backward 报保存的激活与重算激活 metadata 不一致。

## 触发与观测

来源故障为同一位置的 saved shape `[78419,512]` 与 recomputed shape `[78420,512]`，dtype为bfloat16；关闭 gradient checkpointing 后该报错不再触发。这只能缩小重算相关路径，不能确定是哪项输入或缓存改变。

## 探针与操作

1. 沿完整 `sp_forward` 追踪序列维：入口 hidden_states、投影后的QKV、all-to-all后QKV、GDR实际接收的q/k/v，以及输出恢复局部序列的位置。
2. 在同一训练步、同一层的原前向与重算中分别记录 mask内容摘要/shape、q/k/v shape、cu_seqlens及末项、缓存键与命中状态；将两次调用绑定到同一输入后比较。
3. 若怀疑mask原地修改、buffer复用或缓存，先用上述观测区分，做受控单因素验证；不要仅凭入口张量长度不同修改mask。

## 机制与判别

来源完整实现包含以下序列维流转，而非入口两行就直接调用GDR：

| 位置 | 序列维及含义 |
| --- | --- |
| `sp_forward`入口hidden_states | `T_local = T_full / sp_size` |
| attention_mask与`_get_cu_seqlens` | 使用完整序列`T_full` |
| 投影后`gather_seq_scatter_heads` | 聚齐序列维、切分head维；QKV序列长度恢复`T_full` |
| 卷积与GDR消费q/k/v | 使用all-to-all后的完整序列维及对应cu_seqlens |
| `gather_heads_scatter_seq` | 后续再恢复局部序列输出 |

来源中的关键调用是 `interleaved_qkv = gather_seq_scatter_heads(..., seq_dim=1, head_dim=2, ...)`，随后从该结果取得`T`、构造q/k/v并传给`chunk_gated_delta_rule(..., cu_seqlens=cu_seqlens)`。因此入口的完整mask与局部hidden_states并不构成消费点的长度不匹配。

**不能将“attention_mask未按SP切片”写成已定位根因。** 在此实现中直接把mask切成局部长度，可能反而使完整序列GDR的cu_seqlens和序列边界错误。来源提出的缓存/数据指针复用解释也尚未由同一步前向与重算探针闭合，应保持假设。

## 验证信号

已观察到重算shape差1，完整源码支持all-to-all先恢复QKV序列维。没有采用证据证明切mask或移除缓存后的训练已修复；源码核对不等于设备修复验证。

## 适用与失效边界

适用于这种gather-sequence/scatter-heads的SP实现。其他SP布局应以实际消费点为准；不能套用本例的T关系。重算差异的最终原因仍需绑定真实运行输入、缓存和输出后验证。
