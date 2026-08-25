---
type: Guide
title: 非对齐场景
description: 本节介绍非32字节对齐数据的更多处理方式，包括数据搬入、计算和搬出的处理。用户在实际算子开发中，可以参考如下方案介绍和算子样例灵活地处理非对齐场景。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/unaligned_scenario.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 非对齐场景

本节介绍非32字节对齐数据的更多处理方式，包括数据搬入、计算和搬出的处理。用户在实际算子开发中，可以参考如下方案介绍和算子样例灵活地处理非对齐场景。
## 数据搬运和Vector计算的对齐要求
下文描述中的Global指Global Memory上的tensor，Local指Local Memory上的tensor。
下面是一些非对齐搬运和计算的例子。
-   非对齐搬入
当需要从Global拷贝11个half数值到Local时，为保证搬运的数据长度32字节对齐，使用DataCopy拷贝16个half（32B）数据到Local上，Local[11]\~Local[15]被写成无效数据-1。
-   非对齐搬出
当需要从Local拷贝11个half数值到Global时，为保证搬运的数据长度32字节对齐，使用DataCopy拷贝16个half（32B）数据到Global上，Global[11]\~Global[15]被写成无效数据-1。
-   矢量计算起始地址非32字节对齐的错误示例
矢量计算时需要保证起始地址32字节对齐，如下的示例中，从Local1[7]，即LocalTensor的第8个数开始计算，起始地址不满足32字节对齐，是错误示例。
## 非对齐处理方案
DataCopyPad接口提供非对齐搬运的功能，如果基于该接口支持的产品开发算子（参见产品支持情况），则可以直接使用该接口解决非对齐场景下的搬运问题。使用DataCopyPad的完整示例请参考DataCopyPad样例。
部分型号不支持DataCopyPad接口，可以参考如下的搬运方案处理。
首先，使用DataCopy对齐数据搬运接口进行数据搬运，由于搬入时搬运的数据长度必须保证32字节对齐，数据长度非对齐的情况下，从Global逐行搬运Tensor数据到Local中，Local中每行都存在冗余随机数据。
搬入后，进行矢量计算时对冗余数据的处理方式有以下几种：
-   冗余数据参与计算。一般用于elewise计算场景，冗余数据即使参与计算，也不影响最终结果，如下图所示：
-   通过mask参数掩掉冗余数据。一般用于轴归约计算等场景。如下图所示，为只对前4个half数据进行ReduceMin计算，可以通过设置mask参数的方法掩掉冗余数据：
示例片段如下：
-   通过Duplicate逐行清零。计算前，针对每一行数据，调用基础API Duplicate对冗余数据位置填充0值，通过设置mask值，控制仅后5个元素位置有效，将冗余数据填充为0，如下图所示：
示例片段如下：
-   通过Pad一次性清零。计算前，针对多行数据，可以采用高阶API Pad接口对冗余数据一次性清零。
示例片段如下：
最后，使用DataCopy对齐数据搬运接口进行数据搬出。

<!-- cannbot:related:start -->
## 相关

- [SwiGLU 高级 API 在非32B对齐 slice 上精度失败](../../../../runbooks/precision/swiglu_adv_api_fails_non_32b_aligned_slice.md)（`related`）：SwiGLU 高级 API 在非32B对齐 slice 上精度失败说明AscendC::SwiGLU 高级 API（adv_api/activation/swiglu.h）在 dav-2201 上对 slice*sizeof(T) 非 32B 整数倍的 case 产生大错值（fp32 slice=509 MARE≈2.5e9；fp16 全零 slice=506 MARE=93/65504），对齐 slice 正常。banned：非对齐 slice 不得用此 API，回退手写 SiLU 链；对非对齐场景而言，非对齐分块需要多核首尾边界方案；SwiGLU 在非 32B slice 的失败实例提供了对齐假设的反证与验证信号。
- [基础矢量算子](basic_vector_operator.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《非对齐场景》说明本节介绍非32字节对齐数据的更多处理方式，包括数据搬入、计算和搬出的处理。用户在实际算子开发中，可以参考如下方案介绍和算子样例灵活地处理非对齐场景。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [多核非对齐切分](../matrix_advanced_api/feature_scenarios/multi_core_unaligned_split.md)（`related`）：多核非对齐切分说明多核场景，对矩阵进行切分时，若M、N、K无法整除singleCoreM 、singleCoreN、 singleCoreK时，就会出现尾块，即多核非对齐场景。如下图矩阵A、B的最后一行和最后一列的矩阵块：；对非对齐场景而言，非对齐分块需要多核首尾边界方案；SwiGLU 在非 32B slice 的失败实例提供了对齐假设的反证与验证信号。
<!-- cannbot:related:end -->
