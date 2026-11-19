---
type: Guide
title: GE C++回调：IR索引、Dispatcher与动态输出
description: 核对生成的C++ Execute类型映射、D2H标量、IR/物理索引、out作用域疑点及真实输出分配和异步回写。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_cpp.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py
  role: implementation
created_at: '2026-11-10T11:04:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE C++回调：IR索引、Dispatcher与动态输出

## 固定快照与证据范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的custom_op_codegen_common.py、custom_op_codegen_cpp.py和custom_op_codegen_python.py，包含嵌入的生成代码模板。发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这三个同路径，仅记录路径事实，不否定其他发布入口。本文为静态实现合同，产品矩阵未知，保持draft与空平台；未导入上游、调用生成器、编译/加载动态库、读取设备地址或执行回调。

## C++生成与REG_OP分工

generate_cpp_source按zip配对Schema和GE名称，始终生成REG_OP；仅cpp_op_indices选中的项生成Execute类与REG_AUTO_MAPPING_OP，以及TorchNPU/ACL相关头和辅助函数。未选项仍需原型注册，不等于没有C++编译；该文件没有单独校验两列表等长。

## dtype、地址与标量ABI

MapGeDtypeToTorch/MapTorchDtypeToGe覆盖源码列出的常规浮点、整数、无符号整数、bool、complex64/128、qint8/quint8/qint32及三种FP8；其他分支TORCH_CHECK失败。没有在此映射HIFLOAT8、FP4或complex32。类型翻译存在不等于每个产品和原始算子支持全部类型。

CreateNpuTensor只取GE地址与storage shape，用PrivateUse1 from_blob包装；没有重建任意stride/offset或普通输入输出别名。ReadScalarInput按GE GetSize分配字节buffer并总是aclrtMemcpy D2H，检查返回码；它没有Python回调相同的host placement分支或逻辑shape_size校验。

int按INT64读、float按FP32再转double、bool按uint8读；Scalar仅区分GE INT64和其余FP32读取路线，列表数量按buffer字节除元素宽度，没有在这些提取器统一检查余数或标量最小长度。enum提取硬编码为at::ScalarType，不能由共同enum分类推广到任意Device/Layout/MemoryFormat恢复语义。

字符串读到首个零字节或buffer末，字符串列表按零分隔并只在末段非空时追加；不能把包含零字节和末尾空项的输入当作已证明无损。Optional缺值可写Schema默认值或空IValue；各类型默认分支与原型输入缺失是不同层。

## IR输入索引、物理展开与out预分配

普通输入提取按IR索引：required/optional使用对应GetRequiredInputTensor/GetOptionalInputTensor，Tensor[]用GetDynamicInputTensor(ir_idx,i)展开；out不占GE输入。inplace写回另累计运行期物理输入数量，不能混用两种索引。

out返回预分配时会用GetIrOutputInstanceInfo跳过之前Tensor[]展开数，C++模板意图支持与Python不同的排列。不过静态模板有作用域缺口：ge_out_i声明在每个out返回生成的花括号块内，后面的args.emplace_back(CreateNpuTensor(ge_out_i))位于块外。不能把文档或代码分支存在写成该快照所有out生成代码均已编译通过；本次没有运行生成器或编译复现。

## stream、Dispatcher与回写

生成代码从ctx取stream、读当前设备，再getStreamFromExternal和NPUStreamGuard；Dispatcher按准确Schema名/overload findSchemaOrThrow并callBoxed，随后访问npu_stream.stream(true)。局部代码没有检查aclrtGetDevice返回码，也没有提供跨设备完整保证。

普通结果先contiguous，根据真实Torch结果建立origin/storage shape、dtype和字节数，再MallocOutputTensor及异步D2D复制；与Python按GE已有描述分配的机制不同。列表结果逐元素增加物理输出索引；out返回跳过后续复制。

inplace结果先contiguous，要求结果字节数等于原输入GetSize，再异步复制到输入并MakeOutputRefInput。动态列表前序索引展开使用Schema位置生成访问式，含out等组合时仍需与IR索引核对；字节相等也不能独立证明原始stride/offset语义。

普通和inplace的aclrtMemcpyAsync以及MakeOutputRefInput调用没有在这些模板行统一检查返回码；return ge::SUCCESS不是完整设备正确性和异步完成验证。实际stream顺序、源Tensor生命周期和数值仍须匹配栈实验，本次未执行。

- [Schema和别名匹配](torchair_ge_callback_schema_codegen.md)
- [Python分配与标量读取差异](torchair_ge_python_callback_codegen.md)
- [预编译和动态库生命周期](torchair_ge_custom_prescan_compilation.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_cpp.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/custom_op_codegen_common.py)（implementation）
