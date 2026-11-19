---
type: Guide
title: 集成ACL图生成代码：kernel首跑重建、用户流/事件字典与record/wait和控核改写
description: 解释集成fx2acl转换器生成Python工件的装配顺序、kernel首跑的流与事件重建合同、forward行级改写规则及record/wait与控核调用改写，并核对主线与发布快照等价性。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-12T21:16:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成ACL图生成代码：kernel首跑重建、用户流/事件字典与record/wait和控核改写

本卡绑定集成`python/torchair/_acl_concrete_graph/fx2acl_converter.py`两固定pin：主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`（925行）与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`（857行）。只读源码文本，未执行生成的代码、未创建流/事件/Tensor；平台未知，保持draft、空平台。同名生成代码段在其它命名空间已有结论：独立npugraph_ex包的kernel首跑、用户流/事件字典与scope改写见[cond事件闭环](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)与[值包装元数据](torchair_fx_value_pack_metadata.md)，GE路径的缓存kernel首跑见[GE缓存首跑合同](torchair_ge_cached_kernel_first_run_contract.md)；相同模式不能跨命名空间互推，本卡只补集成ACL路径的本地事实。任务更新与UpdatedNodeInfo生成（主线691–834/发布641–772）、`_codegen_tensor_constant`与`_codegen_init`头部（532–578）、normalize_config、parse_*族分别由[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)、[重捕获与输出克隆](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)、[分组配置序列化](torchair_grouped_config_serialization_and_mode_consumers.md)覆盖，本卡只补其余生成代码段。

## 生成工件的装配顺序（两版相同）

`codegen(extend_config, enable_cache)`（主线164–215/发布154–206）按序拼接：头部import（threading、OrderedDict、`rand_strided`、`assert_size_stride`、`AclGraph`/`AclGraphCacheInfo`、`SerializableGraphModule`、`_npu_create_tagged_event`、`torch_npu`）→`_codegen_update_global_dict()`→tensor常数段（仅`_tensor_constant_dict`非空时）→`fx_forward`→`_codegen_init(extend_config)`→用户流字典段（仅`user_stream_label`非空）→tagged事件字典段（仅`tagged_event_names`非空）→`_codegen_kernel(need_update_tagged_event, need_update_user_stream_label)`→`_codegen_example_input_run()`。源码注释明示“DONT CHANGE class names / import path”——`AclGraph`、`AclGraphCacheInfo`类名与`torchair._acl_concrete_graph.acl_graph`导入路径是缓存工件跨版本加载合同的一部分，改名将破坏既有缓存工件的可加载性；本卡只记录该合同，不验证旧工件。

## kernel首跑合同：一次性重建流与事件

`_codegen_kernel`生成模块级`_is_first_run=True`与`kernel(*args, **kwargs)`：首跑内依次执行（两版生成内容相同，主线641–660/发布594–612，差异仅def行的f-string前缀）：

1. `_update_tagged_event_dict()`（仅当缓存信息含tagged事件名）：从`graph_pass`导入`_GLOBAL_SCOPE_TAG_TO_EVENT`与`_GLOBAL_EVENT_LOCK`，持锁为每个tag新建`torch.npu.Event()`写入全局表——事件对象不随工件序列化，每次加载后由首跑重建，与『集成graph_pass原地化与控核Pass的装配』卡中转换器把tag并入`tagged_event_names`的步骤配对。
2. `_update_user_stream_label_dict()`（仅当含用户流标签）：先裸调用`torch.npu.Stream()`初始化流池，再持`_GLOBAL_USER_TAGGED_STREAM_LOCK`逐tag构造Stream——`user_stream_info`含该tag时用其stream_id/device_index/device_type显式重建，否则新建默认Stream写入`_GLOBAL_USER_TAG_TO_STREAM`。恢复的是Stream对象身份到全局字典，不是捕获时的流对象本身；运行中新建默认流的实际行为未验证。
3. sym输入解包（仅`_all_sym_input_idx`非空，注释“only for cache with symint”）：数字名或非`sympy.Symbol`名跳过。
4. `assert_size_stride`断言：对`_all_meta_tensor_input`逐项生成，`numel()==0`的输入跳过（主线662–672/发布614–623）。

首跑分支结束后每次调用直接`return acl_graph(*args, **kwargs)`；断言只在首跑发生，后续运行不做shape/stride复检。

## `_codegen_init`的缓存装配尾段

`_codegen_init`（主线558–600/发布513–557）把`normalize_config()`结果逐键写入生成代码的`compile_configs`字典；`extend_config`仅当`_aclnn_static_shape_kernel`开启且非空才并入，并生成`_update_static_kernel_cache_dir(path)`把`_aclnn_static_shape_kernel.compile_cache_dir`指向运行时传入路径——与[静态Kernel消费者](torchair_integrated_and_standalone_static_kernel_consumers.md)的模型run包恢复分支配套。随后实例化`AclGraph(fx_forward=forward, config=compile_configs)`并用全字段`AclGraphCacheInfo`（pool/stream/capture_error_mode/num_warmup_iters/fx_graph_name/user_inputs_mapping/unupdated_sym_input_index/updated_ops_param/ops_update_rulers/mutated_user_inputs/tagged_event_names/parameter_user_inputs/user_stream_label/user_stream_info/userinput_ref_with_output）调用`acl_graph.load`。`enable_cache`形参在本函数体没有参与分支。

## forward行级改写与record/wait、控核生成代码

`_codegen_fx_forward`（主线691–790）用正则`def forward\(self[^)]*\):`在GraphModule recompile代码中定位forward体（找不到直接ValueError），随后逐行拼接并按首次命中顺序改写：tensor常数`{k} = self`行→`tensor_constants['k']`；need_updated_ops子串命中→拼接更新代码并保留原行`;`之后的内存释放尾部（`split(';', 1)`）；record/wait与控核子串命中→拼接对应生成代码；流scope进入行→原行+`with torch.npu.stream(_GLOBAL_USER_TAG_TO_STREAM['tag']):`并缩进（优先`do_indent()`、无则`_indent += 1`的版本兼容回退）；流scope退出行→原行+反缩进。无命中行原样保留。子串匹配键为`{node.name} = torch.ops.{node.target}`形式，依赖节点名唯一性。

`_codegen_fx_forward_record_wait`（主线836–855/发布774–792）：`air.record.default`节点→`event_{name} = torch.npu.Event()`加`record(torch.npu.current_stream())`；`air.wait.default`节点→对其`args[0]`列表逐个`event_{wait_node.name}.wait(torch.npu.current_stream())`。这些air节点由同批卡『集成graph_pass原地化与控核Pass的装配』所述的事件闭包/record插入产生——Pass写标记节点、codegen换成运行时调用，是同一条链的两端；wait对不存在的record事件名会在运行期NameError，本层无前置校验（静态读取，未复现）。

`_codegen_fx_forward_core_limit`（主线857–880/发布794–812）：把`replace_core_limit_nodes`插入的FX内建函数节点按`str(node.target)`包含`function current_stream`/`function get_stream_limit`/`function set_stream_limit`改写为真实`torch.npu.*`调用，键名分别为`torch_npu_npu_utils_current_stream`、`torch_npu_npu_npu_config_get_stream_limit`、`torch_npu_npu_npu_config_set_stream_limit`——这些是GraphModule print代码中的内建函数引用文本形态，不是torch_npu符号路径。控核配置/恢复语义见同批卡『集成graph_pass原地化与控核Pass的装配』，本卡不重复。

## 示例入口与闭包变量

`_codegen_example_input_run`（主线882–912/发布814–845，两版逐字节相同）：生成`main()`，对sym输入用`rand_int_sym=2`按`2+idx`赋值构造泛化真值（符号表达式名直接写原名），tensor输入经`rand_strided(shape, stride, device, dtype)`构造，最后`return kernel(全入参)`。`_codegen_update_global_dict`（主线914–925/发布847–857，逐字节相同）：`torch.__version__ > 2.5.1`时用`torch._dynamo.guards._get_closure_vars()`，否则用`CLOSURE_VARS`做`globals().update`，并额外注入`nan`常量。版本比较经`packaging.version.parse`，是生成代码的兼容分支，不是对加载环境的认证。

## 两版等价性与边界

本卡所列全部生成代码段经两pin逐函数归一比较：`_codegen_example_input_run`、`_codegen_update_global_dict`字节相同，其余段仅排版差异（含发布`kernel`定义行多一层f-string、`.keys()`显式迭代、赋值拆行），无行为差异；未发现发布版这些段的主线专属回退。`_codegen_fx_forward`的need_updated_ops/任务更新部分（主线691–834）已由[任务更新规则](torchair_integrated_aclgraph_task_update_rules_and_handoff.md)按主线读取，本卡只消费其行级拼接位置事实。生成代码未执行；流池初始化、事件重建、首跑断言的实际运行行为、旧缓存工件的可加载性均未运行验证；`torch.npu.Stream`/`Event`运行语义属torch_npu仓，本卡未审。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（primary）：152–215（dump尾段与codegen装配）、553–689（_codegen_init、_codegen_user_stream_label_dict、_codegen_update_tagged_event、_codegen_kernel、_codegen_assert_size_stride、_codegen_input）、691–790（_codegen_fx_forward行级改写，任务更新子段为关联卡覆盖内容的上下文重读）、836–925（record_wait、core_limit、example_input_run、update_global_dict）。
- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：154–206（codegen装配）、555–664（init尾段、user_stream、tagged_event、kernel、assert、input）、772–857（record_wait、core_limit、example_input_run、update_global_dict全段）；两版等价性由逐函数去注释/空白归一比较与上述实读锚点共同闭合。
- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/graph_pass.py)（implementation）：576–577（_GLOBAL_SCOPE_TAG_TO_EVENT/_GLOBAL_EVENT_LOCK定义，tagged事件字典段的导入目标）。
