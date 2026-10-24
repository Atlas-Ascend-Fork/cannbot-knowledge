# runtime

- [AICError 异常定位与 msDebug Core dump 解析](aicerror_exception_localization.md)：采集 AICError 现场、加载异常算子 Core dump，并从异常核、调用栈、寄存器和内存逐层定位到 CATLASS DSL 代码。
- [原子累加残值分布诊断](atomic_residue_pattern_diagnostic.md)：把 atomic add 临时降级为普通写入，用残值元素的模粒度指纹定位未初始化搬运、写者所有权或同步缺口。
- [Cube Vector 死锁与 Credit 审计](cube_vector_deadlock_and_credit_audit.md)：用资源所有权表审计 Cube、FIX、MTE 与 Vector 的 set/wait、启动 credit、循环归还和阶段排空。
- [debug_print、print_tensor 与最小复现](device_printing.md)：设备标量/张量打印的适用范围、同步要求和最小复现方法。
- [Runtime、DLPack 与正确性诊断](runtime_and_correctness.md)：Launch、device、DLPack、数值 oracle 和 layout 不一致的排查顺序。
- [尾块数据损坏定位](tail_corruption_localization.md)：按 batch、head、tile、row 和 lane 聚合误差，区分源 workspace、搬运、计算消费和写回阶段的尾块损坏。
