---
type: Guide
title: 950 Inductor 矩阵乘调优：候选实现、Catlass 与 Epilogue
description: 区分编译模式和 GEMM 候选库，明确 Catlass 路径、算子列表、融合和测量的启用条件。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE_GEMM_BACKENDS.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_NPU_CATLASS_DIR.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_CATLASS_ENABLED_OPS.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/CATLASS_EPILOGUE_FUSION.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_PROFILE_WITH_DO_BENCH_USING_PROFILING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/CATLASS_EPILOGUE_FUSION.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_CATLASS_ENABLED_OPS.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE_GEMM_BACKENDS.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_NPU_CATLASS_DIR.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_PROFILE_WITH_DO_BENCH_USING_PROFILING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/CATLASS_EPILOGUE_FUSION.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_CATLASS_ENABLED_OPS.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_MAX_AUTOTUNE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_MAX_AUTOTUNE_GEMM_BACKENDS.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_NPU_CATLASS_DIR.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_PROFILE_WITH_DO_BENCH_USING_PROFILING.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/FASTAUTOTUNE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/triton_cv/overview.md
  role: primary
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# 950 Inductor 矩阵乘调优：候选实现、Catlass 与 Epilogue

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## 编译模式与候选实现分开选

TORCHINDUCTOR_NPU_BACKEND 默认 default 为 Triton，可选 dvm、ascendc；它在首次 torch.compile 前设置即可，后端惰性加载。Ascend C 模式要求 PyTorch≥2.9。该变量不等于 GEMM 候选实现名单。

TORCHINDUCTOR_MAX_AUTOTUNE 默认 0，1 增加候选调优和编译时间。TORCHINDUCTOR_MAX_AUTOTUNE_GEMM_BACKENDS 仅此时生效，默认 ATEN,TRITON,CPP，但 CPP 面向 CPU，NPU 实际为 ATen 与 Triton。名称大小写不敏感、逗号分隔，不用空格分隔；CATLASS 是额外候选，需要有效模板库路径。

## Catlass 生效检查

TORCHINDUCTOR_NPU_CATLASS_DIR 在 import torch_npu 前指定有效模板库；未设尝试 torch 安装旁 third_party/catlass，不存在则不加载；无效路径告警并跳过，不影响其他候选调优。需要同时 max-autotune=1 且候选名单包含 CATLASS，不能只提供目录。

TORCHINDUCTOR_CATLASS_ENABLED_OPS 默认 mm,addmm,bmm，可加入 grouped_mm；ALL 表示全部已支持矩阵乘，空字符串表示全部关闭。逗号分隔、大小写不敏感，不能由 ALL 推导任何新算子均被支持。

CATLASS_EPILOGUE_FUSION 默认 0，1 可尝试把 bias/activation 等融合到 matmul，仍依赖模板库和 max-autotune。配置候选库不表示最终一定选中它，须核对实际编译和执行。

## 测量成本

TORCHINDUCTOR_PROFILE_WITH_DO_BENCH_USING_PROFILING 默认 0 为事件计时，1 在 max-autotune 中用 profiling 测量，增加调优开销。INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE 默认 0，1 开启 batch profiler，不等同于启用所有候选库。除后端选择的惰性读取例外外，相关环境配置按来源在导入前完成。

本卡聚焦这些 Catlass/调优页共同声明的 950；不把通用后端页的 A2/A3 支持扩展到 Catlass 子能力。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## Catlass与CUTLASS对照保留库和默认值差别

中英文对照页把MAX_AUTOTUNE、MAX_AUTOTUNE_GEMM_BACKENDS和PROFILE_WITH_DO_BENCH_USING_PROFILING列同名配置；不把同名变成跨平台候选库相同的证明。CATLASS_EPILOGUE_FUSION对照CUTLASS_EPILOGUE_FUSION，均默认0；TORCHINDUCTOR_CATLASS_ENABLED_OPS默认mm,addmm,bmm，而对照的CUTLASS_ENABLED_OPS默认all。NPU_CATLASS_DIR指Catlass模板库，CUTLASS_DIR指CUDA的CUTLASS库，两个目录和库不互换。

## 内置特性页的产品表和自动Tiling范围

同提交torch_npu/_inductor/docs下的六份Catlass环境页明确列Ascend950PR及950DT；公开环境目录中较窄的950DT表保留为其本页范围，不能说所有来源只支持DT，也不由六页的范围扩大其他CostModel、Pass或精度检查能力。内部目录页把Catlass路径默认写为空字符串，公开页及config属性说明另有未设时尝试默认目录的路径，分别按所指读取层次核对。

自动Tiling概述面向950PR/DT及PyTorch2.9示例，区别核间切分（每核数据量/逻辑核数）与核内SubBlock搬运粒度。候选可能很多，先以启发式缩小集合，再编译和实测、缓存选定配置；单Kernel内预编译线程和多个Kernel编译进程是两层并发。文本的10–50%收益描述没有本模型或本次测量依据，不当作收益保证；其中GPU/CUTLASS/C++通用例子也不说明NPU执行了相同后端。

FASTAUTOTUNE默认0、1启用，特性页列950PR/DT；AGGRESSIVE_AUTOTUNE默认0、1启用batch profiler，其特性页另列A2/A3推理系列及950PR/DT。后者的范围只用于这个开关，不扩大整张Catlass卡到A2/A3。首编译成本、候选数量、最终kernel与稳态时延分别评估，源码FASTAUTOTUNE分支的待核对行为仍见配置草稿。

## 从候选日志确认真实产物

内部Catlass概述的FP32样例先设allow_hf32=True，调优(512×256)与(256×1024)的mm+SiLU，日志中catlass_gemm_*是不同配置、mm表示AclNN候选。只有实际选中后，output_code.py中的async_compile.catlass及catlass_fused_silu等名称才说明生成了对应融合；日志出现候选不等于最终使用。示例里的0.0083ms、预编译/benchmark秒数及AtlasA5模板名是历史样例，不是本地结果或默认Tiling。

Triton CV页则展示(200×256)与(256×256)、FP16、B为列优先stride的mm，日志区分persistent_mm与普通triton_mm，示例共462候选、预编译和benchmark分别耗时。其说明文字误复用了Catlass的512×256形状，环境段文字称ATen+Catlass但示例只设TRITON；最小代码还缺os/_t/TestUtils等完整上下文，不能当可直接运行脚本。生成片段只有aten.mm，不据标题“CV融合”证明本例已融合SiLU/ReLU。

Triton页产品表列950DT，生成代码的DeviceProperties却含950PR样例标识；保留产品表与样例身份两层，不据样例扩成所有PR可用。两页生成代码中的模板、stage、tile和指针ABI属于特定产物及Kernel生产细节，不作为本范围的通用开发配方；只摄取模型调用、候选/实际路径与诊断含义，未编译或调用任何产物。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE_GEMM_BACKENDS.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_NPU_CATLASS_DIR.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_CATLASS_ENABLED_OPS.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/CATLASS_EPILOGUE_FUSION.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/TORCHINDUCTOR_PROFILE_WITH_DO_BENCH_USING_PROFILING.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/CATLASS_EPILOGUE_FUSION.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_CATLASS_ENABLED_OPS.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_MAX_AUTOTUNE_GEMM_BACKENDS.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_NPU_BACKEND.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_NPU_CATLASS_DIR.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/TORCHINDUCTOR_PROFILE_WITH_DO_BENCH_USING_PROFILING.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/CATLASS_EPILOGUE_FUSION.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_CATLASS_ENABLED_OPS.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_MAX_AUTOTUNE.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_MAX_AUTOTUNE_GEMM_BACKENDS.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_NPU_CATLASS_DIR.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/TORCHINDUCTOR_PROFILE_WITH_DO_BENCH_USING_PROFILING.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/FASTAUTOTUNE.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/tiling/INDUCTOR_ASCEND_AGGRESSIVE_AUTOTUNE.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/catlass/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/triton_cv/overview.md)（primary）
