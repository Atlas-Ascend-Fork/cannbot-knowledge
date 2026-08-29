---
type: API
title: RegTensor
description: RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/RegTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# RegTensor

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

参数：T: 操作数数据类型，支持的数据类型(宽度)为b8、b16、b32、b64。 • b8：bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、fp8_e8m0_t（fp4x2_e2m1_t、fp4x2_e1m2_t这两个b4类型在Vector侧的内存排布需要为两个一组，表现为b8类型；int4b_t也使用b8类型表达；bool数据类型只支持数据搬运）。 • b16：int16_t、uint16_t、half、bfloat16_t。 • b32：int32_t、uint32_t、float、complex32。 • b64：int64_t、uint64_t、complex64。；regTrait: 类型为RegTrait，支持配置为RegTraitNumOne或RegTraitNumTwo。 • RegTraitNumOne：该RegTensor类型中包含1个相应数据类型的矢量Reg，长度为VL。支持的数据类型为：b8、b16、b32、b64。 • RegTraitNumTwo：该RegTensor类型中包含2个相应数据类型的矢量Reg，每个矢量Reg长度为VL，总长度为2*VL。支持的数据类型为：complex32、b64。

约束：-   RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。
-   寄存器的生命周期限定于单个VF内部。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。；工具链头文件与算子源码探针都显示 dav-3510 的 `VECTOR_REG_WIDTH` 是 256B，不是 512B。int32 寄存器实际只有 `256 / 4 = 64` 个 lane。。API 的 256B 合同由 dav-3510 高半 lane 重放故障及头文件探针具体验证。
- [RegTensor 累加须用 Add 而非 Adds](../../../../../runbooks/compilation/regtensor_add_uses_add_not_adds.md)（`exemplifies`）：RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。；`Adds` 是向量加标量接口，其第三个数据参数是 `scalarValue`。把 `RegTensor<float>` 传入后，模板会尝试把整个寄存器类型当成标量，随后触发 SupportType、可转换性和底层 `vadds` 重载检查。。API 卡定义 RegTensor 是寄存器操作数，runbook 用编译失败证明不能把它当 Adds 的标量参数。
<!-- cannbot:related:end -->
