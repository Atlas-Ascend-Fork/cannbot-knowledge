---
type: API
title: asc_copy_l12l0a
description: 用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# asc_copy_l12l0a

用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。

参数：dst(输出): 目的L0A Buffer地址。；src(输入): 源L1 Buffer地址。；m_start_position(输入): 以M*K矩阵为例，源矩阵M轴方向的起始位置，单位为16个元素。；k_start_position(输入): 以M*K矩阵为例，源矩阵K轴方向的起始位置，单位为32B。；m_step(输入): 以M*K矩阵为例，源矩阵M轴方向搬运长度，单位为16个元素。取值范围：[0, 255]。当进行转置搬运时，还需满足以下额外约束： 数据位宽为4时，m_step必须为4的倍数； 数据位宽为8时，m_step必须为2的倍数； 数据位宽为16时，m_step必须为1的倍数； 数据位宽为32时，m_step无额外约束。；k_step(输入): 以M*K矩阵为例，源矩阵M轴方向搬运长度，单位为32B。取值范围：[0. 255]。当进行转置搬运时，还需满足以下额外约束： 数据位宽为4、8或16时，k_step没有额外约束； 数据位宽为32时，k_step必须是2的倍数。；src_stride(输入): 以M*K矩阵为例，源矩阵K方向前一个分形起始地址与后一个分形起始地址的间隔，单位为512B。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [CMake arch 子目录隔离 dav-3510 专属 API](../../../../../runbooks/compilation/cmake_arch_dav_3510_api.md)（`exemplifies`）：asc_copy_l12l0a 与《CMake arch 子目录隔离 dav-3510 专属 API》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [2201到3510架构变更](../../../../../guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_arch_changes.md)（`explains`）：asc_copy_l12l0a 与《2201到3510架构变更》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [避免bank冲突（NPU架构版本3510）](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_3510.md)（`explains`）：asc_copy_l12l0a 与《避免bank冲突（NPU架构版本3510）》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [AscCopyGm2l0a](../asc_copy_gm2l0a.md)（`related`）：asc_copy_l12l0a 与《AscCopyGm2l0a》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [AscSetL13dPadding](../asc_set_l13d_padding.md)（`related`）：《asc_copy_l12l0a》明确“用于搬运存放在L1 Buffer里的512B大小的矩阵到L0A Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。”；它与《AscSetL13dPadding》的“设置asc_copy_l12l0a搬运接口的Pad填充数值。”在实际调用参数、数据流或结果校验上直接衔接。
- [asc_copy_gm2l1](../asc_copy_gm2l1/asc_copy_gm2l1_arch_2201.md)（`related`）：asc_copy_l12l0a 与《asc_copy_gm2l1》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [asc_copy_gm2l1](../asc_copy_gm2l1/asc_copy_gm2l1_arch_3510.md)（`related`）：asc_copy_l12l0a 与《asc_copy_gm2l1》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [矩阵数据搬运](../cube_data_move.md)（`related`）：asc_copy_l12l0a 与《矩阵数据搬运》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [AscCopyL12L0a](asc_copy_l12l0a.md)（`same_topic`）：asc_copy_l12l0a 与《AscCopyL12L0a》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [AscCopyL12l0aMx](../asc_copy_l12l0a_mx.md)（`same_topic`）：asc_copy_l12l0a 与《AscCopyL12l0aMx》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [AscCopyL12l0aTrans](../asc_copy_l12l0a_trans.md)（`same_topic`）：asc_copy_l12l0a 与《AscCopyL12l0aTrans》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [asc_copy_l12l0a](asc_copy_l12l0a_arch_2201.md)（`same_topic`）：asc_copy_l12l0a 与《asc_copy_l12l0a》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
<!-- cannbot:related:end -->
