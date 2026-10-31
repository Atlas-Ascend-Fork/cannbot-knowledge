---
type: API
title: aclrtSetSysParamOpt
description: 设置当前进程中的运行时参数值。作用域为进程级别，不支持 IPV350。与 aclrtCtxSetSysParamOpt（Context 级）独立。
tags:
- task.lookup
- topic.implementation
- topic.implementation.api_layer.c_api
status: draft
sources:
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/docs/zh/api_ref/03_runtime_configuration.md
  role: primary
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/include/external/acl/acl_rt.h
  role: header
- resource: cann-runtime-raw/runtime/b523035a08ef573b6bc476c8ab2a34733ba069a4/src/acl/aclrt_impl/context.cpp
  role: implementation
source_headers:
- include/external/acl/acl_rt.h
created_at: '2026-09-15T00:00:00Z'
updated_at: '2026-10-29T08:46:01Z'
platforms:
- '950'
- 'a3'
- 'a2'
- '310b'
- '310p'
- '910'
---
# aclrtSetSysParamOpt

## 功能说明

设置当前进程中的运行时参数值。作用域为进程级别，与 `aclrtCtxSetSysParamOpt`（Context 级）独立。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtSetSysParamOptImpl`（context.cpp:166）调用 `SetSysParamOpt(opt, value, false)`。
- 有效 opt 值：`ACL_OPT_DETERMINISTIC(0)`、`ACL_OPT_ENABLE_DEBUG_KERNEL(1)`、`ACL_OPT_STRONG_CONSISTENCY(2)`、`ACL_OPT_ENABLE_KERNEL_EARLY_START(3)`。
- 非法 opt 返回 `ACL_ERROR_INVALID_PARAM`。
- 底层通过 `rtSetSysParamOpt` 写入运行时参数。

## 函数原型

```c
aclError aclrtSetSysParamOpt(aclSysParamOpt opt, int64_t value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| opt | 输入 | 运行时参数，参见 aclSysParamOpt。合法值：0（确定性计算）、1（调试 Kernel）、2（强一致性）、3（Kernel 提前启动）。 |
| value | 输入 | 运行时参数值。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | opt 不在合法范围 | 使用合法的 opt 枚举值 |

## 约束说明

- 本接口应在 [aclInit](acl_init.md) 之后调用。
- 设置后可通过 [aclrtGetSysParamOpt](aclrt_get_sys_param_opt.md) 查询生效值。