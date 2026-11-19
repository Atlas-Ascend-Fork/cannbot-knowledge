---
type: Guide
title: 实验Triton启动：网格分支、动态尺寸缓存与ABI绑定
description: 按真实优先级保存组合核、recipe、标量归约与逐点网格策略，区分普通和静态启动器的参数绑定。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/launcher_codegen.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/compile_result.py
  role: implementation
created_at: '2026-11-11T07:57:58Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton启动：网格分支、动态尺寸缓存与ABI绑定

## 固定实现与调用关系

本文针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的triton_experimental；[后端加载配置](torch_npu_inductor_config_parsing.md)与实际生成启动器是不同阶段。发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b没有同路径launcher_codegen.py，这只记录该路径差异，不据此断言发布版没有Triton能力。未运行上游代码、生成器、exec、编译器或设备；平台未知，保持draft和空平台。

launcher_codegen.py的三个完整函数负责网格语句与Python源码生成。普通npu_triton_heuristics和static_launcher/compile_result的所列调用段都使用它们，

并传入向量核数量以及由recipe存在和device_props.is_a5共同决定的布尔值。

本卡只审这些调用段，设备检测、recipe生产、kernel ABI与后端选择的外部实现仍独立。

## 按实际优先级选择grid_0

XBLOCK从cfg.kwargs取得，缺省为1；grid_type缺省Grid1D。下表按函数的if/elif顺序解释，满足靠前分支就不再使用后面的分支。

| 分支 | 本地条件与生成行为 |
| --- | --- |
| TE组合核 | te_combo_meta不为None，即使为空字典也进入；grid_0为传入num_cores，不使用recipe或xnumel裁剪。 |
| recipe | recipe为真、is_a5为真且不是TE组合核；把配置中所有名字以BLOCK结尾的值作为字面量写入，再嵌入recipe.lines，以recipe.factors的乘积生成max(1,total_blocks)。不设num_cores上限，也不使用仅按xnumel的缓存。 |
| 未拆分标量归约 | npu_linearize为真、x节点数为0、Grid1D、arg_names含R0_BLOCK且npu_rsplit_partial为假；grid_0为1。后者缺省按arg_names是否含ws_ptr判定，显式元数据会覆盖这个缺省。 |
| 简单一维逐点 | _can_clamp_1d_grid要求显式npu_num_x_nodes为0或1、Grid1D、def_args含xnumel且arg_names不含R0_BLOCK；grid_0=max(1,min(ceil(xnumel/XBLOCK),num_cores))，可使用单槽尺寸缓存。 |
| 非linearize一维 | npu_linearize为假、Grid1D且def_args含xnumel；grid_0=max(1,ceil(xnumel/XBLOCK))，不设num_cores上限，可使用单槽缓存。 |
| 其余 | grid_0直接为num_cores。 |

_can_clamp_1d_grid对缺失npu_num_x_nodes取None，因此缺失元数据不会自动进入简单逐点分支；外层标量归约判断却对同一字段缺省取0。不能把逐点helper的保守处理泛化成所有分支。拆分归约和多维网格也不能套用一维逐点的xnumel裁剪公式；非linearize分支尤其不能擅自添加核数上限，否则可能省掉需要处理的tile。

逐点与非linearize公式都设置下界1，使xnumel为0时不会直接产生grid_0=0。注释解释了一维逐点的空输入mask意图；本函数只生成网格，不能单凭这个下界证明任意自定义kernel都正确处理空Tensor。recipe分支虽然保留至少一个program，也不能因此视作对任意recipe有效性、tile覆盖或设备维度限制的认证。

## 单槽缓存与参数绑定

只有标记可缓存的分支在scope中建立_grid_cache=[-1,0]。生成代码仅比较当前xnumel与上次值；相同就复用grid_0，否则重算并覆盖两个槽。它不是按所有动态维度建立的字典，也不是kernel编译或调优缓存。XBLOCK与num_cores已经写入该启动器的表达式；recipe可能依赖多个尺寸，因此明确绕开这个单键缓存。

_gen_launcher_code在scope中按需补max/min，拼出def launcher(...,stream,...)，插入网格语句，固定grid_1=grid_2=1，再插入调用方指定的call_lines。未传call_lines时才默认生成runner(runner_args)。随后用exec创建函数，并附_expected_positional_count=len(def_args)和_npu_def_args=list(def_args)；这个计数不包含额外的stream形参，也不等同于底层设备ABI参数个数。共享函数不选择普通、静态或fast runner。

bound_names只把scope中已存在的指定名字写成带默认值的形参。普通调用段把runner、慢路径、函数/metadata/hooks、max/min和_grid_cache等作为候选默认绑定；静态调用段不传bound_names，保留全局scope绑定。源码注释说明这是减少主机名称查找的意图，不是已测得的性能收益。

普通调用段在use_fast且fast_args已准备时生成条件调用：runner返回非None才调用slow_runner，其余情况只调用runner。激活fast的前置选择和runner实际实现不在该有界段，不能把所有Triton调用都描述成已走fast路径。

静态make_launcher先按需重载npubin并初始化kernel handles，外层def_args保留launcher_arg_names和额外网格参数，设备runner_args则为grid_0/1/2、stream与kernel.runtime_arg_names。它设置config、runnable、寄存器/共享内存、cache_hash、store_cubin=False及_is_static=True等属性；这些赋值本身不证明设备启动、数值或性能已经验收。排查参数错位时应分别核外层网格参数与runtime参数，而不是把两组名字强制当成相同列表。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/launcher_codegen.py)：1–158；共享生成器完整本地定义。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)：441–477；仅所列调用段，不提升整个模块资格。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/compile_result.py)：157–189；仅所列调用段，不提升整个模块资格。
