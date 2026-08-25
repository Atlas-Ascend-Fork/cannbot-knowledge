---
type: API
title: AscCopyL12gm
description: 将数据从L1 Buffer搬运到GM。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12gm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscCopyL12gm

将数据从L1 Buffer搬运到Global Memory。

参数：dst(输出): 目的操作数的起始地址。；src(输入): 源操作数的起始地址。；n_burst(输入): 待搬运的连续传输数据块个数。取值范围：[1, 4095]。；len_burst(输入): 待搬运的每个连续传输数据块的长度，单位为32个字节。取值范围：[1, 65535]。；src_gap(输入): 相邻迭代间，源操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。；dst_gap(输入): 相邻迭代间，目的操作数前一个迭代第一个分形的结束地址到下一个迭代第一个分形起始地址的间隔。单位为32字节。

约束：- 各存储单元的空间大小和对齐要求
- 如果需要执行多条asc_copy_l12gm指令，且asc_copy_l12gm指令的目的地址存在重叠，需要插入同步指令，保证多个asc_copy_l12gm指令的串行化，防止出现异常数据。

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [基础API迁移指导](../../../../guides/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)（`explains`）：AscCopyL12gm 在 2201 上提供 L1→GM 直达搬运，而《基础API迁移指导》明确 3510 不再支持该路径并要求改为 L1→UB→GM；这是迁移该调用所必需的替代契约。
- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm_arch_2201.md)（`related`）：AscCopyL12gm 与《AscCopyL0c2Gm》的实质衔接是：AscCopyL12gm 是 L1 到 GM 的数据路径；L1 到 UB、L0C 到 UB/GM 接口提供相邻存储层的可执行搬运组合，迁移指导则明确 3510 删除该直达路径后的替代方案。
- [AscCopyL0c2Gm](asc_copy_l0c2gm/asc_copy_l0c2gm_arch_3510.md)（`related`）：AscCopyL12gm 与《AscCopyL0c2Gm》的实质衔接是：AscCopyL12gm 是 L1 到 GM 的数据路径；L1 到 UB、L0C 到 UB/GM 接口提供相邻存储层的可执行搬运组合，迁移指导则明确 3510 删除该直达路径后的替代方案。
- [AscCopyL0c2ub](asc_copy_l0c2ub.md)（`related`）：AscCopyL12gm 与《AscCopyL0c2ub》的实质衔接是：AscCopyL12gm 是 L1 到 GM 的数据路径；L1 到 UB、L0C 到 UB/GM 接口提供相邻存储层的可执行搬运组合，迁移指导则明确 3510 删除该直达路径后的替代方案。
- [AscCopyL12ub](asc_copy_l12ub.md)（`related`）：AscCopyL12gm 与《AscCopyL12ub》的实质衔接是：AscCopyL12gm 是 L1 到 GM 的数据路径；L1 到 UB、L0C 到 UB/GM 接口提供相邻存储层的可执行搬运组合，迁移指导则明确 3510 删除该直达路径后的替代方案。
<!-- cannbot:related:end -->
