# cross gen migration guide

- [3510 arch migration](3510_arch_migration/index.md)：NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：
- [Ascend C API兼容性策略](ascend_c_api_compatibility.md)：本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表1，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。
- [instructions for new features](instructions_for_new_features/index.md)：本文介绍NPU架构版本3510新增特性，为开发者将算子程序从其他架构迁移至3510架构提供参考。有关3510架构的整体变更，请参见2201到3510架构变更。
- [跨代迁移指南概述](overview.md)：Ascend C的核心设计目标之一是实现跨代兼容。然而，每一代芯片在微架构上都存在独特的硬件特性，因此无法保证所有接口仅通过重编译就能达成完全的跨代兼容。基于这一前提，本手册旨在为Ascend C算子开发者提供系统化指导，帮助将算子Kernel代码从当前芯片平滑移植到目标代际芯片上运行，实现高效、可控的迁移。
