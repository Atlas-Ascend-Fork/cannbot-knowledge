---
type: Guide
title: GLM-5 在旧 CANN8.5 镜像的部署与 MTP 边界
description: 记录旧 GLM-5 的A2/A3镜像、A3单机W4A8/双机BF16及未测PD，不替代GLM5.1后续教程。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/GLM-5.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms:
- a2
- a3
---

# GLM-5 在旧 CANN8.5 镜像的部署与 MTP 边界

## 范围与先决条件

旧页面给A3和910B/A2的CANN8.5 GLM5专用镜像，并要求更新当时Transformers main；没有固定Transformers commit，因此不构成可复现的完整版本锁。a2仅有镜像入口，部署资源与性能没有同等完整证明。此GLM-5不能替代GLM-5.1/5.2/5.3。

页面链接W4A8 checkpoint明确不含MTP。A3单节点使用TP16、chunk16384/max-prefill280000、静态比例0.7、DeepEP auto、旧graph-bs16；虽设置SPEC_V2/overlap/multistream环境，却没有speculative-algorithm，不能声称MTP已启用。BF16要求至少两台A3，示例TP32、max-prefill131072、graph max16并禁用Radix。

多节点脚本注释要求业务网卡，实际却仍把HCCL/Gloo设lo；跨节点必须以真实互联核对，不能照抄lo。容器设备映射还存在davinci1目标路径拼写错误，应按主机设备节点验证。页面对PD明确写未测试，不得扩展为已验证PD支持或吞吐收益。

迁移到当前安装组时逐项核对独立kernel、Transformers、graph参数与权重描述，先功能/质量再性能。本次没有运行旧镜像或模型。相关[当前GLM5.1配方](sglang_ascend_doc_glm_5_1.md)和[安装版本组](../../deployment/sglang_ascend/sglang_ascend_doc_installation_version_sets.md)保留不同阶段证据。

## Evidence

- [sgl_docs：docs/hardware-platforms/ascend-npus/GLM-5.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/GLM-5.mdx)（primary）
