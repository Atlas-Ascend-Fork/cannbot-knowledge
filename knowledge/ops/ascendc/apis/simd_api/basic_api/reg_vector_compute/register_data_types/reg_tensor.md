---
type: API
title: RegTensor
description: RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.programming_model.execution_unit.vector
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/register_data_types/RegTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/basic_api/reg_compute/kernel_reg_compute_struct_intf.h
---

# RegTensor<a name="ZH-CN_TOPIC_0000001928794188"></a>

## 功能说明<a name="section618mcpsimp"></a>

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

## 定义原型<a name="section620mcpsimp"></a>

```cpp
template <typename T, const RegTrait& regTrait = RegTraitNumOne> struct RegTensor;
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
| :-- | :------------ |
| T | 操作数数据类型，支持的数据类型(宽度)为b8、b16、b32、b64。<br>&bull; b8：bool、int8_t、uint8_t、fp4x2_e2m1_t、fp4x2_e1m2_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、fp8_e8m0_t（fp4x2_e2m1_t、fp4x2_e1m2_t这两个b4类型在Vector侧的内存排布需要为两个一组，表现为b8类型；int4b_t也使用b8类型表达；bool数据类型只支持数据搬运）。<br>&bull; b16：int16_t、uint16_t、half、bfloat16_t。<br>&bull; b32：int32_t、uint32_t、float、complex32。<br>&bull; b64：int64_t、uint64_t、complex64。| 
| regTrait | 类型为RegTrait，支持配置为RegTraitNumOne或RegTraitNumTwo。<br>&bull; RegTraitNumOne：该RegTensor类型中包含1个相应数据类型的矢量Reg，长度为VL。支持的数据类型为：b8、b16、b32、b64。<br>&bull; RegTraitNumTwo：该RegTensor类型中包含2个相应数据类型的矢量Reg，每个矢量Reg长度为VL，总长度为2*VL。支持的数据类型为：complex32、b64。|

## 约束说明<a name="section177921451558"></a>

-   RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。
-   寄存器的生命周期限定于单个VF内部。

## 关键特性

-   complex32类型RegTensor存储结构

    下图为complex32在RegTraitNumOne和RegTraitNumTwo场景下RegTensor存储情况：

    **图1** RegTensor搬运complex32<a id="fig1"></a>

    ![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/regtensor_move_complex32.png "RegTensor搬运complex32")

    complex32是一个包含两个half（实部real、虚部imag）类型的复合类型，通常是连续存储，低位为实部高位为虚部。
    
    在RegTraitNumOne场景下，从Unified Buffer（UB，src0Addr）中以DIST_NORM模式搬运VL数据量，在RegTensor中连续存储。
    
    在RegTraitNumTwo场景下，从UB（src0Addr）中以DIST_DINTLV_B16双搬入模式读取2*VL数据量，将complex32数据交错搬运，偶数索引（实部）的元素存入reg[0]，将奇数索引（虚部）的元素存入reg[1]，数据类型为uint16_t。两个RegTensor存储512B的数据量，reg[0]存的是128个complex32的前16位（实部），reg[1]存的是128个complex32的后16位（虚部）。

-   complex64类型RegTensor存储结构

    下图为complex64在RegTraitNumOne和RegTraitNumTwo场景下RegTensor存储情况：

    **图2** RegTensor搬运complex64<a id="fig2"></a>

    ![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/regtensor_move_complex64.png "RegTensor搬运complex64")

    complex64是一个包含两个float（实部real、虚部imag）类型的复合类型，通常是连续存储，低位为实部高位为虚部。
    
    在RegTraitNumOne场景下，从UB（src0Addr）中以DIST_NORM模式搬运VL数据量，在RegTensor中连续存储。
    
    在RegTraitNumTwo场景下，从UB（src0Addr）中以DIST_DINTLV_B32双搬入模式读取2*VL数据量，将complex64数据交错搬运，偶数索引（实部）的元素存入reg[0]，将奇数索引（虚部）的元素存入reg[1]，数据类型为uint32_t。两个RegTensor存储512B的数据量，reg[0]存的是64个complex64的前32位（实部），reg[1]存的是64个complex64的后32位（虚部）。

-   b64类型RegTensor存储结构

    下图为b64（uint64_t、int64_t）在RegTraitNumOne和RegTraitNumTwo场景下RegTensor存储情况：

    **图3** RegTensor搬运b64<a id="fig3"></a>

    ![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/regtensor_move_b64.png "RegTensor搬运b64")

    在RegTraitNumOne场景下，从UB（src0Addr）中以DIST_NORM模式搬运VL数据量。
    
    在RegTraitNumTwo场景下，从UB（src0Addr）中以DIST_DINTLV_B32双搬入模式读取2*VL数据量，将b64数据交错搬运，偶数索引（低位）的元素存入reg[0]，将奇数索引（高位）的元素存入reg[1]，数据类型为b32。两个RegTensor存储512B的数据量，reg[0]存的是64个b64的前32位（低位），reg[1]存的是64个b64的后32位（高位）。

## 调用示例<a name="section1398164912391"></a>

-   示例一

    ```cpp
    AscendC::Reg::RegTensor<uint32_t> reg;
    AscendC::Reg::MaskReg mask = AscendC::Reg::CreateMask<uint32_t>();
    AscendC::Reg::LoadAlign(reg, src, 0);
    AscendC::Reg::Adds(reg, reg, 1);
    AscendC::Reg::StoreAlign(dst, reg, 0, mask);
    ```

-   示例二

    ```cpp
    // 针对B64,可以传入RegTraitNumTwo
    template<typename T, const AscendC::Reg::RegTrait& Trait = AscendC::Reg::RegTraitNumOne>
    __simd_vf__ inline void AddVF(__ubuf__ T* dstAddr, __ubuf__ T* src0Addr, __ubuf__ T* src1Addr, uint32_t count, uint16_t oneRepeatSize, uint16_t repeatTimes)
    {
        AscendC::Reg::RegTensor<T,Trait> srcReg0;
        AscendC::Reg::RegTensor<T,Trait> srcReg1;
        AscendC::Reg::RegTensor<T,Trait> dstReg;
        AscendC::Reg::MaskReg mask;
        for (uint16_t i = 0; i < repeatTimes; i++) {
            mask = AscendC::Reg::UpdateMask<T,Trait>(count);
            AscendC::Reg::LoadAlign(srcReg0, src0Addr + i * oneRepeatSize);
            AscendC::Reg::LoadAlign(srcReg1, src1Addr + i * oneRepeatSize);
            AscendC::Reg::Add(dstReg, srcReg0, srcReg1, mask);
            AscendC::Reg::StoreAlign(dstAddr + i * oneRepeatSize, dstReg, mask);
        }
    }
    ```


<!-- cannbot:related:start -->
## 相关

- [Ascend950 Reg 扫描按 256B 锁定 lane](../../../../../runbooks/precision/dav3510_vector_register_width_is_256_bytes.md)（`exemplifies`）：RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。；工具链头文件与算子源码探针都显示 dav-3510 的 `VECTOR_REG_WIDTH` 是 256B，不是 512B。int32 寄存器实际只有 `256 / 4 = 64` 个 lane。。API 的 256B 合同由 dav-3510 高半 lane 重放故障及头文件探针具体验证。
- [RegTensor 累加须用 Add 而非 Adds](../../../../../runbooks/compilation/regtensor_add_uses_add_not_adds.md)（`exemplifies`）：RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。；`Adds` 是向量加标量接口，其第三个数据参数是 `scalarValue`。把 `RegTensor<float>` 传入后，模板会尝试把整个寄存器类型当成标量，随后触发 SupportType、可转换性和底层 `vadds` 重载检查。。API 卡定义 RegTensor 是寄存器操作数，runbook 用编译失败证明不能把它当 Adds 的标量参数。
<!-- cannbot:related:end -->
