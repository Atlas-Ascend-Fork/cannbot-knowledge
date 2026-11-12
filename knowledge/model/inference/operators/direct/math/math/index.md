# 模型推理数学计算

- [RowArgmax A2/A3 Direct Invoke 算子知识](sgl_row_argmax.md)：闭合FP32行argmax的扫描获胜tile再重读策略、NaN与并列最小索引、空行和编译launcher缓存，区分逻辑32KB tile与物理分配。
- [RowArgmax 950 Direct Invoke 算子知识](sgl_row_argmax_950.md)：闭合FP32行argmax的扫描获胜tile再重读策略、NaN与并列最小索引、空行和编译launcher缓存，区分逻辑32KB tile与物理分配。
- [FusedScaleShift A2/A3 Direct Invoke 算子知识](sgl_scale_shift.md)：闭合scale/shift两Kernel五候选与11条广播路线，区分full优先、scale_constant与显式dtype转换，记录非二次幂行块和编译器分配边界。
- [FusedScaleShift 950 Direct Invoke 算子知识](sgl_scale_shift_950.md)：闭合scale/shift两Kernel五候选与11条广播路线，区分full优先、scale_constant与显式dtype转换，记录非二次幂行块和编译器分配边界。
- [单位三角矩阵求逆 A3 Direct Invoke 算子知识](sgl_triangular_inverse.md)：说明 triangular_inverse 的 FP16/FP32 列扫实现、物理存储与单位对角前提、逐字段参数、单 AIV 启动、UB 复用及未校验边界。
