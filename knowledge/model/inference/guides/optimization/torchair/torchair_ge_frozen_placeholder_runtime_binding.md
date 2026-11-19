---
type: Guide
title: GE固定权重占位的运行期地址与存储绑定
description: 解释ConstPlaceHolder从原FX输入取得地址、真实存储布局和字节数的时机，区分固定地址承诺与每次调用更新。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
created_at: '2026-11-10T11:19:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE固定权重占位的运行期地址与存储绑定

## 版本与定向范围

本卡静态核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的ConstPlaceHolder更新、运行期更新入口及frozenInput选项构造，相关逻辑一致。未执行地址变更、设备拷贝、缓存加载或性能实验；产品适用范围未知，保持draft与空平台。

## 占位索引指向原始FX参数

_update_constplaceholder_attr_from_inputs只处理带update_node_from_fx_input_idx的ConstPlaceHolder；没有该属性的节点跳过。GeConcreteGraph.update_graph_with_runtime把原FX args传给这个更新器，而内部格式更新使用经过getter处理的GE inputs。不能拿删除死输入、符号打包或非连续处理后的GE输入索引代替该FX索引。

绑定输入必须is_npu，否则AssertionError。更新器写入origin_shape、转换后的GE dtype及真实data_ptr；节点名追加该data_ptr，再统一重写消费者引用。这个名称规则用来区分同名但地址不同的占位，不是按权重内容生成缓存哈希。

## 字节数按真实存储计算

torch_npu已在sys.modules时，origin_format按四维选0、其他维选2；storage_shape来自GetNpuStorageSizes，storage_format来自get_npu_format，size为get_storage_size乘element_size。逻辑shape、存储shape和分配字节数分别取值，不能对带内部格式或padding的权重直接用numel乘element_size替代。

没有torch_npu模块的备用分支用shape、format=2和numel乘element_size，但前面的is_npu断言仍在；它不是普通CPU Tensor自动可用的支持承诺。该分支存在也不能证明真实NPU存储布局已按设备格式核验。

## 绑定发生在未编译阶段

update_graph_with_runtime先检查_is_compiled，已编译便立即返回；未编译时先绑定ConstPlaceHolder，再根据GE输入更新内部格式，之后才处理可选RefData。成功compile后，后续普通调用不会在这个入口重新写占位地址或检查地址改变。

因此，运行期函数名含update不表示每次换权重对象或更换存储都能自动重绑。根据这条静态控制流推断，固定权重的存储替换需要重新建立匹配的编译/缓存实例并验证输出；不能把旧图继续复用建立在本入口会发现新data_ptr的假设上。相同对象内更新内容与替换对象/存储是不同操作，其数值和生命周期仍需实际环境验证。

## frozenInput与ConstPlaceHolder分别核对

_normalize_ge_option另外按experimental_config.frozen_parameter决定frozenInput标记列表；关闭时为各GE输入生成0，打开时调用get_frozen_flag。这个列表依据_input_info_list，而ConstPlaceHolder地址取原FX args，两者不是同一输入索引空间，也不代表已固化整个输入Tensor内容。

实现中的Torch版本2.5.1判断只控制警告文本，不能据此改写公开文档的mark_static_address支持版本。配置入口、输入身份、地址保持和版本约束按[固定地址契约](../../../optimizations/rules/frozen_parameter_address_contract.md)核对。

- [占位创建与死输入重写](torchair_ge_input_rewrites.md)
- [首次调用与运行期编译](torchair_ge_runtime_binding_and_first_call.md)

## Evidence

- [主线运行期更新](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（primary）：708–746、1197–1198、1313–1346、2006–2024。
- [发布运行期更新](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：532–567、1069–1102及_normalize_ge_option对应frozenInput分支；只记已审阅函数范围。

## 普通 Data/RefData 的内部格式绑定

固定主线的 `_update_internal_format_from_inputs` 与发布对应函数是另一条运行期输入处理：它们操作 Data/RefData 的描述符，不能与前文 ConstPlaceHolder 的权重地址、存储字节数更新混为一谈。本节补充两版完整局部函数及其支持格式集合；既有未编译入口和输入索引区别仍按前文证据保留，没有重新审计整个转换器或底层格式转换实现。

两版先检查 `'torch_npu' in sys.modules`；模块未加载就记录信息并返回，不主动导入或尝试把所有输入转换成 NPU 格式。已加载时，从 Data/RefData 节点的 `index` 属性建立字典，再按 `runtime_inputs` 的枚举位置处理；非 NPU Tensor 跳过。这里先用字典长度检查输入序号上界，再以序号取条目，并不独立证明节点 index 连续或没有重复；不能把这个局部检查当成完整图输入结构验证。

对 NPU 输入调用已加载模块的 `get_npu_format`。两版本地接受集合相同：UNDEFINED、NCHW、NHWC、ND、NC1HWC0、FRACTAL_Z、FRACTAL_NZ、NCDHW、NDC1HWC0、FRACTAL_Z_3D，以及 FRACTAL_NZ_C0 的 2/4/8/16 四种变体。集合之外走错误分支；集合之内也只是本地描述符更新准入，不是所有相关 Kernel、dtype、shape、产品的支持表。

通过后，两版都先把运行时格式写到该输入的 output_desc[0] 与 input_desc[0] 的 `format_for_int`，再按下表决定是否补原始格式。

| 运行时存储格式 | 写入 output_desc 的 origin_format |
| --- | --- |
| FRACTAL_NZ 与四种 NZ_C0 变体 | ND |
| FRACTAL_Z、NC1HWC0 | NCHW |
| FRACTAL_Z_3D、NDC1HWC0 | NCDHW |
| 其余本地接受格式 | 此分支不额外写 origin_format |

仅当确定了上述 origin_format，且外部 `_is_gte_cann_version('8.2.RC1')` 返回真，函数才进一步把节点 `_enable_storage_format_spread` 设为 False、清空 output_desc 的 shape.dim、将运行时逻辑 shape 追加到 `origin_shape.list.i` 并设其类型为 2，写入 origin_shape_initialized/origin_format_is_set 标志；随后弹出首个 input_desc，追加 output_desc 副本，再令 input_desc[0].name 为 `x`。低版本或 helper 返回假时，前面写入格式与原始格式的动作仍可能已发生，不能简化成“版本不满足则整个更新都不做”。本卡未执行该 helper，也未展开其版本解析或设备行为。

清空的是 shape.dim，`origin_shape.list.i` 在本地只 `extend`，没有先清空；函数也没有对整次描述符更新建立事务或失败回滚。因此不能从 update 名称推断未编译阶段重复进入一定幂等，或后续失败时前面写入已撤销。这是源码写法及可能的重入边界，没有执行重复调用实验。

主线在处理完输入后额外调用 `validate_grouped_matmul_weight_nz(graph)`，发布对应函数没有这次调用；没有 torch_npu 时的早返回也不会走到主线末尾校验。校验本身的架构、祖先和 dtype 限制见[GE 量化矩阵乘重写与 NZ 校验](torchair_ge_quant_matmul_graph_rewrites.md)，本节只补真实调用位置，不重新资格化校验实现，更不推断发布的其他路径没有任何检查。

这里修改 GE 描述符，没有显式把运行时 Tensor 转成指定格式或拷贝权重。诊断时分别记录 getter 后的 GE 输入位置、实际 NPU 格式、存储布局、描述符前后值及 helper 分支，结合前文未编译入口核对首次运行；不能把这些属性写入当成运行时数据已完成格式转换、收益已测量或后续任意换存储都能重绑的证明。

## 内部格式增补 Evidence

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（primary）：242–257、588–705；只补完整局部格式集合与更新函数，旧权重/调用入口证据原样保留。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：147–162、421–529；只补完整局部格式集合与更新函数，旧权重/调用入口证据原样保留。
