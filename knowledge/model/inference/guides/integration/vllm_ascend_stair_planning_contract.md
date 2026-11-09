---
type: Guide
title: vLLM Ascend STAIR策略：加权时间分箱、风险与受限迁移计划
description: 接入StairEplbPolicy时区分原始样本与预分箱sum、频数权重和预测不均衡，核对hysteresis锚点、协方差风险、replica搜索与迁移预算、PP阶段分片planner、完整计划验证及commit后才保存预测。
tags:
- task.implementation
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/policy/stair.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/eplb/policy/_stair_process.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/policy/test_stair.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/eplb/policy/test_stair_process.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
created_at: '2026-11-03T01:18:51Z'
updated_at: '2026-11-03T01:18:51Z'
platforms: []
aliases:
- StairEplbPolicy
- StairPlan
- plan_sharded_rebalance
- weighted_moments
- incremental_replica_candidates
- STAIR协方差风险
- STAIR planner
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend STAIR策略：加权时间分箱、风险与受限迁移计划

## 任务与输入边界

本卡聚合Ascend `ceac1a2b` 的STAIR策略、独立planner协议、StairConfig与两份专项UT，为新MoE模型接入负载统计和重排决策。统计采样与fresh门禁由[EPLB模型控制器](vllm_ascend_eplb_model_weight_contract.md)维护；计划执行与注册资源见[EPLB通信](vllm_ascend_eplb_transport_contract.md)。本卡解释CPU规划合同，不把预测改善写作NPU、吞吐或时延实测。

rebalance_experts要求正rank/replica数且总replica可被rank数整除，并必须提供当前placement；旧图形状为 `[layers,num_replicas]`，内部转为 `[layers,ranks,slots]` 等容量布局。逻辑load是 `[samples,layers,logical_experts]`，二维原始输入会补一个sample维。不能用physical专家热度直接冒充logical load，或把PP全局层数和当前stage的层号混用。

显式rank_node_ids必须为每rank一个非负整数，并与num_nodes一致；未给时只在ranks能被nodes整除时推导均匀节点布局。CPU group大小须等于规划rank数。输入中的num_groups不能单独证明任意层次分组拓扑已由这条实现处理。

## 两种load表示：mean与sum不能混传

| 入口 | values与sample_counts |
| --- | --- |
| 原始plan_rebalance | `[steps,layers,experts]` 原始样本，sample_counts缺省 |
| prepare_local_load_stats / PreparedLoadStats | 按时间箱保存load的sum，并保存每箱正整数sample_counts |
| 规划内部 | 预分箱sum先除以对应counts，成为箱均值，再以counts加权 |

时间箱按连续边界 `floor(i*steps/bins)` 切分，bins取samples与上限较小者；不整除时各箱样本数不同。compress_load_window直接返回箱均值与counts，而prepare_local_load_stats返回箱sum；混用二者会再次乘除权重，改变热点。

weighted_moments的均值按频数加权，样本协方差分母为总counts减1；仅一个有效样本时方差/协方差为0。由实现可推知，分箱均值保留全局加权均值，但不能保证保留原始箱内逐步波动；这里的协方差与尾部估计针对压缩后的表示，不能声称与任意原始trace完全等价。

## 不均衡比率与hysteresis锚点

placement_replica_counts要求专家ID合法、所有逻辑专家至少一份，且同rank无重复专家。每个专家load按其replica数均分到放置rank，再计算每个时间箱的 `max(rank_load)/mean(rank_load)`；零总负载箱的比率记1。mean_ratio是按counts加权的比率平均，p95_ratio是按counts加权的nearest-rank分位数，不能与端到端请求p95混为一谈。

全零窗口不规划。没有已提交锚点（None/NaN）的第一个非零窗口可进入规划；否则令balance=1/mean_ratio，只要当前balance/已提交balance不高于relative阈值，或当前balance不高于absolute阈值，即通过gate。两个条件为OR，等于阈值也触发。

last_committed_mean_ratios来自真正提交成功的计划预测，不应在仅计算出候选或后台传输刚结束时覆盖。旧预测与当前统计的锚点、当前placement及采样代数需要一起保存；预测值不是提交后重新实测的平衡度。

## 风险、replica与受限LPT搜索

专家risk为mean加 `z_score*sqrt(variance)`，z_score由单侧标准正态quantile转换。分配到rank的方差还包括专家间covariance，并按replica数缩放；仅独立相加各专家方差会漏掉相关性。实现检查协方差shape、对称与对角一致，并只裁剪按浮点舍入容差解释的小负rank方差，不能将任意负方差强制置0继续优化。

FlashTree式replica搜索按风险排序分组，以当前greedy额外副本预算为中心探索邻域，beam去重并限宽；每专家副本不超过rank数，总slots必须满足等容量布局。incremental候选从当前副本数向候选移动，并显式保留当前副本数作为基线。每层最大副本数变化还受总冗余与rank_transfer_limit限制；没有冗余也可以改变专家位置，但不能凭空增加专家槽。

LPT按每副本风险递减放置，选择加入该专家后rank风险最小的合法rank，风险相同用rank ID稳定打破平局。容量、同rank不能重复专家、incoming计数和可行source分配同时参与约束。每个局部放置都需能找到符合source及跨节点预算的迁移，不能等最后才发现计划无源。

placement_search_backtrack_limit限制可行分支的替代次数：首次可行选择免费，接受另一可行选择才消耗回溯。搜索返回None表示本次有界搜索未找到可接受计划，不能据此证明整个拓扑在数学上无解，也不能据此宣称目标硬件不支持。

## transfer limit按层、按方向计算

rank_transfer_limit分别约束每个rank每层的outgoing和incoming专家数；-1不限制，0非法。cross_node_transfer_limit分别约束每个node每层跨节点outgoing和incoming；-1不限制，0禁止跨节点迁移，但仍可有同节点重排。它们不是整个模型累计budget、传输字节上限或实时带宽限速器。

有预算时source分配搜索会尝试更低总跨节点次数的可行方案，必要时重分配较早需求，不能只为每个目的槽局部挑最近源。无限预算有单独的快速路径，优先同节点、source使用次数和rank ID，不把有限预算搜索的全局最小性质无条件套给所有分支。

保留在同rank的专家保持原slot；新专家按ID填空槽。最终source_rank_ids/source_slot_ids索引当前placement，而不是尚未提交的新placement。planner验证每个source确实拥有目标专家，并验证retained slot、专家覆盖、无rank内重复与每层迁移budget。

## 候选接受规则与预测字段

plan_layer拒绝mean或p95不均衡任一退化的候选，从其余候选选预测mean最低者；mean差不超过内部1e-9容差时，按跨节点迁移数、同节点远程迁移数、目标专家及source坐标稳定排序。最优候选仍等于旧placement时返回None，不将no-op当作真实迁移。

plan_rebalance先按当前mean不均衡、相对已提交锚点恶化和layer ID排序合资格层。未接受候选的层保留原placement、同rank同slot source，并令predicted_mean_ratios为NaN；changed层必须是有限且不小于1的预测值。NaN表示没有接受的变更，不应写成0、真实测量缺失值或“该层已经均衡”的保证。

imbalance_ratios保存每层规划前后mean/p95四项。Native入口的predicted_imbalance_summary是逐层这些比率的平均，不是按token或请求数加权的端到端性能指标。真正commit后才允许保存对应预测anchor，随后仍用真实路由和输出验证收益。

## PP阶段分片与持久planner子进程

plan_sharded_rebalance要求CPU group内所有rank使用相同输入/config，group只包含当前PP stage的EPLB ranks。层按rank序号round-robin分配；各rank只规划自己拥有的层，空分片仍参加错误同步和gather，不设单一coordinator汇总全部计算。

先用MIN all-reduce同步本地规划是否成功，任一rank失败时所有rank停止结果gather；成功后对整数计划和浮点统计分别padding/gather，再按原round-robin层序还原，所有rank获得完整计划并validate_plan。局部planner成功不等于整个stage计划可提交。

每个policy复用独立Python子进程，通过socket与np.savez数组交换，np.load禁止pickle；配置与sample_counts经JSON metadata传递。子进程将四类BLAS/OpenMP线程环境设1，约束仅作用于其启动环境，不是改全局服务配置。进程异常/连接错误会停止并清理旧planner，算法ValueError与其他远端错误分别传为ValueError或RuntimeError。

停止helper先关闭连接，等待1秒，超时terminate再等1秒，仍未退出则kill；该关闭等待不等于每次规划请求有1秒deadline，接收路径未在此设置solve超时。helper存在也不证明所有worker退出调用链已闭合；排查残留进程时仍需核对生命周期入口。

## 参数与Agent调优顺序

| 参数 | 固定源码缺省与门禁 |
| --- | --- |
| load_window_bins | 64；允许2–256 |
| load_risk_quantile | 0.75；严格大于0.5且小于1 |
| relative/absolute_balance_threshold | 0.95/0.90；均大于0且不大于1 |
| rank/cross_node_transfer_limit | 均-1；rank须-1或正数，node可为0 |
| replica_search_num_stages / radius / beam_size | 4/8/64；范围1–8、0–32、1–128 |
| placement_search_backtrack_limit | 32；允许0–64 |

先确认logical统计、sum/mean、counts、phase和映射代数，再核对group/topology及源坐标，最后才比较风险、搜索预算和迁移门槛。记录规划CPU耗时、候选/回溯与迁移数量、foreground等待、真实热点、输出及端到端性能；增大beam/radius/backtrack不是无成本或必然更优的默认规则。

两份UT定义了weighted bins、单样本协方差、nearest-rank p95、反相关专家、负方差拒绝、预算可行性/回溯、shard gather、错误同步、显式source与NaN约束等断言，本次没有执行测试或planner。硬件、模型、量化、HIXL和精度/性能的整项适用范围仍需独立证据，不能因CPU计划可构造而填写平台或verified。
