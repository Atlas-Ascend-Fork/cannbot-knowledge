---
type: Guide
title: TorchAir FX Pass 与融合控制：变换层次及生效证据
description: 区分自定义 AOT 后 Pass、GE 融合文件与 npugraph_ex Pattern 替换，避免误解 ALL 关闭语义。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/post_grad_custom_pass.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/fusion_switch_file.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/pattern_fusion_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/pattern_fusion_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/post_grad_custom_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/optimization_switch.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/post_grad_custom_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/pattern_fusion_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/pattern_fusion_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/graph_transform_observer.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/fusion_switch_file.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/post_grad_custom_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py
  role: implementation
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir FX Pass 与融合控制：变换层次及生效证据

## 版本与范围

依据发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013，选择 A2/A3 推理。Pass 注册存在不表示任意模型形状或融合算子均可用；仅静态审阅。

## 自定义 FX Pass

函数签名 _(gm,example_inputs,config) -> None，gm 是 AOT 后 GraphModule，example_inputs 通常是 FakeTensor。Pass 原地修改 gm，返回值被忽略；无法保证等价时必须报错。config.post_grad_custom_pre_pass 在内置 Pass 前执行，post_grad_custom_post_pass 在其后执行，按所需阶段注册，不需要为了使用一个阶段同时填写两者。

如果插入多流 scope/record/wait，要同时保证图依赖与同步次序；改图后的节点存在不代表执行时序正确。

## GE 融合文件

config.fusion_config.fusion_switch_file 指向实际可访问的配置文件，GraphFusion 与 UBFusion 分别控制。ALL:off 只关闭可关闭的规则，部分功能必需规则仍生效；单规则配置优先于 ALL。通过 ge.fusionSwitchFile 日志确认读到了文件，再看 fusion_result.json：match_times 是匹配次数，effect_times 才是生效次数。

## npugraph_ex Pattern

options.pattern_fusion_pass 默认 True，作用于内置和自定义 Pattern 替换。要求融合输出仍被使用、被消除的中间值没有其他消费者；shape 改变可能使 npu_transpose_batchmatmul 的匹配失效并引发 FX 重编译。框架有匹配规则不证明当前安装的 OpPlugin、硬件支持对应融合算子的所有参数，应继续核验接口契约。

## 验证

保存改图前后 FX/GE 结构，核对目标节点、融合计数、输出与跨流时序，再比较端到端开销。关闭融合用于定位，不据此认为所有优化都已关闭。

- [多流依赖](graph_multistream_dependencies.md)
- [转置矩阵乘接口](../../../apis/torch_npu/npu_transpose_batchmatmul.md)


## 发布版 npugraph_ex 自定义 Pass 与 GE Pattern

npugraph_ex 用 options.post_grad_custom_pre_pass/post_grad_custom_post_pass 注册，函数同样原地修改 AOT 后 gm、忽略返回值；它们与 GE CompilerConfig 的配置入口不同。通过 backend="npugraph_ex" 的 Debug 产物核对节点和时序，不由低层 compile_fx 推导完整能力继承。

GE 的 config.experimental_config.pattern_fusion_pass 默认 True，要求 PyTorch≥2.6；规则集不同于 npugraph_ex，来源明确若干转置 matmul 与 AddRMSNormQuant 替换在 max-autotune 不生效。[register_replacement 契约](../../../apis/torchair/register_replacement.md)给出两后端参数和版本门槛。optimization_switch 的同规则配置优先于 fusion_switch_file，详见[GE 编译调优](ge_compile_optimization_controls.md)。

## 主线Pass顺序与缓存身份

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的GE _optimize_fx顺序为：custom pre → 可选Noop消除 → recover_view_inplace → max-autotune下的符号输入优化 → 可选Pattern融合 → view转reshape → custom post。post看到的是内置变换后的图，不能按原始节点名假定仍有相同中间结构。

GraphTransformObserver以(gm, example_inputs, config)调用Pass，调用方不把Pass返回值设为新gm；应按契约原地修改。npugraph_ex文档同样用options的pre/post配置，不把GE配置对象直接传入另一后端。

当前缓存配置串会为pre/post加入函数反汇编的摘要；反汇编不等于闭包或全局变量运行时内容被逐项纳入该参数摘要。遇到不支持反汇编的可调用对象，代码使用固定custom_pass摘要。依赖外部配置时，不能只凭函数码或此摘要就断言完整缓存身份已覆盖变化，应检查实际缓存与重新编译产物；这只是该摘要范围的静态结论，不宣称已复现完整缓存碰撞。

主线npugraph_ex默认规则页列七类融合，包括直接/flatten的AddRMSNorm动态量化、两种cast、三维matmul/transpose及AddRMSNorm静态量化；GE页只展示其中三类并仍列max-autotune的部分限制。不能将两个页面的规则集直接视为完全一致。需保留中间值的消费者、尾轴32字节对齐及融合算子自身的约束；shape改变可能使转置matmul不再匹配并触发重编译。

验证应同时看具体阶段的FX图、融合后的算子接口条件、存储语义与稳态性能，不能把注册成功或pattern_fusion_pass=True当作规则已命中。主线总览范围包括950，但不回推发布段的旧配置或算子支持。

## 主线GE融合文件的对应证据

主线fusion_switch_file页仍保留GraphFusion/UBFusion分别配置、单规则优先于ALL、ALL:off不关闭全部必需规则的约束。图融合改写图结构，UB融合减少中间数据在UB与DDR间往返，两种优化的机制与计数不能互换。系统规则通常默认开启，个别默认关闭以其特殊说明为准；不能把一份示例配置里的规则名当作所有软件栈均存在的名单。

先用TNG_LOG_LEVEL=0日志核对ge.fusionSwitchFile读取到预期文件，再按session_and_graph_id比较match_times/effect_times及UB的repository_hit_times。日志只证明配置被读到，计数只证明对应编译过程，不证明当前输入获得了性能收益或所有调优已关闭。

## 主线GE自定义Pass示例与阶段选择

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的GE post_grad_custom_pass页与发布页接口相同：原地修改AOT后的gm，返回值忽略，pre/post按需要选择，不必为了使用一个阶段同时配置两者。示例在mm前进入stream_1、abs后record并退出、sub前wait；它假定匹配节点和record定义顺序存在，不能不检查图结构就用于多个mm/abs/sub、分支或不同拓扑。FX中插入四种节点只证明改图，最终分流和依赖顺序仍需GE图及Profiler核对。

主线示例已把prof.step()放入Profiler上下文，发布示例在上下文外；不直接复制旧缩进来验收采样。示例用AutomaticUbFusion:off帮助观察分流，这是诊断配置，不代表生产必须关闭融合或关闭全部图优化。

[Noop消除与别名约束](graph_noop_cat_and_reinplace_passes.md)另列主线实现边界，本节不以减少节点数代替时序和数值验收。

## 独立包与TorchAir Pattern管理器的实际差别

固定主线两处Pattern管理器均先按call_function节点stream_label拒绝跨流匹配，再执行用户extra_check。独立npugraph_ex还增加deterministic_scope_level与core_limit_scope一致性检查，普通python/torchair版本没有相同两项检查；不能由同名register_replacement或一份设计表推定两路守卫完全相同。

两处pattern_util都直接与torch.__version__比较门槛，实际排序取决于该对象的比较实现；这里未导入torch，不据表达式宣称存在2.14的字典序误判。普通TorchAir在max-autotune下不注册转置batchmatmul/AddRMSNorm静态量化两类，独立包此处没有同一config.mode分支。候选规则注册、作用域校验、实际替换和算子本身支持仍逐层核对。

## 两后端完整文档规则与输出重排

|输入模式|融合后算子与保留条件|
|--|--|
|AddRMSNorm→DynamicQuant，带smooth_scales|npu_add_rms_norm_dynamic_quant；保留量化输出、scale及仍被使用的残差|
|AddRMSNorm→flatten(0,1)→不带smooth_scales的DynamicQuant，scaleOut再view(-1,1)|同一融合算子，量化输出flatten及scale的view仍需保持输出规格|
|AddRMSNorm取尾维h→view(-1,h)→FP32转换|npu_add_rms_norm_cast；融合后FP32输出仍可需要view，不能以“自动处理”删去输出形状约束|
|AddRMSNorm直接FP32转换|npu_add_rms_norm_cast；此直接模式在npugraph_ex页另列|
|三维matmul→transpose(0,1)/(1,0)|npu_transpose_batchmatmul；shape变化可能使匹配失效并重编译|
|输入transpose→三维matmul→输出transpose|前置transpose变体；仍只列(0,1)/(1,0)|
|AddRMSNorm→Quantize|npu_add_rms_norm_quant；AddRMSNorm输入尾轴32B对齐并满足融合算子自身限制|

前3行是GE页展示的三类，npugraph_ex页列全部7类；GE还明确转置batchmatmul与静态量化融合在max-autotune不生效。图示省略或重排输出不能代替准确算子Schema，例如npugraph_ex直接动态量化图没有画出融合侧smooth_scale输入，不据此删除参数。epsilon等可选属性和残差消费者也须在替换中保留。

npugraph_ex自定义Pass发布页用torch.ops.air的scope_enter/exit/record/wait，主线改为torch.ops.npugraph_ex；不得无条件互作别名。该示例只覆盖单组mm/abs/sub，record定义顺序、scope配对和多匹配图必须另查。主线将prof.step置于采集上下文，查看Pass后图与真实同步关系分别验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/post_grad_custom_pass.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/fusion_switch_file.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/pattern_fusion_pass.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/pattern_fusion_pass.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/post_grad_custom_pass.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/optimization_switch.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/post_grad_custom_pass.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/pattern_fusion_pass.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/pattern_fusion_pass.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/graph_transform_observer.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/fusion_switch_file.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/post_grad_custom_pass.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/design_principles_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py)（implementation）
