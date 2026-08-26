---
type: Optimization
title: 写 AscendC MicroAPI 向量核的静默正确性陷阱：多行 UB 地址步长·寄存器作用域
description: 写 AscendC MicroAPI 向量核的静默正确性陷阱：多行 UB 地址步长·寄存器作用域。你在写 AscendC MicroAPI 向量核（__VEC_SCOPE__ register-level 向量编程，参考实现为 kv_compress_epilog / indexer_compress_epilog 这类逐行处理压缩 KV 的融合算子）。以下两类写法会在特定 shape/迭代下静默写错结果或成为需修的缺陷，编译期不一定报错。
tags:
- task.debugging
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/426
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/478
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 写 AscendC MicroAPI 向量核的静默正确性陷阱：多行 UB 地址步长·寄存器作用域

## 适用场景

你在写 [AscendC](../../../concepts/frameworks/ascendc.md) MicroAPI 向量核（`__VEC_SCOPE__` register-level 向量编程，参考实现为 `kv_compress_epilog` / `indexer_compress_epilog` 这类逐行处理压缩 KV 的融合算子）。以下两类写法会在特定 shape/迭代下**静默**写错结果或成为需修的缺陷，编译期不一定报错。

## 陷阱 1：多行 UB 逐行处理用「累加游标」算行内地址，而非按对齐行步长现算

在 UB 里按行落多段数据（每行 = 量化主体 `quantColNum` + 64 维 RoPE-concat 段 + zero-pad）时，行内各段 local 地址若用「跨迭代按逻辑列数累加的游标指针」算，是错误做法。

为何：UB 里行与行的真实间距是**对齐后的行步长**（`RoundUp` 出的 `curColNumAlign` / `dstCurColNumAlign`，含每行对齐 padding），而按逻辑列数（`quantColNum` / `concatColNum` 等）累加的游标不等于该对齐步长。只要 `colNum` 不是对齐粒度整数倍（`curColNumAlign > curColNum`），从第 2 行（`i>=1`）起游标累积恒定偏差，RoPE 段与 pad 段写到错行位置；`i==0` 或恰好对齐时才碰巧正确——故是**静默、shape 相关**的漂移。同一函数里 load 用未对齐 `i*curColNum`、store 已用对齐 `i*dstCurColNumAlign` 的口径不一致同样致错。

正确写法：行内每段地址一律从**行基址按对齐行步长现算**，去掉所有跨迭代累加游标，且同一 buffer 的 load 与 store 行步长口径一致（都用对齐后步长）：

```cpp
LoadInputData<T0>(xLeft,  xLocalAddr, pregMain, 2*j*VL_FP32 + i * curColNumAlign);      // 主体 load 改对齐步长
__local_mem__ T0* rowRopeXLocalAddr = xLocalAddr + i * curColNumAlign  + quantColNum;   // RoPE 段现算
__local_mem__ T1* rowPadLocalAddr   = yLocalAddr + i * dstCurColNumAlign + concatColNum; // pad 段现算
```

## 陷阱 2：把 __VEC_SCOPE__ 内使用的 MaskReg / RegTensor 声明在作用域外

写 MicroAPI 向量核时，在 `__VEC_SCOPE__` 内被使用的谓词/掩码寄存器 `MaskReg`（含 `CreateMask`/`UpdateMask` 产出、被算子当谓词消费的）以及 `RegTensor` 等寄存器型变量，必须声明在 `__VEC_SCOPE__` 块**内部**。把实际被 `UpdateMask` 迭代、作为 `LoadInputData`/`Muls`/`Cast`/`DataCopy` 谓词的 `MaskReg` 声明在块外部，是需要修的缺陷（`__VEC_SCOPE__` 是向量寄存器的作用域边界）。

正确写法：使用中的寄存器声明移入块内：

```cpp
__VEC_SCOPE__ {
    RegTensor<float> xReg;
    RegTensor<hifloat8_t> tmp;
    MaskReg pregLoop = CreateMask<float>();      // 声明在 __VEC_SCOPE__ 内部
    for (uint16_t i = 0; i < curRowNum; i++) {
        uint32_t sreg = curColNum;
        for (uint16_t j = 0; j < loopCount; j++) {
            pregLoop = UpdateMask<float>(sreg);
            LoadInputData<T1>(xReg, xLocalAddr, pregLoop, j * VL_FP32 + i * curColNumAlign);
            ...
        }
    }
}
```

（把 `MaskReg` 放作用域外具体触发编译错 / UB / 结果错，源未披露；但「使用中的寄存器须声明在 `__VEC_SCOPE__` 内」是维护者落定的写法。）

## 适用边界

限 AscendC MicroAPI `__VEC_SCOPE__` 向量核编写。陷阱 1 针对「UB 多行 + 每行含 quant/rope/pad 段、行步长按 `RoundUp` 对齐」的内核（参考实现产 [MXFP8](../../../concepts/quantization/mxfp8_a8w8.md) / C8 + scale 输出）；陷阱 2 针对任何在 `__VEC_SCOPE__` 内消费寄存器的向量核。不外推为昇腾栈其它 API。

## 相关

- 同属 AscendC 底层写法的静默失效（host 侧入参校验）：[ascendc-op-input-validation-pitfalls](ascendc_op_input_validation_pitfalls.md)。
- 另见 [为 MoE+MLA+MTP 模型做混合精度量化的配置陷阱：保留不量化层·激活分支按位宽子串门控](../rules/deepseekv3_mixed_precision_quant_config_pitfalls.md)。
- 另见 [昇腾性能测量失真陷阱：不代表真实访存的测量输入·折算前被截断的度量口径](perf_measurement_distortion_input_and_metric.md)。

## Evidence

- diff 事实（clone `@a97074cdd551`，`ops/ascendc/src/kv_compress_epilog/op_kernel/kv_compress_epilog_common.h`，`VFProcessDynamicBlockQuant` / `VFProcessDynamicMxFP8Quant`）：旧用累加游标 + 未对齐 load 步长 → 新用 `base + i*RoundUp(colNum)` 现算；`curColNumAlign = RoundUp<T0>(curColNum)`、`dstCurColNumAlign = RoundUp<T1>(concatColNum+padColNum)`、`quantColNum = curColNum - 64`。漂移触发条件 `curColNumAlign > curColNum` 为变量定义推得（推断，未见披露具体 shape 或错误现象）。
  - 溯源下探：[cann-recipes-infer-pr-426-improve-kv-compress-epilog-row-local-address-calculation](https://gitcode.com/cann/cann-recipes-infer/merge_requests/426)
- diff 事实 + 维护者批准（clone `@b044c62`，`indexer_compress_epilog_base.h` / `kv_compress_epilog_common.h` 的 `VFProcessHifp8Quant`，两文件改动逐字节相同）：被 `UpdateMask` 迭代/作谓词的 `MaskReg pregLoop` 由 `__VEC_SCOPE__` 外移入内部。触发何种失败源未披露（推断，不并入事实面）。
  - 溯源下探：[cann-recipes-infer-pr-478-fix-fix-pregmask-define-in-vec-scope](https://gitcode.com/cann/cann-recipes-infer/merge_requests/478)
