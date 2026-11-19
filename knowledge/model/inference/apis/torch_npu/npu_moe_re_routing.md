---
type: API
title: AlltoAll 后按专家重排 Token（torch_npu.npu_moe_re_routing）
description: torch_npu.npu_moe_re_routing：AlltoAll 后按专家重排 Token。MoE网络中，进行AlltoAll操作从其他卡上拿到需要算的token后，将token按照专家顺序重新排列。 说明按 rank/expert 计数重排 token、gather 索引及只支持 count 的发布版边界。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_re_routing.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_re_routing.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_re_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_re_routing.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeReRoutingOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeReRoutingOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_re_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_re_routing.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_re_routing.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T03:38:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
aliases:
- torch_npu.npu_moe_re_routing
---


# npu_moe_re_routing：AllToAll 后的专家重排与 scale 同步

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_re_routing(tokens, expert_token_num_per_rank, *, per_token_scales=None, expert_token_num_type=1, idx_type=0) -> (Tensor, Tensor, Tensor, Tensor)
```

将 AllToAll 收到的 token 从按来源 rank 排列改为按本地专家排列。返回重排 token、同步重排的 pertoken scale、permute_token_idx、expert_token_num。没有输入 per_token_scales 时，第二项输出无效。

## 参数与组合限制

tokens 为 ND、二维 (A,H)、FP16/BF16/INT8，0<H<16384；expert_token_num_per_rank 为 (N,E) 的 INT32/INT64，来源要求元素大于 0且总和等于 A，不能从其他路由接口的空组支持推导此处允许零计数。可选 per_token_scales 为 FP32(A,)。发布文档只支持 expert_token_num_type=1（count）和 idx_type=0（gather），尽管参数说明列举了其他模式的名称，也不能据此使用。

## 验证与模型关联

标记每个来源 rank/专家的 token 和 scale，检查重排后两者仍一一对应，并用返回索引恢复原顺序；对计数和 A 不一致的配置在调用前拒绝。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L465)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [专家并行中的阶段与通信选择](../../concepts/parallelism/expert_parallel.md)

## 完整公式与参考测试的实际边界

发布与主线公开均只列A2/A3推理、图模式；本算子重排已收到的token，本身不执行AlltoAll。主线流程图以dispatch_v2、重排、FFN、combine_v2说明位置，不表示所有分发后端都必须额外执行这一步。count模式1、gather模式0、正计数且总和等于A的契约继续保留。

发布图片与主线双语公式完全对应，但SrcOffset和DstOffset都是对同一矩形范围的双重求和，交换求和次序后相同，不能完整描述rank顺序与expert顺序的两个缓冲区前缀偏移。主线测试golden_calc只复制输入、生成恒等索引并取首rank计数；部分用例只检查shape，生成的多rank计数也不保证总和等于token数。因此这些公式、参考或测试名称均不能作为已验证的多rank寻址金标准。

两版包装在per_token_scales缺失时仍分配FP32(A,)输出，值没有有效性保证；Meta也只分配形状，不把它写成None或全1。两个固定C++另有Byte scale按E8M0解释的路径，而公开scale仍仅FP32，不据代码分支增加公开支持。

## 主线新增类型标记与公开范围

主线schema/C++另加公开原型遗漏的tokens_dtype=None，仅接受HiFloat8及两种FP4标记；FP4用UINT8物理容器并保持输入物理shape。主线GE对FP4先把物理尾长乘2、Bitcast到逻辑FP4，计算后再打包回UINT8；发布GE没有该参数。Meta用类型映射但没有同样的枚举校验，不能由Meta通过推定覆盖类型有效。

主线测试装饰器虽出现950，HiF8比较却依赖上述恒等参考，FP4主要检查shape；idx_type列表[0,1]又被更短zip截为仅0。本卡不据未执行的测试源码扩充950或scatter模式产品支持，也不把类型Bitcast当作数值量化。

## 已有 OpPlugin 7.3.0 文档与版本边界

### AlltoAll 后按专家重排 Token：torch_npu.npu_moe_re_routing

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE网络中，进行AlltoAll操作从其他卡上拿到需要算的token后，将token按照专家顺序重新排列。

### 文档签名

```text
torch_npu.npu_moe_re_routing(tokens, expert_token_num_per_rank, *, per_token_scales=None, expert_token_num_type=1, idx_type=0) -> (Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_re_routing.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_re_routing.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_re_routing.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_re_routing.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeReRoutingOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeReRoutingOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_re_routing.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_re_routing.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_re_routing.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
