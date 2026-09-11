---
type: API
title: IsValid
description: 判断当前grid_group是否可使用sync()接口进行跨线程块同步。grid_group默认支持同步功能，因此接口固定返回true。
tags:
- task.lookup
- topic.implementation.api_layer.simt_api
- topic.programming_model.cooperative_groups
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/cooperative_groups/grid_group/is_valid.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# is_valid

## 功能说明

判断当前`grid_group`是否可使用`sync()`接口进行跨线程块同步。`grid_group`默认支持同步功能，因此接口固定返回`true`。

## 函数原型

```cpp
bool is_valid() const
```

## 参数说明

无

## 返回值说明

固定返回`true`

## 约束说明

仅支持SIMT编程场景，不支持SIMD与SIMT混合编程场景。

## 调用示例

- SIMT编程场景：

    ```cpp
    using namespace cooperative_groups;
    __global__ void simt_kernel(...)
    {
        ...
        grid_group g = this_grid();
        if (g.is_valid()) {
            g.sync();
        }
        ...
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [Grid协作组sync](sync.md)（`related`）：判断当前grid_group是否可使用sync()接口进行跨线程块同步。grid_group默认支持同步功能，因此接口固定返回true。；同步当前Grid内所有SIMT线程。所有线程块中的所有线程都执行到该同步点位置后，Grid内线程才能继续执行。。IsValid 查询的能力对象就是 grid_group 的 sync 跨线程块同步，sync 卡进一步给出所有线程到达同步点的执行语义与约束，因此查询与被查询操作属于同一调用决策链。
<!-- cannbot:related:end -->
