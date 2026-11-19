---
type: Guide
title: GE Triton HOP：路由身份、Grid与TMA合同
description: 说明functional HOP的参数来源、默认值、克隆输出、进程侧表路由、Grid/TMA恢复和Python回调执行边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_python.py
  role: implementation
created_at: '2026-11-10T11:04:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE Triton HOP：路由身份、Grid与TMA合同

## 固定快照与证据范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的custom_op_codegen_common.py、custom_op_codegen_cpp.py和custom_op_codegen_python.py，包含嵌入的生成代码模板。发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这三个同路径，仅记录路径事实，不否定其他发布入口。本文为静态实现合同，产品矩阵未知，保持draft与空平台；未导入上游、调用生成器、编译/加载动态库、读取设备地址或执行回调。

## functional目标和参数来源

is_triton_hop_node要求call_function、目标对象就是triton_kernel_wrapper_functional，并具备kernel_idx、constant_args_idx、grid、tma_descriptor_metadata、kwargs、tensors_to_clone六项；mutation目标另行识别并由预扫描拒绝。名字相似或不完整HOP不能据此认为已有路由。

extract_triton_hop_spec从KernelSideTable取kernel和常量，kwargs须Mapping；通过inspect.Signature及fn包装链补省略的内核默认值。launch_kwargs只能是无重复字符串tuple，非内核参数名的launch项也必须有明确值来源；node kwargs与常量侧表名字重叠或额外未知名拒绝。

每份autotune config都提供且可规范化的内核参数，可作为implicit constexpr跳过普通输入恢复；它不是任意缺失参数推导。静态constexpr只接受None、精确bool/int/str、有限float及递归tuple；类型敏感键区分bool/int，float用hex表达，拒绝其他容器和非有限float。

运行FX Node Meta为Tensor时走GE Tensor输入，为SymInt/SymFloat/SymBool或精确int/float/bool时走GE标量；其他Meta拒绝。静态node值嵌入回调，侧表常量保留侧表来源，不在规格里复制所有运行对象。

## Grid和TMA字段的形状合同

grid须非空list/tuple，每个config秩1至3，各维为精确int或Meta为int/SymInt的FX Node。全静态config保存tuple，混合动态config占一个GE int_list输入；若kernel.configs有非空可取长度则要求数量一致，不由grid规格证明调度值均正或kernel已可执行。

TMA兼容legacy三项experimental包，以及tagged experimental/stable包。experimental字段严格为dims、block_dims、element_size，前两者秩只允许1/2且等长；stable只有block_shape，长度必须等于对应runtime Tensor Meta的rank。字段只允许精确int或int/SymInt Node，动态字段占GE输入；这不是当前设备TMA支持矩阵。

InputSpec索引先运行Tensor/标量，再TMA动态字段，再动态grid；_iter_triton_hop_reg_op_inputs按索引排序并在生成Schema时检查连续。整型GE输入要求标量或指定长度一维、属于明确整数dtype集合，必要时Cast INT64；BOOL不在该集合，Cast也不证明所有大无符号值范围无损。

## 克隆输出与进程内路由身份

预扫描Meta输出须非空dict[str,Tensor]；clone键须非空、字符串、无重复、指向运行Tensor输入，输出key集合须与clone集合一致。不是任意有副作用的输入指针写入均可伪装成functional路线。

路由只用(kernel_idx,constant_args_idx)进程内二元组，合同另比较grid、输入规格、输出键顺序、克隆键顺序、launch参数和TMA字段。重复路由若kernel对象身份变了或合同不同即拒绝；等价合同复用首次规格，不按graph_id造另一份路由。

validate_triton_hop_specs先基于当前快照过滤并验证新增克隆合同；publish_triton_hop_specs在锁内重新查冲突、复制字典并交换快照，读者取一代快照。原子范围是注册表发布，不是之前编译、文件写入和全部外部副作用的事务。ensure_triton_hop_converter_registered仅成功注册后置标志，失败可重试；这个标志不构成任意多线程入口的完整保证。

## 转换时再次核对选中路由

_triton_hop_converter要求已发布路由和Mapping kwargs，再核对侧表是否仍存在、kernel_ref身份、launch tuple、默认值和参数来源、grid/TMA合同、输入标量ABI、输出key顺序及克隆键顺序。标量Sym与对应Python标量按int/float/bool类别匹配；不能把查到路由等同输入任意变化均安全。

静态grid/TMA必须与规格值相同；动态字段按既定秩、数量和整数ABI建GE输入。最后构造空attrs的custom_op，输出名按规格编号，再恢复dict key；它是生成GE节点，不是在此实际启动kernel。

## Python Execute恢复和实际启动

generate_triton_hop_execute复用相同REG_OP输入顺序，包装运行Tensor，按Python回调标量读取ABI恢复值，嵌入静态node constexpr，侧表常量仍由functional HOP读取。TMA按原encoding/kind恢复，动态字段读int/int_list并检查长度；静态grid直接嵌入，动态grid逐项读数量后构建。

生成代码在GE stream上下文调用torch.ops.higher_order.triton_kernel_wrapper_functional，传原侧表索引、恢复的grid/TMA、kwargs及clone名单，可选launch tuple。结果要求dict且预期key存在、对应值为Tensor；随后逐项contiguous，按GE输出描述分配并复制。runtime结果此处检查预期键，不另行要求没有额外键；不能和构图前的键集合检查混写。

它沿用Python回调的有限dtype、host标量placement和GE推导输出容量限制，没有切换到C++回调绕过这些限制的路线。侧表、kernel_ref与进程临时产物也不能当可跨进程迁移的稳定工件。

## 验证与关联

逐层核对目标身份、参数所有权、默认/autotune值、grid/TMA规格、侧表身份、克隆输出合同、GE输入索引及实际回调输出。生成成功、注册表发布和kernel数值/性能通过分别验收，本次只做静态全文审阅，没有执行任何生成或启动。

- [自定义算子预扫描](torchair_ge_custom_prescan_compilation.md)
- [Python runtime标量与输出限制](torchair_ge_python_callback_codegen.md)
- [Schema和REG_OP共同描述](torchair_ge_callback_schema_codegen.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_python.py)（implementation）
