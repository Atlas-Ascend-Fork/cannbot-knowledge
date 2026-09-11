---
type: Runbook
title: 自定义算子接图模式的 lowering 正确性：converter 按 GE IR 原型对齐 + meta 函数显式声明输出 dtype
description: 自定义算子接图模式的 lowering 正确性：converter 按 GE IR 原型对齐 + meta 函数显式声明输出 dtype。带自定义 AscendC 算子的模型在 eager 下正常、一入图（ge_graph / torch 图捕获）就报错或结果错。根子几乎都在自定义算子的图抽象层与真实 kernel 不一致：eager 走真实 kernel（掩盖了 bug），图捕获走算子的 meta 函数（类型/shape 推导）+ converter（lower 成 GE 节点）——这两层一旦与真实算子原型/输出不对齐，只有入图才暴露。给自定义算子接图模式时，把这两层核对齐。
tags:
- task.debugging
- topic.graph_execution
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/412
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/245
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/482
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/2113
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 自定义算子接图模式的 lowering 正确性：converter 按 GE IR 原型对齐 + meta 函数显式声明输出 dtype

## 适用场景

带自定义 [AscendC](../../concepts/frameworks/ascendc.md) 算子的模型在 **eager 下正常、一入图（ge_graph / torch 图捕获）就报错或结果错**。根子几乎都在自定义算子的**图抽象层与真实 kernel 不一致**：eager 走真实 kernel（掩盖了 bug），图捕获走算子的 **meta 函数（类型/shape 推导）+ converter（lower 成 GE 节点）**——这两层一旦与真实算子原型/输出不对齐，只有入图才暴露。给自定义算子接图模式时，把这两层核对齐。

## 坑 1：ATEN schema 与 GE IR / aclnn 原型不对等 → "算子 aten 和 geir 不对等"

torchair 把 fx 图 lower 成 GE IR 时按 converter 定义拼算子输入/attr/输出，**converter 与真实算子（GE IR/aclnn）原型不是自动对齐的**。图模式调测报"有些算子 aten 和 geir 不对等"，三类不对等：

| 不对等类型 | 例 | 修法（converter 按 GE IR 原型对齐） |
|---|---|---|
| **可空输入未占位** | `RmsNormDynamicQuant` 的 `smooth_scale2` 是可空第二输入，旧 converter 只给单个 `smooth_scale`、输出只声明 2 个 | 拆 `smooth_scale1`/`smooth_scale2`（后者传 `None` 占位空指针）、输出扩到 4 个只取需要的 |
| **attr 类型 str↔int** | `InplacePartialRotaryMul` 的 `rotary_mode` torch schema 是 str、aclnn/GE IR 是 int | converter 里用 int 编码（如 `1`）按位置传，不透传 schema 的 str |
| **原型参数数目不对应** | `Compressor` schema 与 IR 原型参数数目不匹配、缺 converter | 按 GE IR 完整位置参数展开、补派生参数 |

同类：converter 的 `inputs` dict 键排列顺序须与算子 GE IR 输入顺序一致。配套——**算子 proto 须补 InferShape/InferDataType**：图模式编译需算子能对每个输出推 shape/dtype（如 `RmsNormDynamicQuant` 补 `InferShape4RmsNormDynamicQuant`/`InferDtype4RmsNormDynamicQuant` + `IMPL_OP(...).InferShape(...).InferDataType(...)`，声明 int8/float 输出）。

```python
# 手写 fx→ge converter，按 GE IR 原型对齐输入占位/attr 编码/输出数目
out = torchair.ge.custom_op("RmsNormDynamicQuant",
    inputs={"x": x, "gamma": gamma, "smooth_scale1": smooth_scale, "smooth_scale2": None, "beta": beta},
    attrs={"epsilon": attr.Float(epsilon)}, outputs=['y1','y2','scale1','scale2'])
return [out[0], out[2]]
```

## 坑 2：改 dtype 的算子 meta 函数用 `empty_like(x)` → 输出 dtype 隐式继承输入

- **信号**：动态量化类算子（输出 dtype ≠ 输入，典型输出 int8）**eager 正常返回 int8，入图后返回 dtype 变成与输入 x 一致（bf16/fp16）**，下游拿到错误 dtype。
- **根因**：meta/fake 函数用 `at::empty_like(x)` 构造输出，`empty_like` 默认**继承 x 的 dtype**。eager 实际跑 kernel 返回真 int8 掩盖了 bug；图捕获只消费 meta 函数推导的 dtype，故只有入图暴露。
- **修法**（1 行）：显式指定输出 dtype：
  ```cpp
  - at::Tensor y_out = at::empty_like(x);
    auto options = x.options();
  + at::Tensor y_out = at::empty_like(x, options.dtype(at::kChar));   // at::kChar = int8
  ```
- **可迁移原则**：凡输出 dtype ≠ 输入 dtype 的自定义 NPU 算子（尤其量化：dynamic-quant→int8、cast、pack 类），其 meta/fake 函数**不能用 `empty_like(input)` 隐式继承输入 dtype**，必须显式声明输出 dtype（`options.dtype(...)` / `at::empty(..., dtype)`）；meta 函数是图捕获期唯一的类型推导来源，其输出 dtype 须与真实 kernel 一致。验证须覆盖图模式、不能只测 eager。

## 坑 3：自定义算子根本没有 Meta 实现 → torch.compile 抓不到它 → 进不了 aclgraph（且 meta 须符号形状安全）

坑 1、坑 2 是「已经能入图、但 lower 结果不对」；本坑更靠前——**算子连图都进不去**。这条出现在另一条图后端上：**aclgraph**（昇腾侧类 CUDA-graph 的图重放，靠 `torch.compile`（torch 2.x）先把前向捕成 fx graph，只有留在 fx graph 里的算子才可能被插进 aclgraph）。

- **信号**：自定义 C++ NPU 算子（如 rotary_embedding、get_masked_input_and_mask 一类）**默认没有 "Meta" dispatch 实现**，`torch.compile` 在 symbolic tracing / shape 推断阶段处理不了它 → 该算子被 graph break 或直接抓不进 fx graph → 永远进不了 aclgraph（不报错、只是静默地没被图捕获）。
- **根因**：`torch.compile` 的 fx 捕获走 **fake/meta tensor**——它不跑真 kernel，只靠算子的 Meta 实现从输入 shape/dtype 推出输出 shape/dtype。自定义算子若没注册 Meta impl，tracing 期无从推导输出，只能退化为 eager 调用、留在图外。**这是「自定义算子要进 aclgraph 图模式」这一类问题的通用前置条件**，不限于某两个算子。
- **修法**：给每个要进 aclgraph 的自定义算子注册一个 **"Meta" dispatch key 的 fake 实现**——只用输入 shape/dtype/参数推输出 shape/dtype、返回空张量，**不做真实运算、不搬数据、不分配 device 内存**。两条等价注册路径可任选：
  - **C++ 路径**：写 `*_meta` 函数返回 `at::empty_symint(...)`，用 `TORCH_LIBRARY_IMPL_EXPAND(_C, Meta, ops)` 注册。
    ```cpp
    std::tuple<at::Tensor, at::Tensor> rotary_embedding_meta(
        at::Tensor &positions, at::Tensor &query, at::Tensor &key,
        int64_t head_size, at::Tensor &cos_sin_cache, bool is_neox) {
      auto num_tokens = positions.sym_numel();               // 符号形状安全，非具体 numel
      auto query_hidden_size = query.sym_numel() / num_tokens;
      auto num_heads = query_hidden_size / head_size;
      at::Tensor query_dst = at::empty_symint({num_tokens, num_heads, head_size}, query.options());
      // ... key_dst 同理
      return {query_dst, key_dst};
    }
    TORCH_LIBRARY_IMPL_EXPAND(_C, Meta, ops) {
      ops.impl("rotary_embedding", &rotary_embedding_meta);
      ops.impl("get_masked_input_and_mask", &get_masked_input_and_mask_meta);
    }
    ```
  - **Python 路径**：写同签名 Python 函数返回 `torch.empty_like(...)`，用**带去重**的 `register_meta_if_necessary(ns, op_name, fn)` 注册（内部先 `torch._C._dispatch_get_registrations_for_dispatch_key("Meta")` 查已注册则跳过，再 `lib.impl(op_name, fn, "Meta")`），避免与 C++ meta 重复注册。
- **新边界（符号形状安全）**：meta 实现**必须避免会破坏 symbolic tracing 的具体 numel 操作**——用 `sym_numel` + `at::empty_symint`（C++）/ 符号安全构造（Python），不要在 meta 里对 tensor 取具体 `numel()` 再做算术。一旦用了具体 numel，动态 shape 下 symbolic tracing 会被打断，算子又掉出图。这是相对坑 1/坑 2（讲输出原型/dtype 对齐）之外、专属 torch.compile fx 捕获路径的约束。
- **注册入口时机**：meta 注册须在自定义算子库 import 之后生效——参考实现把 `import ..meta_registration` 放进 `enable_custom_op()`（并固定 import 顺序），让 meta 注册随自定义算子启用而挂上，否则算子已注册、meta 没挂，一样抓不进图。
- **验证手段**：不能只看跑通，要断言算子确实留在被捕获的 fx graph 内——把算子塞进一个小模型，`torch.compile(model, backend=custom_op_checking_backend)`，在 backend 里对 `str(gm.graph)` 断言目标算子字符串（如 `"_C.rotary_embedding" in graph`）在图内，再用 `torch.npu.NPUGraph()` capture + replay 校验数值。这套断言是判断「算子到底进没进图」的直接手段，比只看端到端结果可靠。
- **可迁移原则**：给自定义 NPU 算子接 **torch.compile → aclgraph** 路径时，「注册符号形状安全的 Meta 实现」是通用前置步骤；缺 Meta 只会静默 graph break，不报错。与坑 1/坑 2 的关系：Meta impl 首先让算子**能进图**，坑 1（converter 原型对齐）、坑 2（meta 输出 dtype 显式声明）再保证**进图后 lower 结果对**——三者按此先后串起，构成自定义算子入图的完整正确性链。哪种图后端（aclgraph / torchair-GE / eager）吃哪类自定义算子见 [custom-op-framework-graph-backend-compat](../../optimizations/experience/rules/custom_op_framework_graph_backend_compat.md)。

## 参考实现及其约束

参考实现（坑 1/坑 2，torchair GE-graph）：DeepSeek-V4 ge_graph bringup 的三个 torchair converter（`npu_rms_norm_dynamic_quant` / `npu_inplace_partial_rotary_mul` / `npu_compressor`）+ `rms_norm_dynamic_quant_proto.cpp` 的 InferShape/InferDataType；`npu_rms_norm_dynamic_quant` meta 函数的 int8 dtype 修复。三类不对等分类取自作者描述且与 diff 修法互证；InferShape/InferDataType 输出取自 proto 实现。范围限本仓 torchair ge_graph 下自定义 AscendC 算子的 converter/meta，不外推整栈；"自定义算子入图的 converter 须按 GE IR 原型对齐、meta 须显式声明输出 dtype"是可迁移的 lowering 正确性规则。

参考实现（坑 3，torch.compile → aclgraph）：vllm-ascend 的 `csrc/torch_binding_meta.cpp`（`*_meta` 函数 + `TORCH_LIBRARY_IMPL_EXPAND(_C, Meta, ops)` 注册 `rotary_embedding` / `get_masked_input_and_mask`）、`vllm_ascend/meta_registration.py`（`register_meta_if_necessary` 去重 + `lib.impl(..., "Meta")` 的 Python 路径）、`vllm_ascend/utils.py::enable_custom_op()` 里 import `meta_registration` 的注册时机。约束：这是 vllm-ascend 推理路径下、torch 2.x `torch.compile` fx 捕获 → aclgraph 这条后端的做法；C++/Python 两路等价、Python 路径带去重以免与 C++ meta 重复注册。合并态 diff 只证「注册 Meta 使算子可被捕获进 aclgraph」的机制，未给 host overhead / 时延 before→after 数字，故只述机制不述收益。「给要进 aclgraph 的自定义算子注册符号形状安全的 Meta 实现」是可迁移前置步骤。

哪种图后端吃哪类自定义算子见 [custom-op-framework-graph-backend-compat](../../optimizations/experience/rules/custom_op_framework_graph_backend_compat.md)。

## Evidence

- diff 事实（@15d78968797f）：三个 converter 按 GE IR 对齐（`smooth_scale2:None` 占位、`rotary_mode` int 编码、Compressor 全位置展开）+ proto 补 InferShape/InferDataType；三类根因取自作者描述、与 diff 互证。溯源下探 [cann-recipes-infer-pr-412-deepseek-v4-ge-graph](https://gitcode.com/cann/cann-recipes-infer/merge_requests/412)
- diff 事实 + 维护者确认（@3a405a81033b）：meta 函数 `empty_like(x)` → `empty_like(x, options.dtype(at::kChar))`；eager 正常/入图 dtype 错的症状 + 根因由维护者在 issue 确认。溯源下探 [cann-recipes-infer-issue-245-bug-report-rms-norm-dynamic-quant-tensor-dtype](https://gitcode.com/cann/cann-recipes-infer/issues/245) · [cann-recipes-infer-pr-482-bugfix-npu-rms-norm-dynamic-quant-meta-tensor](https://gitcode.com/cann/cann-recipes-infer/merge_requests/482)
- 坑 3 diff 事实（合并态 @c0f0b708137838c1387b4f98eeaeda383d06f0d9）：新增 `csrc/torch_binding_meta.cpp`（`TORCH_LIBRARY_IMPL_EXPAND(_C, Meta)` 注册两个 `*_meta`）、`vllm_ascend/meta_registration.py`（`register_meta_if_necessary` 去重 + `lib.impl(..., "Meta")`）、`vllm_ascend/utils.py` 在 `enable_custom_op` 里 import `meta_registration`，均与「注册 Meta 使自定义算子可被 torch.compile 捕获进 aclgraph」对上；「符号形状安全」由 commit `475db0df3b6a`（subject: remove numel operation to support symbolic tracing）+ C++ 用 `sym_numel`/`empty_symint` 佐证；`custom_op_checking_backend` 断言算子留在 fx graph 内为 in-diff 测试。收益数字缺失。溯源下探 [vllm-ascend-pr-2113-core-support-capture-custom-ops-into-aclgraph](https://github.com/vllm-project/vllm-ascend/pull/2113)