---
type: Guide
title: GE元数据辅助：符号形状、占位与候选声明
description: 全文核对TorchAir元数据辅助与Support类，区分占位结果、符号hint、容器版本差异、图诊断和候选声明的证据边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/supported_declaration.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/supported_declaration.py
  role: implementation
created_at: '2026-11-10T10:15:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE元数据辅助：符号形状、占位与候选声明

## 固定版本与证据范围

全文审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的_ge_concrete_graph/utils.py和supported_declaration.py。两版声明类AST相同；utils的Mapping处理、host标志、hint导入回退与deadlock包装存在版本差异。此前只读局部函数的utils在本次补齐全文，不按旧引用提前计为完成。

本文限定辅助函数的静态合同，整卡产品矩阵未知，保持draft与空平台；未导入或执行上游、分配Torch张量、运行声明用例、调用设备或做NPU实验。此处辅助函数只说明元数据和图的处理，不替代完整IR/kernel、精度与性能验证。

## 指定dtype、布局标志和诊断显示分开解释

dtype_promote必须至少一个参数；target_dtype为Torch dtype对象时先翻译GE枚举。GE Tensor或torch.Tensor类型不同时才Cast，非Tensor转指定dtype Const；单输入返回对象，多输入tuple。它不推断公共类型或自动统一shape，具体运算的调用顺序见[算术转换](torchair_ge_arithmetic_lowering.md)。

specific_op_input_layout/output_layout只向节点的layout属性追加索引与字符串；force_op_unknown_shape设置_force_unknown_shape=True，主线set_host_tensor设置_host_tensor=True，发布utils没有后一函数。标记不执行Transpose、数据搬运或设备迁移，也不能由unknown标志认证全部动态维度已支持。

_display_ge_type按有限字典返回名称，否则unknown；该字典未涵盖新HIFLOAT8/FP8/FP4名字，日志unknown不证明类型不存在或kernel不支持。normalize_min/max对限定整型名单用iinfo，其他回退正负inf，不是所有GE枚举的完整有限值范围表。

is_integral_type只把INT8/UINT8/INT16/INT32/INT64认作整型，BOOL由include_bool控制，没有把所有无符号新类型都纳入；is_complex只对torch.Tensor的complex32/64/128返回True。不能把辅助分类函数与整个后端dtype矩阵混用。

## 占位结果不是实际模型输出

make_real_tensor_like对tuple/list递归后均返回list；主线另支持Mapping并保留key，发布版没有这个分支。叶子在no_dispatch下以Meta的size/dtype创建torch.empty，调用内部常量构造再set_meta；没有从真实模型取得数值，也没有在此处填写输出内容，不能拿该占位当精度基准或实际执行结果。

flatten_meta_outputs主线递归Mapping的values及tuple/list，输出扁平list，字典key不进入结果；发布版只递归tuple/list，Mapping会作为整体叶子。容器结构、叶子顺序和形状恢复是不同合同，不能用“都能flatten”掩盖两版字典行为。

## 符号收集、hint和Python固化

get_used_syms_in_meta对符号标量取expr.free_symbols，对Tensor元数据还收集storage_offset、size、stride中的符号；get_used_sym_value_mapping要求每个符号已在输入索引映射，否则AssertionError。compute_value_of_sym从args位置取值，get_sym_int_value对表达式subs后转Python int，generate_sym_exper也提取node.expr。这些是Python元数据计算，不是自动建立运行期GE符号运算图。

generate_shape_from_tensor对SymInt先尝试int(str(dim))，失败回退-1；generate_real_shape_from_tensor失败时改取hint_int。主线hint_int导入ImportError时用optimization_hint别名，发布版直接导入hint_int。hint是编译输入线索，不应被描述为所有运行尺寸固定、已检查范围或实际shape已执行。

_append_real_input_shape按索引和real_shape拼ge.inputHintShape编译选项字符串；此函数只生成字典与日志，不独立证明调用方应用了该选项或收益。convert_tensor_to_list/dtype读取attr_tensor._meta并转Python列表或标量，不能据Tensor形参宣称保持动态属性，见[卷积属性固化](torchair_ge_convolution_lowering.md)。

## 图输入位置和边重命名

get_graph_input_placements仅遍历Data节点，从output_desc[0].device_type区分CPU/HOST与NPU/DEVICE；拒绝其他设备类型，并要求Data索引不超上界且所有位置都填齐，报错要求先重排，本函数不负责重排。is_host_data_tensor却检查Data的input_desc[0].device_type，字段位置不能混写。

_get_input_shape包含Data和RefData，从input_desc[0]取shape，按index放入列表；_get_output_shapes从NetOutput输入描述符收集shape。这些图规格不等于设备实测shape，RefData与普通Data的统计职责也不同。

update_op_input_name_from_mapping跳过空输入边，要求非空边按冒号分成两段，再替换映射命中的节点名并保留输出索引；它不在此层重排数据、推导类型或证明控制依赖执行完成。

## 图转储和死锁检查包装

convert_to_tensorboard尝试导入TensorFlow，失败打印信息并返回None；成功时把GE节点与描述符转换成TF GraphDef展示，属性以字符串保存，输入索引-1转^控制边。convert_to_pbtxt用自有文本构造器形成相似展示，不需要前者的TensorFlow导入；两者都不是完整运行结果或可无损回读的GE序列化保证。

dump_graph的path=None直接返回，经PathManager检查后，txt写str(graph)，py写graph.python_code，其他后缀尝试pbtxt并捕获转换异常打印失败。不能把产生某个文件名等同该格式已完整转换成功。

主线run_deadlock_check先读torch.npu当前设备的vector_core_num，再filter_comm_ops并调用deadlock_check，发布utils没有此包装。它需要设备属性入口，不可宣传为本函数完全不触设备的离线检查；函数调用本身也不证明真实多rank无死锁。本文没有调用它。

## Support只是候选描述，检查还有嵌套边界

_TypedTensor保存dims、dtype、value与value_range，range只检查长度2；构造器没有完整验证维度、值域顺序、广播或产品能力。F32/F16/F64/I32/I16/I64/I8/U8/C64接收value_range；BF16和BOOL的对应构造器没有该关键字；T(value,dtype=...)保存显式value。缺少某个类型的便捷类不等于后端拒绝该dtype。

Support保存args/kwargs和空title，禁止直接torch.Tensor候选：位置参数若为list/tuple，只检查一层元素；关键字值只检查值本身，没有对任意嵌套容器递归。按条件静态推断，关键字list中的Tensor不会在这个浅层检查里被逐项识别；本次未执行例子，不能将这种遗漏写成被正式支持的用例形式。

__str__/__repr__和Support格式化只是描述文本；本模块没有实际Tensor生成、测试执行或结果验收。还需分别确认测试生成器、匹配前提、设备运行与数值检查，不能以Support列表或声明数量宣称全部知识/性能已验证。

## 验证与关联

核对具体调用方的目标dtype、容器结构、符号来源与hint、Data/RefData描述符、graph dump失败状态和声明嵌套层级；若需性能或正确性结论，再在匹配软件栈做独立实验。本卡没有运行这些实验。

- [Converter注册与内建/Prims层次](torchair_ge_registration_prims_lowering.md)
- [集合通信归约与图元数据](torchair_ge_collective_lowering.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/supported_declaration.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/supported_declaration.py)（implementation）
