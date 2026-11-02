---
type: Runbook
title: FlashKDA Prefill 小算子与 padding 冗余：核对 packed TND 和分块状态交接
description: 仅在启用 FlashKDA 且 lower_bound 非空时，将逐请求 BSND 路线改为 packed TND；保留请求边界、FP32
  state 与 SP 去补齐契约，其他配置继续使用参考实现。
tags:
- task.debugging
- task.optimization
- topic.attention
- topic.data_movement
status: stable
sources: []
created_at: '2026-10-30T03:20:04Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
---

# FlashKDA Prefill 小算子与 padding 冗余：核对 packed TND 和分块状态交接

## 现象

Kimi K3 FlashKDA Prefill 的输入已经按请求拼成 packed token，但历史实现又按请求切片，逐请求补齐为 BSND、生成 metadata、调用算子，最后删除补齐并拼接。请求越多，Python 循环、metadata 调用和额外 padding 越明显。Profiler 中出现多个小调用时，应先核对实际分派与输入组织，不能仅看到 FlashKDA 名称就认定已经采用 packed TND。

本卡描述的是一次 packed 调用与状态交接的契约，未提供 NPU 耗时、显存或加速比实测。稳定内容是有条件的调用组织方式，不是对任意算子包版本的速度承诺。

## 适用场景

- 目标为 950PR/DT 的 Kimi K3 KDA Prefill；入口是 `KimiDeltaAttention._forward_core()` → `_chunk_kda_dispatch()` → `_prefill_flash_kda()`。
- 同时满足 `use_flash_kda=True`、`gate_params.lower_bound is not None`，且部署的 metadata/FlashKDA 包支持 packed TND、真实请求边界和尾块处理。
- `use_flash_kda=False` 或 `lower_bound=None` 继续走 PyTorch 参考路线，保留原 gate 语义；不为启用 TND 补造 lower_bound。
- CANN、torch_npu、外部算子包的版本组合必须以部署环境为准，本次未建立完整兼容矩阵；Decode 的 recurrent/fused 路线不由本卡替换。

## 数据契约与根因

令 `B` 为请求数、`T` 为本 chunk 的真实 token 总数、`H` 为本 rank 的 head 数、`D` 为 head 维度：

| 对象 | 逻辑形态与用途 |
| --- | --- |
| `q/k/v/g` | `(T, H, D)` 的真实 packed token；调用前连续化 |
| `beta` | `(T, H)`，对应每 token 每 head 的原始 beta 输入 |
| `query_start_loc` | 连续 int32 前缀和，长度 `B+1`，首项为 0、末项为 `T`；表达请求边界 |
| `initial_state` | FP32 `(B, H, D, D)`，按请求顺序组织，不按 token 组织 |
| 输出与 final state | 输出仍对应真实 packed token，final state 对应同一批请求，用实际 request cache ID 写回 |

历史 BSND 循环对每个请求单独执行切片、补齐、metadata 和调用，最后 cat/stack。TND 把边界交给算子：一次 metadata、一次 FlashKDA 消费整个真实 packed chunk，尾块由支持该接口的算子处理。两者不是只改一个 layout 字符串的差别。

SP/TP 的补齐是另一层语义。`_forward_core` 先根据 `prompt_tokens` 去掉 SP padding，再构造 TND；FlashKDA 返回真实 token 输出后，模型再补回外层 SP 布局。不能把 SP 的尾部零行当成一个请求的真实 token。

## 原路线与完整调用代码

以下方法来自所属类，依赖 `KdaInputs`、`KdaGateParams`、`math`、`torch`、`F`、`_flash_kda_metadata_impl`、`_flash_kda_impl` 和同类 helper。它们是模型方法原文，不是一个可以脱离模型直接执行的脚本。

原逐请求 BSND 方法完整展示了重复工作和 gate/beta 的 padding 规则：

```python
def _prefill_flash_kda(
    self,
    inputs: KdaInputs,
    gate_params: KdaGateParams,
    initial_state: torch.Tensor,
    query_boundaries: list[int],
) -> tuple[torch.Tensor, torch.Tensor]:
    # Restore the per-request BSND path; arena still requires scheduling metadata.
    outputs = []
    final_states = []
    for request, (start, end) in enumerate(
        zip(query_boundaries, query_boundaries[1:])
    ):
        q, k, v, g, b = self._slice_request_inputs(inputs, start, end)
        tokens, key_dim = q.shape[1], q.shape[3]
        pad_len = (-tokens) % _KDA_CHUNK_SIZE
        if pad_len:
            q, k, v = (
                F.pad(t, (0, 0, 0, 0, 0, pad_len)) for t in (q, k, v)
            )
            g = F.pad(g, (0, 0, 0, 0, 0, pad_len), value=float('-inf'))
            b = F.pad(b, (0, 0, 0, pad_len), value=float('-inf'))
        q, k, v, g, b = (t.contiguous() for t in (q, k, v, g, b))
        request_state = initial_state[request:request + 1]
        metadata = _flash_kda_metadata_impl(
            q, v, request_state, layout_qkv="BSND",
        )
        output, state = _flash_kda_impl(
            q, k, v, g=g, beta=b,
            scale=1.0 / math.sqrt(key_dim),
            initial_state=request_state,
            A_log=gate_params.a_log.data,
            dt_bias=gate_params.dt_bias,
            lower_bound=gate_params.lower_bound,
            layout_qkv="BSND",
            metadata=metadata,
        )
        if pad_len:
            output = output[:, :tokens].contiguous()
        outputs.append(output.squeeze(0))
        final_states.append(state.squeeze(0))
    return torch.cat(outputs), torch.stack(final_states)
```

改为 packed TND 后，把所有真实 token 一次交给 metadata 与算子，并保留原 gate 参数：

```python
def _prefill_flash_kda(
    self,
    inputs: KdaInputs,
    gate_params: KdaGateParams,
    initial_state: torch.Tensor,
    query_start_loc: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    # TND consumes the real packed tokens and existing int32 request offsets.
    # The kernel handles tail chunks; no per-request padding or launch is needed.
    q, k, v, g, b = (tensor.contiguous() for tensor in inputs)
    metadata = _flash_kda_metadata_impl(
        q, v, initial_state, layout_qkv="TND", cu_seqlens=query_start_loc,
    )
    return _flash_kda_impl(
        q, k, v, g=g, beta=b,
        scale=1.0 / math.sqrt(q.shape[-1]),
        initial_state=initial_state,
        A_log=gate_params.a_log.data,
        dt_bias=gate_params.dt_bias,
        lower_bound=gate_params.lower_bound,
        layout_qkv="TND",
        metadata=metadata,
    )
```

分派仍必须保留双条件。这里同时携带 Python `query_boundaries` 和 Tensor `query_start_loc`，分别供参考路线与 TND 路线使用，不能删除其中一套便破坏回退：

```python
def _chunk_kda_dispatch(
    self,
    inputs: KdaInputs,
    gate_params: KdaGateParams,
    initial_state: torch.Tensor,
    query_boundaries: list[int],
    query_start_loc: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    # Prefill: dispatch to flash_kda or torch reference by use_flash_kda.
    # Returns: output [tokens, H, D] bf16, final_state [batch, H, D, D] fp32.
    if self.use_flash_kda and gate_params.lower_bound is not None:
        return self._prefill_flash_kda(
            inputs, gate_params, initial_state, query_start_loc,
        )
    return self._prefill_torch_kda(
        inputs, gate_params, initial_state, query_boundaries,
    )
```

## 判别与处理步骤

1. 先记录双门控的实际值，确认本 chunk 进入 Flash 路线。若未进入，先解释配置和 gate 选择，不能拿参考路线的调用次数评估 TND。
2. 核对 `query_start_loc` 与 `query_boundaries` 表达同一请求顺序，边界末项等于**去 SP 补齐后的**真实 token 数；类型为连续 int32。不同请求不能因为拼接而失去边界。
3. 检查 metadata 与 FlashKDA 的 layout 都为 TND，metadata 返回值确实传入对应的这次 Flash 调用。若一端仍为 BSND，不能只修改另一端字符串。
4. 首 chunk 为每请求构造 FP32 初始 state；chunked Prefill 则从 `recurrent_state_ids` 指定的 cache 行读取，而不是每 chunk 重新清零。将返回 final state 写回同一请求 ID，未参与请求的状态保持不变。
5. 保留外层去 SP padding/补回输出的步骤，覆盖真实长度与补齐长度不同的情况。

## 设计决策与性能影响

用已有前缀和而不重新制造 padded batch，减少了逐请求调度工作，并让请求边界显式进入算子。对单个 packed chunk，期望 metadata 和 Flash 调用各一次；这是调用组织的验收，不等于算子只启动一个硬件 kernel，也不等于已经测得加速。

保留 PyTorch 参考路线既用于不支持的 gate 配置，也便于数值对照。它的 gate 激活方式应随 `lower_bound` 的实际分支保持，不把参考分支静默改成 Flash 的前置条件。

## 验证信号与待执行验收

已有 CPU/mock 测试定义检查以下接口事实：输入非连续时能在调用前连续化；请求前缀和以同一 Tensor 进入 metadata；Q/K/V/G 与 beta 形状符合 TND；state 为 FP32 且形状按请求；metadata 的返回对象交给同一 Flash 调用。mock 返回 `v.clone()` 和 `initial_state + 1`，用于检查输出与状态 plumbing，不模拟 NPU 数学。

连续两个 chunk 的检查还核对：后一 chunk 收到上一 chunk 更新的 state，实际请求 cache 行被写回，未参与请求行不变；SP 测试核对 Flash 只接收真实 token，模型输出恢复外层 padding。这里核对的是测试定义，本轮未执行上游 CPU/mock 或 NPU 测试。

部署验收应保存以下实际结果：

| 场景 | 通过信号 | 能证明的范围 |
| --- | --- | --- |
| 不同请求长度、非连续输入、尾块 | 一个 chunk 各调用一次 metadata/Flash，边界与 shape 正确 | 调用与布局 plumbing |
| 两个以上 chunk、稀疏 cache ID | state 连续交接，未参与行不变 | 请求到状态的映射 |
| SP 补齐 | 算子仅接真实 token，外层输出补回且补齐行正确 | 内外布局边界 |
| 开关关闭或 lower_bound 为空 | 进入原参考路线并保留 gate 语义 | 回退分派 |
| 目标 NPU 与参考实现对照 | 输出和 final state 在原精度条件下通过 | 算子数学与状态正确性 |
| 同一 workload 的资源对照 | 留存调用/launch 数、Prefill 耗时、峰值显存 | 实际性能，不能由 mock 推出 |

## 坏实践、回退与失效边界

不要把不支持 TND 的外部包仅靠修改 Python 参数硬接通；先检查真实 schema、metadata 要求和尾块能力。不要只删除旧 padding 而保留 BSND 组织，也不要让 `cu_seqlens` 包含 SP padding。

回退使用与目标包匹配的完整参考路线，保留原 gate 激活、请求切分、state 读写和输出布局；不能只恢复逐请求循环而遗漏旧 padding 的屏蔽规则。不得放宽精度容差以掩盖请求边界或 state 错误。

未决项为目标 NPU 的输出/state 验收和同 workload 的资源实测。只有这些结果完成后，才能说明该部署的收益；现有调用契约不能外推到任意 FlashKDA 版本。
