---
type: API
title: AI CPU API列表
description: 汇总 AI CPU Kernel 调试和内存操作相关的 printf、assert 与 data_store_barrier 接口。
tags: [task.lookup, topic.implementation.api_layer.aicpu_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/ai_cpu_api_list.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# AI CPU API列表

**表1** AI CPU API列表

<table><thead align="left"><tr id="row1440344222113"><th class="cellrowborder" valign="top" width="37.419999999999995%" id="mcps1.2.3.1.1"><p id="p140384218217">接口名</p>
</th>
<th class="cellrowborder" valign="top" width="62.580000000000005%" id="mcps1.2.3.1.2"><p id="p1140384218214">功能描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row19403174252116"><td class="cellrowborder" valign="top" width="37.419999999999995%" headers="mcps1.2.3.1.1 "><p id="p2040314420218">printf</p>
</td>
<td class="cellrowborder" valign="top" width="62.580000000000005%" headers="mcps1.2.3.1.2 "><p id="p340494292115"><span id="ph15404164211219">该接口提供AI CPU算子Kernel调试场景下的格式化输出功能，默认将输出内容解析并打印在屏幕上。</span></p>
</td>
</tr>
<tr id="row10404124212210"><td class="cellrowborder" valign="top" width="37.419999999999995%" headers="mcps1.2.3.1.1 "><p id="p129831814226">assert</p>
</td>
<td class="cellrowborder" valign="top" width="62.580000000000005%" headers="mcps1.2.3.1.2 "><p id="p1404204252114"><span id="ph040464220211">该接口实现AI CPU算子Kernel调试场景下的assert断言功能。</span></p>
</td>
</tr>
<tr id="row1568314516298"><td class="cellrowborder" valign="top" width="37.419999999999995%" headers="mcps1.2.3.1.1 "><p id="p86839512291">DataStoreBarrier</p>
</td>
<td class="cellrowborder" valign="top" width="62.580000000000005%" headers="mcps1.2.3.1.2 "><p id="p7683145172918"><span id="ph56837516296">该接口用于AI CPU与AI Core多核之间的数据一致性同步。</span></p>
</td>
</tr>
</tbody>
</table>
