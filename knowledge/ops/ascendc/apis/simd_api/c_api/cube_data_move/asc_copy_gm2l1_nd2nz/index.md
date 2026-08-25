# AscCopyGm2L1Nd2Nz

- [AscCopyGm2L1Nd2Nz](asc_copy_gm2l1_nd2nz.md)：GM到L1 Buffer带ND2NZ格式转换的数据搬运接口集合，包含不同架构版本。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz_arch_2201.md)：将数据从Global Memory (GM)搬运到Level 1 cache (L1)，支持在数据搬运时进行ND格式到NZ格式的转换。
- [asc_copy_gm2l1_nd2nz](asc_copy_gm2l1_nd2nz_arch_3510.md)：将矩阵数据从Global Memory搬运到L1 Buffer，在此过程中执行ND->NZ/NHWC->NC1HWC0/NHWC->C1HWNC0操作。若D未对齐C0/type(dst)的大小，将会在L1的最内层维度填充0值。GM中的数据以ND类型存储；L1中的数据以NZ形式存储。 ND->N...
