---
type: Guide
title: Inductor配置与加载源码：解析差异和待确认产品范围
description: 保存固定配置及后端加载器的静态事实，区分注释、表达式、公共文档和未闭合的消费者/产品合同。
tags:
- task.lookup
- topic.compilation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/utils.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/environment_variables_summary.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md
  role: constraint
created_at: '2026-11-09T14:37:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor配置与加载源码：解析差异和待确认产品范围

## 固定源码与草稿原因

完整审阅TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的torch_npu/_inductor/config.py和__init__.py，并核对utils.py的classproperty实现。本文描述配置表达式和加载分支，不执行模块；产品范围无法为全部实验开关统一闭合，故保留draft及空platforms。不能把出现环境变量或注册函数当作Kernel、训练、任意模型或软件栈已支持。

## 配置读取和设备查询

配置在模块执行时读取居多；catlass_dir是classproperty，每次属性访问调用函数读取环境，不在装饰器中缓存。公共文档仍要求相关环境提前设置，真正加载模板及下游缓存时机另核。日志未配WARNING、先转大写、非法级别回INFO。

is_ascend950直接比较_C._npu_get_soc_version()与常量260；配置ub_size为950分支256KiB、其他分支192KiB，这些是本文件的编译配置数值，不是所有芯片物理UB规格的证明。prop/num_cube_core/num_vector_core通过模块__getattr__延迟取得，_get_core_nums用lru_cache(maxsize=1)；首次访问仍会调用current_device/get_device_properties，不称其完全不触发初始化。

NPU_DEVICE_LIMIT去空白并去掉空项后须有两个整数，分别为Cube/Vector核数；须为正、不超过属性值，并维持原vector//cube比例，非法时日志后sys.exit。只限制编译配置的来源表达式，不由此承诺硬件资源隔离或任意资源比例均合法。

预编译默认max(os.cpu_count()//max(compile_threads,2),32)，注释“maximum32”与表达式不同。显式字符串空白时沿默认，非空只做int转换，未在此检查正数；文档要求正整数仍适用。某字段有值不等于消费者接受该值。

## 布尔解析器和原始字符串

| 配置写法 | 在本文件中的解析行为 |
| --- | --- |
| _read_env_bool | strip/lower后接受1/true/yes/on |
| _parse_bool_env | strip/lower后接受1/true/yes/on/y |
| 多个精确比较字段 | 只认字符串1，不统一接受true/on |
| enable_inplace_buffers、FlexAttention的dq materialize | lower后认1/true/yes，未strip |
| aggresive_autotune | lower后认1/true；字段保留源码的拼写 |
| 动态shape分组开关 | lower后认1/true/yes |
| check_accuracy、auto_fallback、fallback_warning、traced_fx_graph_cache | 原始环境字符串或各自默认对象，不经过统一布尔转换 |

check_accuracy默认False、auto_fallback默认True、fallback_warning默认False、traced_fx_graph_cache默认None、enable_full_lowering_fallback默认空串（读取NPU_INDUCTOR_FALLBACK_LIST）。dump_fx_graph为原始DUMP_FX_GRAPH字符串或check_accuracy；非空"0"仍为真，可进入split_reductions=False分支，不能据这个分支证明全部精度校验消费者已启用。

_parse_float_env用于CostModel保留比例及分组benchmark显存比例，均默认0.25；float转换失败或≤0/>1告警回默认，没有isfinite检查。容差解析只接受rtol/atol的数字格式，逗号拆分，键大小写不敏感，坏项告警跳过，后一个有效重复键覆盖前一个，没有非负/有限性完整校验。配置层可解析不是公开合法输入证明。

## 静态默认和实验开关

| 字段或环境入口 | 配置中的默认与限定 |
| --- | --- |
| ENABLE_INPLACE_BUFFERS | 默认1；解析为假才把原生inplace_buffers设False，真分支不强制重写True |
| 原生配置覆盖 | coalesce_tiling_analysis、mix_order_reduction、loop_reindexing_after_fusion在模块中设False |
| TORCHINDUCTOR_ENABLE_WELFORD | 默认0、精确1开启 |
| TORCHINDUCTOR_ENABLE_LAYERNORM_V4 | _read_env_bool默认字符串1，附近注释却称默认关闭；不据此推定Welford或全部LayerNorm路径已开启 |
| enable_welford_post_reduction_reuse | 静态True；注释限定全静态、归约范围落在同一静态SIMD tile的复用意图，是否命中另核消费者 |
| catlass固定字段 | debug_info=False、max_profiling_configs=None、min_gemm_size=1、ignore_gemm_in_standard_mm=True |
| CATLASS_EPILOGUE_FUSION与profiling测量 | 默认0，精确1开启；enabled_ops原始字符串默认mm,addmm,bmm |
| INDUCTOR_NPU_BACKEND_GENERATE_TEST_RUNNER_CODE | 默认0、精确1；附近注明该功能尚未实现，不能生成已可用的standalone runner配方 |
| INDUCTOR_INDIRECT_MEMORY_MODE | 仅950分支读取，默认simd_simt_mix，另有simt_template/simt_only；fallback转None，其他非法名回simd_simt_mix |
| TORCHINDUCTOR_NDDMA | 950分支默认1、其他默认0，精确1判断 |
| TORCHINDUCTOR_ENABLE_FAST_GELU | 默认0、精确1 |
| TORCHINDUCTOR_ENABLE_EMBEDDING_DENSE_BACKWARD_LOWERING | 默认0、精确1 |
| TORCHINDUCTOR_ENABLE_EMBEDDING_LOWERING | 默认1、精确1 |
| FLEX_ATTENTION_DQ_BEFORE_SCALE_MATERIALIZE | 默认1、lower后1/true/yes |
| INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE | 默认0，lower后1/true；不把此字段单独当作全部候选调优已启用 |
| INDUCTOR_ASCEND_SYMBOLIC_GROUP_AUTOTUNE/TEMPLATES | 默认0与pointwise,reduction,persistent_reduction；模板配置先拆分、strip并去空项，实际模板筛选在消费者 |
| FASTAUTOTUNE/AUTOTUNE_METHOD | 默认0（精确1）及Expert；profile_path静态./profile_result/，不表示本次已创建目录 |
| TORCHINDUCTOR_NPU_FAST_LAUNCH | _parse_bool_env默认False |
| TORCHINDUCTOR_ENABLE_FUSED_MATMUL_RELU | 默认False，注释标A5专用且仍验证中，不补任意产品支持 |
| TORCHINDUCTOR_ENABLE_MULTI_SLICE_CONCAT | 默认False，未支持pattern仍保留原路径的意图需对应Pass核对 |
| TORCHINDUCTOR_ENABLE_GRAD_MATMUL_TRANSPOSE_OPT | 默认False，目标是transpose(mm(lhs,rhs))反向结果改写为mm(rhs.T,lhs.T)，不证明任意布局可改写 |
| TORCHINDUCTOR_ENABLE_GROUPED_MATMUL_FUSION | 默认False，合并同一cat前独立GEMM；注释说明累加不同、结果接近而非逐位一致 |
| TORCHINDUCTOR_ENABLE_MATMUL_TRITON | 默认False，注释限定带padding行主序输入的ND×2D折叠仍验证中 |
| FlexAttention工作区/策略 | FWD_MASK_WORKSPACE_BYTES默认256MiB，int后max(0,...),0表示精确容量；非法整数字符串在此未捕获。DISPATCH_STRATEGY默认None/原始字符串，不在本文件校验名称 |

FlexAttention两环境全名为TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_FWD_MASK_WORKSPACE_BYTES和TORCHINDUCTOR_ASCEND_FLEX_ATTENTION_DISPATCH_STRATEGY。autotune_continue_on_failure表达式只比较TORCHINDUCTOR_NPU_BACKEND是否精确为default，不按文档未配置的默认模式替表达式补值；lowering_axis_count默认None。

npugraph_trees.disable_cpu_input_check的setter先bool(value)，真时将原生slow_path_cudagraph_asserts设False，注释却写True；随后设回假并不在此恢复原生值。不能把它作为任意CPU输入可捕获的保证，更不能将非空字符串"False"当布尔False。

## 后端加载器的静态路径

__init__临时关闭设备自动加载、配置DVM编译线程、按TORCH_WARM_POOL（默认1、精确1）调用warm_pool后恢复自动加载值；这只是源码路径，本次未导入或创建进程池。DVM选择会把TORCHINDUCTOR_COMPILE_THREADS及原生compile_threads设1，加载时再次处理，目的是共享进程内lowering/autotune/runtime状态。

加载表除文档三模式外还有mlir和triton_experimental。mlir发弃用警告并要求torch_mlir；缺包抛ImportError。default/实验Triton检查triton-ascend，缺失时告警并返回，不因此认为后端已完整注册。未知名字在此字典get回退Triton loader，但_loaded_backend仍记录原字符串，不能据此推荐用非法值选择后端。

公共patch、设备接口/Meta与后端codegen注册分层；加载前restore_inductor_baseline，用户未显式设cpp.march时把None设空串，避免默认Host架构参数混入异构缓存。公共patch还会尽力预热Triton npu_utils Host扩展缓存，编译异常被捕获；注释提到C++20与旁路编译进程，这是导入副作用的线索，不能把只读源码审阅称作已编译或缓存已存在。

Triton路径安装算子分解、lowering、算法选择、异步编译、调度、前后Pass和设备wrapper；NPU_INDUCTOR_FALLBACK_LIST.strip()==allfallback走全fallback注册，否则保留普通fallback及mm/addmm/bmm/grouped_mm注册，多slice-cat受独立开关控制。FlexAttention另注册，不能说fallback等于禁止一切手写Kernel。mask最后一维为1时的_dense_to_ordered补丁按INT32 sum和零索引构造、其余调用原实现，不能推导全部BlockMask可运行。

parallel scheduler只在lower()==true时调用，原生comprehensive_padding在此设False。FASTAUTOTUNE精确1时会尝试启用ENABLE_PRINT_UB_BITS；SampleStack且多进程编译会尝试降为1。该分支使用log.warnings拼写，仅静态路径存在不足以保证实际执行成功。额外OpsHandler的index_select/gather_template/indexput_template/scatter_template注册默认类型传播，也不等于所有索引Kernel规格已闭合。

每次加载后还patch overlap scheduling、清空fast_random_decomps缓存并记录_loaded_backend；实验Triton子包通过_activate隔离激活。以上只记录加载层，不宣称被引用的全部Kernel、Pass、DVM/MLIR模块和Host扩展均已摄取。具体公开环境合同见[编译模式API](inductor_npu_backend.md)及对应调优指南，未运行任何上游代码或设备测试。

## 内置汇总只补文档断言，不闭合全部实验产品

同提交环境汇总另写USE_STORE_IN_CAT默认False，用于cat融合；NDDMA概述泛称950PR/DT，而独立详情只列950DT、其代默认1其他0。Planned Fast Launch默认关闭并面向Python Wrapper的Host固定开销，这些名字/默认不足以替代专门页的运行条件。汇总的空SHUT_DOWN列表“所有pass生效”也不能覆盖独立注册的默认关闭项；四个新图改写开关均默认关闭，且仍会被SHUT_DOWN名单关闭。

内置文档给若干开关补了明确950DT或PR/DT范围，相关稳定指南逐项引用；本文仍包含未闭合的额外实验配置，不因此把整卡转为stable或填充全局platforms。旧线程默认与表达式的差异见资源指南，不将汇总表当作运行配置证明。

## 留存MLIR README与当前加载器分别读取

两个固定提交的ascend_npu_ir/README保留Dynamo→FX→MLIR→CodeGen说明，声称TorchNPU>=2.6具备torch.compile，并列config/env/options三种选择MLIR方式。第一段config示例用==比较而非赋值，后面完整示例才用=；不能直接复制比较表达式就认为后端已修改。

旧文档强调环境在NPU初始化前、config在compile前，具体新环境接口仍有自己的加载/缓存时机；默认模式文档不能覆盖此处旧模块。主线_load_mlir_backend当前明确发FutureWarning称mlir已弃用并要求torch_mlir；缺包抛ImportError。README没有因此作废的标记，也不能据旧三种方式推荐未知产品上任意组合。

run_and_get_code示例只展示FP32乘法及生成wrapper内mlir_fused_mul_0.run的调用身份，没有比较std_out与compile_out的断言或性能测量；返回代码不证明数值、动态shape或硬件支持。该生成片段只按消费者路径阅读，未扩为Kernel生产工程，外部torch-mlir包未获取。950DT在26.1发布说明的MLIR排除与较新主线内部能力仍按版本区别消费。

## TorchAir实验AscendC扩展的独立固定身份

TorchAir发布快照的独立import扩展与主线随torch_npu打包的ascendc后端有不同启用方式、版本条件和缓存目录，见[版本与排障草稿](../torchair/torchair_inductor_ascendc_package_and_debug.md)。本卡PyTorch配置加载器出现ascendc入口不证明两独立主线配套，也不把Triton的Catlass/CostModel、Planned Fast Launch或AOTI能力直接迁到AF路线。

AF静态TopN、PGO独立子进程、图树、view融合及Profiler参数都有自己的条件；TORCHINDUCTOR_*同名前缀不表示读取时机、缓存层、布尔解析或硬件范围相同。当前实验来源硬件未整体闭合，继续保留独立draft，未把源码可见字段提升成设备已验证能力。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/utils.py)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/environment_variables_summary.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/README.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/ascend_npu_ir/README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md)（constraint）
