---
type: API
title: MoE 分组门控与 TopK 专家选择（torch_npu.npu_moe_gating_top_k）
description: torch_npu.npu_moe_gating_top_k：MoE 分组门控与 TopK 专家选择。MoE计算中，对输入x做Sigmoid/SoftMax计算，对计算结果分组进行排序，最后根据分组排序的结果选取前k个专家。 说明分组与Hash选专家、选择bias和权重分离，并限定发布与主线的归一化、输出和平台差异。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_gating_top_k.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeGatingTopKKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeGatingTopKKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_moe_gating_top_k.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_moe_gating_top_k.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_gating_top_k_backward.py
  role: example
created_at: '2026-11-10T03:38:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_moe_gating_top_k
---


# npu_moe_gating_top_k：分组、Hash与归一化范围

## 版本与范围

发布分组TopK依据ascend_26_0_pt28；主线新增950PR及DT、Hash及归一化扩展按独立固定快照记录，主线配套尚未确认。

## 接口与语义

以下是固定来源的接口声明：

```text
npu_moe_gating_top_k(x, k, *, bias=None, k_group=1, group_count=1, group_select_mode=0, renorm=0, norm_type=0, out_flag=False, routed_scaling_factor=1.0, eps=1e-20) -> (Tensor, Tensor, Tensor)
```

对二维路由输入做 Softmax(norm_type=0) 或 Sigmoid(1)，可用 bias 影响专家选择，再按组分数选 k_group 个组、在选定组内取 K 个专家。返回 (yOut,expertIdxOut,normOut)，yOut 与专家索引为 (N,K)；normOut 仅在 out_flag=True 时有意义，类型 FP32、shape 同 x。

## 参数与组合限制

- x 为二维 ND、FP16/BF16/FP32，专家数 E≤2048，支持非连续；bias 可选、同 dtype、一维长度 E。
- 发布要求group_count>0且整除E，每组专家数必须大于2；每组向上按 32 对齐后再乘 group_count 仍须≤2048。
- 1≤k_group≤group_count，1≤K≤(E/group_count)*k_group。group_select_mode=0 按组内最大值选组，1 按组内 Top2 之和选组；renorm 在此版本只支持 0。
- 来源等价逻辑使用加 bias 后的分数选择专家，却从未加 bias 的 norm 结果取权重；Sigmoid 路线再按所选权重之和和 eps 归一化，最后乘 routed_scaling_factor。不要把选择偏置直接加入最终权重。
- 不同模型的分组规则、norm_type、缩放系数均需按模型定义传入，不能由同为 MoE 推定相同。

## 验证与模型关联

构造能区分组内 max 和 Top2-sum 的样例，分别检查选择 ID、未加 bias 的权重、Sigmoid 归一化和 FP32 normOut；不要仅比较专家个数。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L361)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [专家并行中的阶段与通信选择](../../concepts/parallelism/expert_parallel.md)

## 主线Hash模式与分组约束差异

发布A2/A3范围与旧参数继续适用；主线中英文新增950PR及DT，schema、C++和GE Converter新增input_ids与tid2eid。它们必须同时存在或同时缺省：input_ids为INT32/INT64的(N,)，tid2eid为INT32/INT64的(numKeys,K)。专家索引由tid2eid[input_ids]取得，跳过分组TopK选择；仍从归一化结果取出相应专家权重，再按norm_type/renorm和缩放因子处理。Hash不等于跳过权重计算，也不把bias加入最终权重。

主线C++核对成对性、维数、batch与K，并分别检查两个索引dtype，没有在此扫描input_ids值或映射中的专家ID。不能把包装通过视为所有索引有效；需要0≤input_ids<numKeys、专家ID在有效专家范围。仅提供一个输入会在C++、Meta和两个主线GE注册入口被拒绝。Hash直调aclnnMoeGatingTopKV2，没有符号能力回退；普通TopK仍调旧aclnnMoeGatingTopK。

公开组选择限制仍包括E≤2048、G>0且整除E、1≤k_group≤G、1≤K≤(E/G)*k_group，以及每组向上按32对齐后乘G≤2048。发布与主线英文要求每组专家数>2；主线中文改为>group_select_mode，存在语言差异，不能无说明地合成更宽约束。Hash跳过排序的算法说明没有逐项声明取消所有产品限制。

## 主线归一化类型按产品与语言限定

| 主线中文norm_type | 权重规则与范围 |
| --- | --- |
| 0 | 全专家Softmax；renorm=1才对选中权重再归一化 |
| 1 | Sigmoid；始终按选中权重之和加eps归一化，renorm不改变它 |
| 2 | SqrtSoftplus；始终再归一化；A2/A3要求group_count=1，950PR/DT无此专属限制 |
| 3 | Sigmoid，由renorm控制是否再归一化；仅950PR/DT |

上述扩展来自主线中文，不追溯到发布版仅norm_type=0/1、renorm=0的契约。主线英文仍把A2/A3列为0/1、950列为0/1/2，部分总说明还把0/1的函数名称颠倒，参考程序也停留在旧版。因此norm_type=2的A2/A3和950的3属于明确的同提交语言冲突，按来源分别记录，使用前需确认实际配套。

选择始终使用加bias的分数，权重从未加bias的norm结果Gather。主线中文参考修正bias=None与group_count=1的分支，并增加Hash、SqrtSoftplus和renorm规则；旧发布与主线英文参考无条件bias.numpy、在G=1时仍访问只在G>1赋值的group_x，不能直接照抄为通用程序。

## 可选输出、公式与内部反向

两固定C++和Meta无论out_flag如何，都分配完整(N,E)的FP32第三Tensor。out_flag=False时不保证其中的值有效，不能读作完整norm、None或零元素输出。公开公式图把加bias结果命名normOut，并写无条件归一化；静态参考却从未加bias结果取权重且按norm_type决定归一化。这6张不同公式图在发布中文与主线英文中各出现一次，已目视核对，不把图中简式当作所有模式的完整算法。

主线新增生成式backward：输出shape沿用x_norm、dtype沿用grad_y，调用aclnnMoeGatingTopKBackward；自动求导声明只有y可微，保存第三norm输出与专家索引供x梯度使用，未声明bias梯度。这是内部实现事实，公开页仍仅推理，也没有因此自动把out_flag改True；不能据反向声明保证False时保存的norm数值有效或扩充训练支持。

唯一主线反向测试入口为A2 BF16组合且标记Temporarily skipping，未证明950、新norm/Hash或完整自动求导路径。标为CPU FP64的参考在Sigmoid内部仍调用float()，也不能仅据变量名认定全部参考计算为FP64。本次未运行上游、设备测试或新增verified。

两个版本分别提供npu与npu_inference命名空间的GE注册；主线GE MoeGatingTopK的固定IR已接收两个Hash输入。它与Eager Hash ACLNN名称不同，不能仅按是否含V2后缀判断图支持。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE 分组门控与 TopK 专家选择：torch_npu.npu_moe_gating_top_k

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE计算中，对输入x做Sigmoid/SoftMax计算，对计算结果分组进行排序，最后根据分组排序的结果选取前k个专家。

### 文档签名

```text
npu_moe_gating_top_k(x, k, *, bias=None, k_group=1, group_count=1, group_select_mode=0, renorm=0, norm_type=0, out_flag=False, routed_scaling_factor=1.0, eps=1e-20) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_gating_top_k.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_gating_top_k.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeGatingTopKKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeGatingTopKKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_contrib/custom_torch_ops/npu_moe_gating_top_k.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_gating_top_k.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_contrib/custom_torch_ops/npu_moe_gating_top_k.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_gating_top_k_backward.py)（example）
