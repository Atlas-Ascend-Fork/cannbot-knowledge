---
type: Guide
title: SGLang NPU容器构建配方的版本、设备与依赖边界
description: 固定当前Dockerfile的CANN9.1/PTA2.10/内核2026.11组合、A3与950的MemFabric/ZBAL区别及all_npu不安装硬件运行时的事实。
tags:
- task.implementation
- topic.compilation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docker/npu.Dockerfile
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/pyproject_npu.toml
  role: implementation
created_at: '2026-11-08T12:10:40Z'
updated_at: '2026-11-09T04:33:25Z'
platforms:
- a3
- '950'
---

# SGLang NPU容器构建配方的版本、设备与依赖边界

当前Dockerfile默认CANN9.1.0、950、Ubuntu22.04、Python3.12；Torch2.10.0与torch_npu2.10.0.post6匹配，torchvision0.25.0/torchaudio2.10.0。sgl-kernel-npu制品标签2026.11.0.post1，custom-ops、ops-transformer 和 sgl-kernel-npu 的发布 ZIP 名称按 Torch、CANN、设备与架构选择；内部 custom_ops wheel 名为 custom_ops-1.0-cp312-cp312-linux_$(arch).whl，不含 Torch/CANN/设备标识，仍须依据配套发布来源核对兼容性。不能仅升级一个wheel并复用其他制品。

MemFabric/MemCache均1.3.0，mfcli kernel install把950映射A5、a3映射A3，其他设备显式失败；ZBAL的950为1.2.21004.post1，A3为1.1.3。Triton-Ascend3.2.2区分arm64/amd64制品，其他TARGETARCH失败。此处950映射A5是该工具参数，不等于知识库平台名可任意替换。

容器先装CPU Torch wheel再PTA，安装NPU pyproject并source CANN、custom vendor及ATB环境。pyproject的srt_npu是空extra，all_npu只增加diffusion依赖，不自动安装torch_npu/CANN/内核包。文件要求Python>=3.11而此容器为3.12，两者不可当所有ABI wheel通用。

配方含SGLANG_TAG=main、未固定的普通依赖及默认latest的ModelScope/EvalScope，固定Dockerfile源码不能使整次构建完全可重现；arm64下载链接还有时效。知识摄取没有执行构建或下载这些制品。复现需保存镜像digest、实际源码commit、完整依赖与所有构建参数，模型专属旧教程版本应整组使用，不能拼接新版容器默认。
