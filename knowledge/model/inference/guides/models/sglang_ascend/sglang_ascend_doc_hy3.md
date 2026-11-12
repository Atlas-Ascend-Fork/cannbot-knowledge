---
type: Guide
title: Hy3 在 A3 的 BF16 单节点服务与推理模式
description: 记录 Hy3 的 A3 TP16 容量起点、EAGLE/graph 组合和按请求选择 reasoning_effort 的边界。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/hy3.mdx
  role: primary
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-08T11:58:59Z'
platforms:
- a3
---

# Hy3 在 A3 的 BF16 单节点服务与推理模式

## 适用范围

来源对象为295B总参数、21B激活的 Hy3 MoE，使用GQA并带MTP。BF16权重约597.60GB；教程以一台A3、TP16、16×64GB die为部署起点，镜像为CANN9.1 `a3-B105`验证构建。该计数和命令不证明A2、950或更少设备的容量与功能。

## 服务配置

混部示例启用ascend attention、BF16、TP16、静态内存比例0.84，prefill/max-running requests均40。decode graph batch为4/8/16/20/24/28/32/36/40；EAGLE为steps2/topk1/draft3。其环境包括FIA、32 streams、HCCL buffer3000、AIV扩展、overlap plan stream；这些是成组配方，不能从开关名称推断每项独立收益。单节点lo网卡设置也不能照搬到跨节点部署。

请求用chat_template_kwargs中的reasoning_effort选择`no_think`、`low`或`high`，服务端reasoning/tool parser均为auto。`no_think`直接答复；`high`可返回reasoning_content和content，max_tokens应覆盖思考与回答预算。改变思考模式会改变生成工作量，不能把更短输出的延迟变化当算子加速。

来源没有独立best-practice页或性能数字；HTTP200和简单问答只是连通/功能信号。应另测目标长上下文、工具调用与实际生成质量，不能将页面中的宣传性模型比较视作本地验证。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/hy3.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/tutorials/hy3.mdx)（primary）
