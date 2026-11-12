---
type: Concept
title: SGLang 公共算子注册、架构检测与显式后端分发
description: 解释 register_operator/register_impl 的进程级架构缓存、互斥支持集、auto别名、惰性加载和无回退错误分类。
tags:
- task.implementation
- topic.programming_model
- topic.architecture
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/utils/registry.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/utils/generation.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/developer_guide/contribution_guide_zh.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: constraint
created_at: '2026-11-08T11:03:52Z'
updated_at: '2026-11-08T11:03:52Z'
platforms:
- a2
- a3
- '950'
---

# SGLang 公共算子注册、架构检测与显式后端分发

## 稳定身份与选择

`register_operator(op_name)` 将公开函数对象绑定唯一算子名；相同函数或算子名重复注册均失败，`get_op_name` 不从模块路径猜名字。`register_impl(op_name, impl)` 声明具体实现，公开函数通过 `get_impl_by_name` 显式查找。`auto` 是每个算子注册的默认实现别名，不表示基于可用性动态回退。

Python 后端通常首次调用再 import 并缓存 callable；原生后端直接调用已暴露的绑定。注册表只选择入口，不统一执行各后端的 shape/dtype 检查，也不保证外部动态库存在。接口新增后须在所属 operators 模块导出。

## 架构检测与支持集

导入 registry 即调用缓存的 `get_hardware()`。查询可见 device 0 的 ACL 属性601，异常或返回非零时尝试 torch_npu SoC 家族映射；源码支持编号2201→arch22、3510→arch35，对应构建中的A2/A3和950。未知编号和检测失败抛 `HardwareDetectionError`，不会按默认架构继续。进程所有可见卡须同架构；测试的设备选择不重新计算已缓存架构。

支持声明只能给 `supported_generations` 或 `excluded_generations` 之一，成员须为 `Generation`。两者省略仅表示全部**当前已知**枚举，不承诺未来代际；空支持集表示不支持。相同算子/impl可多次声明互不相交的支持集，重叠即拒绝；不同impl的支持集独立。注册时按进程硬件选入 `_IMPLS`，查找时不再挑代际。

## 错误与测试边界

| 情况 | 行为 |
| --- | --- |
| 实现名称从未声明 | `ImplementationNotFoundError`，含已声明名字。 |
| 名称声明过但当前架构不在支持集 | `UnsupportedGenerationError`，携带当前/支持代际。 |
| 后端动态库或依赖缺失 | 后端加载或调用失败；注册表不回退。 |
| `list_impls*` 列出某实现 | 表示已声明，不能据此证明设备可用或模块依赖已安装。 |

`auto` 和其具体后端别名可能是同一 callable，不能作为独立精度基线。计算类接口应提供独立 reference；原地/状态型接口另管输入隔离。测试框架的 probe 只验证分发模式，不证明生产Kernel精度。源码 generation 有旧CANN的torch_npu检测回退，而测试README的部分简述只提ACL失败；消费本版本以源码这条明确分支为准。本次未执行NPU探测或后端运行。
