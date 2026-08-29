---
type: API
title: PhiloxRandom
description: 基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.random_sampling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/random_functions/PhiloxRandom.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# PhiloxRandom

基于Philox算法生成随机数，支持生成half/float/int32_t类型的随机数。通过seed和subsequence初始化随机数生成器，可在counter基础上生成指定数量的随机数。

函数原型提供通过sharedTmpBuffer传入临时空间和接口框架申请两种方式。接口参数包含dstTensor输出随机数Tensor、sharedTmpBuffer临时缓存、PhiloxRandomState随机数生成器状态（含seed、subsequence、counter等信息）、calCount生成元素个数。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [PhiloxRandom 默认 7 rounds 与原生 10 不匹配](../../../../runbooks/precision/philoxrandom_7_rounds_10.md)（`exemplifies`）：基于Philox算法生成随机数，支持生成half/float/int32_t类型的随机数。通过seed和subsequence初始化随机数生成器，可在counter基础上生成指定数量的随机数。；自定义 kernel 调用 `AscendC::PhiloxRandom` 时沿用了 CANN 公共头文件 `philox.h` 的模板默认值 `Rounds=7`，但原生 `aclnnSimThreadExponential` 实际使用 PyTorch 标准 **Philox-4x32-10**（10 rounds）。rounds 数直接决定 Philox 单轮轮函数的迭代次数，7 vs 10 产出的 32 位输出完全不同，因此即使 seed/offset/counter 完全相同，单次调用也 0% 匹配。。API 卡提供 PhiloxRandom 的 seed/subsequence/counter 使用面，runbook 给出与原生 exponential 对齐时必须显式选择 10 rounds 的已验证排障边界。
- [Uint32ToFloat 须用 IEEE754 位操作而非位移乘法](../../../../runbooks/precision/uint32tofloat_ieee754.md)（`exemplifies`）：**API 路径**：AscendC kernel 内 uint32 随机数 → float 转换；对标 CANN `StatelessRandomUniformV2::Uint32ToFloat`（`stateless_random_uniform_v2.h`，arch35 opp 子目录）。；基于Philox算法生成随机数，支持生成half/float/int32_t类型的随机数。通过seed和subsequence初始化随机数生成器，可在counter基础上生成指定数量的随机数。；API 生产由 seed/subsequence/counter 决定的随机流，焦点规定要求 bit-exact 时 uint32 消费到 float 的转换方式。
<!-- cannbot:related:end -->
