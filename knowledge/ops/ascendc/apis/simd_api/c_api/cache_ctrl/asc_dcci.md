---
type: API
title: AscDcci
description: 刷新Data Cache保证与GM一致性，支持单Cache Line刷新和整片刷新，用于多核数据一致性和Scalar写GM场景。
tags:
- task.lookup
- topic.data_movement.memory_access
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cache_ctrl/asc_dcci.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# asc_dcci

## 功能说明

在AI Core内部，Scalar单元和DMA单元都可能对Global Memory进行访问。

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/SIMD-API/c_api/figures/dcci.png "DataCache内存层次示意图") \\

如上图所示：

DMA搬运单元读写Global Memory，数据通过[asc_copy_ub2gm](../vector_datamove/asc_copy_ub2gm/index.md)和[asc_copy_gm2ub](../vector_datamove/asc_copy_gm2ub/index.md)等接口在Unified Buffer（UB）等Local Memory和Global Memory间交互，没有Cache一致性问题；
Scalar单元访问Global Memory，首先会访问每个核内的Data Cache，因此存在Data Cache与Global Memory的Cache一致性问题。
该接口用来刷新Cache，保证Cache的一致性，使用场景如下：

读取Global Memory的数据，但该数据可能在外部被其余核修改，此时需要使用asc_dcci接口，直接访问Global Memory，获取最新数据；
用户通过Scalar单元写Global Memory的数据，希望立刻写出，也需要使用asc_dcci接口。

Scalar单元访问UB数据时，该接口需配合[asc_set_ctrl()](../spr/asc_set_ctrl.md)接口使用，将CTRL[49]设置为1'b1，开启datacache模式。


针对Ascend 950PR/Ascend 950DT，不支持asc_dcci_entire_ub接口。


## 函数原型

   ```cpp
   // 刷新传入地址所在的单个Cache Line
   __aicore__ inline void asc_dcci_single(__gm__ void* dst)

   // 刷新传入的UB地址空间地址所在的单个Cache Line
   __aicore__ inline void asc_ub_dcci_single(__ubuf__ void* dst)

   // 刷新所有Cache Line
   __aicore__ inline void asc_dcci_entire_all()
   __aicore__ inline void asc_dcci_entire_ub()
   __aicore__ inline void asc_dcci_entire_out()
   __aicore__ inline void asc_dcci_entire_atomic()
   ```

## 参数说明

**表1** 参数说明

| 参数名 | 输入/输出 | 描述 |
| :--- | :--- | :--- |
| dst | 输入 | 需要刷新缓存的向量的起始地址。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

无

## 调用示例

```cpp
// 示例：SINGLE_CACHE_LINE模式（x_gm 64B对齐场景）
// 假设x为外部传入的地址，每个核计算16个数据，block_idx为内置变量，通过block_idx计算偏移实现多核间数据隔离
__gm__ float* x_gm = x + block_idx * 16;
for (int i = 0; i < 16; i++) {
    x_gm[i] = static_cast<float>(i + block_idx);
}
// 由于首地址64B对齐，调用asc_dcci_single指令后，数据会立刻刷新到Global Memory
asc_dcci_single(reinterpret_cast<__gm__ uint64_t*>(x_gm));
```


<!-- cannbot:related:start -->
## 相关

- [arch35 小 per-channel 输出读旧值判别与规避](../../../../runbooks/compilation/arch35_per_channel.md)（`exemplifies`）：Runbook 的直接信号是“per-channel ［C］ 小输出经 `DataCopyPad` 写 GM 后，host/下游读到旧值或错值”；asc_dcci 的适用条件是“读取Global Memory的数据，但该数据可能在外部被其余核修改，此时需要使用asc_dcci接口，直接访问Global Memory，获取最新数据；”。API语义帮助判定该旧值现象是否属于多核缓存一致性路径。
- [AscAtomicExch](../atomic/scalar_atomic/asc_atomic_exch.md)（`related`）：原子交换接口明确“Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。”；缓存接口解释“Scalar单元访问Global Memory，首先会访问每个核内的Data Cache，因此存在Data Cache与Global Memory的Cache一致性问题。”，给出交换前后插入 DCCI 的一致性原因。
- [AscAtomicInc](../atomic/scalar_atomic/asc_atomic_inc.md)（`related`）：原子递增接口明确“Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。”；缓存接口解释“Scalar单元访问Global Memory，首先会访问每个核内的Data Cache，因此存在Data Cache与Global Memory的Cache一致性问题。”，给出原子计数器与普通 Scalar/DMA 访问混用时必须补 DCCI 的原因。
- [AscAtomicMax](../atomic/scalar_atomic/asc_atomic_max.md)（`related`）：需要调用asc_dcci接口确保GM与DCache的一致性；存在Data Cache与Global Memory的Cache一致性问题；连接原子操作的明确后置要求与缓存一致性契约。
- [AscAtomicSub](../atomic/scalar_atomic/asc_atomic_sub.md)（`related`）：Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。；该接口用来刷新Cache，保证Cache的一致性；AscAtomicSub 明确产生绕过 DCache 的 GM 更新，AscDcci 提供后续缓存一致性动作，二者构成原子写后的必要维护链。
- [AscAtomicXor](../atomic/scalar_atomic/asc_atomic_xor.md)（`related`）：AscAtomicXor 卡告警“Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。”；AscDcci 卡解释“用户通过Scalar单元写Global Memory的数据，希望立刻写出，也需要使用asc_dcci接口。”，给出原子写 GM 后刷新缓存的直接一致性合同。
<!-- cannbot:related:end -->
