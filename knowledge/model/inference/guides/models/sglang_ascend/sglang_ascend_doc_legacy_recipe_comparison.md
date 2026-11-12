---
type: Guide
title: SGLang 旧昇腾配方的并行选择与性能证据边界
description: 保留旧 R1、V3.2-Exp、Qwen/Coder/Next 的A2/A3工作负载与同名指标差异，避免跨版本比较。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Best%20Practice%20on%20Ascend%20NPU.mdx
  role: primary
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/basic_usage/deepseek_v32.mdx
  role: supporting
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-09T04:33:52Z'
platforms:
- a2
- a3
---

# SGLang 旧昇腾配方的并行选择与性能证据边界

## 这份数据的使用边界

旧sgl-docs将多模型A2/A3配方合并在一个页面，脚本多含CANN8.5工具链路径、旧graph-bs/max-bs、SPEC_V2、prefill-round-robin-balance和decode_round_robin等接口。没有固定SGLang发行版、完整CANN组件组合、warmup、独立重复次数与误差；本次没有执行这些命令。它们保留为上游单场景报告，不能与当前v0.5.18/CANN9.0或B105教程直接相除计算版本加速比。

## 可复用的部署选择

R1 W8A8 PD将normal通信放P、low_latency和NEXTN放D，分别为P1/1/2、D3/1/4或2/1/3；32卡方案包含两个独立P实例和双节点D组，router必须列齐P的8998/8999 bootstrap。W4A8混部用TP16/DP16或DP4，PD按输入长度改变P/D admission、buffer和graph范围。不同精度与资源不能拿同一TPOT标签视为相同吞吐。

V3.2-Exp 64K方案使用旧enable-nsa-prefill-context-parallel，P双节点TP32、max-running1、禁用graph，D双节点TP32/EP32/DP8、low_latency和graph max4。Exp checkpoint、旧开关与当前V3.2/CP策略都不同；不能只改模型路径迁移。

Qwen235 PD为P TP16/DP16 normal、D TP32/DP32 fuseep；QwenCoder480 PD为P TP16/DP2 normal、D TP32/DP4 fuseep，此外有TP32/DP4双节点混部和TP16/DP4单节点混部。Coder配方未启用draft，不能从同页Qwen235的EAGLE3借入推测支持。旧Next配方TP4/max-running80、graph80且无NEXTN，与新Next量化主模型+BF16 draft方案不同。

A2 Qwen32B的部分标题称8卡而命令只TP4/base-device4，可能描述宿主资源而非实际参与设备，来源未解释；不能把“8卡”直接当rank数。旧GLM/Qwen简例与此表同样只给部署起点，需要逐项核对实际生效CLI。

## 上游报告与命令的工作负载

以下按正文场景列出报告TPOT和该段附带benchmark。未重复给benchmark的段落只表示引用前文，不能补造新的请求参数；rate未给时记未知而非假定inf。长度对调、端口或精度矛盾保留在后文。

| 场景 | 报告TPOT | benchmark输入/输出；并发/请求；rate |
|---|---|---|
| DeepSeek-R1 3_5K-1_5K 50ms on A3 32 Cards Separation Mode | 50ms | 3500/1500；768/3072；16 |
| DeepSeek-R1 6K-1_6K 20ms on A3 32 Cards Separation Mode | 20ms | 6000/1600；32/32；未知 |
| DeepSeek-R1 3_9K-1K 20ms on A3 32 Cards Separation Mode | 20ms | 3900/1000；768/768；16 |
| DeepSeek-R1 3_5K-1_5K 20ms on A3 32 Cards Separation Mode | 20ms | 3500/1500；768/768；16 |
| DeepSeek-R1 3_5K-1K 20ms on A3 32 Cards Separation Mode | 20ms | 3500/1000；768/768；16 |
| DeepSeek-R1 2K-2K 50ms on A3 8 Cards Mixed Mode | 50ms | 2048/2048；256/1024；未知 |
| DeepSeek-R1 2K-2K 50ms on A3 16 Cards Separation Mode | 50ms | 2048/2048；400/3200；8 |
| DeepSeek-R1 3_5K-1_5K 50ms on A3 8 Cards Mixed Mode | 50ms | 3500/1500；144/576；未知 |
| DeepSeek-R1 3_5K-1_5K 50ms on A3 16 Cards Separation Mode | 50ms | 3500/1500；384/1536；未知 |
| DeepSeek-V3.2-Exp 64K-3K 30ms on A3 32 Cards Separation Mode | 30ms | 64000/3000；32/64；未知 |
| Qwen3-235B-A22B 3_5K-1_5K 50ms on A3 24 Cards Separation Mode | 50ms | 3500/1500；860/3440；未知 |
| Qwen3-235B-A22B 3_5K-1_5K 50ms on A3 8 Cards Mixed Mode | 50ms | 3500/1500；272/1088；未知 |
| Qwen3-235B-A22B 2K-2K 100ms on A3 8 Cards Mixed Mode | 100ms | 2000/2000；576/576；未知 |
| Qwen3-235B-A22B 2K-2K 50ms on A3 8 Cards Mixed Mode | 50ms | 2048/2048；480/480；未知 |
| Qwen3-235B-A22B 2K-2K 50ms on A3 16 Cards Mixed Mode | 50ms | 2000/2000；768/768；未知 |
| Qwen3-235B-A22B 11K-1K 10ms on A3 8 Cards Mixed Mode | 10ms | 11000/1000；1/1；未知 |
| Qwen3-32B 6K-1_5K 18ms on A3 4 Cards Mixed Mode | 18ms | 6000/1500；32/32；未知 |
| Qwen3-32B 4K-1_5K 11ms on A3 4 Cards Mixed Mode | 11ms | 4096/1500；1/4；未知 |
| Qwen3-32B 18K-4K 12ms on A3 8 Cards Mixed Mode | 12ms | 4000/18000；1/1；未知 |
| Qwen3-32B 3_5K-1_5K 50ms on A3 2 Cards Mixed Mode | 50ms | 3500/1500；78/312；未知 |
| Qwen3-32B 2K-2K 50ms on A3 2 Cards Mixed Mode | 50ms | 2000/2000；120/480；未知 |
| Qwen3-30B-A3B 3_5K-1_5K 50ms on A3 1 Card Mixed Mode | 50ms | 3500/1500；156/624；未知 |
| Qwen3-Coder-480B-A35B-Instruct 3_5K-1_5K 50ms on A3 24 Cards Separation Mode | 50ms | 3500/1500；410/1640；8 |
| Qwen3-Coder-480B-A35B-Instruct 3_5K-1_5K 50ms on A3 16 Cards Mixed Mode | 50ms | 3500/1500；288/1152；20 |
| Qwen3-Coder-480B-A35B-Instruct 3_5K-1_5K 50ms on A3 8 Cards Mixed Mode | 50ms | 3500/1500；80/320；未知 |
| Qwen3-Next-80B-A3B-Instruct 3_5K-1_5K 50ms on A3 2 Cards Mixed Mode | 50ms | 3584/1536；80/160；未知 |
| Qwen3-32B 6K-1_5K 18ms on A2 8 Cards Mixed Mode | 18ms | 6000/1500；32/32；未知 |
| Qwen3-32B 4K-1_5K 11ms on A2 8 Cards Mixed Mode | 11ms | 4096/1500；1/4；未知 |
| Qwen3-32B 3_5K-1_5K 50ms on A2 8 Cards Mixed Mode | 50ms | 3500/1500；78/312；未知 |
| Qwen3-32B 2K-2K 50ms on A2 8 Cards Mixed Mode | 50ms | 2000/2000；120/120；未知 |


## 不应静默修正的来源矛盾

- Qwen32B“18K输入/4K输出”标题的命令却是input4000/output18000；这项12ms不能自动归到18K/4K负载。
- Qwen235低延迟汇总标BF16，正文命令仍带quantization=modelslim；不能单凭标题确认checkpoint精度。
- 若干benchmark端口与前方server/router不匹配，Qwen235双节点还出现quantization参数等号空格；应先核对本地CLI与endpoint，不能把文档脚本完整当成已验证可运行产物。
- A2/A3、物理卡数、并发和输入精度改变时，50ms等标签只是各自场景的结果，不是稳定SLA或独立优化收益。

复现应保存实际checkpoint、设备参与数、CANN/TorchNPU/SGLang版本、P/D拓扑、缓存策略、采样和warmup，并以同负载作对照。参见[当前R1配方](sglang_ascend_doc_deepseek_r1.md)、[当前Qwen235配方](sglang_ascend_doc_qwen3_235b.md)和[性能评测方法](../../optimization/sglang_ascend/sglang_ascend_doc_benchmark_method.md)。


## 旧 DeepSeek V3.2 通用入口

旧通用页另提供dsv32-a2/dsv32-a3镜像名，并称tilelang实现可运行GPU/HPU/NPU；没有给出该NPU路径的版本、产品内核或性能对照。它不能用来把GPU的flashmla/fa3或FP8 KV默认值扩展到NPU，也不能替代本卡Exp配方或当前专门Ascend教程的证据。

## Evidence

- [sgl_docs：docs/hardware-platforms/ascend-npus/Best Practice on Ascend NPU.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/hardware-platforms/ascend-npus/Best%20Practice%20on%20Ascend%20NPU.mdx)（primary）
- [sgl_docs：docs/basic_usage/deepseek_v32.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/basic_usage/deepseek_v32.mdx)（supporting）
