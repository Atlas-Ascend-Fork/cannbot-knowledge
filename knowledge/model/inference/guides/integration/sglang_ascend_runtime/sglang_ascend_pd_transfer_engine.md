---
type: Guide
title: SGLang Ascend PD传输引擎的协议回退与注册失败口径
description: 说明MemFabric TransferEngine的P/D角色、store和session端点、device_rdma预热、协议枚举回退及batch_register只记录失败。
tags:
- task.implementation
- topic.kv_cache
- topic.data_movement.communication.collective_communication
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/ascend/transfer_engine.py
  role: primary
created_at: '2026-11-08T11:53:42Z'
updated_at: '2026-11-08T11:53:42Z'
platforms: []
aliases:
- AscendTransferEngine
- ASCEND_MF_TRANSFER_PROTOCOL
---

# SGLang Ascend PD传输引擎的协议回退与注册失败口径

AscendTransferEngine包装memfabric_hybrid.TransferEngine而不是Mooncake原生engine，虽然继承MooncakeTransferEngine。包缺失会在构造时重新抛导入错误；只接受Prefill或Decode角色。ASCEND_MF_STORE_URL提供集中store，hostname与RPC端口组成session_id；初始化前端口为0时，成功后重新取端口并更新session，不能先缓存0端点发布给peer。

ASCEND_MF_TRANSFER_PROTOCOL去空白转小写，未设置默认sdma。仅显式protocol字符串等于device_rdma时，在engine初始化前用world device group做all_gather预热HCCL，避免RDMA初始化冲突；大小依运行时launch_world_size。未知协议若安装的TransDataOpType没有对应大写枚举，则告警并回SDMA，不是硬失败；旧文档里的device_urma等名是否可用取决于实际安装包。

engine.initialize接store_url/session_id/role/npu_id/op_type，非0直接RuntimeError。batch_register捕获异常或非0结果后仅debug记录，没有把失败状态抛出或返回给调用方；所以构造成功、调用注册函数返回None均不证明每段内存已经可远端访问。

实施时核对P/D store可达一致、角色、设备绑定、真实RPC端点和实际协议；再用小块实际传输、返回码与对端数据校验确认注册。协议回退会改变性能与网络路径，须在日志/基准中记录。此实现与[HIXL概念](/model/inference/concepts/techniques/hixl.md)和另一个Recipes封装不是相同参数合同。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
