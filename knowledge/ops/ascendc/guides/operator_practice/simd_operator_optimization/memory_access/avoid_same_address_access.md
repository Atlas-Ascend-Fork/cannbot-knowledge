---
type: Guide
title: 避免同地址访问
description: '>该性能优化指导适用于如下产品型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/avoid_same_address_access.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 避免同地址访问

【优先级】高
【描述】MTE2、MTE3、Scalar等单元访问Global Memory数据时，其地址请求会按照512字节粒度对齐后进行处理。当同时访问Global Memory的数据，且地址处于连续的512字节范围内时，由于数据一致性的原因，多个请求会被串行处理，进而影响数据搬运效率。
当前算子执行机制保证用户Kernel入参（包括Workspace/Tiling）的地址512字节对齐，因此开发者只需要根据地址的偏移量即可判断两个地址是否会落入连续的512字节范围内。
如下图所示，AI Core内的各个核对Global Memory的数据同时发出读写请求，尽管addr0\~addr5是多个不同的地址，但因为落在连续的512字节范围内，被视为同一个地址请求，此时这几个数据请求会被串行处理，数据访问效率会降低。同地址访问的影响受同时访问的核数影响，同地址访问的核数越多时，串行导致的性能劣化越严重。
避免同地址访问的方法主要是调整数据访问顺序。下文介绍配套的样例请参考DataCopy最佳实践样例中的优化点4。
调整数据访问顺序
本节以Atlas A2 训练系列产品/Atlas A2 推理系列产品或Atlas A3 训练系列产品/Atlas A3 推理系列产品上一个形状为 [6144, 512]的half类型输入进行GM到UB搬运这一种场景为例，说明如何通过调整数据访问顺序规避同地址访问冲突，该场景使用48个核参与搬运，即numBlocks=48。
为了体现同地址冲突的影响，上述场景关闭L2Cache hint。输入每行数据大小为1024字节（512个half），Tile为 ([128, 64])，通过DataCopyPad完成GM到UB搬运。每个核都会完整载入一遍输入矩阵，N方向按64列切分，单次搬运数据量为128 * 64 * 2字节。原始实现中，所有核按相同的mBlockIdx顺序访问同一输入矩阵，容易在同一时刻访问相同的GM地址段；优化实现中，每个核按 ((mBlockIdx + blockIdx) \% numBlocks)在块组内轮转访问顺序，降低同地址访问冲突概率。
下文示意图中，M0-M47表示输入矩阵沿M方向切分后的48个分块，T0-T47表示时间轴上的48个搬运时刻。

<!-- cannbot:related:start -->
## 相关

- [asc_nop（内存访问函数）](../../../../apis/simt_api/memory_access_functions/asc_nop.md)（`explains`）：主要用于避免多个线程读写同地址时可能发生的卡死问题。；当同时访问Global Memory的数据，且地址处于连续的512字节范围内时，由于数据一致性的原因，多个请求会被串行处理，进而影响数据搬运效率。；目标页补充同地址请求的 512 字节归并和串行机制，可用于识别 asc_nop 所针对的访问形态。
<!-- cannbot:related:end -->
