---
type: Runbook
title: KDA CP Prefill 卷积异常：临时 cache 的真实请求不得占用保留零槽
description: 实验分支修复把临时卷积 cache 扩一行并从非零槽分配请求，附 CPU 索引回归；零槽语义属于该 causal_conv1d 接口，不外推到其他状态缓存。
tags:
- task.debugging
- topic.precision
- topic.attention
- topic.parallelism
status: draft
sources: []
created_at: '2026-10-30T03:17:19Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      parallelism:
        all_of:
        - cp
      phase:
      - prefill
---

# KDA CP Prefill 卷积异常：临时 cache 的真实请求不得占用保留零槽

## 现象

Kimi K3 的 KDA CP Prefill 把每个请求的短卷积历史先放入层内临时 cache，再将最后一个 CP 分段的状态交给请求 owner、供后续 Decode 使用。若卷积输出出现异常或 NaN，除了检查输入和权重，还应检查这层临时 cache 的 slot 约定：该 `causal_conv1d` 接口将 slot 0 保留为 null，而旧代码从 0 开始给真实请求编号。

这只是定位卷积状态链的一条具体检查。当前没有修前修后 NPU 数值对照，不能仅凭提交描述把任何 CP NaN 都归因于这一点，也不能声称改完索引已解决整网精度。

## 适用场景

- 目标为 950PR/DT 上实验性的 KDA CP Prefill 路线，入口是 `KimiDeltaAttention` 在 `enable_cp` 分支中创建临时 `conv_cache`。
- 涉及 `temporary_conv_cache_ids()`、`previous_conv_state()`、`qkv_conv1d()` 和 `sync_last_cp_state()`；本卡只改临时卷积槽位，不更改 KDA recurrent state 的统一索引规则。
- 必须先确认部署版本支持该 CP 路线，且实际卷积接口仍保留零槽。CANN/算子包具体版本与 CP 组配置需按真实环境记录，没有确认时不进行全局索引替换。
- 优先把未修改的非 CP 路线保留为对照；实验路径通过状态和精度验收后再评估性能。

## 根因与状态交接链

令当前 packed batch 中真实请求数为 `B`，卷积历史宽度为 `K-1`，QKV 投影宽度为 `Q`。旧临时 cache 只有 `(B, K-1, Q)`，请求 ID 为 `[0, B)`；第一个请求因此占据保留的 null slot。

修复必须成对进行：容量改成 `(B+1, K-1, Q)`，真实请求 ID 改为 `[1, B+1)`。零槽保持预留，最后一个真实请求也有合法空间。只修改其中一端会分别留下首请求仍用 null 或末请求越界的问题。

CP 中的状态方向还要保持不变：每个 rank 收集本请求本段尾部，经 CP 组交换后得到前一个分段的卷积历史；本段卷积完成，再同步最后 CP rank 的完成状态；只有持有该请求持久块的 owner 才写回框架 cache。临时 slot ID 与框架 `state_ids` 不是同一命名空间。

## 判别方法

1. 从实际 forward 确认 `enable_cp`、`query_boundaries` 和 `batch = len(query_boundaries)-1`，不要把 SP 补齐 token 数当成请求数。
2. 记录 `conv_cache.shape`、`conv_state_ids` 的 dtype/取值、卷积调用收到的 cache 与 ID，以及 readback 时使用的 ID。真实请求 ID 不得含 0，最大 ID 必须小于 cache 第一维。
3. 检查初始历史写入、卷积调用、完成状态读回三处是否共用同一组临时 ID；三处中任何一处还按零起始读取都会破坏请求对应关系。
4. 再核对 owner 的持久块映射与 CP 最后分段同步，区分“卷积接口把首请求当 null”与“最终状态写错 owner”。两者不能凭相同的 NaN 现象混为一谈。

## 成对修改的机制代码

原 `enable_cp` 分支的临时容量和索引单元如下；这是模型方法内的局部因果块，依赖已计算的 `batch`、`fused_qkv` 和 `self`：

```python
conv_cache = fused_qkv.new_zeros(
    batch,
    self.qkv_conv1d.kernel_size - 1,
    self.qkv_projection_size,
)
conv_state_ids = torch.arange(
    batch, dtype=torch.int32, device=fused_qkv.device
)
```

修复后的同一单元为：

```python
conv_cache = fused_qkv.new_zeros(
    batch + 1,
    self.qkv_conv1d.kernel_size - 1,
    self.qkv_projection_size,
)
conv_state_ids = temporary_conv_cache_ids(batch, fused_qkv.device)
```

完整 ID helper 明确表达接口的零槽契约：

```python
def temporary_conv_cache_ids(batch: int, device: torch.device) -> torch.Tensor:
    """Return valid temporary slots; causal_conv1d reserves slot zero as null."""
    return torch.arange(1, batch + 1, dtype=torch.int32, device=device)
```

为了避免只改 ID 却丢失跨 CP 的历史，下面保留计算前段卷积历史的完整 helper。其 `_all_gather_first_dim` 依赖同一模块的 CP 通信封装；`query_boundaries` 是本 rank 上按请求划分的 token 边界：

```python
def previous_conv_state(
    local_qkv: torch.Tensor,
    query_boundaries: Sequence[int],
    state_width: int,
    group,
    cp_size: int,
    cp_rank: int,
) -> torch.Tensor:
    """Collect each segment tail and return the immediately preceding tail."""
    batch = len(query_boundaries) - 1
    tails = local_qkv.new_zeros(batch, state_width, local_qkv.shape[-1])
    for request, (start, end) in enumerate(
        zip(query_boundaries, query_boundaries[1:])
    ):
        length = min(state_width, end - start)
        if length:
            tails[request, -length:].copy_(local_qkv[end - length:end])
    gathered = _all_gather_first_dim(tails, group, cp_size)
    gathered = gathered.reshape(cp_size, batch, state_width, local_qkv.shape[-1])
    if cp_rank == 0:
        return torch.zeros_like(tails)
    return gathered[cp_rank - 1].contiguous()
```

后段的完整同步 helper 将最后一个 CP rank 的完成状态复制给各 rank，由 forward 中的 owner 判断决定是否写入持久 cache：

```python
def sync_last_cp_state(
    local_state: torch.Tensor,
    group,
    cp_size: int,
) -> torch.Tensor:
    """Replicate the last CP rank's completed state on every CP rank."""
    batch = local_state.shape[0]
    gathered = _all_gather_first_dim(local_state, group, cp_size)
    return gathered.reshape(cp_size, batch, *local_state.shape[1:])[-1].contiguous()
```

## 处理步骤与设计决策

改造时先扩大临时容量，再用 helper 生成 int32 ID。用这些 ID 把 `previous_conv_state` 写入临时 cache，原样传给 `qkv_conv1d`；卷积完成后仍用同一组 ID `index_select` 读回，再执行 `sync_last_cp_state`。持久 cache 的写回继续使用框架分配的 `state_ids`，不把临时 `[1, B+1)` ID 直接套到框架块表。

选择额外预留一行是为了服从该卷积接口，额外一行不增加真实请求数，也不改变 packed token 的 `cu_seqlens`。首 CP rank 使用零历史，其余 rank 使用上一分段历史；是否有初始状态的标记仍与 CP rank 对齐，而不是因为临时 cache 增加一行就给所有请求标为已有历史。

## 验证信号与验收步骤

已有 CPU 测试定义直接检查 helper 返回 int32、精确覆盖所有非零真实请求槽位、并且不含零。其完整测试函数如下，参数 `batch` 由该测试的参数化装饰器提供，`KCP` 为测试加载的模块对象：

```python
def test_temporary_conv_cache_ids_skip_reserved_null_slot(batch):
    cache_ids = KCP.temporary_conv_cache_ids(batch, torch.device("cpu"))

    assert cache_ids.dtype == torch.int32
    assert torch.equal(cache_ids, torch.arange(1, batch + 1, dtype=torch.int32))
    assert not torch.any(cache_ids == 0)
```

本轮核对了这些断言，但没有执行 CPU 或 NPU 测试。该测试即使通过，也只证明 ID helper，不证明临时 cache 容量、CP 通信、卷积内核或整网精度已正确。

部署验收还需完成：

- **局部索引**：不同 batch 下逐项核对容量、最小/最大真实 ID、ID dtype 和零槽未被真实请求使用；覆盖首个请求和最后一个请求。
- **状态链**：核对前段历史写入与本段读回的请求顺序，验证非 owner 不误写持久 cache，owner 写回的是最后分段状态。
- **数值对照**：同一输入、权重和原精度阈值下，比较 CP 与非 CP 的卷积输出、Prefill 最终状态、随后 Decode 输出；覆盖 CP 分片边界和含多请求的批次，并保留非有限值检查。

## 坏实践与回退

不要全库把状态索引零值加一；padding/null 请求、其他 Mamba 后端和 recurrent cache 可能有不同契约。不要只把 `arange` 起点改一而不扩大容量，也不要扩大容量却继续从零编号。不能靠关闭非有限值检查或放宽误差掩盖状态错误。

回退使用完整的非 CP 基线，并保留相同输入和权重以定位差异。回滚实验修改时，容量、ID helper 和所有使用点一起恢复；不要让初始写入与完成读回采用两套编号。

## 失效边界与未决项

优先未决项是目标 NPU 上复现卷积异常、核实所用 `causal_conv1d` 的 null 约定，并完成修前修后的单点数值对照。若异常来自权重、通信或其他状态路径，这项修改不能替代对应归因。未确认 CP 支持或接口版本时，本卡只作为诊断线索，保留 draft。
