---
type: API
title: ReinterpretCast
description: 将当前GlobalTensor重解释为用户指定的新类型。转换后的Tensor与原Tensor地址及内容完全相同，Tensor的内存大小（比特数）保持不变。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/ReinterpretCast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/kernel_tensor.h
---

# ReinterpretCast<a name="ZH-CN_TOPIC_0000002132450370"></a>

## 功能说明<a name="section618mcpsimp"></a>

将当前GlobalTensor重解释为用户指定的新类型。转换后的Tensor与原Tensor地址及内容完全相同，Tensor的内存大小（比特数）保持不变。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename CAST_T>
__aicore__ inline GlobalTensor<CAST_T> ReinterpretCast() const
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table4835205712588"></a>
<table><thead align="left"><tr id="row118356578583"><th class="cellrowborder" valign="top" width="17.77%" id="mcps1.2.3.1.1"><p id="p48354572582"><a name="p48354572582"></a><a name="p48354572582"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="82.23%" id="mcps1.2.3.1.2"><p id="p583535795817"><a name="p583535795817"></a><a name="p583535795817"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row18835145716587"><td class="cellrowborder" valign="top" width="17.77%" headers="mcps1.2.3.1.1 "><p id="p1383515717581"><a name="p1383515717581"></a><a name="p1383515717581"></a>CAST_T</p>
</td>
<td class="cellrowborder" valign="top" width="82.23%" headers="mcps1.2.3.1.2 "><p id="p18689719202918"><a name="p18689719202918"></a><a name="p18689719202918"></a>指定重解释后的新类型。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

重解释后的GlobalTensor。

## 约束说明<a name="section633mcpsimp"></a>

当数据类型发生转换后，元素个数可能无法取整，例如3个int4b\_t类型转换为uint32\_t，则转换后调用GetSize接口，只能获取向下取整的整数值，这种场景在CPU状态运行时，会有对应的提示告警信息。

## 调用示例<a name="section17531157161314"></a>

```cpp
uint64_t dataSize = 256; //设置input_global的大小为256

AscendC::GlobalTensor<int32_t> inputGlobal; // 类型为int32_t
inputGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t *>(src_gm), dataSize); // 设置源操作数在Global Memory上的起始地址为src_gm，所占外部存储的大小为256个int32_t

AscendC::LocalTensor<int32_t> inputLocal = inQueueX.AllocTensor<int32_t>();    
AscendC::DataCopy(inputLocal, inputGlobal, dataSize); // 将Global Memory上的inputGlobal拷贝到Local Memory的inputLocal上
...
// 假设inputGlobal为int32_t类型，包含16个元素（64字节）
// 调用ReinterpretCast将inputGlobal重解释为int16_t类型
AscendC::GlobalTensor<int16_t> interpreTensor = inputGlobal.template ReinterpretCast<int16_t>();
// 示例结果如下，二者数据完全一致，在物理内存上也是同一地址，仅根据不同类型进行了重解释
// inputGlobal:0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
// interpreTensor:0 0 1 0 2 0 3 0 4 0 5 0 6 0 7 0 8 0 9 0 10 0 11 0 12 0 13 0 14 0 15 0
```


<!-- cannbot:related:start -->
## 相关

- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：“转换后的Tensor与原Tensor地址及内容完全相同，Tensor的内存大小（比特数）保持不变。”给出焦点端事实；“xT = xIO.ReinterpretCast<CT>()”给出候选端事实。API 的同地址重解释合同解释了 runbook 中 xT 仍别名 xIO 的事实，并直接支撑 FreeTensor 早释后别名被复用内存覆盖的根因判断。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [MoeDistributeDispatch 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/mc2/moe_distribute_dispatch_950.md)（`related`）：算子声明的固定版本源码包含对 `ReinterpretCast(...)` 的直接调用（第 665 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/mc2/moe_distribute_dispatch_v2/op_kernel/moe_distribute_dispatch_v2.h#L665)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
