---
type: Guide
title: SGLang 昇腾自定义算子的集成与版本对齐
description: 区分 Ascend C torch op 和 Triton Python 调用，记录 schema、workspace、包版本与设备测试边界。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/development/operator_development.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# SGLang 昇腾自定义算子的集成与版本对齐

## 两类集成入口

来源将sgl-kernel-npu分成Ascend C共享库torch op和Triton Python kernel。前者经过Host验证/tiling/launch与Device计算，再在PyTorch注册；后者通过Python直接import。这里只提炼公开开发工作流，没有闭合任何Device执行图，也没有由helloworld示例推导产品支持，因此draft空平台。

Ascend C集成需同步Host/Device源、声明、schema、PrivateUse1实现绑定与CMake来源列表；mutating输出用Tensor(a!)、optional用Tensor?并在实现处理。工作区需求决定相应编译组/HAVE_WORKSPACE与HAVE_TILING，不可把示例“无需workspace”泛化到复杂算子。入口名会影响生成的aclrtlaunch头文件；上游保留的KernalHelloworld/sgl_kenel等拼写不能凭习惯改名后继续假设链接成立。

教程使用torch.ops.npu命名示例；实际接口必须与安装的sgl-kernel-npu固定版本注册相符，不能只凭文档断言符号存在。Triton算子也须核对具体导出函数和NPU编译适配，而不是把GPU kernel原样import。已有[算子注册机制](../../../concepts/kernels/sgl_operator_registry.md)提供更细源码证据。

## 生命周期与版本配套

sgl-kernel-npu与SGLang是独立包。先完成kernel变更、单元测试与版本发布，再更新SGLang使用的依赖与调用。贡献页指出docker/npu.Dockerfile的SGLANG_KERNEL_NPU_TAG，而算子页要求pyproject依赖；这是不同消费入口，升级时需分别核对实际构建版本，不只改其中一处就宣称所有镜像对齐。文档给出的发布频率和自动发布叙述不是本次已发生的发布事件。

单元验证需比较PyTorch参考结果，覆盖非整齐shape、BF16/FP16、in-place输出与必要边界；只通过2048元素示例不能证明尾块、别名或workspace安全。再到SGLang服务测模型正确性与性能。CANN编译、库导入、torch schema可调用和模型质量分别是不同证据。本次未执行任何编译、安装、测试或上游贡献命令。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/development/operator_development.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/development/operator_development.mdx)（primary）
