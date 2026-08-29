---
type: API
title: AscNdimCopyGm2ub
description: 多维数据搬运接口，将数据从GM搬运到UB，支持最多5个维度和Padding功能。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_ndim_copy_gm2ub.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---

# AscNdimCopyGm2ub

多维数据搬运接口，将数据从Global Memory (GM)搬运到Unified Buffer (UB)。相比于基础数据搬移接口，可以更加自由配置搬入的维度信息。 本功能最多能处理5个维度，每个维度都可以单独配置Stride，且支持随路Padding功能。相关配置参数有很多，需要通过不同的接口传入。 表1 Stride配置涉及的所有参数及其传入接口，其中i表示第i维，可取值[0,4]
函数原型：void asc_ndim_copy_gm2ub(__ubuf__ int8_t* dst, __gm__ int8_t* src, uint32_t loop0_size, uint32_t loop1_size, uint32_t loop2_size, uint32_t loop3_size, uint32_t loop4_size, uint8_t loop0_lp_count, uint8_t loop0_rp_count, bool padding_mode, asc_load_l2_cache_mode l2_cache_mode)
约束：各存储单元需满足相应空间大小和对齐要求；多条指令的目的地址重叠时必须插入同步以保证串行。单条指令全部数据的地址范围总宽度不得超过 40 位（1 TB），且 loopi_dst_stride 为升序时，不同循环的地址空间不能交织或重叠。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscLoadL2CacheMode](../enum/asc_load_l2_cache_mode.md)（`related`）：“表示数据从GM搬运到UB时的L2 Cache管理策略，在调用asc_copy_gm2ub_align和asc_ndim_copy_gm2ub时使用。”与“函数原型：void asc_ndim_copy_gm2ub(__ubuf__ int8_t* dst, __gm__ int8_t* src, uint32_t loop0_size, uint32_t loop1_size, uint32_t loop2_size, uint32_t loop3_size, uint32_t loop4_size, uint8_t loop0_lp_count, uint8_t loop0_rp_count, bool padding_mode, asc_load_l2_cache_mode l2_cache_mode)”分别给出双端正文事实；枚举卡定义 GM 到 UB 搬运的 L2 管理策略，asc_ndim_copy_gm2ub 将该枚举作为直接 l2_cache_mode 参数，连接缓存策略选择与多维搬运调用。
- [AscNdimPadCountConfig](../struct/asc_ndim_pad_count_config.md)（`related`）：asc_ndim_pad_count_config用于asc_set_ndim_pad_count接口中，设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。；多维数据搬运接口，将数据从Global Memory (GM)搬运到Unified Buffer (UB)。相比于基础数据搬移接口，可以更加自由配置搬入的维度信息。 本功能最多能处理5个维度，每个维度都可以单独配置Stride，且支持随路Padding功能。；候选是该 padding 配置的最终消费操作。
- [AscSetNdimPadCount](asc_set_ndim_pad_count.md)（`related`）：用于设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。；多维数据搬运接口，将数据从Global Memory (GM)搬运到Unified Buffer (UB)。相比于基础数据搬移接口，可以更加自由配置搬入的维度信息。 本功能最多能处理5个维度，每个维度都可以单独配置Stride，且支持随路Padding功能。相关配置参数有很多，需要通过不同的接口传入。 表1 Stride配置涉及的所有参数及其传入接口，其中i表示第i维，可取值［0,4］；PadCount 配置函数直接为 AscNdimCopyGm2ub 提供逐维左右 padding，主搬运接口明确支持随路 Padding。
- [AscSetNdimPadValue](asc_set_ndim_pad_value.md)（`related`）：“当asc_ndim_copy_gm2ub接口的padding_mode参数为true时，该值将设置为Padding的填充固定值。”给出 pad value 生效条件；“本功能最多能处理5个维度，每个维度都可以单独配置Stride，且支持随路Padding功能。”说明 AscNdimCopyGm2ub 是执行该随路 Padding 的搬运接口。
<!-- cannbot:related:end -->
