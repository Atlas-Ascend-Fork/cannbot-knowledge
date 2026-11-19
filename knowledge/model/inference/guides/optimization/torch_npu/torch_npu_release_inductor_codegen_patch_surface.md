---
type: Guide
title: TorchNPU 26.0.0发布版Inductor codegen包补丁面：设备映射、编译cflags与sizevars简化
description: 记录发布pin（f3ecfe4a）torch_npu/_inductor/codegen包导入时安装的monkey patch面：Reduction.num_splits与LoopBody索引改写、TritonScheduling/SIMDKernel接线、SizeVarAllocator.simplify简化、cpp_utils设备到kPrivateUse1映射与cpp_builder优化cflags替换，及与主线空壳/背移实现的版本分界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/_sizevars.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/cpp_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/cpp_builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/cpp_builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/_sizevars.py
  role: implementation
created_at: '2026-11-13T05:34:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU 26.0.0发布版Inductor codegen包补丁面：设备映射、编译cflags与sizevars简化

## 固定来源与范围

本卡记录发布pin f3ecfe4a7ef7395754da7ca2e35661a7132b519b（TorchNPU 26.0.0/v26.0.0-pytorch2.8.0）的`torch_npu/_inductor/codegen/__init__.py`（35行）、`codegen/_sizevars.py`（9行）、`codegen/cpp_utils.py`（6行，主线pin无此文件）与`cpp_builder.py`（162行）——主线对应物分别为0字节空文件、64行背移版、不存在与78行无patch函数版。全文静态阅读（四文件合计212行全文+两主线对照全读），未导入/运行。整卡draft、platforms为空。

## codegen/__init__.py：导入即安装的六路monkey patch

发布版`torch_npu/_inductor/codegen/__init__.py`在包导入时完成六类替换，全部绑定vendored torch._inductor内部属性：

| 替换目标 | 安装来源 | 作用 |
| --- | --- | --- |
| `Reduction.num_splits` | codegen/ir.py `num_splits` | Reduction按分裂因子切分循环（与ir.py发布版`loopbody__call__`、`transform_dims_in_indexing`、`substituted_dims_in_indexing`同文件配套） |
| `LoopBody.transform_dims_in_indexing` / `substituted_dims_in_indexing` / `__call__` | codegen/ir.py | 索引表达式改写与LoopBody调用入口（setattr/直接赋值两种装法） |
| `TritonScheduling.group_fn` / `select_index_dtype` / `create_tiling` | codegen/{scheduling,triton}.py | Triton调度分组、索引dtype选择与tiling创建接线（源内注释"need to enable this to speedup attn_cp_test"） |
| `SIMDKernel.is_compatible` | codegen/triton.py | SIMD kernel兼容性判定 |
| `sizevars.SizeVarAllocator.simplify` | codegen/_sizevars.py | sympy化简替换（见下节） |

**这是导入即生效的模块级替换**，没有开关或幂等保护；重复导入不重复安装（模块缓存），但与其它patch来源（如ascend_npu_ir插件、DVM enable）的先后顺序决定最终生效版本。引用任一被替换符号的行为前先确认本包是否已被导入。

## _sizevars.py：仅一条expand+xreplace化简

发布版`simplify(self, expr)`对tuple/list逐项`sympy.expand(s).xreplace(self.replacements)`，标量同样处理——即把torch._inductor的SizeVarAllocator化简替换为"展开+替换表直代"，无守卫与回退。主线64行版在此之上新增`_statically_known_stride_multiple_of`（结构化整除证明，背移pytorch/pytorch@93879b11e3b5）与`patch_simplify`（连带给`ir.Layout._stride_expr_ge_or_false`装`compare_strides`，带`_torch_npu_integer_strides`标记）；该契约由[主线Inductor reduction Welford测试期望](torch_npu_main_inductor_reduction_welford_tests.md)承载，**仅适用主线**——发布26.0.0没有stride结构化证明，布局比较走torch原生实现。

## cpp_utils.py与cpp_builder.py：C++侧设备串与编译选项patch

发布版`codegen/cpp_utils.py`仅`patch_device_to_aten()`：设`torch._inductor.codegen.cpp_utils.DEVICE_TO_ATEN["npu"] = "at::kPrivateUse1"`——发布版C++ codegen把NPU设备串映射到PrivateUse1 aten命名空间的唯一入口，由`_inductor/__init__.py`与`codegen/cpp_wrapper.py`引用（主线pin无此文件，设备映射走其它路径）。发布版`cpp_builder.py`（162行）在`include_paths`/`library_paths`之外新增四个函数：`get_cpp_torch_device_options`、`_get_optimization_cflags`、`patch_get_cpp_torch_device_options`、`patch_get_optimization_cflags`——把torch._inductor cpp构建的设备选项与优化cflags做成可整体替换的面；主线78行版无这四个函数（主线cpp_builder的ASCEND_HOME_PATH导入期getter选择由[Catlass二进制缓存与加载](torch_npu_catlass_binary_cache_and_loading.md)承载）。**引用发布版C++编译选项行为时先确认patch函数是否已被调用**，不能从主线cpp_builder推导。

## 边界与验证方式

本卡四个文件均为发布pin事实，主线对照仅用于分界：发布codegen/__init__.py为主动patch面而主线为空文件；发布_sizevars无stride证明；发布cpp_utils主线不存在；发布cpp_builder四patch函数主线独缺。全部静态阅读，未验证patch安装顺序、与DVM/ascend_npu_ir enable的交互及cflags实际内容差异；排障时按目标pin实际导入链核对。本卡不新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/__init__.py)（primary）：全文件35行阅读（两版diff：主线0字节）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/_sizevars.py)（implementation）：全文件9行阅读；主线64行对照全读。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/cpp_utils.py)（implementation）：全文件6行阅读（主线pin无此文件）。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/cpp_builder.py)（implementation）：全文件162行符号级阅读（include_paths/library_paths体差异+四patch函数）；主线78行对照全读。
- [主线对照来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/_sizevars.py)（implementation）：全文件64行（patch_simplify背移面，分界用）。
- [主线对照来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/cpp_builder.py)（implementation）：全文件78行（无patch函数，分界用）。
