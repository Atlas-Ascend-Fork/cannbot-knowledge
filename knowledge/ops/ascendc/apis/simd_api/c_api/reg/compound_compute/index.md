# 复合计算

- [AscAbsSub](asc_abs_sub.md)：根据mask对源操作数src0和src1进行按元素相减再求绝对值，将结果写入dst。
- [AscAxpy](asc_axpy.md)：根据mask将src每个元素与标量value求积后与dst对应元素相加，结果写回dst。
- [AscExpSub](asc_exp_sub_deprecated.md)：将src0与src1相减的差值作为e的指数计算，结果写入dst。
- [AscFma](asc_fma.md)：完成src0与src1逐元素相乘再加dst的融合乘加运算，根据mask将结果写回dst。
- [AscMadd](asc_madd.md)：完成dst与src0逐元素相乘再加src1的融合乘加运算，根据mask将结果写回dst。
- [复合计算](compound_compute.md)：寄存器侧复合计算类接口汇总，提供abs_sub、axpy、madd、fma等多操作融合的矢量计算能力。
