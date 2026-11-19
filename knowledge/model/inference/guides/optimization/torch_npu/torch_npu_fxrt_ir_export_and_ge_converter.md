---
type: Guide
title: FXRT IR导出与GE转换器：ABI边界、版本化导出合同与SymInt保持
description: 记录FXRT向GE系FX转换器导出图的两条路径：ir_graph_export的POD字典版本化合同（ABI0/ABI1永久边界）与fx_to_c_graph的C++
  GraphExecutor构建（复用fx_backend钩子、不特化SymInt）。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/ir_graph_export.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/ir_graph_export.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/ir_graph_export_fields.inc
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_to_c_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_ir.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/common/intrusive_ptr_caster.h
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT IR导出与GE转换器：ABI边界、版本化导出合同与SymInt保持

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FXRT出向导出面：`runtime/executor/ir_graph_export.*`（含字段清单inc）、`python/fxrt/fx_to_c_graph.py`与`pybind/fxrt/pybind_ir.cpp`。静态阅读，未运行转换器；整卡draft、platforms为空。FXRT自身执行路径见[FXRT推理运行时](torch_npu_fxrt_runtime.md)。

## ABI0/ABI1是永久边界，不是待清理的技术债

`ir_graph_export.h`的文件头注释是本卡最重要的合同：GE系FX转换器的host库按`_GLIBCXX_USE_CXX11_ABI=0`构建，而fxrt/torch/torch_npu是ABI=1，**单个ir::Graph对象无法跨这条线共享**；GE host库按构造就是ABI=0，所以这个边界“直到GE自身迁移前是永久的”——早期注释说“ABI统一后删除”已作废，不要按旧注释行动。因此导出面只允许POD与字符串：`GraphExecutor::ExportIrGraph`把ir::Graph展平成dict交给Python层，树外消费者自行重建图。

## 版本化导出合同

字段清单集中在`ir_graph_export_fields.inc`（与消费者共享），键名经`ir_export_keys`常量写出（拼错即编译错）。`kIrExportSchemaVersion=1`：消费者必须拒绝schema_version不匹配的dict，**也必须拒绝完全没有schema_version的dict**（那是版本化之前的producer，已知会缺layout与symbol-channel键）；丢字段读回是"unset"而非报错，所以靠版本号提前失败而不是靠缺字段。修改字段清单必须升版本号，并同步test/fxrt/的golden期望。pybind_ir.cpp把ExportIrGraph等经nanobind暴露（intrusive_ptr_caster.h提供IR侵入指针的Python桥接）。

## fx_to_c_graph：复用fx_backend钩子，不跑FXRT

`build_c_graph_executor(gm, example_inputs)`构建C++ GraphExecutor但**跳过BuildExecutor/run**：在converter专用上下文里临时替换fx_backend的op映射与arg钩子（结束恢复原状，不改fx_backend.py源码），复用remove_matched_nodes、copy消除、full/getitem/setitem分解与输入/算子/输出钩子，call_module同样NotImplementedError。converter-only映射补充gather/_unsafe_view/repeat/constant_pad_nd/pad/full_like/ge/ne/mul_scalar/reduce_sum等前端未注册项。

## SymInt不许int()特化

`_concretize_shape_dim_for_abi0`是转换器侧的关键纪律：静态Python int保持int，**SymInt一律转成-1哨兵（ABI0 int_list的动态维表示），绝不int(symint)**——int(symint)会在inductor compile_graph还在运行时给Dynamo的活动ShapeEnv装上相等guard（如batch==120），RecSDK的mark_dynamic随之要么ConstraintViolationError要么每个batch编一张图。shape_list/as_strided两个arg钩子把size/stride/offset列表按此规则具体化，让ViewAlias/Path C的as_strided拿到具体静态维、动态维保持符号。这与fx_backend侧`SymbolicShapeManager.from_torch_with_sym`绑定的语义一致，但实现路径不同，不能互相替代。

## 边界与验证方式

本卡未实际导出或消费任何dict：schema_version拒绝逻辑、ABI0消费者的字段重建、SymInt哨兵的端到端效果（mark_dynamic下不增图）都应按真实转换器链路复核。升级字段清单时确认版本号与golden测试同步。converter路径与fx_backend路径的钩子差异（映射补集、SymInt策略）在排障时先分清走的哪条。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/ir_graph_export.h)（primary）：定向范围1–90。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/ir_graph_export_fields.inc)（implementation）：全文件63行。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_to_c_graph.py)（implementation）：定向范围1–130、257–302。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_ir.cpp)（implementation）：定向范围230–250。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/common/intrusive_ptr_caster.h)（implementation）：全文件51行。
