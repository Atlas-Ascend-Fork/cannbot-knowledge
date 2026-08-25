# basic api

- [interface classification](interface_classification/index.md)：连续计算API，支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连续写入目的操作数，解决一维tensor的连续计算问题。
- [基础API概述](overview.md)：基础API实现对硬件能力的抽象，开放芯片的能力，保证完备性和兼容性。标注为ISASI（Instruction Set Architecture Special Interface，硬件体系结构相关的接口）类别的API，不能保证跨硬件版本兼容。
- [quick reference](quick_reference/index.md)：Mask用于控制矢量计算中参与计算的元素个数，支持以下工作模式及配置方式：
