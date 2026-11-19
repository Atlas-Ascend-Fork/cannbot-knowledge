---
type: Guide
title: torch_npu 发布版 Inductor lowering 白名单回退与 overload 覆写机制（lowering_op_list 的实际作用面）
description: 记录发布 pin 扁平 lowering.py 的"白名单外全部回退"机制：GENERATE_LIST/foreach 豁免/LOWERING_OVERLOAD_OP 先删后注册、make_reduction 的 kept_idx/reduced_idx 簿记及 kernel_analysis 消费、embedding 参数硬编码坑，与主线反转为显式 391 项 FALLBACK_LIST + allfallback 逃生门的对照。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/lowering.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/lowering_op_list.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/kernel_analysis.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_fx.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_fallback_list.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_override_list.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/lowering_common.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
created_at: '2026-11-12T08:00:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版 Inductor lowering 白名单回退与 overload 覆写机制

## 固定版本与适用范围

发布 pin（f3ecfe4a）default（Triton）分支：`_inductor/__init__.py:68-69` 把 torch 全局 `inductor_lowering.make_reduction/make_fallback` 换成本仓实现，`:106-108` 调 `_register_npu_inductor_fallbacks()`，作用面是 `lowering_op_list.py` 的三张表加运行时重注册。本卡覆盖发布版接线卡中"降级注册"一行的事实面；主线对照见后节。`lowerings` 字典内容随 vendored torch 版本变化，两 pin 的清单不可互推。纯静态阅读；draft、platforms 为空。

## 发布版机制表（实际门槛 → 动作 → 失败/版本边界）

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| op 已在 torch `decompositions` 且未 `override_decomp` | `npu_make_fallback`（`lowering.py:55-74`）直接 `RuntimeError: both a fallback and a decomp for same op` | packet 逐 overload 展开；非 packet/overload/HO 类型同样 RuntimeError（`:74`）；注册时加 `add_needs_realized_inputs`，可选 layout constraint |
| `make_fallback = npu_make_fallback`（`:76`）且 `__init__.py:69` 替换 torch 模块属性 | 上游后续经 `lowering.make_fallback` 的注册流改走本仓版本 | 属性替换只影响该模块属性；已持有旧函数引用的调用方不受影响（一般限制，静态记录） |
| 扫描 torch `lowerings`（`:156-168`）：op **不在** decompositions、**不在** GENERATE_LIST 展开集、且 str(op) 不含 GENERATE_LIST2 子串 | `make_fallback(op)` 注册 extern/operator fallback（经 `fallback_handler`，`:63-65`；实际 NPU ACLNN/acl_op/其他派发在 handler 下游，本链未证明），并 `FALLBACK_LIST.append(op)`（`:168`；表在 `lowering_op_list.py:88` 空表起步，是运行时记录） | GENERATE_LIST（`lowering_op_list.py:9-82`，约 72 项，`aten.where` 在 `:24/:50` 重复出现）是保留 torch 代码生成的白名单：elementwise/比较/选择/形状族 + `npu_dtype_cast/_npu_dtype_cast` + `triton_kernel_wrapper_mutation` + `invoke_subgraph`；GENERATE_LIST2 仅 `"foreach"`（`:84-86`）子串豁免。静态结构注记：迭代 `lowerings` 的同时 `register_lowering` 就地写同键不增字典长度；若出现 packet 键且其 overload 不在表中，字典增长会触发 RuntimeError——本卡只记录结构，不判断 vendored torch 中是否实际发生 |
| LOWERING_OVERLOAD_OP（`:92-111`，16 项：cumsum/mean/max/min/amin/amax/argmax/argmin/var_mean/var/embedding/split/split_with_sizes/nll_loss_forward/gather/cat） | 先 `del lowerings[op]`（`:170-172`），再由 `_register_npu_inductor_fallbacks` 下半段的自定义实现顶替（注释 `:90-91`） | `split/split_with_sizes` 删除后本文件未见重注册，其处理预期来自 decompositions 或其他 pass，未在本链内核对；`gather/nll_loss_forward` 最终走 `:318-320` 显式 `make_fallback` |
| 自定义 re-registration（`:180-316`） | reductions 经本仓 `make_reduction`（`:89-131`）；mean 对 fp16/bf16 升 fp32 计算（`:217-218`）；cumsum 对 int/bool 且未指定 dtype 时改 int32、0 维走 to_dtype 复制（`:227-236`）；var/var_mean 分母 `sympy.Max(denom-correction, 0)`（`:261`）；cat 按提升 dtype 统一后走 `ir.ConcatKernel`（`:305-316`） | `make_reduction` 用 `object.__setattr__` 给 Reduction 节点写 `kept_idx/reduced_idx`（`:117-126`）再 realize；消费端 `codegen/kernel_analysis.py:205-206` 缺 `reduced_idx` 即 RuntimeError，`:266-285` 据此推 low_dims 与归约维，衔接[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)记录的 `triton_config_npu_index` 从 inductor_meta 读 `split_axis/low_dims` |
| `aten.embedding`（`:300-303`） | `fallback_handler(aten.embedding.default)(weight, indices, padding_idx=-1, scale_grad_by_freq=False, sparse=False)` | **硬编码坑**：函数签名收到的 `padding_idx/scale_grad_by_freq/sparse` 实参不透传，固定 -1/False/False；带非默认 embedding 参数的图与 eager 行为可能不同，使用前按实际图核对 |
| 尾部显式回退（`:318-320`） | `make_fallback(aten._log_softmax/gather/nll_loss_forward)` | 与 LOWERING_OVERLOAD_OP 中 gather/nll_loss_forward 的删除配合，二者最终为 extern fallback |

`FALLBACK_LIST` 在 release 是**输出**：只被 `lowering_fx.py:62` 导入（dump_fx_graph 路径）消费，不参与回退决策；mlir 插件路径另有 `ascend_npu_ir/ascend_npu_ir/config.py:193-225` 固定 29 项的 `FALLBACK_LIST`（头 7 项为 mm/bmm/addmm/convolution/convolution_backward/_adaptive_avg_pool2d/max_pool2d_with_indices；尾部 `:201-224` 另含 max_pool2d_with_indices_backward、avg_pool2d(+backward)、lookup_seed/random/device_put、upsample_nearest2d(+backward)、embedding、constant_pad_nd、abs/max/amax/amin、slice_scatter/select_scatter、gather/scatter、`npu._npu_dropout`、empty/index/copy_，及 cat/permute 两个注释项），由 `npu/npu_lowering.py:27` 遍历全表消费（rg 锚），是另一张表，不与本文混写。

## 主线对照（机制反转，静态证据）

- 主线回退循环（主线 `lowering.py:389-392`）只对 **在** `FALLBACK_LIST` 中且不在 decompositions 的 op 做 `make_fallback`：`FALLBACK_LIST = NPU_EXTRA_FALLBACK_LIST`（`lowering_fallback_list.py:438`），显式枚举 391 项（`:36-436`，静态脚本计数）。就本循环/本表而言，发布版是"白名单外默认回退"，主线是"黑名单内才回退"；该反转不外推为整个后端规则：同一函数还先按 env 逗号列表追加 `FALLBACK_LIST` 并从 `LOWERING_OVERRIDE_OP` 移除（`:347-358`）、删除 `LOWERING_OVERRIDE_OP` 既有注册（`:360-366`）、重建自定义 lowering（`:368+`）并调用 `_add_fallback_ops_for_torchgen()`（`:398`）——override 与 torchgen 两条路径的 fallback 在回退循环之外仍在。
- 逃生门：主线 `__init__.py:293-296` 当 `enable_full_lowering_fallback`（config `NPU_INDUCTOR_FALLBACK_LIST`，见[配置解析卡](torch_npu_inductor_config_parsing.md)）`strip() == "allfallback"` 时改走 `_enable_full_lowering_fallback()`（主线 `lowering.py:1350-1362`，经 `enable_full_lowering_fallback_common`，排除 `TritonKernelWrapperMutation/Functional` 两个 HOP），近似复现发布版默认行为；否则 `_register_npu_inductor_fallbacks()`（`:296`）。env 逗号列表还可在 `:347-358` 逐项 resolve 追加 FALLBACK_LIST 并从 LOWERING_OVERRIDE_OP 移除。
- `npu_make_fallback` 两 pin 逐字等价（release `:55-76` vs 主线 `:107-128`，diff 实查仅差行尾 `# noqa: F811`）；release `_init_set`（`:140-146`）与主线 `lowering_common.py:71-77` `add_overload` 逐行等价。
- 主线 LOWERING_OVERRIDE_OP 扩充（`lowering_override_list.py` 48 行全文）：新增 mm/bmm/addmm/pow/convert_element_type/fractional_max_pool3d/flex_attention(+backward) 等，另有 INDIRECT_MEM_OVERRIDE_LIST 11 项（`:33-45`）仅在 `inductor_indirect_memory_mode == "simt_template"` 时并入（`:47-48`）——与[矩阵乘 kernel 家族卡](torch_npu_inductor_triton_matmul_kernel_family.md)的 per-op 注册相衔接；发布版 GENERATE_LIST 不含 mm 家族，torch 侧 mm/bmm/addmm lowering（如在 vendored torch 的 lowerings 中存在）按白名单循环整体改为 extern fallback，这与[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)记录的"发布版无 per-op mm 注册"负证据一致。
- 主线 `make_reduction`（主线 `:152-197`）新增 `strict_reduction` 参数与 `_SUPPORTS_STRICT_REDUCTION` 开关，且非 fx 路径不再写 `kept_idx/reduced_idx`：该簿记仅存于 fx dump 路径，由 `lowering_fx.py` `_make_reduction_inner`（`:850-905`）承担，`kept_idx/reduced_idx` 构造在 `:861-870`（主线 `lowering.py:378-381` 仅在 `npu_config.dump_fx_graph` 为真时经 `_register_npu_inductor_fallbacks_fx` 接入）；`lowering_fx.py:917-926` 实为 `clone()` 函数体，非簿记所在。

## 失效边界与静态口径

- 本卡只覆盖 release default 分支与两 pin 结构对照；未运行任何编译/回退/精度实验，不构成对回退后下游派发 kernel（ACLNN/acl_op 等，实际派发路径未在本链证明）数值或性能的承诺。
- 白名单循环的字典结构注记是静态观察，实际是否触发取决于 vendored torch 的 lowerings 键型。
- 主线 triton_experimental 隔离树有一套同形 GENERATE_LIST/回退机制，见[实验 Triton 激活与 lowering 路由卡](torch_npu_experimental_triton_activation_and_lowering_routes.md)，不与本文混写。
- 与[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（`:68-69/:106-108` 接线行）和[发布版分解表面卡](torch_npu_release_flat_inductor_decomposition_surfaces.md)（decompositions 侧配合）边界互链。
