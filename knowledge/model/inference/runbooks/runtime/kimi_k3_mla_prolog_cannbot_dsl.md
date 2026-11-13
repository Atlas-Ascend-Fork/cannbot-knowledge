---
{
  "type": "Runbook",
  "title": "Kimi K3 MLA decode prolog 的 NZ 布局迁移（CANNBot-DSL mla_prolog/quant_mla_prolog）",
  "description": "Kimi K3 MLA decode prolog 使用 CANNBot-DSL mla_prolog/quant_mla_prolog 时的 NZ 布局迁移：三路投影权重转 [O,K] true FRACTAL_NZ、MXFP8 descale 转 NZ (K/64,O,2)；py_compile 与 6 项 CPU 单测通过、PR 创建成功。",
  "tags": [
    "task.implementation",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Kimi K3 MLA decode prolog 的 NZ 布局迁移（CANNBot-DSL mla_prolog/quant_mla_prolog）
## 适用场景
Kimi K3（cann-recipes-infer models/kimi_k3_1，MLA decode 路径）使用 CANNBot-DSL samples/attention 的 quant_mla_prolog / mla_prolog 算子并需要为其准备 NZ 布局权重的场景；依赖环境需安装含这两个算子的 CANNBot-DSL 算子包（如 --operators mla_prolog quant_mla_prolog 构建产物）。
## 触发与观测
- 触发：Kimi K3 MLA decode prolog 算子实现的迁移任务。
## 探针与操作
- 布局迁移：三路投影权重转 [O, K] true FRACTAL_NZ（pack_bf16_nz 用 npu_format_cast(linear.T.contiguous(), 29)，pack_mxfp8_nz 用 npu_format_cast(weight.detach().contiguous(), 29)）；MXFP8 权重 descale 转 NZ (K/64, O, 2)（pack_mxfp8_scale_nz）；激活 descale 逻辑形状改为 (T, dim/32)；新 mla_prolog 的 descale_q 为 (T, N, 1)，进入 quant_flash_mla_with_kvcache 前 squeeze 回 (T, N)。
通过 cannbot-dsl 0.7.1 包定位 samples/attention 的算子接口，读取 quant_mla_prolog 的 __init__ 导出面（WQrQuantMode/QkvQuantMode/CacheMode/RopeMode 枚举与 _VALID_PAIRS，事件 101）；对照旧调用点签名。
## 机制与判别
- 布局迁移：三路投影权重转 [O, K] true FRACTAL_NZ（pack_bf16_nz 用 npu_format_cast(linear.T.contiguous(), 29)，pack_mxfp8_nz 用 npu_format_cast(weight.detach().contiguous(), 29)）；MXFP8 权重 descale 转 NZ (K/64, O, 2)（pack_mxfp8_scale_nz）；激活 descale 逻辑形状改为 (T, dim/32)；新 mla_prolog 的 descale_q 为 (T, N, 1)，进入 quant_flash_mla_with_kvcache 前 squeeze 回 (T, N)。
- 验证：python -m py_compile 通过；pytest -q models/kimi_k3/tests/test_mla_prolog_allgather_order.py 6 passed；PR（feat(kimi-k3): migrate MLA decode prolog to CANNBot-DSL samples，head 4f1cb2e）创建成功，state=open、mergeable=true。
工件一：权重/尺度打包函数：

```python
def pack_bf16_nz(weight):
    """Convert a framework [K, O] Linear weight to Prolog [O, K] true NZ."""
    if weight.dtype != torch.bfloat16 or weight.ndim != 2:
        raise ValueError("BF16 MLA Prolog requires a two-dimensional BF16 weight")
    # Linear processing delivers [K, O] in ND or NZ; the DSL Prolog takes
    # true FRACTAL_NZ with the [O, K] logical shape.
    linear = torch_npu.npu_format_cast(weight.detach(), 2)
    return torch_npu.npu_format_cast(linear.T.contiguous(), 29)


def pack_mxfp8_nz(weight):
    """Checkpoint [O, K] E4M3 -> DSL Prolog [O, K] true FRACTAL_NZ."""
    return torch_npu.npu_format_cast(weight.detach().contiguous(), 29)


def pack_mxfp8_scale_nz(scale, output, k):
    """Checkpoint [O, K / 32] E8M0 -> DSL Prolog NZ (K / 64, O, 2)."""
    logical = scale.view(torch.uint8).reshape(output, k // 64, 2)
    return torch_npu.npu_format_cast(
        logical.permute(1, 0, 2).contiguous(),
        29,
        input_dtype=torch.float8_e8m0fnu,
    )
```

工件二：forward 调用点：

```python
        if self.use_w8a8c8:
            x, sx = torch_npu.npu_dynamic_mx_quant(x, dst_type=torch.float8_e4m3fn)
            sx = sx.view(torch.uint8).reshape(
                tokens, hidden_states.shape[-1] // 32
            ).view(torch.float8_e8m0fnu)
            outs = self.mla_prolog_op(
                x, self.mla_w_qa, self.mla_w_qb, self.mla_w_kva,
                self.kv_b_proj_decode_w_k, sx, self.mla_s_qa, self.mla_s_qb,
                self.mla_s_kva, self.mla_gamma_qa, self.mla_gamma_kva,
                cache, slots, self.mla_kv_scale,
                norm_eps=1e-6,
            )
            q, q_descale = outs[0], outs[1].reshape(tokens, -1)
        else:
            outs = self.mla_prolog_op(
                x, self.mla_w_qa, self.mla_w_qb, self.mla_w_kva,
                self.kv_b_proj_decode_w_k, self.mla_gamma_qa, self.mla_gamma_kva,
                cache, slots,
                norm_eps=self.q_a_layernorm.variance_epsilon,
            )
            q, _ = outs[0], outs[1]
```

工件三：descale_q 形状细化：

```python
q, q_descale = outs[0], outs[1].squeeze(-1)
```

判别要点：旧接口 NZ 权重以 set_ 视图暴露物理维会被算子拒绝，新 DSL 接口要求 true FRACTAL_NZ 且逻辑形状 [O, K]；MXFP8 权重 descale 需 NZ (K/64, O, 2)，与激活 descale 的 (T, dim/32) 逻辑形状配对。
## 验证信号
事件 297：python -m py_compile 通过（compile_ok）；事件 298/303：pytest -q models/kimi_k3/tests/test_mla_prolog_allgather_order.py 6 passed（4 warnings）；事件 370：PR #1 创建成功（state=open、mergeable=true，head 4f1cb2e）；事件 371：git log 确认提交 4f1cb2e。
## 适用与失效边界
验证层级为静态检查与 CPU 级单测（allgather 顺序逻辑，CPU tensors），未包含 NPU 数值一致性验证；运行环境需 CANNBot-DSL 算子包。适用于 K3 NoPE / PA_NZ 模式组合，其他 RopeMode/CacheMode 组合需按 _VALID_PAIRS 重新绑定。

## 补充机制片段
### 机制片段

### 机制片段

### 机制片段

### 机制片段
```python
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
6 passed, 4 warnings in 3.18s
```
