---
type: Guide
title: 自定义算子入图：Schema、Meta、函数化与 Converter 交付
description: 围绕已有 Eager 算子明确 npugraph_ex 与 GE 的图适配步骤和验收证据，避免把可执行实现误当作入图完成。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/op_plugin_adapt_torchair.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/custom_op_zero_delivery.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_2/models/custom_op_loader.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/in_place_op_cases.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/non_in_place_op_cases.md
  role: supporting
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/inplace_op_graph_entry.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/inplace_op_graph_entry_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/feature/原地操作算子入图指导.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/in_place_op_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/non_in_place_op_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/op_plugin_adapt_torchair.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/overview.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 自定义算子的图模式接入

## 输入与目标

输入为已能在同一软件环境下 Eager 运行的自定义算子、准确 Schema、目标图后端及模型输入域。目标是保留算子语义、输出结构和原地行为，并让所选后端实际捕获和执行。

## 接入顺序

1. 固定 `torch.ops` 的命名空间、名称、overload、可选参数、别名和 mutation。先验证 Eager 计算与参考结果一致。
2. 提供 Meta/符号推导，覆盖输出 shape、dtype 及内存关系；只返回数值上看似正确的样例 Tensor 不能证明动态输入推导正确。
3. 若是 In-place 算子，确保满足该版本自动函数化的 Schema 前提，或补齐所需适配，并验证输入修改与输出别名语义。非原地算子无需人为增加原地转换。
4. npugraph_ex 复用 PyTorch 图前端交付件，再核对捕获安全性。GE 原生适配需要准确的 Ascend Converter；固定主线另提供零交付件路径：Schema-based 算子具备 Schema、PrivateUse1 实现和 Meta 后可由 TorchAir 自动生成适配代码，无须手写 Converter 或额外交付 OPP 包。已有原生 Converter/GE IR 时优先使用已有实现；需要 SuperKernel、分核或原生融合等能力时选择原生适配。此主线能力不据此推定在 26.0.0 发布组合中存在。
5. 插件化适配可把 Meta 与 Converter 放在独立 Python 模块，于模型执行前加载；这条路径的前提是 Eager 实现已经存在。

## Recipes 中的命名空间与交付件

固定 Recipes 的 custom_ops 包先加载自定义 .so，再把 torch.ops.custom 的公开对象挂到 torch_npu。因此出现 `torch_npu.npu_*` 调用不证明它属于所安装 TorchNPU/OpPlugin 的标准接口。`npu_gather_selection_kv_cache`、`npu_swiglu_clip_quant`、`npu_dequant_swiglu_clamp_quant`、`npu_moe_init_routing_group_quant` 在该快照的 `TORCH_LIBRARY(custom, m)` 注册；它们的接口契约见下方独立卡，完整 Kernel 分析仍需按相应来源和 producer 单独处理，不从名字相近的标准算子推断。

GLM5.2 的 loader 还区分：Eager/npugraph_ex 加载实际 PrivateUse1 Kernel，GE 路线另加载 Converter；部分加载函数在交付件缺失时返回 False 或静默跳过。函数返回、Python 属性存在、Schema 存在和可执行实现必须分别核对，不能把 import 未报错视为交付成功。这是固定模型实现的例子，不是所有版本的自动加载协议。

## 验收与失败定界

分别检查 Eager、Meta、FX 节点、GE 转换或捕获，以及实际输出。单独覆盖空输入、动态形状和原地修改等真实需要的边界。Meta 失败先检查符号关系；原生适配缺少 Converter 时按准确 overload 补齐，零交付件路径则先确认前置交付件和该版本的自动适配限制；只有图执行失败时再检查底层执行器。

失败时保留可用的 Eager 路线和输入证据；不能把 graph break 当作整图接入成功。本卡蒸馏固定主线的接入契约，不包含完整算子源码生产或真机验证。

## 版本入口

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 已有 Recipes 接口契约

以下独立卡已补齐文档、Schema 和包装层契约；它们仍属于 Recipes 自定义交付件，完整 Device Kernel/Host/Tiling 的生产与设备验证分别留项。

- [A3 Gather 选择缓存与原地状态](../../../apis/recipes_custom_ops/npu_gather_selection_kv_cache.md)
- [A3 SwiGLU 分组削波与有效尾部](../../../apis/recipes_custom_ops/npu_swiglu_clip_quant.md)
- [A3 反量化与变体门控](../../../apis/recipes_custom_ops/npu_dequant_swiglu_clamp_quant.md)
- [950 PerGroup FP8 路由](../../../apis/recipes_custom_ops/npu_moe_init_routing_group_quant.md)

## 发布版失败案例入口

固定发布子模块的 A2/A3 案例将 unsupported operator/部分 dispatch TLS 断言、返回 CPU Tensor 的 Meta、缺少函数化的 mutation 及缺少原生 Converter 分开处理。这些是需验证的原因线索，不能用一个通用异常字符串唯一判定根因；也不能把发布版案例范围扩展到本卡主线的其他产品。

- [按前端、Meta、函数化和后端阶段检查](../../optimization/torchair/torchair_graph_failure_triage.md)
- [Meta/GE 输出规格与内存不足](../../optimization/torchair/ge_shape_dtype_failure_diagnosis.md)

## 主线案例的自动函数化与原生映射前提

固定主线 In-place 案例要求 Schema 明确写别名 Tensor(a!)，Tensor 参数在基本类型参数之前，并且不返回被修改输入本身；独立新输出仍可返回。在此约定下可使用 PyTorch 2.6+ 的自动函数化，无需再手写同一转换。其语义包括先复制被修改输入、在副本上调用，再重定向后续使用；是否消除拷贝是后续优化问题，不能靠修改 Schema 隐藏 mutation。

原生 Ascend C 工程中，被修改输入需有同名输出；PyTorch 只返回新增输出时，Converter 必须选择正确的 GE 输出索引，不能把回写输入误当返回值。非原地与原地案例都要求输入顺序、数量和类型与原型一致；Optional Tensor、Tensor[] 和普通属性分别映射，不可把列表长度写死。

自动映射到原生 GE IR 还依赖大驼峰名称及输入输出顺序/数量一致，Scalar 类型入参等情况可能需要手写 Converter；仅在输入输出可对应时才采用来源说明的自动 InferShape/InferDataType，不能一概删除工程默认推导。Kernel 直调没有天然原生 GE IR，但主线[零交付件回调](../../optimization/torchair/ge_custom_op_callback_boundaries.md)是另一条路线，布局、dtype、动态输出和同进程限制须单独满足。

案例中的 Kernel/Tiling 使用生成的空实现，仅作接入流程演示；日志打印 Eager/图模式 ok 不证明业务算子数值正确。实际实现还要分别验证 Eager、npugraph_ex 和 GE；自定义 OPP 包同 vendor 名可能互相覆盖，交付时核对 vendor 和目标架构。本文没有编译或安装这些示例。

## OpPlugin原生交付与图交付不是同一次验收

TorchNPU固定主线的两语言适配页要求同步交付版本化Schema/实现、需要时的derivatives、文档模板、公开白名单、Schema清单和Meta注册。OpInterface等生成头文件或Python属性存在不独立证明特定版本可调用；FakeTensor的shape/dtype/stride/别名要与真实Eager语义一致。

文档npu_transpose的permute/empty_like和自定义add的Meta只是注册示意，不保证动态输入、混合dtype与返回别名都正确。add示例前向支持alpha、反向却只复制grad两次，其测试也没有通过自动求导验证绑定；不能据历史UT ok就把它当可入图的正确算子。具体版本、NZ路由、结构化配置和示例差异见[框架适配草稿](../../optimization/torch_npu/torch_npu_opplugin_adaptation.md)。

本节只补框架交付的检查层次，不把没有产品矩阵的整套适配示例扩为本卡三类产品的已验证配方，也不代替原有Converter、函数化与捕获合同。父仓及OpPlugin版本锁定仍须独立核对。

## feature目录的旧手动函数化示例

两固定快照feature目录的示例基于Torch2.1，称Torch2.5+自动函数化、TorchAir后续支持；同主线正式案例写2.6+。这是不同文档时代/入口，不能据旧future措辞判断当前主线必须手写，自动转换仍按前面的准确Schema前提核对。

旧例用my_inplace(Tensor(a!) x, Tensor(b!) y)->()明确两处mutation，原地Meta无返回值，非原地版本返回两个empty_like，并须clone两个输入再执行修改。C++函数化先sync/unpack，以AutoDispatchSkipFunctionalize避免递归，再replace_/commit_update/sync；Python插件方式用PrivateUse1+Meta+Functionalize注册并copy_回写。此例不证明任意别名、视图、输入重叠或符号形状都可复用同一实现。

GE Converter对应非原地版本，先TensorMove两输入，再调用原地GE IR并返回两个输出。**插件化章节的Converter漏写return**，与前面工程化章节有return的版本不同；直接照抄会按Python默认返回None，不能作为双Tensor输出的正确配方。这是静态阅读结论，未运行示例。Kernel/Tiling空实现与vendor覆盖仍只视为接入演示和交付前提，未摄取独立Kernel生产工程。

## 正式案例的结构化适配字段

发布正式案例已全文审阅；其PyTorch≥2.6自动函数化前提与主线正式案例一致，不能将feature目录Torch2.1手动路线的旧future措辞混入此处。非原地Schema的Tensor?、Tensor[]分别对应可选、动态输入，float/int作为属性；Meta示例empty_like(x)仅在“输出规格与x完全相同”的假设下成立。

案例在op_plugin_functions.yaml的custom项配置op_api: all_version，并用gen_opapi.out.size/dtype指向真实参考输入、exec指向aclnnMyOp；my_inplace新增输出z则参考y。这里all_version是该配置的版本选择语法，不证明所有TorchNPU/CANN组合均支持。多输出可用out0/out1，out变体的字段须匹配Schema输出参数名，不能机械用同一模板生成所有算子。

原地算子的Ascend IR包含回写x与新增z，PyTorch只返回z时Converter选第二输出；显式inputs/outputs方式与位置args方式按ge.custom_op各自约束解析。插件模块须在编译/执行前加载，不能因文件存在就视为Meta已注册。案例的msopgen命令、Python3.8/3.9构建示例及空Kernel/Tiling属于历史流程示意，不替代实际配套及数值实现。

## Evidence

- [docs/zh/custom_op_graph/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/overview.md)（primary）
- [docs/zh/custom_op_graph/op_plugin_adapt_torchair.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/op_plugin_adapt_torchair.md)（supporting）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
- [自定义算子零交付件入图](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/custom_op_zero_delivery.md)（supporting）
- [Recipes 挂载入口](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py)（example）
- [Recipes 自定义 Schema](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp)（example）
- [GLM5.2 按后端加载](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_2/models/custom_op_loader.py)（example）

- [补充固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/in_place_op_cases.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/non_in_place_op_cases.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/inplace_op_graph_entry.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/feature/inplace_op_graph_entry_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/feature/原地操作算子入图指导.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/in_place_op_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/non_in_place_op_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/op_plugin_adapt_torchair.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/custom_op_graph/overview.md)（constraint）
