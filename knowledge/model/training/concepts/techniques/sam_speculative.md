---
type: Concept
title: SAM 无损投机推理（后缀自动机投机解码加速 RL Rollout）
description: SAM 无损投机推理是一种无模型（Model-Free）、基于检索的投机解码方案：用后缀自动机（Suffix Automaton, SAM）在线编码当前生成序列的所有子串，在 O(1) 平均时间内从历史文本中检索「最长匹配后缀 + 后续序列」作为草稿（draft），再由主模型逐 token 验证 + 拒绝采样，保证输出与主模型直接生成严格一致（无损）。它瞄准的是 LLM 强化学习后训练中的 Rollout 采样瓶颈——RL 训练需数百万次交互式生成，其耗时占整个训练链条绝大部分（长序列场景可占 80% 以上，见 vllm-ascend）。
tags:
- task.optimization
- topic.speculative_decoding
- topic.reinforcement_learning
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/sam_decoding.md
  role: supporting
created_at: '2026-06-12T00:00:00Z'
updated_at: '2026-06-26T00:00:00Z'
platforms:
- a3
---

# SAM 无损投机推理（后缀自动机投机解码加速 RL Rollout）

## Summary

**SAM 无损投机推理**是一种**无模型（Model-Free）、基于检索**的投机解码方案：用[**后缀自动机（Suffix Automaton, SAM）**](https://oi-wiki.org/string/sam/)在线编码当前生成序列的所有子串，在 O(1) 平均时间内从历史文本中检索「最长匹配后缀 + 后续序列」作为草稿（draft），再由主模型逐 token 验证 + 拒绝采样，保证输出与主模型直接生成**严格一致（无损）**。它瞄准的是 LLM 强化学习后训练中的 **Rollout 采样瓶颈**——RL 训练需数百万次交互式生成，其耗时占整个训练链条绝大部分（长序列场景可占 80% 以上，见 [vllm-ascend](../frameworks/vllm_ascend.md)）。

与依赖辅助草稿模型的投机方法（EAGLE-3 / [MTP](../../../inference/concepts/techniques/mtp_speculative_decoding.md)）相比，SAM **不引入任何额外模型参数**：既省去训练 draft model / auxiliary head 的成本，又**不必担心 RL 中模型权重频繁更新导致的草稿分布漂移**，且训练时无需额外内存管理——这对训推共卡的 Colocate 框架（[verl](../frameworks/verl.md) 全共卡部署）尤为友好，对现有系统即插即用。在 [Qwen3 RL](../../guides/recipes/qwen3_rl.md) 上（GRPO/DAPO 2K+32K）带来约 +10% 的端到端收益。

## SAM 原理：后缀自动机构造草稿

SAM 是能高效解决字符串问题的数据结构，直观上是给定字符串**所有子串**的压缩形式，以 O(|S|) 空间存储。它维护两个核心集合：

- **结束位置 `endpos`**：对子串 T，`endpos(T)` 是 T 在 S 中所有结束位置的集合（如字符串 ABCBC 的 `endpos(BC)`={2,4}）。`endpos` 相同的子串归入同一**状态**（`endpos` 等价类），由此实现 O(|S|) 空间压缩。
- **后缀链接 `link`**：状态 u 的 `link(u)` 指向 u 最长子串的**最大真后缀**所在状态。后缀链接构成**后缀链接树**，使 SAM 能以 O(|S|) 线性时间[**增量构造**](https://oi-wiki.org/string/sam/)——每加入一个新字符同时更新转移函数 `next`（自动机部分）与 `link`（结构部分），单次更新 O(1)。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image35.png" width="55%"></p>
<p align="center"><sub>图：基于字符串 ABCBC 构建的 SAM——左 `next` 为状态转移函数（自动机部分），右 `link` 为后缀链接（结构部分）；每加一字符同时更新两者，单次 O(1)（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/sam_decoding.md">SAM 投机推理文档</a>·1.1 SAM 原理）</sub></p>

[**SAM-Decoding**](https://arxiv.org/abs/2411.10666) **把 SAM 用于投机解码**：投机被转化为后缀自动机中的后缀匹配。SAM-Decoding 提出静态 SAM（S-SAM，基于已有语料库冷启动）与动态 SAM（D-SAM，完全基于当前 prompt 在线构建）两种；RL Rollout 落地**采用纯动态 SAM**——为实现零迁移成本、不引入额外系统维护复杂度，不涉及额外语料库。每生成一个 token 并被主模型验证通过后立即更新 D-SAM：可通过现有 `next` 边转移则直接更新状态，否则新建节点 + 添加 `next`/`link` 边，使 D-SAM 始终包含最新序列；同时维护每个状态的 `min_endpos`（等价类字符串首次出现位置）。

**草稿生成**：从当前序列最后一个 token 起，沿 `link` 边回溯，直至找到能通过 `next` 边转移到下一 token 的节点；据其 `min_endpos` 在当前序列中定位匹配后缀起点，提取后续连续 token 作为候选。单次查询最坏 O(|S|)、平均 O(1)。以 ABCBC 为例，当前末 token 是 C，沿 `link` 回溯到节点 BC，该节点能 `next` 转移即停止——其最长子串 BC 是出现过的**最长后缀**，把其后续序列作为 draft token。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image37.png" width="50%"></p>
<p align="center"><sub>图：草稿生成示例——末 token C 沿 link 回溯到节点 BC，该节点找到 next 边（蓝色虚箭头）即停止回溯，取其后续序列作为本次 draft token（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/sam_decoding.md">SAM 投机推理文档</a>·1.1 基于 SAM-Decoding 的草稿生成）</sub></p>

生成草稿后用主模型逐 token 验证：候选 token 符合主模型预测分布则保留，否则触发「拒绝」——从拒绝位置由主模型重新生成，这就是**拒绝采样**。拒绝采样确保最终输出与主模型直接生成完全一致，实现「无损加速」。

## 与其它投机方法的比较

随大模型推理加速需求增长，投机解码已从「大模型+小模型」演化出多条路线。三种代表性方法分别走不同进化方向：**SAM-Decoding**（基于检索的非参数化方法，靠后缀自动机挖掘上下文重复模式）、**EAGLE-3**（基于特征外推的轻量 auxiliary head，树状注意力推测，辅助模型路线 SOTA）、**MTP**（基于模型本身的自投机，如 DeepSeek-V3，把投机内化为训练目标）。核心维度对照：

| 特性/算法 | SAM | EAGLE-3 | MTP |
|---|---|---|---|
| 草稿生成方式 | 借助后缀自动机检索：从已生成历史文本检索「最长后缀 + 后续序列」作草稿 | 主模型特征层之上用轻量 EAGLE head（通常 1 层）+ 树状注意力（Tree Attention）做特征外推生成草稿 | 模型结构里加多 token 预测头（multi-token heads），一次预测多个未来 token 作草稿 |
| 额外组件 | 无额外模型参数；若用冷启动需一个额外语料库 | 需训练依附主模型的极小网络（参数量通常 <1%），用 Training-time Test 消除训推偏差 | 需在结构中加 multi-token heads（预训练阶段引入效果最佳） |
| 部署成本/难度 | 较低，即插即用、无需微调/附加训练；主要挑战在工程上高效实现自动机数据结构 | 中等，需针对特定主模型训练 EAGLE Head，增加模型管理复杂度（Base + Adapter） | 较高，需预训练阶段加 MTP 头；外挂 MTP head + 微调效果通常远不如原生 |
| 适用场景 | prompt 复用率高或生成内容强结构性时极佳（数学、代码、部分 Agent 场景） | 取决于训练 EAGLE head 的数据，与训练分布相似场景表现好 | 原生训练泛化性较好，能应对更多样场景 |

跨域对照：MTP 投机在推理侧的落地（DeepSeek-R1 自研 executor `next_n`、Qwen3-Next 的 SGLang `NEXTN` + GDN 算子 `num_accepted_tokens`）见 [mtp-speculative-decoding](../../../inference/concepts/techniques/mtp_speculative_decoding.md)。

## SAM 接受率

用 Qwen3-8B 在 Math500 上测 SAM-Decoding 接受率：投机 token 个数 3、temperature=0、repetition penalty=1、不设 top-k/top-p、TP=4、推理框架 [vLLM-Ascend](../frameworks/vllm_ascend.md)。此处接受率指 **mean acceptance length**（含 1 个 bonus token），SAM 为不带额外语料库的动态 SAM。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image38.png" width="55%"></p>
<p align="center"><sub>图：Qwen3-8B / Math500 上 SAM-Decoding 接受率随序列长度变化——不用冷启动时接受率与序列长度正相关，长序列场景收益更佳（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/sam_decoding.md">SAM 投机推理文档</a>·1.3 SAM 接受率）</sub></p>

不使用冷启动时**接受率与序列长度正相关**——动态 SAM 在序列变长后积累更多可匹配子串，因此长序列推理场景使用 SAM 收益不错。默认投机个数设为 3（加 1 个本就要解码的 bonus token 刚好 4 个），因为投机个数增加带来的接受率提升有边界效应，不建议设太大。

## 无损性验证（算子精度 + 下游评测 + 端到端）

拒绝采样在理论上保证无损，但实践精度还受其它因素影响。SAM 在 RL 场景的无损性从三个层级验证：

**1. 算子精度。** 普通解码与投机解码用不同算子：vLLM-Ascend 中普通解码走 `torch_npu._npu_paged_attention`（token-by-token），投机解码走 `torch_npu._npu_paged_attention_splitfuse`（为 draft tokens 生成 logprobs）。统计相同输入下两个算子对各 token 预测 logprobs 的差值：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image39.png" width="62%"></p>
<p align="center"><sub>图：普通解码算子 `_npu_paged_attention` 与投机解码算子 `_npu_paged_attention_splitfuse` 对相同输入的逐 token logprobs 差值——严格为 0，表明两算子无精度差异（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/sam_decoding.md">SAM 投机推理文档</a>·2.1 算子精度）</sub></p>

**2. 下游评测。** Qwen3-32B 在 GSM8k / AIME2024 纯推理测评（pass@1，temperature=0.6、repetition penalty=1、不设 top-k/top-p）：

| 数据集 | 不开启 SAM | 开启 SAM |
|---|---|---|
| GSM8k | 88.9 | 88.7 |
| AIME2024 | 66.5 | 66.8 |

开启 SAM 投机不影响推理任务准确率。

**3. 端到端后训练。** 用 [DAPO](grpo_dapo.md) 算法（基于 [verl](../frameworks/verl.md)）在 DAPO-MATH-17k 上训 Qwen3-32B，固定 vLLM 随机种子，开启/不开启 SAM 的每步平均回复长度曲线与 reward 曲线在数值和趋势上基本吻合。结合算子精度与下游评测，可断定 **SAM 投机在 RL 后训练场景精度无损**。

## RL 后训练 Rollout 场景的落地意义

LLM 强化学习后训练需大量交互式采样收集/评估数据，这个过程涉及数百万次生成迭代，是推理成本主要瓶颈。SAM-Decoding 的 Model-Free + Retrieval-Based 特性为这一阶段提供轻量、易落地的加速路径：

- **无参数化、抗分布漂移**：不需额外模型参数，省去训练 draft model / auxiliary head 的成本，也不必担心模型权重更新导致的草稿分布漂移；训练时无需额外内存管理——对训推共卡的 Colocate 框架（[veRL](../frameworks/verl.md) 全共卡）尤为重要，对现有系统即插即用。
- **对 RL 数据天然亲和**：许多 RL 任务生成的 Context 含大量重复/结构化元素。在 RLVR（Reinforcement Learning with Verifiable Rewards）场景，数学问题表现为重复的公式结构与计算步骤、代码生成表现为高度重复的语法模式与库调用、Agent 规划表现为结构化行动指令或观察报告。SAM 的后缀自动机设计能高效捕捉这些局部重复，快速从历史生成中检索最长匹配后缀作高质量草稿，**显著提高 draft token 接受率**。

月之暗面 [Seer](https://arxiv.org/abs/2511.14617) RL 框架同样使用基于压缩后缀树的 Model-Free 投机解码，利用 GRPO「同一 prompt 生成多个响应」的分组特性挖掘组内模式相似性，与 SAM 异曲同工。

## 性能优化（接受率 × 额外耗时）

投机性能取决于接受率与投机算法本身额外耗时（draft 生成/验证、拒绝采样）。落地做了两大优化（代码在 `llm_rl/qwen3`）：

**自适应开关（batch size 阈值）。** 在 `vllm_ascend/worker/model_runner_v1.py` 适配了关于 batch size 的自适应开关：开关开启时，仅当 vLLM engine 当前处理请求数 ≤ 阈值才生效投机。双重动机——(a) 减少额外耗时：当前验证 draft token 的 Page Attention 算子在 (batch size, sequence length) 增大时劣化严重，大 batch 长序列下验证额外耗时会超过投机收益，故只在小 batch 开启；(b) 提高接受率：动态 SAM 在 Rollout 初期后缀树体量小、接受率低，而 Rollout 后期同步 RL 框架存在生成长度不均（请求排队/抢占导致长输出请求调度延迟、少数请求主导执行阶段），以单步请求总数作 Rollout 进程指示物，**在长尾请求中显著加速**。对应 patch `0001-vllm_ascend-feature-bs_threshold_for_spec_decode.patch`（`NPUModelRunner` 用 flag `speculative_decoding_active` 控制开关），环境变量 `VLLM_SPECULATIVE_BATCH_SIZE_THRE` 解析为 `speculative_auto_bs_thre`，**代码默认 `-1`**——仅当 `speculative_auto_bs_thre > 0` 才按阈值裁剪（`num_reqs > 阈值` 关投机），不设该变量则自适应裁剪开关关闭、恒投机（上游使用文档示例口径写默认 32，与代码不一致）。

**拒绝采样加速。** vllm-ascend 原生投机实现性能较差，单 step 带来超 50ms 额外耗时、完全掩盖收益；改用纯 PyTorch **向量化（Vectorization）**优化，**把拒绝采样耗时减到原本约十分之一**。主要重写 `vllm_ascend/sample/rejection_sampler.py` 三个函数：`expand_batch_to_tokens`（把 temperature/top-k/top-p 从「每请求一值」展开成「每 draft token 一值」）、`sample_recovered_tokens_pytorch`（为被否决草稿位置即时生成 recovered token）、`rejection_random_sample_pytorch`（按接受-拒绝规则逐位比对、全接受时追加 bonus token）。核心是去掉所有 Python 循环、消除循环内重复张量创建（原生实现含嵌套 for 与反复 `.clone()`/`torch.full()`，无法利用 NPU 并行）。该重写以 vllm_ascend 侧 patch 形式落在 `llm_rl/qwen3/patches/vllm_ascend/`（重写 rejection-sampler；patch 编号随上游推进而变——d17909e 该目录收录 0001–0006，master 上为 0009），后续可用 Triton 进一步优化。

实现上，`SAM` 类（`add_tokens(tokens)` 状态更新 / `gen_draft(index, start_token)` 序列预测）是动态自动机本体，`SAMDecodingProposer` 类（`spec_decode/sam_proposer.py`，文档简称 `SAMProposer`）是 `vllm-ascend` 后端调用接口——其暴露给 `NPUModelRunner` 投机入口的方法是 `generate_token_ids(...)`，内部再循环调 `propose(...)` 生成草稿（文档措辞称经 `propose_draft_token_ids` 调用，代码实名为 `generate_token_ids`）；vLLM 侧由 `0002-vllm-feature-enable_sam_decoding.patch` 在投机配置中支持 `method=sam`。

## 在 Qwen3 RL 的实测收益

DAPO 长序列 RL 场景下，Qwen3-32B dense 与 Qwen3-235B-A22B MoE 两个代表性模型的 SAM 加速收益；统一配置 DAPO-MATH-17k、`max_response_length`=34816、SAM 阈值（32B 为 8 / 235B 为 8）、投机 token 数 3、eager 模式（详见 [qwen3-rl](../../guides/recipes/qwen3_rl.md)）。

**Qwen3-32B**（2 机 16 卡 32die、`max_num_seqs`=128、TP8）：

| | 单轮平均推理时间 /s | 单步总推理时间 /s | 单步总时间 /s |
|---|---|---|---|
| 不开启 SAM | 3904.22 | 4159.06 | 4730.86 |
| 开启 SAM | 3548.62 | 3793.29 | 4374.99 |
| 收益 | **10.02%** | 9.64% | 8.13% |

**Qwen3-235B-A22B**（8 机 64 卡 128die、`max_num_seqs`=64、TP4）：

| | 单轮平均推理时间 /s | 单步总推理时间 /s | 单步总时间 /s |
|---|---|---|---|
| 不开启 SAM | 7102.92 | 14287.54 | 15441.45 |
| 开启 SAM | 6467.52 | 12811.98 | 13960.98 |
| 收益 | 9.82% | **11.52%** | 10.60% |

**客户场景**（A3 128die Qwen3-32B + verl + DAPO，阈值 4、投机数 4、`max_num_seqs`=256）：单步总推理时间 9094s→8223s（**10.59%**）、单步总时间 11870s→11000s（7.91%）——达成 A3 集群 RL 性能提升目标。

**Rollout 长尾分析**：特别统计 SAM 在 Rollout 长尾阶段（当前请求数在投机阈值以下）的表现，性能达非投机 **1.35X**；若后续优化算子支持更大投机阈值，收益将更明显。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/qwen3_figures/image42.png" width="50%"></p>
<p align="center"><sub>图：SAM 投机在 Rollout 长尾阶段（紫色部分，请求数低于投机阈值）的加速——性能达非投机 1.35X（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/sam_decoding.md">SAM 投机推理文档</a>·3.2.4 Rollout 长尾分析）</sub></p>

叠加 [npugraph_ex](../../../inference/concepts/techniques/npu_graph_mode.md) 入图的收益：Qwen3-32B GRPO 16 卡 2K+34K `generate_sequences` 首步推理 2444s（关）→2106s（开 SAM，+13%）→1621s（SAM+npugraph_ex，+33%）；DAPO 同设 4562s→4109s（+10%）→3261s（+29%）。

## 使能配置

veRL Hydra 配置（Qwen3-32B 样例默认开启 `method=sam` + `num_speculative_tokens=3`）：

| 配置 | 类型 | 说明 |
|---|---|---|
| `actor_rollout_ref.rollout.engine_kwargs.vllm.speculative_config.method` | veRL Hydra 命令行参数 | 投机方法（如 `sam`），必须配置 |
| `actor_rollout_ref.rollout.engine_kwargs.vllm.speculative_config.num_speculative_tokens` | veRL Hydra 命令行参数 | 投机预测 token 数，必须配置 |
| `VLLM_SPECULATIVE_BATCH_SIZE_THRE` | 环境变量 | batch_size 自适应裁剪阈值，可选；代码默认 `-1`（不设则不裁剪、恒投机），仅 `>0` 生效（文档示例口径称默认 32） |

关闭 SAM 时移除启动脚本（`internal/train_grpo_qwen3_32b_32die_true_weight.sh`）中这两个 Hydra 配置即可：

```diff
python3 -m verl.trainer.main_ppo --config-path="${CONFIG_DIR}" \
     --config-name='ppo_megatron_trainer.yaml' \
     ...
-    +actor_rollout_ref.rollout.engine_kwargs.vllm.speculative_config.method=sam \
-    +actor_rollout_ref.rollout.engine_kwargs.vllm.speculative_config.num_speculative_tokens=3 \
     $@
```

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/sam_decoding.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/sam_decoding.md)（SAM 原理 §1.1 / 与 EAGLE-3·MTP 比较 §1.2 / 接受率 §1.3 / RL 落地意义 §1.4 / 算子精度 §2.1 / 下游评测 §2.2 / 端到端 §2.3 / 性能优化（自适应开关·拒绝采样向量化）§3.1 / Qwen3-32B·235B·客户场景·长尾 §3.2）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/features/sam_speculative_decoding.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/features/sam_speculative_decoding.md)（使用说明：method/num_speculative_tokens/VLLM_SPECULATIVE_BATCH_SIZE_THRE；实现方案：`SAM`/`SAMDecodingProposer` 类（文档简称 `SAMProposer`）、D-SAM、拒绝采样加速、batch_size 自适应开关）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/qwen3/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/qwen3/README.md)（Qwen3-32B/235B GRPO·DAPO benchmark；patch 清单 `0001/0002-...enable_sam_decoding`、`0001-vllm_ascend-feature-bs_threshold_for_spec_decode.patch`、`0002-vllm_ascend-feature-enable_sam_decoding.patch`、`spec_decode/sam_proposer.py`；启动脚本 `internal/train_{grpo,dapo}_qwen3_32b_32die_true_weight.sh`）
- 外部参考：[SAM-Decoding 论文 arXiv:2411.10666](https://arxiv.org/abs/2411.10666)、[Seer arXiv:2511.14617](https://arxiv.org/abs/2511.14617)、[OI-Wiki 后缀自动机](https://oi-wiki.org/string/sam/)
- [vllm-ascend](https://github.com/vllm-project/vllm-ascend) — 上游推理引擎仓（SAM 投机经 patch 适配 vLLM/vLLM-Ascend）
- [verl](https://github.com/volcengine/verl) — 上游 RL 框架仓（Hydra `speculative_config` 经 vLLM rollout 后端透传）

## Links

- [verl](../frameworks/verl.md)（承载 RL 框架：SAM 经 veRL `rollout.engine_kwargs.vllm.speculative_config` 在 rollout 阶段使能，全共卡部署下 Model-Free 即插即用）
- [vllm-ascend](../frameworks/vllm_ascend.md)（rollout 推理后端：SAM 自适应开关在 `model_runner_v1.py`、拒绝采样加速在 `rejection_sampler.py`，draft 验证走 `_npu_paged_attention_splitfuse`）
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（落地实践：Qwen3-32B/235B GRPO·DAPO 2K+32K，SAM 约 +10%、叠 npugraph_ex 至 +29%~33%）
- [grpo-dapo](grpo_dapo.md)（承载 RL 算法：端到端无损验证用 DAPO，SAM 对 GRPO「一 prompt 多响应」分组重复天然亲和）
- [npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md)（同实践可叠加的 npugraph_ex 入图特性，与 SAM 收益正交叠加）
- [mtp-speculative-decoding](../../../inference/concepts/techniques/mtp_speculative_decoding.md)（跨域对照：基于模型自投机的 MTP 推理方案，与 SAM 的 Model-Free 检索路线对比）
- [scalebox](../frameworks/scalebox.md)（Code RL 投机加速场景）
- [agent-rl-loop](agent_rl_loop.md)（投机解码叠加 agent RL 多轮流水）
- [qwen3-code-toolcall-rl](../../guides/recipes/qwen3_code_toolcall_rl.md)（EAGLE3/Suffix 投机 vs SAM 对照）

<!-- cannbot:related:start -->
## 相关

- [Qwen3 长序列 RL 训练实践（235B-A22B 2K 推 32K + 32B SAM 投机，veRL/MindSpeed/vLLM-Ascend，GRPO/DAPO）](../../guides/recipes/qwen3_rl.md)（`related`）：SAM 卡记录“统一配置 DAPO-MATH-17k、`max_response_length`=34816、SAM 阈值（32B 为 8 / 235B 为 8）、投机 token 数 3、eager 模式”；Qwen3 recipe给出“32B 推荐自适应阈值 8、投机 token 数 3”。概念机制与可复用训练配置、收益验证在此接合。
<!-- cannbot:related:end -->
