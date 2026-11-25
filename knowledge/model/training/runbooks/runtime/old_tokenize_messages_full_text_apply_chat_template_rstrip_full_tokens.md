---
{
  "type": "Runbook",
  "title": "DeepSeek-V4（torchtitan-npu）SFT 须关闭 greedy packing：稀疏注意力路径不消费 attention mask，文档间无隔离",
  "description": "torchtitan-npu（DeepSeek-V4 / deepseek_v4_mini SFT flavor，NPU 训练）把 SFT chat 数据从旧仓 `NonPackedChatDataLoader` 迁到上游 `ChatDataLoaderConfig` 体系时，判定是否允许上游 greedy packing。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# DeepSeek-V4（torchtitan-npu）SFT 须关闭 greedy packing：稀疏注意力路径不消费 attention mask，文档间无隔离

## 适用场景

torchtitan-npu（DeepSeek-V4 / deepseek_v4_mini SFT flavor，NPU 训练）把 SFT chat 数据从旧仓 `NonPackedChatDataLoader` 迁到上游 `ChatDataLoaderConfig` 体系时，判定是否允许上游 greedy packing，以及如何以最小改动（默认行为逐字节不变）加回非打包路径。

## 触发与观测

- 触发（source 0 seq 166/192，用户问询）：当前实现的 dsv4 是否有 attention mask 机制？使用 packing 会带来什么影响？
- 源码验证结论（source 0 seq 185，逐级追到 model.py 底层）：
  - `Attention.forward`（model.py:773）把 `attention_masks` 只传给 `inner_attention`（:801）；
  - `InnerAttention.forward`（:658）真正算注意力的 `self.sparse_attn(q, kv, self.attn_sink, kv_compress, compress_topk_idxs)`（:676）**不接收 attention_masks**，mask 只被转交 `li_loss`（:689）；
  - `DSAIndexerLoss.forward`（:273-302）签名收 `attention_masks` 但函数体从头到尾没用；
  - 滑窗/压缩选择全部按**绝对位置**构建：`GetWindowTopkIdxs`（:350）与 `GetCompressTopkIdxs`（:366）都用 `torch.arange(seqlen)` 在整条序列上算 topk，无文档边界概念。

## 探针与操作

- 判定链（源码级）：对"参数存在≠被消费"做 dead-thread 排查——签名有 `attention_masks` 时必须追到最底层计算调用确认实参。上游 packing 的前提（EOS 边界 + flex/varlen mask 文档隔离）在 dsv4 上两条都不成立：sparse_attn 不吃 mask；indexer/滑窗按绝对位置跨文档取 topk。
- 最小改动实现（默认不变，source 0 seq 212-238/335-348，共 3 文件约 6 行）：
  1. `config/configs.py`：`ChatDataLoaderConfig` 加 `packing: bool = True` 与 `add_bos: bool = True`（默认 True，tau/gsm8k 等现有 config 行为零变化）；
  2. `patches/torchtitan/chat_dataset.py`：`_patched_loader_init` 末尾 `self.dataset._packing = getattr(config, "packing", True)`、`self.dataset._add_bos = getattr(config, "add_bos", True)`；`_patched_iter` 默认 `yield from _orig_iter(self)`（逐字节等于上游），`packing=False` 才走非打包分支（一样本一序列、右 pad `_eos_id`、label `IGNORE_INDEX`、positions=range、超长丢弃、epoch reshuffle seed=42+epoch——与旧仓 NonPackedChatDataset 逐行对齐）；else 分支 `encode(full_text, add_bos=getattr(self, "_add_bos", True), add_eos=False)`；
  3. `config_registry.py` 的 `deepseek_v4_mini_1b_sft`：`packing=False, add_bos=False`，yelp processor 内联，`split: "train[500:1500]"`（HF parquet split 切片是 Arrow 级高效切片，先于 shuffle/DP 分片作用于原始行）。
- BOS 判别实测（source 0 seq 318，逐字）：`encode('').ids = []`、`bos_id = 0`（`<｜begin▁of▁sentence｜>` 存在）、`encode('hello').ids = [33310]` —— HF 层不加 BOS，torchtitan `encode(add_bos=True)` 的 `if not hf_adds_bos and add_bos: insert(bos_id)` 会真实插入，**不是 no-op**。

## 机制与判别

- packing 危害机制（source 0 seq 185）：后一文档 token 经滑窗与压缩 KV 跨文档 attend 前一文档 token，无任何隔离；compressor 压缩比假设长单序列，短样本拼接使稀疏路由/压缩分布偏离单样本推理 regime——训练/推理 regime 不一致，loss 可能更低更平滑但泛化崩坏。
- 等价性判别（source 0 seq 376，逐字）：真实 mini tokenizer（deepseek-v4-mini-1B-init）+ 3 条不同长度 yelp 样本，旧仓 `sft_chat.py` 流水线（apply_chat_template + add_bos=False + 逐轮 mask）vs 新仓 else 分支（add_bos=False + `<|im_start|>assistant\n` header 扫描 mask）：`input_ids equal: True`、`label_ids equal: True`、训练 span 逐 token 相同（`\n5 stars<|im_end|>` 等）、首 token 非 BOS——`ALL ALIGNED: True`。
- 默认路径等价（source 0 seq 440）：`_packing/_add_bos` 默认 True 时三处新增（getattr 透传、yield from 原始 __iter__、encode add_bos=True 字面量）与原实现逐行等价。

## 验证信号

- 源码级（等级：源码审读）：attention mask dead-threading 三级追踪（seq 171-185）。
- CPU 级（等级：CPU 功能验证，真实 tokenizer）：BOS 行为实测（seq 318）；新旧流水线 3 样本逐 token 对齐 ALL ALIGNED: True（seq 376）；`py_compile` 三文件通过（seq 254/353）。
- 缺口：未跑 NPU 训练 step 验证端到端 loss；packing 对比实验（同数据 packing=True vs False 的 loss/泛化差）未做，危害结论是代码机制推断+源码证据。

## 适用与失效边界

- 适用：原生稀疏注意力（compressor/indexer/sparse_attn）模型在 torchtitan 系框架的 SFT 数据管线——"上游 packing 依赖 mask 文档隔离"的假设须逐模型验证 sparse 路径是否消费 mask；迁移非打包 loader 的最小侵入模式（config 默认 True 开关 + patch 内 gate + flavor 级关闭）。
- 失效/不覆盖：消费 attention mask 的标准 dense 注意力模型 packing 仍安全；BOS 结论绑定 deepseek-v4-mini-1B tokenizer（HF 层不加 BOS）；多轮/多样本展开（旧仓 `_is_single_turn` 展开）在非打包分支未补齐（yelp 单轮不需要）；NPU 端到端未验证。

## 附：断言存档

- torchtitan-npu 的 DeepSeek-V4 实现中 attention_masks 是空传（dead-threaded）：Attention.forward 只把它传给 inner_attention；InnerAttention.forward 的稀疏注意力调用 self.sparse_attn(q, kv, attn_sink, kv_compress, compress_topk_idxs) 不接收 mask（只转交 li_loss）；DSAIndexerLoss.forward 签名收 mask 但函数体未用；滑窗/压缩 topk 由 GetWindowTopkIdxs/GetCompressTopkIdxs 用 torch.arange(seqlen) 按整条序列绝对位置构建。因此上游 ChatDataLoader 的 greedy packing（依赖 EOS 边界 + mask 文档隔离）在 dsv4 上造成跨文档 attend 与压缩分布偏移，SFT 必须关闭 packing（一样本一序列右 pad）。

```text
def old_tokenize(messages):
    full_text = tk.apply_chat_template(messages).rstrip("\n")
    full_tokens = tk.encode(full_text, add_bos=False, add_eos=False)
    if full_tokens[-1] != eos_id:
        full_tokens.append(eos_id)
    if len(full_tokens) - 1 > SEQ_LEN:
        return None
    input_ids = full_tokens[:-1]
    shifted = full_tokens[1:]
    labels = [IGNORE_INDEX] * len(shifted)
```

```text
encode('').ids     = []
bos_id             = 0
bos in encode('')  = False
encode('hello').ids= [33310]
```
