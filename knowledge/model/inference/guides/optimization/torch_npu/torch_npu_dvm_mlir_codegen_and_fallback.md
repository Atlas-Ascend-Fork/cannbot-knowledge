---
type: Guide
title: DVM融合执行：代码生成、FX回退与模板边界
description: 区分固定两版DVM的规则筛选、代码生成和FX导入，解释主线Triton混合边界、布局缓存身份及调试同步成本。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/mlir_fusion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/graph_build.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/graph_build.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/meta_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/mlir_fusion.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/graph_fusion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/graph_fusion.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/fx_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/fx_pass.py
  role: implementation
created_at: '2026-11-10T12:23:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# DVM融合执行：代码生成、FX回退与模板边界

## 固定路线和证据范围

本卡审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的DVM MLIR融合调用链，并对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的选定生成/回退/安装函数。全部DVM emitter、Matmul模板与原生DVM运行库不在本卡审阅范围，不能据下述规则认证任意算子组合（独立graph_fusion入口见文末专节）。整卡平台未知，保持draft、空平台；不运行上游、设备或性能实验。

两版DVM入口均导入`dvm.mlir_fusion`；主线通过`_load_dvm_backend()`先安装MLIR适配，再由该模块末尾的enable注册`NpuDvmScheduling`与`NpuDvmWrapperCodeGen`。其配置enable具有进程内一次性保护。它是Inductor DVM路线，区别于[Eager lazy fusion](torch_npu_eager_lazy_fusion.md)，也不能从DVM这一环境值推导每个子图都生成DVM机器码。

## 先通过规则，才生产DVM builder

主线`NpuDvmKernel.codegen_kernel()`逐节点检查：FakeTensor placeholder的dtype须在所选类型集合；call_function须通过DVM规则。cat、permute和矩阵类各受独立使能门槛，clone还要求输入连续或满足can_use_view_load；注册表有该target时仍需其rule返回真。此处没有注册规则就不会因通用名字相似自动接受，默认调用也未打开allow_common_rule。

只有全部节点通过时才创建DvmCodegenInterpreter并生成builder；否则设dvm_codegen=None，保留可读FX表示。这里的规则检查不验证原生库每种shape、精度或运行成本；生成阶段发生其他错误也不能由此推断必有异常捕获后自动回退。

所选主线配置默认enable_cat=False、enable_fusion_permute=False、view_fusion_level=1；矩阵融合只在导入时环境变量`INDUCTOR_DVM_ENABLE_MATMUL_FUSION`精确等于字符串`1`时开启。它们是内部配置及消费者观察，不是新增公开稳定配置接口。开关允许进入规则层，不保证最终融合、收益或数值逐位一致。

## 完整FX回退和DVM生成不是CPU/设备二分

主线define_kernel在dvm_codegen缺失，或最终kernel_name命中force_fallback_kernel_names时，构造设备、输出、动态/突变、非连续索引与FX缓存等metadata，经父类辅助层生成`async_compile.import_fx`。有DVM builder的分支则生成并定义相应builder函数，其代码带`@dvm.kernel(...)`装饰器。

这两个分支都以`gpu=False`传给wrapper.define_kernel，源码用于把定义移出编译期Triton autotune区间；这个参数不是把NPU Tensor迁往CPU的指令，不能据名字判断执行设备。FX import实际运行与所有异常回退消费者未在本卡闭合，排障需继续检查生成的wrapper与真实算子调用。

主线`wrapper.src_to_kernel`的局部复用key由源码与布局key组成，后者纳入排序后的non_contiguous_indices键值和DVM输入cont_flag_input。该映射是当前wrapper的定义复用，不是跨进程二进制兼容或持久缓存命中保证。别只按相同计算文本忽略stride、view和连续性元数据；真实输出存储、临时转换与workspace仍需另外观测。

## 混合Triton模板有明确边界

主线DVM loader在配套Triton可用时注册NPU FlexAttention模板；DVM调度遇到TritonTemplateBuffer时，纵向融合拒绝跨这条边界，横向融合也拒绝含DVM或Triton模板的组合。Triton模板代码生成委托NPUTritonScheduling，并拒绝prologue_nodes；DVM Matmul模板同样明确不支持prologue融合，其epilogue还受另外的规则控制。

因此DVM后端出现Triton模板不自动表示选错后端；也不能把“模板作为一个融合kernel生成”误读为其前后所有pointwise都已合并。FlexAttention mask-in与mask-out选择另见[前向分派](torch_npu_flex_attention_forward_dispatch.md)；本卡不重复设备模板与Matmul epilogue的完整约束。

## 两个版本的安装方式与缓存身份不能混写

发布版的选定codegen只对call_function/placeholder的FakeTensor dtype进行所示判定，没有主线在此逐call_function执行DVM rule的同一实现。发布define_kernel的局部key是`(src_code, tuple(non_contiguous_indices))`，后半仅迭代字典键；主线改用上述包含索引值与输入连续标志的布局key。发布版DVM builder还向set_kernel_info传contiguity_flags，与主线选定生成体不同，不将主线metadata/缓存结论反套到发布。

发布版enable直接替换NpuMlirKernel/NpuMlirScheduling的方法；主线注册专门DVM调度/wrapper。两版所选enable都关闭allow_buffer_reuse；主线还设置specialize_float、reduction展开阈值、size_asserts与comprehensive_padding等。这里的buffer复用开关仅对应这个Inductor层，不能推广为设备分配器不缓存、所有输出永不复用或整体内存必定更高。

## 调试同步会改变性能观测

DVM装饰器先调用builder并setup，再提供返回输出的call和写入预分配输出的run。主线两者在dvm_config.debug_mode为真时都会追加NPU synchronize；发布版读取dvm模块自身debug_mode。同步失败时打印kernel身份、参数摘要与dump/das后重新抛出异常。两版debug默认均False，这不是所有正常调用无任何同步的证明。

同步检查有助把异步错误缩到该次调用后，但会改变运行重叠与计时；开启debug所得吞吐不能直接代表正常稳态。比较DVM优化时先确认实际DVM builder/FX导入/Triton模板路线，再记录shape/dtype/stride、配置读取时机、数值、首次编译与关闭调试后的稳态。所选源码没有提供本地性能结论，本卡没有新增verified。

## 独立graph_fusion入口与DVM wrapper分配

独立 graph_fusion 入口的实现面如下（静态阅读，未运行）。`dvm/graph_fusion.py`提供第二条融合路线：`GraphFusionPartitioner`基于torch.fx的CapabilityBasedPartitioner加`DvmOpSupport`（按`GRAPH_FUSION_SUPPORT_OP`白名单：add/sub/mul/div/pow/比较类等元素运算）分区，`split_partition_with_union_find`用UnionFind合并；`dvm_graph_fusion(graph)`对FX图做融合并生成带`@dvm.kernel`装饰的_fused_run桩（fake实现走FusedMeta）；`_dvm_generate_fallback_kernel`给无法DVM化的子图生成fallback kernel。它复用fx_pass的decompose_k1_matmul_to_mul、insert_promote_cast_by_pos_prims、insert_sum_fp32_prepost_cast_prims、expand_to_reshape等预处理与op_emitter的DVM_OP_REGISTRY，测试用例可经fx_test的generate_dvm_fx_case落盘回归。**graph_fusion与mlir_fusion是不同入口**：前者按FX子图分区生成DVM kernel，后者是本卡正文所述NpuDvmScheduling路线；两入口的支持集与回退条件不同，不能混用结论。`dvm/wrapper.py`的NpuDvmWrapperCodeGen继承NpuMlirWrapperCodeGen：子图沿用MLIR wrapper，主图write_header追加`empty_strided_npu = torch_npu._C._empty_strided_npu`，make_allocation在NPU且非内存生命周期跟踪/非pinned时改用NPUWrapperCodeGen的分配路径——**DVM wrapper的中间缓冲分配与MLIR wrapper不同源**，比较内存行为时先确认实际wrapper类。本增补不新增verified。

## graph_fusion/graph_build/fx_pass的两版分界

前一节默认主线语境；发布pin（TorchNPU 26.0.0）同路径文件差异如下（diff+AST比对）：

- **graph_fusion.py（430行→407行）**：`GraphFusionPartitioner`融合算子注册机制分叉——主线用`Library("dvm", "FRAGMENT")`手工`lib.define(…, tags=[torch._C.Tag.flexible_layout])`+`lib._register_fake`+`lib.impl`并登记`_fused_libs[qualname]`（源码注释：flexible_layout让共享producer免于各消费者定stride拷贝）；发布用`torch.library.custom_op("dvm::fused_graph_…", mutates_args=(), device_types="npu", schema=…)`+`register_fake`。FakeTensor检查范围：主线`[*orig_inputs, *orig_outputs]`，发布仅`orig_inputs`。主线在分区器内调用`decompose_k1_matmul_to_mul`，发布无此调用。`GRAPH_FUSION_SUPPORT_OP`白名单、`split_partition_with_union_find`、insert_promote_cast_by_pos_prims等其余预处理两版都在（体差异）；发布另有`dump_fx_test`/`uncont_policy`变量，`_fused_libs`主线独有。
- **fx_pass.py（251行→204行）**：发布**没有`decompose_k1_matmul_to_mul`**——前节「复用fx_pass的decompose_k1_matmul_to_mul」句仅适用主线；`annotate_mm_transpose_flags`：主线elif覆盖`(aten.addmm.default, aten.baddbmm.default)`且bias一维检查，发布仅`aten.addmm.default`（baddbmm转置标注主线独有）。其余9符号AST一致。
- **graph_build.py（232行→157行）**：`DvmCodegenInterpreter`与`is_fx_dynamic`体差异——主线对`node.meta["val"]`为None先continue防护，发布直接索引（meta缺val的节点发布版抛KeyError、主线跳过）。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/mlir_fusion.py)（primary）：定向范围114–282, 284–374, 531–562。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）：定向范围141–177, 430–436, 455–474。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/config.py)（implementation）：定向范围7–38。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/graph_build.py)（implementation）：定向范围31–57, 138–144；两版diff比对（U0 23 hunks，+61/−136）。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/__init__.py)（implementation）：定向范围34–49, 75–138。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/meta_kernel.py)（implementation）：定向范围425–431。
- [固定实现来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py)（implementation）：定向范围17–20。
- [固定实现来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/mlir_fusion.py)（implementation）：定向范围29–32, 82–195, 310–328。
- [固定实现来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/__init__.py)（implementation）：定向范围16–16, 62–124。
- [增补固定来源（主线）](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/graph_fusion.py)（primary）：430行结构+关键函数阅读；两版diff比对（U0 21 hunks，+29/−52；GraphFusionPartitioner函数级diff）。[增补fx_pass来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/fx_pass.py)（implementation）：26–57窗+两版diff（发布缺decompose_k1_matmul_to_mul、annotate范围差）。[增补wrapper来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/wrapper.py)（implementation）：30行全读。
- [补绑发布来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/graph_fusion.py)（implementation）：分界绑定，全文件diff+GraphFusionPartitioner函数级比对（custom_op vs Library FRAGMENT）。
- [补绑发布来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/graph_build.py)（implementation）：分界绑定，全文件diff+is_fx_dynamic/DvmCodegenInterpreter比对。
- [补绑发布来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/fx_pass.py)（implementation）：分界绑定，全文件diff（204行；缺decompose_k1_matmul_to_mul）。
