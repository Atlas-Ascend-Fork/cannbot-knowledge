---
type: Guide
title: SGLang融合算子的NPU平台分派与能力元数据
description: 区分forward_npu平台组合与forward_torch_npu内核来源、自动选择的capabilities守卫、强制后端和PrivateUse1注册生命周期。
tags:
- task.implementation
- topic.architecture
- topic.implementation.operator_registration
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/fused_op.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/kernels/spec.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/utils/custom_op.py
  role: implementation
created_at: '2026-11-08T12:10:30Z'
updated_at: '2026-11-09T04:33:52Z'
platforms: []
aliases:
- BaseFusedOp
- forward_torch_npu
- PrivateUse1
---

# SGLang融合算子的NPU平台分派与能力元数据

BaseFusedOp区分KernelBackend来源与平台：forward_torch_npu属于torch_npu后端，forward_npu属于NPU平台组合路径，二者不能互换。除TORCH_COMPILE外，其他优化后端自动选择需方法真正override且在capabilities声明；TORCH_COMPILE只须显式列入priority，便直接加入候选，不检查override或capabilities，可继承默认forward_torch_compile对forward_native做torch.compile。capability集合是OR，空集合表示无设备限制，CUDA架构边界只用于CUDA，不用于推断昇腾型号。

正常自动分派先处理OOT覆盖，再按priority找合格内核，再forward_npu，最终forward_native。NPU平台不自动回退forward_cuda；只有HIP定义HIP→CUDA链。forward_native的存在不证明所有native算子都获NPU性能验收。TORCH_COMPILE不在默认自动priority，以免服务进程意外触发编译。

静态分派首次调用缓存；override backend_eligible的算子按每次输入重新挑选。显式每调用backend直接调用指定实现并严格失败，不保证经过自动能力过滤；全局调试强制后端仅在NotImplementedError时告警回普通分派。available_backends是结构枚举，auto_selected_backend只是静态元数据观察，不能单独作为shape/dtype支持表。

direct_register_custom_op在NPU用PrivateUse1实现，按mutates_args推导schema，可注册fake实现；Library对象需活到算子使用结束。已存在同名符号时跳过，故多引擎避免重复注册并不证明旧符号签名/实现与新版本一致。扩展算子应实现相应forward方法并保留公共forward的分派机制。

验收记录实际选中实现、设备、shape/dtype、能力表、图模式与fake/mutation合同；分别覆盖自动/显式/全局强制及多引擎。新NPU适配不能仅增加枚举或import后就宣称可用。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
