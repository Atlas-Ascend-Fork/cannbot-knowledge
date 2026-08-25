---
type: Guide
title: Matmul开启AtomicAdd选项
description: 【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/matrix_compute/matmul_atomic_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Matmul开启AtomicAdd选项

【优先级】中
【描述】__对于Matmul得到的结果矩阵C(m, n)，若后续需要和GM上的矩阵D(m, n)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。
【反例】
将Matmul的结果矩阵C和GM上的矩阵D分别搬到UB上，做完Add操作后，结果再搬出到GM。这样至少要多分配一块UB内存给矩阵D，假设在分离架构的处理器上执行，将多做三次搬运操作（矩阵C从GM搬到UB、矩阵D从GM搬到UB、Add结果从UB搬出到GM）。
【正例】
计算Matmul结果时，调用IterateAll接口或者GetTensorC接口搬运到矩阵D的GM地址上，同时将接口中enAtomic参数设为1，搬出到GM时，Matmul结果矩阵C会累加到矩阵D上，从而得到两个矩阵Add后的结果。
【性能对比】
以矩阵维度M=64，N=256，K=256，矩阵D为(64, 256)为例，Matmul开启AtomicAdd选项前后的性能对比如上图所示，平均cycle数从开启AtomicAdd选项前的154181变为开启后的135054，性能优化12.4%。因此在这种场景下，开启AtomicAdd选项能获取更优的性能。

<!-- cannbot:related:start -->
## 相关

- [AscAtomicAdd](../../../../apis/simd_api/c_api/scalar_compute/asc_atomic_add.md)（`explains`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“AscAtomicAdd”定义：对Global Memory中的数据执行原子加操作，将val累加到address指向的数据元素上，返回修改前的值。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
- [AtomicAdd](../../../../apis/simd_api/basic_api/atomic_operations/atomic_add.md)（`explains`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“AtomicAdd”定义：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
- [SetAtomicAdd](../../../../apis/simd_api/basic_api/atomic_operations/set_atomic_add.md)（`explains`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“SetAtomicAdd”定义：对后续搬运到GM的数据开启原子累加，将拷贝内容与GM已有值求和后写入。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
- [SetSplitK](../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/set_split_k.md)（`explains`）：SetSplitK 与《Matmul开启AtomicAdd选项》的实质衔接是：SplitK 必须与 multi-core split、split range、single range/shape、core 数和 AtomicAdd 汇合配置一致。
- [通过BT Buffer实现高效的bias计算](bt_buffer_bias_compute.md)（`related`）：焦点处理BT Buffer 承载 Matmul Bias 以减少搬运和等待；Matmul开启AtomicAdd选项正文说明“【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩”。候选是 Bias 计算的可替换暂存/累加路径或减少 AIC/AIV 等待的直接优化。
- [通过L0C Buffer数据暂存实现高效的矩阵乘结果累加](l0c_buffer_matmul_accumulate.md)（`related`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“通过L0C Buffer数据暂存实现高效的矩阵乘结果累加”定义：【描述】算子实现中对矩阵乘的结果进行累加时（比如矩阵A1 \ B1 + A2 \ B2...结果的累加），可将前一次矩阵乘的结果暂存在L0C Buffer（CO1）上，调用Mmad接口实现矩阵乘结果累加。相比于每次矩阵乘的结果从L0C Buffer（CO1）搬运到GM上，再搬运到UB上进行累加计算，可减少数据搬运的次数，提升内存使用效率。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
<!-- cannbot:related:end -->
