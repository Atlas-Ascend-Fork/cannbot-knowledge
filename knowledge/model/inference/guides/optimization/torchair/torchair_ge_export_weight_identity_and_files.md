---
type: Guide
title: GE导出权重工件：对象身份、常量替换与外置文件
description: 解释权重id映射、含图体积的外置阈值、输入节点替换、文件写入和非原子导出边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/export_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/export_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_export.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_gear_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
created_at: '2026-11-10T14:08:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE导出权重工件：对象身份、常量替换与外置文件

## 固定导出消费者

本卡定向审阅TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`及发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的export_utils权重处理链。七个选定函数去除logger表达式后AST相同，路径选择函数仅作分别静态阅读，不扩大成全部导出逻辑相同。产品矩阵未知，保持draft、空平台；没有导出模型、写权重或执行ATC。

主线GeConcreteGraph.export先make_export_graph，再normalize、生成options和可选拓扑模板，最后把序列化图交给原生export。已有[Dynamo导出部署](dynamo_export_offline_deployment.md)解释公开前提和成功信号，[拓扑模板](torchair_ge_export_topology_templates.md)解释多卡占位；这里补齐图和权重文件实际如何产生，不能把Python图准备结束当作AIR或OM已可用。

## 权重选择依据对象身份

_get_model_weight_names先遍历named_buffers，再遍历named_parameters，以`id(tensor) -> name`写字典；同id后写覆盖。导出处理只转换inputs中id命中的项，不按名字相似、shape、data_ptr或共享Storage推断权重。用新对象替换权重、只共享Storage或上游重新包装输入时，不能依赖这个函数自动恢复原映射。

make_export_graph复制原图proto并沿用used_process_group映射，取得可选rank_N子目录后处理权重。_convert_data_to_const按inputs枚举位置i直接改export_graph.op[i]、保留该节点名字；它没有逐项通过Data.index搜节点，所以调用方输入与图节点顺序必须对应。命中的权重要求is_contiguous，否则AssertionError；不是先自动contiguous再保存。

替换完成后，_sort_graph_data_index只重写编号：按当前节点顺序先给全部Data编号，再给全部RefData编号。它没有重排整个op列表，也不能据其名字推定任意输入/输出映射已重新匹配。

## 外置阈值包含已有图体积

_is_weight_externalized以当前export_graph.ByteSize为起点，对inputs中每个id命中的Tensor加`element_size()*nelement()`并计数；严格大于`(2048-200)*1024*1024`才统一选择FileConstant，否则Const。这不是仅把模型权重总量与2G比较，也不是最终AIR大小的精确计算或设备峰值内存估计。

计数以输入出现次数为单位，没有按Storage或文件名去重；有权重且超过阈值时，所命中的权重统一外置，不是只外置超出的尾部几项。没有命中权重时直接返回，不能凭模型里存在Parameter就推定导出已冻结它。

内嵌路线把权重.cpu后构造readable=False的GE Const。外置路线写FileConstant的shape、dtype和路径；两者都是导出图替换，不是继续读取训练时可变Parameter的运行期引用。修改原模型后需要重新建立匹配工件，不能把外置文件名当作自动同步机制。

## 文件名、数据路径与视图边界

外置文件名由模型name把所有点替换成下划线，无额外扩展名；FileConstant引用同一路径。这里没有通用名称碰撞检查，不同名字映射为同一文件名时不能假定会自动加后缀。rank查询失败会退回根目录；成功时图和权重目录为rank_N，而AIR名字追加rank数字，不能仅凭目录数量认证完整rank集合。

BF16通过`inp.cpu().untyped_storage()._write_file(...)`写出；其它类型通过`inp.numpy(force=True).tofile(...)`。这是两种消费者，不能把一个分支的底层存储写入语义机械套到另一个。局部仅检查contiguous，没有另外校验任意view的storage_offset或底层Storage范围；BF16路线把untyped_storage交给writer，不能只据连续性认证所有切片外置字节已与逻辑shape一一对应。本卡未审完底层writer，也未做视图文件复现。

这些写法不证明任意低精度/扩展dtype都有numpy或storage导出能力；仍按准确软件栈/公开合同核对。整模型参数量、每个Tensor逻辑字节、外置文件实际长度和最终图引用应分别验收。

## 不是原子导出事务

所读顺序是创建目录、替换图节点、逐个写外置权重、dump dynamo.pbtxt，随后才由调用方继续normalize和原生export。这里没有统一临时目录提交或失败回滚；中途异常可能留下部分文件，已有pbtxt/权重文件也不单独证明AIR导出完成。

部署前核对每个FileConstant的实际路径、文件名、shape/dtype和文件内容，再按公开相对/绝对路径要求迁移图、权重、options及rank拓扑。本次没有执行保存、加载、精度或性能实验，不新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/export_utils.py)（primary）：定向范围14–169。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/export_utils.py)（implementation）：定向范围14–164。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_export.py)（implementation）：定向范围16–36。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：定向范围1850–1866。

## options.json 的白名单过滤与作用域复制

主线`export()`在权重外置与图归一化之后、原生`_torchair.export`之前调用`_generate_export_options_config`写options.json：全局选项按白名单过滤后同时填入`global`与`session`两个作用域（session为浅拷贝），本图选项按白名单过滤后只填入`graph`作用域。文件写到`_get_subpath(export_path_dir)`，rank可获取时为`rank_N`子目录，否则为导出根目录；`options.json`以`w`截断重写、`indent=4`，写前经PathManager路径检查。建目录、路径检查或json写入抛出的异常沿`export()`直接上抛，本次调用不会进入原生export，AIR不产生；没有try/except、临时文件或回滚。

### 白名单键与来源

两张白名单是模块级硬编码常量，过滤按白名单顺序遍历，输出键序固定为白名单序、与用户传入顺序无关：

- compile白名单（18键）：ge.exec.static_model_ops_lower_limit、ge.opSelectImplmode、ge.deterministic、ge.quant_dumpable、ge.tiling_schedule_optimize、ge.enableSingleStream、ge.oo.level、ge.exportCompileStat、ge.topoSortingMode、ge.jit_compile、ge.exec.atomicCleanPolicy、ge.inputHintShape、ge.fusionSwitchFile、ge.aicoreNum、ge.exec.allow_hf32、ge.optimizationSwitch、ge.oo.constantFolding、ge.oo.deadCodeElimination。
- execute白名单（8键）：ge.exec.staticMemoryPolicy、ge.featureBaseRefreshable、ge.exec.outputReuseMemIndexes、ge.exec.allTensorNotEmpty、ge.exec.frozenInputIndexes、ge.exec.hostInputIndexes、ge.exec.dumpStep、ge.exec.dumpLayer。

两个作用域层的execute options同样从compile options字典过滤而来，没有独立的执行选项输入；`global`与`session`内容相同是复制行为，不是两个层次各有一套配置的证据。

### 导出的是子集，不是完整有效配置

`_normalize_ge_option`在导出前向选项字典原地注入运行期键，能进入options.json的有：全局的ge.exec.staticMemoryPolicy="2"、ge.opSelectImplmode="high_precision"，本图的ge.deterministic、ge.exec.atomicCleanPolicy="1"、ge.exec.allTensorNotEmpty、ge.inputHintShape及条件性的ge.exec.outputReuseMemIndexes。不在两张白名单内的运行期键不会导出：ge.exec.outputReuseInputMemIndexes、ge.deterministicLevel、frozenInput（execute白名单里的ge.exec.frozenInputIndexes是另一个键名）和动态分档的ge.inputShape、ge.dynamicDims、ge.dynamicNodeType。部署侧按options.json复刻环境时，不能把它当作完整有效配置的等价物。

### 触发与版本边界

触发门槛是`config.export.export_mode`为真：`run()`在输入处理与运行期图更新后调用`export(inputs)`并随即抛出`ExportSuccess("export graph over")`结束本次执行。options.json导出是主线独有：发布7c6c754的export()从图归一化直接进入可选拓扑模板和原生export，两版export()经规范化AST比对仅差选项归一化与options.json生成两行；发布版没有两张白名单常量、过滤函数或`_get_subpath`导入。

## 实现来源

- [主线转换器options.json链](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：123–156、1178–1201、1850–1866、1974–2031、2340–2409。
- [发布转换器export对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：1467–1478；全树符号检索与AST顶层清单核对options.json功能缺席。
- [主线导出子路径](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/export_utils.py)（primary，扩大范围）：25–44。
- [主线动态分档选项键名](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_gear_utils.py)（implementation）：90–120，仅核对generate_dynamic_dims_option产出的键名。
- [主线输入提示键名](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）：345–349，仅核对_append_real_input_shape产出的键名。
