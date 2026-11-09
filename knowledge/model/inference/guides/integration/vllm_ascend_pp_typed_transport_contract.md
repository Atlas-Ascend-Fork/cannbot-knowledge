---
type: Guide
title: vLLM Ascend PP 传输接入：PPTransportDataType、辅助隐状态与 TopK 缓冲
description: 接入流水并行模型时核对推测解码能力表、辅助隐状态的阶段边界、TopK 的发送接收与共享缓冲、类型化 intermediate 工厂及键排序；区分模型产出、Runner
  开关与真实跨卡传输验收。
aliases:
- PPTransportDataType
- SpecPPSupport
- resolve_spec_pp_support
- pp_stage_requires_topk_indices
- add_pp_transport_tensors
- get_pp_transport_tensors
- make_empty_intermediate_tensors
tags:
- task.implementation
- task.debugging
- topic.parallelism
- topic.speculative_decoding
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/pp_transport.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_pp_transport.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/sequence.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T01:39:11Z'
updated_at: '2026-11-02T01:47:35Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend PP 传输接入：PPTransportDataType、辅助隐状态与 TopK 缓冲

## 接入任务与固定范围

新模型接入 PP 时，普通 hidden/residual 之外还可能传递辅助隐状态或复用前层 TopK。先核对方法能力、阶段边界、接收缓冲和键集合，再验证真实通信。模型能产出辅助状态、payload 中出现 Tensor、Runner 打开输出开关，是不同阶段的证据。

本卡固定 Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整阅读 pp_transport.py 267 行及其 UT 121 行；独立 Native 5df63a7203cdb9328d824a27b682e77c7b9928be 的 sequence.py 62 行也全文阅读。Main Runner 仅阅读 151–217 行初始化接线，utils 仅阅读 220–227 行 should_reuse_topk。Main 配对 Native pin 是 544f182d9f0c9bfe8bd7645525951d5e3692a542；独立 Native 容器接口不是配对 ABI 或 NPU 验收。整项传输的硬件范围未闭环，保持 draft、空平台；本次未导入或执行上游代码和测试。

模型内部状态仍按各自接口核对：[MiniMax-M3 语言模型](vllm_ascend_minimax_m3_language_contract.md)、[Kimi DSpark](vllm_ascend_kimi_dspark_adaptation.md)及[GLM MLA DSpark](vllm_ascend_glm_mla_dspark_adapter.md)维护模型与草稿的捕获语义；[方法选型](../optimization/vllm_ascend_speculative_method_selection.md)维护方法和 Runner 的其他限制。本卡维护通用 payload 接口，不能把不同模型的 tap、materialized/raw 格式或词表处理合并成同一协议。

## SpecPPSupport：登记能力与完整准入分开

SpecPPSupport 是冻结 dataclass，包含可选 architectures 集合及 needs_aux_hidden_states，后者缺省 False。方法表通过 MappingProxyType 包装，其固定内容如下。

| 方法 | 表内架构限制 | 是否要求辅助隐状态 |
| --- | --- | --- |
| mtp | architectures=None，不按架构过滤 | False |
| eagle3 | MiniMaxM3SparseForCausalLM、MiniMaxM3SparseForConditionalGeneration | True |
| dspark | DeepseekV4ForCausalLM、GlmMoeDsaForCausalLM、KimiLinearForCausalLM、KimiK3ForCausalLM、KimiK3ForConditionalGeneration | True |

resolve_spec_pp_support 在未配置 speculative_config、PP size 不超过 1、方法未登记或受限架构不匹配时返回 None，没有在这些分支抛出“禁止运行”的异常。架构集合非 None 时，model_config 缺失也返回 None；MTP 没有该架构过滤，不能据此宣称任意模型或完整 PP/MTP 组合都已运行兼容。

所读 Runner 先解析该表，再调用父初始化；返回能力且 needs_aux_hidden_states=True 时，把 use_aux_hidden_state_outputs 设 True。None 不代表此处把已有值设 False，更不等于父类或其他准入逻辑的最终结论。另有针对部分 FIA 架构的 sync_spec_pp_cpu_counts 条件，不能把它与能力表合成“相同模型集合”。Runner 其他初始化、实际拒绝、调度及通信不在这个有界片段范围内。

MiniMax-M3 模型内部允许 Eagle3/DSpark 的辅助层选择，也不意味着这个固定 PP 表同时为两种方法登记了 M3。需要同时检查实际模型产出、方法表和 Runner 消费，不能互相替代。

## PPTransportDataType 与中间容器

PPTransportDataType 只有 AUX_HIDDEN_STATES 和 TOPK_INDICES，值分别为 aux_hidden_states、topk_indices。键前缀由 pp_transport、类型值和下划线组成，例如 pp_transport_aux_hidden_states_0 与 pp_transport_topk_indices_0。类型注解不等于所有公开 helper 都有运行时类型校验。

独立 Native IntermediateTensors 直接持有传入的 tensors 字典；字符串索引返回原 Tensor，赋值更新同一字典。切片会对每个 Tensor 应用切片并新建容器，不自动 clone 底层 storage。empty_like 逐项调用 torch.empty_like，不能把其结果视为零初始化或已有有效接收数据。手工构造函数是为 Dynamo 保留来源定位的实现选择，不构成所有编译/图模式已验证的证明。

items 返回字典条目，len 返回键数，不能用来推断 batch 行数。相等判断要求对应容器类型、相同键集合和逐项 torch.equal；值相等也不证明存储互相独立。

这些 helper 只组织对象、键和值；没有在自身执行 HCCL send/recv、barrier 或跨进程同步。payload 被构造成功不能代替多卡传输成功。

## TopK 在哪个阶段需要接收和发送

pp_stage_requires_topk_indices 对 start_layer<=0 或 start_layer>=num_hidden_layers 返回 False。有效阶段边界满足以下任一条件时返回 True：indexer_types 中对应项忽略大小写后为 shared；或 use_index_cache 为真且 should_reuse_topk 对该层为真。先检查是否有该项，不把相邻层或第一个模型层误当成本阶段入口。

should_reuse_topk 存在 index_topk_pattern 时，只认合法索引处的大写 S。缺少 pattern 时，使用 index_topk_freq（缺省 1）与 index_skip_topk_offset（缺省 2）的取模公式：`max(layer_id-offset+1,0)%freq != 0`。这段 helper 没有检查 freq 非零；配置验证应在调用方闭环，不能用“构造成功”证明所有整数都合法。

configure_pp_topk_transport 只有 data_types 选择 TOPK_INDICES 时才设置状态：receive_pp_topk_indices 按 model.start_layer 判断，send_pp_topk_indices 按 model.end_layer 判断，二者均要求已有 topk_indices_buffer。buffer 为 None 时两个标记为 False。未选择该类型时直接返回，并没有主动清除先前标记；切换配置或复用模型对象时需要核对已有状态。

这里维护的是阶段边界需求与标记，未分配 TopK buffer，也未执行发送。发送标记为真不证明消费者已经读到了相同请求/层的索引。

## make_empty_intermediate_tensors：先接通工厂，再核对接收预算

make_empty_intermediate_tensors 包装模型原 tensor_factory。缺省只添加 AUX_HIDDEN_STATES，include_start_layer 缺省 True；需要 TopK 时必须显式选择，并预先准备模型状态。重复类型和不在工厂映射中的类型会在返回 wrapper 前抛 ValueError。不要把这里的集合成员检查解释成对全部非法输入类型都有统一错误处理。

调用 wrapper 时，先执行原工厂得到 IntermediateTensors，再按 data_types 的给定顺序追加对应接收缓冲。辅助状态和 TopK 的预算方式不同。

| 接收类型 | 实际分配或借用 | 核对要点 |
| --- | --- | --- |
| 辅助隐状态 | 对每个预期输入层创建 torch.zeros，形状为 `(batch_size, model.config.hidden_size)`，使用工厂传入的 dtype/device | 计入真实接收层数和本阶段边界，不能以目标模型总层数统一分配 |
| TopK | receive 标记为真时借用已有 topk_indices_buffer 的 `[:batch_size]` view，作为单个 Tensor 加入 payload | 检查首维容量、原 buffer 的 dtype/device、共享 storage 和生命周期；该路径丢弃工厂传入的 dtype/device |

辅助状态计数为 layer_idx<start_layer，或 include_start_layer=True 且 layer_idx==start_layer 的辅助层数。UT 用 start=2、aux=(0,2,4) 检查默认包含阶段起点，得到两个 `(3,4)` CPU buffer；这只是测试设计，不证明完整模型捕获和跨阶段顺序已经正确。

TopK 接收要求已有 buffer，batch_size 大于其首维容量时明确 ValueError；它没有在此重新分配或扩容，也没有验证所有负 batch、TopK 宽度和 stride 情形。借用 view 保留原存储，不能由新增 payload 键推导已经隔离并发请求或图重放的状态。

## add/get 的原地更新、排序与残留键

add_pp_transport_tensors 把传入列表按 0 起始的后缀写入同一 tensors 字典，并返回同一 IntermediateTensors。它覆盖相同序号，没有删除此类型更高序号的旧键。若复用同一 payload 且列表由长变短，旧尾部会保留；调用方应重建 payload 或明确清理，不能假设 helper 自动缩短键集合。该条件推导不表示本次已复现某条生产 Runner 的残留问题。

get_pp_transport_tensors 收到 None 时返回空列表；否则只收集对应前缀的键，把后缀转 int，再按数字排序。因此后缀 2 应排在 10 前，不能用字典插入顺序或字符串排序替代。后缀不合法会在 int 转换时失败；实现未要求后缀连续，也未核对 Tensor shape、请求身份或写入完成事件。

add_pp_transport_buffers 先按 count 创建 zeros，再委托 add。为了减少初始化开销直接改成 empty，必须先证明后续每个消费点之前都已完整覆写，不能仅依据 Native empty_like 的存在或函数名“empty”作优化依据。

## 适配与验证顺序

固定目标模型、方法、PP 分区、辅助层与实际配置对象；分别列出模型产出格式、方法表返回值和 Runner 最终开关。枚举各阶段 start/end、aux 接收数量及 TopK send/receive，核对第一阶段、末边界、shared/index-cache 两种路径与无 buffer 情形。SP token 补齐和裁剪由模型调用方负责，通用 helper 不会自动恢复完整 hidden/residual 布局。

随后验证 payload 键集合、数字顺序、dtype/device、容量与别名，覆盖列表缩短、非法后缀、重复类型和不支持类型；再在匹配环境中检验跨卡发送接收、真实辅助状态顺序、dummy/idle、graph capture/replay 与请求并发。需要优化时另留无改动基线、通信/初始化耗时和模型质量，不能把接收缓冲构造当作端到端性能结果。

来源 UT 主要检查 TopK 边界条件、方法/架构与 PP size 的能力选择、aux 阶段起点以及 Kimi 的三个别名。它没有完成上述全部容量、别名、残留键、通信和图验证，本次也没有执行这些 UT、NPU、模型或 Agent A/B。出现不匹配时停止该 PP/spec 组合的完整支持结论，恢复已有验证的分区和方法配置；不通过丢辅助层、截断 TopK 或补零掩盖协议差异。
