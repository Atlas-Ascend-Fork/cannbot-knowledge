---
type: Guide
title: GE Python回调：标量ABI、签名与输出写回
description: 核对生成的Python Execute签名、runtime dtype与host标量读取、逻辑输出/out排列及按GE规格分配后的复制边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_python.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py
  role: implementation
created_at: '2026-11-10T11:04:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE Python回调：标量ABI、签名与输出写回

## 固定快照与证据范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的custom_op_codegen_common.py、custom_op_codegen_cpp.py和custom_op_codegen_python.py，包含嵌入的生成代码模板。发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这三个同路径，仅记录路径事实，不否定其他发布入口。本文为静态实现合同，产品矩阵未知，保持draft与空平台；未导入上游、调用生成器、编译/加载动态库、读取设备地址或执行回调。

## 临时文件与执行签名

_ensure_py_dir首次建带PID前缀的临时目录，追加ASCEND_CUSTOM_OPP_PATH并保留原值，后续返回缓存；没有在此退出清理或刷新已缓存路径。GE逐次PreRun扫描的说明是源码注释，本次没有运行GE验证加载行为。

Python Execute签名来自同一build_reg_op_proto：GE输入按IR顺序作为位置参数，元数据属性作为关键字参数；out参数不作为GE输入，借ctx预分配。_safe_param_name靠追加下划线处理保留字和冲突，没有替换非法字符；不能宣称任意原始字符串都能由它变成合法标识符。

generate_python_op_file_source按zip(schemas,targets)生成类，不单独检查两表等长；generate_and_write_python_op_file用w写文件并返回目录，不代表GE已经导入、注册或执行成功。

## GE地址包装与dtype域

_wrap_ge_tensor_as_torch检查非None、地址非零，取storage_shape和runtime data_type，经有限映射后调用create_npu_tensors包装。它没有还原原始stride、storage_offset或普通共享Storage关系，也不是复制原始数据内容的函数。

Python映射只包含源码表中的常规浮点、整数、bool和复数；没有量化、FP8、HIFLOAT8/FP4等条目。该表手写模板预期的GE Python runtime整数编码，本次没有核对外部SDK完整码表，不能仅据注释认证编码一致；也不能直接与proto/图API同整数混用而报告冲突。目标dtype有无kernel仍需独立依据。

_ge_stream_context在ctx.get_stream非零时以当前NPU设备构造ExternalStream并进入torch.npu.stream，零则直接yield；没有在本文件证明跨设备、跨进程或所有生命周期安全。

## 标量读取有位置、dtype与逻辑字节门槛

_read_bytes_from_ge拒绝None、空地址、size=0，要求read_size为正int且不超存储大小，只允许TensorPlacement.ON_HOST/FOLLOWING并用ctypes.string_at读取；其他placement拒绝。虽然模板保留D2H常量，实际这条读取函数没有走设备复制，不能用C++回调的D2H能力替它背书。

_read_scalar_from_ge的int/enum为INT64、float为FP32、bool为1字节；Scalar/Scalar列表仅接受INT64或FP32。要求存储大小按元素字节对齐、shape_size为正int，标量逻辑数量恰为1，只读取逻辑字节而非全部padding。空列表、零尺寸、缺shape_size或不同dtype不由“支持列表”泛化为可接受。

str按UTF-8解码，str_list按零字节分割并去末尾空项；普通整/浮/布尔列表转对应Python/NumPy值。字符串中的零字节、尾空字符串及空存储仍需核对，不能由Const拼接视为无损格式承诺。

## out、逻辑返回和写回

is_out=True时，若Tensor[]返回出现在任何固定返回之前则生成阶段报错；Python绑定缺少相同物理输出实例索引查询，因此只允许固定返回在动态列表之前。out参数按已匹配返回索引预分配并包装；不代表任意out/列表排列都支持。

_normalize_outputs按逻辑Schema返回数处理：无返回只接受None或空序列；单个Tensor[]形成嵌套的一项列表；多个返回要求序列且长度准确。逻辑返回层与GE物理展开索引必须分开，不能直接flatten所有结果。

实际生成调用是torch.ops.namespace.op.overload(*args)，没有根据已保存is_kwarg_only另建调用kwargs；对于含关键字专用参数尤其out，应核对真实调用合同，不以Schema字段存在推导完整可用。本次未执行反例。

普通返回及inplace返回都先contiguous，非Tensor还可能torch.as_tensor。普通输出用GE推导描述分配，_copy_torch_into_ge只先比结果numel不超过GE容量，再dest.copy_；容量足够不等于所有shape、广播和dtype语义相同。inplace写回按前序参数累计物理输入索引，再make_output_ref_input；动态输入和out跳过会改变索引合同。

## 验证

核对生成签名与实际调用参数、runtime dtype域、地址/placement、标量逻辑数量、输出层级和GE分配描述；再分别验证精度、布局、原地写回及stream。此处只审阅生成模板，没有执行任何地址读取、内存复制、回调或设备实验。

- [Schema与REG_OP](torchair_ge_callback_schema_codegen.md)
- [C++回调差异](torchair_ge_cpp_callback_codegen.md)
- [文档级回调边界](ge_custom_op_callback_boundaries.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_python.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py)（implementation）
