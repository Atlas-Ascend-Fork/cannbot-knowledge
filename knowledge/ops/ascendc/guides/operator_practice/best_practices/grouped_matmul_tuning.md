---
type: Guide
title: GroupedMatmul算子性能调优案例
description: 本案例对分组Matmul即GroupedMatmul算子的per-token量化场景进行性能分析和优化，GroupedMatmul算子计算过程（通过python代码表达）为：
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/grouped_matmul_tuning.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# GroupedMatmul算子性能调优案例

## 案例介绍
本案例对分组Matmul即GroupedMatmul算子的per-token量化场景进行性能分析和优化，GroupedMatmul算子计算过程（通过python代码表达）为：
验证平台为Atlas A2 训练系列产品/Atlas A2 推理系列产品。
优化分析以如下算子规格为例：
算子规格
主要介绍以下优化方法：
-   对于Vector计算占比较高（Vector Bound）的场景，将AI Core中的AIC核和AIV核启动比例设置为1:2；
-   优化CV并行流水，减少Cube和Vector计算间的空闲等待时间；
-   优化Vector计算流水，提高Vector并行计算速度。
## 获取性能数据
固定8核测试，即当前性能和后续优化tiling中numBlocks固定设置为8。
通过msOpProf算子调优工具获取算子性能数据：
-   获取真实环境执行的性能数据（指令的cycle占比数据ArithmeticUtilization.csv），包含各个流水的占比情况；
-   获取仿真性能数据（指令流水图），包含各个流水的占用区间，可观察流水间依赖情况，从而优化并行效率。
## 分析主要瓶颈点
固定8核进行测试的情况下，通过msopprof命令获取指令的cycle占比数据如下：
通过msopprof simulator获取到的指令流水图如下图所示：
结合上述两种数据（真实数据和仿真数据）进行性能分析：
-   Vector计算bound，当前为减少核启动开销设置为1:1；
-   实际优化过程中，对上述问题进行优化、Vector计算占比下降后，Cube和Vector计算各自都有间隙，相互之间都有等待耗时；
-   Vector计算没有开启double buffer，计算和数据搬运部分没有并行。
## 设计优化方案
-   将AI Core中的AIC核和AIV核启动比例设置为1:2。每次AIC输出的数据，由两个AIV并行计算对应的反量化和激活函数；在Vector侧代码的循环里，AIV0和AIV1交替进行计算（前提条件，循环次数不为1）。代码示例如下：
-   AIC和AIV启动比例设置为1:2后，出现Cube和Vector计算各自都有间隙、相互之间都有等待耗时的情况。分析原因是因为Vector和Cube计算存在使用一份workspace进行数据传递的场景，通过4份workspace的方案进行优化：host按4倍baseM * baseN申请workspace，Cube侧代码在计算前可以跳过前4轮的等待。
-   Vector计算开启double buffer，InitBuffer指定分配内存块个数为2。
## 验证优化方案性能收益
-   将AI Core中的AIC和AIV启动比例设置为1:2后，执行总耗时从218.1us下降为154.2us。指令流水图显示Cube计算间等待变小。
-   如上图所示，Vector计算已经不处于bound状态，但Cube和Vector计算都有间隙，未被充分利用（上述两个箭头的位置）。
