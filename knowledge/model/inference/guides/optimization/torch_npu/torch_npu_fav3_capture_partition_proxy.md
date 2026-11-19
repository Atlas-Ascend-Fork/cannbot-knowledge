---
type: Guide
title: FAv3捕获分区：TND、dropout与版本条件
description: 解释固定主线default Triton对FAv3前反向的代理改写、CANN 9.1门槛和捕获分区边界，不把unsafe标记当成数值算法变化。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/fav3_partition_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/_proxy_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
created_at: '2026-11-10T12:23:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FAv3捕获分区：TND、dropout与版本条件

## 从默认Triton入口到局部改写

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的FAv3分区Pass、代理注册与加载入口。发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`不含同路径`fx_passes/fav3_partition_pass.py`和`fx_passes/_proxy_ops.py`；这只说明所查路径缺失，不否定发布版其他捕获处理机制。整卡平台未知，保持draft、空平台，未运行上游或设备实验。

`_load_backend()`按后端名字选loader，`default`映射`_load_triton_backend()`。后者先检查配套Triton存在，没有则告警并返回；正常加载路径随后调用`register_fav3_partition_pass()`。因此这是已接到默认Triton加载链的优化处理，不能因文件存在便推广到DVM、Ascend C或任意自定义后端。

注册函数将同一个PatternMatcherPass挂入`POST_GRAD_PATTERNS['fav3_partition']`，并对`post_grad_fusion_options`用setdefault添加空选项；已有用户值保留。模块级规则分别匹配`npu_fusion_attention_v3.default`及`npu_fusion_attention_grad_v3.default`。注册、该阶段被执行、节点匹配和最终分区是不同条件，不能据这次注册认定每张图都已分区。

## 实际条件比“TND都回Eager”窄

规则先要求`torch._inductor.config.triton.cudagraphs`为真，再用normalize_function把参数规范成kwargs；规范失败、input_layout不是Python字符串或keep_prob不是Python int/float时，均不做这次改写。它不是符号keep_prob或未知layout的通用判定器，也没有在此替代API的完整参数验证。

| 选定局部条件 | 是否改写到代理 |
| --- | --- |
| layout转大写后不是TND | 否 |
| TND且keep_prob<1.0 | 是 |
| TND且keep_prob==1.0，模块加载时CANN版本比较结果低于9.1.0 | 是 |
| TND且keep_prob==1.0，比较结果至少9.1.0 | 否 |

所有条件还受前述捕获开关与参数类型检查约束。这里不将“小于1”转写成完整合法概率范围，也不把未命中规则解释为任意shape/dtype都能捕获。

CANN判定在模块级执行`_is_gte_cann_version('9.1.0')`，辅助层默认查询CANN模块并转发到原生版本比较；该布尔结果随后被规则复用，不是每个节点重新检测所有组件版本。升级版本、替换安装或改变捕获配置后的实际加载状态应独立核对，不用驱动版本字符串代替这里的CANN比较。

## 代理保留原算子，改变的是捕获处理信号

命中处理器只把FX节点target换成对应`*_unsafe`代理，不重写节点参数、结果结构或dropout数学表达式。代理从原重载schema生成同签名定义，挂`Tag.cudagraph_unsafe`，CompositeExplicitAutograd实现直接调用原算子；fake实现也委托原算子，以复用原有Meta及混合CPU序列长度/NPU数据的传播逻辑。

该tag是交给上游Inductor捕获分区机制的信号。所选文件的意图是把不适合捕获的FAv3留在Eager区间，周围仍可编译/捕获；上游完整分区消费者不在本卡范围，`graph_partition`配置和代码生成未实测，因此不把tag本身写成“必然完成局部分区”，或说出现代理就整图退回Eager。它也没有将原FAv3替换成另一种Attention算法。

诊断捕获覆盖率时，保留后端/捕获与分区配置、CANN比较结果、FX规范化后的layout和keep_prob，以及前反向target改写前后的图，再核对实际captured与Eager区间、时间线和数值。额外dispatcher跳转与分区边界的成本不能只凭代理名字估计。训练输出/梯度存储仍受[NPUGraph训练代际](../../../../training/guides/torch_npu_npugraph_training_lifecycle.md)等生命周期约束；算子参数与产品支持见[FAv3接口](../../../../training/apis/torch_npu/npu_fusion_attention_v3.md)，不由此局部Pass扩展。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/fav3_partition_pass.py)（primary）：定向范围25–102。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/_proxy_ops.py)（implementation）：定向范围16–66。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）：定向范围179–205, 307–321, 430–436, 455–474。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）：定向范围51–62。
