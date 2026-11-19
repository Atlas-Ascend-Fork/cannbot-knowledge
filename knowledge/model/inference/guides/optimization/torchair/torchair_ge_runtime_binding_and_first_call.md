---
type: Guide
title: GE运行期绑定与首次调用编译时序
description: 按两版执行器实现区分FX输入、GE输入、首次绑定、AOE和编译，说明事件日志计时的实际覆盖范围。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-10T11:19:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE运行期绑定与首次调用编译时序

## 版本和证据范围

定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的GeConcreteGraph输入处理、运行期更新和调用链；所述条件在这两版一致。仅静态审阅选定函数，未运行上游、生成执行输入代码、调用NPU或测量收益；硬件范围未知，保持draft与空平台。

## FX参数需要先转换为GE输入

首次未编译调用从_input_info_list生成_input_process，之后每次调用仍执行该处理器。普通_TensorInput直接保留；其他getter生成对应处理代码，原FX参数中未被getter索引引用的项按索引倒序删除。GE输入顺序和数量因此不能直接等同于原FX args；符号打包、非连续输入和死输入删除后的索引必须与输入信息表对应。

_gen_input_process生成Python kernel并通过compile/exec建立模块；对_RngStatusInput另用运行期getter补写，因为该项不走同一普通代码生成路径。这个普通调用分支有RNG状态处理，不表示持久缓存支持RNG；_codegen_input在enable_cache=True且遇到相应项时明确抛错。

## 首次编译与后续调用

GeConcreteGraph构造时已经归一化全局选项并调用initialize_graph_engine，所以不能把所有GE初始化成本都归于首次graph.run。__call__先得到GE inputs，再以它们和原始FX args更新运行期图；已编译时该更新立即返回。

导出模式在运行期更新后执行export并抛ExportSuccess，不继续普通load、compile、run。普通未编译路径归一化选项，先取GE dump选项，再initialize_graph_engine、设置dump、graph.load。之后在满足条件时auto_tune，调用compile，最后graph.run；compile只在成功返回后把_is_compiled设True。后续调用复用输入处理器与已编译图，仍处理本次输入并运行，不重新执行该运行期图绑定。

should_auto_tune要求aoe_mode非None、is_dynamic=False且_auto_tune_times为0。is_dynamic只检查Data输出描述shape中的-1/-2并缓存布尔值；它不是对所有算子值依赖和业务分支动态性的证明。auto_tune成功后递增次数，不能把所有首次调用都视为必定执行AOE。

## 日志中的compile与run如何解读

事件日志的process input区间截止输入处理完成；compile区间从那里持续到compile调用之后，包含运行期图更新、未编译图load和可选AOE等工作，不只是设备编译器耗时。graph run区间包围Python的graph.run调用，后续RefData复制写回、符号/输入视图重建和FX输出映射在此时间点之后。

这些time.time时间戳没有在本调用链插入显式设备同步，因此不能直接当作完整设备执行时延或完整端到端延迟。评估优化时分别记录冷启动、命中后调用、稳态输入处理与实际设备耗时，再核对输出和输入存储语义；本卡没有给出性能数据。

- [FX编译和执行器选择](torchair_fx_compiler_pipeline.md)
- [输入重写与索引重排](torchair_ge_input_rewrites.md)
- [固定权重运行期绑定](torchair_ge_frozen_placeholder_runtime_binding.md)
- [输出别名与输入复用](torchair_ge_output_alias_and_input_reuse.md)

## Evidence

- [主线执行器](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（primary）：1137–1254、1313–1346、1496–1508、1869–1875、1948–1952、2034–2103。
- [发布执行器](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：相应构造、__call__、runtime update、compile、is_dynamic、auto_tune和输入代码生成函数；定向范围见入库清单，不表示全文覆盖。

## 输入分类与 getter 的具体合同

GE 根据编译时 meta 选择输入类别与 getter；普通运行随后按已经生成的处理器读取本次 FX 参数。分类会影响固定地址准入，getter 则影响 Host 打包及非连续输入处理，不能只按输入名称判断成本。

| parse_input 条件与顺序 | 记录或行为 | 优化时核对 |
| --- | --- | --- |
| 符号输入 | 创建 shape/real_shape 均为空的 CPU Data，记录表达式到 FX 参数位置，选择 `_ValueInput` | GE 输入位置仍须跟随前文打包与重排 |
| Tensor 为 Parameter，或存在 `_torchair_is_parameter` 属性 | 先归 PARAMETER；属性只查存在，不读取真假 | 会先于下行分支命中 |
| 未命中 Parameter，且 `_dynamo_static_input_type == 'guarded'` | 若 shape 任一维为符号则拒绝，否则归 STATIC_TENSOR | 符号 shape 拒绝只适用于实际进入这个 elif 的输入 |
| 其他 Tensor | 归 TENSOR；meta 设备为 None/cpu 时标 CPU，否则此处标 NPU | 该二分不代表所有其他设备均受支持 |
| Tensor getter | 编译时 meta 连续则用 `_TensorInput`，否则 `_DiscontiguousTensorInput`；记录 shape、real_shape、dim_gears 与 placement | 后续调用不会在此重新分类布局；冻结还取决于 getter 等字段，见[输入重写](torchair_ge_input_rewrites.md) |

`_GeInputInfo` 保存上述元数据，dim_gears 默认空字典。`_ValueType` 还定义 BUFFER，但这个 parse_input 没有将任一分支赋成 BUFFER。

| getter | 直接 `__call__` | `codegen` 产生的文字 |
| --- | --- | --- |
| `_ValueInput` | `torch.tensor(args[index])` | 对应 GE 位置赋 `torch.from_numpy(numpy.array([args[index]]))` |
| `_TensorInput` | 返回原参数 | 抛断言；普通 Tensor 由外层处理，不调用此代码生成方法 |
| `_DiscontiguousTensorInput` | 调用参数的 `.contiguous()` | 对应 GE 位置赋同样的 `.contiguous()` 调用 |
| `_RngStatusInput` | 保存的 rng_status.consume() | 在 GE 输入列表插 None，交前文实际消费者另行补写 |
| `_SymPackInput` | 收集 FX 索引后 `torch.tensor(list)` | 在 GE 输入列表插入 `torch.from_numpy(numpy.array([...]))` |

对标量实参，`_ValueInput` 两种写法分别传标量与单元素列表；生成路径还由 NumPy 推导 array dtype，字符串中未显式指定 dtype。两条路径的 rank、dtype 与分配方式不能直接等同。非连续 getter 则每次发出 `.contiguous()` 调用；是否新分配取决于该次真实 Tensor，不能一概按必然复制或零拷贝估算。

| 固定版本差异 | 主线 92e1e967 | 发布 7c6c754b |
| --- | --- | --- |
| 输入名 | 已提供 arg_pos_to_source 且取得名称时替换 target | 此函数没有对应改名块 |
| Host 标记 | 对符号 Data 与 CPU Tensor Data 调用 set_host_tensor | 此函数没有这两次调用；其他 Host 处理另计 |
| 非 Tensor、非符号 placeholder | debug 后返回原值，不登记上述 GE Data | else 分支要求 Tensor，否则断言失败 |

原值返回只描述此入口，不能替代后续算子对 Python 对象的支持判断。本节静态对照两版完整 parse_input 与字节相同的 80 行 getter/信息结构；未运行生成代码、NumPy/Tensor 构造或设备实验，前文实际执行链与首次调用证据原样保留。

## 输入分类与 getter 增补 Evidence

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（primary）：1510–1593；仅完整局部输入分类或所列 getter/信息结构，旧运行期消费者证据保留，未提升整模块资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：1250–1303；仅完整局部输入分类或所列 getter/信息结构，旧运行期消费者证据保留，未提升整模块资格。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）：695–774；仅完整局部输入分类或所列 getter/信息结构，旧运行期消费者证据保留，未提升整模块资格。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）：597–676；仅完整局部输入分类或所列 getter/信息结构，旧运行期消费者证据保留，未提升整模块资格。
