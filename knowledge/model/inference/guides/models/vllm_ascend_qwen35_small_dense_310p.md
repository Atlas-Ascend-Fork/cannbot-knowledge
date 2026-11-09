---
type: Guide
title: vLLM Ascend Qwen3.5 小规格：310P FP16/W8A8 与混合状态
description: 在Atlas300I DUO按2B/4B/9B的FP16和专属310P权重接入，核对TP1/2与GDN状态；Atlas200I Pro先确认实际芯片族。
  补齐 Qwen3.5-9B 等小模型的 MTP1 与最多两个捕获尺寸、单NPU TP1、8080监听空间及GSM8K与TextVQA来源口径。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Qwen3.5-Dense.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3.5-Dense.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-30T15:39:43Z'
platforms:
- 310p
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- Qwen3.5-2B
- Qwen3.5-4B
- Qwen3.5-9B
---

# vLLM Ascend Qwen3.5 小规格：310P FP16/W8A8 与混合状态

## 范围与芯片确认

教程针对2B/4B/9B的GDN+full Attention，列Atlas300I DUO和200I Pro，最早版本0.23rc1。本卡平台只登记已确认310P分支，不把所有名为Atlas200I的设备映射到同一芯片或310B；先检查SoC与安装包构建目标。

## 权重和并行

FP16权重与Eco-Tech W8A8-310P各有独立checkpoint，不能因小模型就选BF16或标准A2 quant config。来源只给TP场景，DUO TP1/2按可见device，单可见NPU的Pro用TP1；不默认DP/EP/多机PD。

## 状态与内存

小总参数不消除hybrid recurrent-state契约。先验证长输入、混batch、请求结束/复用的GDN state与Attention KV，再分别增加chunk/prefix/图/投机，未知组合保持关闭。长度、seq数和memory utilization按真实可用HBM，不能将27B系列的TP4/256K推荐移到2B/4B/9B。

## 验收与回退

核对FP16参考、量化layer scheme、实际Runner与兼容算子，在同硬件比质量/峰值与服务延迟。依赖冲突先按专用镜像处理，不能全局卸载用户环境包。失败回该芯片已验证FP16/最小配置并重建状态。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## 完整小模型配方与中文对应

Qwen3.5-Dense.po 的79条消息已逐条对照完整399行英文，78条msgid连续匹配，1条为MTP参数文字修订，没有新的硬件能力变化。准确模型为 Qwen3.5-2B、Qwen3.5-4B、Qwen3.5-9B；原始FP16模型与 Eco-Tech 对应的 Qwen3.5-2B-W8A8-310P、Qwen3.5-4B-W8A8-310P、Qwen3.5-9B-W8A8-310P 是不同产物，不能用标准A2量化权重替代专属310P布局。当前教程给的是FP16启动例，量化清单本身不是全部INT8路径已在本仓通过的证明。

三份服务例均为TP1、seq32、context16384、gpu-memory-utilization0.90、dtype=float16、mamba-ssm-cache-dtype=float16。源码建议仅在checkpoint带MTP head时用 qwen3_5_mtp，示例num_speculative_tokens=1；不能把启动例当所有微调/转换checkpoint都有head。实际可见多设备的DUO可评估TP2，单可见NPU的200I Pro用TP1；没有在本配方列出DP/EP或多机PD支持。

FULL_DECODE_ONLY、capture[2,16]、enable_npugraph_ex=false分别保留。TP模式最多两个图尺寸；MTP1将无MTP的[1,8]放大成[2,16]。正文[1,2,4,8]→[2,4,8,16]只演示乘法，不解除两档限制；不能照抄四档当合法配置，也不因禁npugraph_ex断言全图都不可用。长度、seq32和0.90都是起点，不是各种HBM容量上的并发承诺。

## 8080、宿主系统与进程空间

示例服务绑定127.0.0.1:8080，Docker模板另发布8080:8080。由这些值可推知，需要先明确请求从容器内还是宿主发起：容器内loopback服务不能仅靠端口发布就视为宿主可达；在真实网络命名空间检查监听地址和目标URL。此为对源配置的工程推断，本次没有启动容器或验证网络。不要把“Docker Up”“pip show”或宿主端口存在当实际forward成功。

DUO模板映射0–7设备不表示TP1服务使用八个worker；200I Pro只映射所选NPU，Ubuntu24.04与openEuler24.03的设备、驱动/系统配置、libyaml及其他库挂载不同。模板shm-size=10g也不是模型HBM预算。版本/镜像宏实际展开后按[环境准备](../deployment/vllm_ascend_versioned_environment.md)核对；旧卸载Triton建议仍只作来源条件，不在知识摄入时修改环境。

## 精度口径与停止条件

| 源文DUO报告 | GSM8K accuracy | TextVQA accuracy |
| --- | --- | --- |
| Qwen3.5-2B | 77.71 | 76.09 |
| Qwen3.5-4B | 93.18 | 79.08 |
| Qwen3.5-9B | 95.30 | 82.33 |

其AISBench配置为VLLMCustomAPIChat、max_out_len4096、batch_size16、request_rate0、retry2、temperature0、ignore_eos=false、enable_thinking=false，并用extract_non_reasoning_content。这些是来源分数与评测配置，未给完整数据版本/权重hash，不转移成200I Pro、INT8或本仓结果；TextVQA表不替代真实图片processor/请求验证。服务采样长度、Chat与Completions各自长度字段按实际API schema检查，不能仅因HTTP200就假定所有参数被消费。

优先保存实际加载身份、FP16参考、首请求非空输出和GDN/KV生命周期，再逐项加图、MTP、量化、共享前缀与负载；质量偏离、状态复用异常、首请求失败或容量不足时回完整最小参考。来源没有具体吞吐/时延数字，本次没有运行AISBench/NPU或修改verified。


## 小规格模型的 MTP1 与两个捕获尺寸

以 Qwen3.5-9B 为例，先确认实际checkpoint含MTP head，再按MTP1配置num_speculative_tokens=1。TP模式要求最多两个捕获尺寸，源例把无MTP的[1,8]变为[2,16]；两个捕获尺寸和K+1倍数是同时满足的条件，不因换成小规格模型就放宽。Qwen3.5-2B、Qwen3.5-4B的对应样例遵循相同条件，仍分别检查权重与实际内存。
