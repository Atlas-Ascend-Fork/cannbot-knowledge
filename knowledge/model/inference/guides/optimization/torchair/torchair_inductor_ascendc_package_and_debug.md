---
type: Guide
title: TorchAir 实验 Inductor AscendC：版本、启用、缓存与排障
description: 区分固定发布快照的独立扩展与主线内置后端，记录调试开关、产物和分阶段故障定位。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/README.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/docs/manuals.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/README.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/decomposition.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/passes/auto_functionalize_legacy_ops.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchAir 实验 Inductor AscendC：版本、启用、缓存与排障

## 固定身份与草稿范围

本卡比较TorchAir发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013与主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的实验Inductor扩展。文档没有覆盖全部实验功能的独立产品矩阵，保留draft/空platforms；不把其他PyTorch主线或TorchAir功能页的设备表移来补全。没有安装、导入、编译或设备运行。

发布README要求torch2.8+、示例torch_npu==2.8与CANN主线，单独editable安装experimental/_inductor_npu_ext/python，并在编译函数首次调用前import inductor_npu_ext。它是该实验模块的条件，不等于已固定26.0发布组合包含这一主线CANN扩展。

主线README列torch2.9至2.12、CANN主线，扩展随torch_npu打包为torch_npu/_inductor/ascendc，无需单独import；用torch.compile(options={"npu_backend":"ascendc"})，或在import torch前设置TORCHINDUCTOR_NPU_BACKEND=ascendc。专门PyTorch环境页的惰性读取时机另按其快照，本模块按自身更早的设置要求使用，不能由同名环境变量推定安装配套一致。CMake至少3.16、GCC至少7.3，set_env.sh路径随真实CANN安装位置。

README的勾选规划表示当时路线：Pointwise/Reduction、动态shape、workspace及硬件成本建模已勾选，水平/垂直、MM序幕尾声、SuperKernel、静态化、PGO等未勾选；主线另有静态TopN等详细设计，不能据未勾选否定实现，也不能据规划证明任意模型已支持。框架图展示FX/分解/Lowering→Scheduler→LoopIR/调度→AscendC的层次，没有额外硬件或性能矩阵；PyPTO是关注的DSL方向，不据描述登记为本版已运行后端。

## Wrapper选择与调试配置

主线默认PythonWrapper；cpp_wrapper=True或TORCHINDUCTOR_CPP_WRAPPER=1把整图Host调度生成C++并增加首次编译成本。手册限定仅torch.compile JIT，不支持AOT、常量图和图内多流；叠加AclGraph需PyTorch至少2.12并关闭graph_partition，仍遵循相应PyTorch的CppWrapper约束，不把另一条Triton AOTI能力套到这里。

| 配置 | 此扩展的作用及代价 |
| --- | --- |
| TORCH_COMPILE_DEBUG=1 | 保存中间产物及详细日志；缓存命中可能缺少新生成的文件 |
| TORCHINDUCTOR_COMPILE_THREADS=1 | 关闭异步编译，便于定位；默认取CPU相关原生配置，不保证少进程必然更快 |
| TORCHINDUCTOR_FORCE_DISABLE_CACHES=1 | 关闭原生Inductor缓存，但不单独绕过扩展ascendc缓存 |
| ASCEND_LAUNCH_BLOCKING=1 | 同步定位首个错误、降低性能，并使TASK_QUEUE_ENABLE走0 |
| TASK_QUEUE_ENABLE=0/1/2 | 本扩展分别直接下发、队列下发、队列内计算tiling并下发；0不代表所有设备计算自动同步完成 |
| TORCHINDUCTOR_ASCENDC_AUTOTUNE_TOPN | 正整数、默认1不做PGO；最多请求10个候选，实际数量可能更少 |

TORCHINDUCTOR_ASCENDC_DEBUG接受逗号分隔的裸选项或+前缀。cpu打桩不证明NPU可运行；allfallback与lowering互斥并在启动报错。decompose跳过扩展分解白名单、lowering放开原生lowering；nomatmul/nocat/nocanfuse分别关闭对应融合，gmm启用GroupedMatmul，gather放开gather/embedding/index_select及中文手册所称受支持整数索引。nommfold保留上游view-fold决策，noloadtrans关闭独立load-transpose切分，nothrow以unsupported占位继续而不是证明计算正确。layoutcheck检查size/stride/dtype/device，不一致抛FusedLayoutContractError；未开时手册描述告警路径，不能把开关关闭当布局已匹配。调试项默认未配关闭，不是统一生产性能配方。

## 日志、缓存与产物身份

主线调试日志在当前debug run的torchinductor/inductor_ascendc_rank_<rank>.log，rank优先已初始化分布式组，其次RANK，最后0。Generating kernel展示融合Loop；Road展示轴/索引重排；Sync/Async compile展示编译路线；Cache hint/Reuse表明缓存路径。退出时Lowered统计只说明允许Lowering，仍需有实现和最终融合产物，不能当已融合证据。

asc_graph.py是AscIR/Codegen入口，asc_kernel.py包含生成编译流程，inductor_wrapper.cpp是参数、workspace、tiling和下发包装；TopN另有asc_tiling.py、inductor_tiling_wrapper.cpp和逐候选asc_kernel_<hash>.py。graph.svg依赖Graphviz/pydot。output_code.py、前后FX/IR及节点映射用于核对实际路径；kernel_args_dump.log和layout_check.log分别用于下发参数与布局定位。benchmark.py的检查/采集区别见[数值与性能复现](torchair_inductor_ascendc_benchmark_contract.md)。

发布缓存在执行目录.npu_kernels_<user>，主线改为绝对TORCHINDUCTOR_CACHE_DIR（默认/tmp/torchinductor_<user>）下ascendc/host_<hostname>/autofused_<topologyhash>/<codegenhash>，同机rank共享namespace。匹配拓扑及生成代码hash，文件锁协调本扩展并发；不等于任意环境的二进制兼容保证。手册提示跨OS共享文件系统可能失去锁保护，旧torch相对缓存路径可引发CppCompileError，2.13修复说法只作为该手册断言，不扩为本README所列2.9..2.12已修复。

调试时优先换新的独立扩展缓存目录；修改asc_kernel.py或重编wrapper会直接影响对应本地缓存及后续模型运行。记录代码、软件身份和配置再比较，不用原生禁缓存开关的名字推定扩展冷编译已发生。重复固定输入还可能提高L2命中；首次/稳态、编译/运行及设备/端到端时间分别记录。

## 分阶段定位

| 报错阶段 | 优先核对 |
| --- | --- |
| Failed to execute graph code | 末尾原始Python异常及中间AscIR代码；扩展与CANN接口是否配套 |
| Failed to build ascend kernel | 异常给出的编译命令、真实编译器error与CANN符号签名 |
| Failed to build wrapper | Host头文件、链接库、GCC、TorchNPU及实际ABI |
| kernel init failed | 紧邻栈上方kernel名、库依赖、AutofuseTiling/AutofuseLaunch符号及静态tiling初始化 |
| execution failed | 动态tiling、stream、workspace或launch阶段；异步错误位置未必是根因 |

手册的-1和“usually”归因是排查线索，不能从一条报错唯一断言缓存损坏、OOM或Kernel实现错误。保留完整栈、版本、最小输入与实际缓存路径；Kernel编译/执行问题可按手册分流至AutoFusion，TorchAir问题按后端分流。本卡未执行任何复现命令，外部仓库/链接内容也未因此入库。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/README.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/docs/manuals.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/README.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/README_en.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals_en.md)（constraint）
## 主线导入期的全局配置改写与SoC探测

主线`__init__.py`在import时依次执行`_patch_inductor_lowering_device_selection`、`_finetune_inductor_config`（63–105）、`_patch_input_symbol_binding`、`_finetune_lowering`，随后按调试项分流：未设`decompose`时`_finetune_decompose()`，未设`cpu`时加载NPU lowering与passes，否则把backend注册到cpu设备。`_finetune_inductor_config`改写进程全局：dynamo`recompile_limit`8→16（注释：per-layer compile默认不够）、`specialize_float=True`、`do_not_emit_runtime_asserts=True`；inductor`unroll_reductions_threshold=1`、`size_asserts=False`（注释：npu算子返回连续张量，可能与meta输出不同）、存在该属性时`cpp_cache_precompile_headers=False`（AscendC用自身include集，跳过PyTorch通用PCH）、`DeviceProperties.multi_processor_count=0`；`allfallback`调试项追加`force_disable_caches=True`。C++设备选项与cpp_wrapper经torch_npu版本兼容入口patch。`_load_npu_passes`（107–135）把`run_pre_grad_custom_pass`/`run_post_grad_custom_pre_pass`注册进inductor配置，已被占用时仅告警不覆盖并提示可能引入额外tensormove；两组pass的逐条行为见[前后置FX改写](torchair_inductor_ascendc_pre_grad_fusion_passes.md)。

主线`common/__init__.py`定义`Soc`枚举（A2/A3/A5）并在import时探测：`soc_version>=260`→A5、`>=250`→A3、`220<=v<240`→A2，未知版本回退None并告警（等价不做SoC gating）；host-only调试（cpu/nothrow）直接None。下游各卡的`Soc.A5`门控均消费该值，None不门控不等于支持所有设备。

## 发布版扩展的导入期形态

发布`__init__.py`（293行）先以`sys.modules.setdefault('torch_npu._inductor',None)`检查并拒绝与torch_npu内置inductor重复注册，再`register_backend_for_device("npu", NPUScheduling, NpuWrapperCodeGen)`。其`_finetune_inductor_config`同样设recompile_limit=16、specialize_float、unroll=1、size_asserts=False、multi_processor_count=0，并把inductor分解表清空后只保留`{aten._to_copy.default}`白名单（主线是更大的keep集，见下节）；`pre_grad_custom_pass`缺省注册`auto_functionalize_legacy_ops`——把`torch.ops.npu.npu_scatter_nd_update_`替换为`modern::npu_scatter_nd_update_`自定义算子（原地签名，AOT可自动函数化并在融合后re-inplace，与主线`inductor_custom_passes`里的同名替换同构），已占用时告警跳过；另提供`_stub_debugging_host_only`配合host-only调试。发布`common/__init__.py`只有stderr logger（`[RANKn]`前缀，TORCH_COMPILE_DEBUG=1时DEBUG否则ERROR），没有主线SoC探测——发布扩展不做SoC门控。发布`config.py`是6行私有桩（`_sync_around_fuse_kernel`/`_debugging_host_only`），主线那组TORCHINDUCTOR_ASCENDC_*解析在发布不存在，不能对发布pin设置同名变量期待同样行为。

## 主线分解白名单与自定义分解

主线`decomposition.py`的`_finetune_decompose`（仅当未设`decompose`调试项时执行）先`_whitelist_decompositions`清空inductor分解表只留keep集：`_to_copy/rsub/silu/sgn/detach/floor_divide/matmul/arange/clamp/full_like/t/transpose/empty_permuted`、batch_norm系列（legit三型+backward+functional+native）、`masked_fill/_log_softmax/_softmax/native_layer_norm/native_group_norm/tril/triu/full/stack/linalg_vector_norm/isfinite/sigmoid_backward/conj_physical/cat`、zeros/ones/new_*家族、`norm/dist/renorm/silu_backward/native_layer_norm_backward`、`_fused_rms_norm(+backward)`（backward无native kernel，分解是NPU唯一执行路径，无条件keep）；`current_soc`已知且>=A5才追加`leaky_relu/_softmax_backward_data/gelu`（A2/A3上gt不支持bool输出、log1p/expm1无注册，拆开产生eager fallback切图，劣于整算子fallback）。

随后弹出来源`aten.upsample_nearest2d`全部分解表项与`CompositeImplicitAutograd/Autograd`kernel并清`_dispatch_cache`，再`make_fallback(aten.upsample_nearest2d)`——扩展侧让该family整体走fallback；这与TorchAir GE侧`adjust_implicit_decomposition`的vec改道是两层不同机制，互不替代（见[GE填充与采样](torchair_ge_padding_sampling_lowering.md)新增节）。覆写分解注册三组：`_unsafe_view`无条件覆写（非连续输入改用reshape而非view）；torch>=2.9且未设nommfold时覆写`matmul`（lhs>=3维、rhs 1–2维且lhs可零拷贝折叠→reshape+mm/mv+_unsafe_view）与`bmm`（rhs为batch维stride=0的广播共享2D权重→reshape+mm+reshape，对齐torch 2.9行为）；A5+（或SoC未知）追加`elu/mish/softplus`覆写，各自以fp16/fp32/bf16为门槛、其余dtype返回NotImplemented保持整算子fallback。最后`_remove_extra_random_decomps`清空`extra_random_decomps`并失效`fast_random_decomps`缓存，避免fallback_random=False时RNG被分解为bool mask与NPU期望的uint8 mask不兼容。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py)（implementation）：1–170完整读取（finetune 63–105、load passes 107–135、导入序列151–163）；171–966为调度/融合override，归融合决策等既有卡。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py)（implementation）：1–293完整读取。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/__init__.py)（implementation）：1–49完整读取。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/__init__.py)（implementation）：1–26完整读取。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/decomposition.py)（implementation）：1–378完整读取（whitelist 235–345、finetune 348–378、覆写54–233）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/passes/auto_functionalize_legacy_ops.py)（implementation）：1–46完整读取。
