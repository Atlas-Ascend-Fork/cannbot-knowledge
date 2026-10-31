---
type: Concept
title: MoE Dispatch / Combine v2：按模型选择通信与量化
description: 更新当前各模型MC2门控、独立组、950量化与fullmesh用法，撤回Gemma旧回退和固定搜索计数。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/hccl_utils.py
  role: implementation
created_at: '2026-05-31T00:00:00Z'
updated_at: '2026-10-29T14:57:06Z'
platforms:
- a2
- a3
- '950'
---

# MoE Dispatch / Combine v2：按模型选择通信与量化

## 两算子之间仍有专家计算

npu_moe_distribute_dispatch_v2完成分发、接收和专家重排，产出expand_x、scale、assist_info_for_combine、expert_token_num和EP/TP接收计数；GMM计算专家后，combine_v2复用assist及接收计数做逆向归并与routing权重合流。它不同于Prefill的init-routing→AllToAll→re-routing→GMM→逆向AllToAll→finalize多算子链。

当前常见入口如下，不能只凭通用算子名推断模型开关：

| 模型 | 当前路径 |
| --- | --- |
| R1/V3.2/GLM/Kimi | 纯EP Decode走MC2，Prefill走DR；moeTP分支另行处理 |
| Qwen3.5 | enable_decode_moe_dispatch_combine_v2且非Prefill、EP>1、moeTP1；当前使用独立moe_ep_group_mc2，不再直接取普通EP组 |
| Gemma4 | EP Decode当前只走MC2，旧local_experts切换已删除；Prefill为DR |
| LongCat-Lite | 当前A2每rank专家>24时自动回退DR，其他纯EP按模型开关选择；MC2配置已包含fullmesh_v2和copy_expert_num |

## 独立通信组、量化和平台

R1等当前调用通过CommManager的moe_ep_group_mc2取得HCCL名，与普通EP集合通信分组。是否注册、实际是否消费、buffer如何计算必须分别检查，不能用一份固定“只有6处”仓库搜索计数替代契约。

Qwen3.5的950 MXFP8分支dispatch量化mode4、y_dtype=float8_e4m3fn，scale重排后给GMM，combine comm_quant_mode同为4；非量化分支0。非950设置fullmesh_v2，950不设置。V4也按平台/实际gmm_quant_mode选择dispatch模式和dtype，当前A4W4有专门分支，不能用“所有950 combine固定mode4”概括。

Lite/Gemma当前代码也显式设置fullmesh_v2。Lite同时传identity专家copy_expert_num，旧文档“fullmesh_v2绝对不支持零专家”的概括不能再作为当前仓通用限制；实际算子包兼容仍需按模型验证。Lite独立组buffer计算却传is_full_mesh_v2=False，不能由comm_alg字符串自行替换预算公式。

HCCL_BUFFSIZE不足时按真实提示调整并保持各rank一致；AIV是否有利取决于阶段与负载。Prefill微批文档建议SDMA以避免争Vector；量化精度评测还需核对可能的不确定性。旧Hy3报告的CANN8.5 shared_expert_x/SuperKernel失败不作为当前软件组合的普遍禁令。

## 验收

检查选中的模型分支、通信组、专家数、dtype/scale、assist映射及实际packet布局；覆盖不同batch、零token/专家负载与末尾请求。只有实测能确认减少下发或通信后的净收益。本次未执行NPU算子。共享分支同步见[MoE多流](moe_multi_stream.md)，Prefill链见[Double Routing](double_routing.md)。


## Evidence

- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（primary）
- [modeling_qwen3_5_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_5/models/modeling_qwen3_5_moe.py)（implementation）
- [modeling_gemma4.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py)（implementation）
- [modeling_longcat_flash_lite.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py)（implementation）
- [hccl_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/hccl_utils.py)（implementation）
