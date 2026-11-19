---
type: Guide
title: 实验FlexAttention：源码适配、梯度归属与稀疏元数据
description: 区分实验Triton与默认FlexAttention路线，解释AST结构计数、captured梯度/空块改写、模板渲染与原子compact
  offset。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_adapter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_template.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_config_generator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_strategy.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/__init__.py
  role: implementation
created_at: '2026-11-11T08:19:18Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验FlexAttention：源码适配、梯度归属与稀疏元数据

## 与默认路线区分的固定版本

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf实验Triton下flex_attention包六个完整本地模块。它复用默认FlexAttention源码、模板及多个helper，不能把[通用FlexAttention介绍](torch_npu_inductor_flex_attention.md)和[默认前向分派](torch_npu_flex_attention_forward_dispatch.md)直接当成这套适配器全部实现合同。发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b同六路径不存在，仅记录路径差异。

本卡没有导入这些模块、调用inspect/源码转换器、exec、生成模板、分配Tensor或执行前后向。平台与完整数值范围未知，保持draft和空平台；未重新展开默认lowering、外部模板正文及实际设备kernel。

__init__重导出注册、设备校验与patch入口；patch_flex_attention只委托共享patch，_validate_device复用默认函数，_register_npu_inductor_flex_attention才调用实验注册。不能仅因包可导入就认定已完成目标算子的注册、设备支持或编译。模板模块和policy模块本身含顶层源码复制/模板构造，所以“只看导出函数”也不足以概括其导入依赖。

## 小子图策略与候选配置

_prepare_linearize_fusion_options先复制kernel_options；score/mask graph按非output节点计数，含placeholder等节点，缺nodes时计0。TRITON_EXPERIMENTAL_LINEARIZE和FUSION用setdefault(True)，显式传值保留；FUSE_SMALL_SUBGRAPHS则被重新赋为总节点数<=24且FUSED_CAPTURED_BUFFERS长度<=8，FUSION_NODE_COUNT也被覆盖。它没有在这里直接读取或内联任意FX子图，不能把一个True选项当融合成功。

策略对象将前向mask-out/compact、反向dQ/dKdV、mask位置、tasklist及reduce模板分别接入，并额外给decode配置元组(64,2,1)。配置生成器沿用默认valid_block_m/n及_is_valid_block_pair做组合，固定num_warps=4；BWDDKDV用num_stages=2，其余为1。反向mode只接受BWD/BWDDQ/BWDDKDV；默认生成器如何确定合法块大小和外部选优仍独立。

## 源码复制的结构校验是版本边界

_compile_copy用inspect取得指定默认函数源码、解析AST，以default.__dict__的浅副本叠加替换globals，调整行号后compile/exec得到同名新函数。它没有原地改写默认函数的源码；但globals里的外部对象并未全部深拷贝，最终register()仍调用实际注册流程，不能从字典副本推出所有全局状态完全隔离。

transform模式要求准确匹配一组计数：static_workspace=1、captured_grad_guard=1、dispatch_plan=3、mapping=2、captured_owner=2、captured_subgraphs=1、options=2，以及dQ/dKdV subgraphs和dkdv_inputs_for_autotuning各1；任何计数不同就RuntimeError。精确替换按不含位置信息的AST相等判断，另有按ast.unparse或目标名字识别的规则。这些校验定位上游结构变化，不是对任意新版默认函数自动兼容的保证。

主要变化包括强制static_workspace_path=False；前/反向kernel_options改由policy准备；去掉maybe_append_choice的dispatch_plan参数及compact mapping的use_workspace参数；把“禁止mutated_grads”的特定assert替换为mask-out选项赋True。实验globals还把get_flexattention_dispatch_strategy固定为none，mask-out及tasklist入口分别受共享NPU config门槛控制，tasklist还要求默认兼容性谓词通过。因此不能把默认路线的静态workspace、dispatch-plan或任务列表自动选择不加区别地搬到这里。

_decoding_copy只扩充名为configs的带注解列表赋值，并要求这种结构恰好1处；不匹配就报错。注册时分别复制两个mask-in lowering、decode函数和最终注册函数，不是只替换一个设备kernel字符串。

## captured梯度与空块有两个适配层

AST规则让dQ options的RUN_CAPTURED_GRADS=False，dKdV为bool(joint_outputs.mutated_grads)，并把这些mutated_grads加入dKdV调优输入。重写的make_bwd_subgraphs_and_mutations只有base_mutated_inputs长度为2且存在mutated_grads时追加captured_grads_compute及对应可变输出。owns_captured_grads的两处参数按AST遍历先后赋值：第一处取mutated_grads的bool，第二处False，不是通过任意外部所有者标签作推理。

_ZeroGradValueInit在反向mask-in副本中给broadcasted_grad_value=empty_strided的特定赋值后插入fill_(0)并固定布局；要求恰好匹配1处。另一个模板字符串层_guard_empty_backward_blocks要求6段旧文本各出现1次：初始化has_q_blocks，汇总普通/完整稀疏Q块是否存在，对dK做where清零，并仅在有Q块时store dV。两层分别针对其实际默认lowering或模板位置，不能由这些局部改写直接认证所有mask、captured梯度或空输入的完整反向正确性。

## 模板渲染不等于普通TE逐点网格

ExperimentalTemplateKernel把jit装饰器精确出现1次的triton_heuristics.template改为npu_triton_heuristics.template；复制def_kernel时追加实验heuristics导入。复制generate时要求嵌套make_kernel_render的显式位置参数列表恰为[out_node]；本地条件不检查原有varargs、kwonlyargs、kwargs或defaults，增加hint_override=None和_kwargs，将局部kernel_options复制成render_options，必要时覆盖hint_override，并只把恰好1处**kernel_options换成**render_options。runtime renderer则在复制的命名空间换用实验TemplateKernel。

这些Attention模板有自己的SymbolicGridFn：前向为(ceil(Q/BLOCK_M),batch,q_heads)；反向合并ceil(Q/BLOCK_M2)*(q_heads//kv_heads)+ceil(KV/BLOCK_N1)，另两维batch/kv_heads；decode为(ceil(Q*gqa_group/BLOCK_M),batch*kv_heads,SPLIT_KV)。本地grid函数没有额外核验所有head整除与维度参数，调用前提沿外部lowering核对，不能直接套[普通TE共享网格](torch_npu_experimental_triton_grid_and_launcher_codegen.md)的一维裁剪公式。

_template统一给名字加te_，按需透传compile_options/manual_output_buffer，并对source执行两个propagate_nan文本的全量replace。这个去除NaN传播参数的helper没有匹配次数检查；不把字符串改写或模板构造成功推广成NaN/Inf传播、精度或性能已验证。导入的默认mask-out/tasklist/reduce设备正文仍按各自来源解释，不能因实验包绑定了这些名字就提升其全部资格。

## compact offset是原子分配位置，不保证逻辑行前缀顺序

实验_build_runtime_compact_sparse_mask_offsets为kv_num_blocks形状创建INT32 q_offsets，计算row_count及upper_capacity=row_count*kv_indices.shape[3]，以sizevars.check约束该上界<=INT32最大值。total_blocks为长度1的INT32缓冲，先fill零并固定布局；候选标记前两个输入可变、num_stages=1/warps=4，未取得任何choice就RuntimeError，选优使用列出的fake输入生成器。

本地offset模板按program-id跨行循环，读取每行num_blocks，用tl.atomic_add(TOTAL_BLOCKS,num_blocks)返回的旧值作为该行base并写q_offsets。grid为(max(1,min(row_count,NUM_VECTOR_CORE)),1,1)。这是并行原子分配段位置的规则，不保证offset按逻辑行顺序等于普通cumsum；上界检查也没有在这个函数逐项验证实际num_blocks非负或不超行容量。

compact mapping通过_compile_copy复用默认mapping函数，仅替换实验模板。上界、offset、mapping、假输入与真实mask必须按各自阶段核对；本卡没有执行稀疏布局、梯度或启动时延实验，既不报告节省比例，也不把“能复制上游源码”当作升级后的兼容验收。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention.py)：1–142；完整本地模块，导入/复制的外部正文另计。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_adapter.py)：1–263；完整本地模块，导入/复制的外部正文另计。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_template.py)：1–252；完整本地模块，导入/复制的外部正文另计。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_config_generator.py)：1–34；完整本地模块，导入/复制的外部正文另计。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/flex_attention_strategy.py)：1–10；完整本地模块，导入/复制的外部正文另计。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/flex_attention/__init__.py)：1–3；完整本地模块，导入/复制的外部正文另计。
