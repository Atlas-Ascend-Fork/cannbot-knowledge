---
type: Guide
title: 实验Triton后端激活：lowering保留、显式回退与全局配置
description: 区分包导入与激活、生成/保留/显式回退三类列表、Bernoulli图捕获门槛、后置索引重绑及配置副作用。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/overrides.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering_override_list.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering_fallback_list.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_template_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/ir.py
  role: implementation
created_at: '2026-11-11T08:35:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton后端激活：lowering保留、显式回退与全局配置

## 固定的注册层，不是全算子能力表

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf实验Triton的包入口、overrides及两张完整注册列表，并补lowering中实际批量注册、后置重绑及index_put片段。没有导入/激活后端、修改配置或环境、执行lowering、启动设备或运行性能实验；平台未知，保持draft和空平台。

GENERATE_LIST表示不被本轮批量回退覆盖，KEEP_UPSTREAM_LOWERING表示保留已有专门lowering，EXPLICIT_FALLBACK_LIST则为批量扫描无法发现的项显式注册。名字出现在列表不证明设备代码生成成功、数值/梯度正确或所有dtype/shape可用；外部decomposition、原生算子和上游lowering仍独立。

## 包导入与_activate分别做什么

实验包顶层导入config与device.get_current_raw_stream并定义_activate，不在包入口直接调用_activate。_activate没有本地完成标志或回滚机制；重复选择后端是否被外层loader拦截按[后端配置与加载](torch_npu_inductor_config_parsing.md)的实际生命周期另核，不能把它作为任意反复调用都幂等的公共API。

实际顺序先导入heuristics与overrides，注册NPU backend，应用共享补丁并把共享select_algorithm.NPUTritonKernel换为实验kernel；再patch FlexAttention并改其设备校验函数，将layout_optimization和split_reductions设False。随后设置调试日志、应用overrides，导入模板heuristics，再注册device op overrides、批量fallback/log-softmax fallback、实验FlexAttention及device interface，最后调用enable_mspti_autotune。

overrides模块被导入时就把上游inductor_config.size_asserts=False，这与apply_npu_overrides函数调用是不同时间点。activation里对共享对象/配置的写入没有在本地用finally自动恢复；注释中的“物理隔离”不能解释为完全没有全局影响。注释把decomposition/dispatcher覆盖安排在外部loader的先行阶段，apply_npu_overrides本身不完成这些工作；外部真实实现与失败行为另核。

_route_worker_logs_for_debug只有debug开启才把torch._inductor logger设DEBUG；环境变量未设置时才关worker_suppress_logging，WORKER_LOGPATH为空时才用config.worker_log_path。它不是无条件覆盖所有用户日志设置。mspti准备和真实计时门槛见[调优计时与输入隔离](torch_npu_experimental_triton_autotune_timing_and_input_isolation.md)。

## 三类列表由真实扫描条件解释

批量注册先把GENERATE_LIST中的packet及其所有overload展开成gen_set；KEEP列表同样展开。扫描已有lowerings时先跳过keep_set，只有不在decompositions也不在gen_set且属于OpOverloadPacket/OpOverload/HigherOrderOperator的项，才make_fallback并记入FALLBACK_LIST。它不会仅凭“没在生成列表”就遍历整个torch.ops并找到所有未注册算子。

| 列表 | 固定实现中的要点 |
| --- | --- |
| GENERATE_LIST | 包含逐点、shape/view、归约、复制/可变、mm/bmm/addmm及卷积等packet。列表有重复项，gen_set会去重；A5条件分支实际追加空列表，不能由该注释声称新增了间接访存算子。 |
| KEEP_UPSTREAM_LOWERING | 保留control_deps、条件存在的assert族、index_put/index_put_、_local_scalar_dense；_inductor_test.realize存在才追加。这里也保护本模块的自定义index_put注册，名称并不意味着这些项都必然是未经改动的上游函数。 |
| EXPLICIT_FALLBACK_LIST | 具体列出reflection_pad2d及反向、bilinear2d及反向、nearest1d/3d backward、_unique/_unique2的default/out、grid_sampler_3d及反向的default/out，以及npu_gather_backward、私有dropout前/反向。每项原样make_fallback并记录，不由此认证原生内核完整合同。 |

view/as_strided/alias/detach等保留项表达布局与变更语义的意图；不能把它们全部换成物化extern后仍宣称原别名关系自然保持。control_deps、assert及realize也有专门IR语义，KEEP只是防止这次generic fallback覆盖，不代替外部实现审阅。

FALLBACK_LIST是模块级列表，所列注册函数直接append，没有在每次调用前清空；它不是唯一去重后的已验收算子清单，也不能按长度推导实际编译图中fallback节点数。

## Bernoulli的图捕获限制与后置index重绑

批量注册最后对列出的bernoulli/bernoulli_五个overload取已有lowering；不存在就略过，存在则套一层函数。调用这个wrapper时，只有V.graph.disable_cudagraphs_reason仍为None才写入“缺graph-safe seed/offset ABI”的理由，然后仍调用原lowering。它设置的是整张编译图的捕获禁用原因，不是在这里把整张图退成Eager或关闭Inductor编译；也不把注释的RNG序列一致性当成本次运行证明。

文件末尾先把原批量注册函数保存到_orig_npu_inductor_fallbacks，再用同名函数包装：先执行原扫描，再overwrite aten._unsafe_index与aten.index.Tensor为本模块实现。只读第一个同名def会漏掉实际对外绑定。相关index_select改写的全部形状/广播门槛不在本卡展开，不由后置重绑推导所有高级索引都能被改写。

index_put的单独实现先clone目标再把values转为目标dtype，交外部index_put_fallback；原地index_put_直接使用self，同样先转换values。两者均用type_promotion_kind=None注册，KEEP避免批量扫描将其覆盖成缺少转换的generic fallback。转换存在不等于任意值、重复索引或accumulate精度都已验收。

## softmax路由与其余覆盖的边界

_register_softmax_aclnn_fallback受实验config.log_softmax_aclnn_fallback控制，对aten.log_softmax及_log_softmax两个packet，以及各自存在时的default，分别从decompositions、lowerings删除后make_fallback。这里不枚举全部out/反向overload，也不追加前述FALLBACK_LIST。safe_softmax与普通softmax宽度路由在外部decomposition入口，不能把此函数概括成“所有softmax一律回原生”。

apply_npu_overrides按顺序重绑逐点autotune门控、尝试关闭递归dict-tag guards、关闭pad-mm形状padding、处理addmm融合、安装stride-order/Max1/整数往返Pass，再调用codegen补丁。每个被调函数的完整实现仍按各自范围解释，整数往返的数值边界见[FX整数往返消除](torch_npu_experimental_triton_integer_roundtrip_elision_scope.md)。

逐点autotune门控仅当实验heuristics模块已在sys.modules时才重绑，替换函数返回not inductor_meta.get('autotune_pointwise',True)，没有再检查全局deterministic开关。这个局部门控不认证所有kernel或RNG的确定性。recursive-dict开关受实验config控制，导入Dynamo config任意Exception时返回，有对应属性才设False；pad-mm开关受配置控制，实际只把shape_padding设False，其他Pass不能据此宣称全关。

排查后端选择与性能时，应分别保留loader选择、activation完成位置、有效全局配置、具体overload、decomposition命中、gen/keep/explicit分类、后置重绑和图捕获原因。列表、flags与注册日志只描述路由，设备支持、数值及吞吐应由相应实现和最终验证说明。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/__init__.py)：1–121；完整本地入口/列表模块，被调外部实现另计。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/overrides.py)：1–104；完整本地入口/列表模块，被调外部实现另计。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering_override_list.py)：1–183；完整本地入口/列表模块，被调外部实现另计。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering_fallback_list.py)：1–61；完整本地入口/列表模块，被调外部实现另计。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py)：1–161、365–389、901–914；仅所列有界注册与lowering块。

## GEMM模板候选与NPU benchmark注册

本节补完整npu_template_heuristics.py的117行，对应前文_activate中的模块导入。模块顶层先尝试torch._inductor.heuristics.registry/template.triton的导入；只有ModuleNotFoundError才换template_heuristics两个路径，并不是任意ImportError或缺少某个导入名字都走兼容分支。两套外部类、装饰注册器和模板正文未在本卡展开，没有因注释的Torch版本范围就认证当前环境必然配套。

NPUConfigHeuristic先调用BaseConfigHeuristic.__init__，将mm_configs设为6个GemmConfig参数元组：

```text
(32,32,32,1,4)
(64,64,32,2,4)
(64,64,64,2,4)
(128,64,32,2,4)
(64,128,32,2,4)
(128,128,32,2,4)
```

exhaustive_configs直接引用同一mm_configs列表，不是额外生成的大范围穷举池。这里保存构造实参，不代替外部GemmConfig字段协议、tile支持和完整资源检查；注释中的“小且保守”、192KB和设备测时不是本次编译或性能验收。

NPUMMTemplateConfigHeuristic通过两个装饰器分别注册mm_template.uid/bmm_template.uid与device_type=npu，并继承MMTemplateConfigMixin。NPUAddMMTemplateConfigHeuristic另以op_name=addmm和baddbmm分别登记，并继承AddMMConfigMixin及前一类；不能把普通mm/bmm的注册自动视作覆盖带bias的两个op_name。bias/epilogue如何由外部mixin调整，以及max_autotune/max_autotune_gemm的实际should_run门槛，都仍按继承实现另核，不由装饰器存在宣称默认编译已选用Triton GEMM。

模块还以register_benchmarker('npu',_default_npu_bench,override=True)登记benchmark路由。shim使用kw.setdefault('device_type','npu')，转交self.benchmark_gpu并传warmup/rep；只在缺device_type键时补NPU，显式给None或其他值不会被这行覆盖。它没有自行计时、选择最佳配置或验证输入，外部Benchmarker和候选select_algorithm仍独立。

这三类作用——MM/BMM候选、按op_name登记的AddMM/BAddBMM候选、NPU benchmark dispatch——不能只按docstring开头“两项注册”的计数概括。导入命中sys.modules可能避免再次执行模块正文，但外部registry的全局生命周期、重复激活和失败回滚未在这里统一解决。排查GEMM未调优或仅见ATen extern候选时，应分别核注册键/mixin、有效调优开关、实际候选、benchmark device_type和最终编译/数值/计时，不能引用注释中的ATen胜负或提速倍数作为当前模型结论。

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_template_heuristics.py)：1–117；完整本地模块，外部注册器、mixin、模板与测时实现另计。

## IR注册的导入副作用与stride谓词

本节补ir.py完整64行，填充前文_install_safe_stride_order的本地实现。该模块同时有导入即执行的三处handler赋值，以及需要调用_install_safe_stride_order才安装的Layout方法，不能把它们都概括成一个完成标志控制的注册。

_install_safe_stride_order先看Layout上的_npu_safe_stride_order_installed；truthy就早返。新静态方法依序用V.graph.sizevars.guard_or_false检查right==0、left==0、left>=right，分别返回True、False、True。仍未返回时构造left%right==0；若表达式遍历中存在负整数指数的SymPy Pow就False，否则交guard_or_false检查整除条件。最后把该静态方法写到Layout._stride_expr_ge_or_false并置marker。

这不是任意数值的通用>=比较器，最后还有整除判据；负整幂检查也不等于独立验证所有符号表达式/除数都合法。这里没有给整个计算包总except或回滚，外部guard_or_false的guard生成与错误行为未在此展开，不能拿其它模块statically_known谓词的合同替代。

模块顶层把OpsHandler.index_select设为调用self._default('index_select',(src_name,weight_index,indirect_var,set_indirect,bound),{})的wrapper；把dtype传播的同名静态方法设为V.graph.get_dtype(src_name)，shape传播设为getattr(indirect_var,'shape',None)。两个传播函数不在这里消费weight_index/set_indirect/bound做完整索引合法性检查，shape缺失仍可返回None；这也不是新增一个公共aten设备kernel或自动实现所有索引计算。

这些顶层赋值不由Layout的安装marker逐项保护，也没有保存旧handler供本地撤销。实际device支持、bound与间接索引语义需结合外部handler和生成器核对；本次没有调用guard、传播handler、生成代码或设备实验，旧平台与verified保持不变。

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/ir.py)：1–64；完整本地IR注册模块，外部guard/handler协议另计。
