---
type: API
title: asc_copy_l12l0b
description: 用于搬运存放在L1 Buffer里的512B大小的矩阵到L0B Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l12l0b/asc_copy_l12l0b_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# asc_copy_l12l0b

用于搬运存放在L1 Buffer里的512B大小的矩阵到L0B Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。

参数：dst(输出): 目的L0B Buffer地址。；src(输入): 源L1 Buffer地址。；m_start_position(输入): 以M*K矩阵为例，源矩阵M轴方向的起始位置，单位为16个元素。；k_start_position(输入): 以M*K矩阵为例，源矩阵K轴方向的起始位置，单位为32B。；m_step(输入): 以M*K矩阵为例，源矩阵M轴方向搬运长度，单位为16个元素。取值范围：[0, 255]。进行转置搬运时，还需满足以下额外约束： 数据位宽为4时，m_step必须为4的倍数； 数据位宽为8时，m_step必须为2的倍数； 数据位宽为16时，m_step必须为1的倍数； 数据位宽为32时，m_step无额外约束。；k_step(输入): 以M*K矩阵为例，源矩阵M轴方向搬运长度，单位为32B。取值范围：[0. 255]。进行转置搬运时，还需满足以下额外约束： 数据位宽为4、8或16时，k_step没有额外约束； 数据位宽为32时，k_step必须是2的倍数。；src_stride(输入): 以M*K矩阵为例，源矩阵K方向前一个分形起始地址与后一个分形起始地址的间隔，单位为512B。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_copy_l12l0b](asc_copy_l12l0b_arch_2201.md)（`same_topic`）：用于搬运存放在L1 Buffer里的512B大小的矩阵到L0B Buffer里。包含2D格式搬运、3D格式搬运。；用于搬运存放在L1 Buffer里的512B大小的矩阵到L0B Buffer里，包含2D格式搬运、2D格式转置搬运、3D格式搬运。；两卡是同一 L1 到 L0B 512B 搬运接口的平台版本，Arch3510 增加 2D 转置路径，适合比较迁移差异。
<!-- cannbot:related:end -->
