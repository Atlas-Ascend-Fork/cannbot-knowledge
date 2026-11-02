---
type: Runbook
title: MegaKDA ReplaySSM 权重 ABI 排查：NZ 视图不能替代原始 allocation root
description: 核对 ReplaySSM 的原始方向、shape、BF16 和 FRACTAL_NZ root，复用加载阶段的权重所有者；重复转置和 format_cast
  不构成 root 契约证明。
tags:
- task.debugging
- topic.memory
- topic.compilation
- topic.data_movement
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
      phase:
      - decode
---

# MegaKDA ReplaySSM 权重 ABI 排查：NZ 视图不能替代原始 allocation root

## 现象

Kimi K3 使用 MegaKDA ReplaySSM Decode 路线时，权重即使打印出预期 shape、BF16 和 FRACTAL_NZ，也可能不满足图调用的 allocation root 契约。常见切入点是 `prepare_mega_replayssm_weights()`：如果它取 Prefill Linear 的权重，反向转置、`contiguous()` 再 `npu_format_cast(..., 29)`，不能因此认定得到了独立且正确的原始 root。

本卡保存这条接口的 ABI 检查与适配方式。当前没有可直接引用的完整修前图错误现场，也未完成修后目标 NPU 验收；因此不能把下面的静态检查等同“本次已复现并修好”的结论，卡片继续为 draft。

## 适用场景

- 工程入口：`KimiDeltaAttention` 的 `prepare_mega_kda_weights()` → `prepare_mega_replayssm_weights()` → ReplaySSM Decode 调用。
- 目标范围：950PR/DT、BF16 MegaKDA、启用 `use_mega_kda_replayssm` 的接口版本。普通 snapshot MegaKDA 的可接受 Tensor 形态不能代替 ReplaySSM 的要求。
- 必要前提：六个原始方向 NZ root 已在加载阶段准备，并由模型持有，Prefill Linear 使用这些 root 的转置视图；本卡不通过修改外部算子 ABI 绕过要求。
- 具体 CANN、PyTorch、torch_npu 与算子包版本必须随部署记录。本次未建立任意版本组合都有效的兼容矩阵。

## 根因与判别方法

NZ format 是布局属性，allocation root 还包含“实际由谁拥有这块存储”的身份。Prefill 的 `[in, out]` 权重本身可能是原 root 的转置 view；再次转置或 cast 不足以证明回到了算子要求的 root。这里必须沿权重准备链核对所有权，不能只看最后两个维度相同。

1. 先确认 `use_mega_kda_replayssm` 实际为真，并检查 root 准备先于 ReplaySSM 准备、后者先于 capture；否则验证的是另一条路线。
2. 对照下表检查每个 root 的逻辑 shape、dtype 和格式；隐藏维度应取对应 Linear 的真实输入/输出尺寸，不用某个测试 shape 常量替代。
3. 检查 `_mega_replayssm_*` 是否直接引用 `_mega_*` root，同时核对 Prefill Linear 仍是匹配的转置视图。`detach()` 不代表重新分配，storage 地址相同也不单独证明 ABI root 身份；准备阶段的所有权链同样需要确认。
4. root 缺失、shape 不符或格式/dtype 不符时先失败退出，回查构造和准备阶段；不要继续 capture 才让外部算子报告更晚的错误。

| ReplaySSM 参数 | 应引用的 root | 预期逻辑 shape |
| --- | --- | --- |
| `_mega_replayssm_qkv_weight` | `_mega_qkv_weight` | `(qkv_projection_size, qkv_proj.input_size)` |
| `_mega_replayssm_decay_a_weight` | `_mega_fa_weight` | `(head_dim, f_a_proj.input_size)` |
| `_mega_replayssm_decay_b_weight` | `_mega_fb_weight` | `(projection_size, head_dim)` |
| `_mega_replayssm_beta_weight` | `_mega_beta_weight` | `(num_heads, b_proj.input_size)` |
| `_mega_replayssm_output_gate_weight` | `_mega_output_gate_weight` | `(projection_size, g_proj.input_size)` |
| `_mega_replayssm_output_weight` | `_mega_output_projection_weight` | `(o_proj.output_size, projection_size)` |

## 尝试过的路线与机制代码

旧准备方式中的完整局部 helper 如下。`self`、`nn`、`torch` 和 `torch_npu` 来自外层模型作用域；此片段展示被替换的转换逻辑，不是推荐的独立实现：

```python
def to_nz(
    linear: nn.Module, expected_shape: tuple[int, int], label: str
) -> torch.Tensor:
    weight = linear.weight.detach().transpose(-2, -1).contiguous()
    if weight.dtype != torch.bfloat16:
        raise TypeError(
            "MegaKDA ReplaySSM requires BF16 projection weights, got "
            f"{weight.dtype}"
        )
    if tuple(weight.shape) != expected_shape:
        raise RuntimeError(
            f"MegaKDA ReplaySSM {label} weight has shape "
            f"{tuple(weight.shape)}, expected {expected_shape}"
        )
    return torch_npu.npu_format_cast(weight, 29)
```

它先从已经后处理的 Linear 反向转置，再 cast 到 NZ。shape 检查能发现维度不符，却不能证明返回值满足 allocation root 契约。这是“形状/格式看起来正确仍须追溯存储所有者”的关键区别。

适配方式直接复用已有 root。下面是包含 shape 检查的完整准备方法；较早的复用实现只检查 root 存在、格式和 BF16，部署时应检查实际版本是否也包含这里的 shape 防线：

```python
def prepare_mega_replayssm_weights(self) -> None:
    """Prepare the same KDA weights in ReplaySSM's required ABI format.

    ``prepare_mega_kda_weights`` has already converted the six checkpoint
    weights to FRACTAL_NZ allocation roots and made the Prefill Linear
    parameters transpose views of those roots. Reusing the roots here is
    required: transposing a FRACTAL_NZ Linear view and casting it again
    leaves a view of FRACTAL_NZ storage, which the ReplaySSM graph ABI
    rejects.
    """
    if not self.use_mega_kda_replayssm:
        return

    roots = (
        (
            "qkv",
            self._mega_qkv_weight,
            (self.qkv_projection_size, self.qkv_proj.input_size),
        ),
        (
            "decay-a",
            self._mega_fa_weight,
            (self.head_dim, self.f_a_proj.input_size),
        ),
        (
            "decay-b",
            self._mega_fb_weight,
            (self.projection_size, self.head_dim),
        ),
        (
            "beta",
            self._mega_beta_weight,
            (self.num_heads, self.b_proj.input_size),
        ),
        (
            "output-gate",
            self._mega_output_gate_weight,
            (self.projection_size, self.g_proj.input_size),
        ),
        (
            "output",
            self._mega_output_projection_weight,
            (self.o_proj.output_size, self.projection_size),
        ),
    )
    replay_names = (
        "_mega_replayssm_qkv_weight",
        "_mega_replayssm_decay_a_weight",
        "_mega_replayssm_decay_b_weight",
        "_mega_replayssm_beta_weight",
        "_mega_replayssm_output_gate_weight",
        "_mega_replayssm_output_weight",
    )
    for (label, root, expected_shape), replay_name in zip(roots, replay_names):
        if root is None:
            raise RuntimeError(
                f"MegaKDA ReplaySSM {label} weight root was not prepared"
            )
        if tuple(root.shape) != expected_shape:
            raise RuntimeError(
                f"MegaKDA ReplaySSM {label} weight has shape "
                f"{tuple(root.shape)}, expected {expected_shape}"
            )
        fmt = torch_npu.get_npu_format(root)
        fmt_id = fmt.value if hasattr(fmt, "value") else int(fmt)
        if fmt_id != 29:
            raise RuntimeError(
                f"MegaKDA ReplaySSM {label} weight must be FRACTAL_NZ, "
                f"got format={fmt_id}"
            )
        if root.dtype != torch.bfloat16:
            raise TypeError(
                "MegaKDA ReplaySSM requires BF16 projection weights, got "
                f"{root.dtype} for {label}"
            )
        setattr(self, replay_name, root)
```

该方法依赖前一阶段创建的六个 `_mega_*` 属性，不能单独粘贴到没有 root 准备的类上。引用关系的建立也必须发生在 graph capture 前；不能在 replay 过程中重绑参数或临时重新转换。

## 设计决策

优先保留一次加载、一份 root、多路消费者的所有权结构，而不是为了 ReplaySSM 从 Prefill view 再造六份权重。这里有两个同时成立的要求：ReplaySSM 得到原 root，Prefill 仍得到其正确方向的视图。只解决其中一端可能让另一阶段失效。

显存共享与 ABI root 是相邻但不同的验收项：共享关系可见 [避免重复权重存储](../performance/mla_megakda_duplicate_weight_storage.md)，本卡额外要求算子调用拿到正确所有者。普通 MegaKDA 能调用一个 view，不足以推出 ReplaySSM 也能调用。

## 验证信号与待执行验收

本轮已核对准备方法的直接引用、六组 shape 检查，以及缺失 root、错误格式和错误 dtype 的失败分支。没有执行 ReplaySSM NPU capture/replay；文中的 RuntimeError/TypeError 文字来自实现的显式检查，不是伪造的运行日志。

目标部署需要依次留存：

1. 六个参数的 root 来源、逻辑 shape、format、dtype、offset 和 storage 关系；每个断言失败都回到加载阶段解释，不删除断言。
2. 同一权重与输入下，Prefill 输出及最终 recurrent state 对齐原路线，确认准备改造没有影响转置视图消费者。
3. ReplaySSM capture 成功后，改变真实输入、slot 和接受长度执行多轮 replay，核对状态提交、历史状态保留、输出和生成精度；单次能调用不覆盖 replay 的状态语义。
4. 若需要评价资源成本，在同一配置分别记录常驻显存和图内存池占用；没有实测不报告省显存或提速结果。

## 坏实践、回退与失效边界

- 禁止以 `contiguous()`、`detach()` 或再次 `format_cast(..., 29)` 的存在作为 root 证明；必须核对准备链和消费者 ABI。
- 不要把缺失 root 的报错改成从任意 Linear 静默重建，这会掩盖准备顺序问题，可能恢复重复分配。
- 回退应成套恢复权重准备与算子版本。如果切回 snapshot MegaKDA，还必须同步关闭 ReplaySSM 并恢复对应 state/metadata，不能只改一个开关或缩小状态池。

未决项优先是目标 NPU 上的修前错误复现与修后完整验收，以及当前算子包对 allocation root 的准确接口要求。接口若已经改变，应重新读取真实 schema，不凭另一版算子经验扩大适用范围。
