---
type: Guide
title: SGLang Diffusion RainFusion：空间重排、块选择与批次边界
description: 说明8×8空间重排、128块TopK估计、首帧密集保护，以及当前仅取首batch选择索引的限制。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/attention/backends/rain_fusion_attn.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/layers/attention/backends/laser_attn.py
  role: implementation
created_at: '2026-11-08T12:26:53Z'
updated_at: '2026-11-09T04:32:54Z'
platforms: []
---

# SGLang Diffusion RainFusion：空间重排、块选择与批次边界

## 场景和步骤

RainFusion依赖attentions并支持32/64/96/128 head_dim。metadata给latent最后三维与patch，各轴整除后计算空间几何；skip_first_steps内调用LASER。稀疏阶段以128块平均池化Q/K估计分数，选择ceil(num_blocks*(1-sparsity))阈值，分数并列可保留更多块；首帧行列始终dense。

token按空间8×8块重排，attention后逆重排；当前可用范围应限定为 hq、wq 均能被8整除的空间形状。非整齐分支虽特殊保留首帧和余量，但宽度余量在正向追加到末尾，逆向却先恢复原始高宽再切余量，不能保证原token位置恢复；例如 latent_shape=(2,8,9) 的尾列会被分散。宽度非8整除须修复并验证可逆性后才能启用，其他余量组合也需单独核对。此步骤改善空间相邻性，但产生索引、copy及估计开销，不能仅按剩余FLOPs预测端到端收益。

## 当前实现边界

选择索引从mask[0]构造，不能据此宣称每个batch都独立得到最优稀疏模式。TND调用中的长度列表按源码为每batch同seqlen；接入多batch前需核对扩展该参数语义，不能自行替换成另一个FA接口的累计边界规则。仅一条NPU调用不构成任意batch安全证明。

用相同seed比较LASER、稀疏输出质量，对非8整齐空间先做重排/逆重排一致性的拒绝或修复验证，再覆盖首帧、padding、不同batch的条件；记录实际密度与copy时间。未证实多batch语义时采用已核对单batch或恢复dense后端。本次未执行验证，不能将稀疏估计当作无损替代。
