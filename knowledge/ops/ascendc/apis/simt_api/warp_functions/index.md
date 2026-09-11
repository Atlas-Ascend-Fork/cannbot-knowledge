# Warp函数

- [Lane ID类函数](lane_id_functions/index.md)：获取线程在其所在Warp内的索引。
- [Warp函数](warp_functions_intro.md)：Warp是SIMT线程执行和调度的基本单位。一个线程块内的线程会按照线性线程号被划分为多个Warp，当前一个Warp包含32个线程。同一Warp内的线程执行相同的指令流，但每个线程拥有独立的寄存器和Lane ID，可处理不同的数据地址和分支路径。
- [Warp Reduce类函数](warp_reduce_functions/index.md)：对Warp内所有活跃线程输入的val求和。Warp内所有活跃线程返回相同的结果。
- [Warp Shfl类函数](warp_shfl_functions/index.md)：Warp级数据交换接口，按分组宽度获取指定线程持有的变量值，支持数据分发与动态交换场景
- [Warp Vote类函数](warp_vote_functions/index.md)：查看Warp内所有线程是否为活跃状态。 返回一个32bit的无符号整数，若Warp内某个线程是活跃（已结束线程是非活跃状态）的，则返回值中与线程Lane ID对应的bit位为1，否则为0。Warp内所有活跃线程返回相同的结果。
