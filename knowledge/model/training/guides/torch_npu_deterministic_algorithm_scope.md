---
type: Guide
title: 确定性算法范围：产品清单与主线状态冲突
description: 区分 A2/A3 与 950DT 的算子清单、布尔状态和真实下发，不从总览推导统一的一次设置限制。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/deterministic_computing_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/determin_API_list.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUFunctions.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/deterministic_computing_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/determin_API_list.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/determin_API_list.md
  role: constraint
created_at: '2026-11-09T08:47:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 确定性算法范围：产品清单与主线状态冲突

## 固定范围

依据TorchNPU `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 原生确定性清单、OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 自定义算子清单及主线接口/实现。确定性针对相同输入、相同硬件和软件上的相同操作，不能据此承诺跨版本、跨产品或不同算法逐位一致。设置应在实际运行网络/算子的进程内，不能只在不执行网络的父进程设置。

## 按产品选择已列出的算法

A2/A3原生清单涵盖以下类别，符号仅限定该页列出的对应入口：

- 矩阵/向量：dot、matmul、mm、bmm、mv、trace、addmm/Tensor.addmm、addbmm/Tensor.addbmm_、addmv/Tensor.addmv_。
- 规约：cumsum、mean、sum、std/std_mean、var/var_mean。
- 神经网络：functional.batch_norm、layer_norm、embedding、prelu、adaptive_avg_pool2d、avg_pool2d、interpolate、fold、unfold，aten.convolution_backward。
- 损失：functional.binary_cross_entropy、binary_cross_entropy_with_logits、ctc_loss、nll_loss、mse_loss、l1_loss、smooth_l1_loss、kl_div、multilabel_margin_loss、soft_margin_loss，以及nn.NLLLoss2d。
- 索引写回：Tensor.put_、Tensor.index_put、Tensor.index_put_。

950DT原生清单另列Tensor.put_、max_unpool2d/3d、_unique/_unique2、scatter/scatter_、scatter_add/scatter_add_、index_add、index_copy/index_copy_、bincount、Tensor.index_put_、linalg.vector_norm、functional.batch_norm、Tensor.coalesce；还列aten.upsample_bicubic2d/bilinear2d/linear1d及_upsample_bilinear2d_aa/_upsample_bicubic2d_aa反向、functional.adaptive_max_pool3d反向、grid_sampler_2d/3d反向。反向限定不自动扩展到同名所有前向/反向变体。

自定义清单的A2/A3条目为npu_convolution_transpose、npu_linear、npu_deformable_conv2d；950DT条目为npu_scatter_nd_update及其原地版、scatter_update及其原地版、npu_fusion_attention_grad。不要把一个产品的清单并到另一产品，未列接口也不直接等于已经证明不支持确定性。

清单说明可通过torch.use_deterministic_algorithms(True)开启，以torch.are_deterministic_algorithms_enabled()检查布尔配置。查询返回True只证明配置状态，不证明某个Kernel已经选择确定性实现；还需实际下发并观察目标算子。确定性可能降低性能，不能在调优基线间无记录地改变开关。

## 同一提交里的文档与实现冲突

两份总览仍写“同线程只认第一次有效设置，需真正下发一次算子才算有效”。但同一固定主线的set_deterministic_level接口页明确支持动态修改，主线OpParamMaker按状态快照重新应用改变后的effective_level，只有已应用0且仍为0时走线程缓存快速返回。不能把总览这段旧限制推广为全部主线路径的一次设置事实，也不能仅凭实现分支宣称所有异步队列、通信器和已有编译图都已动态切换。

[全局level接口](../apis/torch_npu/set_deterministic_level.md)记录0..3、布尔协调及CANN/算子包门槛；[前后向标记](../apis/torch_npu/deterministic_with_backward.md)依赖Tensor反向链且不支持图；[图内scope](../../inference/guides/optimization/torchair/torchair_core_limits_and_determinism.md)按对应后端处理。三者的状态作用范围不同，不相互替代。

## 验证边界

先固定软件栈、产品、输入、随机状态与通信顺序，在实际计算进程设置，区分Python状态、下发日志及目标Kernel，再比较多次原始输出。对于动态切换，用独立进程基线或明确同步边界验证新任务；不要把尚在执行的旧任务与新配置混作一个样本。[HF32和未初始化内存填充](torch_npu_precision_switches_and_deterministic_fill.md)也需分别核对，确定性开关不替代数值模式和合法输入约束。

本卡仅静态审阅，无设备、训练、跨batch或性能实测；未新增verified事件。

## 根API与HCCL确定性协调

同提交七版本torch页中英文use_deterministic_algorithms/are_deterministic_algorithms_enabled及set/get_deterministic_debug_mode列三产品。同时设置HCCL_DETERMINISTIC与use_deterministic_algorithms时，若前者开启确定性则HCCL接口启用确定性，否则由后者控制HCCL确定性；此处没有给已创建通信器和异步任务的完整动态切换协议。

同页重申TorchNPU默认不执行未初始化内存填充，需显式设fill_uninitialized_memory=True；见[填充API](../apis/torch_npu/fill_uninitialized_memory.md)。英文额外对is_deterministic_algorithms_warn_only_enabled明确三产品均不支持，中文未列，不能用普通enabled查询支持补齐warn_only入口。配置查询、内存填充和具体Kernel确定性分别验收。

## 英文总览不消除实现状态冲突

同提交英文deterministic_computing_apis与中文给出相同的A2/A3及950名单、同进程设置与性能代价，并同样保留“同线程只认首次有效设置”的旧提示。因此双语一致也不能替该提示增加实现证据；上文与主线set_deterministic_level及状态快照实现的冲突仍保留，布尔查询不替代实际下发和Kernel确认。

## 发布版清单与主线清单分开消费

OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文自定义确定性清单仅点名npu_group_norm_swish；主线英文清单与本卡已核对的主线中文一样，按A2/A3列卷积转置、linear、deformable_conv2d，按950DT另列scatter更新与fusion_attention_grad。发布列表不能被主线列表覆盖；主线没有列GroupNorm Swish也不证明它不再需要确定性控制，其接口页另有前向、反向及产品差异。

发布清单同样写同线程首次有效设置和实际算子下发条件；这里保留发布文档口径，不将主线状态快照实现回推发布，也不把该旧总览限制当全部主线路径的唯一行为。两版本都要求设置与计算在同一实际进程，布尔查询仍只确认配置。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/deterministic_computing_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/determin_API_list.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-set_deterministic_level.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUFunctions.cpp)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch.md)（primary）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch.md)（constraint）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/deterministic_computing_apis.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/determin_API_list.md)（primary）

- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/determin_API_list.md)（constraint）
