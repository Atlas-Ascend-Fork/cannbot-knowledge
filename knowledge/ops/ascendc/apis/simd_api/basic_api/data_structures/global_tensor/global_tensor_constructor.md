---
type: API
title: GlobalTensor构造函数
description: GlobalTensor构造函数。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.development_mode.tensor_programming
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GlobalTensor_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
---

# GlobalTensor构造函数<a name="ZH-CN_TOPIC_0000002167642833"></a>

## 功能说明<a name="section618mcpsimp"></a>

GlobalTensor构造函数。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline GlobalTensor<T>() {}
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

<a name="table4835205712588"></a>
<table><thead align="left"><tr id="zh-cn_topic_0000001429830437_row118356578583"><th class="cellrowborder" valign="top" width="16.28%" id="mcps1.2.3.1.1"><p id="zh-cn_topic_0000001429830437_p48354572582"><a name="zh-cn_topic_0000001429830437_p48354572582"></a><a name="zh-cn_topic_0000001429830437_p48354572582"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="83.72%" id="mcps1.2.3.1.2"><p id="zh-cn_topic_0000001429830437_p583535795817"><a name="zh-cn_topic_0000001429830437_p583535795817"></a><a name="zh-cn_topic_0000001429830437_p583535795817"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="zh-cn_topic_0000001429830437_row1835857145817"><td class="cellrowborder" valign="top" width="16.28%" headers="mcps1.2.3.1.1 "><p id="zh-cn_topic_0000001429830437_p5835457165816"><a name="zh-cn_topic_0000001429830437_p5835457165816"></a><a name="zh-cn_topic_0000001429830437_p5835457165816"></a>T</p>
</td>
<td class="cellrowborder" valign="top" width="83.72%" headers="mcps1.2.3.1.2 "><p id="zh-cn_topic_0000001429830437_p168351657155818"><a name="zh-cn_topic_0000001429830437_p168351657155818"></a><a name="zh-cn_topic_0000001429830437_p168351657155818"></a>GlobalTensor的数据类型。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

无。

## 约束说明<a name="section633mcpsimp"></a>

无。

## 调用示例<a name="section17531157161314"></a>

参考[调用示例](set_global_buffer.md#section17531157161314)。


<!-- cannbot:related:start -->
## 相关

- [SetGlobalBuffer](set_global_buffer.md)（`related`）：GlobalTensor 默认构造函数，创建空的 GlobalTensor 对象，后续通过 SetGlobalBuffer 设置 GM 地址和大小。模板参数 T 为数据类型。支持 950/a2/a3。；传入 GM 全局数据地址和大小，初始化 GlobalTensor。参数：buffer 为 GlobalTensor 源操作数（GM 地址），bufferSize 为元素个数。支持 950/a2/a3。。构造函数只产生空对象并明确指定后接 SetGlobalBuffer，目标接口负责绑定 GM 地址和元素数，二者组成 GlobalTensor 从空对象到可访问全局内存视图的初始化顺序。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [QuantBatchMatmulInplaceAdd 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/quant_batch_matmul_inplace_add_950.md)（`related`）：算子声明的固定版本源码包含对 `GlobalTensor(...)` 的直接调用（第 193 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/common/cmct/kernel/kernel_qbmm_cube.h#L193)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->
