---
type: Guide
title: SGLang NPU IPC重建的TP rank映射补丁
description: 说明NPU multiprocessing重建为何改写设备索引、register_sgl_tp_rank的前置条件和固定第六索引的版本脆弱性。
tags:
- task.implementation
- topic.implementation.cross_process
- topic.parallelism
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/utils/patch_torch.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/utils/serialization.py
  role: supporting
created_at: '2026-11-08T11:53:40Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
aliases:
- register_sgl_tp_rank
- monkey_patch_torch_reductions
---

# SGLang NPU IPC重建的TP rank映射补丁

monkey_patch_torch_reductions按is_npu分支处理。CUDA路径把设备号转换UUID并在目标可见设备中找回；NPU路径因源码注释的HDK UUID限制，仅包住torch_npu.multiprocessing.reductions.rebuild_npu_tensor，不使用CUDA的UUID回查算法。

NPU重建包装先改写args索引6的设备号为SGLANG_TP_RANK，再调用保存的原始重建函数。必须先register_sgl_tp_rank，缺失时断言；传入旧device参数不会参与真正的新设备选择。此处是固定版本的进程内TP映射，不是任意进程、跨节点物理卡UUID自动发现。

以_rebuild_npu_tensor_original属性判幂等；参数位置常量6依赖上游reduce/rebuild签名，升级torch_npu需重新核对。重复初始化不同rank或不同可见设备环境后，不能依赖先前全局状态自动适配。

先记录worker可见设备列表、local/TP rank和IPC来源，再验证少量Tensor的设备、数值和所有权；同时覆盖未注册rank和重复patch。不把反序列化成功当成分布式通信已就绪。回退补丁需新进程与配套TorchNPU环境。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
