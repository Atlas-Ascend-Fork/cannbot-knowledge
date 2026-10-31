---
type: API
title: aclrtGetSysParamOpt
description: 获取当前进程中的运行时参数值。若未设置则返回各参数默认值 0，支持检测选项未设置错误。
tags:
- task.lookup
- topic.implementation.resource_query
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
# aclrtGetSysParamOpt

## 功能说明

获取当前进程中的运行时参数值。若未调用 `aclrtSetSysParamOpt` 设置，返回各参数默认值 0。

内部行为（固定 commit `b523035a` 源码结论，不构成跨版本承诺）：
- `aclrtGetSysParamOptImpl` 调用 `GetSysParamOpt(opt, value, false)`。
- 有效 opt 同 Set 接口（0/1/2/3）；非法 opt 返回 `ACL_ERROR_INVALID_PARAM`。
- `value` 非空校验不通过返回错误。
- 底层通过 `rtGetSysParamOpt` 读取。若选项未设置，RTS 返回 `ACL_ERROR_RT_SYSPARAMOPT_NOT_SET`，本接口映射后返回。

## 函数原型

```c
aclError aclrtGetSysParamOpt(aclSysParamOpt opt, int64_t *value);
```

## 参数说明

| 参数名 | 输入/输出 | 说明 |
| --- | --- | --- |
| opt | 输入 | 运行时参数，参见 aclSysParamOpt。 |
| value | 输出 | 运行时参数值。 |

## 返回值说明

返回 0 表示成功，其他值表示失败。固定实现中可区分的失败场景：

| 内部错误 | 触发点 | 调用方处理 |
| --- | --- | --- |
| `ACL_ERROR_INVALID_PARAM` | opt 不在合法范围；value 为空指针 | 提供合法参数 |
| `ACL_ERROR_RT_SYSPARAMOPT_NOT_SET` | 对应选项未调用 Set 设置过 | 若已知未设置可忽略，或先调用 Set |

## 约束说明

- 本接口应在 [aclInit](acl_init.md) 之后调用。