---
type: Guide
title: TorchAir诊断与导出配置：对象及路径边界
description: 区分Debug路径拼接、Dump序列化创建目录与Export未冻结属性替换，连接主线Eager和导出入口并保留本地校验边界。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/dump_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/dump_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/export_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/export_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_export.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_export.py
  role: implementation
created_at: '2026-11-11T03:20:13Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# TorchAir诊断与导出配置：对象及路径边界

本卡绑定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013中debug_config、dump_config和export_config完整本地定义，主线消费者按Evidence定向核对。产品和完整配套未知，保持draft、空平台；未构造配置、写目录、加载模型、导出、捕获或初始化通信。公开使用范围继续见[数据Dump](../torch_npu/torchair_data_dump_modes.md)及[Dynamo导出](dynamo_export_offline_deployment.md)。

## Debug路径生成不创建数据目录

_DebugBase将_path默认设None，enabled只检查type.value是否非None。full_path禁用时返回None；启用时默认目录点号，已初始化distributed则取rank，否则rank0。文件名含name、rank、pid与type后缀，with_timestap（保留参数拼写）为True时另加UTC的年月日时分秒及微秒时间戳；False时无时间戳。这段路径拼接本身没有创建目录或检查权限，也未调用dist.is_available。

_Dump允许type为txt/pbtxt/py且默认None，_DataDump允许npy且默认None并声明filter=None；二者都将path追加到_fixed_attrs，path setter用os.path.realpath后写入_path包装值。它只规范绝对/真实路径，不能据此推导目录已存在、可写或产物已生成。_DataDump另外将filter加入_fixed_attrs，未在这个类检查Callable或返回节点类型；过滤和FX数据执行语义继续复用[FX Eager Dump实现](../torch_npu/torchair_fx_eager_dump_execution_and_coverage.md)。

_FxSummary只允许csv且默认关闭，skip_compile默认True。主线_NpuFxCompiler在max-autotune且summary开启时调用汇总，skip_compile为真会直接返回Eager包装；捕获模式先提示不生成csv。debug.data_dump开启会直接返回_NpuFxDumper的Eager包装。配置路径存在、编译成功和真实优化图执行是不同证据。其余Debug开关与序列化见[分组配置](torchair_grouped_config_serialization_and_mode_consumers.md)。

## dump_config的声明与目录副作用

| 字段默认值 | 本地检查 |
| --- | --- |
| enable_dump=False、quant_dumpable=False | bool候选包装。 |
| dump_path=./ | MustExistedPathValue；显式赋值需已有目录，但构造默认未调用setter。 |
| dump_mode=all | 候选input/output/all。 |
| dump_data=tensor | 候选tensor/stats。 |
| dump_step为空串 | RegexValue按数字、可选连接号及竖线模式re.match；示例0\|1\|2-5\|6。仅为本地语法检查，不验证步号顺序或实际迭代。 |
| dump_layer为空串 | RegexValue允许来源中的数字/英文字母/下划线/双引号/空格/斜杠/反斜杠/点；不校验图中节点是否存在。 |
| dump_config_path=None | 非None赋值要求已有.json文件，空串拒绝；这里不解析JSON内容。 |
| data_dump_stage=optimized | 候选original/optimized。 |

full_path在distributed可用、已初始化且world_size>1时创建worldsizeN_global_rankR子目录；其他情况创建worldsize1_global_rank0。os.makedirs(exist_ok=True)有真实目录副作用，不是单纯字符串转换，失败也不在本函数吞掉。as_dict只在对应enable_dump分支调用full_path，故调用序列化可能创建目录。

非None dump_config_path始终先写global的ge_dump_with_acl_config，不要求enable_dump且不按mode过滤。本地函数没有因为该JSON路径存在就抑制旧细项；JSON优先解释属于下游合同，不能把文档优先级误写成这里已经删除旧键。

enable_dump且max-autotune时输出global ge.exec.enableDump=1、dumpPath/full_path、dumpMode、ge.quant_dumpable的1/0及dumpData；dump_step/dump_layer非空才分别附加dumpStep/dumpLayer。enable_dump且reduce-overhead/npugraph_ex时输出global aclgraph.enableDump=1、dumpPath/full_path及dumpStage；未匹配的mode不进入这两路。返回值总是({},dump_options)。所读两版仅有单卡目录名的无插值f串/普通字符串差异，没有据此生成新的目录合同。

主线_NpuFxCompiler在enable_dump.value为1、stage为original且捕获mode时调用这组as_dict后返回insert_save_npugraph_tensor，发生于创建深复制GraphModule和AclConcreteGraph之前。优化路径的后续张量保存、Watcher及JSON执行仍按各自消费者核验，不能从这个早返回推广全部路径已覆盖。

## export配置未启用基类字段冻结

_ExportConfig继承NpuBaseConfig，但构造函数没有调用super().__init__。它声明export_mode为False候选包装、export_path_dir为默认./的MustExistedPathValue，export_name/weight_name/inputs_name为None，experimental子配置三个bool字段enable_record_nn_module_stack、auto_atc_config_generated、enable_lite_export均默认False。

由于export对象没有_fixed_attrs，普通export.export_mode=True和export.export_path_dir=字符串赋值直接替换属性，不会走原OptionValue.value或目录setter。不能仅看初始化时的MustExistedPathValue类名就断言外部导出路径已经被该setter检查；显式调用仍留存包装对象的.value setter才是另一种操作。子experimental自己调用了基类初始化，保留其包装校验。

_ExportConfig.as_dict在export_mode真值成立时，只把当前export_path_dir对象本身和export_name放入local，未自动取.value或递归experimental；关闭时返回空字典对。未被外部字符串赋值替换的默认路径仍可能是包装对象，这个函数不统一保证返回字符串。weight_name、inputs_name和三个experimental开关也没有被这个函数全部序列化。

主线_get_export_config在None时新建根配置，否则沿用传入对象，直接设置export_mode=True、export_path_dir、export_name、weight_name及enable_ref_data=True。dynamo_export先只取export_name的basename，检查目录及目标.air是否符号链接，再在上下文finally恢复_IN_EXPORT_CONTEXT；没有在该finally把配置改动还原。不要把导出调用理解为原配置对象的隔离副本或自动复位。

GeConcreteGraph.export直接读取这些export属性，按权重身份制作图，生成归一化选项配置；auto_atc_config_generated为真才调用拓扑模板生成，再将路径和最终air名交给_torchair.export。enable_lite_export还在主线_NpuFxCompiler的导入选择中直接读取，并非必须出现在root字典中。权重文件与rank拓扑的完整合同复用[权重与文件](torchair_ge_export_weight_identity_and_files.md)、[拓扑模板](torchair_ge_export_topology_templates.md)；本卡不认证本地路径检查、外部导出库、全部experimental消费者或实际离线部署。

## 本地覆盖与运行验收

三组配置的所有本地定义已核对；debug增加的主线deadlock字段及分组serializer见相邻卡。对Debug filename、Dump创建目录、JSON下游和export属性替换分别保留输入、mode、rank、原对象及最终消费者证据，不能用一次序列化结果代替整套配置或数值/性能验收。本次没有运行上游或新增verified。

## 配置实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py)（primary）：1–120。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py)（implementation）：1–118。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/dump_config.py)（implementation）：1–55。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/dump_config.py)（implementation）：1–55。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/export_config.py)（implementation）：1–34。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/export_config.py)（implementation）：1–34。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_export.py)（implementation）：16–36, 38–86。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：684–720, 735–744。
- [固定实现 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：1850–1866。

## GE dump JSON的实际消费者与缓存

两固定版本都在未编译图的调用分支中，先从全局选项`pop`七个dump键，再初始化GE，构造/写出dump JSON并调用`AclmdlSetDump`，之后才`graph.load`。因此这些键在这条初始化调用前已从传入字典移出；是否写JSON还受下表第二行限制。

| 条件或步骤 | 本地行为 | 排查影响 |
| --- | --- | --- |
| 图节点含`torchair_enable_data_dump`属性 | 只检查属性键存在，读取并解码的值没有参与判断；收集节点type，为空才用name | False或空值没有在这里排除该节点；收集目标通常是算子类型，不能当精确节点实例名。 |
| 是否生成JSON | 六个映射细项中至少一个值非None且转字符串strip后非空：Path/Mode/Data/Layer/Step/quant_dumpable | 只有`ge.exec.enableDump`或仅图上scope标记不满足这里的写出门槛。`enableDump`被提取，却没有写入这张JSON映射。 |
| layer集合 | 按空格拆dumpLayer，和上述节点类型并入set后转list | 去重但不保顺序；没有因属性值为假而再次过滤。 |
| 首次有效配置 | 细项写入模块全局`g_cached_dump_root`，值统一转str；加入当前model_name及可选layer | 缓存不按图、设备或输出目录另建对象。 |
| 后续有效配置 | 修复dump/dump_list容器类型后只append新的model条目 | 不刷新首次缓存的dump_path/mode/data/step等细项，也没有在本函数清空或去重模型条目。配置切换后不能假定JSON只含本图与本次细项。 |
| 写入与设置 | 在当前目录`ge_dump_data_json`下，以worldsize/rank/pid命名，`w`重写整个缓存；通信未初始化时用1/0 | 每个进入此分支的图都可能产生Host目录/序列化开销；文件名没有图ID。 |

缓存更新先于建目录和写文件；这些操作及json.dump异常不在末尾的try中，没有本地回滚。只有`AclmdlSetDump`调用段捕获Exception、记录错误后继续；发布版该try还包含局部导入，主线用已有模块绑定。不能把一次设置失败视为缓存已恢复，或把整个dump流程的异常都当作仅日志。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)：272–281、1198–1211、2272–2353、2406–2417。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)：169–178、967–977、1759–1840、1843–1858。
## 发布版npu_export的共享默认配置对象

发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的`_get_export_config`签名是`config=CompilerConfig()`——默认参数在函数定义时求值一次，此后所有不显式传config的`dynamo_export`调用共享同一个CompilerConfig实例；主线已改为`config=None`并在函数体内新建。结合上文「主线_get_export_config在None时新建根配置」的对照：发布版前一次导出设置的`export_mode/export_path_dir/export_name/weight_name/enable_ref_data`会留在共享实例上被下一次调用继承，主线每次调用拿到隔离对象。发布版也没有主线`_IN_EXPORT_CONTEXT`标志与finally恢复段。需要可重复、互不污染的多次导出时，发布版必须每次显式传入新建的CompilerConfig；本节为静态签名事实，未执行两次导出验证继承行为。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_export.py)（implementation）：1–75完整读取；与主线`diff -w`（51行差异）定位`_get_export_config`默认参数与`_IN_EXPORT_CONTEXT`缺席。
