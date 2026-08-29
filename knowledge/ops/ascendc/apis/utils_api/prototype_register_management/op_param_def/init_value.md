---
type: API
title: InitValue（OpParamDef）
description: 通过该host侧接口设置算子输出的初始值，设置后会在算子执行前对算子输出的GM空间进行清零操作或者插入memset类算子进行初始值设置。
  InitValue和SetNeedAtomic接口配合使用，SetNeedAtomic接口需要配置为true。
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpParamDef/InitValue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# InitValue

## 功能说明
通过该host侧接口设置算子输出的初始值，设置后会在算子执行前对算子输出的GM空间进行清零操作或者插入memset类算子进行初始值设置。
InitValue和SetNeedAtomic接口配合使用，SetNeedAtomic接口需要配置为true。
## 函数原型
-   在算子执行前，对输出参数对应GM空间进行清零。
-   指定输出参数初值的类型和值，输出参数调用该接口，会在算子执行前，对输出参数对应GM空间插入对应类型和值的memset类算子。
-   指定输出参数初值类型和值的列表，依次对应输出参数的数据类型和数据格式组合，会在算子执行前，对输出参数对应GM空间插入对应类型和值的memset类算子。
## 参数说明
## 返回值说明
OpParamDef算子定义，OpParamDef请参考OpParamDef。
## 约束说明
-   InitValue和SetNeedAtomic接口配合使用，否则会出现初始化不生效的情况。
-   针对OpParamDef &InitValue(uint64_t value)接口，算子输出参数的数据类型支持范围如下：UINT64/INT64/UINT32/INT32/UINT16/INT16/UINT8/INT8/FLOAT32/FLOAT16，超出该范围为未定义行为。
-   针对OpParamDef &InitValue(const std::vector &value)接口输入value的size需要与输出参数配置的DataType或DataTypeList接口参数的size一致。同时，相同数据类型需保证设置的类型和值相同，否则将会报错。
-   对于同一个输出参数仅支持调用一种接口设置初值，调用多种InitValue接口为未定义行为；多次调用同一种接口以最后一次调用设置的初值为准。
-   基于旧版本CANN包（不支持InitValue特性）生成的自定义算子工程，无法兼容InitValue接口。在使用非当前版本CANN包生成的自定义算子工程时，需特别注意兼容性问题。您可以通过查看自定义算子工程下cmake/util/ascendc_impl_build.py中有无output_init_value字段来确认当前工程是否支持该特性，如果未找到该字段，则需要重新生成自定义算子工程以启用InitValue特性。

<!-- cannbot:related:start -->
## 相关

- [LinalgCholesky A2/A3 ACLNN 算子知识](../../../../operators/aclnn/math/math/linalg_cholesky.md)（`related`）：Cholesky 卡说明“Kernel 只写被选三角；`Cholesky` OpDef 为临时输出声明 `.InitValue(0)`”；InitValue 页说明“设置后会在算子执行前对算子输出的GM空间进行清零操作或者插入memset类算子进行初始值设置。”，该 Host 初始化为未写的相反三角提供零值。
<!-- cannbot:related:end -->
