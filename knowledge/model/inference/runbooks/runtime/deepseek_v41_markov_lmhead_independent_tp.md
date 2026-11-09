---
type: Runbook
title: recipes专用：草稿Markov头的独立TP配置
description: 仅适用于 recipes/CANN Executor 的 DSpark Markov 头：分别核对 embedding、词表修正头与主 LM head 的 TP、token 行及重组通信。
tags:
- task.debugging
- topic.parallelism
- topic.speculative_decoding
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:37:06Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：Markov 头独立 TP
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：草稿Markov头的独立TP配置

## 适用性与框架边界

本卡的 Markov 头、`markov_lmhead_tp_size` 和具体组/配置步骤仅适用于 recipes/CANN Executor 的 DSpark 适配，不是 vLLM 公共参数或已验证的原生投机解码配方。

通用原则：每个预测头应分别核对 token 行归属、词表列分片与负责重组的通信组；不同头无需共用同一 TP 度。

必要条件：必须确实采用文中的 token 条件低秩 Markov 修正分支与相同的行/词表分片协议，才适用下文具体 guard、AllGather/AllToAll 和 reshape。

recipes 专属操作：`embed_tp_size`、`lmhead_tp_size`、`markov_lmhead_tp_size` 的分工、DSpark 元数据检查与通信组注册均为该参考实现合同；不能从这些字段翻译出其它框架的开关。

vLLM 读者可在自身模型实现、参数 weight loader/post-load 和分布式组职责中分别追踪预测头的词表片与 token 行；先确认是否存在同类头。这里只提供职责定位，没有同名参数翻译、接入或版本兼容验证。

## 现象

token 是分词后的序列元素，token ID 是词表中的整数编号。语言模型把每个 token 的 hidden state（H 维特征向量）通过 LM head 投影成 V 个词表分数 logits，再交给采样器。TP 可以沿词表列分片：每个 rank 只产生 V/P 个分数，必须为每个 token 重组成完整词表，才能保持 token ID 与分数列的对应关系。

DSpark 是这里 recipes/CANN Executor 的推测解码实现名称。草稿模型先提出若干候选 token，主模型再验证候选并按接受规则保留可接受部分；本卡不规定具体接受算法。Markov Head 是草稿里的“由 token ID 生成低秩词表修正项”的模块，并非另一个主 LM head。它先查 token embedding 得到 R 维向量，再投影到 V 维；这里的 Markov rank R 指低秩维度，与分布式进程 rank 是两回事。

触发问题是：主模型 lmhead_tp_size 调大后，误认为 Markov 词表头与 embedding 也采用相同分片。三者实际读取不同配置和通信组。结果即使张量元素总数正确，也可能把另一 token 的词表片接过来，不能只检查最后一维是否等于 V。

## 适用场景

仅用于 recipes/CANN Executor 当前 V4.1 的 DSparkMarkovHead 与主模型 forward_lm_head 的权重轴、token 行和通信重组静态排查。源码目标 Ascend 950，CANN 版本未知，未运行 AllGather/AllToAll 或采样。适用粒度 exact_task，路线 recommended_fastpath，表示遵守当前实现约束。

可迁移的是为每个输出头分别追踪“行由谁持有、列由谁持有、哪个组重组”；其它框架是否拥有同类 Markov 修正头、采用何种重组通信，需要在其实际实现中确认。

## 判别方法

在该 recipes 适配中找主模型词表投影、草稿的 token 条件修正分支、两者的权重装载与采样前 logits 汇总入口。其它框架只借鉴这组职责检查，不要求拥有 Markov 分支。对每个入口记录 TP 参数来源、分片轴、组成员、组内 rank 和 token 行顺序。以下具体字段和组名均为 recipes 专属，职责对照如下：

| 模块 | 输入→输出 | TP 配置与通信组 | 应保持的关系 |
|---|---|---|---|
| 主 LM head | hidden [T,H]→logits [T,V] | lmhead_tp_size / lmhead_tp_group | 汇总后每行对应原 token 的完整词表 |
| Markov w1 | token ID [T]→embedding [T,R] | embed_tp_size / embed_tp_group | 词表外片 mask 为零，AllReduce 后取到正确 token 向量 |
| Markov w2 | embedding [T,R]→修正项 [T,V] | markov_lmhead_tp_size / markov_lmhead_tp_group | 分的是输出词表列，不能沿用主 LM head 的组内 rank |

在这条 recipes 分支中，先检查 Markov TP 为正且整除 world_size 与 vocab_size；这只能排除尺寸前提错误。再区分 token 行布局：attn_dp_size==1 时 TP ranks 持有相同 token 行，直接投影并 AllGather 各词表片；attn_dp_size>1 且相应头 TP>1 时，先 AllGather 行，让每个词表片计算者见到待计算的行，再 AllToAll 把完整词表送回原 token 行的持有者。主头与 Markov 头分别使用自己的组与 P。

**教学推演（非 NPU 实测）**：设词表 V=12，Markov TP=2。相同 token 行 t 在两个 rank 上分别得到词表 0–5 和 6–11，按词表次序拼接才是 t 的 12 列。若两 rank 分别持有不同 token 行 a、b，直接拼各自的局部投影会得到“a 的前半词表+b 的后半词表”。本实现先让两 rank 都计算 a、b 的本地词表片，再交换，使持有 a 的一方拿到 a 的两片、b 亦然。若主头 TP=4、Markov TP=2，主头每片 3 列，Markov 每片 6 列；错误复用主头组无法由一次 reshape 修正。

复验时给 token 行与词表片附上可追踪身份，检查汇总后 [T,V] 的每一行均来自同一 token、列顺序覆盖完整词表，再与未分片的对应头输出比较。只要行归属不一致，就先修通信/重排，不继续调采样参数。当前主头还把 prefill 的每请求最后 token 取为 q_len=1，decode 则恢复 bs×q_len；需保留展平顺序才能比较。下面命令仅是 recipes 原仓可选导航：

```bash
rg -n 'DSparkMarkovHead' models/deepseek_v4_1/models/modeling_dspark.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`DSparkMarkovHead.__init__` 的 w1 是按输入 token 词表分片的 embedding，w2 是按输出词表分片的 Linear；二者 tp_size/rank 来源不同。`forward` 返回完整 logits 和 markov_embed。`new_token_ids/mask` 将全局 token ID 转为本片索引并屏蔽非本片 token；`markov_hidden` 是是否聚合 token 行之后的 [行数,R]，`gathered_logits` 则是待重排的词表片。最后 reshape→permute→reshape 将“片优先”顺序还原为“token 优先”。

```python
class DSparkMarkovHead(nn.Module):
    """Add a token-conditioned low-rank vocabulary bias to each proposal step.

    The embedding follows the model TP group.  The vocabulary projection has
    an independent TP setting, controlled by
    ``speculative_config.markov_lmhead_tp_size``.
    """

    def __init__(
        self,
        config: DeepseekV41Config,
        infer_config: InferenceConfig,
        prefix: str,
        comm_manager: CommManager = None,
    ):
        super().__init__()
        self.comm_manager = comm_manager
        parallel_config = infer_config.parallel_config
        self.embed_tp_size = parallel_config.embed_tp_size
        self.attn_dp_size = parallel_config.attn_dp_size
        self.markov_lmhead_tp_size = int(
            infer_config.speculative_config.markov_lmhead_tp_size
        )
        self.vocab_size = config.vocab_size
        self.vocab_size_per_rank = self.vocab_size // self.embed_tp_size
        self.embed_tp_rank = (
            comm_manager.get_rank("embed_tp_group")
            if self.embed_tp_size > 1 else 0
        )
        self.markov_w1 = VocabParallelEmbedding(
            config.vocab_size,
            config.dspark_markov_rank,
            config.pad_token_id,
            torch.bfloat16,
            tp_size=self.embed_tp_size,
            tp_rank=self.embed_tp_rank,
        )
        self.markov_w2 = ColumnParallelLinear(
            config.dspark_markov_rank,
            config.vocab_size,
            bias=False,
            params_dtype=torch.float32,
            quant_config=None,
            tp_size=self.markov_lmhead_tp_size,
            tp_rank=(comm_manager.get_rank("markov_lmhead_tp_group")
                     if self.markov_lmhead_tp_size > 1 else 0),
            prefix=f"{prefix}.markov_w2",
        )

    def forward(self, token_ids: torch.Tensor):
        if self.embed_tp_size > 1:
            new_token_ids = token_ids - self.embed_tp_rank * self.vocab_size_per_rank
            mask = (new_token_ids >= 0) & (new_token_ids < self.vocab_size_per_rank)
            markov_embed = self.markov_w1(new_token_ids * mask) * mask.unsqueeze(-1)
            dist.all_reduce(markov_embed, group=self.comm_manager.get_group("embed_tp_group"))
        else:
            markov_embed = self.markov_w1(token_ids)

        if self.attn_dp_size == 1 or self.markov_lmhead_tp_size == 1:
            markov_hidden = markov_embed
        else:
            markov_hidden = torch.empty_like(markov_embed).repeat(self.markov_lmhead_tp_size, 1)
            dist.all_gather_into_tensor(
                markov_hidden,
                markov_embed,
                group=self.comm_manager.get_group("markov_lmhead_tp_group"),
            )

        logits = self.markov_w2(markov_hidden.float())
        if self.markov_lmhead_tp_size > 1:
            if self.attn_dp_size == 1:
                gathered_logits = torch.empty_like(logits).repeat(self.markov_lmhead_tp_size, 1)
                dist.all_gather_into_tensor(
                    gathered_logits,
                    logits,
                    group=self.comm_manager.get_group("markov_lmhead_tp_group"),
                )
            else:
                gathered_logits = torch.empty_like(logits).view(-1)
                dist.all_to_all_single(
                    gathered_logits,
                    logits.view(-1),
                    group=self.comm_manager.get_group("markov_lmhead_tp_group"),
                )
            logits = gathered_logits.reshape(
                self.markov_lmhead_tp_size, markov_embed.shape[0], -1
            ).permute(1, 0, 2).reshape(markov_embed.shape[0], self.vocab_size)
        return logits, markov_embed
```

`update_model_cfg` 的作用是草稿构造前的元数据检查。`next_n/dspark_block_size` 是候选 token 数，`dspark_markov_rank` 是低秩维度，`dspark_noise_token_id` 是词表 ID；这些与 Markov TP 的进程数分别检查，不能用一个 rank 概念混在一起。整除 guard 后还需检查实际请求布局。

```python
    @staticmethod
    def update_model_cfg(config, infer_config: InferenceConfig):
        """Validate DSpark-only model metadata before draft construction."""
        config.n_mtp_layers = resolve_dspark_proposal_num_layers(config, infer_config)
        target_layer_ids = config.dspark_target_layer_ids
        next_n = infer_config.speculative_config.num_speculative_tokens
        if next_n != config.dspark_block_size:
            raise ValueError(
                f"DSpark requires num_speculative_tokens={next_n} equal to "
                f"dspark_block_size={config.dspark_block_size}."
            )
        if (isinstance(config.dspark_markov_rank, bool)
                or not isinstance(config.dspark_markov_rank, int)
                or config.dspark_markov_rank <= 0):
            raise ValueError("DSpark markov rank must be greater than 0.")
        if (isinstance(config.dspark_noise_token_id, bool)
                or not isinstance(config.dspark_noise_token_id, int)
                or not 0 <= config.dspark_noise_token_id < config.vocab_size):
            raise ValueError(
                "DSpark noise token id must be within the model vocabulary range."
            )
        markov_lmhead_tp_size = int(
            infer_config.speculative_config.markov_lmhead_tp_size
        )
        world_size = infer_config.parallel_config.world_size
        if markov_lmhead_tp_size <= 0 or world_size % markov_lmhead_tp_size != 0:
            raise ValueError(
                f"markov_lmhead_tp_size={markov_lmhead_tp_size} must be positive "
                f"and divide world_size={world_size}."
            )
        if config.vocab_size % markov_lmhead_tp_size != 0:
            raise ValueError(
                f"vocab_size={config.vocab_size} must be divisible by "
                f"markov_lmhead_tp_size={markov_lmhead_tp_size}."
            )
```

`forward_lm_head` 输入 outputs 的轴为 token×H，先按 prefill/decode 决定哪些 token 行进入主头。`bs` 来自请求元数据，`q_len` 是每请求的输出步数；`hidden_states` 是聚合行后的输入，`new_logits` 是通信后的中间词表片。返回值恢复为 [bs,q_len,V]。这是主头的独立流程，不是 Markov w2 的共享汇总器。

```python
    def forward_lm_head(self, outputs, kv_len, is_prefill=True, attn_metadata=None):
        num_tokens, hidden_size = outputs.shape
        seq_used_q = attn_metadata.get("seq_used_q")
        bs = seq_used_q.numel()
        if is_prefill:
            if self.cp_size > 1:
                outputs = self.gather_cp_last_token_hidden(outputs, attn_metadata)
            else:
                gather_index = kv_len - 1
                gather_index = gather_index.unsqueeze(1).repeat(1, outputs.shape[-1])
                outputs = torch.gather(outputs, 0, gather_index).view(-1, 1, hidden_size)
            q_len = 1 # prefill takes the last token
        else: # combine bs and q_len axes for lm_head
            outputs = outputs.view(num_tokens, 1, hidden_size)
            q_len = num_tokens // bs
        if (self.attn_dp_size == 1) or (self.lmhead_tp_size == 1):
            hidden_states = outputs
        else:
            # allgather: (bs / attn_dp, hidden_size) -> (bs, hidden_size)
            hidden_states = torch.empty_like(outputs).repeat(self.lmhead_tp_size, 1, 1)
            dist.all_gather_into_tensor(hidden_states, outputs, group=self.comm_manager.get_group("lmhead_tp_group"))

        logits = self.lm_head(hidden_states) # (lmhead_tp_size * bs / attn_dp, 1, vocab_size / lmhead_tp_size)
        if self.lmhead_tp_size > 1: # -> (bs / attn_dp, 1, vocab_size)
            if self.attn_dp_size == 1:
                new_logits = torch.empty_like(logits).repeat(self.lmhead_tp_size, 1, 1)
                dist.all_gather_into_tensor(new_logits, logits, group=self.comm_manager.get_group("lmhead_tp_group"))
            else:
                new_logits = torch.empty_like(logits).view(-1)
                dist.all_to_all_single(new_logits, logits.view(-1), \
                        group=self.comm_manager.get_group("lmhead_tp_group"))

            # transpose: (lmhead_tp_size * bs / attn_dp, vocab_size / lmhead_tp_size) -> (bs / attn_dp, vocab_size)
            new_logits = new_logits.reshape(
                self.lmhead_tp_size, bs * q_len, logits.shape[1], -1).permute(1, 2, 0, 3)
            logits = new_logits.reshape(bs * q_len, logits.shape[1], self.config.vocab_size)
        logits = logits.reshape(bs, q_len, -1).float()
        return logits
```

通信注册块仅在 Markov TP>1 时建立 markov_lmhead_tp_group。`group_num=world_size/P` 表示有多少个这样的组，`group_size=P` 才是每次词表重组的参与进程数。排查时还要确认实际组成员与 token 布局相配。

```python
    def init_parallel_comm_group(self):
        super().init_parallel_comm_group()
        markov_lmhead_tp_size = int(
            self.infer_config.speculative_config.markov_lmhead_tp_size
        )
        if markov_lmhead_tp_size <= 0 or self.world_size % markov_lmhead_tp_size != 0:
            raise ValueError(
                f"markov_lmhead_tp_size={markov_lmhead_tp_size} must be positive "
                f"and divide world_size={self.world_size}."
            )
        if markov_lmhead_tp_size > 1:
            self.comm_manager.register_group(
                name="markov_lmhead_tp_group",
                group_num=self.world_size // markov_lmhead_tp_size,
                group_size=markov_lmhead_tp_size,
                platform_version=self.platform_version,
            )
```

</details>

## 设计决策

recipes 的 Markov w2 单独控制词表分片，使它不必跟主 LM head 绑定。源码明确以 float32 参数、quant_config=None 构造 w2；不能无依据地套用主头的 MXFP8 或 NZ 后处理。embedding 与输出头的词表分片职责也不同，不能因都涉及 vocab 就共用同一 rank 计算。

## 系统信息

Markov 模块与组注册位于 `models/deepseek_v4_1/models/modeling_dspark.py`，主 LM head 位于 `models/deepseek_v4_1/models/modeling_deepseek.py`。完整代码依赖原工程 Linear、embedding 与 CommManager；外部框架按上述职责寻找对应入口。

## 预防

同时保存 embed_tp_size、lmhead_tp_size、markov_lmhead_tp_size、attn_dp_size 和各组成员。对 prefill/decode 分别核对 token 行恢复，不把“最后一维为 V”作为唯一验收。

## 验证信号

固定源码核对确认 DSparkMarkovHead、草稿元数据 guard、主 LM head 与 Markov 组注册的完整实现。它证明三套配置/组和两类重组分支存在，没有本卡的 CPU 集体通信、NPU 或采样统计结果。（来源平台：源码目标 950；证据等级：artifact_verified。）

## 失效边界

整除检查不证明组中 token 行布局一致，也不证明任意 DP/TP 组合可运行。原生逐 token MTP 不在当前 V4.1 registry 支持中，不能把 Markov 路径等同该功能。未执行真实权重装载、AllToAll、NPU 推理或采样分布验收；自有框架即使拥有同类头，其实现也须另行验证；本卡的 Markov 专名及配置字段不属于 vLLM 公共参数。

## 坏实践

把主头 TP 直接赋给 Markov 头或 embedding；只改 Linear 的分片数却保留旧通信组；把 q_len 展平顺序丢失误诊成采样问题；因词表总宽度正确就认定列归属正确。
