---
type: Guide
title: SGLang Ascend 安装：分平台组件版本组与历史文档差异
description: 对齐A3/950的CANN9.1.0组件组、Python3.12、TorchNPU、MemFabric和NPU Kernel，保留旧A2/A3
  CANN8.5说明的边界，并定义服务与PD验收入口。
tags:
- task.implementation
- topic.compilation
- topic.model_serving
- topic.parallelism
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/SGLang%20installation%20with%20NPUs%20support.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/getting-started/installation.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/getting-started/quick_start.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/glossary.mdx
  role: supporting
created_at: '2026-11-08T11:40:32Z'
updated_at: '2026-11-09T04:30:33Z'
platforms:
- a2
- a3
- '950'
aliases:
- SGLang NPU installation
- SGLang Ascend version mapping
---

# SGLang Ascend 安装：分平台组件版本组与历史文档差异

## 版本组与适用范围

SGLang 组件须按同一个 CANN 版本组配套，不能把两个文档快照中的单个最新版组合在一起。这里的“新版”指 sglang 固定提交中的文档，“旧版”指独立 sgl-docs 固定提交，不表示本次对任一二进制组合做过运行验证。

| 项目 | 旧 sgl-docs 安装说明 | sglang 当前安装说明 |
| --- | --- | --- |
| 明确展示的硬件 | A2、A3 | A3、950PR/DT |
| Python | 仅3.11 | CANN9.1.0组要求3.12 |
| HDK | 25.3.RC1 | 25.5.2 |
| CANN组件表 | 8.5.0 | 9.1.0；Toolkit、Kernels、NNAL同组 |
| torch / torchvision | 2.8.0 / 0.23.0 | 2.10.0 / 0.25.0 |
| torch_npu | 命令为2.8.0；组件表另称Pytorch Adapter7.3.0 | 2.10.0.post6 |
| MemFabric-Hybrid | 1.0.5 | 1.2.1，按cp312和CPU架构选wheel |
| memcache_hybrid | 未在旧表列出 | 1.2.1 |
| Triton-Ascend | 表为3.2.0、安装命令未锁版本，另装Bisheng20251121 | 3.2.2，按cp312和CPU架构选wheel |
| sgl-kernel-npu | 表中未锁定版本 | 2026.9.0.post9 |
| MemFabric-zbal | 未列出 | A3表列1.1.3，正文限定aarch64集群额外安装 |

旧正文另写 CANN Toolkit/Kernels/NNAL 至少8.3.RC2，这比同页8.5.0组件表宽；本卡保留这个差异，不据此宣称所有更高CANN均兼容。当前安装页没有重新给出A2的9.1.0整套方案，不能把旧A2示例自动升级到当前版本组。

## 安装路径和设备专属包

预配Docker镜像适合部署；源码安装适合修改和核对依赖。当前页中的`cann9.1.0-a3-B105`和`cann9.1.0-950-B105`被来源明确称为validated build，不是stable release；daily标签也不能视为固定二进制版本。知识证据绑定的是页面提交，并未获取镜像digest或外部依赖清单。

源码安装依次准备匹配Python、CANN、PyTorch/torch_npu、Triton及所需Kernel；将`python/pyproject_npu.toml`用作项目配置后安装`python[all_npu]`。来源要求`setuptools<80`以保留pkg_resources，并列出libGL等系统依赖。DeepEP只在MoE EP选择`--moe-a2a-backend deepep`时需要，纯TP不因框架安装而必须启用。

950的Gemma类归一化路径必须安装包含`sgl_kernel_npu.norm.gemma_rmsnorm`的950专属release包，或按来源的950目标构建；A2/A3 wheel不可替代。模块能导入是第一步，不是目标模型前向已经正确。Kernel库自身的两种构建入口与包身份见[构建指南](/model/inference/guides/integration/sgl_kernel_npu/sgl_build_and_install.md)。

MemFabric用于PD KV传输。新页要求除安装Hybrid wheel外运行设备专属kernel安装，950用`--soc-version A5`、A3用`A3`；命令里的A5是该工具参数，知识库平台ID仍为950。旧MemFabric1.0.5流程不能证明与新kernel安装机制等价。

## 服务、容器和PD边界

A3示例映射16个逻辑davinci设备，950示例映射8个；旧A2示例只映射0–7。这里是文档场景的设备配置，不能仅按设备数量识别所有产品。模型权重须在容器可见，CPU架构和Python ABI须与wheel一致；镜像本身至少预留30GB，权重空间另算。

混部直接向服务端口发送请求；跨节点混部只向node-rank0入口发送。PD需要独立Prefill、Decode和router，所有进程设置可互达且一致的`ASCEND_MF_STORE_URL`，router的Prefill bootstrap端口须与P端相同。950示例额外设置`ASCEND_USE_FIA=1`，PD协议为`device_urma`；旧A2在RDMA场景示例使用`device_rdma`，不能跨平台照搬。

多模态示例除`--attention-backend ascend`外，还选择`--mm-attention-backend ascend_attn`和适用模型开关。系统调优建议包括CPU performance模式、关闭NUMA自动平衡、较低swappiness和CPU affinity；它们是上游部署设置，收益与回退需按实际主机基线验收，本次没有修改主机设置。

## 验证和失效条件

先核对组件版本、目标设备与NPU基本张量计算，再检查Kernel模块导入和启动日志。服务就绪后向对应混部/路由入口检查`/health`、`/generate`和`/v1/chat/completions`；多模态请求还需图片可访问。简单问答成功只证明请求链路，不替代模型精度与性能测试。

版本混装、错误平台wheel、容器设备或权重路径缺失、PD store不可达、bootstrap不一致、未安装router包均会使完整流程失效。切换版本应保留原环境/镜像用于回退，而非仅更新一项依赖。本次只阅读两个固定Git来源，未下载或执行依赖、镜像、安装脚本、构建、模型推理、精度评测或性能测试。

## Evidence

- [sgl_docs 安装说明](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/SGLang%20installation%20with%20NPUs%20support.mdx)（primary）
- [sglang 安装说明](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/getting-started/installation.mdx)（primary）


## 快速启动与资源计数

快速启动页使用CANN9.1 A3 B105验证镜像和Qwen/Qwen2.5-7B-Instruct，先确认容器设备、权重可见和health/generate/chat端口可达；该示例模型的HTTP成功只证明基础链路，不能证明大模型精度、长序列容量或吞吐。运行不同硬件须按匹配镜像和实际设备节点设置，不从示例的16个davinci映射推导任意主机有16设备。

术语页把A3示例物理卡与die数区分（8物理卡、16die，每die64GB），950例子为8device；命令TP rank应按进程可见逻辑设备计数，不能把页中“NPU/core”宽泛用词当AI Core个数。模型教程给出的物理卡数、TP和节点数仍需逐条核对，尤其旧A2标题与实际TP不一致的配方。


- [sglang：docs/docs/hardware-platforms/ascend-npus/getting-started/quick_start.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/getting-started/quick_start.mdx)（supporting）
- [sglang：docs/docs/hardware-platforms/ascend-npus/reference/glossary.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/reference/glossary.mdx)（supporting）
