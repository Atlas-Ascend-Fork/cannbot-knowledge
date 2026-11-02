---
type: Runbook
title: C8 MLA 图编译残留 auto_functionalized_v2：检查可变 FP8 cache 与 E8M0 scale 边界
description: 实验适配以 uint8 原始字节跨越 opaque 算子图边界，在内部恢复 FP8/E8M0 视图；保留 cache mutation 和不可变
  scale 视图身份，CPU 回归不替代 NPU 验收。
tags:
- task.debugging
- topic.compilation
- topic.graph_execution
- topic.precision
status: draft
sources: []
created_at: '2026-10-30T03:17:18Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      execution_mode:
      - npugraph_ex
      model_features:
        all_of:
        - mla
      phase:
      - decode
---

# C8 MLA 图编译残留 auto_functionalized_v2：检查可变 FP8 cache 与 E8M0 scale 边界

## 现象

Kimi K3 C8 MLA 把 Prolog 的量化投影、FP8 cache 更新和 Flash MLA 接成同一条 Decode 路线。目标 PyTorch 2.10 的 `npugraph_ex` 在 AOT 后的展开阶段出现 `auto_functionalized_v2 was not removed` 时，应检查 opaque 算子的签名，而不只是检查 Prolog 或 FA 能否单独 eager 调用。

这里有两个边界：cache 是原地修改的 FP8 编码存储，权重 scale 是不可变的 E8M0 编码。只把 cache 改成 uint8，而让 E8M0 scale 继续穿过高阶节点签名，仍可能留下展开问题。本卡给出已存在的适配机制和验收方法；目标 PyTorch/NPU 的修后结果尚待确认，保持 draft。

## 适用场景与依赖

- 工程路径：`models/kimi_k3/models/mla_w8a8c8.py` 的 `QuantMLADecode.forward()` → `torch.ops.kimi_k3_mla.w8a8c8_decode` → `_decode_impl()` → Native Prolog 与量化 Flash MLA。
- 目标是 950PR/DT 的 MLA MXFP8 权重、E4M3 cache、`npugraph_ex` Decode。具体 CANN/torch_npu、编译后端和算子包版本需在部署验收时记录，不能由卡片的 `platforms` 推断组合兼容。
- 适配器对真实权重、scale、归一化参数及 Native 接口还有既有约束；此处只解释图边界问题，不放宽权重布局、核数、norm epsilon 或算子 schema。
- 未验证其适用于任意 PyTorch、其他 FP8 dtype、其他模型、GE 图或所有可变算子。CPU AOT 与目标 NPU 需要分开验收。

## 根因判别：四个层次不能混在一起

| 层次 | 要确认的事实 | 不能据此得出的结论 |
|---|---|---|
| Native 单算子 | 实际 Prolog/FA 接口、dtype 和布局能调用 | 整个模型的 AOT 展开一定通过 |
| opaque 外层签名 | FP8/E8M0 是否仍作为外层张量 dtype，cache 是否声明可变 | 输出 shape 的 fake 实现正确就代表 mutation 正确 |
| AOT 后图 | 是否确实出现并成功展开 `auto_functionalized_v2` | 仅 `aot_eager` 返回即覆盖了相同展开 pass |
| NPU capture/replay | 更新、历史保留与输入变化是否正确 | CPU surrogate 的赋值通过即代表 NPU cache 写入正确 |

先保留完整失败堆栈和失败 pass 的图，定位留下的高阶节点及它的参数 dtype。再核对所有 `scales` 和 `cache`，不能只检查其中一项。错误发生在编译期时，不应把它诊断为模型产生了 NaN 或把容差调整当成处置。

## 图边界的字节载体

`uint8` 在这里表示原始量化编码的载体，不表示把模型改成整数算术。外层保存字节，opaque 内用 `view(dtype)` 解释同一存储；使用 `.to(dtype)` 做数值转换会改变编码语义。

完整的 scale 布局 helper 如下：`output` 是权重输出维，`k` 是输入维，每组 K 的长度为 32，因此 scale 元素数为 `output × k / 32`；`k / 64 × 2` 只是把同样数量的字节组织为 Native 需要的形状，并未重新计算 scale。

```python
def logical_mx_scale(scale, output, k):
    """Keep the actual E8M0 bytes: one exponent for each group of 32 K."""
    if k % 64 or scale.numel() != output * k // 32 or scale.element_size() != 1:
        raise ValueError("MXFP8 Prolog requires [O, K/32] E8M0 scales and K divisible by 64")
    return scale.view(torch.uint8).reshape(output, k // 64, 2).contiguous()
```

不可变权重 scale 还有对象身份约束。每轮重新调用 `view()` 可得到共享存储但身份不同的 Tensor；若上游预处理缓存按 Tensor identity 建键，仍会重复准备。以下 helper 缓存视图，并持有输入张量来避免身份复用：

```python
@lru_cache(maxsize=256)
def _e8m0_view(scale):
    """Reuse a zero-copy view of an immutable byte buffer for Native caching.

    The upstream prepared-weight cache keys on Tensor identity. Keeping these
    views stable avoids preparing the same weights again during graph capture.
    The bounded cache retains its source tensors, preventing identity reuse.
    """
    if scale.dtype != torch.uint8:
        raise ValueError("MLA graph inputs must carry E8M0 scales as uint8 bytes")
    return scale.view(torch.float8_e8m0fnu)
```

它只适合加载后不再改变的 scale buffer。更换权重或量化方案时必须重新准备相匹配的适配器；不能让该缓存跨越不同内容的 buffer 生命周期。

## 完整 opaque 实现单元

以下 `_decode_impl` 是现有函数原文。它依赖模块中的 `torch`、`F`、`_e8m0_view`，以及安装好的 Native Prolog、`cann_ops_transformer` 接口；不是独立运行脚本。它把 E8M0/FP8 view 留在 opaque 实现内，最终返回 BF16 输出：

```python
def _decode_impl(x, weights, scales, wkb, gamma_qa, gamma_kva, cache, slots,
                 kv_scale, block_table, seqlens, cu_q, metadata, mask, q_len, softmax_scale):
    import torch_npu
    from ops.quant_mla_prolog import quant_mla_prolog_op

    queries, descales = [], []
    fp8_cache = cache.view(torch.float8_e4m3fn)
    e8m0 = torch.float8_e8m0fnu
    native_scales = [_e8m0_view(scale) for scale in scales]
    slots = slots.reshape(-1).to(torch.int64)
    for start in range(0, x.shape[0], 128):
        chunk = x[start:start + 128].contiguous()
        indices = slots[start:start + 128].contiguous()
        count = chunk.shape[0]
        native = 8 if count <= 8 else 32 if count <= 32 else 64 if count <= 64 else 128
        if native != count:
            chunk = F.pad(chunk, (0, 0, 0, native - count))
            indices = F.pad(indices, (0, native - count), value=-1)
        quantized, scale_x = torch_npu.npu_dynamic_mx_quant(chunk, dst_type=torch.float8_e4m3fn)
        scale_x = scale_x.view(torch.uint8).reshape(native, x.shape[-1] // 64, 2).view(e8m0)
        q, descale_q = quant_mla_prolog_op(
            quantized, *weights, wkb, scale_x, *native_scales,
            gamma_qa, gamma_kva, fp8_cache, indices, kv_scale, 1e-6,
        )
        # Concatenate bytes because float8 cat is not required from the backend.
        queries.append(q[:count].view(torch.uint8))
        descales.append(descale_q[:count])
    q = torch.cat(queries, dim=0).view(torch.float8_e4m3fn)
    descale_q = torch.cat(descales, dim=0)
    blocks, block_size, _, width = cache.shape
    physical = fp8_cache.view(blocks, 1, width // 32, block_size, 32)
    output, _ = torch.ops.cann_ops_transformer.quant_flash_mla_with_kvcache(
        q, physical, descale_q, kv_scale, block_table, seqlens, 1,
        cu_seqlens_q=cu_q, metadata=metadata,
        attn_mask=mask if q_len > 1 else None,
        softmax_scale=softmax_scale, mask_mode=3 if q_len > 1 else 0,
        max_seqlen_q=q_len, head_dim_v=512,
        layout_q="TND", layout_kv="PA_NZ", layout_out="TND",
    )
    return output
```

处理时应成套检查：`QuantMLADecode` 注册的三个 `s_*` buffer 仍为 uint8；传给外层 custom op 的 cache 仍为 uint8；只有 `_decode_impl` 内部恢复 E8M0 scale 与 E4M3 cache。不能仅在调用点临时转换一个参数。

## mutation 与 fake 契约

cache 更新必须在 schema 中真实声明为可变。现有注册单元如下，`Tensor(a!) cache` 不可删除：

```python
_LIBRARY = torch.library.Library("kimi_k3_mla", "FRAGMENT")
_LIBRARY.define(
    "w8a8c8_decode(Tensor x, Tensor[] weights, Tensor[] scales, Tensor wkb, "
    "Tensor gamma_qa, Tensor gamma_kva, Tensor(a!) cache, Tensor slots, "
    "Tensor kv_scale, Tensor block_table, Tensor seqlens, Tensor cu_q, "
    "Tensor metadata, Tensor? mask, int q_len, float softmax_scale) -> Tensor"
)
_LIBRARY.impl("w8a8c8_decode", _decode_impl, "PrivateUse1")
```

对应 fake 实现只负责输出元信息；它不能替代真实 cache 更新行为：

```python
@torch.library.register_fake("kimi_k3_mla::w8a8c8_decode")
def _decode_meta(x, weights, scales, wkb, gamma_qa, gamma_kva, cache, slots,
                 kv_scale, block_table, seqlens, cu_q, metadata, mask, q_len, softmax_scale):
    return x.new_empty((x.shape[0], wkb.shape[0], 512), dtype=torch.bfloat16)
```

若把 cache 假装只读来让高阶节点消失，会破坏图对副作用的理解。若修改 fake 的返回 dtype 或 shape，则须与 Native 实际输出重新对齐，而不是以能编译为标准。

## 设计决策与排查顺序

1. 保留现有模型权重、scale 编码和 cache 语义，只调整图边界的载体类型，避免把编译兼容与重新量化混成一项改动。
2. 图内不额外生成 E8M0 视图；视图生成发生在 opaque 内部，且不可变 scale 复用身份。
3. 保持 cache mutation 声明以及 BF16 输出，把易触发展开的 dtype 细节封装在实现侧；不能修改已安装框架的过滤规则来掩盖不匹配。
4. 先核验字节、布局、storage 和 identity，再执行 AOT 与实际展开 pass，最后进入 NPU capture/replay。任何一层失败均保留现场，不跳到整网性能测试。

## 验证信号

本轮已核对实际 schema、fake 实现、字节载体和视图缓存函数。现有回归定义会构造真实适配器与外层 schema，CPU surrogate 中检查 `scales` 为 uint8、AOT 后确实存在高阶节点、执行 `decompose_auto_functionalized` 后节点消失，再做两次不同 slot/value 的写入，检查历史值与视图身份复用。这些断言界定了测试要证明的范围；本轮未执行这些模型测试，也没有取得目标 NPU 的修后结果。

## 部署验收与未决项

- 在目标版本中核对 scale 的原始字节、`untyped_storage().data_ptr()`、shape 和重复使用时的视图身份，确认未发生数值 cast 或额外复制。
- 用实际 AOT 后端及与失败现场相同的展开 pass 检查图；`aot_eager` smoke 单独通过不能替代这一步。
- 对 Native 直连、opaque 接口、完整模型依次验收。至少两轮改变输入值、slot 与 KV 长度，比较 eager 输出、被更新 cache 字节及未写入历史位置。
- 若 CPU surrogate 通过而 NPU 失败，优先核对目标 torch_npu/算子 schema、FP8 支持与图生命周期，不把 CPU 通过写成目标环境通过。

## 坏实践、回退与失效边界

禁止将 `view` 换成数值转换来适配 dtype，禁止删除 mutation 声明，禁止仅依赖 fake 输出或一次固定输入 replay，禁止用新权重或新的误差容差替换原验收问题。

回退应恢复整套匹配的适配器、buffer 准备与编译缓存；若使用其他 MLA 路线，还要恢复对应 cache 布局与 metadata，不能只改 custom op 名称。当前最优先未决项是目标 PyTorch 2.10/torch_npu 环境的实际展开与 capture/replay 验收；跨版本、跨平台迁移仍未验证。
