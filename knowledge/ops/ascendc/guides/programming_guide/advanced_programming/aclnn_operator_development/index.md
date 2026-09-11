# aclnn operator development

- [Aclnn算子工程化开发快速入门](aclnn_quick_start.md)：本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
- [附录](appendix/index.md)：本文是参考内容，整理算子工程编译过程涉及的CMake函数接口，供需要深入了解编译机制的高级开发者查阅。
- [compilation and deployment](compilation_and_deployment/index.md)：本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：
- [design and implementation](design_and_implementation/index.md)：本文介绍如何编写并注册GenSimplifiedKey回调。该回调用于预编译多份核函数（Kernel）binary的场景：算子开发者根据本次调用的输入、输出和属性生成一个自定义simplified key片段，运行时框架使用该片段查找对应的binary。
- [invocation](invocation/index.md)：本文是扩展内容，介绍算子开发完成后，编译产物如何被加载和执行，以及开发时的设计决策如何影响运行表现。本文从算子开发者视角梳理运行时调用的基本模型和代码写法对运行行为的影响。
- [高级编程概述](overview.md)：本文是基础内容，说明Aclnn算子工程化开发这组文档的范围、阅读顺序和前置条件。建议先确认环境满足要求，再按快速入门跑通AddCustom示例，跑通后回到对应章节逐步补齐细节。
