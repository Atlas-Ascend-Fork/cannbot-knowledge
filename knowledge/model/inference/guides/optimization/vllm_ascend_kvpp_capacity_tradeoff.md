---
type: Guide
title: vLLM Ascend KVPP：用分层缓存与广播换取长上下文容量
description: 对照KVPP中文旧版与当前设计，核对TP×PCP层所有权、固定K和动态K的模型约束及图/connector门槛，分开裁决950DT容量、时延吞吐与实验状态。
tags:
- task.optimization
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/kvpp.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/kvpp.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_placement.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/kvpp.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/kvpp.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-10-30T05:32:14Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend KVPP：用分层缓存与广播换取长上下文容量

## 适用范围与决策目标

固定 Ascend ceac1a2 的 KVPP 是实验功能，面向非 hybrid MLA/SFA 模型中 TP/PCP 重复 KV 导致的容量瓶颈。先核对目标平台、量化和 Attention backend；来源的容量测试仅限 950DT 的特定 GLM-5.2 部署，不构成 A2/A3 的性能结果。

## 存储、通信和容量预算

在每个 DP replica、PP stage 内，TP×PCP 组按层连续均衡分配持久缓存所有权；同层主 KV、indexer 与量化组件构成一个 bundle。scheduler 的逻辑块号不变，模型计算仍用原 TP/EP/PP 配置。draft 缓存独立分配，不能与 target 共享。

每 rank 的每块物理预算是“拥有的 target bundle 总量 + 本地 draft 缓存 + 2×最大 target bundle”。两份 scratch 交替接收非本 rank 所有的层。历史缓存广播传送整层的全部已分配块，并非只传当前请求活跃块；容量扩大也可能增加广播量。ready/completion event 保证数据就绪，预取是否被计算隐藏取决于实际时间线。

## 配置与排除条件

启用 `additional_config.enable_kvpp=true`，使用 eager 或 PIECEWISE。FULL、FULL_DECODE_ONLY、DCP、hybrid、Dynamic-K 均不在支持范围；固定 K 的 MTP/DSpark/Eagle3 还受模型和 backend 约束。TP、EP、PP、PCP 等逐项支持不表示它们任意组合都已验证。PP 组合仍有来源记录的间歇性 E2E 输出不一致，验收失败必须停用。

PD 只在 P 端启用 KVPP，使用实验 MooncakeConnectorV2；D 端关闭。Memcache pooling 使用 AscendStoreConnector、producer/both、whole-block，不能推导 consumer 已验证；KV events 与 consumer write-back 不支持。Mooncake layerwise 要求 load_async=false，独立 topology namespace，已有 replicated 对象不能复用；来源仅验证单节点 TP8 eager，GLM-5.2 验证仍待完成。

## 验证、收益与回退

固定同一部署比较启动自动计算的 cache capacity、峰值 HBM、长输入 TTFT、prefix hit 分布和吞吐。来源单节点 GLM-5.2-W4A8C8 TP8+EP 的 6.25 倍是缓存 token 容量；其非 pooling 测试吞吐反而下降，不能当成吞吐加速倍数，也不能当总 HBM 节省比例。

容量充足、广播成为关键路径、输出不一致或 connector 未验证时，关闭 KVPP，恢复同模型基线。本次只核对固定文档和代码，没有复测来源数字。


## 平台范围复核

主指南明确950DT GLM-5.2整项部署与off/on测量；本卡仅按该950DT范围声明，其他硬件及950其他产品变体仍需补证，不把容量比当全平台性能。


## KVPP中文版本差异与配置入口

两份kvpp.po共125条有效译文，设计27条中18条、用户指南98条中84条msgid匹配当前英文，其余23条逐项保留差异。旧设计只按TP归组、仅eager、禁PCP/PD/图和fixed-step MTP，当前设计改TP×PCP、eager/PIECEWISE、独立draft缓存及条件化connector组合。不能因中文旧限制忽略当前能力，也不能从当前逐项支持表推出所有组合同时通过。

旧用户译文把PCP限定MRv2并要求VLLM_USE_V2_MODEL_RUNNER=1，当前英文移除这些句子；旧性能通用设置还列DSA-CP/MRv1，当前英文不再列出，不能据旧表给当前测量补回这些条件。文档删句只说明描述已变，不单独证明每个Runner/PCP/模型实现都完成支持；选定Runner仍按有效配置与具体路径验收。

当前KVPPConfig.from_vllm_config用typed bool读取enable_kvpp，禁用返回size=1，启用按TP×PCP计算size；所读validate方法拒DCP、非PIECEWISE的非eager、非MLA或hybrid，MultiConnector要求非空子项且只接受MooncakeConnectorV2/AscendStoreConnector，Mooncake V2 consumer被拒。这里是该validator的局部条件，不代表所有上游字段、角色、SDK和模型都已验证，不能绕过后端的更细限制。

旧译文“所有固定K方法”改为方法本身受模型/backend支持约束，Dynamic-K从未验证措辞收窄为不支持。旧Mooncake layerwise行即使同时写GLM-5.2待验证仍标✅，当前明确Experimental；其单节点TP8 eager报告不验证PP/PCP/DCP。MultiConnector的子角色独立、owner load完成后才广播、completion信号保留到下步metadata绑定，以及独立topology namespace都要单独成立。load_async=false不等于全服务同步，也不启用owner持久cache跨层复用。

## 来源容量与延迟/吞吐测量分开读

固定指南单节点使用GLM-5.2-W4A8C8、8×950DT、TP8+EP；双节点使用GLM-5.2-W8A8C8-mxfp8、每节点8×950DT、TP8+PP2+EP且分层38/40。两套都列chunked prefill、prefix caching、async scheduling、LI-C8、eager，调度预算32768、max_num_seqs=12、memory utilization=.90，未开MTP和SFA-C8。不同权重量化/拓扑只在各部署内部比KVPP off/on，不跨表归因。

| 来源部署 | 关闭/开启容量tokens | 来源容量倍数 | 同token容量的等效KV内存节省 |
| --- | --- | --- | --- |
| 单节点 | 235008 / 1467904 | 6.25× | 83.99% |
| 双节点PP | 555392 / 2972416 | 5.35× | 81.32% |

容量由服务自动计算、无block-count override；单节点来自pooling配置，双节点来自非pooling启动日志。等效KV内存节省是容量比估计，不是整个服务HBM实际下降比例。

| 来源部署/输入 | 关闭/开启TTFT秒 | 来源时延变化 |
| --- | --- | --- |
| 单节点32K | 2.623 / 2.614 | -0.33% |
| 单节点64K | 5.295 / 5.375 | +1.52% |
| 单节点128K | 10.901 / 11.268 | +3.36% |
| 双节点32K | 2.900 / 2.905 | +0.19% |
| 双节点64K | 4.503 / 4.887 | +8.53% |
| 双节点128K | 7.805 / 8.665 | +11.01% |

TTFT是prefix hit=0、1 output token、客户端并发1的4请求均值，正数表示变慢；不是p99/SLO。上表保留来源四舍五入后的数值与报告百分比，没有本次原始请求记录或复算精度证明。

非pooling吞吐测试另用40请求、客户端并发12、128K输入/1输出：单节点0% hit为12492.4→12205.7 input tokens/s（-2.30%），90%为116516.2→110224.8（-5.40%）；双节点分别21395.2→18742.3（-12.40%）、177375.4→154717.3（-12.77%），90%场景实际hit=89.9414%。这些负载中容量增大但非pooling吞吐没有提高，不能将6.25×/5.35×写成加速比或推断所有pooling请求表现。所有数字均为上游报告，本批未运行模型/通信/性能实验。


## 固定K与动态K的模型约束

本卡中的固定K是固定数量的投机token；动态K（Dynamic-K）是相应的可变K路径。当前KVPP指南明确不支持动态K，不能把旧中文“尚未验证”改写成可直接启用，也不能把配置一个固定K值解释成动态K已实现。

固定K同样不是所有draft/模型的充分条件：来源只在所选MTP、DSpark、Eagle3等方法本身获模型和attention backend支持、draft缓存独立且不共享target KV的条件下列支持。先确认方法/模型组合，再选KVPP与允许的eager/PIECEWISE；单独换图模式不会消除动态K限制。具体每轮接受长度和端到端收益仍需实测，本次没有运行投机推理。
