---
type: Guide
title: SGLang MindSpore模型实现复用Torch HCCL的启动边界
description: 说明NPU专用MindSpore runner的rank与端口环境、PYNATIVE O0初始化和现有Torch组handle复用，区分通信接入与全模型支持。
tags:
- task.implementation
- topic.parallelism
- topic.architecture
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/mindspore_runner.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/model_runner.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/validation_hook.py
  role: supporting
created_at: '2026-11-08T12:10:31Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
aliases:
- reuse_hccl_comm
- init_ms_distributed
---

# SGLang MindSpore模型实现复用Torch HCCL的启动边界

参数校验要求model_impl=mindspore仅NPU；ModelRunner按TP×PP计算world_size，rank=TP×pp_rank+tp_rank，local_rank=gpu_id。此runner模块当前主要完成通信初始化，不是任意PyTorch模型自动转换器，模型实现/加载器必须另行支持。

从dist_init_addr或host:port构建rendezvous，_get_host_and_ip用冒号拆分，不能据此宣称支持任意IPv6形式。MindSpore调度端口在原端口<65500时加35，否则减35，需另行保证不占用。未预设MS_ROLE时rank0起MS_SCHED子进程，其余环境设MS_WORKER、DEVICE_ID、MS_WORKER_NUM和MS_NODE_ID；已有MS_ROLE时不重写这套环境。

初始化设置infer_boost=on、jit_level=O0、PYNATIVE_MODE、Ascend设备，再ms.communication.init(hccl)。之后遍历Torch已建立的_groups，从ProcessGroupHCCL取本地rank的comm handle，经GroupOptions.hccl_config传给MindSpore create_group复用。私有_get_backend/get_hccl_comm和内部GroupOptions属于版本敏感接口，不能认为换TorchNPU/MindSpore版本仍自动兼容。

验收先核对双方rank、local可见设备和端口，再比对组成员/handle与少量collective，最终验证具体模型输出、图模式和吞吐。调度子进程退出管理与通信复用不等于模型权重或KV共享；失败恢复应先定位阶段：_get_host_and_ip 可在环境设置和通信初始化前报错，修正地址后应按尚未产生的状态处理；来源未定义所有失败均需重启双方。若已启动调度子进程或建立通信组，应核对这些已创建资源再决定清理/重启方案，其恢复步骤仍需在实际环境验证。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
