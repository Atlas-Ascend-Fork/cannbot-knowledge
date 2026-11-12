---
type: Guide
title: SGLang昇腾命令生成器：卡数、容器与验证徽标
description: 说明A3双die和950单设备计数、NPU挂载，以及生成器状态和CPU字符串测试不能代替运行验证。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/_deployment.jsx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/_playground.jsx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/scripts/tests/diffusion-builders.test.mjs
  role: constraint
created_at: '2026-11-08T12:33:42Z'
updated_at: '2026-11-08T12:33:42Z'
platforms:
- a3
- '950'
---

# SGLang昇腾命令生成器：卡数、容器与验证徽标

## 设备数与运行环境

公共生成器catalog将A3一节点表示为8卡/16 die，每个die一个/dev/davinciN；950PR/DT一节点8卡/8设备。docker的npuDevices分别16和8，TP的实际值仍由模型recipe决定，不能以节点设备数自动覆盖所有模型的TP。_playground也使用同样的NPU设备枚举。

NPU Docker分支使用--device列表、davinci_manager、hisi_hdc并挂载driver/firmware、ascend_install.info、queue_schedule等Host资源，区别于NVIDIA --gpus all。生成的容器骨架只组织资源，不安装缺失的CANN/custom op，也不保证任意image兼容。

## 验证状态语义

cell.verificationStatus覆盖verified布尔值，未知状态安全地显示unverified；in-progress表示最终验证进行中。match维度决定选哪一格，overlay只叠加参数，隐藏选择需重新落到有效项。生成器能够输出命令、resource字段命名verifiedRecipes、页面其他硬件存在测量，均不是该NPU格已经运行的证据。

diffusion-builders.test.mjs只断言字符串/配置：例如A3八设备Wan生成TP2/SP4/LASER，ZImage双设备生成TP2，以及A2 FLUX2双设备TP2；本次没执行这些测试，测试本身也不加载模型。使用时先确认精确格、全部overlay、设备数与验证状态，再按服务、质量、性能三层验收。
