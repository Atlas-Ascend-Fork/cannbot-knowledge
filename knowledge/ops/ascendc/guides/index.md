# Ascend C 开发指南

- [Ascend C多层级编程接口选择参考](asc_how_to_choose_api.md)：欢迎使用 Ascend C 进行昇腾AI处理器算子开发。Ascend C不仅致力于开放芯片完备编程能力支撑实现极致性能，同时通过多层级编程API设计，让您能够根据项目需求、团队技能与性能目标，灵活选择最合适的API，在开发效率与运行性能之间取得最佳平衡。
- [cross gen migration guide](cross_gen_migration_guide/index.md)：arch22→arch35 迁移与反向生成的参考总纲：给出 L1~L5 分层迁移模型的适用条件与范围（L1 基础适配必做、L2 RegBase 重写、L3 SIMT、L4 需 IsRegbaseSocVersion 或 UB 不足时升级、L5 仅供参考），以及目录地图、被 brief 构建层消费的方式与来源可复现性说明。
- [getting started](getting_started/index.md)：介绍CANN和Ascend C的定位与多层级API体系，提供从快速入门到高级编程的学习路径导航。
- [msprof Agent 使用指南](msprof_agent_guide.md)：让 Agent 用 msprof 做性能分析而不撑爆 context 的指南：先用系统级 msprof 定位瓶颈，落到单算子再用算子级 msopprof（等同 msprof op）展开；核心是分层读取——优先只读 op_statistic 聚合 csv，再按需 grep op_summary 取关键指标，避免读二进制 trace。
- [operator practice](operator_practice/index.md)：本文档主要用于指导开发者基于Ascend C编程语言在昇腾AI处理器上开发高性能的算子。在阅读此文档时，需要开发者具备如下能力：
- [精度验证](precision/index.md)：aclnn 接口调用指南：精度验证必须经 torch_aclnn_helper.h 的 EXEC_NPU_CMD 宏构建 PyTorch C++ Extension，Python 侧用 torch.ops.npu.<op> 调用；不存在 torch.ops.aclnn 命名空间。
- [programming guide](programming_guide/index.md)：本指南为AscendC算子开发综合技术手册，系统涵盖SIMD/SIMT编程模型、语言扩展特性、C++类库API、编译运行机制、调试调优及高级编程等核心技术。文档兼顾入门学习与深度实践，适配不同层级研发人员。入门开发者可依托本指南完成技术体系搭建，资深算子工程师亦可借此深化技术能力，充分挖掘昇腾AI处理器硬件算力，高质量完成自定义算子的开发与性能优化。
- [快速开始](quick_start.md)：根据本地是否有NPU设备和使用目标选择对应的环境准备方式：
- [AscendC SIMD Development Reference](simd_development_reference.md)：AscendC SIMD 开发参考，主张 arch35/A5 上多算子计算链默认走 Regbase MicroAPI 而非 Membase LocalTensor（后者每步 UB 往返加 PipeBarrier，实测拖累可达数十倍）；另含量化 kernel 常用 SIMD API 与 MXFP4 范式。
- [technical appendix](technical_appendix/index.md)：AscendC::TPosition::A1代表设备上用于矩阵计算的逻辑内存，用于存放左矩阵，物理存储对应AI Core的L1 Buffer。

- [regbase](regbase/index.md)：补全 API 汇总中的模板、有效 lane、分组归约和局部存储约束，区分候选目录与实现证据。

- [blaze](blaze/index.md)：将 Block/Copy 的合法 base shape 与 Scheduler 的当前逻辑范围分开，按实际消费者校验 tiling、workspace 和融合后处理。
- [catlass](catlass/index.md)：保存长度、布局、mask 和 MLA 语义，限制固定尺寸与通路结论。
- [diagnostics](diagnostics/index.md)：固定 reference 的调用约束与版本边界。该接口实现AI CPU算子Kernel调试场景下的assert断言功能。 算子执行中，如果assert内部条件判断不为真，则输出assert条件、触发文件名、行号等信息。
- [memory](memory/index.md)：修正以元素数冒充字节数的多处说明，保存不同类型的物理布局。
- [moe](moe/index.md)：将特征、来源三元组、收发计数和量化 scale 按同一有效条目顺序关联，区分最大容量与本轮实际 token 数。
- [reductions](reductions/index.md)：保留 TwoPass、Welford 与分组归约的适用条件。
- [vector](vector/index.md)：补充向量标量分流、scope 搬运和重载身份，限制机械映射。

- [layouts](layouts/index.md)：纠正BA/AB方向及Select极性，保留Softmax布局。
- [shmem](shmem/index.md)：Blaze Heavy Kernel 覆盖与性能条件的来源实现、适用条件与审视结论。
- [synchronization](synchronization/index.md)：用读写集合区分 RAW、WAR 和 WAW，说明额外缓冲与局部屏障的实际作用。
- [torch extensions](torch_extensions/index.md)：对齐 ACLNN 参数、GE OpDef、PyTorch schema 与 Meta/图转换，避免将不同接口层的名称和顺序直接互换。

- [communications](communications/index.md)：APACE AllGather 预触发与 scale 等待边界的来源实例与适用边界。
- [matmul](matmul/index.md)：补齐 Iterate 与 IterateAll 的不同调用、workspace 单位及消费前完成边界。
- [sorting](sorting/index.md)：保存小维度稀疏更新中按索引分组的机制，明确原始位置、跨块分组和累计顺序。

- [simt](simt/index.md)：保留维度和数值语义映射，纠正 shuffle 参数及 VF 统一禁令。

- [tiling](tiling/index.md)：保存多路径选择，纠正D为1直通和未执行Tiling的路径。

- [environments](environments/index.md)：纠正设备修饰符和命名空间的误判，保存Tensor、队列及Mask操作边界。

- [registration](registration/index.md)：核对 L2、L0、OpDef、图推导与 Kernel 的实际支持域，补足广播和空输入检查。

- [attention](attention/index.md)：纠正设计中的二次除法，保存mask、分核和内存尺度条件。
- [performance](performance/index.md)：APACE Host 参数接线与实际计时的来源实例与适用边界。

- [pooling](pooling/index.md)：区分物理行距、有效尾部和特定快速路径的支持范围。

- [data movement](data_movement/index.md)：保存多维搬运和MX物理行距，补齐参数状态与反向映射。

- [testing](testing/index.md)：APACE 多rank启动与 context 复用范围的来源实例与适用边界。

- [compilation](compilation/index.md)：APACE 构建根目录与版本化符号的来源实例与适用边界。
