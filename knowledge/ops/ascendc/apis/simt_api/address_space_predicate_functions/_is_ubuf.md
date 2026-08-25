---
type: API
title: __isUbuf
description: 判断输入的指针是否指向Unified Buffer内存空间的地址。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_predicate_functions/__isUbuf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isUbuf

判断输入的指针是否指向Unified Buffer内存空间的地址。
函数原型：unsigned int __isUbuf(const void* ptr)
返回值：如果输入的指针指向Unified Buffer内存空间的地址，则返回1，否则返回0。
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Reg LoadAlign 不接受 const __ubuf__ 指针](../../../runbooks/compilation/reg_loadalign_requires_nonconst_ubuf_pointer.md)（`exemplifies`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《Reg LoadAlign 不接受 const __ubuf__ 指针》明确“CANN 9.0.1 RegBase 的两参数 LoadAlign/StoreAlign 要求非 const UB 指针；const 会让 VF 封装与 asc_vf_call 编译失败。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [SIMT __ubuf__ 静态数组 UB 占用不随分支释放](../../../runbooks/compilation/simt_ubuf_ub.md)（`exemplifies`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《SIMT __ubuf__ 静态数组 UB 占用不随分支释放》明确“SIMT kernel 的 __ubuf__ 静态数组是编译期分配、生命周期绑所在函数栈的 UB 资源，运行时分支只控制是否解引用、不控制是否占用；把“需要该数组”与“不需要该数组”两条路径塞进同一函数，会令不解引用的路径也白白占住 UB。给出按解引用关系拆函数的判别方法。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [__aicore__ 禁止 void* 转 __ubuf__ 桥接](../../../runbooks/compilation/aicore_void_ubuf.md)（`exemplifies`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《__aicore__ 禁止 void* 转 __ubuf__ 桥接》明确“dav-3510 上为混合 dtype Reg wrapper 用 void* 形参 + 内部 (__ubuf__ T*) 强转桥接 LocalTensor<half> 与 LocalTensor<float>，编译报 casting 'void *' to type '__ubuf__' not allowed in aicore function（5 处）；void* 桥接路线 banned，须改 const LocalTensor<T>& 形参 + 内部 GetPhyAddr()。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [__ubuf__ 指针传普通形参导致编译失败](../../../runbooks/compilation/ubuf_pointer_preserves_address_space.md)（`exemplifies`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《__ubuf__ 指针传普通形参导致编译失败》明确“Ascend C 地址空间是类型的一部分；__ubuf__ 指针不能隐式绑定到普通 T* 形参，未使用参数应删除或按真实地址空间声明。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [__cvta_generic_to_ubuf](../address_space_conversion_functions/_cvta_generic_to_ubuf.md)（`related`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《__cvta_generic_to_ubuf》明确“将输入的指针转换为其指向的Unified Buffer内存空间的地址值并返回。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [__cvta_ubuf_to_generic](../address_space_conversion_functions/_cvta_ubuf_to_generic.md)（`related`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《__cvta_ubuf_to_generic》明确“将Unified Buffer内存空间的地址值转换为对应的指针并返回。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [地址空间谓词函数](address_space_predicate_functions.md)（`same_topic`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《地址空间谓词函数》明确“SIMT API地址空间谓词函数汇总，提供判断指针是否指向Global、UBuf、Local地址空间的断言能力。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
<!-- cannbot:related:end -->
