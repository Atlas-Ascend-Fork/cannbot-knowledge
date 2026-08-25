# aclnn operator development

- [Aclnn算子工程化开发快速入门](aclnn_quick_start.md)：本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。
- [附录](appendix/index.md)：aclnn算子开发附录，包含命名转换规则、cmake函数参考与外部样例链接。
- [compilation and deployment](compilation_and_deployment/index.md)：本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：
- [design and implementation](design_and_implementation/index.md)：本文属于基础内容，介绍Host侧Tiling在aclnn工程化算子开发方式中的基本编写流程。Host侧Tiling承接算子功能设计中的Tiling设计结论，把输入shape、属性和运行场景转换成Kernel启动前需要的参数。
- [invocation](invocation/index.md)：本文是扩展内容，介绍算子开发完成后，编译产物如何被加载和执行，以及开发时的设计决策如何影响运行表现。本文从算子开发者视角梳理运行时调用的基本模型和代码写法对运行行为的影响。
- [高级编程概述](overview.md)：本文是基础内容，说明Aclnn算子工程化开发这组文档的范围、阅读顺序和前置条件。建议先确认环境满足要求，再按快速入门跑通AddCustom示例，跑通后回到对应章节逐步补齐细节。
