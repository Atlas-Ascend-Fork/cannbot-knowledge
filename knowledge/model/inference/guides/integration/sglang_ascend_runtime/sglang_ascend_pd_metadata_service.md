---
type: Guide
title: SGLang Ascend PD元数据驻留、配置服务与启动职责
description: 说明PD输出元数据在NPU的D2D路径、int64 bootstrap标识、固定行宽，以及node0配置存储与HTTP bootstrap的不同职责。
tags:
- task.implementation
- topic.model_serving
- topic.parallelism
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/utils.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/managers/disagg_service.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/disaggregation/common/conn.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/unit/disaggregation/test_disaggregation_wire.py
  role: evidence
created_at: '2026-11-08T12:07:26Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
aliases:
- MetadataBuffers
- ASCEND_MF_STORE_URL
---

# SGLang Ascend PD元数据驻留、配置服务与启动职责

MetadataBuffers在NPU时把首输出token、logprob、hidden state等元数据分配在NPU，由D2D通道搬运；其他平台默认CPU的经验不能直接套用。bootstrap_room由uint64改为int64以绕过当前NPU uint64限制，checksum复用同dtype/device。output_ids等16个int32构成64B行，满足源码注明的最小RDMA粒度；top_logprobs宽度默认128，不能据注释TODO断言更大值已拒绝或支持。

customized_info容量必须非负，为0不分配；sampling mask按环境开关分配，DSA topk按正维度分配并以-1填充。元数据须满足 CommonKVManager.validate_aux_buffers 的容量兼容校验，不能只验证KV主buffer。启用 customized-info 传输时，两个 customized-info 槽位的行字节数必须相等，对应其他缓冲允许源行字节数小于或等于目标，不能要求所有dtype/hidden宽度严格相同；缓冲列表还兼容单侧可选的64B checksum。源码测试定义了 Prefill hidden_size=16/float32 与 Decode hidden_size=128/float16 的接受案例（本次未运行），允许 Decode 单侧推测配置；未启用 customized-info 且对端未给行长时该校验直接返回，不能视为布局已验证。bootstrap_room用于检测元数据错配，不是全KV内容校验的替代。

get_kv_class按ASCEND选择manager/sender/receiver/bootstrap类。服务入口在Prefill启HTTP bootstrap；启用PD role switch时其他非null角色也预先启动，以免切换时重建，同行实例需不同bootstrap端口。MemFabric配置存储仅node_rank0且ASCEND后端调用create_config_store(ASCEND_MF_STORE_URL)，异常导致启动失败。HTTP房间注册与MemFabric配置存储不同，两个地址/端口都需核对。

Rust server能替代CommonKVBootstrapServer子类的HTTP注册时仍需单独创建Ascend配置存储；不能因为省略Python HTTP服务就省略MemFabric store。验收记录P/D版本、rank、URL、元数据schema、KV布局和首token转移，验证role switch及错误地址；服务可达不证明数据已正确恢复。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
