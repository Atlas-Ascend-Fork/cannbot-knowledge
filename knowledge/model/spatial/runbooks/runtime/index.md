# 运行问题

- [3DGS build mask 向量核异常：TileSum 的元素数被当成字节数](flash_gaussian_build_mask_ub_overflow.md)：在 A2 大 tile 数的 flash_gaussian_build_mask 中，按 int32 元素宽度检查 UB 分配、SetValue 和 DataCopyPad 的一致性。
