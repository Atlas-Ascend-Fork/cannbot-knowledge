---
type: Guide
title: FX Eager数据Dump：采集覆盖、dtype转换与额外执行
description: 梳理TorchAir FX dumper入口与落盘消费者，说明Converter门控、位置参数覆盖、filter两次调用及部分文件不能证明完整采集。
tags:
- task.debugging
- topic.precision
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/fx_dumper.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/fx_dumper.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/data_dump_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/data_dump_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py
  role: implementation
created_at: '2026-11-10T14:57:23Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FX Eager数据Dump：采集覆盖、dtype转换与额外执行

本卡绑定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`中的`python/torchair/`实现，补充[数据Dump模式](torchair_data_dump_modes.md)的真实FX消费者。它不是GE执行数据、独立npugraph_ex捕获数据，也不是自动精度比较器。平台未知，保持draft、空平台；未导入上游、执行图、采集/加载npy、编译或访问设备。

## 开启后真正执行什么

主线debug.data_dump的type默认None，enabled按type.value是否非None判断，候选type为npy。两版_get_compiled_gm在开启data_dump时创建_NpuFxDumper(gm)，提前返回_CompiledFxGraph，跳过后面的_gen_compiled_gm常规成图分支。更早的max-autotune fx_summary.skip_compile分支也可能先返回原gm，不能认为只要配置data_dump就一定到达dumper。

在本卡对应的GE max-autotune入口，_CompiledFxGraph运行该Interpreter，dumper通过super().run真实执行传入FX图。不是只把节点文本写文件，也没有同时执行GE结果并算误差。这份gm仍来自编译前端/AOT流程，不等于完全绕过Dynamo的原生模型Eager基准；流水线分工见[FX编译管线](../torchair/torchair_fx_compiler_pipeline.md)。不把此实现直接用作所有ACL模式或任意自定义backend的可用性保证。

## 被执行的节点不一定都有文件

本地只装饰call_function。处于_dump_ctx且_get_converter(target)非None时，才进入数据保存；没有命中Converter仍调用原函数继续执行。日志里的“non aten”不是一个独立的aten白名单判断，真实门控是Converter查询；查询还可使用target._ge_converter。注册存在不证明GE转换、编译或设备精度已验证。

因此节点执行、存在Converter、filter选中、写完输入、写完输出是不同阶段。不能把没有文件当成该算子没有执行，也不能从本地只有call_function装饰推导call_module、call_method和嵌套子模块全部已有同等逐节点覆盖。

## filter有两次调用和执行语义

run_node先调用filter(n)判断是否为None；返回None时仍执行该节点，只是不进入该节点的dump上下文。首次返回非None后，又调用filter(n)，把第二次结果赋给n，再交给Interpreter.run_node。

对通常的筛选用途，应让filter稳定返回原节点或None。带计数、随机值或其它副作用的filter会被选中分支调用两次；返回另一个节点还会改变交给Interpreter的执行对象，不能把它仅当文件名标签。这里没有为第二次返回None或无效对象增加统一校验。_dump_ctx使用线程局部node，finally清为None；这只描述所读上下文，不能扩展成任意嵌套/并发执行安全保证。

## 输入覆盖与保存后的dtype

| 数据位置 | 所读保存逻辑及边界 |
| --- | --- |
| 位置参数args | 逐个编号。非空list/tuple且首元素是Tensor时展开一层；其它值整体交给_as_numpy。不是任意嵌套pytree展平。 |
| 关键字参数kwargs | 传给原函数执行，但保存循环没有单独遍历kwargs。不能据INPUT文件重建完整关键字实参或所有默认值。 |
| 返回值 | 顶层list/tuple逐项保存，其它对象作为一个结果。字典或更深容器不在这里按Tensor叶子递归展开。 |
| Tensor转换 | detach→cpu→numpy；BF16额外转float32。npy中的FP32因此不独立证明原算子以FP32计算。 |
| 非Tensor转换 | 尝试np.array，异常时再尝试字符串数组。不能一律当作数值Tensor样本。 |

Tensor路径的cpu、dtype转换、numpy及np.save都增加真实工作；源码未在这层给出无等待或固定开销保证。_as_numpy对非Tensor的fallback也没有包住Tensor转换及全部np.save异常。插桩后耗时不能当正常优化后的GE吞吐。

## step和部分文件的含义

dumper从_step=0开始，只有整次super().run正常返回后才加一。文件按world/rank、子图名及step组织；每次命中的call_function先取时间戳并保存所有位置输入，再执行原函数，最后保存输出，同一次函数的INPUT/OUTPUT共用该时间戳。

函数执行、后续输入转换或某个输出保存失败，都可能已经留下较早的文件；所读实现没有事务式删除这些文件，失败调用也未在run末尾递增step。因此step目录存在、出现INPUT或输出文件数非零，不证明整图执行及全部保存成功。它也不是训练迭代、服务token或跨rank全局步数的自动对齐协议。

做精度定位应先固定版本、实际后端、子图、rank、成功调用的step、目标节点和完整实参，再确认输出保存完成。BF16对照保留原dtype语义；缺失kwargs、未命中Converter或容器未展开时另补证据。数据采集没有在此计算误差阈值或给出通过判定，比较方法复用[精度与性能定界](torchair_accuracy_and_performance_triage.md)。

## 版本和证据边界

两版_dump_ctx、_as_numpy、_trace_dump及_NpuFxDumper完整类的选定AST相同；这只覆盖所列采集逻辑，不声明两版完整AOT/GE流水线、外部NumPy/PyTorch版本或运行支持等价。未执行过滤器、Converter注册、数据采集或数值/性能实验，没有新增verified。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/fx_dumper.py)（primary）：定向范围16–21, 28–138。

- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/fx_dumper.py)（implementation）：定向范围16–21, 28–138。

- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：定向范围562–605, 693–718。

- [固定实现来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：定向范围488–524, 612–633。

- [固定实现来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py)（implementation）：定向范围16–36, 54–68, 103–110。

- [固定实现来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：定向范围323–338。

- [固定实现来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：定向范围218–232。
## data_dump_eager 参数与产物承诺的逐项配对

本节把 `ascend_ir/features/basic/data_dump_eager.md` 的参数表、产物命名与目录说明同两固定 pin 的 `configs/debug_config.py`、`fx_dumper.py` 及 `_get_compiled_gm` 构造点逐项配对；前文已覆盖的 filter 两次调用、step 递增与部分文件边界不重复。两版实现同构：`fx_dumper.py` 两版仅 69–70/123–125 行折行排版差异，docs 页两版仅 `${...}` 与 `$\{...\}` 的转义及行尾空白差异。

| 文档承诺 | 实现核对（静态读到，两 pin 同语义） | 边界 |
| --- | --- | --- |
| data_dump.type「当前仅支持npy格式」 | `_DataDump.type = OptionValue(None, ["npy"])`（debug_config.py:57 两版） | enabled 按 type.value 非 None 判定；候选外取值由 OptionValue 拒收 |
| data_dump.path「默认为当前执行路径」 | `full_path` 取 `path = "." if self._path.value is None`（debug_config.py:30 两版） | path setter 为 `os.path.realpath(value)`（:68 两版）——显式路径也被规范化为绝对真实路径，文档未提 |
| 产物 `${op_type}-${aten_ir}.${param_type}${param_idx}${timestamp}.npy` | 名称串 `{node.name}-{target}.INPUT/OUTPUT.{i}.{timestamp}`（fx_dumper.py 主线 76/79/85、发布 77/80/86），`.npy` 由 np.save 落盘补齐 | op_type 是 FX 节点名（不是 GE 算子类型）、aten_ir 是 aten target 原文；同次调用的 INPUT/OUTPUT 共用同一时间戳（前文既有结论） |
| （文档未记载的双层索引） | 非空 list/tuple 且首元素是 Tensor 的位置参数展开一层，逐元素文件名用 `INPUT.{i}.{j}`（fx_dumper.py 主线 74–78、发布 75–79） | 文档参数表只定义了单层 `${param_idx}`；该展开与 kwargs 不保存的既有边界同源（保存循环只遍历 args） |
| 目录 `worldsize${world_size}_global_rank${global_rank}/graph_1/{step}/` | `step_path` 拼出 `{dump_path}/worldsize{N}_global_rank{R}/graph_{n}/{step}`（fx_dumper.py 主线 117–125、发布 118–125） | worldsize 前缀仅当 dist 已初始化且 world_size>1（118–121），否则硬编码 `worldsize1_global_rank0/`（主线 123–125/发布 124–125）；`full_path` 返回值中的 `_rank_{r}_pid_{p}_ts_{t}.npy` 后缀经 `os.path.dirname` 丢弃（主线 122/124） |
| graph_1 注释为「${global_rank}所在进程的子图名称」 | 目录名 `graph_{n}` 固定来自构造点 `name="graph_" + str(_next_unique_graph_id())`（npu_fx_compiler.py 主线 713–714、发布 629–630；计数器主线 640–643、发布 565–568） | n 是进程内递增的全局图计数，与 GeConcreteGraph/AclConcreteGraph 图名同一序列；不是模型子图名，也不能从该目录名反推 rank |

「开启该功能后，GE图模式相关的功能配置均不生效」在 data_dump 上兑现为 `_get_compiled_gm` 提前返回（前文既有结论；更早的 fx_summary 分支主线 696–705/发布 615–623 可再提前）。run_eagerly 页同一句承诺的实现兑现位置与程度由[FX编译管线](../torchair/torchair_fx_compiler_pipeline.md)本轮配对承载。

## 固定来源与核验范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/data_dump_eager.md)（constraint）：1–60 全文读取（使用约束 9、参数表 27–33、产物说明与目录树 35–59）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/data_dump_eager.md)（constraint）：与主线 diff 仅 37/45/47/54 行转义与行尾空白差异，约束句、参数表与目录结构同义。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py)（implementation）：16–68 窗口（`_DebugBase.full_path` 26–36、`_DataDump` 54–68）；主线同窗口一并补读，两版行号一致。
- 本卡既有 fx_dumper.py 主线来源（primary）核验范围为 1–138 行（`_trace_dump` 59–89、`step_path` 117–125、`run_node` 127–134）；发布版 1–138 经 diff 核对仅 69–70/123–125 折行差异。既有 npu_fx_compiler.py 两 pin 来源其他核验窗口：主线 690–716（fx_summary 分支 696–705 在前、data_dump 分支 707–716 提前返回）、发布 609–631（对应 615–623/625–631）；`_next_unique_graph_id` 主线 640–643、发布 565–568。全部为静态读取，未 import/运行上游。
