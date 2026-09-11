---
type: API
title: LoadUnzipIndex
description: 加载GM上的压缩索引表到内部寄存器。 索引表包含LoadDataUnzip所需的压缩信息，例如压缩长度等，用于获取压缩后的数据。 索引表由压缩工具根据对应的权重数据离线生成。一个LoadUnzipIndex指令可以加载多个索引表，而每个LoadDataUnzip指令只能消耗一个索引表。因此，索引表之间的顺序应该由用户来确定，以确保其与压缩数据的对应性。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.cube
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/LoadUnzipIndex.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- 310p
source_headers:
- include/basic_api/kernel_operator_mm_intf.h
---

# LoadUnzipIndex<a name="ZH-CN_TOPIC_0000001913174992"></a>

## 功能说明<a name="section618mcpsimp"></a>

加载GM上的压缩索引表到内部寄存器。

索引表包含LoadDataUnzip所需的压缩信息，例如压缩长度等，用于获取压缩后的数据。

索引表由压缩工具根据对应的权重数据离线生成。一个LoadUnzipIndex指令可以加载多个索引表，而每个LoadDataUnzip指令只能消耗一个索引表。因此，索引表之间的顺序应该由用户来确定，以确保其与压缩数据的对应性。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T = int8_t, typename Std::enable_if<Std::is_same<PrimT<T>, int8_t>::value, bool>::type = true> 
__aicore__ inline void LoadUnzipIndex(const GlobalTensor<T>& src, uint32_t numOfIndexTabEntry)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1** 模板参数说明

| 参数名称 | 描述 |
| --- | --- |
| T | src的数据类型。<br>&nbsp;&nbsp;&nbsp;&nbsp;&bull;当src使用基础数据类型时，其数据类型必须为int8_t，否则编译失败。<br>&nbsp;&nbsp;&nbsp;&nbsp;&bull;当src使用TensorTrait类型时，src数据类型T的LiteType必须为int8_t，否则编译失败。<br>最后一个模板参数仅用于上述数据类型检查，用户无需关注。 |

**表2** 参数说明

| 参数名称 | 输入/输出 | 含义 |
| --- | --- | --- |
| src | 输入 | 源操作数，索引表地址，类型为GlobalTensor。<br>&nbsp;&nbsp;&bull; src地址必须2字节对齐。<br>&nbsp;&nbsp;&bull; src长度必须是512字节的整数倍，最大为32KB。 |
| numOfIndexTabEntry | 输入 | 输入数据，表示加载的索引表个数。<br>&nbsp;&nbsp;&bull;索引表个数必须大于0。 |

## 返回值说明<a name="section640mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

- 操作数地址对齐要求请参见[通用地址对齐约束](../../../general_description_and_constraints.md#section796754519912)。
- LoadUnzipIndex必须在任何LoadDataUnzip指令之前执行。
- LoadUnzipIndex加载的索引表个数必须大于或等于LoadDataUnzip指令执行的次数。

## 调用示例<a name="section6461234123118"></a>

该调用示例支持的运行平台为Atlas 推理系列产品AI Core。详细用例请参考[LoadDataUnzip](load_data_unzip.md)。

```cpp
indexGlobal.SetGlobalBuffer((__gm__ int8_t*)indexGm);
AscendC::LoadUnzipIndex(indexGlobal, numOfIndexTabEntry);
```


<!-- cannbot:related:start -->
## 相关

- [LoadDataUnzip](load_data_unzip.md)（`related`）：将 GM 上的压缩数据解压并搬运到 L1 Buffer（A1/B1）或 L0B Buffer（B2）。执行前须先调用 LoadUnzipIndex 加载压缩索引表到内部寄存器。；加载 GM 上的压缩索引表到内部寄存器，供 LoadDataUnzip 使用。索引表由压缩工具根据权重数据离线生成，包含压缩长度等信息。一个 LoadUnzipIndex 可加载多个索引表，每个 LoadDataUnzip 只消耗一个，索引表顺序须与压缩数据对应。。LoadDataUnzip 明确以前置 LoadUnzipIndex 为执行条件，目标接口负责加载并排序其消费的压缩索引表，二者组成索引准备后解压搬运到 L1/L0B 的有序调用链。
<!-- cannbot:related:end -->
