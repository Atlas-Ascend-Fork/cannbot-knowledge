# 基础数学直调算子

本目录保存基础数学与选择类 Direct Invoke 算子知识。

- [ArgMax A5](arg_max_a5.md)：说明 A5 最大值索引归约、布局专用与跨核路线。
- [Cummin A5](cummin_a5.md)：说明 A5 累积最小值的 AIV、SIMT 与多 Kernel 扫描路线。
- [Exp A5](exp_a5.md)：说明 A5 指数计算的 dtype 和向量流水特化路线。
- [Gcd A5](gcd_a5.md)：说明 A5 最大公约数的 SIMT 与广播 fallback 路线。
- [MaskedScale A5](masked_scale_a5.md)：说明 A5 掩码缩放的广播、DAG 与 UB 复用路线。
- [Maximum A5](maximum_a5.md)：说明 A5 等形和多类广播 Maximum 路线。
- [TopK A5](top_k_a5.md)：说明 A5 TopK 的 radix、merge、SIMT、NDDMA 与 workspace 路线。
