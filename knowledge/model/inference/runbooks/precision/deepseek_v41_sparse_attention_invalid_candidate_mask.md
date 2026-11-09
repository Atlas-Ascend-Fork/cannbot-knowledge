---
type: Runbook
title: 稀疏Attention无效候选：安全索引与归一化屏蔽
description: 候选含无效槽时，分别验证地址安全、softmax参与资格与Value贡献；可迁移的是不变量，-1及sink公式仅属历史参考接口。
tags:
- task.debugging
- topic.attention
- topic.precision
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:32:31Z'
platforms: []
aliases:
- DeepSeek V4.1 参考稀疏候选的双重屏蔽
---

# 稀疏Attention无效候选：安全索引与归一化屏蔽

## 适用性与框架边界

本卡是**可迁移机制**：无效候选既不能触发非法读取，也不能获得 softmax 权重或向输出贡献 Value。成立前提是所选 Attention 后端以“有效候选集合”定义结果；sentinel、有效长度、位图或融合跳过都可表达集合，不要求各引擎采用同一中间张量。

下文的 `-1`、共享 KV、每头 sink 以及“安全 gather → KV 清零 → logit 置负无穷”是 recipes 历史 PyTorch 参考函数的具体方案；当前 recipes 已切换量化融合 MLA，不能从参考函数推定融合内核内部实现。其他后端应按自己的候选和空行约定判断，不直接复制该公式。

vLLM 或其他引擎的读者可从实际选中的 **Attention backend** 定位候选选择、KV 读取和归一化；attention metadata builder 提供候选/有效长度等输入时，一并核对其生产规则。ModelRunner 负责实际执行输入与后端衔接；这里没有验证 vLLM 支持本文模型或算子，也没有提供补丁或配置映射。

## 现象

稀疏注意力只读取选中的历史位置。给候选列表补上无效槽后，原本有效位置的权重改变，或读取缓存时出现非法地址，应拆成三个观察项：地址是否可访问、候选是否进入归一化、候选是否贡献输出。只确认没有越界，仍不能排除分母污染。

## 适用场景

诊断原则适用于使用补齐候选、无效标记或有效长度的稀疏 Attention；具体行为须以目标后端合同为准。下列源码证据只覆盖 `gather → einsum → sink softmax → einsum` 的共享 KV 参考实现，适用粒度 `same_operator`；路线优先级 `recommended_fastpath` 仅描述这份参考代码采用的方式。候选索引由上游选择器提供，`-1` 表示无候选。历史平台与 CANN 实测范围未知，故 `platforms: []`，保持诊断草稿；素材没有索引报错、误差数值或修后 NPU 输出。

以下轴表解释 recipes 历史例子的生产消费关系；在自有后端先写出对应的逻辑角色，再使用实际布局和无效标记：

| 输入或中间量 | 轴与单位 | 生产者 → 消费者 |
|---|---|---|
| `query_states [B,M,H,D]` | B 个请求，每请求 M 个查询位置、H 个头、D 个通道 | Q 投影 → 匹配计算 |
| `kv_states [B,N,D]` | 每请求 N 行历史 KV；有效地址为 `[0,N)` | 缓存准备 → gather |
| `topk_idxs [B,M,K]` | 每查询 K 个候选槽；K 包含无效槽，不等于有效候选数 | 选择器 → gather 与 mask |
| `valid [B,M,K]` | 每个候选槽的布尔有效性；本函数只识别 `-1` | 索引判断 → KV/logit 屏蔽 |
| `logits [B,M,H,K]` | 每查询、每头、每候选的归一化前分值 | Q 与选中 KV 点积 → softmax |
| `attn_sink [H]` | 每头一个只进入分母的 sink 分值，不对应可输出的 Value | 模型参数 → softmax |

## 根因与判别方法

地址安全与候选参与资格是两条契约。可用删除候选、融合跳过或显式 mask 保证它们；具体方式取决于后端接口。下文参考方案先把 `-1` 临时替换为地址 0，才能安全 gather；这个 0 只是可读取的地址，不能让它变成真实候选。随后清零无效槽取到的 KV，并将对应 logit 置为 `-inf`。对有限 Q，清零 KV 后点积为 0，仍会贡献 `exp(0)=1`；只有 logit 屏蔽才从 softmax 分母中删除它。sink 则继续参与分母，不能把它误当作一条 KV。

**教学推演，非 NPU 观测。** 一个查询只有真实候选 a，却用两个槽存成 `[a,-1]`。设 a 的 logit 为 z、Value 为 v，sink 为 s。正确输出为 `exp(z)·v/(exp(z)+exp(s))`。若只安全取址并清零第二槽，它会把分母变成 `exp(z)+1+exp(s)`，即使其 Value 为 0 也会稀释 a。若只把 `-1` 换成 0 而不清零，则第 0 行真实 KV 还会污染匹配与输出。这个例子解释了为何“没有越界”不足以判定 mask 正确。

## 快速检查

1. 在自己的推理后端找到“候选选择 → 历史 KV 读取 → softmax → Value 累加”四个职责，记录实际调用路径。若使用融合算子，应查其接口和实际输出，不能把下述历史 Python 函数当作正在执行的内核。
2. 记录自有候选接口的轴、sentinel（无效标记）或有效长度及真实 N。按接口合同区分无效槽与非法索引；本卡历史例只接受 `-1` 或 `[0,N)`，其他负数/越界值须由生产者纠正，不能泛化这个 sentinel。
3. 沿同一候选核对读取地址、归一化参与资格和输出贡献。预期无效槽不触发非法读取，且对分母/输出均无贡献；融合跳过可不生成对应中间量。历史显式张量方案的观察项是安全索引、清零 KV 和 `-inf` logit，三者齐备仅排除这一方案的静态遗漏。
4. 在目标环境固定有效候选集合，只增加无效槽数量，与真正删除无效候选的独立参考比较。输出随无效槽数改变，支持分母或 Value 屏蔽问题；输出相同仍需另测越界、非有限输入与全无效情况。先确认目标后端的空行约定；下文带 sink 的接口还须分别检查有限 sink 与 sink 为 `-inf`。

## 完整代码

下面保留 recipes 历史完整前后函数与当前融合调用，供需要核对证据的读者对照。先按上面的三个不变量检查自己的后端；这些函数依赖参考实现的共享 KV 与 sink 接口。

<details>
<summary>recipes 实现对照：完整函数、轴广播与融合调用边界</summary>

### 修改前：无效索引直接进入 gather

阅读前版时，先看 `topk_idxs` 怎样原样进入 gather，再看 softmax 分母：这里没有候选有效性判断，后面的数值稳定化也不负责删除无效候选。函数输入是上表五项，返回 `[B,M,H,D]` 的加权输出。

```python
def sparse_attn(
    query_states,
    kv_states,
    attn_sink,
    topk_idxs,
    softmax_scale,
):

    B, M, H, D = query_states.shape
    N = kv_states.shape[1]
    K = topk_idxs.shape[-1]

    kv_selected = torch.gather(
        kv_states.unsqueeze(2).expand(B, N, K, D),
        dim=1,
        index=topk_idxs.unsqueeze(-1).expand(B, M, K, D)
    )


    logits = torch.einsum(
        "bsnd,bskd->bsnk",
        query_states,
        kv_selected
    )

    logits.mul_(softmax_scale)


    sink = attn_sink.reshape(1, 1, H, 1).to(logits)


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

    return output
```

### 修改后：安全 gather 与 softmax mask 成对出现

后版先产生 `valid` 与 `safe_idxs`，再把同一份有效性分别广播到 `[B,M,K,D]` 的 KV 和 `[B,M,H,K]` 的 logits。最后的 `probs` 只给真实 Value 分配权重；sink 的指数项保留在分母。

```python
def sparse_attn(
    query_states,
    kv_states,
    attn_sink,
    topk_idxs,
    softmax_scale,
):
    """BSND shared-KV attention; topk_idxs uses -1 for invalid candidates.

    Other indices must be in [0, N). Computation dtype and sink handling are
    unchanged. Invalid candidates contribute neither to softmax nor to output.
    """

    B, M, H, D = query_states.shape
    N = kv_states.shape[1]
    K = topk_idxs.shape[-1]

    valid = topk_idxs != -1
    # Replace -1 before gather; index 0 is only a temporary safe address.
    safe_idxs = topk_idxs.masked_fill(~valid, 0).long()
    kv_selected = torch.gather(
        kv_states.unsqueeze(2).expand(B, N, K, D),
        dim=1,
        index=safe_idxs.unsqueeze(-1).expand(B, M, K, D)
    )
    kv_selected = kv_selected.masked_fill(~valid.unsqueeze(-1), 0)


    logits = torch.einsum(
        "bsnd,bskd->bsnk",
        query_states,
        kv_selected
    )

    logits.mul_(softmax_scale)
    # Zero KV alone still contributes exp(0) to the softmax denominator.
    logits = logits.masked_fill(~valid.unsqueeze(2), float("-inf"))


    sink = attn_sink.reshape(1, 1, H, 1).to(logits)


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

    return output
```

### 当前主线融合调用：历史函数的适用边界

当前模型方法展示适用边界：它调用 `sparse_attn_ops`，而非上述参考函数。CP（上下文并行）把长提示词分给多个设备；代码中的 prev/next 是 Zigzag 调度的两段，因果可见范围不同，分别准备参数。这段调用代码不能揭示融合算子的内部 mask。

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

先定义有效候选集合，再分别证明读取安全与归一化/输出等价；不要以“安全地址”替代语义有效性。若后端会跳过无效槽，应检查跳过条件同时覆盖分母和 Value 累加；若显式物化张量，则沿 mask 广播轴逐项检查。

参考方案用 0 作为临时安全地址，清零 KV 与 mask logits 分别阻止输出污染和分母污染。原 dtype、scale 与 sink 稳定化公式保持原样；这些选择不构成其他后端必须清零 KV 的要求，也不能证明参考或融合 MLA 已通过精度验收。

## 系统信息

需要 `torch`，输入处于相同设备，`topk_idxs` 经 `.long()` 后用于 gather。该完整函数是历史参考实现；与它配套的示例只构造合法索引，不能充当 `-1` 用例的验证。

## 部署验收

待验：有限 sink 下分别覆盖混合合法/无效候选、全无效候选、首地址数据非零、候选数不同但有效集合相同；与逐项删除无效候选的独立参考比较，检查输出有限且不随无效槽数改变。还需单独检查任何小于 `-1` 或大于等于 N 的索引，后版只识别 `-1`，没有进行全范围校验。本轮没有执行这些试验。

## 验证信号

本轮只读取固定 Git 源码并恢复原始 blob 与函数字节。以下是实现的静态核对结果，不是模型/NPU 执行结果；未运行源仓脚本、测试、编译或推理。

- 恢复的后版函数中，安全索引生成、选中 KV 清零与 logit 置负无穷均存在，函数全文及前版均可从固定 blob 重建。（来源平台：历史源码目标未确认；证据等级：artifact_verified；范围：源码）
- 当前主线独立参考文件已不存在；Attention 的实际调用路径已改为量化融合算子。这个观测只确认代码路径变化。（来源平台：950 源码目标，未上板；证据等级：artifact_verified；范围：源码）

## 预防

让索引 sentinel、实际候选长度和 Value 屏蔽在同一审查中核对；补上无效候选用例，而不是仅运行全部索引合法的随机示例。

## 坏实践

只把 `-1` 换成 0 会引入真实第 0 行；只把选中 KV 置 0 会污染 softmax 分母；仅在最终输出置 0 无法修复部分候选无效时的权重偏差。不可把形状 padding 数直接当有效候选数。

## 失效边界

全无效且 sink 为 `-inf` 时，稳定化里的 `-inf - (-inf)` 可能产生 NaN；该后版没有显式全无效早退，应列为优先待验，不可承诺全无效输出必为 0。NaN/Inf KV、重复有效候选、越界索引和空 K 也未获验证。修复前后的运行数值缺失，不能据此发布“精度修复成功”。
