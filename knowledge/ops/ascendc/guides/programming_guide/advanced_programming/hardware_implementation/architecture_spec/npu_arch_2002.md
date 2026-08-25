---
type: Guide
title: NPU架构版本2002
description: '本节介绍__NPU_ARCH__版本号为2002的硬件架构和其功能说明。对应的产品型号为:'
tags: [task.lookup, topic.programming_model.execution_unit]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2002.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# NPU架构版本2002

本节介绍__NPU_ARCH__版本号为2002的硬件架构和其功能说明。对应的产品型号为:
-   Atlas 推理系列产品
## 硬件架构图
## 计算单元
Cube计算单元和Vector计算单元同核部署
本架构中，Cube计算单元和Vector计算单元同核部署，共享同一个Scalar计算单元。
Vector计算单元
-   Vector计算单元的数据来源来自于Unified Buffer，要求32字节对齐。
-   数据从L0C Buffer传输至Unified Buffer需要以Vector计算单元作为中转。
Cube计算单元
-   Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和中间结果。
## 存储单元
获取存储单元的内存空间大小
开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。
各存储单元的最小访问粒度（对齐要求）
各存储单元推荐使用的数据排布格式
-   L0A Buffer、L0B Buffer和L0C Buffer推荐分别采用以下分形格式：
-   L0A Buffer：FRACTAL_ZZ
-   L0B Buffer：FRACTAL_ZN
-   L0C Buffer：FRACTAL_NZ
这些格式针对矩阵乘法等计算密集型任务进行优化，可显著提升计算效率。
-   L1 Buffer缓存推荐使用FRACTAL_NZ格式。当L1采用NZ格式时，数据搬运到L0A/L0B Buffer（需分别转换为ZZ和ZN格式）时，可降低格式转换开销。
-   Unified Buffer对数据格式没有要求。
解决存储单元的访问冲突，提升读写性能
当多个操作尝试同时访问Unified Buffer同一个bank或者bank group时，可能会发生bank冲突，包括读写冲突、写写冲突、读读冲突，这种冲突会导致访问排队，降低性能。可以通过优化bank分配的方式来提升读写性能，具体信息请参考避免UB的bank冲突章节。
## 搬运单元
搬运时的对齐要求
由于搬运后的数据用于参与数据计算，因此对搬运数据大小有要求，搬运到Unified Buffer的数据大小需要按照DataBlock对齐，其余存储单元的数据搬运必须按分形要求进行搬运。例如，数据从L1 Buffer搬运到L0A Buffer时，数据格式需要从NZ转换为ZZ格式，搬运数据的大小要按分形大小对齐，如果L1 Buffer的剩余大小不足1个分形，则硬件执行中会出现异常。
## 同步控制
核内同步
由于AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的方式运行，在读写Local Memory（如Unified Buffer）时可能存在数据依赖关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。
