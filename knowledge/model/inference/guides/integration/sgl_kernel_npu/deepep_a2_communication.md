---
type: Guide
title: DeepEP A2：单机与跨机通信的缓冲、量化与人工验收
description: 按A2专用来源区分单机/跨机token边界、HCCL缓冲预算、分层通信变量和CI缺口，保留Normal API与配置指南的容量差异。
tags:
- task.implementation
- topic.parallelism
- topic.mixture_of_experts
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/A2_DEEPEP.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/NORMAL_API.md
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md
  role: supporting
created_at: '2026-11-08T11:02:02Z'
updated_at: '2026-11-08T11:02:02Z'
platforms:
- a2
aliases:
- A2 DeepEP
- HCCL_BUFFSIZE
cann_versions:
- 9.0.0
- 9.1.0
---

# DeepEP A2：单机与跨机通信的缓冲、量化与人工验收

## 场景选择与软件配套

A2 专用文档面向 Atlas A2、aarch64/x86，列出驱动 HDK 至少 25.3.RC1、CANN 9.0.0 或 9.1.0 及配套固件。模块总 README 的驱动基线更宽，A2 集成应按这份专项说明核验。`deepep2` 为 A2 构建目标，不能据 wheel 包名在其他芯片复用。

SGLang 的 Prefill 节点建议 `--deepep-mode normal`、Decode 节点 `low_latency`、混合节点 `auto`。单机说明以 ranks=8 为适用条件，ranks<8 不作收益承诺；跨节点说明针对 ranks>8。

| 场景 | Normal 配置指南上限 | Low-Latency 配置指南上限 | 量化边界 |
| --- | --- | --- | --- |
| A2 单机 | bs=8000 | bs=512 | Prefill 可选 INT8 |
| A2 跨机 | bs=4096 | bs=512 | Prefill 禁用 Normal 量化 |

Normal API/layout 文档的 A2 单机输入上限另写 8192，与配置指南的 8000 不同。二者来自同一提交，本页保留差异；不能因为 layout 接受 8192 就把端到端验收上限放宽。长序列同样不能只按环境变量乘积推导总容量。

## HCCL 缓冲预算

A2 仅支持 HCCL 通信域，必须在执行前设置足够的 `HCCL_BUFFSIZE`；默认 200 MB 不是任意形状可用保证。记 b 为每 rank 最大 token 数、R 为 EP ranks、E_local 为本地专家数、K 为 top-k、H 为 hidden：

- 非分层预算：`(b×R×min(E_local,K)×H×2B + 2MB)×2`。
- 分层跨机预算：`num_experts×b×(H×2B + 4×K×4B) + 4MB + 800MB`。

这些为来源给出的场景预算，计算结果转换成环境变量的 MB 数时须统一字节单位，不能把形状乘积直接当 MB。配置指南还分别给出了长序列按每轮 token、非长序列按总 token 的窗口公式，均要求保留额外 padding 空间；不能与上面的分层公式混成一条所有路径通用公式。

## 变量和跨机约束

| 配置 | 作用与限制 |
| --- | --- |
| 取消 `HCCL_OP_EXPANSION_MODE` | A2 DeepEP 专项文档要求禁用，不套用其他模型 AIV 通信配置 |
| `HCCL_INTRA_PCIE_ENABLE=1`、`HCCL_INTRA_ROCE_ENABLE=0` | 分层跨机时 P、D 两侧一致配置 |
| `DEEP_NORMAL_MODE_USE_INT8_QUANT=0` 或未设置 | A2 跨机 Prefill 保持不量化；源码更宽的模式守卫不能扩大支持 |
| `MOE_EXPERT_TOKEN_NUMS_TYPE` | 未设/1 返回每专家 token 计数；0 返回前缀和，消费方必须匹配 |

长序列“蚂蚁搬家”涉及 `DEEPEP_NORMAL_LONG_SEQ_ROUND`、`DEEPEP_NORMAL_LONG_SEQ_PER_ROUND_TOKENS` 和 combine 端开关。README 给出的轮数/每轮 tokens 可配置范围不是 A2 全链路已经支持到该乘积的证据，应先按 Normal API 的具体平台边界核验。

## 验收与当前覆盖缺口

先验证 wheel 导入与 `deep_ep_cpp` 动态库定位，再分开运行来源保留的 `test_intranode.py`、`test_low_latency.py`、`test_normal_and_low_latency.py`；A2 跨机需先配置 `run_test_internode.sh` 的主节点 IP，并在目标网络与目标 CANN 环境人工验证。

固定版本文档明确 A2 多节点 CI 自 2026-09-02 停用，脚本仍在不代表持续验证仍在运行。CANN 8.5.0 的矩阵也已移除，不能写成当前兼容范围。窗口混用和事件限制见[Buffer 指南](deepep_buffer_strategies.md)，接口数据契约见[Normal](../../../apis/deepep/deepep_normal_dispatch_combine.md)与[Low-Latency](../../../apis/deepep/deepep_low_latency_dispatch_combine.md)。

本次未执行安装、通信脚本、跨机连接、数值或性能测试，上述命令仅为来源中的后续验收入口。

## Evidence

- [python/deep_ep/doc/A2_DEEPEP.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/A2_DEEPEP.md)（primary）
- [python/deep_ep/doc/NORMAL_API.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/doc/NORMAL_API.md)（constraint）
- [python/deep_ep/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/deep_ep/README.md)（supporting）
