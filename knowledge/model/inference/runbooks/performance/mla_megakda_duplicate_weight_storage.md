---
type: Runbook
title: Kimi K3 融合后常驻显存增加：检查 MLA 与 MegaKDA 是否重复保存 NZ 权重
description: 在 BF16 MLA Prolog 或 MegaKDA 接入后核对加载顺序与重复格式转换；分别检查 Prolog buffer 与对应 Linear、MegaKDA
  NZ root 与 Prefill 转置视图的存储共享，保留不同分片权重。
tags:
- task.debugging
- task.optimization
- topic.memory
- topic.data_movement
status: stable
sources: []
created_at: '2026-10-30T03:17:18Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      objective:
      - memory
---

# Kimi K3 融合后常驻显存增加：检查 MLA 与 MegaKDA 是否重复保存 NZ 权重

## 现象

Kimi K3 在昇腾 950PR/DT 上接入 BF16 MLA Prolog 或 MegaKDA 后，权重加载后的常驻显存增加；即使还没有执行长 Prefill，也能看到增量。此时先区分“融合算子需要独立布局”与“同一布局被准备了两次”。显存增加本身不是重复权重的证明，分配器缓存、编译缓存、算子 workspace 和不同 TP 分片也会占用内存。

本卡处理的是加载阶段的所有权问题：已有 Linear 的权重已经做过转置/格式后处理，融合路径又准备另一份等价权重，或者先为 MegaKDA 保存 NZ root，随后公共 Linear 后处理再次分配存储。诊断对象是权重的底层 storage，不是运行时 recurrent state、KV cache 或模型参数的 Python 对象数量。

## 适用场景

- 工程入口：`KimiLinearForCausalLM.process_weights_after_loading()`，涉及 `KimiMLAAttention.prepare_prolog_weights()` 和 `KimiDeltaAttention.prepare_mega_kda_weights()`。
- 平台与模式：目标为 950PR/DT；准备工作发生在图捕获之前，之后的 Prefill、Decode 必须继续遵守各自的权重布局。本文没有给出可移植到任意 CANN/torch_npu 版本的保证，未确认的版本应在部署环境另行记录。
- 精度边界：下述共享方案针对 BF16 MLA 和 BF16 MegaKDA。C8 MLA 的打包、scale 和 gamma 仍有独立准备契约，不直接套用 BF16 引用方式。
- 使用顺序：先确认重复存储及实际消费者，再修改加载顺序；先通过输出和状态验收，再讨论节省显存。未核对量化模式或分片关系时不启用共享改造。

## 根因与数据流

检查点必须放在权重后处理的前后两个阶段。加载后的 checkpoint Linear 起初是 `[out, in]` 方向；公共 MatMul 后处理可能转置并转 NZ。若 BF16 Prolog 在前面保留了一份，再执行 ND → 转置 → NZ，会得到另一份 allocation。即使数值相同，二者也不共享 storage。

MegaKDA 的方向正好相反：融合入口需要原始 `[out, in]` 方向的 NZ allocation root，Prefill Linear 使用其转置视图。因此让两者共用 storage 的方式不是让 shape 一致，而是“一个 root，两种消费者视图”；同时必须把这些 Linear 从公共重复后处理中排除，否则刚建立的共享关系又会被替换。

## 判别方法

1. 固定同一权重、量化模式、并行配置和算子路线，在 `process_weights_after_loading()` 前后分别记录每个配对的 dtype、逻辑 shape、stride、`storage_offset()`、`untyped_storage().nbytes()`、`untyped_storage().data_ptr()`，在 NPU 上同时记录格式。不要只用 `id(tensor)` 或 `is_contiguous()` 判断。
2. 对照下表逐项检查。`detach()` 可以产生新 Tensor 对象但复用 storage；转置视图可以 shape/stride 不同而复用 storage。只要消费者布局和分片正确，这两种差异都不构成重复。
3. 若配对地址不同，沿加载顺序定位第一次发生独立分配的 `format_cast`、`contiguous` 或公共后处理，而不是在 forward 中强制替换权重。
4. 只有配对共享且两阶段输出验收通过，才比较加载后常驻显存和推理峰值。常驻显存下降不自动代表长 Prefill 峰值下降。

| 路径 | 应共享存储的配对 | 消费者语义 |
| --- | --- | --- |
| BF16 MLA Prolog | `mla_w_qa` ↔ `q_a_proj.weight` | Prolog 引用已经后处理的 QA 权重 |
| BF16 MLA Prolog | `mla_w_qb` ↔ `q_b_proj_decode.weight` | 引用全头 Decode QB，不能替换成 Prefill 分片 |
| BF16 MLA Prolog | `mla_w_kva` ↔ `kv_a_proj_with_mqa.weight` | 引用已经后处理的 KVA 权重 |
| MegaKDA | `_mega_qkv_weight` ↔ `qkv_proj.weight` | 前者为 root，后者为转置视图 |
| MegaKDA | `_mega_fa_weight` ↔ `f_a_proj.weight` | 前者为 root，后者为转置视图 |
| MegaKDA | `_mega_fb_weight` ↔ `f_b_proj.weight` | 前者为 root，后者为转置视图 |
| MegaKDA | `_mega_beta_weight` ↔ `b_proj.weight` | 前者为 root，后者为转置视图 |
| MegaKDA | `_mega_output_gate_weight` ↔ `g_proj.weight` | 前者为 root，后者为转置视图 |
| MegaKDA | `_mega_output_projection_weight` ↔ `o_proj.weight` | 前者为 root，后者为转置视图 |

特别检查 MLA 的两套 QB：`q_b_proj` 使用 `attn_tp_size`/`attn_tp_rank`，而 `q_b_proj_decode` 使用 `tp_size=1`、`tp_rank=0`。当 Attention TP 大于一时，Prefill 持有按头分片的权重，Decode 持有全部头。二者不在上表的共享配对内；不得为“消除重复”把分片权重强行合并。

## 处理步骤与机制代码

以下方法保留所属类中的 `self`、`nn`、`torch`、`torch_npu` 及量化 helper 依赖；它们不是脱离模型可直接运行的独立脚本。迁移时应核对同一实现的构造和消费者，不能只复制最后一行赋值。

原 BF16/C8 共用准备入口在公共 Linear 后处理之前执行，BF16 分支额外创建布局：

```python
def prepare_prolog_weights(self) -> None:
    """Prepare BF16/C8 buffers once, before shared Linear postprocessing."""
    if self.use_w8a8c8:
        from ops.quant_mla_prolog import quant_mla_prolog_op

        self.mla_prolog_op = quant_mla_prolog_op
    else:
        self.mla_prolog_op = torch.ops.cann_ops_transformer.mla_prolog
    for name, linear in (("qa", self.q_a_proj), ("qb", self.q_b_proj_decode),
                         ("kva", self.kv_a_proj_with_mqa)):
        weight = linear.weight.detach()  # Checkpoint [O, K], before transpose/NZ.
        if self.use_w8a8c8:
            packed = pack_mxfp8_nz(weight)
            self.register_buffer(f"mla_s_{name}", logical_mx_scale(
                linear.weight_scale.detach(), *weight.shape,
            ))
        else:
            nd = torch_npu.npu_format_cast(weight, 2)
            packed = torch_npu.npu_format_cast(nd.transpose(0, 1).contiguous(), 29)
        self.register_buffer(f"mla_w_{name}", packed)
    if self.use_w8a8c8:
        self.register_buffer("mla_gamma_qa", self.q_a_layernorm.weight.detach().float().contiguous())
        self.register_buffer("mla_gamma_kva", self.kv_a_layernorm.weight.detach().float().contiguous())
        self.register_buffer("mla_kv_scale", torch.tensor(
            [1.0], dtype=torch.float32, device=self.q_a_proj.weight.device,
        ))
```

改造后 C8 保持原打包路径，BF16 分支直接引用当前 Linear 权重；这一步必须在公共后处理完成后执行：

```python
def prepare_prolog_weights(self) -> None:
    """Pack C8 before Linear postprocessing; share BF16 weights afterwards."""
    if self.use_w8a8c8:
        from ops.quant_mla_prolog import quant_mla_prolog_op

        self.mla_prolog_op = quant_mla_prolog_op
    else:
        self.mla_prolog_op = torch.ops.cann_ops_transformer.mla_prolog
    for name, linear in (("qa", self.q_a_proj), ("qb", self.q_b_proj_decode),
                         ("kva", self.kv_a_proj_with_mqa)):
        weight = linear.weight.detach()
        if self.use_w8a8c8:
            packed = pack_mxfp8_nz(weight)
            self.register_buffer(f"mla_s_{name}", logical_mx_scale(
                linear.weight_scale.detach(), *weight.shape,
            ))
        else:
            packed = weight
        self.register_buffer(f"mla_w_{name}", packed)
    if self.use_w8a8c8:
        self.register_buffer("mla_gamma_qa", self.q_a_layernorm.weight.detach().float().contiguous())
        self.register_buffer("mla_gamma_kva", self.kv_a_layernorm.weight.detach().float().contiguous())
        self.register_buffer("mla_kv_scale", torch.tensor(
            [1.0], dtype=torch.float32, device=self.q_a_proj.weight.device,
        ))
```

MegaKDA 先创建六个 NZ root，让 Prefill 参数引用其转置，并返回需要跳过公共后处理的 Linear 集合：

```python
def prepare_mega_kda_weights(self) -> set[nn.Module]:
    """Share NZ roots with MegaKDA and transpose views with Prefill."""
    prepared = set()
    if not self.use_mega_kda:
        return prepared
    for name, linear in (
        ("qkv", self.qkv_proj),
        ("fa", self.f_a_proj),
        ("fb", self.f_b_proj),
        ("beta", self.b_proj),
        ("output_gate", self.g_proj),
        ("output_projection", self.o_proj),
    ):
        if linear.weight.dtype != torch.bfloat16:
            raise ValueError(f"MegaKDA requires BF16 {name} projection weights")
        weight = torch_npu.npu_format_cast(linear.weight.detach().contiguous(), 29)
        setattr(self, f"_mega_{name}_weight", weight)
        linear.weight.data = weight.transpose(0, 1)
        prepared.add(linear)
    return prepared
```

整个初始化顺序需要同时调整，不能只修改上面某一个方法：

1. C8 MLA 打包、MegaKDA root 准备在公共 Linear 后处理之前完成。
2. `_split_kv_b_proj()` 仍读取 checkpoint 原始方向，因此先于会改变 Linear 布局的循环，相关 `kv_b_proj` 模块继续跳过。
3. 公共循环首先跳过 `prepared_mega_linears`，其余模块按本身 quant method 处理。
4. 最后再为非 C8 的 MLA 绑定 Prolog buffer，准备 MegaKDA 卷积权重及其他 runtime buffer；这些步骤均在 graph capture 之前。

下面保留实际后处理方法中的完整因果段；前面的模块名表负责决定其他 Linear 是否使用 NZ，这里不改变其选择：

```python
prepared_mega_linears = set()
for module in list(self.modules()):
    if isinstance(module, KimiMLAAttention) and module.use_w8a8c8:
        module.prepare_prolog_weights()
    elif isinstance(module, KimiDeltaAttention):
        prepared_mega_linears.update(module.prepare_mega_kda_weights())
self._split_kv_b_proj()
for module_name, module in self.named_modules():
    if module in prepared_mega_linears:
        continue
    if "kv_b_proj" in module_name:
        continue
    if isinstance(module, KimiShortConvolution):
        module.build_conv_weight()
        continue
    quant_method = getattr(module, "quant_method", None)
    if quant_method is not None and hasattr(
        quant_method, "process_weights_after_loading"
    ):
        module_leaf_name = module_name.rsplit(".", 1)[-1]
        is_nz = module_leaf_name in nz_linear_module_names
        quant_method.process_weights_after_loading(module, is_nz=is_nz)
for module in self.modules():
    if isinstance(module, KimiMLAAttention) and not module.use_w8a8c8:
        module.prepare_prolog_weights()
    if isinstance(module, KimiDeltaAttention) and module.use_mega_kda:
        # Pack before graph capture; keep Prefill's [K, 3*H*D] layout.
        module._mega_conv_weight = (
            module.qkv_conv1d._conv_weight.view(
                module.qkv_conv1d.kernel_size, 3, module.num_heads, module.head_dim
            ).permute(1, 2, 0, 3).contiguous()
        )
self.model.prepare_attn_res_effective_queries()
self.model.initialize_runtime_buffers()
```

## 设计决策

BF16 MLA 选择“后处理完成后引用”，避免重复转换；MegaKDA 选择“先建立 root，再给 Prefill 转置视图”，因为其融合 ABI 需要原始方向。两种方法解决的是同一所有权问题，却不能交换执行顺序。C8 的权重编码需要独立打包，因此保留在前置准备中；把所有模式统一放到循环之后会破坏其输入假设。

## 验证信号

已核对实现中的三组 MLA 配对、六组 MegaKDA 配对，以及跳过重复 Linear 后处理的集合传递。这里确认的是代码中的共享机制，没有执行目标 NPU 的显存或数值实验；本卡的 stable 内容是上述加载和诊断契约，不是实测节省承诺。

部署验收按以下顺序留存结果：

- **存储层**：九组配对共享底层 storage；MegaKDA root 保持自身方向，Linear 视图满足 Prefill MatMul 约定；不同 TP 分片不要求共享。
- **计算层**：原精度阈值下对齐 Prefill、Decode 两阶段输出，覆盖 BF16/C8 开关及实际 TP 配置；有 chunked Prefill 时验证跨 chunk 状态交接。不能仅以加载成功作为通过。
- **资源层**：同一 workload 比较加载完成后的常驻占用和推理峰值，分开报告；没有这两组实测就不报节省比例。

## 坏实践与预防

- 只比较 Python 对象身份，误把 `detach()` 或转置视图当成新权重；应比较 storage，并同时检查 offset、方向和布局。
- 为了共享让 `q_b_proj` 与 `q_b_proj_decode` 指向同一 Tensor，破坏 TP 分片语义。
- 改了 `prepare_mega_kda_weights()` 却继续让公共循环处理同一 Linear，共享关系会在后续转换中丢失。
- 在 forward 中反复 `format_cast` 或改写 `.weight.data`，把一次性准备变成执行期分配与图输入变化。

## 回退与失效边界

回退必须恢复配套的准备顺序、后处理和编译缓存，不能只回滚一个转置。布局发生变化后重新生成主模型编译缓存，再以相同输入做对照。

未决项是目标环境的常驻/峰值显存和精度实测。本卡不能证明任意融合版本都允许复用同一种视图；ReplaySSM 对 allocation root 的额外要求见 [NZ allocation root 检查](../runtime/megakda_replayssm_nz_allocation_roots.md)。
