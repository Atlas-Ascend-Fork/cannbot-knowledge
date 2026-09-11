---
type: API
title: InitBufPool
description: 初始化TBufPool内存资源池，适用于内存资源有限时手动指定UB/L1内存资源复用的场景。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/InitBufPool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_tpipe.h
---

# InitBufPool<a name="ZH-CN_TOPIC_0000001912722601"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

初始化TBufPool内存资源池。本接口适用于内存资源有限时，希望手动指定Unified Buffer（UB）/L1内存资源复用的场景。本接口初始化后在整体内存资源中划分出一块子资源池。划分出的子资源池TBufPool，提供了如下方式进行资源管理：

-   TPipe::InitBufPool的重载接口指定与其他TBufPool子资源池复用;
-   TBufPool::[InitBufPool](../t_buf_pool/init_buf_pool.md)接口对子资源池继续划分；
-   TBufPool::[InitBuffer](../t_buf_pool/init_buffer.md)接口分配Buffer；

关于TBufPool的具体介绍及资源划分图示请参考[TBufPool](../t_buf_pool/index.md)。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <class T>
__aicore__ inline bool InitBufPool(T& bufPool, uint32_t len)
template <class T, class U>
__aicore__ inline bool InitBufPool(T& bufPool, uint32_t len, U& shareBuf)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table4835205712588"></a>
<table><thead align="left"><tr id="row118356578583"><th class="cellrowborder" valign="top" width="18.47%" id="mcps1.2.3.1.1"><p id="p48354572582"><a name="p48354572582"></a><a name="p48354572582"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="81.53%" id="mcps1.2.3.1.2"><p id="p583535795817"><a name="p583535795817"></a><a name="p583535795817"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row1835857145817"><td class="cellrowborder" valign="top" width="18.47%" headers="mcps1.2.3.1.1 "><p id="p5835457165816"><a name="p5835457165816"></a><a name="p5835457165816"></a>T</p>
</td>
<td class="cellrowborder" valign="top" width="81.53%" headers="mcps1.2.3.1.2 "><p id="p1334183893115"><a name="p1334183893115"></a><a name="p1334183893115"></a>bufPool的类型。</p>
</td>
</tr>
<tr id="row18835145716587"><td class="cellrowborder" valign="top" width="18.47%" headers="mcps1.2.3.1.1 "><p id="p2023982513308"><a name="p2023982513308"></a><a name="p2023982513308"></a>U</p>
</td>
<td class="cellrowborder" valign="top" width="81.53%" headers="mcps1.2.3.1.2 "><p id="p1386393113012"><a name="p1386393113012"></a><a name="p1386393113012"></a>shareBuf的类型。</p>
</td>
</tr>
</tbody>
</table>

**表2**  参数说明

<a name="table5376122715308"></a>
<table><thead align="left"><tr id="row1337716275309"><th class="cellrowborder" valign="top" width="12.36%" id="mcps1.2.4.1.1"><p id="p1537762711305"><a name="p1537762711305"></a><a name="p1537762711305"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="12.370000000000001%" id="mcps1.2.4.1.2"><p id="p153771127123013"><a name="p153771127123013"></a><a name="p153771127123013"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="75.27000000000001%" id="mcps1.2.4.1.3"><p id="p17377162715303"><a name="p17377162715303"></a><a name="p17377162715303"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row19377627133012"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.2.4.1.1 "><p id="p55733283248"><a name="p55733283248"></a><a name="p55733283248"></a>bufPool</p>
</td>
<td class="cellrowborder" valign="top" width="12.370000000000001%" headers="mcps1.2.4.1.2 "><p id="p1357372832410"><a name="p1357372832410"></a><a name="p1357372832410"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.27000000000001%" headers="mcps1.2.4.1.3 "><p id="p1457322822419"><a name="p1457322822419"></a><a name="p1457322822419"></a>新划分的资源池，类型为TBufPool。</p>
</td>
</tr>
<tr id="row13377162793019"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.2.4.1.1 "><p id="p1357312818241"><a name="p1357312818241"></a><a name="p1357312818241"></a>len</p>
</td>
<td class="cellrowborder" valign="top" width="12.370000000000001%" headers="mcps1.2.4.1.2 "><p id="p857319288247"><a name="p857319288247"></a><a name="p857319288247"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.27000000000001%" headers="mcps1.2.4.1.3 "><p id="p17573122810249"><a name="p17573122810249"></a><a name="p17573122810249"></a>新划分资源池长度，单位为Byte，非32Bytes对齐会自动补齐至32Bytes对齐。</p>
</td>
</tr>
<tr id="row1371133216245"><td class="cellrowborder" valign="top" width="12.36%" headers="mcps1.2.4.1.1 "><p id="p1417710361241"><a name="p1417710361241"></a><a name="p1417710361241"></a>shareBuf</p>
</td>
<td class="cellrowborder" valign="top" width="12.370000000000001%" headers="mcps1.2.4.1.2 "><p id="p15177113615246"><a name="p15177113615246"></a><a name="p15177113615246"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="75.27000000000001%" headers="mcps1.2.4.1.3 "><p id="p11771236152417"><a name="p11771236152417"></a><a name="p11771236152417"></a>被复用资源池，类型为TBufPool，新划分资源池与被复用资源池共享起始地址及长度。</p>
</td>
</tr>
</tbody>
</table>

## 约束说明<a name="section633mcpsimp"></a>

-   新划分的资源池与被复用资源池的硬件属性需要一致，两者共享起始地址及长度；
-   输入长度需要小于等于被复用资源池长度；
-   其他泛用约束参考[TBufPool](../t_buf_pool/index.md)。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>

由于物理内存的大小有限，在计算过程没有数据依赖的场景或数据依赖串行的场景下，可以通过指定内存复用解决资源不足的问题。完整算子样例参考：[tbufpool\_management样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/04_memory_management/tbufpool_management)。

```cpp
// 声明一个指向TPipe管道对象的指针
AscendC::TPipe* pipe;
// 定义两个子资源池对象tbufPool1和tbufPool2
AscendC::TBufPool<AscendC::TPosition::VECCALC> tbufPool1, tbufPool2;
// 初始化第一个子资源池tbufPool1
pipe->InitBufPool(tbufPool1, bufSize * 3);
// 初始化第二个子资源池tbufPool2，并指定tbufPool2复用tbufPool1的起始地址及长度；
pipe->InitBufPool(tbufPool2, bufSize * 3, tbufPool1);

// 计算串行，不存在数据踩踏，实现了内存复用及自动同步的能力
tbufPool1.InitBuffer(srcQue0, 1, bufSize);
tbufPool1.InitBuffer(srcQue1, 1, bufSize);
tbufPool1.InitBuffer(dstQue0, 1, bufSize);
CopyIn();
Compute(); 
CopyOut();
tbufPool1.Reset();
tbufPool2.InitBuffer(srcQue2, 1, bufSize);
tbufPool2.InitBuffer(srcQue3, 1, bufSize);
tbufPool2.InitBuffer(dstQue1, 1, bufSize);
CopyIn1();
Compute1();
CopyOut1();
tbufPool2.Reset();
```


<!-- cannbot:related:start -->
## 相关

- [ExternImplBufpool](../custom_t_buf_pool/extern_impl_bufpool.md)（`related`）：焦点卡规定“自定义TBufPool之前，必须通过TPipe::InitBufPool接口进行TBufPool内存资源池初始化”，候选卡说明初始化后“在整体内存资源中划分出一块子资源池”；该调用是使用自定义宏前不可省略的资源准备步骤。
- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：TBufPool::InitBuffer接口分配Buffer；调用TBufPool::InitBuffer接口为TQue/TBuf进行内存分配。。焦点接口先从整体内存划分子资源池，候选接口再从该 TBufPool 向 TQue/TBuf 分配具体 Buffer。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 5 / 5 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `InitBufPool(...)` 的直接调用（第 347 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_mem_friendly.h#L347)
- [MoeDistributeDispatch A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch.md)（`related`）：算子声明的固定版本源码包含对 `InitBufPool(...)` 的直接调用（第 926 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_v2_full_mesh.h#L926)
- [MoeDistributeDispatch 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_950.md)（`related`）：算子声明的固定版本源码包含对 `InitBufPool(...)` 的直接调用（第 926 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_v2_full_mesh.h#L926)
- [NormRopeConcatGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/posembedding/norm_rope_concat_grad.md)（`related`）：算子声明的固定版本源码包含对 `InitBufPool(...)` 的直接调用（第 710 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/posembedding/norm_rope_concat_grad/op_kernel/norm_rope_concat_grad.h#L710)
- [NormRopeConcatGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/posembedding/norm_rope_concat_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `InitBufPool(...)` 的直接调用（第 710 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/posembedding/norm_rope_concat_grad/op_kernel/norm_rope_concat_grad.h#L710)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
