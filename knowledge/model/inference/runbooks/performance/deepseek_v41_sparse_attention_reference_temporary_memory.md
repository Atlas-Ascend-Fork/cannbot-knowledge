---
type: Runbook
title: 参考Attention显存膨胀：检查物化张量与原位复用
description: 参考张量路径显存不足时，按真实物化与存活期定位峰值；原位复用需有限输入和无旧值依赖，历史三处补丁不证明当前融合内核收益。
tags:
- task.optimization
- topic.attention
- topic.memory
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms: []
aliases:
- DeepSeek V4.1 参考Attention的物化与原位复用
---

# 参考Attention显存膨胀：检查物化张量与原位复用

## 适用性与框架边界

本卡是**可迁移机制**：显存成本取决于实际物化的张量、dtype 与同时存活期；把结果改为原位操作，只有在旧值无消费者、无别名/autograd依赖且数值语义允许时才成立。应先判断峰值来自基础物化还是临时副本。

recipes 历史 PyTorch 参考函数中的 `mul_`、`masked_fill_`、`div_` 三处替换是实例，不是融合 Attention 的改法，也没有实现按预算 query 分块。当前 recipes 已用量化融合 MLA；它的 workspace、CP 固定两段调用和内存峰值须单独核对。

vLLM 或其他引擎可从 **Attention backend 的参考/融合执行路径与 workspace 分配**入手，由 ModelRunner 的执行输入确定本次 query 规模，再以目标环境分配记录定位峰值。无需查找 recipes 函数或配置；这里没有验证 vLLM 模型/算子支持或可直接应用的补丁。

## 现象

长提示词的 Prefill（一次处理提示词）出现显存不足（OOM）时，稀疏 Attention 仍可能物化很大的候选 KV、匹配分值和归一化副本。先把本次查询规模与实际分配、存活期对应起来，才能判断原位复用是否覆盖瓶颈；“只选 K 个候选”不能替代内存归因。

本卡用历史参考函数展示可重建的分配变化。素材没有 OOM 栈、峰值显存或修后通过日志，不能把提交主题当成修复结果。

## 适用场景

诊断原则用于自有参考张量路径的显存归因；以下完整实现的证据范围限于历史共享 KV 函数，适用粒度 `exact_task`，路线优先级 `recommended_fastpath` 仅描述历史采用的原位路线。历史执行平台未确认，`platforms: []`；当前融合路线源码目标为 950，本轮均未运行。输入须有限，且中间量不存在反向传播（autograd）或外部别名依赖；这些前提之外没有等价性验证。

以下轴表对应 recipes 历史示例，其他后端须换成真实物化布局。函数中的 Query（Q）由当前 token 投影产生，Key/Value（KV）来自窗口与压缩历史，上游选择器为每个查询给出候选索引。参考函数先收集候选，再计算权重并加权同一批 KV。

| 符号 | 在本函数中的含义 | 决定的存储 |
|---|---|---|
| M（或输入的 T） | 本次 packed 查询行数；三维 Q 被补成 `[1,M,H,D]` | 随本次处理的查询数增长 |
| H、D | 每查询的头数、每头通道数 | Q 为 `[1,M,H,D]` |
| N | 可读取的共享 KV 行数，输入为 `[N,1,D]` | 索引有效范围 `[0,N)` |
| K | 每查询候选数组的尾维，包含 `-1` 补齐槽 | gather 为 `[1,M,K,D]`，logits 为 `[1,M,H,K]` |
| sink / `attn_sink [H]` | 每头一个只进入softmax分母的额外分值，不对应输出Value | 模型参数 → 归一化 |
| b | 为估算而假定的每元素字节数；实际以各中间量 dtype 为准 | 元素数乘 b 才是字节数 |

该方法的 KV 与索引组织按单个 packed 批次处理，不能因为局部变量写了 B 就外推为任意 B 的实现。有效候选较少也不会自动缩小已分配的 K 轴。

## 根因与判别方法

先确认每个操作创建视图还是分配独立 storage，再将各 storage 的存活区间叠加找峰值。对下文参考路径，`expand` 只建立重复读取的视图；`gather` 要生成真实的候选 KV，第一项 `einsum` 要生成真实 logits。仅这两项就占 `b×M×K×D + b×M×H×K`，还未计输入、指数、概率、分母与输出。减少归一化的副本不能消除这两项随查询数增长的成本。

**教学推演，非显存实测。** 假设一次有 4 个查询、每个 3 个候选槽、2 个头、每头 4 个通道。gather 物化 48 个元素，logits 物化 24 个元素；给这批查询增加一倍行数，两者也各增加一倍。前版又为 KV mask、logit mask 和概率除法分别生成相应尺寸的结果；后版重用这三处已有结果，48 与 24 这两个基础物化量仍存在。这里的数字只是解释元素计数，不是源模型配置或可支持长度。

后版的 KV 屏蔽改成乘布尔 mask。有限输入时可据此分析复用；但 `NaN×0`、`Inf×0` 仍可能产生 NaN，并不等价于 `masked_fill(...,0)`。若异常值污染输出，应先检查这一变化，不能只看内存是否下降。

## 快速检查

1. 在自己的工程中确定报错发生在参考张量运算还是融合 Attention 内。保存实际 OOM 位置、执行模式和分配记录；若是融合工作区失败，下述 Python 中间量估算只能作定位思路。
2. 找到“展开历史视图 → 复制候选 → 计算匹配分值 → 指数/归一化”四个阶段。记录各输出的真实 shape、dtype、分配字节和存活期；逻辑 expand 尺寸不计作独立分配，gather 输出要计入。
3. 按实测 M/K/H/D 估算物化下界，并与峰值区间比对。gather/logits 已占主要成本，说明单靠三处原位化可能不足；若副本长期并存，继续检查结果是否仍被调试器或外部引用持有。
4. 替换前先核对原数据是否还会被使用，再以相同输入、dtype、推理模式比较峰值和输出。有限输入结果接近而峰值下降，才支持这次复用有效；出现 NaN/Inf 或别名冲突时回到原分配路线定位，不能放宽误差标准。
5. 若仍超预算，分别检查整步 KV 分配与融合工作区；需要新的查询分块方案时应独立设计与验收。本历史修改没有实现它。

## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes 历史前后完整函数与当前融合调用对照</summary>

### 修改前：mask与归一化分配新张量

前版中 `safe_idxs/valid` 维护候选有效性，gather 产生 `kv_selected`，einsum 产生 `logits`。注意三个重新赋值位置：KV 的 masked_fill、logits 的 masked_fill、exp_logits 的除法都返回新结果。最后返回 `[M,H,D]`。 `max_val` 同时考虑真实候选和 sink 以稳定指数计算；`exp_sink` 只加入分母，最后输出仍是选中 KV 的加权和。

```python
    def sparse_attn(
        self,
        query_states,
        kv_states,
        topk_idxs
    ):
        """BSND shared-KV attention; topk_idxs uses -1 for invalid candidates.

        Other indices must be in [0, N). Computation dtype and sink handling are
        unchanged. Invalid candidates contribute neither to softmax nor to output.
        """
        if query_states.ndim == 3:
            T, H, D = query_states.shape
            query_states = query_states.view(1, T, H, D)

        B, M, H, D = query_states.shape
        N = kv_states.shape[0] #T,1,D
        K = topk_idxs.shape[-1] #M,K

        valid = topk_idxs != -1  #M,K
        # Replace -1 before gather; index 0 is only a temporary safe address.
        safe_idxs = topk_idxs.masked_fill(~valid, 0).long()
        kv_selected = torch.gather(
            kv_states.expand(N, K, D),
            dim=0,
            index=safe_idxs.unsqueeze(-1).expand(M, K, D)
        ).view(1, M, K, D)#B,M,K,D
        valid = valid.unsqueeze(0) # 1,m,k
        kv_selected = kv_selected.masked_fill(~valid.unsqueeze(-1), 0)

        logits = torch.einsum(
            "bsnd,bskd->bsnk",
            query_states,
            kv_selected
        )
        logits.mul_(self.softmax_scale)
        # Zero KV alone still contributes exp(0) to the softmax denominator.
        logits = logits.masked_fill(~valid.unsqueeze(2), float("-inf"))

        sink = self.attn_sink.reshape(1, 1, H, 1).to(logits)
        max_val = torch.maximum(
            logits.amax(-1, keepdim=True),
            sink
        )

        exp_logits = torch.exp(logits-max_val)
        exp_sink = torch.exp(sink-max_val)
        probs = exp_logits / (exp_logits.sum(-1, keepdim=True) + exp_sink)
        output = torch.einsum(
            "bsnk,bskd->bsnd",
            probs,
            kv_selected
        )

        return output.view(M, H, D)
```

### 修改后：三处原位复用

后版沿同一数据流，只把三处结果改为 `mul_`、`masked_fill_`、`div_`。`exp_logits.div_` 后 `probs` 复用它的存储；gather、logits、exp 的生成本身仍在。阅读时还要检查乘零对非有限值的边界。

```python
    def sparse_attn(
        self,
        query_states,
        kv_states,
        topk_idxs
    ):
        """BSND shared-KV attention; topk_idxs uses -1 for invalid candidates.

        Other indices must be in [0, N). Computation dtype and sink handling are
        unchanged. Invalid candidates contribute neither to softmax nor to output.
        """
        if query_states.ndim == 3:
            T, H, D = query_states.shape
            query_states = query_states.view(1, T, H, D)

        B, M, H, D = query_states.shape
        N = kv_states.shape[0] #T,1,D
        K = topk_idxs.shape[-1] #M,K

        valid = topk_idxs != -1  #M,K
        # Replace -1 before gather; index 0 is only a temporary safe address.
        safe_idxs = topk_idxs.masked_fill(~valid, 0).long()
        kv_selected = torch.gather(
            kv_states.expand(N, K, D),
            dim=0,
            index=safe_idxs.unsqueeze(-1).expand(M, K, D)
        ).view(1, M, K, D)#B,M,K,D
        valid = valid.unsqueeze(0) # 1,m,k
        kv_selected.mul_(valid.unsqueeze(-1).to(kv_selected.dtype))

        logits = torch.einsum(
            "bsnd,bskd->bsnk",
            query_states,
            kv_selected
        )
        logits.mul_(self.softmax_scale)
        # Zero KV alone still contributes exp(0) to the softmax denominator.
        logits.masked_fill_(~valid.unsqueeze(2), float("-inf"))

        sink = self.attn_sink.reshape(1, 1, H, 1).to(logits)
        max_val = torch.maximum(
            logits.amax(-1, keepdim=True),
            sink
        )

        exp_logits = torch.exp(logits-max_val)
        exp_sink = torch.exp(sink-max_val)
        probs = exp_logits.div_(exp_logits.sum(-1, keepdim=True) + exp_sink)
        output = torch.einsum(
            "bsnk,bskd->bsnd",
            probs,
            kv_selected
        )

        return output.view(M, H, D)
```

### 当前主线：融合Attention调用及CP两段调用

当前融合调用用于辨认运行路径。CP（上下文并行）把长上下文分布到不同设备，固定的两个 Zigzag 段分别有因果元数据；`q.chunk(2)` 是调度语义，不能作为按显存预算分块的证据。

```python
    def sparse_attn(self, q, win_kv, cmp_kv, cmp_sparse_indices, attn_metadata, is_prefill):
        if is_prefill and self.cp_size > 1:
            if self.layer_idx == 0:
                wait_event(self.enable_multi_streams, attn_metadata["metadata_event"], 1)
            # The two zigzag segments see different causal ranges, so each runs with its own metadata.
            q_prev, q_next = q.chunk(2, dim=0)
            if cmp_sparse_indices is None:
                idx_prev, idx_next = None, None
            else:
                idx_prev, idx_next = cmp_sparse_indices.chunk(2, dim=0)
            o_prev = self.sparse_attn_ops(**self.prepare_fa_kwargs(
                q_prev, win_kv, cmp_kv, idx_prev, attn_metadata["prev"], is_prefill))[0]
            o_next = self.sparse_attn_ops(**self.prepare_fa_kwargs(
                q_next, win_kv, cmp_kv, idx_next, attn_metadata["next"], is_prefill))[0]
            output = torch.cat([o_prev, o_next], dim=0)
            return self.select_local_attn_heads(output)
        fa_kwargs = self.prepare_fa_kwargs(q, win_kv, cmp_kv, cmp_sparse_indices, attn_metadata, is_prefill)
        if self.layer_idx == 0:
            wait_event(self.enable_multi_streams, attn_metadata["metadata_event"], 1)
        return self.select_local_attn_heads(self.sparse_attn_ops(**fa_kwargs)[0])
```

</details>

## 设计决策

原位化决策应按存储所有权和旧值的最后消费者做出，并以实际峰值与输出对照验收；融合后端则按其 workspace 合同处理。原位化只适用于不再需要原数据的中间张量。这里 logits 的屏蔽发生在后续最大值/exp 之前，exp_logits 归一化后直接作为 probs 使用；若调试器、反向传播或外部别名还依赖改写前数据，则需重新评估。当前主线 CP 中的 `q.chunk(2)` 是两段 Zigzag 元数据的语义拆分，不是根据显存自适应切 query 的 OOM 方案。

## 系统信息

参考代码依赖 PyTorch 的 gather/einsum 与共享 KV 格式。当前代码依赖 950 的量化融合 MLA 算子与单独生成的元数据，不能把历史参考的逐行显存估计直接等同于当前内核工作区。

## 性能影响

可以从源码确认少了三个与主中间张量同尺寸的结果分配；没有同机成对峰值显存或时延数据，不能填节省百分比、可支持长度或收益承诺。

## 部署验收

待验：在同输入、dtype、执行模式下测前后峰值 allocated/reserved，并做输出误差比较；单独记录 gather、logits、exp 的尺寸与存活期。若仍 OOM，再定位是否为融合算子 workspace、整步 KV 分配或别的模块；不得把未实现的 query chunk 当作已有修复。本轮未执行这些检查。

## 验证信号

本轮只读取固定 Git 源码并恢复原始 blob 与函数字节。以下是实现的静态核对结果，不是模型/NPU 执行结果；未运行源仓脚本、测试、编译或推理。

- 前后完整方法仅将选中 KV 屏蔽、logit 屏蔽和概率除法改为原位形式；不存在新加入的 query chunk 循环。（来源平台：历史源码目标未确认；证据等级：artifact_verified；范围：源码）
- 当前主线使用融合 MLA，CP 条件下固定调用两个 Zigzag segment；这是调用图事实，没有 OOM 重现结果。（来源平台：950 源码目标，未上板；证据等级：artifact_verified；范围：源码）

## 预防

把实际内存报错、执行路径、张量角色和峰值观测一起保存；审查显存补丁时先识别 view 与物化操作，再检查临时张量是否仍被引用。

## 坏实践

将提交标题“fix OOM”当成运行通过；把 `expand` 的逻辑尺寸算作实际分配；声称该补丁实现 chunk；为了避免比较失败而放宽输出容差，均不能支持结论。

## 失效边界

没有 NPU OOM 原始信号、峰值分配或成功 AFTER，当前候选只接纳为历史源码的显存归因诊断规则，不能作为已验证OOM修复配方。输入本体与不可避免的 gather/logits 已超预算时，原位化仍不够；有训练/autograd需求、NaN/Inf输入或别名复用时也未验证。
