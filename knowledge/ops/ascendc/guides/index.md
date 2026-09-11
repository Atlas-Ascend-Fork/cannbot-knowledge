# Ascend C 开发指南

- [Ascend C多层级编程接口选择参考](asc_how_to_choose_api.md)：欢迎使用 Ascend C 进行昇腾AI处理器算子开发。Ascend C不仅致力于开放芯片完备编程能力支撑实现极致性能，同时通过多层级编程API设计，让您能够根据项目需求、团队技能与性能目标，灵活选择最合适的API，在开发效率与运行性能之间取得最佳平衡。
- [cross gen migration guide](cross_gen_migration_guide/index.md)：本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表1，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。
- [getting started](getting_started/index.md)：介绍CANN和Ascend C的定位与多层级API体系，提供从快速入门到高级编程的学习路径导航。
- [operator practice](operator_practice/index.md)：本文档主要用于指导开发者基于Ascend C编程语言在昇腾AI处理器上开发高性能的算子。在阅读此文档时，需要开发者具备如下能力：
- [programming guide](programming_guide/index.md)：本指南为AscendC算子开发综合技术手册，系统涵盖SIMD/SIMT编程模型、语言扩展特性、C++类库API、编译运行机制、调试调优及高级编程等核心技术。文档兼顾入门学习与深度实践，适配不同层级研发人员。入门开发者可依托本指南完成技术体系搭建，资深算子工程师亦可借此深化技术能力，充分挖掘昇腾AI处理器硬件算力，高质量完成自定义算子的开发与性能优化。
- [快速开始](quick_start.md)：根据本地是否有NPU设备和使用目标选择对应的环境准备方式：
- [technical appendix](technical_appendix/index.md)：AscendC::TPosition::A1代表设备上用于矩阵计算的逻辑内存，用于存放左矩阵，物理存储对应AI Core的L1 Buffer。
