---
type: Guide
title: DeepSeek V4.1 Flash：950 单卡的 Engram 与专家卸载
description: 区分 Host 随机查表与 CPU 专家计算，按 HBM、Host/NUMA 内存、重叠窗口和热专家覆盖率评估 950 单卡部署。
tags:
- task.implementation
- topic.model_serving
- topic.memory
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4_1/dsv41-flash-950-single-card.md
  role: primary
created_at: '2026-10-29T04:09:04Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- '950'
---

# DeepSeek V4.1 Flash：950 单卡的 Engram 与专家卸载

## 适用范围与预期产物

面向固定文档中的 128 GB HBM 昇腾 950 单卡、vLLM-Ascend + KTransformers + kt-kernel 路径。产物应包含实际软件版本、权重驻留规划、Host/NUMA 容量、正确性与 TTFT/TPOT 的实测记录。

## 容量与两类卸载

510.29 GB checkpoint 中，Engram 与 routed experts 占主要容量。Engram 通过行号请求在 Host 查表，再把命中向量搬回 NPU；CPU 专家由 kt-kernel 执行 GEMM。这两条路径的数据访问与计算成本不同。

来源的每层 384 专家中 100 个驻留 NPU、284 个下放 CPU；该配置的 die 权重约 90.29 GiB，Host 稳态约 557.97 GiB。Host 统计包含 /dev/shm、匿名内存与源页缓存，不能只按 checkpoint 大小估算。NUMA 绑定还要求各内存域分别满足容量。这些是文档实例，驻留数需按目标机器重算。

## 实施步骤

1. 先确认实际依赖与加载器，在完整权重上区分 Engram、专家与其他权重，预算 KV 池及临时缓冲。
2. 分别建立 Host 查表和 CPU 专家基线，再考虑副流。host 路径在 routing 后 fork，NPU combine 后、CPU 贡献合并前 join；ACL 外部事件由完成线程放行。
3. 共享专家的输入不依赖 CPU 结果，可在依赖允许时移入重叠窗口。窗口大小约束可隐藏的 CPU 时间。
4. 评估 stream_prefill 与 dynamic_resident 的组合：后者依赖前者，按本次 Prefill 热度重选驻留专家。驻留覆盖率、搬运成本与 prompt 长度共同决定收益。

## 验证、回退与停止条件

先单请求验证输出与状态，再在相同数据和种子下比较串行、副流及动态驻留配置，分别记录 TTFT、TPOT、Host/NUMA 内存与专家覆盖率。资源不足、外部事件无法可靠放行、路径版本不兼容或正确性变化时停止扩大测试，回到已验证的串行/静态驻留基线。

文档中的 35.60→30.31 ms 与另一组 29.77→25.29 ms 属于不同对照，不应拼成连续消融。短序列循环拼接的 TTFT 表仅展示流式特性；stream_prefill_min_tokens 的最优交叉点尚需实测。SSD Engram 和 Decode 专家预取属于未来方案。

## Evidence

来源提供容量表、流依赖、观测数据与精度表；本批仅审阅文档，未在 NPU 或完整权重上复测。
