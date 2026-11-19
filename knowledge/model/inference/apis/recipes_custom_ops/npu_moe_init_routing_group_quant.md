---
type: API
title: custom.npu_moe_init_routing_group_quant：950 分组 FP8 路由
description: 聚焦 quant_mode 4/5 和固定 128 分组，说明显式专家范围、四返回及包装层形状差异。
tags:
- task.lookup
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_moe_init_routing_group_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_moe_init_routing_group_quant.cpp
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp
  role: header
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py
  role: constraint
created_at: '2026-11-09T02:45:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# custom.npu_moe_init_routing_group_quant：950 分组 FP8 路由

## 来源与交付范围

依据 Recipes 固定提交 `944d2d3ece86f7df33dbb0cb155c72ca619a9c66` 的独立接口文档、Schema 与 PyTorch 包装层。该接口在 `torch.ops.custom` 注册；安装并导入对应 custom_ops 包后才可能挂到 torch_npu，不能据同名前缀认定为标准 TorchNPU/OpPlugin 内置接口。来源的产品支持和软件配套分别核对；这不是 `ascend_26_0_pt28` 标准包已内置该接口的声明。

## 接口

```text
custom.npu_moe_init_routing_group_quant(Tensor x, Tensor expert_idx, Tensor? scale=None, Tensor? offset=None, int active_num=-1, int expert_capacity=-1, int expert_num=-1, int drop_pad_mode=-1, int expert_tokens_num_type=-1, bool expert_tokens_num_flag=False, int quant_mode=-1, SymInt[] active_expert_range, int row_idx_type=-1, int group_size=128) ->(Tensor, Tensor, Tensor, Tensor)
```

## 本卡覆盖路径

产品表确认 950PR/950DT。选择 dropless、quant_mode=4/5 的 PerGroup FP8 路线，group_size 固定 128；不把通用 MoE InitRouting v2 的限制视作本接口限制，也不推广到 A3。

输入 x=(N,H)，expert_idx 为 INT32(N,K)。显式设置 active_num=N*K、drop_pad_mode=0、expert_tokens_num_flag=True、expert_tokens_num_type=1(count)、row_idx_type=1，并传具体两元素 active_expert_range=[0,expert_num]；避免照抄签名中的 -1/False 默认值。expert_capacity 文档称当前未使用，仍需满足对应校验，不能据默认值省略其合法性检查。

## 返回和量化布局

返回 (expanded_x,expanded_row_idx,expert_tokens_count_or_cumsum,expanded_scale)。quant_mode=4 输出 E5M2，=5 输出 E4M3FN；该路径 expanded_x=(N*K,H)，expanded_scale 为 FP32(N*K,ceil(H/128))。scatter 索引中无效部分未初始化，只读取实际活跃元素，不把所有 N*K 位置都视为有效路由。

专家统计 type=1 表示逐专家 count，不按参数表中“累计”一词改为 cumsum。若改为 key_value/type=2，包装层分配 (expert_num,2)，而 count 用 active range 长度；本卡不提供子范围 key/value 拼接配方。

## 文档与包装层边界

- 文档要求 active_num=N*K，包装层却按 active_num 截断分配；本卡遵循文档约束，不能仅依据 min 分配逻辑宣称任意裁剪可用。
- 空 active_expert_range 在包装层用于部分输出形状推导，但调用底层时仍传原数组；因此本卡要求显式范围，不依赖“空等于全范围”的一致性。
- MXFP8 quant_mode=2/3 的包装层 scale 为 E8M0、shape=(rows,ceil(ceil(H/32)/2),2)，与参数表笼统 FLOAT32 描述不同；不能复用本卡 mode4/5 的 scale 布局。静态/动态 INT8 和不量化分支需分别核验。

核对 count 总数、路由索引回映射、每组 FP8 scale 和有效 token 前缀；与排序后逐专家处理参考比较。


## 验证边界

核对自定义 .so、Schema、PrivateUse1/Meta 注册及所用图后端，分别比较输出、原地行为和多次调用。仅完成文档和包装层静态审阅；未分析完整 Device Kernel/Host/Tiling，未加载 .so、执行上游代码或进行设备数值和性能验证。

- [自定义算子交付与图适配](../../guides/integration/torchair/custom_operator_graph_contract.md)
- [软件栈基线](../../concepts/frameworks/ascend_software_stack_baselines.md)

## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/docs/custom-npu_moe_init_routing_group_quant.md)（primary）
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/npu_moe_init_routing_group_quant.cpp)（implementation）
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/csrc/ops_def_registration.cpp)（header）
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/ascendc/torch_ops_extension/custom_ops/__init__.py)（constraint）
