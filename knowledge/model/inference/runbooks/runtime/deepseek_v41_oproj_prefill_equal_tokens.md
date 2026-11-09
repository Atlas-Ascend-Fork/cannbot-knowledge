---
type: Runbook
title: TP投影token数不等：通信前补齐并保留有效行
description: TP投影采用等分collective且各rank token数不同时，先达成统一通信长度并保留有效行映射；变长split或其他通信协议按自身合同处理。
tags:
- task.debugging
- topic.parallelism
- topic.data_movement
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：O 投影 TP 的变长前缀对齐
---

# TP投影token数不等：通信前补齐并保留有效行

## 适用性与框架边界

本卡是**可迁移机制**：同一次集合通信的参与者必须对分块元素数、轴顺序、归约归属和有效行达成一致。只有实际协议要求等尺寸块而各 rank token 数不同，才需要本文这种统一长度与 pad/trim；可变 split 或其他协议不自动要求相同补齐。

recipes 的 `oproj_tp_size`、组内 MAX、metadata 传递点，以及 AllToAll→组矩乘→ReduceScatter 的重排/裁剪位置，是普通 Attention DP + O 投影 TP 的方案。低时延 AllReduce、Attention TP 与其他后端须按各自协议检查，不能复制它的分支条件。

vLLM 或其他引擎可从 **模型 O 投影的 TP 实现、分布式通信组与实际 collective 边界**定位，ModelRunner 的输入准备用于确认本地有效 token 行；必要时追踪对应 metadata builder。无需查找 recipes 字段或 helper，也没有验证 vLLM 使用这条投影路线。

## 现象

多个设备分别处理不同长度提示词，却通过要求等尺寸块的集合通信共同执行 Attention 输出投影时，可能在集体通信处遇到形状不一致，或让补齐行混入后续残差计算。排查时要区分本地真实 token 数和通信要求的统一 token 数，不能只检查通道是否能被并行度整除。

O 投影把 Attention 各头的输出映射回模型隐藏维。以下是 recipes 的具体实例：DeepSeek V4.1 普通 Attention DP（数据并行，各 rank 处理不同请求）可以同时启用 O 投影 TP（张量并行，多个 rank 合作计算投影的通道/组）。这里每个 rank 是通信进程；即使本地请求不同，它们在同一个 O 投影通信组中仍要使用匹配的发送/接收形状。历史修改增加组内 MAX、pad 与 trim，没有实际通信错误日志或硬件复测。

## 适用场景

通用诊断适用于同组采用等尺寸 collective 的投影；下文精确 pad/trim 方案仅覆盖 recipes 普通 packed Prefill（把提示词有效 token 拼成连续行）中 attn_tp_size==1、oproj_tp_size>1 的输出投影。入口为 `get_prefill_oproj_max_tokens` 与 `Attention.attn_post`。低时延 TP 使用另一条 AllReduce（全归约）路径，不适用本卡 pad/trim 解释；Decode（逐步生成）及 Attention TP 也不由本卡证明。

源码目标 950，CANN 运行版本未确认，本轮只做固定源码及真实差异核对，未运行 NPU 推理、编译或跨 rank 通信。适用粒度 `exact_task`，路线优先级 `recommended_fastpath` 表示当前实现的契约，保持诊断草稿。

## 判别方法

先确认实际 collective 是否要求等尺寸分块，随后逐 rank 比较发送/接收元素数、目标轴和有效行归属；这些协议条件决定需要 padding 还是显式变长分割。recipes 这一条普通路径使用等分 AllToAll（全互换）和 ReduceScatter（归约后分发）。前者把不同投影组交给负责它们的 rank，后者把各组的隐藏维贡献相加并送回各 token 所属 rank。源码没有传入变长 split sizes，因而组内调用者需要先统一 token 维。

| 量/张量 | 轴、单位与生产消费关系 |
|---|---|
| P / oproj_tp_size | 同一 O 投影通信组内 rank 数 |
| Tlocal / Tmax | 本 rank 输入行数 / 同组各行数的最大值；模型在层循环前对 Tlocal 做 MAX |
| G / num_groups_per_rank | 当前 Attention 输出的投影组数，需可被 P 整除 |
| F | 展平后的每组输入特征宽度，`o` 进入通信前为 `[T,G,F]` |
| H | 模型隐藏通道数；wo_a/wo_b 投影并归约后的输出为 `[Tmax,H]` |
| `local_num_tokens` | pad 前保存的 Tlocal，最后裁剪成 `[Tlocal,H]` 供残差等后续模块使用 |

**教学推演，非通信观测。** 假设 P=2、G=4，rank0有3个 token，rank1有5个。MAX 得到 Tmax=5，rank0补2行，rank1不补；两边都将 `[5,4,F]` 视为 `[5,2,2,F]`，把目标 rank 轴移到前面。这样向每个对端发送的块都是 `5×2×F` 个元素，接收后为 `[10,2,F]`。两个 rank 分别计算所属投影组对所有 token 的贡献，再 ReduceScatter 得到各自 `[5,H]`；rank0裁成3行，rank1保留5行。若直接用3和5构造等分通信块，同组各自认为的分块大小就不一致；若最后不裁，rank0会把2行补齐数据交给后续模块。

补齐发生在输出投影局部边界，原始请求长度不应因此改写。真实实现的 MAX 结果是设备 int32 Tensor；它进入 F.pad 的转换/同步行为还需部署确认，不能自行加 `.item()` 后宣称没有行为变化。

## 快速检查

1. 在自己的后端找到 Attention 输出到隐藏维的投影链，标出数据并行分工、投影张量并行组及其 collective（集体通信）。确认实际是否走等分 AllToAll/ReduceScatter；可变 split 或低时延 AllReduce 需要按其自身协议诊断。
2. 在同一次通信调用前，逐 rank 记录本地有效行数、分块轴、dtype、组成员及调用顺序。若采用本文等分方案，还应核对 G/P、F、dtype 一致且 Tmax 来自同一个 O 投影组；通道整除但 T 不同，仍支持 token 维对齐问题。
3. 沿自有输入准备和投影调用追踪通信长度与行映射，确认每层使用同一协议。对采用本文 pad 方案的路径，全部 rank 应为 `[Tmax,G,F]` 并按同一目标 rank 顺序交换；recipes 通过 metadata 向 attn_post 传递 Tmax。shape 匹配却来源错乱时，继续查 transpose/flatten 的轴语义。
4. 跟随投影输出到实际归约与残差入口，检查协议恢复的行数、顺序和归属。采用本文 ReduceScatter 方案时，归约前应能按 P 个目标 token 块切分，归约后为 Tmax 行，裁剪后严格为原 Tlocal 行；多行、少行或错序都需继续核对有效行映射。
5. 在目标环境用不等长 rank 输入比较单独投影的参考结果，并覆盖空/非空 rank、真实 padding kernel 和量化分支。只有形状一致不能证明数值或通信通过；补齐额外计算/传输代价也应在同 workload 下测量。

可选的 recipes 源码导航命令如下；其他引擎按前述通信和投影职责定位自己的组件：

```bash
rg -n 'attn_post' models/deepseek_v4_1/models/modeling_deepseek.py
```


## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes O 投影对照：完整前后实现、MAX 与层前传递</summary>

以下是源文件中的完整函数或完整因果块，未改写为示意代码。它们依赖原工程上下文；不是可脱离工程直接运行的独立程序。

Attention.attn_post（`models/deepseek_v4_1/models/modeling_deepseek.py`）：

历史前版直接从 o.shape[0] 取得 num_tokens，并用它同时构造 AllToAll、组投影视图和 ReduceScatter。函数返回隐藏维 x；同组本地 T 不一致时，没有统一通信 token 维的步骤。

```python
    def attn_post(
        self,
        o: torch.Tensor,
        attn_metadata: Optional[Dict] = None,
    ):
        '''
        oproj_tp: split on group dim, o: [B, S, G, N, D/G] -> [B, S, G/tp_size, N, D/G]
        transpose to make the splitted dim to be the primary
        split o_a on group dim (batch); split o_b on group dim (reduce)
        '''
        num_tokens = o.shape[0]
        o = self.apply_rope(o, attn_metadata, inverse=True)
        o = o.view(num_tokens, self.num_groups_per_rank, -1).to(torch.bfloat16)
        if self.oproj_tp_size > 1:
            # [num_tokens, tp_size, G/tp_size, ND/G] -> [tp_size, BS, G/tp_size, ND/G]
            o = o.view(num_tokens, self.oproj_tp_size, self.num_groups_per_rank // self.oproj_tp_size, -1)
            o = o.transpose(1, 0).contiguous().view(-1)
            all2all_output = torch.empty_like(o)
            dist.all_to_all_single(all2all_output, o,
                                   group=self.comm_manager.get_group("oproj_tp_group"))
            o = all2all_output.view(self.oproj_tp_size * num_tokens,
                                    self.num_groups_per_rank // self.oproj_tp_size, -1)

        # o_a_proj
        if self.mm_quant_mode == "w8a8mxfloat8":
            o, o_scale = torch_npu.npu_dynamic_mx_quant(o, dst_type=torch.float8_e4m3fn)
            o = torch_npu.npu_transpose_quant_batchmatmul(o, self.wo_a.weight, dtype=torch.bfloat16,
                                                            x1_scale=o_scale.view(torch.float8_e8m0fnu),
                                                            x2_scale=self.wo_a.weight_scale.view(torch.float8_e8m0fnu),
                                                            group_sizes=(0, 0, 32), perm_x1=(1, 0, 2),
                                                            perm_x2=(0, 1, 2), perm_y=(1, 0, 2))
        else:
            o = torch_npu.npu_transpose_batchmatmul(o, self.wo_a.weight, perm_x1=(1, 0, 2), perm_y=(1, 0, 2))
        if self.oproj_tp_size > 1:
            # [oproj_tp_size, num_tokens, num_groups_per_rank // oproj_tp_size * o_lora_rank]
            o = o.view(self.oproj_tp_size, num_tokens, -1)
        else:
            o = o.view(num_tokens, -1)

        # o_b_proj
        x = self.wo_b(o)

        if self.oproj_tp_size > 1:
            # [oproj_tp_size, num_tokens, dim] --> [oproj_tp_size * num_tokens, dim]
            x = x.view(self.oproj_tp_size * num_tokens, -1)
            reduce_scatter_output = torch.empty((num_tokens, x.shape[-1]), dtype=x.dtype, device=x.device)
            dist.reduce_scatter_tensor(reduce_scatter_output, x,
                                       group=self.comm_manager.get_group("oproj_tp_group"))
            x = reduce_scatter_output.view(num_tokens, x.shape[-1])
        return x
```

Attention.attn_post（`models/deepseek_v4_1/models/modeling_deepseek.py`）：

当前方法先完成对应 RoPE（旋转位置编码）的逆变换，再保存 local_num_tokens；普通 O 投影 TP 的 Prefill 才按 metadata 补到 Tmax。后续通信和投影用统一 num_tokens，ReduceScatter 后按原长度裁剪。DSpark 是草稿模型，is_dspark 只区分它的旋转参数，不改变本卡普通通信形状契约。

```python
    def attn_post(
        self,
        o: torch.Tensor,
        attn_metadata: Optional[Dict] = None,
        is_dspark: bool = False,
    ):
        '''
        oproj_tp: split on group dim, o: [B, S, G, N, D/G] -> [B, S, G/tp_size, N, D/G]
        transpose to make the splitted dim to be the primary
        split o_a on group dim (batch); split o_b on group dim (reduce)
        '''
        num_tokens = o.shape[0]
        if is_dspark:
            rope_slices = attn_metadata["dspark_rope_slices"]
            draft_cos, _ = rope_slices["draft"]
            draft_neg_sin = rope_slices["draft_neg_sin"]
            o = self._apply_win_rope(o, (draft_cos, draft_neg_sin))
        else:
            o = self.apply_rope(o, attn_metadata, inverse=True)
        o = o.view(num_tokens, self.num_groups_per_rank, -1).to(torch.bfloat16)

        local_num_tokens = num_tokens
        if self.oproj_tp_size > 1 and self.attn_tp_size == 1:
            oproj_max_tokens = attn_metadata.get("oproj_max_tokens", None)
            if attn_metadata["is_prefill"] and oproj_max_tokens is not None:
                o = F.pad(o, (0, 0, 0, 0, 0, oproj_max_tokens - num_tokens))
                num_tokens = oproj_max_tokens
            # [num_tokens, tp_size, G/tp_size, ND/G] -> [tp_size, BS, G/tp_size, ND/G]
            o = o.view(num_tokens, self.oproj_tp_size, self.num_groups_per_rank // self.oproj_tp_size, -1)
            o = o.transpose(1, 0).contiguous().view(-1)
            all2all_output = torch.empty_like(o)
            dist.all_to_all_single(all2all_output, o,
                                   group=self.comm_manager.get_group("oproj_tp_group"))
            o = all2all_output.view(self.oproj_tp_size * num_tokens,
                                    self.num_groups_per_rank // self.oproj_tp_size, -1)

        # o_a_proj
        if self.mm_quant_mode == "w8a8mxfloat8":
            o, o_scale = torch_npu.npu_dynamic_mx_quant(o, dst_type=torch.float8_e4m3fn)
            o = torch_npu.npu_transpose_quant_batchmatmul(o, self.wo_a.weight, dtype=torch.bfloat16,
                                                            x1_scale=o_scale.view(torch.float8_e8m0fnu),
                                                            x2_scale=self.wo_a.weight_scale.view(torch.float8_e8m0fnu),
                                                            group_sizes=(0, 0, 32), perm_x1=(1, 0, 2),
                                                            perm_x2=(0, 1, 2), perm_y=(1, 0, 2))
        else:
            o = torch_npu.npu_transpose_batchmatmul(o, self.wo_a.weight, perm_x1=(1, 0, 2), perm_y=(1, 0, 2))
        if self.oproj_tp_size > 1 and self.attn_tp_size == 1:
            # [oproj_tp_size, num_tokens, num_groups_per_rank // oproj_tp_size * o_lora_rank]
            o = o.view(self.oproj_tp_size, num_tokens, -1)
        else:
            o = o.view(num_tokens, -1)

        # o_b_proj
        x = self.wo_b(o)

        if self.low_latency_tp:
            if self.compress_ratio == 0:
                dist.all_reduce(x, group=self.comm_manager.get_group("oproj_tp_group"))
        elif self.oproj_tp_size > 1:
            # [oproj_tp_size, num_tokens, dim] --> [oproj_tp_size * num_tokens, dim]
            x = x.view(self.oproj_tp_size * num_tokens, -1)
            reduce_scatter_output = torch.empty((num_tokens, x.shape[-1]), dtype=x.dtype, device=x.device)
            dist.reduce_scatter_tensor(reduce_scatter_output, x,
                                       group=self.comm_manager.get_group("oproj_tp_group"))
            x = reduce_scatter_output.view(num_tokens, x.shape[-1])

            # trim tokens if padded in prefill
            if attn_metadata["is_prefill"] and (local_num_tokens < num_tokens):
                x = x[:local_num_tokens]
        return x
```

DeepseekV41Model.get_prefill_oproj_max_tokens（`models/deepseek_v4_1/models/modeling_deepseek.py`）：

MAX helper 的输入是本 rank hidden_states，返回设备端单元素最大长度 Tensor。只有 Prefill 且 O 投影 TP>1 才生成；它使用的通信组必须与每层 O 投影消费组一致。

```python
    def get_prefill_oproj_max_tokens(self, hidden_states, is_prefill):
        # get global max tokens
        if not is_prefill or self.oproj_tp_size <= 1:
            return None
        local_num_token = hidden_states.shape[0]
        max_num_token = torch.tensor([local_num_token], dtype=torch.int32, device=hidden_states.device)
        dist.all_reduce(max_num_token, op=dist.ReduceOp.MAX, group=self.comm_manager.get_group("oproj_tp_group"))
        return max_num_token
```

DeepseekV41Model.forward prefill O-projection metadata handoff（`models/deepseek_v4_1/models/modeling_deepseek.py`）：

模型在层循环前把 MAX 结果写入 attn_metadata，使同一步各层得到同一预算。这里的 MoE（混合专家）chunk 准备只是相邻工程上下文，不属于 O 投影补齐机制。

```python
        residual = None
        prefill_moe_global_chunks = self.get_prefill_moe_global_chunks(hidden_states, is_prefill)
        attn_metadata["oproj_max_tokens"] = self.get_prefill_oproj_max_tokens(hidden_states, is_prefill)
```

</details>

## 设计决策

先选择与实际 collective 匹配的长度协议；等尺寸 pad 方案应只在 O 投影局部通信边界补齐，并携带原有效行映射，输出再裁回有效行，不改写原始请求长度。recipes 使用组内 MAX 后 pad/trim，代价来自 Tmax−Tlocal 的额外计算/传输；代价随请求分布变化，本轮无成对性能实测。MAX tensor 参与 F.pad 的设备与 host 同步行为需上板确认，不能自行 .item() 改写后称等价。

## 系统信息

recipes 实现对照的模型入口为 `models/deepseek_v4_1`，推理调度位于 `executor/core/model_worker`，通信由 CommManager 注册与解析。所有代码片段对应固定源码；内部版本、blob、行段和逐字摘要仅保存于本轮审计清单。

## 预防

检查本地 token 长度不等的 batch，追到 metadata 生成、每层消费、pad、ReduceScatter、trim 五个节点；验证 residual 接收到原本 Tlocal 行。

## 验证信号

来源是固定 Git 源码与其真实差异，不是 Agent 执行会话。本轮只验证实现、分支和映射的存在与逐字一致；以下没有运行通过、精度通过或性能改善的含义。

- 静态逐字核对 `models/deepseek_v4_1/models/modeling_deepseek.py` 的 `Attention.attn_post`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `models/deepseek_v4_1/models/modeling_deepseek.py` 的 `Attention.attn_post`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `models/deepseek_v4_1/models/modeling_deepseek.py` 的 `DeepseekV41Model.get_prefill_oproj_max_tokens`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。
- 静态逐字核对 `models/deepseek_v4_1/models/modeling_deepseek.py` 的 `DeepseekV41Model.forward prefill O-projection metadata handoff`，观察到本卡内联的分支/映射；此项仅证明固定源码行为（来源平台：源码目标 950；证据等级：artifact_verified）。

## 失效边界

本文具体方案假定 recipes oproj_tp_group 内分块维度、组数与 dtype 一致；通用可迁移部分仅是通信协议与有效行对应检查。使用变长 split 的接口不要求复制 Tmax pad/trim。全等长度 decode、oproj_tp_size=1、low_latency_tp、Attention TP 不由此卡诊断。待验：不同 rank 为空/非空请求时的 collective 行为和 padding kernel 支持。

本轮未执行 NPU 推理、真实 checkpoint 装载、跨 rank 通信或编译回放。隔离 CPU 检查仅在本卡验证信号明确列出的函数和输入范围内成立；其余部署验收仍待目标环境执行。

## 坏实践

用 oproj_tp_size 的整除校验代替 collective token 维一致性；补齐后忘记裁剪；在 low_latency_tp 的 AllReduce 路径复用普通 DP AllToAll 解释。
