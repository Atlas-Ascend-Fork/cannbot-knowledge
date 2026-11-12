---
type: Guide
title: TorchNPU 推理接口选型：功能索引、版本与产品支持
description: torch_npu 官方文档索引的使用边界：按功能区分量化、Attention、MoE 和多流候选，再核对版本、产品、签名、返回与副作用。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/SKILL.md
  role: supporting
created_at: '2026-11-10T03:39:02Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- agnostic
aliases:
- torch_npu 官方文档索引
- TorchNPU 接口选型
- torch_npu API 功能
---

# TorchNPU 推理接口选型：能力、版本与产品支持

## 从能力定位接口

TorchNPU 官方文档索引中的名称用于找到候选，功能说明用于区分候选。先保留准确命名空间和接口名，再结合算子用途筛选；仅在模型代码里出现某名字，不能证明当前重载、dtype 或产品已支持。

量化链应区分三类动作：[npu_anti_quant](../../apis/torch_npu/npu_anti_quant.md)将整数数据按 scale/offset 恢复为浮点；[npu_dynamic_quant_asymmetric](../../apis/torch_npu/npu_dynamic_quant_asymmetric.md)从输入范围生成量化值、scale 和 offset；[npu_trans_quant_param](../../apis/torch_npu/npu_trans_quant_param.md)将 scale 编码成量化矩阵乘使用的整数位域。最后一种不是对浮点 scale 做普通数值类型转换。

Attention 选型还要区分全量/增量、普通/稀疏、QKV/MLA 及量化缓存。[FIA 参数与模型路径](../../concepts/kernels/fused_infer_attention_score.md)和[融合链选择](attention_fusion_chain_selection.md)给出具体消费者。MoE dispatch/combine 需要配对的通信元数据；普通路由、MC2 和带残差归一化的融合 combine 不可只按名字互换，见[并行接入](parallel_groups_and_weight_shards.md)。

## 接口形状、版本和副作用

以目标 torch_npu/op-plugin 版本的函数签名、返回项和约束为依据。本机 docstring 只描述本机安装版本；为另一套软件选择接口时，要读取那一版文档。没有 docstring 不证明接口不可调用；存在 callable 也不证明任意可选参数都可用。固定文档快照与本机运行行为分别记录。

接入时核对参数次序、可选项及返回结构，特别是被替换算子的 dtype、shape、layout 和副作用。函数名相近不表示重载或输出协议相同。

按实际产品支持表筛选，再检查 dtype、layout、维度、空张量和图模式约束。Beta 是接口文档分组，不等同于知识卡 draft；draft/空平台表示本批证据尚未定位产品。旧的 Atlas 产品名称不能未经映射就当成 A2/A3。API 名字出现在官方目录中，也不代替目标版本的产品支持声明。

配套 API 卡保留各自的源表分组、固定版本、产品范围、签名和具体约束；正式或 Beta 分组均不构成跨软件版本的兼容承诺。这些卡片用于固定文档的选型核对，未做 NPU 实测，不代表已在当前模型执行。

[quant_scatter](../../apis/torch_npu/npu_quant_scatter.md)与[quant_scatter_](../../apis/torch_npu/npu_quant_scatter_.md)的原地副作用不同。多流里的 [erase_stream](../../apis/torch_npu/erase_stream.md)用于移除张量生命周期标记，不能代替 Event 等待；这类 API 的旧版支持范围也要单独核对。

## 融合接入与回退

先建立同等语义的非融合参考，再逐项比较形状、数值和状态变化，最后在相同负载下确认真实内核及净收益。索引摘要只能用于候选发现，不提供跨版本签名或通用加速保证。遇到目标 API 缺失、产品范围未知或融合不支持时，保留明确缺口；采用等价回退后须继续验证，不能只凭成功加载宣称目标融合已生效。


## Evidence

- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（primary）
- [固定来源](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/SKILL.md)（supporting）
