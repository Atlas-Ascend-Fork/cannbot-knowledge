# AscCopyGm2L1

- [AscCopyGm2L1](asc_copy_gm2l1.md)：GM到L1 Buffer数据搬运接口集合，包含不同架构版本asc_copy_gm2l1_arch_2201和asc_copy_gm2l1_arch_3510。
- [asc_copy_gm2l1](asc_copy_gm2l1_arch_2201.md)：将矩阵数据从Global Memory搬运到L1 Buffer中，并支持不同类型的pad模式。
- [asc_copy_gm2l1](asc_copy_gm2l1_arch_3510.md)：将矩阵数据从Global Memory搬运到L1 Buffer中，支持以下两种搬运模式： - 填充模式：搬运过程中可以对数据进行填充或移除填充值。 - 2D搬运模式：支持2D矩阵数据搬运，支持压缩能力。（NPU_ARCH 220x版本不支持.）
