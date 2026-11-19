---
type: Guide
title: TorchAir 配置入口：GE CompilerConfig 与 npugraph_ex options
description: 扩展两类配置入口的版本边界，核对集成赋值、叶子比较、类级options状态与分组序列化前的告警合同。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/compiler_config.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/compiler_config.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/compiler_config.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/aclgraph_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/aclgraph_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/quick_start.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/npugraph_ex.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/api.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/advanced.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/basic.md
  role: constraint
created_at: '2026-11-09T04:38:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchAir 配置入口：GE CompilerConfig 与 npugraph_ex options

## 固定来源

本卡依据主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`，选择 A2/A3 推理；发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的 GE 类定义另列版本证据。类中出现字段只证明该快照配置入口存在，不证明全部后端、产品和参数组合都有效。

## 两个配置对象的职责

GE 路线用 `torchair.CompilerConfig()` 配置 debug、aoe_config、export、dump_config、fusion_config、experimental_config、inference_config、ge_config 等分组，然后在构造 get_npu_backend 时传 compiler_config。主线 GE 类还列有 aclgraph_config、npugraphex_config，mode 默认 max-autotune，枚举包含 reduce-overhead 和 npugraph_ex；不能因此推导它与独立后端配置对象可交换。

独立 npugraph_ex 后端通过 `torch.compile(..., backend="npugraph_ex", options={...})` 传选项，其 CompilerConfig 的 mode 仅允许 npugraph_ex。它直接声明 capture_limit、clone_input/clone_output、static_kernel_compile、force_eager、图池、Pass 和 Dump 等字段；没有 GE 的分组结构。字段和默认值应以所部署的固定版本逐项核对，尤其不要把 debug.run_eagerly 当作 force_eager 的通用别名。

## 定位配置未生效

先记录实际 backend、构造时传参、mode、版本和首次编译前的配置，再检查图、日志及产物。两类配置都出现的自定义 pre/post Pass 仍需核对各后端支持时机和接口。私有 `_vllm_` 字段不因列在类定义中就成为通用稳定调优接口；不要从字段存在推导默认开启或跨版本兼容。

- [获取 GE 后端](../../../apis/torchair/get_npu_backend.md)
- [捕获和回退选项](npugraph_ex_capture_controls.md)
- [Pass 和融合控制](torchair_fx_pass_and_fusion_controls.md)
- [软件栈来源边界](../../../concepts/frameworks/ascend_software_stack_baselines.md)

仅静态审阅，未运行编译或测量配置收益。

## 根安全声明的旧配置摘要不能覆盖实际入口

发布/主线根安全声明保留get_npu_backend、get_compiler、CompilerConfig、dynamo_export和私有格式权重等Python入口简介；这不是每个option最新默认值或整个后端的能力表。graph_dump在发布声明误写dtype、主线改type，且参数说明把custom_decompositions写成单数，均不造配置别名。

其中experimental_config摘要仍写jit_compile="auto"、topology_sorting_strategy="DFS"、separate_atomic_clean=True、static_model_ops_lower_limit为“节点上限”等旧描述；这些值须与具体版本的实际配置/特性页核对，不凭根摘要覆盖本卡GE mode及独立npugraph_ex结构，或将名称lower_limit机械理解为相反方向。支持的接口/字段、默认值和最终Runtime行为是不同证据层次。

安全声明的公开边界只涵盖有文档的Python接口，内部动态库导出与字段可见不自动稳定。根声明缺少的新能力按独立主线页面审阅，不把整个摘要当完整白名单。

## 主线npugraph_ex公开字段的默认值

以下按该固定主线API页列出的字段逐项归组，字段存在不证明任意组合有效；实际实现及独立包版本仍分别核对。

|默认值|字段|
|--|--|
|False|force_eager、clone_output、disable_static_kernel_compile_cache、static_kernel_compile、frozen_parameter、dump_tensor_data、super_kernel_optimize、deadlock_check、force_recapture、unsafe_skip_npugraph_capture_validation|
|True|reuse_graph_pool_in_same_fx、clone_input、remove_noop_ops、remove_cat_ops、inplace_pass、input_inplace_pass、pattern_fusion_pass|
|None|use_graph_pool、post_grad_custom_pre_pass、post_grad_custom_post_pass、super_kernel_optimize_options、super_kernel_debug_options|
|64，合法1..INT64_MAX|capture_limit|
|optimized，候选original/optimized|data_dump_stage|
|./，要求路径存在|data_dump_dir|
|global，候选global/thread_local/relaxed|capture_error_mode|
|npugraph_ex，唯一模式|mode|

post_grad_custom_pre_pass/post_grad_custom_post_pass/use_graph_pool还被加入_fixed_attrs，不从可打印的配置串推导这三者可以任意序列化。类定义同时列_vllm_aclnn_static_kernel_sym_index默认0（范围0..INT64_MAX）与_sym_range默认None，仅记录为私有集成字段，不将它们暴露为通用模型调优入口。发布GE API页的类摘要只列max-autotune；本次新增实现核对发现，两固定版python/torchair/configs/compiler_config.py实际均接受max-autotune、reduce-overhead、npugraph_ex。文档摘要与实现入口分别保留版本证据，不能用摘要删除实际枚举。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/compiler_config.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/compiler_config.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/compiler_config.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md)（constraint）

## 两固定版集成配置的赋值与取值实现

以下补充仅描述两固定提交python/torchair/configs的本地实现；沿用前文文档的A2/A3范围，不据源码新增产品或组合支持，也未新增运行验证。独立npugraph_ex/configs的基类是另一份实现，尤其不能套用其保留Python bool的value语义。

OptionValue构造器直接保存default、optional与_value，不调用setter。__bool__读取原始_value的Python真值；value getter把None保留为None，把str(_value)恰为True/False的值分别转为字符串1/0，其余转str。候选校验只在optional为tuple/list时用成员相等比较，没有严格类型校验；例如0/1可与False/True相等。赋值被接收和实际后端支持分开判断，推荐按公开字段的真实类型传参。

| 包装类 | 赋值检查与返回形态 |
| --- | --- |
| IntRangeValue | isinstance(v,int)且闭区间内；Python bool也是int子类。getter继承字符串形式；None默认可保存，不表示setter也接受None。 |
| IntListValue | 构造时只检查None或list/tuple；setter将None变为空list，检查list/tuple且各项isinstance(int)，保留原list/tuple引用，不复制；getter直接返回_value。 |
| StrOptionValue | 构造和setter仅收str或None；getter仍继承基础字符串转换。 |
| DictOptionValue、CallableValue | 分别要求dict/Callable或None，getter返回原对象，没有深复制或可序列化保证。 |
| FileValue | None可接受；否则检查exists与isfile。 |
| MustExistedPathValue | setter拒绝None，要求exists且isdir；不额外检查读写权限。 |
| MustExistedFileAddr | None可接受，空串先ValueError，其余检查exists、默认.json后缀及isfile。两版空路径错误文字相同，发布用了无插值f字符串。 |
| RegexValue | re.match(regex,v)不匹配时ValueError；没有独立类型检查或额外fullmatch，实际边界依正则。 |
| DeprecatedValue | 默认None，沿用候选值校验并保存replacement；序列化非None值时打印弃用警告，replacement为None时提示不再配置，否则提示替代字段。 |

这些路径类的默认值由基础构造器直接保存，不能仅从字段声明推导构造时已经检查文件系统。

NpuBaseConfig.__init__只收集当时实例__dict__内的OptionValue/NpuBaseConfig字段为_fixed_attrs。其后给不存在的固定字段赋值会报错；已有OptionValue字段的赋值委托value setter，已有其他固定字段直接替换，没有递归类型检查或复制。根CompilerConfig另外追加两项自定义Pass名。_AclGraphConfig仅声明use_custom_pool=None，_NpuGraphExConfig也是普通类，两者不属于上述两种类型，因此不进入根_fixed_attrs，也不由根as_dict递归。嵌套修改use_custom_pool和直接替换根的aclgraph_config是不同操作。

基类as_dict按实例字段插入顺序遍历，只处理_fixed_attrs：非None OptionValue值进入local，子配置返回的local/global以update合并到同一级键。后处理的重复键覆盖先前值；并非带组名前缀的完整对象快照。CompilerConfig传mode.value给子配置，末尾删除两项自定义Pass，不把callable发送为这两个字符串选项。逐组转换和直接消费者见[序列化及模式](torchair_grouped_config_serialization_and_mode_consumers.md)。

## 配置引用和相等比较的局限

本次核对主线get_npu_backend返回绑定原compiler_config的partial；get_compiler把原对象交给_NpuFxCompiler，后者保存同一引用。_gen_compiled_gm的deepcopy针对GraphModule，不能据此断言配置已深复制。只读dict也不能替代隔离配置对象；配置构造后何时修改会影响哪次编译，仍需按首次调用和缓存路径核对。

CompilerConfig.__eq__先限制other为CompilerConfig，再将_get_all_leaf_properties所得叶子字典比较。该helper用显式栈、vars(obj).copy()浅复制各层属性，没有生成独立配置快照；遇到无vars或空属性对象作为叶子，带子属性对象继续下钻，普通字段值None跳过，叶子若有value属性才取它。它也会遍历包装器私有default/optional/_value及_fixed_attrs等内部属性。普通npugraphex_config实例没有实例字段时按对象叶子参与比较；不能将这个__eq__理解为两个配置的可打印选项相等、稳定内容hash或任意循环对象比较保证。

## 集成options映射的状态与失败顺序

两版_NpuGraphExConfig声明相同的类级默认值及23项映射。False默认项为force_eager、clone_output、static_kernel_compile、super_kernel_optimize、frozen_parameter、dump_tensor_data；True默认项为reuse_graph_pool_in_same_fx、clone_input、remove_noop_ops、remove_cat_ops、inplace_pass、input_inplace_pass、pattern_fusion_pass；use_graph_pool、两个Pass、两个super_kernel字典、私有sym_range默认None；capture_limit=64，data_dump_stage=optimized，data_dump_dir=./，私有sym_index=0。这些是集成类初值，不能把前文独立API页中的额外字段补进白名单。

| 集成options字段 | 分组目标 |
| --- | --- |
| static_kernel_compile、super_kernel_optimize、super_kernel_optimize_options、super_kernel_debug_options | experimental_config.aclgraph下分别为_aclnn_static_shape_kernel、_super_kernel_optimize及两个同名私有字典字段。 |
| _vllm_aclnn_static_kernel_sym_index、_vllm_aclnn_static_kernel_sym_range | experimental_config.aclgraph._aclnn_static_shape_kernel_sym_index、_aclnn_static_shape_kernel_sym_value_range。 |
| inplace_pass、input_inplace_pass、reuse_graph_pool_in_same_fx | 分别反向映射debug.aclgraph.disable_reinplace_inplaceable_ops_pass、disable_reinplace_input_mutated_ops_pass、disable_mempool_reuse_in_same_fx。 |
| remove_noop_ops、pattern_fusion_pass、frozen_parameter | experimental_config对应同名字段。 |
| remove_cat_ops、clone_input | debug.aclgraph对应同名字段。 |
| force_eager、clone_output、capture_limit | debug.run_eagerly、debug.aclgraph.enable_output_clone、debug.aclgraph.static_capture_size_limit。 |
| post_grad_custom_pre_pass、post_grad_custom_post_pass | 根配置同名字段。 |
| use_graph_pool | aclgraph_config.use_custom_pool。 |
| dump_tensor_data、data_dump_stage、data_dump_dir | dump_config.enable_dump、data_dump_stage、dump_path。 |

invert_bool只反转真实bool及整数0/1，其余原样交下游setter。_process_kwargs_options逐项先查白名单，再setattr到_NpuGraphExConfig类本身，然后做转换、按点路径getattr并给实际目标赋值。目标校验失败时类级赋值已经发生；前面已成功的选项也没有局部事务回滚。其classmethod as_dict遍历类__dict__中的映射键，返回类级原始值，不读取某个CompilerConfig分组的最终值或实例覆盖。不能把它当每次新建CompilerConfig就会自动清零的独立状态。

## 支持检查只产生有限告警

两版_check_config_support把vars叶子展开，max-autotune用GE排除表，其他mode用捕获排除表；非空警告只在max-autotune/reduce-overhead发UserWarning，reduce-overhead另发弃用警告。npugraph_ex没有因此获得完整支持认证。全局warning过滤设once也不是严格配置验证；本地函数没有按这张排除表拒绝编译。

_get_warn_config用raw键值or对应._value键取值，再检查非None及列表条件；空列表表示任意非None值，非空列表用成员比较。直接raw叶子为假值而._value不存在时，or可能使其变成None而不进入警告；标准包装值须依实际展开键判断。

下表为完整两版排除条件，值均描述本地告警触发条件，不定义全套后端能力。

| GE路线检查字段 | 触发值 |
| --- | --- |
| debug.aclgraph.disable_reinplace_input_mutated_ops_pass | [True] |
| experimental_config.aclgraph._aclnn_static_shape_kernel | [True] |
| experimental_config.aclgraph._aclnn_static_shape_kernel_build_dir | 任意非None |
| debug.aclgraph.clone_input | [False] |
| debug.aclgraph.disable_reinplace_inplaceable_ops_pass | [True] |

| 捕获路线检查字段 | 触发值 |
| --- | --- |
| inference_config.dynamic_gears_merge_policy | ['product'] |
| debug.fx_summary.type | ['csv'] |
| dump_config.enable_dump | [True] |
| ge_config.export_compile_stat | ['1', '0'] |
| export.experimental.auto_atc_config_generated | [True] |
| export.experimental.enable_record_nn_module_stack | [True] |
| ge_config.enable_single_stream | [True] |
| ge_config.oo_level | ['O1'] |
| ge_config.oo_constant_folding | [True, False] |
| ge_config.oo_dead_code_elimination | [True, False] |
| experimental_config.topology_sorting_strategy | ['BFS', 'RDFS', 'StableRDFS'] |
| experimental_config.cc_parallel_enable | [True] |
| experimental_config.enable_ref_data | [True] |
| experimental_config.tiling_schedule_optimize | [True] |
| experimental_config.enable_view_optimize | [False, True] |
| fusion_config.fusion_switch_file | 任意非None |
| experimental_config.static_model_ops_lower_limit | 任意非None |
| ge_config.aicore_num | 任意非None |
| ge_config.optimization_switch | 任意非None |
| ge_config.multistream_parallel_mode（仅main；release无此项） | 任意非None |

本次完整审阅的是本地配置定义与上述主线入口范围；两版配置的AST相同部分复用审阅，全部实质差异单列。文件存在、静态比较与Contract通过都不替代实际后端、产品或模型验证。

## 配置实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py)（implementation）：1–273。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py)（implementation）：1–254。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/compiler_config.py)（implementation）：1–165。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/compiler_config.py)（implementation）：1–158。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/aclgraph_config.py)（implementation）：1–15。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/aclgraph_config.py)（implementation）：1–15。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/npugraphex_config.py)（implementation）：1–123。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/npugraphex_config.py)（implementation）：1–122。
- [固定实现 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：651–654, 745–779, 804–820, 995–1064。



## 主线API页字段清单滞后独立包实现

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的 npugraph_ex API 页（api/npugraph_ex/compiler_config.md，发布快照无此页）以类源码片段罗列独立包 CompilerConfig，但比 `npugraph_ex/npugraph_ex/configs/compiler_config.py` 少两个字段：`static_kernel_compile_group`（第 41 行 StrOptionValue(None)）与 `record_statistics_debug_info`（第 63 行 OptionValue(False,[True,False])）。前文「主线npugraph_ex公开字段的默认值」按该 API 页逐项归组，同样漏列这两项；按实现补入：static_kernel_compile_group 供静态 Kernel 编译复用用户 Gloo 组——显式组要求 dist 已初始化、组名为非空字符串、解析出的组为包含当前 rank 的 Gloo 后端，任一不满足即 ValueError（static_kernel.py 41–49）；未显式提供时自动建本地 Gloo 组且每次编译后销毁，显式组归属调用方、不被销毁（54–58）；as_dict 仅在其值非 None 时写出该键（compiler_config.py 113–114），因此配置串缺席不代表该路径未启用过。record_statistics_debug_info 默认 False，开启后编译器在输入/输出 debug 日志中追加 min/max/norm/mean 统计（npu_fx_compiler.py `_summary` 296–302、调用点 607/616），属调试信息量开关、不改变编译结果。字段存在不证明任意组合有效，组合行为仍按静态 Kernel 与统计日志实现核对。

文档树自身的导航页不承载承诺：两固定版 `npugraph_ex.md`、`api/api.md`、`advanced/advanced.md`、`basic/basic.md` 均为单行标题页，无承诺-实现配对差异。发布快照该文档树缺少 superkernel/cond/deterministic（advanced 与 api/scope 各页）、dfx/deadlock_check、basic/force_recapture、unsafe_skip_npugraph_capture_validation、capture_error_mode 及 api/npugraph_ex/compiler_config 页，quick_start 功能表相应少行；而发布配置层仍接受 super_kernel_optimize 及 options/debug 两字典并映射 `experimental_config.aclgraph._super_kernel_optimize`（npugraphex_config.py 14–16、39–41）。即发布实现存在 SuperKernel 开关但 npugraph_ex 文档无对应功能页，配置可用性与文档页集合独立成立；各主线性功能的发布缺席已由对应主题卡记录，不在此重复。

- [静态 Kernel 消费者](torchair_integrated_and_standalone_static_kernel_consumers.md)

## 补充来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）：31–70 类字段区、102–135 as_dict。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py)（implementation）：41–58 组解析与释放、535 显式组分支。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：296–302、607、616。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py)（implementation）：14–16、39–41。
- [固定约束 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/quick_start.md)（constraint）：1–160 全文；功能表 61–97 与两版文档页集合 diff。
- [固定约束 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/npugraph_ex.md)（constraint）：单行标题页全文。
- [固定约束 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/api.md)（constraint）：单行标题页全文。
- [固定约束 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/advanced.md)（constraint）：单行标题页全文。
- [固定约束 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/basic.md)（constraint）：单行标题页全文。
