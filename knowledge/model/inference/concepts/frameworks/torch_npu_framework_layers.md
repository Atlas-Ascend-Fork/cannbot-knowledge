---
type: Concept
title: TorchNPU框架层次：设备适配、执行路径与扩展依赖
description: 区分PyTorch分发、TorchNPU设备资源、CANN执行和外部扩展，限定架构图及生态能力概述的含义。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/product_overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/product_overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/libraries.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/libraries.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.zh.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/architecture.svg
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/architecture.svg
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/initialization_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/initialization_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/eager_mode_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/eager_mode_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/graph_mode_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/graph_mode_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/tensor_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/tensor_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CONTRIBUTING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CONTRIBUTING.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/overview.md
  role: constraint
created_at: '2026-11-09T16:42:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU框架层次：设备适配、执行路径与扩展依赖

## 固定来源与支持层次

固定PyTorch/TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的双语README、产品概述、软件库和配套页。本卡限定已列A2/A3系列与950DT，不扩为950PR，也不由框架总览推定每个算子/模式都支持这些产品。主线候选未形成已验证配套，不能回推26.0/PyTorch2.8。

## 层次和数据路径

模型调用PyTorch Core的nn/autograd/optimizer/DataLoader及Dispatcher；TorchNPU通过PrivateUse1设备适配，将NPU接口、Tensor/内存、算子下发、通信和图后端接入框架。Python包建立用户入口，torch_npu._C提供C++核心；底层使用CANN ACL运行时、算子库、GE及HCCL，设备硬件和互联仍有独立约束。架构图把基础计算、分布式、图模式、调试调优列为功能域，下方Core承担算子/设备适配、资源和混合精度。

| 路径 | 图中表达与使用边界 |
| --- | --- |
| Eager | Python→算子调用/Dispatcher→TorchNPU适配→ACL/Host任务队列→设备执行。概述图不是所有同步/队列配置的精确实现时序；右侧“返回Host”不能理解为每次自动把Tensor搬CPU或等待设备完成。 |
| Graph | Dynamo捕获FX，选Inductor/NPUGraphs/NPUGraph_EX等后端，再编译/捕获并执行；不是每个后端都做同样融合、训练与缓存。“一次下发”不保证整段含graph break的Python只启动一次Kernel。 |
| Tensor | 参数/输入按需从Host到HBM，中间结果在Device传递，输出按业务需要回Host；不要求每步往返，也不解除异步拷贝、跨流依赖和内存寿命。 |

概述的“只改.cuda为.npu”“承载全部框架特性”是设备适配方向，不是全API/所有dtype/生态库的兼容保证。OOM自动快照、Swap、跨流复用等也各受配置与具体实现限制；不能仅凭总览启用或假定默认开启。

## 初始化图与设备初始化

两语言初始化图给出六阶段：C扩展加载；日志/Profiler/Rendezvous、CANN库与算子注册等核心模块加载；设备、ProcessGroupHCCL、Dynamo与RPC注册；按monkey→api→distributed→dynamo→profiler→npu→warning→asd应用patch；注册屏障/Shutdown钩子；可选运行特性。它是该文档的依赖说明，不证明所有条件分支均执行，也不把导入注册等同CANN设备已初始化。自动加载、懒初始化及探针边界见[初始化指南](../../guides/optimization/torch_npu/torch_npu_initialization_and_device_detection.md)。

## 扩展库分别承担什么

| 库 | 本页说明与版本边界 |
| --- | --- |
| TorchAir | FX到GE的图编译/执行扩展，软件库页写PyTorch>=2.6、TorchNPU master；它不是所有后端必须的独立最新包，也不替代精确gitlink和配套表。 |
| OpPlugin | 将PyTorch算子接到昇腾算子库，可做框架算子适配；master是文档入口，实际基线固定子模块提交，C++ extensions是另一适配方式。 |
| HyperParallel | 本页介绍1.1.0、PyTorch>=2.6；以shard_module/parallelize_module注入并行/重计算/Offload，fully_shard与HSDPModule处理全/混合分片；列TP/EP/CP/PP及混合并行。只摄取此页依赖角色，未摄取外部库API实现、配置或性能保证。 |
| AKG | 软件库页写PyTorch>=2.7.1、TorchNPU master，以MLIR为Inductor提供算子生成/缓存/加载能力；外部AKG仓未纳入三仓范围，不能用该最低值替代逐后端的安装/硬件约束。 |
| Triton-Ascend | 两语言列A2/A3；英文另写latest和PyTorch2.7.1/2.9，中文仅TorchNPU master，没有同样版本短名单。保留差异，不据该表扩大950或否定新版内部特性页。 |

库介绍的“减少显存/提升吞吐”等是来源能力说明，不是本卡的测量结论。MindSpeed、veRL和外部插件链接不构成其内容在本卡范围内的证据；本卡未导入或执行上游。

- [版本与来源身份](ascend_software_stack_baselines.md)
- [模型迁移最小验收](../../../training/guides/torch_npu_mnist_migration_acceptance.md)

## 仓内目录与对外接口边界

主线双语CONTRIBUTING把torch_npu/csrc、npu、distributed、profiler、dynamo、_inductor、_afd及torchnpugen等列为实现/生成层目录。目录存在、C扩展可导入、测试收录或二进制导出符号都不单独构成公开稳定接口契约；适配开发与模型调用分别按相应文档约束。

两固定提交的安全声明要求公开接口同时符合公开约定且有文档展示；意外暴露接口可能改变/删除。正式接口以Python为主，**Libtorch场景为例外**；二进制包内部动态库符号不是直接对外服务承诺。因此实现证据可解释Python行为，不把_C内部函数、任意dlsym符号或未声明的C++入口提升为稳定用户API。已正式说明的[C++生命周期](../../apis/torch_npu/libtorch_npu_lifecycle.md)和[扩展编译](../../guides/optimization/torch_npu/torch_npu_native_extension_backend_scope.md)各按自身范围消费。

贡献指南中的目录/构建/测试描述仅补充职责说明，SIG/CLA/提交/云端代码检查及PR流程属于上游治理，不作为模型优化配方。安全声明的公网地址表是依赖/下载链接清单，不表示外部仓库、数据文件、FlameGraph脚本或最新在线文档已经摄取或执行。

## OpPlugin总览的公开契约与beta状态

两固定OpPlugin总览说明用monkey-patch替换部分PyTorch入口；“默认支持版本匹配的全量PyTorch版本”限定于该TorchNPU发行所匹配的PyTorch范围，单接口约束可以收窄，不是任意主线提交或跨版本组合兼容。发布总览列2.7.1/2.8/2.9/2.10，主线所列版本随自身总览消费，不能反向改写发布配套。

总览仍笼统称正式对外只有Python、C++为内部不建议使用；它没有消除安全声明的Libtorch例外，也不抹去已明确公布的C++生命周期/部署/稳定ABI入口。以具体场景文档共同限定，不将所有导出符号一并认作公开契约。

beta指上游实验接口，可能有异常、参数或名称变更、移除；知识卡的stable是知识生命周期，不承诺这个API已脱离beta。公开约定、上游beta/废弃状态、版本配套与运行验证分别记录。总览外指的公开API规范和环境变量页面不由链接自动算作完整摄取。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/product_overview.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/product_overview.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/libraries.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/libraries.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.zh.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/README.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/COMPATIBILITY.en.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/architecture.svg)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/architecture.svg)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/initialization_flow.png)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/initialization_flow.png)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/eager_mode_flow.png)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/eager_mode_flow.png)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/graph_mode_flow.png)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/graph_mode_flow.png)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/tensor_flow.png)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/tensor_flow.png)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CONTRIBUTING.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/CONTRIBUTING.en.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md)（primary）

- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md)（constraint）

- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/overview.md)（primary）

- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/overview.md)（constraint）

- [固定来源 26](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/overview.md)（constraint）
