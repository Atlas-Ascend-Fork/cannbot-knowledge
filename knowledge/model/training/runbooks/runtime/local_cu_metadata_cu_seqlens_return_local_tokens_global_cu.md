---
{
  "type": "Runbook",
  "title": "Qwen GDN CP 排障：head exchange 后勿重复叠加序列 CP，撤回错误边界重建草案",
  "description": "回查同一轨迹后续纠正：现有GDN在head exchange后持有完整序列；早期补cp_context及按本地长度重建全局边界的草案不应采用，NaN/Inf根因仍未闭合。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---


# Qwen GDN CP 排障：head exchange 后勿重复叠加序列 CP，撤回错误边界重建草案

## 适用场景

- 平台范围依据：source 0 seq 53的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 框架/模型链路：torchtitan-npu（qwen3dot6 适配）Qwen3.5/3.6 GDN（Gated Delta Net）线性注意力，vendored FLA 算子 + Ascend GDN；CP/FSDP2/DP 并行。
- 平台/版本：Ascend NPU 训练（目标 Qwen3.6 9B/27B，64K 长序列 SFT，入口 `0914-qwen35_9b_64k_cp8_fsdp2_sft.sh`）。
- 目标：解释"CP=2/4 单独可用、CP+FSDP2（如 CP4+FSDP2）梯度 NaN/Inf、CP=1 不支持"的三态症状。

## 触发与观测

- 触发（user_reported，source 0 seq 314）："CP和FSDP2两种并行都存在时，例如CP=4，FSDP=2，会出现训练梯度为NAN和INF的问题，如果只是CP=2或4，并不会出现。且不支持CP=1的训练方式，一定需要CP并行"。

## 探针与操作

- 源码核对（source_read，source 0 seq 463/521/660/739 系列 rg/sed 探针）：对照 `flash-linear-attention/fla/ops/gated_delta_rule`、`fla/ops/cp` 与 qwen3dot6 vendored 树的 CP 接口面。
- 已被后续分析否定的历史草案（source 0 seq925/956），保留用于识别错误路线，**不可作为修复采用**。其“每rank仍持有局部序列”的前提与现有head exchange路径不符，`[0,total]`也会丢失文档边界：

```python
def build_fla_cp_context(metadata, mesh, conv1d_kernel_size: int):
    """Build the operator-level FLA CP context for a rank-local Qwen batch.

    Qwen's CP adapter presents each rank with a contiguous local shard.  FLA
    needs the pre-shard sequence boundaries to compute recurrent-state and
    convolution boundary communication, so reconstruct the single packed
    sequence used by the long-context recipe from the local length.
    """
    from fla.ops.cp import build_cp_context

    local_cu = metadata.cu_seqlens
    if mesh.size() <= 1:
        return None
    local_tokens = int(local_cu[-1].item())
    global_cu = local_cu.new_tensor([0, local_tokens * mesh.size()])
    return build_cp_context(
        global_cu,
        group=mesh.get_group(),
        conv1d_kernel_size=conv1d_kernel_size,
    )
```

历史草案还给 `chunk_gated_delta_rule` 与 `causal_conv1d` 增加了 `cp_context`，并增加CP=1分支。这些编辑和语法检查不构成训练正确性证据；下面按后续纠正说明为什么不能直接采用。

## 机制与判别

- 区分两种执行方式：FLA原生序列CP需要跨rank递归状态与卷积边界通信；sequence→head交换则先让每rank获得完整序列、只保留部分heads。后者不能仅因没有 `cp_context` 就判为“CP退化为独立分段”。
- 本来源的 `exchange_sequence_heads` 在GDN计算前执行sequence→head重分布（source 0 seq394/653）。seq1243明确纠正早期分析：各rank已经持有完整序列，不能再叠加FLA的序列CP context。初期“缺cp_context导致CP+FSDP2 NaN/Inf”诊断撤回，真实NaN/Inf根因仍未闭合。
- `build_sequence_metadata` 已通过Replicate重建全局文档边界（source 0 seq653）。再取其末项乘mesh.size会重复放大长度；即使输入真的还是局部分片，单凭本地长度也不能恢复packed文档内部边界。
- seq1968用全局 `[0,4,7,12]` 与各rank局部边界解释这一差别；seq2185再次指出 `[0, local_tokens * mesh.size()]` 对packed variable-length文档不可靠。各rank token数相同并不能修复边界丢失。
- 早期还比较过gate backward的FP32累加差异（source 0 seq675）；其与本次NaN/Inf的因果关系没有运行验证，不能用来替代已撤回的根因。

## 验证信号

- 早期草案的 `py_compile` 与 `bash -n` 通过（source 0 seq1033），仅说明语法；它发生在后续路径纠正之前，不能验证草案的CP语义。
- source 0 seq1243明确撤回前述关键判断；seq394/653的源码及后续seq1968/2185的边界分析可用于检查错误路线。
- NaN/Inf组合症状来自用户报告（seq314）；原轨迹未提供该草案修复前后的NPU训练数值对照。

## 适用与失效边界

- 用于Qwen GDN并行路径审计：先确认进入算子前到底是局部序列还是全序列/head分片，再决定是否需要原生FLA序列CP通信。
- 必须保留真实全局 `cu_seqlens` 的全部文档边界，不能用单一 `[0,total]` 代替packed文档集合；不能将已经全局化的末项再次乘CP degree。
- 不把本页作为NaN/Inf根因已定位或修复成功的依据；CP-only、CP+FSDP2和CP=1的训练正确性仍需在相同版本、负载下分别验证。

## 附：断言存档

- source 0 seq1243纠正了早期缺cp_context诊断：head exchange后每rank已有完整序列，不能再机械叠加序列CP context。
- 历史 `build_fla_cp_context` 草案既可能重复放大全局长度，也会丢失packed文档内部边界；语法通过不能证明其正确，应撤回采用。
