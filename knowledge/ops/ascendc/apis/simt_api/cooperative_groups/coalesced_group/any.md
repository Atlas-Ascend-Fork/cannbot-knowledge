---
type: API
title: CoalescedGroup协作组any
description: 判断coalesced_group组内是否有线程的输入不为0。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/coalesced_group/any.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# any

## 功能说明

判断`coalesced_group`组内是否有线程的输入不为0。

## 函数原型

```cpp
int any(int predicate) const
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| predicate | 输入 | 操作数。 |

## 返回值说明

当`coalesced_group`组内所有线程的输入均为0，返回0，否则返回1。

## 约束说明

无

## 调用示例

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        if (threadIdx.x % 2 == 0) {
            coalesced_group active = coalesced_threads();
            int result = active.any(1); // 返回1
        }
        ...
    }
    ```

- SIMD与SIMT混合编程场景：

    ```cpp
    using namespace cooperative_groups;
    __simt_vf__ inline void simt_kernel(...)
    {
        ...
        if (threadIdx.x % 2 == 0) {
            coalesced_group active = coalesced_threads();
            int result = active.any(1); // 返回1
        }
        ...
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [Ballot](ballot.md)（`related`）：“返回值：当coalesced_group组内所有线程的输入均为0，返回0，否则返回1。”与“返回值：32-bit的无符号整数：若coalesced_group组内线程输入的predicate不为0，则返回值中与线程rank对应的bit位为1，否则为0。”是双方正文中的具体合同。两端观察同一 coalesced_group 内各线程 predicate；Any 折叠为组级布尔值，Ballot 保留逐 rank 位图，互读可按后续分支需求选择结果粒度。
<!-- cannbot:related:end -->
