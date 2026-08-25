# ReduceProd接口

- [GetReduceProdMaxMinTmpSize](get_reduce_prod_max_min_tmp_size.md)：在host侧获取ReduceProd接口计算所需的最大和最小临时空间大小，用于选择合适的空间作为Tiling参数传递到kernel侧。
- [ReduceProd](reduce_prod.md)：对一个多维向量在指定的维度求积。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为\(2, 3\)的二维矩阵进行运算，指定在第一维求乘积，输出结果为\[4, 10, 18\]；指定在第二维求乘积，输出结果为\[6, 120\]。 图1 ...
- [ReduceProd接口](reduce_prod_interface.md)：对多维向量在指定维度求连乘积，并提供临时空间大小获取接口。
