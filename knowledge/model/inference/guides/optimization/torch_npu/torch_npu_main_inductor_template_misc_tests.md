---
type: Guide
title: 主线 Inductor 模板/precompile 杂项测试族：INDEX_DTYPE 选择、rtree 标量存储回归、BERT 守卫与复数转换
description: 固定提交下 test/_inductor 十一个模板/precompile 杂项测试文件的测试侧契约：NPUTritonTemplate 的 _write_index_dtype_define、triton_experimental r-tree 提升后的存储行重写、_npu_rsplit_outer 准入守卫与 dualview 折叠、复数 convert_element_type 与 aclnnIsClose 复数限制。
tags:
- task.testing
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_template_index_dtype.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_triton_experimental_rtree_store.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_triton_experimental_native_bert_regressions.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_complex_dtype_conversion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_to_copy_stride.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_add_triton_wrap.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
created_at: '2026-11-12T17:11:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 主线 Inductor 模板/precompile 杂项测试族：INDEX_DTYPE 选择、rtree 标量存储回归、BERT 守卫与复数转换

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `test/_inductor` template_precompile_misc 族十一文件。其中四个文件为既有实现面卡的镜像（见末节指卡），本卡承载七个文件的测试侧新事实。未运行任何测试。

## 模板 INDEX_DTYPE 选择（test_template_index_dtype.py，190 行）

`select_algorithm.NPUTritonTemplate._write_index_dtype_define` 是 canonical/staged 此前零命中的实现面：向模板 defines 写 `INDEX_DTYPE : tl.constexpr = <dtype>`。

- **选择序**：显式 override（仅 `tl.int32`/`tl.int64`，非法值 ValueError "Unsupported index dtype"）→ 无 override 时按 `TritonScheduling.can_use_32bit_indexing` 的判定（safe → int32，否则 int64）；真实范围检查按 numel 与最大 stride（任一 ≥2^31 → int64）。`generate`/`make_runtime_renderer_factory` 把 override 放进 defines 与 kernel kwargs、不进 `meta`；`manual_output_buffer` 时用 `call_sizes` 代替 `layout.size` 参与判定，`large_input_buffers`（大辅助输入）不参与自动范围检查。
- **符号签名**：两个符号 SizeArg 的签名在 jit_lines 后全部被类型化为统一的 `i32`/`i64`（`triton_meta["signature"]` 全值等于该集合）——索引 dtype 决定全部 size 形参类型，而非只影响索引表达式。

## r-tree 提升后的标量存储行重写（test_triton_experimental_rtree_store.py，86 行）

回归修复：整图归约输出为标量（xnumel==1）时走整数索引 store；上游 store codegen 追加的 `.broadcast_to(<value.shape>)` 用的是 **r-tree 提升前**捕获的 CSE 形状，store 行保持提升前秩，Triton 拒编译 `ValueError('Cannot broadcast, rank mismatch')`。修复由 `torch_npu/_inductor/triton_experimental/codegen/triton.py:643` 的 `_rewrite_reduction_store_shape` 重建 store 行（该函数在 :1016 的 new_lines 管线中与 `_fix_masked_load_ptr`、`_npu_preserve_mixed_leaf_mul_where` 并列消费）。触发形态是 CausalLM loss（shift + log_softmax + nll_loss ignore_index；labels[:,1:] 的 stride 切片 reshape 注入 clone，归约索引分解成两个 r 节点、r-tree 被提升），历史产物名 `triton_unk_fused_clone_nll_loss_forward_slice_view_*`（Electra/Roberta/XGLM）。测试以 `EXPERIMENTAL_MARKER`（wrapper 的 `triton_experimental import npu_triton_heuristics` 导入行）识别 TE 代码生成。

## BERT 守卫三件（test_triton_experimental_native_bert_regressions.py，126 行）

- `_npu_rsplit_outer_applicable` 两拒绝分支：输出缓冲同时含物化 pointwise 输出（除归约输出外的 `output_buffers` 成员）→ False；归约 range tree 嵌套多节点（`r0_1`/`r0_2` 同树）→ False。OUTER r-split 只接受单一干净归约树。
- `_fold_dualview_reduction_index`：`ncfg.fold_dualview_rnode=True` 时，`inner + 512*outer`（r0_2 长 512、r0_3 长 4）折叠为已注册的扁平符号 `r0_1`（长 2048=512×4）——折叠结果必须命中 range tree 已登记的节点表，而不是凭空新符号。
- `_wrap_launcher_with_downcast` 的 input_output 写回（int32 视图 `add_` 后原 int64 张量更新）为[静态/快速 launcher 测试契约卡](torch_npu_experimental_triton_static_launcher_tests.md)已持 ABI/三模式事实的镜像。

## 复数与 dtype 边界

- test_complex_dtype_conversion.py（113 行）：`prims.convert_element_type` 的实数↔complex64 在编译图内保持 eager 语义——实→复 imag 全零、复→实取 `.real`、复→复、transpose/slice/empty/scalar 布局、±0/NaN/Inf 的 signbit、动态实→复一次编译、`torch.fft.fftn` 实输入编译输出复数（fullgraph）。**设备侧约束锚**：`aclnnIsClose` 不支持 complex64，NPU 上比较须拆 real/imag 两个分量（:35-50 assert_npu_equal）——排障时复数逐位比较不可直接用 allclose 类工具。
- test_to_copy_stride.py（60 行）：`aten._to_copy` 对 `as_strided` 非连续源在 FakeTensorMode 与编译产物上都保持源 stride（(4,2048,16,192) 形）——stride 保持回归。
- test_add_triton_wrap.py（53 行）：用户 `@triton_op`+`wrap_triton` 手写 kernel 在 inductor 编译后以 `sin_kernel_0.run` 形式保留调用（不被融合吞掉）——[矩阵乘族卡](torch_npu_inductor_triton_matmul_kernel_family.md) "用户手写 Triton kernel wrapper 仍被保留" 注释的编译产物级观测。

## 已覆盖镜像（不新建卡）

- test_template_precompile.py（93 行）：`_precompile_worker` 路由（TEMPLATE 无 size hints 串行、vector 多 config 并行、threads=1 串行、已有 compile_results 幂等走串行不重 prepare、skip_precompile 直返；`template()` 置 size_hints=None 而 `foreach()` 保留 hints 且同为 TEMPLATE 类型、保住 3 config 并行）——[precompile 流水线卡](torch_npu_main_inductor_precompile_pipeline.md) :833-852 逐条持有。
- test_precompile_without_device.py（42 行）：并行 worker 不触碰设备接口（forked 子进程 "Cannot re-initialize NPU"、逐 config 异常/栈收集）——同卡 :1380-1413 持有。
- test_triton_extension_cxx_standard.py（167 行）：`_with_cxx20` 只改 torch launcher 路径、driver/utils/注册类 globals 三命名空间分别 patch、幂等、Triton 3.2 spec_from_file_location 例外、torch<2.13 不 patch、GCH 头回归——[静态 launcher C++ 卡](torch_npu_static_launcher_native_runtime_cpp.md) triton_compat 节逐条持有。
- test_compile_autograd.py（53 行）与 test_assert_scalar.py（51 行）：compiled autograd（backward 内构造 torch.device("npu")）与 `aten._assert_scalar`（capture_scalar_outputs）纯数值 smoke，无断言 NPU 特有分支，不构成测试侧缺口，不另建卡。

## 失效边界与静态口径

- 全部未运行；`_write_index_dtype_define` 的 defines/kwargs、rtree 重写、BERT 守卫均为源码控制流与 mock 骨架阅读，`#4947` 类故障号为 docstring 静态记录。
- `_rewrite_reduction_store_shape` 只在 triton_experimental 代码生成树内消费；默认后端的 store codegen 是否需要同类重写未核，不外推。
