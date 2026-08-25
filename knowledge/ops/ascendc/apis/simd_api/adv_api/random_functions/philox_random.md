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

- [Philox offset 须放 counter[2:3] 而非 [0:1]](../../../../runbooks/precision/philox_offset_counter_2_3_0_1.md)（`exemplifies`）：PhiloxRandom API 定义 128bit counter、key 与 count 的消费接口，是 counter[2:3] offset 布局最终进入随机数生成的执行端。
- [PhiloxRandom 默认 7 rounds 与原生 10 不匹配](../../../../runbooks/precision/philoxrandom_7_rounds_10.md)（`exemplifies`）：PhiloxRandom 默认 7 rounds 与原生 10 不匹配 与《PhiloxRandom》的实质衔接是：Philox 与原生逐元素对齐同时依赖显式 10 rounds、counter[2:3]、offset=12、group4 切分及 uint 到 uniform/exponential 转换，所选卡组成同一 RNG 序列契约。
- [SIMT 切分未 coalesce 致 block 边界错位](../../../../runbooks/precision/simt_coalesce_block.md)（`exemplifies`）：API 明确 PhiloxRandom 以 128bit counter、seed/subsequence/counter 状态生成序列，解释本卡为何 block 边界变化会改变后续随机数而非仅改变执行顺序。
- [Uint32ToFloat 须用 IEEE754 位操作而非位移乘法](../../../../runbooks/precision/uint32tofloat_ieee754.md)（`exemplifies`）：Uint32ToFloat 须用 IEEE754 位操作而非位移乘法 与《PhiloxRandom》的实质衔接是：bit-exact 随机链必须与 Philox 原生实现一致：counter/round/offset 先生成 uint32，再按 IEEE754 尾数位重解释；通用 Cast 不能替代该位级契约。
- [exponential_ 0% 匹配须改 -log(1-u) 路径](../../../../runbooks/precision/exponential_0_log_1_u.md)（`exemplifies`）：“PhiloxRandom”处理基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。；“exponential_ 0% 匹配须改 -log(1-u) 路径”明确自定义 AscendC kernel 拦截 aten.exponential_ 同 seed 0% bit-exact 匹配时，判别 kernel exponential 分支是否存 u 直接 Log(u)（坏模式）：native aclnnInplaceUniform 生成 u∈[0,1) 后存 1-u∈(0,1] 再 …。实质衔接：这些卡直接定位 PhiloxRandom 的轮数、counter/offset、每核 group=4 对齐以及 uint32 到浮点分布变换，能够执行性地解释随机序列不一致。
- [philox offset 推进量须固定 12 而非元素数](../../../../runbooks/precision/philox_offset_12.md)（`exemplifies`）：philox offset 推进量须固定 12 而非元素数 与《PhiloxRandom》的实质衔接是：Philox 多次调用的一致性同时依赖固定 offset=12、10 rounds、counter[2:3]、每核 group4 和 uint32→uniform/exponential 转换。
- [多核 numPerCore 须对齐 Philox group 4](../../../../runbooks/precision/numpercore_philox_group_4.md)（`exemplifies`）：“PhiloxRandom”处理基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。；“多核 numPerCore 须对齐 Philox group 4”明确bit-exact 复现原生随机算子时，host 自算的多核 numPerCore 必须向上对齐到 Philox group size 4，否则跨核元素落入不同 counter group，从某元素起全线偏移。。实质衔接：这些卡直接定位 PhiloxRandom 的轮数、counter/offset、每核 group=4 对齐以及 uint32 到浮点分布变换，能够执行性地解释随机序列不一致。
- [随机函数](random_functions.md)（`related`）：随机函数总览当前唯一展开的生成接口是 PhiloxRandom，目标卡给出其计数器、key、rounds 与输出契约。
<!-- cannbot:related:end -->
