---
type: Guide
title: 静态Kernel编译的两条实现：后端路由、dump与去重边界
description: 区分集成TorchAir与独立npugraph_ex的实际接线、Eager或捕获式dump、选项映射和编译前去重，避免跨路径套用缓存合同。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/static_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/dynamo/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/dump_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/aclgraph_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py
  role: implementation
created_at: '2026-11-10T14:48:13Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 静态Kernel编译的两条实现：后端路由、dump与去重边界

本卡绑定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`，比较`python/torchair/`集成实现与`npugraph_ex/npugraph_ex/`独立实现，并核对发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的集成路径。TorchNPU入口另绑定主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`；这里只证明所列导入和消费者，不据此认证任意跨仓安装组合。整卡平台未知，保持draft、空平台；未导入上游或执行FX、捕获、编译、run包安装及缓存反序列化。

## 先确定对象来自哪个命名空间

[后端职责](../../../concepts/frameworks/torchair_backend_boundaries.md)已区分GE与捕获；本卡进一步区分两份捕获实现。相同的mode字符串和函数名不能决定实际文件。

| 所读入口 | 实际调用路径 |
| --- | --- |
| TorchNPU两版的`backend="npugraph_ex"`注册路径 | `_get_npugraph_ex_backend`放入惰性模块并返回`_exec`；`_exec`导入`npugraph_ex`，创建该包的CompilerConfig并调用该包get_npu_backend。它没有在此转换为torchair.get_npu_backend。主线还提供惰性setup后的同名entrypoint。 |
| TorchAir两版`get_npu_backend`返回的callable，配置mode为reduce-overhead或npugraph_ex | `_npu_backend`处理选项，经自己的编译器创建`torchair._acl_concrete_graph.fx2acl_converter.AclConcreteGraph`；该类导入并构造`torchair._acl_concrete_graph.acl_graph.AclGraph`。所读主线生成代码也保留这个import路径。 |
| 固定主线独立包`npugraph_ex.get_npu_backend` | 包入口重导出自己的编译器；它创建`npugraph_ex._acl_concrete_graph.fx2acl_converter.AclConcreteGraph`。不能只因上游调用来自TorchNPU，就把它归入同仓python/torchair实现。 |

TorchNPU惰性模块随后使用包内相对导入；实际wheel内容、来源版本与配套仍需单独核对。这里没有将两个仓库主线强行配对，也没有把发布独立包的所有内部逻辑当成主线实现。

## static_kernel_compile映射到不同消费者

两版集成_NpuGraphExConfig把static_kernel_compile映射到`experimental_config.aclgraph._aclnn_static_shape_kernel`。其options白名单来自完整OPTIONS_TO_CONFIG_MAP；所读表未接受`static_kernel_compile_group`和`disable_static_kernel_compile_cache`这两个名字，传入会触发该处理函数的ValueError。不能把独立包公开的两个配置直接塞进集成路径。

主线独立CompilerConfig则有static_kernel_compile、static_kernel_compile_group及disable_static_kernel_compile_cache；as_dict分别输出对应项。使用条件和Gloo生命周期复用[静态编译配置](../../../optimizations/rules/npugraph_ex_static_kernel_compile.md)及[独立包设计边界](npugraph_ex_standalone_design_contracts.md)，本卡不扩展产品支持。

两版集成AclGraph在首次准备中先预热并逐轮同步，随后按_aclnn_static_shape_kernel调用本命名空间的compile_static_kernel。通过环境检查后，集成函数只有use_cache_compile严格等于字符串"1"才进入模型run包恢复分支；其它值进入普通编译分支。主线代码生成把normalize_config和extend_config写入compile_configs，再构造AclGraph，故不能仅凭外层Python布尔值或“有模型缓存”日志判断已选中run包恢复分支。

## 同名dump函数的实际执行不同

| 比较点 | 两版集成static_kernel | 固定主线独立static_kernel |
| --- | --- | --- |
| 采集期间执行 | 开启AclopStartDumpArgs；GraphModule经torch.fx.Interpreter.run，其它callable直接调用；正常完成后同步当前stream | 创建临时NPUGraph及dump_stream，在relaxed捕获上下文调用fx_func；此局部函数未调用replay |
| 流和控核 | 所选函数没有创建同样的dump_stream或复制/恢复控核步骤 | 获取来源流控核，必要时设置dump_stream；finally停止dump、reset图并恢复借用流原控核 |
| 单卡调用者的dump异常 | 所读单卡函数直接调用_fx_func_run，没有此处局部except继续选择目录 | 所读单卡函数捕获dump异常并warning，随后仍选择JSON目录 |

集成_fx_func_run的finally保证尝试停止dump；FX执行失败时，后续当前流synchronize不会到达。独立函数清理步骤依次执行，不能据finally存在保证每个恢复步骤在前一步失败后仍运行。独立源码注释称dump为Host-only、节省设备执行，但本卡仅确认上述Python调用链与未显式replay；不把注释当所有底层操作均无设备活动或实测节省时间的证据。独立完整细节复用[dump与选择](npugraph_ex_static_kernel_dump_and_selection.md)。

因此调优时应分别记录额外Eager执行、当前流同步、临时捕获和编译安装成本；两条路径的首次时延不能用同一组阶段假定解释。没有实测性能或数值结论。

## 编译前已见集合与持久run缓存分开

两版集成get_compile_dir按算子JSON原始字节的hash查进程内_compiled_op_set，将文件复制到selected目录后就加入集合；这一步发生在static_compile、安装与reselect之前。集合中出现hash不能证明编译成功。该selected去重字段本身没有附加SuperKernel或确定性字段，也不是所有缓存失效的完整保证；不能拿独立包的持久缓存键替它补条件。

主线集成在这一步还按文件名黑名单跳过条目，发布所读同一函数没有此判断。主线模型缓存分支选择全量_opcompile并另做黑名单搬移，不能用selected目录是否存在判断成功或全部已编译。这里只比较所读入口和去重，不认证任意文件残留、重试或失败回滚。

主线独立单卡函数在目录选择后还可查持久run缓存，命中则安装/reselect并返回，否则编译后更新缓存再安装。该层的键、文件锁和目录所有权分别按[设计合同](npugraph_ex_standalone_design_contracts.md)与[run包生命周期](npugraph_ex_static_kernel_run_package_lifecycle.md)核对。不要将两份代码的同名函数、进程已见集合、模型run恢复及独立持久run索引合并成一个“缓存命中”。

## 本次静态核对边界

两版集成compile_static_kernel、_compile_static_kernel_for_single_card和_fx_func_run的完整函数AST一致；这是三个选定函数的语法对照，不是整模块、Gloo行为或发布独立包等价。其余仅审阅Evidence所列范围。既有缓存、输入输出与捕获卡继续按各自固定命名空间使用；没有完成所有跨版本/跨流异常恢复、底层ACL行为或运行支持验证。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/static_kernel.py)（primary）：定向范围39–73, 209–231, 357–400, 499–534, 760–821。

- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/static_kernel.py)（implementation）：定向范围34–49, 120–140, 371–393, 633–684。

- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：定向范围750–784, 995–1064。

- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：定向范围660–680, 860–903。

- [固定实现来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/npugraphex_config.py)（implementation）：定向范围1–123。

- [固定实现来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/npugraphex_config.py)（implementation）：定向范围1–122。

- [固定实现来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：定向范围18–26, 164–182, 363–380, 558–578。

- [固定实现来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：定向范围18–26, 335–341。

- [固定实现来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：定向范围37, 1030–1056。

- [固定实现来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：定向范围30, 928–946。

- [固定实现来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/__init__.py)（implementation）：定向范围1–16。

- [固定实现来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：定向范围746–769, 923–984。

- [固定实现来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）：定向范围29–64, 107–135。

- [固定实现来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/static_kernel.py)（implementation）：定向范围312–354, 700–732。

- [固定实现来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py)（implementation）：定向范围13, 142–171, 192–201, 231–257。

- [固定实现来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/dynamo/__init__.py)（implementation）：定向范围106–130, 152–175。
## 发布独立包的配置层：平铺别名与嵌套子配置

发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的独立`npugraph_ex`自带完整的`npugraph_ex/configs/`配置树：包入口从`npugraph_ex.configs.compiler_config`导出CompilerConfig，其固定子配置为debug、dump_config、experimental_config、aclgraph_config、npugraphex_config（平铺别名shim）与mode，两个post_grad键原样透传。该树与集成路径同构，而不是主线独立包单文件平铺CompilerConfig的镜像；集成配置对象的职责划分见[配置边界](torchair_compiler_config_boundaries.md)，本卡只比较三个变体的接受面。

| 变体 | options接受面 | static_kernel_compile_group / disable_static_kernel_compile_cache | deadlock_check平铺名 |
| --- | --- | --- | --- |
| 集成两pin | 23键别名OPTIONS_TO_CONFIG_MAP白名单，未知键ValueError | 拒收（本卡既有结论） | 无：主线别名表无此键、只能嵌套赋值debug.aclgraph.deadlock_check；发布连该嵌套选项都缺席 |
| 独立主线 | 平铺CompilerConfig属性hasattr白名单，错误信息列出公共属性 | 接受 | 接受（平铺属性） |
| 独立发布 | 24键别名白名单=集成23键+deadlock_check | 拒收；ValueError并打印排序后的白名单，与集成同错误形态 | 接受，映射到debug.aclgraph.deadlock_check |

独立发布的别名映射与集成逐字相同（static_kernel_compile→experimental_config.aclgraph._aclnn_static_shape_kernel、use_graph_pool→aclgraph_config.use_custom_pool、capture_limit→debug.aclgraph.static_capture_size_limit、三个dump键→dump_config.*等），但解析目标是`npugraph_ex`自己的子配置对象；inplace_pass、input_inplace_pass、reuse_graph_pool_in_same_fx三键同样经invert_bool翻转后写入目标。`_process_kwargs_options`还会把原始值setattr到`_NpuGraphExConfig`类属性上（类级共享、跨实例），转换后的值才进入嵌套目标，本行为与集成版一致。因此键名与映射相同不能推出配置对象或行为相同。

## 三变体的取值形态与消费侧配套

| 变体 | bool取值形态（OptionValue.value getter） | 消费侧比较风格 |
| --- | --- | --- |
| 集成两pin | True/False转成字符串"1"/"0" | AclGraph平铺dict按`=='1'`字符串比较 |
| 独立主线 | 保留Python bool（isinstance分支） | acl_graph按truthy判断，如`config.get('deadlock_check', False)` |
| 独立发布 | True/False转成字符串"1"/"0"，与集成一致 | acl_graph按`config.get('deadlock_check','0')=='1'`字符串比较 |

取值形态与比较风格在同一变体内配套：主线独立包_option_base.py的getter保留bool，其acl_graph消费端改为truthy判断；发布独立包两端回到字符串合同。as_dict的`mode`参数签名只存在于集成_option_base（两pin），独立两侧均为无参as_dict。序列化键名也有对应差异——主线独立包AclGraph以`static_kernel_compile`为键、发布以`_aclnn_static_shape_kernel`为键，run_eagerly与捕获两条编译分支的完整行为复用[控核与静态编译门](npugraph_ex_core_limit_stream_targets_and_static_kernel_gate.md)，本卡不重述。

## 独立发布的写入校验与序列化边界

- 门槛→失败：别名层只转发，校验发生在嵌套目标的OptionValue写入。bool选项的optional校验是相等成员判断（`v not in optional`），不是严格bool类型门：invert_bool翻转bool与int 0/1，int 0/1翻转后以数值相等通过目标[True, False]列表；float 0.0/1.0被invert_bool原样返回，也因1.0 == True、0.0 == False通过成员判断，但float经getter序列化为"1.0"/"0.0"而非bool的"1"/"0"，通过校验不等于获得布尔序列化与消费侧`=='1'`语义；其余取值仍触发`v not in optional`的ValueError。bool选项应传真实bool值，本卡不编造运行时示例。capture_limit经IntRangeValue(64, 1, INT64_MAX)要求isinstance(v, int)且在界内，该类型门收bool（bool是int子类）；data_dump_dir→dump_config.dump_path是MustExistedPathValue，目录不存在直接FileNotFoundError；两个_vllm符号键中sym_index是IntRangeValue(0, 0, INT64_MAX)（同样收bool后按数值范围判定），sym_value_range是IntListValue(None)：接受list或tuple，逐元素isinstance(val, int)亦收bool元素；显式经setter传None归一为[]，构造默认None保留为None，本卡不臆造后端空列表后果。
- aclgraph_config与npugraphex_config是普通类（不继承NpuBaseConfig），不进CompilerConfig._fixed_attrs：初始化后对这两棵子树整体重赋值会被白名单拒绝；use_custom_pool本身没有OptionValue校验，也不参与as_dict序列化——use_graph_pool只被npu_fx_compiler直接读取并作为AclConcreteGraph的pool参数，不进入AclGraph平铺dict。
- as_dict只输出部分键：_AclGraphDebugConfig.as_dict不输出disable_reinplace_*与remove_cat_ops，这三项由fx2acl_converter直接嵌套读取；_DataDumpConfig的dump_mode、dump_step、dump_layer、dump_data、quant_dumpable、dump_config_path没有平铺别名，只能嵌套赋值，as_dict在enable_dump为真时只产出aclgraph.enableDump/dumpPath/dumpStage三个全局键；experimental_config的keep_inference_input_mutations与npu_fx_pass同样只在直接嵌套读处消费。
- 静态Kernel序列化门：_AclGraphExperimentalConfig.as_dict仅当_aclnn_static_shape_kernel.value等于"1"才写出_aclnn_static_shape_kernel、_build_dir（None时写空串，注释说明底层ge::AscendString不接受None）、sym_value_range与sym_index；super_kernel_optimize同理。开关为False时这些键整体从序列化结果消失。

## 发布独立包deadlock_check的接线

别名第24键→debug.aclgraph.deadlock_check→debug.as_dict进入平铺dict→AclGraph在TORCH_COMPILE_DEBUG或该键为'1'时debug_dump()导出图JSON→utils.run_deadlock_check读取设备vector_core_num后调用包内npugraph_ex.tools.aclgraph_check（固定源码ls确认三工具文件存在，run_deadlock_check从该包导入deadlock_check）。这是四个配置变体中唯一“平铺别名+包内工具”齐备的形态：集成发布选项与工具缺席、集成主线只能嵌套赋值且工具在python/torchair侧、主线独立包是平铺属性加truthy消费；三者的正负证据复用[死锁检查工具链](torchair_gegraph_check_deadlock_toolchain.md)。工具在设备上的实际产物与文档路径的对应关系仍是运行时口径，本卡不闭合。

## enable_view_optimize：发布独立包的失败边界

发布独立包npu_fx_compiler在torch_npu已导入且捕获图存在`npu.npu_weight_quant_batchmatmul.default`节点时，执行`self.config.experimental_config.enable_view_optimize = False`意图临时关闭视图优化；但该包的_ExperimentalConfig没有enable_view_optimize选项（集成两pin的experimental_config.py第26行均有），NpuBaseConfig.__setattr__对不在_fixed_attrs的键直接ValueError并由pretty_error_msg重抛同类型。因此在此触发条件下，发布独立包不是“关闭优化后继续编译”，而是编译直接失败；不能把集成的同名赋值语义移植到独立发布。该结论仅限已全读的发布独立包代码；主线独立包与集成的对应段不在本卡范围，不作宣称。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/npugraphex_config.py)（implementation）：1–124完整读取（末行无换行符，wc -l计123）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）：1–79完整读取。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/experimental_config.py)（implementation）：1–86完整读取。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/debug_config.py)（implementation）：1–121完整读取。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/dump_config.py)（implementation）：1–43完整读取。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/aclgraph_config.py)（implementation）：1–12完整读取。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/configs/_option_base.py)（implementation）：1–254完整读取。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/_option_base.py)（implementation）：1–271完整读取；与发布独立版diff核对bool getter与as_dict签名差异。
- [新增来源 9](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/__init__.py)（implementation）：1–34完整读取。
- [新增来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：43, 305–325, 595–644, 655–714, 800–854, 930–945。
- [新增来源 11](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：240, 274, 281, 328–369。
- [新增来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：895–950, 1225–1240。
- [新增来源 13](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)（implementation）：16, 495–506（文件止于506行）。
- [新增来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py)（implementation）：30–42。
- [新增来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py)（implementation）：30–42；与独立包版diff核对（仅import路径与as_dict(mode)签名差异，bool字符串化相同）。
- [新增来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py)（implementation）：26，enable_view_optimize存在性。
- [新增来源 17](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py)（implementation）：26，enable_view_optimize存在性。
- 复核范围（既有来源）：主线独立`npugraph_ex/npugraph_ex/npu_fx_compiler.py` 34, 795–810, 950–965；主线独立`npugraph_ex/npugraph_ex/configs/compiler_config.py` 1–215完整读取（正文前缀仍记29–64, 107–135）；集成主线`python/torchair/configs/npugraphex_config.py` 1–123完整复认；发布集成`python/torchair/configs/npugraphex_config.py`与`python/torchair/configs/debug_config.py`对deadlock_check做全文件rg负向扫描（零命中）。
