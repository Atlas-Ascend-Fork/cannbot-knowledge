---
type: Guide
title: GE 编译调优：在线编译、优化级别、View 与 Tiling 下沉
description: 按下发与编译瓶颈选择配置，记录 O1 例外、View 失效组合和 Tiling 下沉的版本约束。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/jit_compile.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/oo_level.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/optimization_switch.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/view_optimize.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/tiling_schedule_optimize.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/appendix/host_tiling_update.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/jit_compile.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/oo_level.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/optimization_switch.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/view_optimize.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/tiling_schedule_optimize.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/ge_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/ge_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/continguous_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/continguous_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_scope_attr.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE 编译调优：在线编译、优化级别、View 与 Tiling 下沉

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。本卡选取来源支持的 A2/A3 推理范围，其他产品和特殊参数另行核对。

## 编译成本与算子选择

config.experimental_config.jit_compile 当前只支持字符串 "auto"，不是可选 True/False 的万能 JIT 开关。静态 shape 选择在线编译；动态 shape 优先已有二进制，找不到再在线编译。分别记录首次编译和稳态执行成本。

## 图级优化与融合定位

config.ge_config.oo_level 默认 O3；O1 保留静态下沉等相关优化、关闭大部分图/UB 融合，但安装包 fusion_config.json 的 ExceptionalPassOfO1Level 仍开启。该功能在此发布文档中明确为实验功能、暂不支持商用，不能将 O1 当作关闭所有优化的对照。

oo_constant_folding、oo_dead_code_elimination 默认 None 随级别决定，可显式 True/False。optimization_switch 使用 "Pass:on;OtherPass:off"，名称大小写精确、分号分隔；与 fusion_switch_file 同配且指向同一规则时 optimization_switch 优先，需看生效日志和融合结果。

## View 优化

enable_view_optimize 默认 True，面向 permute/t/transpose/view/reshape。图内多流、算子控核、不超时 scope、指定算子 Dump 范围时，该优化不生效；不能把这些组合的收益变化全部归给 View 开关。精度定界可关闭并比较实际节点和存储关系。

## Tiling 下沉

tiling_schedule_optimize 默认 False；GE 静态 shape、部分 Cube/Vector 融合算子（例如 FIA）可将值依赖 Tiling 下沉至 Device AI CPU。新 CANN 编出的下沉算子不兼容不支持它的旧运行环境。

npugraph_ex 的 Host Tiling 参数刷新是另一机制：捕获时记录待更新算子并插入 Event wait，Replay 调用后下发更新并用 Event record 保序，不能把它称为 GE 的 Device Tiling 下沉。

- [融合规则与 Pass](torchair_fx_pass_and_fusion_controls.md)
- [FA 值依赖与静态下沉](torchair_ge_dynamic_shapes_and_fa_tiling.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线编译配置复核

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的在线编译、多级优化、融合开关、View优化和Tiling下沉页面仍分别限定GE图模式；总览列A2/A3/950推理。jit_compile仍仅列字符串auto，oo_level仍是暂不用于商用的试验配置，不能因主线增加产品范围便移除这些条件。

O1仍有安装包ExceptionalPassOfO1Level例外；独立常量折叠/死边消除开关能覆盖级别默认值。optimization_switch相同规则优先于fusion_switch_file，不同名称规则则需分别核对，不由一个开关推出整个优化流水线都关闭。

View优化仍在多流、限核、不超时scope和指定Dump范围时失效。Tiling下沉仍限静态shape及当前支持的Cube/Vector融合算子，不给出某个CANN最低版本号；需核对编译与运行环境实际均具备该特性，不从“新包”字样自行推导版本阈值。下沉目标是Device AI CPU，不能与npugraph_ex的Host Tiling刷新混称。

## optimization_switch固定规则名录

两固定快照页面的104条列表项对应102个不同规则名；DynamicRNNInsertTransposePass与FusedBatchNormGradFusionPass各重复一次，重复条目不代表另一个Pass。下列保留准确大小写和拼写（包括源表的sedBatchNormGradFusionPass），只作为该页可配置名称的定位入口，不证明当前安装包包含每项或关闭后功能仍正确。

`AABiasaddConvFusion`、`AddNFusionPass`、`AddRmsNormFusionGraphPass`、`ADeformableConv2dPass`、`ADepthwiseFusionPass`、`ALSTMFusionPass`、`ApplyAddOutputPass`、`AReduceMeanFusionPass`

`AReduceSumFusionPass`、`ArgMaxWithFusionPass`、`AvgPool3DFusionPass`、`AvgPool3DGradFusionPass`、`AvgPoolGradFusionPass`、`AvgPoolQuantProcessFusionPass`、`BatchMatMulFusionPass`、`BatchMatmulV2QuantProcessFusionPass`

`BatchNormBnInferFusionPass`、`BatchNormGradBnInferGradFusion`、`BatchNormGradInfGradFusion`、`CastRemoveFusionPass`、`clip_by_norm_nodivsquaresum`、`CommonLSTMFusionPass`、`CommonSubexpressionEliminationPass`、`ConstToAttrGatherV2Fusion`

`ConstToAttrPass`、`ConstToAttrReduceSumFusion`、`ConstToAttrResizeNearestNeighborGradFusion`、`ConstToAttrStridedSliceV2Fusion`、`Conv2DQuantProcessFusionPass`、`Conv2DTDQuantProcessFusionPass`、`COPYPass`、`DeConvQuantProcessFusionPass`

`DeformableOffsetsFusionPass`、`DepthwiseDfFusionPass`、`DepthwiseDwMulFusionPass`、`DepthwiseFusionPass`、`DepthwiseInsertTransDataFusionPass`、`DepthwiseToConv2dFusionPass`、`DreluFusionPass`、`DWConv2DQuantProcessFusionPass`

`DynamicGRUV2GradFusionPass`、`DynamicRNNFusionPass`、`DynamicRNNGradAFusionPass`、`DynamicRNNGradAlignFusionPass`、`DynamicRNNGradDAlignFusionPass`、`DynamicRNNGradDFusionPass`、`DynamicRNNGradFusionPass`、`DynamicRNNInsertTransposePass`

`DynamicRNNSeqFusionPass`、`EinsumPass`、`FCQuantProcessFusionPass`、`FixPipeAbilityProcessPass`、`FlattenV2Pass`、`FusedBatchNormBertFusionPass`、`FusedBatchnormFusionPass`、`FusedBatchNormGradFusionPass`

`GlobalAvgPoolPass`、`GroupConv2DQuantProcessFusionPass`、`HostBNFusionPass`、`HostShapeOptimizationPass`、`In-placeAddRmsNormFusionPass`、`MapIndexFusionPass`、`MatMul2MatMulV2FusionPass`、`MatmulV2QuantProcessFusionPass`

`MaxPoolWithArgmaxFusionPass`、`NormalizeFusionPass`、`PackFusionPass`、`PassThroughFusionPass`、`PassThroughSecondFusionPass`、`PermuteFusionPass`、`PoolingQuantProcessFusionPass`、`PReluGradFusionPass`

`PriorBoxPass`、`ProposalFusionPass`、`RNNFusionPass`、`sedBatchNormGradFusionPass`、`SingleBatchNormFusion`、`SoftmaxGradExtFusion`、`SpatialTransformerDPass`、`SPPPass`

`TbeAntiquantMaxpoolingFusionPass`、`TbeConvCommonRules0FusionPass`、`TbeConvCommonRules2FusionPass`、`TbeConvDequantS16FusionPass`、`TbeConvRequantFusionPass`、`TfMergeConv2DBackpropInputFusionPass`、`TfMergeSubFusionPass`、`TfTagNoConstFoldingFusionPass`

`TransdataCastFusionPass`、`TransposedUpdateFusionPass`、`UnpackFusionPass`、`V100NotRequantFusionPass`、`V200NotRequantFusionPass`、`WeightQuantBatchMatmulV2TransposeFusionPass`、`YoloPass`、`YoloV2DetectionOutputPass`

`YoloV3DetectionOutputV2Pass`、`ZConcatDFusionPass`、`ZConcatExt2FusionPass`、`ZConfusionSoftmaxGradFusionPass`、`ZSplitVDFusionPass`、`ZSplitVFusionPass`

其中CommonSubexpressionEliminationPass是GE公共表达式消除，HostShapeOptimizationPass是该页所述AI CPU断流水Pass。用大小写精确的 `Pass:on;Other:off` 按需配置；页面特别提醒这些规则关闭可能影响功能，不把完整名称表当作批量关闭方案。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/jit_compile.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/oo_level.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/optimization_switch.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/view_optimize.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/tiling_schedule_optimize.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/appendix/host_tiling_update.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/jit_compile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/oo_level.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/optimization_switch.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/view_optimize.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/tiling_schedule_optimize.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
## 编译调优承诺的源码配对

本节把本卡五页（jit_compile/oo_level/optimization_switch/view_optimize/tiling_schedule_optimize）的文档承诺与两固定 pin 的 TorchAir Python 实现配对；选项赋值与校验机制、序列化键名、tiling local/global 与 O1 覆盖 topoSortingMode 等既有结论分别以[分组配置序列化与模式消费者](torchair_grouped_config_serialization_and_mode_consumers.md)、[配置边界与支持告警](torchair_compiler_config_boundaries.md)为准，此处只补实现锚点与新差异，不重述。

- jit_compile 仅支持 "auto"：`OptionValue("auto", ["auto"])`（experimental_config.py:20，两版同行同枚举）；max-autotune 序列化在值为 "auto" 时写 local `ge.jit_compile="2"`（两版 46–47，枚举只有 auto，等价于该分支恒写）。静态/动态 shape 的编译方式判别不在已读 TorchAir 路径中——本仓只把 "auto" 编译为选项值 "2" 交给 GE；两个 unsupport 名单（compiler_config.py:63–91 主线/63–81 发布）均未列 jit_compile，reduce-overhead/npugraph_ex 下设置它既无告警也不进入 aclgraph 分支序列化。
- oo_level 候选恰为 O1/O3：`OptionValue("O3", ["O1", "O3"])`（ge_config.py:14 两版），文档表外取值在 TorchAir 层即被拒。`ge.oo.level` 无条件写 global（主线 32/发布 31），默认 O3 也随会话发送；O1 时另写 local `ge.topoSortingMode="3"`（两版 37–38），该覆盖关系与合并顺序见序列化卡。oo_constant_folding/oo_dead_code_elimination 默认 None：None 时不发送 `ge.oo.constantFolding`/`ge.oo.deadCodeElimination`（主线 33–36/发布 32–36），文档「O1/O3 下默认开启」依赖 GE 按级别自行开启，TorchAir 层未显式下发布尔值；显式 True/False 才写 "true"/"false"。O1 例外的 ExceptionalPassOfO1Level 在两 pin python/torchair 内零命中，该名单属 CANN 安装包 fusion_config.json，不在本仓。
- optimization_switch 无格式校验：`OptionValue(None, None)`（ge_config.py:19 两版），"Passname1:on;Passname2:off" 语法只存在于文档；非 None 时经 `OptionValue.value` 的字符串化转发 global `ge.optimizationSwitch`（两版 40–41）——非 None 值的 `str()` 结果若精确等于 "True"/"False"，则分别输出 "1"/"0"，否则输出其 `str()` 表示；字符串 "True"/"False" 本身也会被映射，不是任意对象原样转发（主线 _option_base.py:33–41/发布 32–40）。文档「配置同一融合规则时以本功能为准」的优先级不在已读实现路径中——TorchAir 同时转发 `ge.optimizationSwitch` 与 `ge.fusionSwitchFile`（后者见序列化卡），优先级裁决属 GE 下游消费，本仓静态读数既不能证明也不能证伪。
- enable_view_optimize 的实际门：默认 True（experimental_config.py:26 两版）。GE 转换器 `parse_output` 与 `_parse_node_internal` 挂 `@guard_view_input`（fx2ge_converter.py:1595、1722）：开关开启、target 属 `view_white_list` 恰好五个 ATen 目标（permute.default/view.default/transpose.int/t.default/reshape.default，主线 continguous_utils.py:20–26，发布 20–21 同五项，与文档五算子一一对应），且（无 scope 属性或仅 super_kernel scope）时跳过建 GE 节点；否则对参数做反推 `optimize_view`。view/reshape 还要求输出全部符号维已记录在源 mapsym（continguous_utils.py:107–110），引入新符号维的 view 不获跳过处理。文档「多流/控核/不超时/Dump 范围不生效」对应实现的通用 scope 门：`has_scope_attr()` 为真且非纯 super_kernel 即中断跳过（_scope_attr.py:79–92 主线）；scope 构造器还包括 deterministic、data_dump、npu_stream_switch、limit_core_num（scope/__init__.py:22–81 主线）——四项清单未穷尽实现门，任何非 super_kernel scope（如确定性 scope）同样在该 scope 块内禁用 view 跳过。
- 文档未列出的强制关闭：图内含 `npu.npu_weight_quant_batchmatmul.default` 且 torch_npu 已导入时，`_gen_compiled_gm` 直接把 `config.experimental_config.enable_view_optimize` 置 False 并打 warning（npu_fx_compiler.py:728–734 主线/641–647 发布）；该赋值落在共享 CompilerConfig 对象上且读到的路径无恢复逻辑，同一配置对象的后续图编译也不再享受该优化。发布版 `_get_npu_outputs_of_view_ops` 还没有主线为 `detect_fake_mode` 返回 None 补的 FakeTensorMode 回退（主线 continguous_utils.py:128–132），两版 view 跳过内部路径存在该实现差异。
- tiling_schedule_optimize 只做布尔转发：默认 False（experimental_config.py:28 两版），序列化 main 写 local、release 写 global（版本差异已在序列化卡，不重述）。文档「静态 Shape、FIA/IncreFlashAttention 等融合算子才下沉」的条件在已读的 TorchAir 路径中无对应检查：该字段在 python/torchair 的全部引用只有字段定义、序列化、unsupport 名单与主线导出白名单（负向扫描）；FusedInferAttentionScore/IncreFlashAttention 的命中只是算子转换器命名，不引用该开关。条件裁决与执行属 GE/算子层。
- 「仅适用于GE图模式」的实现语义：集成 `get_npu_backend` 构造时调用 `_check_config_support`（npu_fx_compiler.py:1059 主线/898 发布）。reduce-overhead 下 oo_level="O1"、显式 oo_constant_folding/oo_dead_code_elimination、tiling_schedule_optimize=True、enable_view_optimize、optimization_switch 的任意非 None 取值触发一次 UserWarning「may not take effect or report error」（compiler_config.py:70–91、94–121 主线/68–81、84–109 发布）；npugraph_ex 模式收集了告警项但不满足输出条件（`mode in ["max-autotune","reduce-overhead"]`，主线 109/发布 99），静默无告警；独立 npugraph_ex 包的 npu_fx_compiler.py 未见该检查（负向扫描）。GE 模式走 unsupport_geconfig_list，不含这五项。合法取值下没有模式对这五项抛硬错误——「无硬错误」只限定 `_check_config_support` 的模式告警逻辑：名单外取值（例如 oo_level="O2"）在 setter 赋值时即抛 ValueError（主线 _option_base.py:43–60/发布 42–48），与模式无关。「仅适用于GE图模式」在 TorchAir 层不是拒绝执行，也不能概括为「capture 路线不序列化」：`_GEConfig.as_dict(mode)` 不读取 mode（主线 24–45/发布 23–44），`ge.oo.level` 无条件、显式 CF/DCE 与非 None optimization_switch 在任何 mode（含 capture 配置）照常序列化；`CompilerConfig.as_dict` 把 `self.mode.value` 原样传给 `NpuBaseConfig.as_dict`（两版 compiler_config.py:54–60），后者在任何 mode 都委托全部嵌套 config（主线 _option_base.py:249–273/发布 234–254）——OO level/显式 CF/DCE/optimizationSwitch 因此仍出现在 capture 配置的序列化结果里。五项中只有 experimental 的 `ge.jit_compile`/`ge.tiling_schedule_optimize` 两个 GE 键写在 `mode=="max-autotune"` 分支内（两版 40–52），capture 模式不写这两个键。序列化在场不等于下游消费或生效：GE 侧是否消费这些键、capture 路线是否存在后续过滤，静态读数没有消费者证明，不从序列化推断生效；enable_view_optimize 另有 Python 侧消费者 `guard_view_input`（见上一条）。另按 `_get_all_leaf_properties` 遍历全部叶子值（compiler_config.py:134–165）与 OptionValue 把默认值存入 `_value`（主线 _option_base.py:17/发布 16）的静态读数，reduce-overhead 下未显式设置 enable_view_optimize 时其默认 True 同样进入告警比对，即该告警不要求用户显式配置；其余四项的默认值不在各自名单内，默认构造不触发。
- 主线 fx2ge_converter.py 的 COMPILE_OPTIONS_WHITELIST（124–143，含 ge.jit_compile/ge.oo.level/ge.optimizationSwitch/ge.oo.constantFolding/ge.oo.deadCodeElimination/ge.tiling_schedule_optimize/ge.fusionSwitchFile）与 `_filter_options_by_whitelist`（2356–2362）只在导出 options.json 路径过滤作用域（`_generate_export_options_config` 2365–2398，导出行为见[导出身份与 options 文件](torchair_ge_export_weight_identity_and_files.md)）；该白名单与过滤函数为 main 独有，release pin 的 python/torchair 内 rg 未命中（负向扫描），发布版导出走其自身路径，不能用主线白名单推导发布版 options.json 键集。

### 配对差异归组

| 文档承诺 | 实际门槛与动作（静态读到） | 失败/版本边界 |
| --- | --- | --- |
| jit_compile「系统自行判断编译方式」 | 枚举仅 "auto"；max-autotune 恒发 local ge.jit_compile="2"（两版 46–47） | 静态/动态判别交 GE，本仓 0 强制点；非 GE 模式不序列化且无告警（unsupport 名单未列） |
| oo_level O1/O3、次级开关「默认开启」 | 枚举恰 O1/O3；ge.oo.level 恒发 global；O1 另写 local topoSortingMode="3"；折叠/DCE 为 None 时不发送 GE 键 | 「O1/O3 下默认开启」是 GE 级别行为；ExceptionalPassOfO1Level 属 CANN 安装包（两 pin 0 命中） |
| optimization_switch「同规则以本功能为准」 | OptionValue(None,None) 无格式校验，非 None 经 OptionValue.value 字符串化转发 global ge.optimizationSwitch（str(value) 精确为 "True"/"False" 时转 "1"/"0"，其他情况取 str(value)，字符串 "True"/"False" 也映射） | 优先级不在本仓路径中裁决；错误格式的实际后果静态不可见 |
| view_optimize「多流/控核/不超时/Dump 不生效」 | guard_view_input：五目标白名单+通用 scope 门+view/reshape mapsym 门 | 四项清单未穷尽（任何非 super_kernel scope 同样禁用）；weight_quant_batchmatmul 图样强制关闭且不恢复（两版均有，文档未列）；发布版无 FakeTensorMode 回退 |
| tiling_schedule_optimize「静态 Shape、融合算子才下沉」 | 仅布尔→"1"/"0" 序列化（main local/release global） | 下沉条件在本仓 0 检查点；兼容边界按文档+CANN 实际版本核对 |
| 五页均称「仅适用于GE图模式场景」 | reduce-overhead 一次 UserWarning、npugraph_ex 静默、GE 模式不列这五项；capture 配置仍序列化 ge_config 侧键，仅 experimental jit/tiling GE 键限 max-autotune 分支（正文「实现语义」条） | 合法取值无硬错误、名单外取值 setter 抛 ValueError；「不生效」不是「被拒绝」，也不可由序列化推断 |

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py)（implementation）：1–117 全文读取（五页相关字段 20/26/28 与 as_dict 34–56；56 行后的 aclgraph 子组与五页无直接关系，仅作通读）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py)（implementation）：14–30、34–56 窗口读取；与主线全文件 diff 显示 1–56 内除 tiling local/global（43 行）外仅排版差异，57 行后未复读。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/ge_config.py)（implementation）：1–45 全文读取。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/ge_config.py)（implementation）：1–44 全文读取；oo_level/折叠/DCE/optimization_switch 定义与序列化和主线一致（仅排版差异）。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/compiler_config.py)（implementation）：1–165 全文读取（unsupport 两名单 63–91、_check_config_support 94–121、_get_warn_config 124–131、_get_all_leaf_properties 134–165）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/compiler_config.py)（implementation）：63–112 窗口读取（两名单与 _check_config_support 输出条件与主线同构）；1–62、113 行后未复读。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/continguous_utils.py)（implementation）：1–188 全文读取（view_white_list 20–26、is_view_case 95–114、guard_view_input 170–187、FakeTensorMode 回退 128–132）。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/continguous_utils.py)（implementation）：20–21、160–178 窗口读取；与主线全文件 diff 显示除排版外仅主线多 FakeTensorMode 回退（128–132）。
- [新增来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：700–759、1050–1065 两窗口读取（weight_quant 强制关闭 728–734、get_npu_backend 内 _check_config_support 调用 1059）。
- [新增来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：635–650、890–902 两窗口读取（weight_quant 强制关闭 641–647、_check_config_support 调用 898）。
- [新增来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：95–169、1588–1600、1716–1726、2355–2399 四窗口读取（COMPILE_OPTIONS_WHITELIST 124–143、@guard_view_input 1595 与 1722、@guard_scope_attr 1723、导出过滤 2356–2398）。
- [新增来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/_scope_attr.py)（implementation）：1–131 全文读取（apply 布尔写 40–41、has_scope_attr 79–80、has_only_super_kernel_scope_attr 83–92）。
- [新增来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/scope/__init__.py)（implementation）：1–81 全文读取（scope 构造器清单 22–81）。
- [新增来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py)（implementation）：11–60、249–273 窗口读取（OptionValue 把默认值存入 `_value` 在 17 行；`value` 属性 33–41 把非 None 字符串化、布尔映射 "1"/"0"；setter 名单外取值抛 ValueError 43–60；`NpuBaseConfig.as_dict` 249–273 在任何 mode 委托全部嵌套 config；赋值校验机制以[配置边界](torchair_compiler_config_boundaries.md)为准，不重述）。
- [新增来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py)（implementation）：10–60、234–254 窗口读取（发布版对应锚点：`self._value = default` 在 16 行、`value` 属性 32–40、setter 42–48、`NpuBaseConfig.as_dict` 234–254，与主线同语义）。
- 同时对主线五页功能页全文复读：jit_compile（1–28）、oo_level（1–50）、optimization_switch（1–141）、view_optimize（1–39）、tiling_schedule_optimize（1–38）；发布同路径五页未复读，配对以上文既有两版对照结论为准。全部为静态读取，未运行编译、GE 会话或 NPU 实验；「告警不触发」指代码路径不调用 warnings.warn 的静态读数。
