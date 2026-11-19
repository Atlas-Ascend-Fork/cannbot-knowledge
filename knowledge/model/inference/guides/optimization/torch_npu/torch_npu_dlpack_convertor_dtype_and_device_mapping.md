---
type: Guide
title: TorchNPU DLPack 转换器：dtype/设备映射契约与子字节不对称边界
description: 固定主线源级核对 DLConvertor 的 toDLPack/fromDLPack：dtype 编码映射与 float8/BComplex32/量化拒绝面、UInt1-7
  整字节化、stride 归一化、kDLExtDev 设备映射及 from_blob 下游衔接。
tags:
- task.implementation
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/DLConvertor.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/DLConvertor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/DLConvertor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/DLConvertor.h
  role: implementation
created_at: '2026-11-13T05:22:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU DLPack 转换器：dtype/设备映射契约与子字节不对称边界

## 固定版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，整读 `torch_npu/csrc/aten/common/DLConvertor.cpp`（318 行）与 `.h`。静态阅读，未执行 DLPack 互操作或设备实验。本卡只覆盖 C++ 转换器语义；Python 侧 `torch_npu.utils.dlpack` 包装与 `from_blob` NPU 存储构造面另行成卡，不在此合并声明。

## 导出方向：getDLDataType

`dtype.bits = element_size() * 8`、`lanes = 1`。编码映射：UInt1–UInt7 与 Byte/UInt16/32/64 全部落 `kDLUInt`；Int1–Int7 与 Char/Short/Int/Long 落 `kDLInt`；Half/Float/Double 落 `kDLFloat`；BFloat16 落 `kDLBfloat`；Bool 落 `kDLBool`；ComplexHalf/Float/Double 落 `kDLComplex`。关键点：**导出位宽按 `element_size() * 8` 计算，具体元素大小由配套 PyTorch 提供**。本实现没有另行携带 UInt1–UInt7 的枚举身份；若某子字节类型在目标环境以 1 字节元素导出，则得到 `kDLUInt/bits=8`，与 Byte 编码相同。子字节类型的可构造性、元素大小及往返结果应按配套版本核对。版本门控的显式拒绝面（`TORCH_CHECK(false, ..., PTA_ERROR(ErrCode::TYPE))`）：BComplex32（≥2.14 起，DLPack 无 complex-of-BFloat16 编码）、Float8_e5m2/e5m2fnuz/e4m3fn/e4m3fnuz/e8m0fnu（≥2.16 追加 e5m3fnu）、全部 QInt/QUInt 量化类型、Bits1x8/Bits2x4/Bits4x2/Bits8/Bits16 位打包类型、Undefined/NumOptions。这些类型不能经 DLPack 出口，报错是类型错误而非静默降级。

## 设备映射

导出：CPU → `kDLCPU`；PrivateUse1（NPU）→ `kDLExtDev`；其他设备类型直接 `TORCH_CHECK` NOT_SUPPORT。导入：`kDLCPU` → CPU 设备；`kDLExtDev` → `PrivateUse1(device_id)`；其余 `device_type` 拒绝。DLPack 面只认这两种设备编码。

## 导入方向：toScalarType

要求 `lanes == 1`（否则 NOT_SUPPORT）。仅接受整字节宽度：kDLUInt 8/16/32/64 → Byte/UInt16/UInt32/UInt64；kDLInt 8/16/32/64 → Char/Short/Int/Long；kDLFloat 16/32/64 → Half/Float/Double；kDLBfloat 仅 16 → BFloat16；kDLComplex 32/64/128 → ComplexHalf/ComplexFloat/ComplexDouble；kDLBool 仅 8 → Bool；其他 bits/code 一律 NOT_SUPPORT 拒绝。**导入没有 UInt1–UInt7 的专用枚举映射**。若以 `kDLUInt/bits=8` 导出，回读映射为 Byte；若导入位宽不在此 switch 支持的集合内，则走拒绝路径。该实现不保证子字节 dtype 身份往返一致。

## toDLPack：stride 归一化与生命周期

构造时对 `shape[i] < 2` 的维度把 stride 归一为 1（对齐上游 gh-83069），再以 `as_strided` 建视图；`ATenDLMTensor` 持有该视图句柄，`manager_ctx` 指回自身、`deleter` 删除宿主对象，因此 shape/strides 指针的有效性与 Tensor 生命周期绑定在 manager 上。`device_id` 仅在 `is_cuda() || is_privateuseone()` 时取真实编号，其余为 0；`byte_offset` 固定 0。把 manager 当作引用而非值拷贝：DLManagedTensor 被消费方 `deleter` 后宿主 Tensor 即释放。

## fromDLPack：strides 分支与 from_blob 下游

`strides == nullptr` 走仅 sizes 的 `at_npu::native::from_blob`；有 strides 走带 strides 重载，deleter 包装 `src->deleter` 并透传 device/dtype 选项与 `{device}` 设备表。即 DLPack 导入的设备侧存储构造、所有权与格式初始化全部委托本仓 from_blob 实现；from_blob 面的设备一致性检查与 InefficientStdFunctionContext 行为在 from_blob 专卡核对，本卡不重复推导。

## 验证与失效边界

定向验证：UInt4/Int2 等子字节类型导出后的 bits/code、Float8 与量化类型确实抛类型错误、`lanes != 1` 的外部 DLPack 张量被拒、`kDLExtDev` 跨包导入落在指定 NPU 设备、shape<2 维度 stride 归一不改变语义。本卡未执行上述实验；`TORCH_NPU_VERSION_GE` 门控表明 BComplex32/Float8_e5m3fnu 的拒绝面随版本推进变化，升级后须按新 ScalarType 重对映射表。本卡不声明 Python `to_dlpack/from_dlpack` 包装行为与任何平台的互操作支持。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/DLConvertor.cpp)（primary），读取范围 1–318 全文。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/DLConvertor.h)（implementation），读取范围 1–25 全文。

## 发布 pin 对照（f3ecfe4a）

本节结论来自发布 pin 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 等价绑定（结论对发布 pin 直接适用）

- `torch_npu/csrc/aten/common/DLConvertor.h`：注释差异等价（代码 token 流相同）。

### 版本边界（发布 pin 行为不同）

- `torch_npu/csrc/aten/common/DLConvertor.cpp`（318 → 309 行）：dtype 拒绝面构成两版差异。主线以 `TORCH_NPU_VERSION_GE(2,14)` 门控 BComplex32 显式拒绝（"BComplex32 (complex<BFloat16>) is not supported by dlpack"）、以 `(2,16)` 门控追加 Float8_e5m3fnu case；发布版**无版本宏、无 BComplex32 case 且该 switch 无 default 分支**；该差异只说明旧源码缺少相应专用分支，类型能否由配套 PyTorch 提供及进入该函数须另行核对。float8 家族（e5m2/e5m2fnuz/e4m3fn/e4m3fnuz/e8m0fnu）仍直接 `TORCH_CHECK` 拒绝。「版本门控的显式拒绝面」一节的 BComplex32 结论**限定主线**；发布版拒绝面按其固定文件核对，BComplex32 的类型可用性与调用结果需结合配套 PyTorch 核验，不由该分支缺席单独推定。

### Evidence（发布 pin 补绑）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/DLConvertor.cpp)（release-twin-binding）：diff 级全文对照（版本宏与 BComplex32 拒绝差异）。
- [发布孪生 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/DLConvertor.h)（release-twin-binding）：注释差异等价。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
