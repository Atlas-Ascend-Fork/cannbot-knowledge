---
type: Runbook
title: MoE分组表切换：路由与两次矩乘须采用同一语义
description: 接口条件：专家行段表示须由路由、两次专家矩乘与激活共同遵守；type2 的编号/计数仅指本文 recipes 算子 ABI。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.compute.quantization
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:38:52Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 MoE TP 稀疏分组表须贯穿两次矩乘
---

# MoE分组表切换：路由与两次矩乘须采用同一语义

## 适用性与框架边界

本卡是**接口条件下可迁移的诊断方法**：先确认专家行段的含义，再沿路由、专家计算、归并检查同一协议。以下源码是 DeepSeek V4.1 的 recipes / CANN Executor 参考实例。

| 层次 | 读用范围 |
|---|---|
| 通用原则 | 路由分桶的专家编号、有效行段和行映射，须与两次专家矩乘、激活及最终归并一致。 |
| 成立前提 | 目标后端确实使用可对应的专家分组表示；先核对其真实 ABI、容量/丢弃规则和排列。type1/type2 名字本身不能证明语义相同。 |
| recipes 专属 | enable_grouplist_type2、group_list_type、expert_tokens_num_type 与 custom SwiGLU 签名属于文中适配；此处 type2 的 (expert_id,count) 解释仅在对应算子 ABI 下成立。 |
| vLLM / 其他框架入口 | 按 MoE prepare/dispatch 的分桶与排列、experts 的输入格式、finalize/归并的反排列及权重应用位置追踪；不要求找到同名字段，不提供配置翻译。 |

本轮没有在 vLLM 或其他框架接入/运行验收；职责入口只帮助读者定位自己的生产者和消费者。

## 适用场景

MoE（混合专家）层接收若干 token 的隐藏向量。路由器为每个 token 选 K 个 routed expert（按选择参与计算的专家）；shared expert 则处理所有真实 token。为批量计算，路由阶段把 token 复制、按专家聚在一起，GMM1（分组矩阵乘）做 Gate/Up 两个投影，SwiGLU 对 Gate 半 g 做 SiLU，再逐元素乘 Up 半 u，即 SiLU(g)×u，合成激活，GMM2 做 Down 投影，最后 Combine/Finalize 按原 token 顺序加权合回，并纳入 shared 贡献。本卡诊断连接这些阶段的“哪段行属于哪个专家”协议。

适用任务是诊断路由到专家计算之间的分组表示错配，目标框架应先选择实际的分桶/专家/归并入口。本文 recipes 实例使用 DeepSeek V4.1 的 low_latency_tp 本地路由和 W4A8MxFp4MoEGMMMethod。TP（张量并行）在各 rank（通信组中的计算进程）上计算专家中间维度的一部分，最后求和；这里各 rank 使用相同 token 和路由。enable_grouplist_type2 控制稀疏分组表。路线为 recommended_fastpath 的调用契约核查；后续 type2 调用细节的适用粒度限该实现和量化方法，通用诊断不要求采用它们。并非已通过部署验证的修复配方。

目标平台为 950（模型说明的支持范围）；本轮证据仅是固定源码静态核验，未运行 CPU/NPU、编译、图、精度或性能测试。CANN 和独立 custom_ops 包版本未知。其他后端可按职责排查，但必须先确认其分组表 ABI。

## 现象

切换稀疏表后，若路由、GMM1、激活或 GMM2 中只有一部分切换格式，相同字节会被解释为不同的专家边界。可疑表现包括分组参数不匹配或专家段结果错位；这是待排查的风险，本轮没有具体报错或精度失败观测。只看张量元素总数一致，无法判断格式正确。

## 根因与判别方法

先从目标后端的真实 schema 确定分组表如何描述专家行段，再检查每个消费者。下述枚举、表结构与变量轴属于 recipes 参考 ABI：type1 在本路径表示按专家排列的一维计数。type2 每行是 (expert_id, count)，不是累计结束位置。当前适配仅在上游仍返回一维计数时补齐 expert_id；已有二维表直接沿用，不按计数重排，也不自行删除零计数行。GMM1、SwiGLU 和 GMM2 必须沿着相同专家顺序解释已排序的 token 行。

| 符号或张量 | 轴与单位 | 来源 → 消费者 |
|---|---|---|
| x | [T,H]；T 为本 rank 的 token 行数，H 为隐藏通道 | 层输入 → 路由 |
| topk_ids / topk_weight | [T,K]；专家编号 / 路由权重 | Gate/TopK → 路由 / Finalize |
| expanded_x | [T×K,H] 的路由行及其量化存储视图；每行是一份 token 专家任务 | 路由 → GMM1 |
| expert_tokens | type1 为每专家计数；type2 为 [表行数,2]，两列单位分别为专家编号和行数 | 路由、参数适配 → 两次 GMM 和 SwiGLU |
| row_idx | 路由展开行与源 token 的映射索引；具体方向遵循路由/Finalize 配套 API | 路由 → Finalize |
| pertoken_scale | 每个路由行、每个 MX 通道块的 scale；不是一行一个标量 | 路由或动态量化 → 对应 GMM |
| mm1_mm3 | [展开行数,2I_r]；I_r 为本 rank 的专家中间通道宽度，最后一轴是 Gate/Up 两半 | GMM1 → SwiGLU |
| intermediate_h | [展开行数,I_r] 及其量化 scale | SwiGLU → GMM2 |
| expert_output / output | 按专家排列的部分输出 / [T,H] 部分和 | GMM2 → Finalize → TP all_reduce |

MX 低精度将权重值与按通道块的 scale 分开存储。以下 reshape 是 recipes 的表示适配条件：这里 FP4 权重、FP8 激活和 E8M0 scale 的 dtype 标记共同决定算子解释。reshape_mx_scale 只把最后一个 scale 轴配成二元组：原有 G 个槽变为 [ceil(G/2),2]，G 为奇数时补一个尾槽。它不修复专家表顺序，也不把 scale 变成每 token 一个数。

以下是教学推演，不是上板观测。假设三个专家编号为 0、1、2，展开行数为 6，对应计数为 2、0、4。按本卡“一维计数适配为二维对”的分支得到 (0,2)、(1,0)、(2,4)：前两行属于专家 0，专家 1 无行，后四行属于专家 2。若把计数当累计位置，第二项 0 就无法解释为前一段之后的结束位置；若按 count 重排表而不重排 expanded_x，专家 2 的权重可能作用到原先专家 0 的行。即使计数和仍为 6，语义已经改变。诊断重点因此是“行段—专家权重”的对应关系，而非仅比较总和。该推演不表示所有外部 type2 算子都已验收零计数行；部署仍按其真实 ABI 核对。

## 诊断路径

1. 在自己的框架按 prepare/dispatch、experts、finalize/归并职责找到路由分桶器、第一层专家投影、门控激活量化、第二层专家投影和反路由器。记录本次选择的实现与量化模式；先从一个可解释的小路由样本检查数据布局。
2. 在路由出口记录 T、K、展开的有效行数、原 token/专家映射，以及分组表的 dtype、列含义、专家编号顺序和 count 总和。无丢弃/容量裁剪的本卡路径预期总和为 T×K；其他后端先按自己的丢弃规则确定有效行数。
3. 在三个消费者入口分别记录表格式枚举、实际表内容及展开行顺序。若第一个不一致点在激活处，检查它是否仍使用另一种默认格式（本文 recipes 中对应 type1）；若表一致但数值不符，再检查 Gate/Up 两半与 scale 块轴，避免归因给表格式。
4. 修正时让生产者与所有消费者一起采用其后端支持的格式。保持输入、权重和路由不变，先逐段核验专家行归属，再比较两次矩乘、激活和最终输出；最后覆盖零计数专家与非连续活跃专家。精度准则使用该框架既有验收规则，不通过放宽容差掩盖错位。

<details>
<summary>recipes / CANN Executor 完整实现对照（可选阅读）</summary>

## 快速检查

已有 recipes 源码时，可选用下述只读搜索定位对应角色。没有该仓库也可执行上述入口记录与不变量核验。

```bash
rg -n 'expert_tokens_num_type|group_list_type|swiglu_expert_tokens|gmm_group_list' models/deepseek_v4_1/models/modeling_deepseek.py module/quantization/mxfp4.py
```

## 系统信息

下列原样代码分别属于模型层和 MXFP4 MoE 量化模块，依赖权重加载后的布局、通信组、PyTorch、torch_npu，以及单独部署的 custom_ops。它们组成参数传递证据，不是可脱离模型直接运行的程序。

## 机制代码

### 路由生产者：_build_moe_tp_routing_args

输入 x、topk_ids；输出 routing_args 和 routing_quantizes_input。active_num 给出展开任务数，expert_tokens_num_type 决定计数格式，quant_mode 决定路由是否同时量化 x。后一个布尔值将决定下游是否沿用路由产生的 scale。

```python
    def _build_moe_tp_routing_args(self, x, topk_ids):
        routing_quantizes_input = self.gmm_quant_mode in ("w8a8mxfloat8", "w4a8mxfloat4")
        routing_args = {
            "expert_idx": topk_ids,
            "active_num": x.shape[0] * self.top_k,
            "expert_num": self.num_experts,
            # type=2: routing emits the sparse [E, 2] (expert_id, count)
            # directly in expert order; type=1 keeps the count list.
            "expert_tokens_num_type": 2 if self.enable_grouplist_type2 else 1,
            "expert_tokens_num_flag": True,
            "active_expert_range": [0, self.num_experts],
            "quant_mode": 3 if routing_quantizes_input else -1,
        }
        return routing_args, routing_quantizes_input
```

### 参数适配：_build_moe_tp_gmm_args

输入路由的展开行、分组表、scale 和量化标记；输出交给专家 FFN 的参数字典。sparse_pairs 是协议适配结果；gmm_group_list 供两次 GMM，swiglu_group_list 使自定义激活显式选择 type2。这里 int64 转换不会纠正错误专家编号或错误行序。

```python
    def _build_moe_tp_gmm_args(self, expanded_x, tokens_per_expert, pertoken_scale, routing_quantizes_input):
        group_list_type = 1
        gmm_group_list = tokens_per_expert
        swiglu_group_list = None
        if self.enable_grouplist_type2:
            if tokens_per_expert.dim() == 1:
                # Pre-fix op form: build the sparse pairs locally.
                expert_ids = torch.arange(self.num_experts, dtype=torch.int64,
                                          device=tokens_per_expert.device)
                sparse_pairs = torch.stack(
                    [expert_ids, tokens_per_expert.to(torch.int64)], dim=1)
            else:
                # type=2 direct output: [E, 2] (expert_id, count).
                sparse_pairs = tokens_per_expert
            # The GMM walks the pairs in order; they must keep expert order.
            group_list_type = 2
            gmm_group_list = sparse_pairs.to(torch.int64)
            swiglu_group_list = gmm_group_list
        gmm_args = {
            "x": expanded_x,
            "expert_tokens": gmm_group_list,
            "group_list_type": group_list_type,
            "swiglu_expert_tokens": swiglu_group_list,
            "swiglu_limit": self.swiglu_limit,
            "enable_cann_ops_nn": True,
            "low_latency_tp": self.low_latency_tp,
        }
        if routing_quantizes_input:
            gmm_args["pertoken_scale"] = reshape_mx_scale(pertoken_scale)
        return gmm_args
```

### 三个连续消费者：W4A8MxFp4MoEGMMMethod.apply

本函数把分组协议贯穿完整专家计算，返回 expert_output 对应的 out_hidden。

| 阶段 | 关键变量与输出 | 应检查的对应关系 |
|---|---|---|
| 输入量化 | 缺少 pertoken_scale 才动态产生 x 与 scale | scale 属于当前 x 的块轴 |
| GMM1 | w13_weight → mm1_mm3；此后记录 gmm1_events | expert_tokens 与 group_list_type 配对 |
| SwiGLU | mm1_mm3 → intermediate_h、更新后的 scale | low_latency_tp 自定义包显式接收同一表和 type；其他分支签名不同 |
| GMM2 | w2_weight → out_hidden | 沿用同一专家表，消费激活的新 scale |

```python
    def apply(
        self,
        layer: torch.nn.Module,
        x: torch.Tensor,
        expert_tokens: torch.Tensor,
        group_list_type: int,
        pertoken_scale: torch.Tensor = None,
        final_output_dtype: torch.dtype = torch.bfloat16,
        **kwargs
    ):
        # Keep the torch_npu operator argument name. pertoken_scale does not
        # mean one scale for a whole token; the token dimension is indexed
        # independently, and each token stores MX scales per BLOCK_K hidden values.
        if pertoken_scale is None:
            x, pertoken_scale = torch_npu.npu_dynamic_mx_quant(x, dst_type=torch.float8_e4m3fn)
        num_tokens = x.shape[0]
        mm1_mm3 = torch_npu.npu_grouped_matmul(
            [x], [layer.w13_weight.transpose(1, 2)],
            antiquant_scale=[layer.w13_weight_scale.transpose(1, 2)],
            per_token_scale=[pertoken_scale],
            group_list=expert_tokens, split_item=3,
            output_dtype=torch.bfloat16, group_type=0,
            weight_dtype = torch_npu.float4_e2m1fn_x2,
            per_token_scale_dtype=torch_npu.float8_e8m0fnu,
            group_list_type=group_list_type,
            tuning_config=[0]
        )[0]

        record_event(layer.gmm1_events is not None, layer.gmm1_events, 0)
        swiglu_limit = kwargs.get("swiglu_limit", None)
        enable_cann_ops_nn = kwargs.get("enable_cann_ops_nn", False)
        if enable_cann_ops_nn and kwargs.get("low_latency_tp", False):
            # Low-latency TP path: repo custom op (separately deployed package).
            import custom_ops
            group_quant_kwargs = {}
            if swiglu_limit is not None:
                group_quant_kwargs["clamp_limit"] = swiglu_limit
            swiglu_expert_tokens = kwargs.get("swiglu_expert_tokens")
            glt = 2 if swiglu_expert_tokens is not None else 1
            swiglu_group_index = swiglu_expert_tokens if swiglu_expert_tokens is not None else expert_tokens
            group_quant_kwargs["group_index"] = swiglu_group_index
            group_quant_kwargs["dst_type"] = torch.float8_e4m3fn
            group_quant_kwargs["quant_mode"] = 1
            group_quant_kwargs["block_size"] = 32
            group_quant_kwargs["round_scale"] = True
            group_quant_kwargs["output_origin"] = False
            group_quant_kwargs["group_list_type"] = glt
            intermediate_h, pertoken_scale, _ = torch.ops.custom.npu_swiglu_group_quant(mm1_mm3, **group_quant_kwargs)
        elif enable_cann_ops_nn:
            intermediate_h, pertoken_scale, _ = torch.ops.cann_ops_nn.swiglu_group_quant(
                mm1_mm3,
                dst_type=torch.float8_e4m3fn,
                round_scale=True,
                quant_mode=1,
                clamp_limit=_get_swiglu_clamp_limit(swiglu_limit),
                group_index=expert_tokens)
        else:
            intermediate_h, pertoken_scale = torch_npu.npu_swiglu_mx_quant(
                                                mm1_mm3,
                                                group_index=expert_tokens,
                                                dst_type=torch_npu.float8_e4m3fn,
                                                activate_left=True,
                                            )
        out_hidden = torch_npu.npu_grouped_matmul(
            [intermediate_h],
            [layer.w2_weight.transpose(1, 2)], bias=None,
            antiquant_scale=[layer.w2_weight_scale.transpose(1, 2)],
            per_token_scale=[pertoken_scale],
            group_list=expert_tokens, split_item=3,
            output_dtype=final_output_dtype, group_type=0,
            weight_dtype = torch_npu.float4_e2m1fn_x2,
            per_token_scale_dtype=torch_npu.float8_e8m0fnu,
            group_list_type=group_list_type,
            tuning_config=[0]
        )[0]

        return out_hidden
```

### scale 视图适配：reshape_mx_scale

输入任意前导轴、最后一轴为 scale 槽的张量；输出保留前导轴的二元对视图。只在奇数槽时增加一个零尾槽，原有效 scale 顺序不变。

```python
def reshape_mx_scale(scale_tensor):
    """
    Reshape the last dimension into pairs for GMM/MM operators; an odd
    group count gets one zero tail slot for the pair view.
    """
    import torch
    num_groups = scale_tensor.size(-1)
    if num_groups % 2:
        pad = torch.zeros((*scale_tensor.shape[:-1], 1), dtype=scale_tensor.dtype,
                          device=scale_tensor.device)
        scale_tensor = torch.cat((scale_tensor, pad), dim=-1)
        num_groups += 1
    return scale_tensor.view(*scale_tensor.shape[:-1], num_groups // 2, 2)
```

### 完整连接：moe_infer_tp

本函数连接路由、参数适配、专家 FFN 与 Finalize；row_idx 恢复源 token 行，topk_weight 提供加权系数。shared 分支只有在最终合并前必须就绪；最终 all_reduce 合并 routed 与 shared 的 TP 部分和。engram_resource_events[5] 在路由后、专家 GMM 前记录，不能拿它当作 GMM 已完成的信号。

```python
    def moe_infer_tp(self, x, topk_ids, topk_weight, hidden_states_share, moe_events,
                     engram_resource_events=None, shared_expert_stream=None,
                     shared_merged_x=None):
        """Local routing over all experts; sum the TP-sharded FFN outputs."""
        shared_expert_events = moe_events.get("shared_expert", [])
        if not self.low_latency_tp:
            wait_event(self.enable_multi_streams and hidden_states_share is not None, shared_expert_events, 1)
        routing_args, routing_quantizes_input = self._build_moe_tp_routing_args(x, topk_ids)
        if engram_resource_events is not None:
            record_event(True, engram_resource_events, 4, self.exe_mode)
        expanded_x, row_idx, expert_tokens, pertoken_scale = torch_npu.npu_moe_init_routing_v2(
            x, **routing_args)
        if engram_resource_events is not None:
            record_event(True, engram_resource_events, 5, self.exe_mode)
        shared_h, shared_scale = None, None
        if shared_merged_x is not None:
            record_event(True, moe_events["shared_pipeline"], 0)
            with npu_stream_switch(True, shared_expert_stream):
                wait_event(True, moe_events["shared_pipeline"], 0)
                shared_h, shared_scale = self.shared_experts.swiglu_a8float8(shared_merged_x)
        gmm_args = self._build_moe_tp_gmm_args(
            expanded_x, expert_tokens, pertoken_scale, routing_quantizes_input)
        self.experts.gmm1_events = moe_events["moe_gmm1"] if shared_merged_x is not None else None
        expert_output = self.moe_ffn(**gmm_args)
        if shared_merged_x is not None:
            main_stream = torch.npu.current_stream()
            with npu_stream_switch(True, shared_expert_stream):
                wait_event(True, moe_events["moe_gmm1"], 0)
                hidden_states_share = self.shared_experts.down_proj(shared_h, shared_scale)
                record_stream(True, hidden_states_share, main_stream)
                record_event(True, shared_expert_events, 1)
        if self.low_latency_tp:
            # Only Finalize consumes the shared branch; routing and GMM are independent.
            wait_event(self.enable_multi_streams and hidden_states_share is not None, shared_expert_events, 1)
        output = torch_npu.npu_moe_finalize_routing(
            expert_output, skip1=hidden_states_share, skip2=None, bias=None,
            scales=topk_weight.to(expert_output.dtype),
            expanded_src_to_dst_row=row_idx,
            export_for_source_row=None, drop_pad_mode=2)
        # Shared experts are intermediate-dim sharded too: one reduce for
        # routed + shared partial outputs.
        dist.all_reduce(output, group=self.comm_manager.get_group("moe_tp_group"))
        return output
```

</details>

## 设计决策

把专家编号、行段和格式枚举作为同一协议检查，可以定位“数据内容正确但消费者解释错误”的问题；目标后端若不用该表结构，仍可检查行段到专家的映射。

recipes 实例的决策：该实现保留现有二维表的行序；是否省略零计数专家由路由算子合同决定。low_latency_tp 的 custom SwiGLU 使用特定 block_size、round_scale 和 output_origin 参数，切换算子包必须重新核对完整签名。

## 验证信号

本轮只核对固定源码和逐字机制代码，验证的是调用契约。

- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 路由开关选择 type2；参数适配仅对一维返回值补专家编号，结果转为 int64。
- [来源平台：950（仅源码目标，未上板）；证据等级：artifact_verified，静态源码] 两次 GMM 接收同一 group_list_type 和专家表；low_latency_tp 的 custom SwiGLU 显式接收匹配的 group_index/type。

没有 kernel、图执行、精度、显存或性能通过信号；保持 draft，未生成 verified 事件。

## 部署验收

以下为待执行检查：目标框架先按其 ABI 覆盖有效/空专家、非连续活跃专家与反排列；若部署本文 recipes 接口，再在实际 NPU 和部署包版本上分别覆盖 type1/type2、零计数与非连续活跃专家；保存各阶段表格式、有效行和 scale 布局，使用相同输入权重对照输出。先完成逐阶段与最终精度验收，再单独测性能。

## 坏实践

在本文 recipes ABI 下把 type2 当累计边界、按 count 排序却不重排数据，或只修改 GMM 而留下默认格式的 SwiGLU，都会破坏协议。缺少 custom_ops 时应明确依赖失败，不能静默替换成不同签名并视为同一路径。

## 失效边界

其他量化方法、外部自定义算子支持版本和其他平台未验证；本卡不证明所有二维表均被这些算子接受。外部框架若有 token 丢弃、容量填充或不同专家编号体系，应先替换为自己的有效行与编号规则，再复用诊断方法。
