---
type: Runbook
title: recipes专用：低时延TP的Q-B与MLA/LI配对
description: 仅适用于 recipes/CANN Executor 的 low_latency_tp 路径：按实际 Q-B consumer、MLA/LI 配对及 O/sink 分片核对配置和布局。
tags:
- task.debugging
- topic.parallelism
- topic.attention
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:37:06Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：低时延 TP 的 Q-B 与行布局
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：低时延TP的Q-B与MLA/LI配对

## 适用性与框架边界

本卡具体配置与排查步骤仅适用于 recipes/CANN Executor 的 DeepSeek V4.1 `low_latency_tp` 参考路径，不能用于配置原生 vLLM。

通用原则：逻辑 TP 度、某个算子实际接收的 Q head 数、输出分片与通信参与者是不同维度，应按 producer/consumer 的接口逐层对账。

必要条件：只有采用下文相同的低时延分支、压缩层角色和稀疏 Attention consumer，才适用其具体分片规则。复制完整 Q-B 是当前选定 consumer 要求完整 Q 的结果，不是所有 Attention 或 TP 的要求。

recipes 专属操作：相邻偶/奇 rank 的 MLA/LI 配对、全模型 TP 配置重写、压缩层有效 TP 减半、全量 Q-B、sink 聚合和指定通信组都属于该参考实现的组合策略；它们不是 TP 的定义。

vLLM 读者仅借鉴按 token/head/组追踪布局：查自己的模型参数装载与 post-load、分布式组和执行准备职责，先确认选定 Attention 的输入/输出合同。不要复制本卡 rank 配对或配置重写；本卡没有验证 vLLM 接入、同名参数或版本兼容。

## 现象

token 是分词后的序列元素，token ID 是它在词表中的整数编号。一次模型前向把 token ID 转成 hidden state；可将输入记为 x[T,H]，T 是本次 token 行数，H 是每行的隐藏维度。张量并行（TP）可把同一次计算的权重轴分给多个进程；参与者的 token 行如何分布与汇总，由实际通信和算子接口共同约定。rank 是分布式进程编号，通常对应一个设备执行者；global_rank 是全体进程中的编号，组内 rank 是其在某个通信组里的位置，两者不能混用。

recipes/CANN Executor 这条路径的低时延 Attention 把部分进程用于 MLA（多头潜在注意力，这里承担注意力计算），部分用于 LI（生成压缩 KV/索引等输入）。Q-B 是查询的第二级投影：Q-A 先把 H 维 hidden 压到 Rq 维，Q-B 再展开为 A 个 attention head、每个 D 维的查询 Q。O 投影把注意力输出变回 H 维 hidden，供下一层消费。于是“有多少 rank 参与全模型 TP”和“本层谁持有多少 head”并不是同一个问题。

排查触发是：设置 attn_tp_size 后装载 guard 拒绝配置，或按普通 head TP 切 Q-B 后与稀疏 Attention 的输入不符。当前低时延路径仍生成全 head Q，再切 Attention 的输出；直接把 Q-B 按全局卡数切开会先破坏这个生产者—消费者关系。这里是源码可见的诊断规则，没有记录硬件上的具体失败输出。

## 适用场景

仅用于 recipes/CANN Executor 的 DeepSeek V4.1 low_latency_tp 适配中的配置归一化、Attention 权重分片与通信组静态排查。当前入口是装载前检查、Attention 构造和权重后处理；低时延路径仅允许 eager/npugraph_ex，未覆盖 GE、TP 与 CP 组合或跨机部署。

源码目标为 Ascend 950，CANN 运行版本未知；本卡只有固定源码核验，没有 NPU 推理或性能验证。适用粒度 exact_task，路线 recommended_fastpath，含义是按当前实现契约诊断。可迁移的是按 token/head/组维追踪布局的方法；其它框架须先核对自己的 Attention 算子是否也需要完整 Q，不能直接照搬本实现的偶奇 rank 分工。

## 判别方法

在上述 recipes 路径中找到三个职责入口：装载前配置检查、Attention 的 Linear/参数构造、通信组建立与权重后处理。记录配置进入检查前后的值，随后按层记录压缩模式、global_rank、组成员、组内 rank、Q-B 与 O 投影的实际 tp_size。不要从启动 YAML 的一个 TP 数推导全部参数轴。

1. 检查该 recipes 分支的配置归一化。这里要求 world_size 为偶数、attn_tp_size>1 且等于 world_size，head 数、O 分组数与 MoE 中间维满足相应整除，force_eplb=False。guard 会把 moe/o_proj/lmhead/embed/dense/shared 的 TP 改为 world_size，把 attn_dp/embed_dp 和 moe_ep_size 改为 1；实际生效值应以检查后的对象为准。若这些条件已经不满足，先处理配置，不继续归因到权重格式。
2. 检查该 recipes 分支的本层角色。compress_ratio>0 时，相邻偶/奇 global rank 成对，偶数运行 MLA；有效 Attention/O TP 为 world_size/2，组内编号用 global_rank//2。compress_ratio==0 时不分 MLA/LI 角色，有效 Attention TP 不减半。两类层都复制 Q-B，以满足当前选定 consumer 的全 head Q 合同；其它 Attention consumer 是否要求完整 Q 须独立核验。
3. 沿此分支的轴检查消费关系。把 Q 理解为 [T,A,D]，Q-B 输出宽度必须为 A×D。Attention 输出再按有效 TP 的 head 区间取 [T,A/P,D]。wo_a 分 O 的组维，wo_b 消费同一个组片并产生 [T,H] 的部分和；检查二者的 P 与 rank 一致。压缩层只有 MLA rank 贡献部分和，LI rank 提供零，最后在全体 oproj_tp_group 上 AllReduce。
4. 检查此分支每 head 的 sink 参数。window-only 层保留全 head sink；压缩层先装载本地 sink，再在偶数 rank 的 separate_mla_tp 上 AllGather 成全 head 的 full_attn_sink。它必须在 warm-up/抓图前就绪；输出切片正确而 sink 仍是局部长度时，问题尚未排除。

**教学推演（非 NPU 实测）**：仅演示布局算术：设全局 4 个 rank、8 个 head，且其它 guard 均满足；这不是已验证的部署配置。压缩层的 MLA 组是 [0,2]，有效 P=2；rank 0/2 都生成 8 个 head 的 Q，Attention 后各取 head 0–3/4–7。rank 1/3 执行配对的 LI 工作，O 输出为零。AllReduce 汇总的是两个互补的 O 部分和。若误按全局 P=4 切 Q-B，每个 MLA rank 只生成 2 个 head，不能满足全 head 输入；若把奇数 rank 也当 MLA 重复贡献，则又破坏“每份 O 只贡献一次”。对照 window-only 层，同样的 4 rank 按 P=4 各取 2 个输出 head，不能把压缩层的 P=2 写回全局配置。

复验时先核对每层 Q 的 head 数、sink 总长度、O 输入片覆盖是否完整且无重叠，再在目标环境比较各 rank 汇总后的 hidden 与参考路径。只有轴与组都符合而输出仍错，才继续查 Attention 算子输入、事件依赖和数值；本卡没有这些后续运行结果。下面的 rg 仅用于 recipes 源码可选导航，外部框架按职责定位：

```bash
rg -n 'check_model_config_before_loading|low_latency_tp|wq_b|full_attn_sink' models/deepseek_v4_1/models/modeling_deepseek.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`check_model_config_before_loading` 接受模型与并行配置，输出是原地修改后的 parallel_config，或明确异常。循环里的 tp_name 是各子模块的并行参数；先看它们被统一到 world_size，再看整除检查，便能区分用户输入与真正用于建层的配置。

```python
        low_latency_tp = bool(custom_params.get("low_latency_tp", False))
        if low_latency_tp:
            if parallel_config.world_size % 2:
                raise ValueError("low_latency_tp requires an even world_size for MLA/LI rank pairs")
            if exe_mode not in ("eager", "npugraph_ex"):
                raise ValueError("low_latency_tp uses native streams; select eager or npugraph_ex")
            if parallel_config.attn_tp_size <= 1:
                raise ValueError("low_latency_tp requires attn_tp_size > 1")
            if parallel_config.attn_tp_size != parallel_config.world_size:
                raise ValueError("low_latency_tp requires attn_tp_size == world_size")
            # Low-latency TP keeps one identical token layout through the model.
            for tp_name in (
                "moe_tp_size", "o_proj_tp_size", "lmhead_tp_size",
                "embed_tp_size", "dense_tp_size", "shared_tp_size",
            ):
                setattr(parallel_config, tp_name, parallel_config.world_size)
            parallel_config.attn_dp_size = 1
            parallel_config.embed_dp_size = 1
            parallel_config.moe_ep_size = 1
            if config.num_attention_heads % parallel_config.attn_tp_size != 0:
                raise ValueError("num_attention_heads must be divisible by attn_tp_size")
            if config.o_groups % parallel_config.attn_tp_size != 0:
                raise ValueError("o_groups must be divisible by attn_tp_size")
            if config.moe_intermediate_size % parallel_config.moe_tp_size != 0:
                raise ValueError("moe_intermediate_size must be divisible by moe_tp_size")
            if model_config.force_eplb:
                raise ValueError("Basic MoE TP requires force_eplb=False for identical routing on all ranks")
        elif parallel_config.attn_tp_size > 1:
            raise ValueError(f"{parallel_config.attn_tp_size=} is not supported yet! "
                             "Set low_latency_tp=True to enable the low-latency TP path.")
```

`Attention.__init__` 把配置落到当前层。`is_mla_rank` 决定是否创建实际 Attention 参数，`attn_tp_rank` 是本层 head/组片编号；`num_heads_per_rank=A/P`，`q_num_heads=A` 则说明 Q 的生产宽度与输出持有宽度不同。`wo_tp_size/rank` 同时传给 wo_a、wo_b，保证两级 O 投影共享分片坐标。`dim/q_lora_rank/o_lora_rank/head_dim/n_groups` 分别对应 H/Rq/Ro/D/G，均是维度计数，不是 token 数。

```python
        self.is_mla_rank = not self.low_latency_tp or self.compress_ratio == 0 or self.global_rank % 2 == 0
        self.attn_group_name = "attn_tp_group"
        self.attn_tp_rank = self.comm_manager.get_rank(self.attn_group_name) if self.attn_tp_size > 1 else 0
        if self.low_latency_tp and self.compress_ratio > 0:
            self.separate_mla_peer_rank = self.global_rank ^ 1
            self.separate_mla_stream = kwargs["separate_mla_stream"]
            self.attn_group_name = "separate_mla_tp"
            self.attn_tp_size //= 2
            self.oproj_tp_size //= 2
            self.attn_tp_rank = self.global_rank // 2
        self.mm_quant_mode = (
            config.quant_config.mm_quant_mode
            if config.quant_config is not None
            else "w16a16")

        self.dim = config.hidden_size
        self.n_heads = config.num_attention_heads

        self.num_heads_per_rank = self.n_heads // self.attn_tp_size
        # Low-latency TP computes full-head Q on each MLA rank.
        self.q_num_heads = self.n_heads if self.low_latency_tp else self.num_heads_per_rank
        self.q_lora_rank = config.q_lora_rank
        self.o_lora_rank = config.o_lora_rank
        self.head_dim = config.head_dim
        self.rope_head_dim = config.qk_rope_head_dim
        # set self.partial_slice, used for inplace_partial_rotary_mul
        self.partial_slice = [self.head_dim - self.rope_head_dim, self.head_dim]
        self.nope_head_dim = config.head_dim - config.qk_rope_head_dim
        self.n_groups = config.o_groups

        self.num_groups_per_rank = max(self.n_groups // self.attn_tp_size, 1)
        self.window_size = config.sliding_window
        self.eps = config.rms_norm_eps

        self.is_kv_source = layer_idx in config.kv_source_layers
        self.is_index_source = layer_idx in config.index_source_layers
        if self.low_latency_tp and self.compress_ratio > 0 and not self.is_mla_rank and self.is_kv_source:
            self.compressor_stream = kwargs["separate_mla_compressor_stream"]
        runs_mla = self.is_mla_rank
        runs_indexer = not self.low_latency_tp or self.compress_ratio == 0 or not self.is_mla_rank

        if runs_mla:
            sink_heads = self.n_heads if self.low_latency_tp and self.compress_ratio == 0 else self.num_heads_per_rank
            self.attn_sink = nn.Parameter(torch.empty(sink_heads, dtype=torch.float32))
            self.attn_sink.weight_loader = self.load_attn_sink
            self.register_buffer("full_attn_sink", None, persistent=False)
        if runs_mla or self.is_index_source:
            self.wq_a = ReplicatedLinear(self.dim,
                                         self.q_lora_rank,
                                         params_dtype=torch.bfloat16,
                                         quant_config=config.quant_config,
                                         prefix=f"{prefix}.wq_a",
                                         )
            self.q_norm = DeepseekV41RMSNorm(self.q_lora_rank, self.eps)

        if runs_mla:
            # Sparse FA consumes all Q heads; keep Q-B replicated for low-latency TP.
            self.wq_b = ColumnParallelLinear(config.q_lora_rank,
                                            self.n_heads * self.head_dim,
                                            bias=False,
                                            quant_config=config.quant_config,
                                            tp_size=1 if self.low_latency_tp else self.attn_tp_size,
                                            tp_rank=0 if self.low_latency_tp else self.attn_tp_rank,
                                            prefix=f"{prefix}.wq_b",
                                            )
            self.wkv = ReplicatedLinear(self.dim,
                                        self.head_dim,
                                        params_dtype=torch.bfloat16,
                                        quant_config=config.quant_config,
                                        prefix=f"{prefix}.wkv",
                                        )
            self.kv_norm = DeepseekV41RMSNorm(self.head_dim, self.eps)

            # consider oproj_tp
            if self.low_latency_tp and self.compress_ratio > 0:
                wo_tp_size = self.attn_tp_size
                wo_tp_rank = self.attn_tp_rank
            elif self.oproj_tp_size == 1:
                wo_tp_size = self.attn_tp_size
                wo_tp_rank = self.comm_manager.get_rank("attn_tp_group") if self.attn_tp_size > 1 else 0
            else:
                wo_tp_size = self.oproj_tp_size
                wo_tp_rank = self.comm_manager.get_rank("oproj_tp_group")
            quant_config = config.quant_config if self.mm_quant_mode == "w8a8mxfloat8" else None
            self.wo_a = ColumnParallelLinear(self.n_heads * self.head_dim // self.n_groups,
                                            self.n_groups * self.o_lora_rank,
                                            params_dtype=torch.bfloat16,
                                            bias=False,
                                            quant_config=quant_config,
                                            tp_size=wo_tp_size,
                                            tp_rank=wo_tp_rank,
                                            prefix=f"{prefix}.wo_a",
                                            )
            self.wo_b = RowParallelLinear(self.n_groups * self.o_lora_rank,
                                        self.dim,
                                        tp_size=wo_tp_size,
                                        tp_rank=wo_tp_rank,
                                        bias=False,
                                        input_is_parallel=True,
                                        quant_config=config.quant_config,
                                        prefix=f"{prefix}.wo_b",
                                        )
```

`load_attn_sink` 输入完整的每 head 标量数组，输出当前参数所需的片。window-only 低时延分支直接保留全量；其它分支按本层 rank×每 rank head 数取连续区间。它只负责装载，后面的权重后处理才负责聚合。

```python
    def load_attn_sink(self, param, loaded_weight):
        if self.low_latency_tp and self.compress_ratio == 0:
            shard = loaded_weight
        else:
            rank = self.attn_tp_rank if self.low_latency_tp else 0
            shard = loaded_weight.narrow(0, rank * self.num_heads_per_rank, self.num_heads_per_rank)
        default_weight_loader(param, shard)
```

`select_local_attn_heads` 的输入 output 第 0 轴是 token、第 1 轴是 head；仅在 window-only 低时延层按本层 TP 取片，其余模式原样返回。不要在调用前再切一次。

```python
    def select_local_attn_heads(self, output):
        if self.low_latency_tp and self.compress_ratio == 0:
            start = self.attn_tp_rank * self.num_heads_per_rank
            return output[:, start:start + self.num_heads_per_rank].contiguous()
        return output
```

`sparse_attn_low_latency` 消费全 head q、窗口/压缩 KV 与索引，先等待必要的索引事件，再以 full_attn_sink 调用稀疏 Attention。算子返回值的第 1 轴才在本函数末尾切成本地 head。

```python
    def sparse_attn_low_latency(self, q, win_kv, cmp_kv, cmp_sparse_indices, attn_metadata, is_prefill):
        if self.is_index_source:
            wait_event(True, attn_metadata["attention_events"]["separate_mla"], SEPARATE_MLA_DONE)
        fa_kwargs = self.prepare_fa_kwargs(q, win_kv, cmp_kv, cmp_sparse_indices, attn_metadata, is_prefill)
        fa_kwargs["sinks"] = self.full_attn_sink if self.attn_tp_size > 1 else self.attn_sink.detach()
        output = self.sparse_attn_ops(**fa_kwargs)[0]
        start = self.attn_tp_rank * self.num_heads_per_rank
        return output[:, start:start + self.num_heads_per_rank].contiguous()
```

`forward_separate_mla` 连接角色分工与最终归约：MLA 分支执行 Q/Attention/O，LI 分支准备输入并返回与 x 同形的零；两者都参与最后的 AllReduce，返回每个 rank 相同的 [T,H] hidden。

```python
    def forward_separate_mla(self, x, attn_metadata, is_prefill, kv_cache):
        if self.is_mla_rank:
            win_kv, q = self.attention_prolog_mla_rank(x, attn_metadata, is_prefill, kv_cache)
            o = self.sparse_attn_low_latency(
                q, win_kv, kv_cache.cmp_cache, kv_cache.shared_idx, attn_metadata, is_prefill,
            )
            output = self.attn_post(o, attn_metadata)
        else:
            self.attention_prolog_li_rank(x, attn_metadata, is_prefill, kv_cache)
            output = torch.zeros_like(x)
        # MLA shards contribute once; the same result reaches every MoE/mHC rank.
        dist.all_reduce(output, group=self.comm_manager.get_group("oproj_tp_group"))
        return output
```

通信注册块明确了两个不同用途：separate_mla_pair 的成员是相邻偶奇 rank，separate_mla_tp 只有偶数 rank。前者服务配对协作，后者服务 MLA 分片；名称相似不能互换。

```python
        world_size = self.world_size
        platform_version = self.platform_version
        if self.low_latency_tp:
            self.comm_manager.register_group(
                name="separate_mla_pair",
                subgroups=[[rank, rank + 1] for rank in range(0, world_size, 2)],
                allow_physical_reuse=False,
                platform_version=platform_version,
            )
            self.comm_manager.register_group(
                name="separate_mla_tp",
                subgroups=[list(range(0, world_size, 2))],
                platform_version=platform_version,
            )
```

权重后处理遍历 Attention 层，只在压缩层的 MLA rank 且有效 P>1 时聚合 sink。分配长度 n_heads 的固定 buffer，再沿该层 Attention 组填满，解释了为何该工作属于装载期而非图回放内。

```python
        # Fixed inference weights: gather once, before warm-up and graph capture.
        for module in self.modules():
            if (isinstance(module, Attention) and module.low_latency_tp and module.compress_ratio > 0
                    and module.is_mla_rank and module.attn_tp_size > 1):
                module.full_attn_sink = module.attn_sink.new_empty(module.n_heads)
                dist.all_gather_into_tensor(
                    module.full_attn_sink, module.attn_sink.detach().contiguous(),
                    group=self.comm_manager.get_group(module.attn_group_name),
                )
```

</details>

## 设计决策

该 recipes 路径复制 Q-B 以满足当前选定稀疏 Attention consumer 的全 head 输入；输出 head 与 O 分片再分摊工作。统一 token 行顺序使后续 TP 继续消费相同请求布局，但复制查询投影也有重复计算。本卡没有 profiling，不能据“低时延”名称承诺收益。全局 TP 配置与局部有效 TP 并存是这套实现的选择。

## 系统信息

实现对照集中于 `models/deepseek_v4_1/models/modeling_deepseek.py`；通信注册由 CommManager 承担。下列完整因果块依赖原工程的参数装载器、通信和 Attention 算子，不是可脱离工程运行的示例。

## 预防

为每层保存一份配置归一化结果、rank 角色、组成员、Q 输出 head 数、sink 长度和 O 分片区间的对照。配置或压缩层分工变化后重新核对整条链；回退到已有参考运行配置时也应重新装载权重与建立通信组。

## 验证信号

固定源码核对覆盖装载 guard、Attention 构造、sink 装载、两处 head 切片、MLA/LI 前向、通信组注册及抓图前 sink 聚合，确认本卡保留的代码与这些职责对应。没有本卡的 CPU 或 NPU 执行结果。（来源平台：源码目标 950；证据等级：artifact_verified。）

## 失效边界

旧方案概述曾描述从 Q-B 开始按 head 做 TP；该设计需要稀疏 Attention 同时支持按 head 分片的 Q 输入。当前实现已回退为各 MLA rank 全量计算 Q-B，让 Attention 消费完整 Q 后才切输出。按 head 分片的输入路径仍是后续计划，不能把方案概述当成已启用的权重分片契约；部署排查应以实际参数构造和 forward 分支为准。

具体步骤限于当前 recipes/CANN Executor 的 V4.1 分支；偶奇配对与全模型 TP 重写不应推导为所有框架必须的约束。普通 head TP、其它 Attention 算子的全量/局部 Q 要求、GE 图、跨机 pair 通信及 TP/CP 组合均未验证。没有 NPU 推理、真实权重装载、跨 rank 通信或编译回放结果；轴检查通过后仍须完成目标环境的输出与通信验收。MoE 的非均匀 TP/grouplist 问题不在本卡范围。

## 坏实践

把全局 world_size 当成每层所有 Linear 的切分数；把压缩层的有效 TP 减半写回全局配置；按全局 rank 直接切 sink；在图回放中临时补建 full_attn_sink；把未启用 low_latency_tp 的 attn_tp_size>1 当成已有运行通路。
