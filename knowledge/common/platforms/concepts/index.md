# 硬件参考

Ascend 910B/910_95 硬件规格与强制约束速查。生成任何 Triton Ascend kernel 之前必须过一遍约束检查清单。

- [ascend_910b](ascend_910b.md)：910B2/910B3 核心架构、Grid 语义、内存层次、编译选项
- [ascend_910_95](ascend_910_95.md)：910_95/950PR/950DT（dav-c310，Reg-based A5 架构）核数、UB/L1/L0C 容量、专有数据通路与 910B 差异
- [npu_memory_model](npu_memory_model.md)：GM/L1/UB/L0A/L0B/L0C 存储层次、MTE/FIX 数据通路与 tl.load/store/dot 的硬件映射
- [constraints_cheatsheet](constraints_cheatsheet.md)：强制约束速查（UB/Gird/对齐） + 性能约束 + autotune 搜索空间
- [ascend_patterns](ascend_patterns.md)：Ascend 特有的编程模式与 GPU→Ascend 迁移差异
