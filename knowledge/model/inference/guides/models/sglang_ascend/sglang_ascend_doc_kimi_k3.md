---
type: Guide
title: Kimi K3在A3与950的参考混部、2P4D和草稿配置
description: 按生成器真实NPU cell限定W4A8/MXFP4、KDA预算、DSPARK和MemFabric，保留验证进行中、容量TODO及HiCache测试差异。
tags:
- task.optimization
- task.testing
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/moonshotai/kimi-k3.jsx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/Moonshotai/Kimi-K3.mdx
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/_kimi_k3_mamba_ratio_calculator.jsx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/_kimi_k31_mamba_ratio_calculator.jsx
  role: constraint
created_at: '2026-11-08T12:38:11Z'
updated_at: '2026-11-08T12:38:11Z'
platforms:
- a3
- '950'
---

# Kimi K3在A3与950的参考混部、2P4D和草稿配置

## 权重、版本和证据范围

K3为KDA/MLA混合MoE，源配置93层（69 KDA、24 MLA）、896 routed+1shared专家。这里只摄取明确NPU分支；不将CUDA/ROCm的MegaMoE、DCP性能或B300验证数字移植到NPU。所有NPU cell均标验证进行中，Cookbook也说尚无这些最终权重/当前代码的完整serving轮次，精度没有逐cell重测，因此本卡draft。本次没有执行上游或验证性能。

A3用sgl-npu/Kimi-K3-W4A8 ModelSlim（文档约1.49TB）、main-cann9.1.0-a3镜像；950PR/DT用moonshotai/Kimi-K3 MXFP4、cann9.1.0-950-B070镜像，量化从checkpoint检测，cell不传quantization（ModelSlim另需该参数）。DSPARK草稿RadixArk/Kimi-K3-DSpark约4.5GB。标签不是不可变镜像digest，部署须记录实际版本与权重revision。

## 每个角色是一组配置

| 配方 | 拓扑与内存 | 调度、图与缓存 |
|---|---|---|
| A3混部 | 4节点×8物理卡×2die=64rank，TP64/attention-DP4，shared/dense MLP按attention-TP分片，static0.78 | max-running64/Mamba64、chunk16384、graph2/4/8/16、DeepEP auto |
| A3 2P4D Prefill | P池2节点，TP16/PP2/DP2，PP层48,45，static0.85 | NOSPEC、禁图/Radix/custom-allreduce、overlap-plan-stream0、chunk4096/max-running16、DeepEP auto |
| A3 2P4D Decode | D池4节点，TP64/PP1/DP4，static0.82 | DSPARK、graph16、max-running16、禁Radix/custom-allreduce、linear verify triton、DeepEP auto |
| 950混部 | 4节点×8卡=TP32，文档称dp1；shared-experts-tp-size4，static0.9 | max-total200000/max-running32、chunk2048、graph32、禁Radix/custom-allreduce、DeepEP auto；没有950 PD cell |

A3正常混部dispatch128、HCCL_BUFFSIZE200、DeepEP HCCL1800；P/D dispatch64、HCCL_BUFFSIZE800/1200。长序列轮次64×512是此组配方，不能泛化容量。950 dispatch64、DeepEP HCCL2000，并关闭多种folded/stacked/graph embedding优化。SGLANG_NPU_USE_FIAS_V2_BSND在脚本注释，cell未开启；不能代补成默认。

## DSPARK与CPU序列镜像

除A3 PP2的P角色只能NOSPEC，NPU生成器为扁平角色固定DSPARK：block7、topk1、draft quantization unquant、draft attention ascend。CUDA的enable-linear-replayssm-spec不向NPU发出；隐藏该选项不是对其它版本实现的结论。

可选target MLA verification `SGLANG_NPU_USE_FLASH_MLA=1`与draft MHA `ASCEND_USE_PAGED_MTP=1`默认false，要求sgl-kernel-npu提供attention.flash_mla及attention.paged_mtp_attention。若要关闭CPU序列长度mirror/host attention参数更新，需要**两个kernel均开**并显式`SGLANG_NPU_ATTN_BACKEND_NEEDS_CPU_SEQ_LENS=0`；只选kernel仍保留默认1的CPU镜像。来源宣称适用于eager和graph replay，须按实际模块版本验证。

源码还留容量TODO：950 batch32×verify宽8可达每rank256 tokens，而dispatch配置64；它要求稳态batch32复核，不能拿CUDA sizing rule直接断定NPU必失败或已安全。草稿block、graph batch和通信容量必须一起验收。

## 2P4D连接与内存预算

A3 PD共6节点。每个pool各有自己的dist-init头和nnodes/node-rank（P0–1、D0–3），不可把两个pool合并到一个rendezvous。所有6节点的ASCEND_MF_STORE_URL都指向**P头**34670；HTTP P30000、D30100、bootstrap8998，router可在任意可达主机，客户端走router8000。HCCL/Gloo接口和本机业务IP在每节点分别填，P先启动，再D。

K3/K3.1两个ratio calculator会检测device=npu并广播ratio=null/baseRatio=null，不生成mamba-full-memory-ratio；显式max-mamba-cache-size也阻止ratio覆盖。K3.1另对pinned ratio、PD decode及TPU跳过，不能把其CUDA DSA/DFLASH ring公式当K3 NPU预算。A3混部显式Mamba64，PD按max-running预算；950另限paged KV总token，启动后必须读回实际KV与状态容量。

## 入口限制与测试差异

该NPU生成器固定Balanced（P为Default）、不开放tool calling、HiCache L2/L3，并用“NPU不支持Mamba缓存”解释HiCache禁用；这是页面的配方/可见性边界。当前源码又有[Kimi K3 mixed HiCache L2测试定义](../../testing/sglang_ascend/sglang_ascend_doc_validation_cache_pd.md)（TP64/DP4/Mamba240/ratio4），以及Mamba L3文件回读定义，表明来源间存在版本内差异；测试未执行，不能据任一侧宣称全局支持或禁止。

reasoning parser kimi_k3把思考放reasoning_content、答案放content，模型始终thinking，reasoning_effort控制深度。Cookbook公开图像输入合同只支持image而拒video/audio；其CUDA ViT/IPC/EPD性能不是NPU验证。NPU工具调用尚未在这些配方支持，不能由通用工具示例推定可用。质量应先在真实权重、greedy/采样和图模式下核验，再测接受长度、TTFT/TPOT、资源归还及PD状态传输。

## Evidence

- [docs/src/snippets/configs/moonshotai/kimi-k3.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/configs/moonshotai/kimi-k3.jsx)（primary）
- [docs/cookbook/autoregressive/Moonshotai/Kimi-K3.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/cookbook/autoregressive/Moonshotai/Kimi-K3.mdx)（supporting）
- [docs/src/snippets/_kimi_k3_mamba_ratio_calculator.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/_kimi_k3_mamba_ratio_calculator.jsx)（constraint）
- [docs/src/snippets/_kimi_k31_mamba_ratio_calculator.jsx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/src/snippets/_kimi_k31_mamba_ratio_calculator.jsx)（constraint）
