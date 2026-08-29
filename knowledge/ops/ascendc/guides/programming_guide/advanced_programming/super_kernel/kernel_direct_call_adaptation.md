---
type: Guide
title: 核函数直调算子额外适配说明
description: 对于使用>>方式开发的Ascend C算子，除了遵循算子适配说明中的通用约束外，还需要在算子Kernel入口侧增加SuperKernel入口函数。本文档介绍具体的适配方法。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/super_kernel/kernel_direct_call_adaptation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核函数直调算子额外适配说明

对于使用>>方式开发的Ascend C算子，除了遵循算子适配说明中的通用约束外，还需要在算子Kernel入口侧增加SuperKernel入口函数。本文档介绍具体的适配方法。
## SuperKernel与普通Kernel的区别
### 普通Kernel入口函数
- 函数签名：__global__ __vector__ void func(参数列表)
- 参数直接作为函数参数传递。
- 直接调用即可。
### SuperKernel入口函数
- 函数签名：__sk__ __vector__ void func(const ArgsStruct *args, sk::SkSystemArgs *sysArgs)
- 参数通过结构体指针传递，需要用户定义参数结构体并封装入参。
- 可选添加sk::SkSystemArgs *sysArgs参数，用于获取系统信息（如block num）。
- 需要与普通Kernel函数通过SK_BIND宏绑定。
## SuperKernel适配规则
### SK子函数编写规则
#### 规则1：函数签名格式
> 注意：只有__sk__是强约束，必须出现在函数签名中。
#### 规则2：Kernel Type标识与原global函数保持一致
- 如果原global函数使用__cube__，则SK子函数也必须使用__cube__。
- 如果原global函数使用__vector__，则SK子函数也必须使用__vector__。
- 如果原global函数是__mix__(c, v)，则SK子函数也必须使用__mix__(c, v)。
示例：
#### 规则3：定义参数结构体
用户需要根据原global函数的实际参数定义一个结构体来封装所有入参：
> 注意：
> - 结构体必须根据用户实际算子核函数（global函数）的参数进行定义，不要直接复制示例中的字段名。
> - 结构体字段必须按原函数参数顺序排列。
> - 对于size小于4字节的类型（如int16_t、int8_t、uint16_t、uint8_t），必须使用alignas(4)确保内存对齐（ABI要求）。
> - 示例：alignas(4) int16_t val;、alignas(4) uint8_t flag;
#### 规则4：可选添加SkSystemArgs参数
如果原算子使用了AscendC::GetBlockNum()接口，在SK场景下可以通过添加sk::SkSystemArgs *sysArgs参数来获取期望的block num：
> 注意：
> - sk::SkSystemArgs *sysArgs参数是可选的，如果算子未使用block num信息，或者sk::SkSystemArgs提供的功能（当前仅支持获取block num），则无需在函数入口传入sysArgs参数，这样可以避免不必要的代码修改。
> - 用户需要根据实际情况修改原代码中的AscendC::GetBlockNum()调用：
>   - 直接使用sysArgs->skNumBlocks访问成员变量。
>   - 或者使用sysArgs->SkGetNumBlocks()接口获取。

<!-- cannbot:related:start -->
## 相关

- [SK_BIND（SuperKernel）](../../../../apis/utils_api/super_kernel/sk_bind.md)（`explains`）：本接口为算子SuperKernel场景提供绑定原核函数和SK子函数的能力。核函数直调算子的完整适配方法请参见核函数直调算子额外适配说明。；- 需要与普通Kernel函数通过SK_BIND宏绑定。。API 卡定义 SK_BIND 的绑定能力并指向直调适配说明，Guide 把该宏列为 SuperKernel 入口与普通 Kernel 配套的必需步骤。
- [SuperKernel原理介绍](principles.md)（`related`）：核函数直调算子额外适配说明：对于使用>>方式开发的Ascend C算子，进入SuperKernel前需要进行的额外适配工作。；对于使用>>方式开发的Ascend C算子，除了遵循算子适配说明中的通用约束外，还需要在算子Kernel入口侧增加SuperKernel入口函数。本文档介绍具体的适配方法。；目标指南展开焦点明确列出的直调算子额外适配路径。
- [基于样例工程完成Kernel直调](../../appendix/kernel_direct_call_from_sample.md)（`related`）：完成算子kernel侧实现；需要在算子Kernel入口侧增加SuperKernel入口函数。样例工程卡给出普通 Kernel 直调的构建、Host 调用和验证流程，适配卡说明把这类直调算子纳入 SuperKernel 时必须增加 SK 入口、参数结构和 SK_BIND 的差异步骤。
- [算子适配说明](operator_adaptation.md)（`related`）：对于使用>>方式开发的Ascend C算子，除了遵循算子适配说明中的通用约束外，还需要在算子Kernel入口侧增加SuperKernel入口函数。本文档介绍具体的适配方法。；自定义算子要支持融合进SuperKernel，开发流程上与普通算子并无显著差异，但需要遵循以下一系列特定约束。这些约束与具体的开启方式（npugraph_ex后端或GE图模式）无关，大部分约束与算子启动核数（block num）以及SuperKernel启动核数之间的关系相关，需要开发者在算子设计阶段就予以关注。Kernel 直调适配明确建立在通用算子适配约束之上，并增加入口函数这一专属步骤，二者组成完整接入链。
<!-- cannbot:related:end -->
