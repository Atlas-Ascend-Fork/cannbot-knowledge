---
type: Guide
title: SGLang Mooncake Ascend传输协议的显式选择与设备身份
description: 说明ENABLE_ASCEND_TRANSFER_WITH_MOONCAKE如何改写hostname与protocol、物理卡覆盖参数和初始化超时，以及它与MemFabric
  Ascend后端的区别。
tags:
- task.implementation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/distributed/device_communicators/mooncake_transfer_engine.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/environ.py
  role: supporting
created_at: '2026-11-08T12:23:03Z'
updated_at: '2026-11-08T12:23:03Z'
platforms: []
---

# SGLang Mooncake Ascend传输协议的显式选择与设备身份

Mooncake TransferEngine的ENABLE_ASCEND_TRANSFER_WITH_MOONCAKE开启时，hostname追加空闲端口和npu_<id>，id优先ASCEND_NPU_PHY_ID，值-1则用worker gpu_id，并强制protocol=ascend；否则遵循MOONCAKE_PROTOCOL。它不因模型设备为NPU就无条件切Ascend协议。

engine.initialize使用P2PHANDSHAKE、设备名或空字符串，并受SGLANG_DISAGGREGATION_ENGINE_INIT_TIMEOUT deadline限制；非零返回抛RuntimeError。transfer_sync捕获异常转-1，负值debug日志后返回，调用者必须处理返回码，不能以无Python异常当传输成功。

这是Mooncake engine内部的协议适配，与--disaggregation-transfer-backend ascend所用MemFabric AscendTransferEngine不同；两套store/身份/注册与错误处理不可混用。显式物理卡参数也需核对可见设备映射，不能猜测进程local编号总等物理编号。

验收记录实际transfer backend、协议、session hostname、device身份和返回码，先小块再真实P/D KV与输出精度；本文没有验证外部Mooncake Ascend插件版本、芯片覆盖或带宽。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
