---
type: Guide
title: 950 Inductor 编译资源与 Pass 定界
description: 区分编译子进程和预编译线程，说明 Pass 关闭、并行调度阈值及日志读取时机。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_COMPILE_THREADS.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHNPU_PRECOMPILE_THREADS.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/SHUT_DOWN_FX_PASS_LIST.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/ENABLE_PARALLEL_SCHEDULER.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_LOG_LEVEL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/ENABLE_PARALLEL_SCHEDULER.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_LOG_LEVEL.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/SHUT_DOWN_FX_PASS_LIST.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_COMPILE_THREADS.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHNPU_PRECOMPILE_THREADS.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/TORCHINDUCTOR_COMPILE_THREADS.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/TORCHNPU_PRECOMPILE_THREADS.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/limit_core/limit_core.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/INDUCTOR_ASCEND_LOG_LEVEL.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/environment_variables_summary.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/SHUT_DOWN_FX_PASS_LIST.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/image.png
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.png
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/joint_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/post_grad.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/graph_match_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/ascend_custom_passes/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/ascend_custom_passes/register_custom_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/fx_pass_level.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/check_mode.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/fx_check_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/joint_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/graph_match_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/ascend_custom_passes/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/ascend_custom_passes/register_custom_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/utils/fx_pass_level.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/utils/check_mode.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/utils/fx_check_utils.py
  role: implementation
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# 950 Inductor 编译资源与 Pass 定界

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## 并发资源

TORCHINDUCTOR_COMPILE_THREADS 虽名为线程，文档描述的是并发编译进程：默认 min(32,CPU核数)，1 在主进程串行，大于 1 使用相应并发。通用路径无内置上限，设置过大可耗尽内存或创建进程失败；Ascend C 模式上限 32。需要导入前设置。

TORCHNPU_PRECOMPILE_THREADS 另控制预编译线程，默认 max(CPU核数 // max(compile_threads,2),32)。因此减少编译进程数不一定降低预编译线程数，默认还可能远高于32；显式正整数覆盖，非整数记录异常退出。它在 torch_npu._inductor 初始化读取。

## Pass 的启用与关闭

SHUT_DOWN_FX_PASS_LIST 在 import torch_npu 前设置 all 或逗号分隔的注册函数名，让这些自定义 Pass 不注册；仅在默认关闭列表上追加，不能借此重新开启默认关闭项。用于对照数值和图变化，不是“关闭所有图编译”。

ENABLE_PARALLEL_SCHEDULER 仅大小写不敏感的 true 开启，1 不开启；默认 false。只对 NPU Python wrapper 生成生效，按 Cube/Vector 重排分流，节点总数不超过内置阈值（默认20）不执行。不能把变量开启当作所有图均已多流。

INDUCTOR_ASCEND_LOG_LEVEL 默认 WARNING，可选 DEBUG/INFO/ERROR/CRITICAL，在 _inductor 初始化读取并缓存，运行中修改不生效。先以串行编译、单个 Pass 对照缩小问题，再恢复正常配置测量。

本卡选这些资源/Pass 文档共同列出的 950；通用后端支持列表不能证明所有产品都有这些子能力。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## 预编译解析与日志回退的源码区别

中英文文档要求TORCHNPU_PRECOMPILE_THREADS显式正整数；同提交config.py的解析只执行去空白后的int转换，没有在这里检查大于0，非整数记录异常并sys.exit。不能因负数或0能通过这层转换就视为受支持配置，后续线程池与实际编译仍需独立核对。代码旁注释写“maximum ...32”，实际表达式和文档都是max(...,32)，即默认下限32；以表达式说明这处冲突。

日志初始化将INDUCTOR_ASCEND_LOG_LEVEL转大写，未配为WARNING，未识别字符串回到INFO；这补充文档列出的合法级别，不把非法配置视为关闭日志。core数量访问也经延迟属性和单次缓存读取设备属性，避免在模块导入时因该查询初始化设备；这是配置代码的策略，不是本地fork实验结果。更完整解析差异见[配置源码草稿](torch_npu_inductor_config_parsing.md)。

## 对照PyTorch时区分同名与新增入口

中英文环境对照页将TORCHINDUCTOR_COMPILE_THREADS列同名配置，但TORCHNPU_PRECOMPILE_THREADS是TorchNPU扩展的独立预编译控制，不是前者的别名。INDUCTOR_ASCEND_LOG_LEVEL对照torch._inductor.config.log_level，TORCHINDUCTOR_NPU_BACKEND对照Inductor配置机制，社区没有这两个同名环境变量；不能向CUDA环境设置这些名字并假定同样生效。

TORCH_CACHING_PRECOMPILE也列为同名入口，具体默认与触发条件仍按[自动预编译缓存](torch_npu_automatic_precompile_cache.md)，不由对照表替代版本和产品门槛。名称/默认可随PyTorch版本变化，按固定来源和实际配套分别核验。

## 内置旧说明与实际配置表达式的差别

同提交内部特性页和汇总表把COMPILE_THREADS默认写32、PRECOMPILE_THREADS写CPU核数的一半；公开环境页和已读config.py则分别为min(32,CPU核数)、max(CPU核数//max(compile_threads,2),32)。保留来源差异，以当前配置表达式解释该提交的默认，而不把旧简化数字当成所有机器的真实值。内部两并发页明确列A2/A3推理系列及950PR/DT，不据它扩大本卡所有Pass和调度的产品范围。

NPU_DEVICE_LIMIT内部页仅列950DT，未配置用全部核，示例按Cube,Vector写14,28。它提到A2/A3与950DT核数比1:2是比例背景，不是该功能的三产品支持表；该页称图中AclNN、手写/融合Triton与Catlass算子使用受限核数。结合配置解析的正数、属性上限及实际vector//cube比例校验，不承诺严格资源隔离、并发实例一定提速或任意图都已遵守限制。该设置主要面向小shape难以占满核的多实例评估。

## 图优化清单、训练例外和阶段冲突

内部SHUT_DOWN页明确实际关闭集合是默认关闭项与用户名单的并集，空字符串不能启用四个默认关闭的改写；all只指这组自定义Pass，不是关闭Dynamo、Lowering或全部编译。主要面向推理，带ignore_inference_check的Pass可在训练生效，不能由“图优化默认开”推广全部训练图。

图优化概述列PRE的cat_slice_cat_fold_pass/pad_slice_fold/fusion_attention_v3_pass，以及POST的fold_four_op_pass、fold_cast、fold_cat、fold_clone、fold_expand、fold_detach、fold_reduce、fold_sink_view、fold_slice、fold_squeeze、fold_to_copy、view_fold_pass、fold_where、fold_redundant_ops、dtype_optimal_pass、cat_to_view_pass、repeat_to_expand_pass、fold_iota_arithmetic_pass、broadcast_const_mask_compress、masked_add_compose_pass、bool_cast_mul_to_where_pass、sign_diff_hamming_fuse_pass、batch_embedding_fusion_pass及stack_sum_to_add_chain_pass。它把dtype_optimal_pass放POST，注册日志却标PRE；文字又称“新增5个”而紧邻默认关闭表只有四项，保留这些不一致，不据清单次序推定实际阶段或整个训练适用集合。

两张已查看流程图区分pre_grad_custom_pass、joint_custom_post_pass、post_grad_custom_pre_pass，再到Lowering、调度和CodeGen；内置示例的pad后slice消除只演示对应形态。注册日志说明已注册，真正改写还须[四项匹配条件](torch_npu_inductor_fx_rewrite_conditions.md)和产物核对；计算图多流的分组/依赖与自定义策略另见[并行调度](torch_npu_inductor_parallel_schedule.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_COMPILE_THREADS.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHNPU_PRECOMPILE_THREADS.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/SHUT_DOWN_FX_PASS_LIST.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/ENABLE_PARALLEL_SCHEDULER.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_LOG_LEVEL.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/ENABLE_PARALLEL_SCHEDULER.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_LOG_LEVEL.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/SHUT_DOWN_FX_PASS_LIST.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_COMPILE_THREADS.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHNPU_PRECOMPILE_THREADS.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/TORCHINDUCTOR_COMPILE_THREADS.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/TORCHNPU_PRECOMPILE_THREADS.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/limit_core/limit_core.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/INDUCTOR_ASCEND_LOG_LEVEL.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/environment_variables_summary.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/SHUT_DOWN_FX_PASS_LIST.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/image.png)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.png)（primary）

## 双版注册执行、缓存与训练路径的本地实现

补充固定主线ac0e1564与发布f3ecfe4的完整注册/驱动及辅助模块静态对照；发布源码未给本段新增产品支持表，不扩大前文文档选定范围。整个ascend_graph_pass大型改写实现、Fav3分区和外部Torch机制不因这些入口读完而闭合。

主线register_custom_pass把函数的ignore_inference_check属性先赋值，再合并默认关闭集合和SHUT_DOWN_FX_PASS_LIST。默认关闭项随已导入config的四开关决定；multi_slice开关同时控制sink_pointwise_cat_pass和multi_slice_concat_pass，但不关闭独立默认开启的remove_cast_after_slice_by_add_cat。环境字符串按逗号拆分、去空白、忽略空项，OrderedSet去重；all或精确函数名命中仅跳过append并原样返回函数。未命中按PassType/FxPassLevel列表追加，没有重复注册保护、完整类型校验或热刷新接口。环境是在每次装饰注册时读，默认关闭tuple由模块导入时配置构造；运行后改环境不自动清空已有注册表。

发布register_custom_pass只有直接append，没有上述关闭集合和ignore_inference_check形参。主线inference检查仅not torch.is_grad_enabled；发布还把非空IS_OPTIMIZER_TEST视为True，字符串'0'也非空，不能按布尔0解释。它不是遍历图证明无梯度、无训练副作用。

PRE驱动先在inference时按LEVEL1/2/3执行整张PRE表，随后不论inference再按函数名执行fusion_attention_v3_pass；因此推理模式下同名已注册项可被调用两次，训练也会被这个专门分支调用，不是统一的“PRE只跑一次”。POST主线先在inference时stable_topological_sort，随后执行inference或带ignore标记的项；发布POST整个执行仅在inference分支内，没有该训练标记逻辑或局部topological_sort。驱动没有为各Pass做事务回滚或逐项数值验收。

主线pre/post配置写入CustomGraphPass对象。uuid用本graph_match_pass及ascend_graph_pass两个文件hash，并以注册表按迭代顺序形成(pass_type, level, 函数名tuple)的repr作为extra，使注册集合和这两个实现文件参与缓存身份；不等于对全部被调模块、闭包或运行环境逐项hash。发布直接把驱动函数赋给两个配置槽，没有本地CustomGraphPass/uuid封装。两版设置均直接覆盖配置槽，没有保存旧值或本地恢复。

## NPU局部补丁与枚举helper

主线joint补丁先从各节点meta.val的pytree叶子判断是否有device.type='npu'，调用原constant_fold_uniform_value并保留其返回，只有此前判NPU图才额外DCE。发布调用原函数后，只要GraphModule就DCE，包装没有显式返回原结果。主线post_grad另遍历pass_patterns[1]，只给handler恰为mm_plus_mm的LoweringPatternEntry包extra_check：NPU匹配直接False，其他匹配继续旧predicate；按id仅在本次遍历去重，再次调用可重复包裹。补丁函数在本地定义不等于已经在所有初始化路线调用，DCE/检查也不代替重新编译和正确性证明。

FxPassLevel与PassType分别为1/2/3和PRE=1、POST=2，同类按value比较与hash；主线另有ComputeType VECTOR=1、CUBE=2、SCALAR=3、MEMORY=4、MIX=5、MLP_VECTOR=6、UNKNOWN=100，以及GroupType VECTOR=1、CUBE=2、MIX_01=3、MIX_02=4、MAIN=5。GroupType的lt/eq实际检查other是否ComputeType而非GroupType，不把它推成同类排序已经与其它枚举一致；发布只存前两个枚举。

has_storage只接受meta中val为Tensor，调用untyped_storage并仅捕获NotImplementedError；不检查所有别名重叠、容量或设备有效性。主线fx_passes包导入Fav3注册和mm_plus_mm补丁函数但只把前者列__all__，不代表这里执行了这些函数。Attention图桥见[局部包装合同](torch_npu_inductor_graph_attention_bridge.md)，不能与其它Attention分区/CP路线混用。
