---
type: Guide
title: vLLM Ascend MRv1 EPLB策略：Default、FlashLB、Swift与迁移时间轴
description: 区分逻辑热点、专家副本和物理槽，提炼Default贪心、FlashLB风险/窗口/重排匹配及Swift通信约束的真实目标与门禁，并追踪EplbUpdator的采集、规划、异步搬运和映射更新，避免把预测均衡当实际提交或收益。
aliases:
- DefaultEplb.rebalance_experts
- FlashLB.rebalance_experts
- FlashTree.optimize_balanceness
- SwiftBalanceEplb.rebalance_experts
- EplbUpdator.forward_before
- generate_log2phy_map
tags:
- task.implementation
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/eplb_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_default_eplb.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_flashlb.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_swift_balancer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/eplb_updator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_factory.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/eplb/core/policy/policy_abstract.py
  role: constraint
created_at: '2026-11-03T06:12:03Z'
updated_at: '2026-11-03T06:12:03Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MRv1 EPLB策略：Default、FlashLB、Swift与迁移时间轴

## 先分清策略返回值和真正提交

固定Main ceac1a2，完整阅读本卡5份策略/映射/更新实现、factory与abstract两份已绑定来源，distributed/eplb的空说明包作skip。三种算法都属于旧core MRv1策略体系，不与MRv2 distributed policy的default/stair混用。factory为0 Random、1 Default、2 Swift、3 FlashLB；未知值可告警回落Random，type3另warm_up并不复用返回实例。Numba/SciPy/TorchNPU依赖均只静态阅读，没有导入/JIT/执行策略、通信或硬件测试。

策略实际返回(changed, per_layer_priority, placement)。[模型权重与提交合同](vllm_ascend_eplb_model_weight_contract.md)已指出当前旧worker.do_update丢弃前两项，并在预测日志后做局部校验/回滚；不能只看到changed或更低热点就认为策略优先级已被执行、权重已迁移或性能已提升。本卡补算法内部和EplbUpdator时间轴，保持原有来源owner与状态边界。

## 初始化映射要与checkpoint物理槽一致

无shared mix时，generate_global_placement先排全部逻辑专家0..N-1，再附冗余副本0..R-1按N取模，最后按EP reshape，要求(N+R)%EP=0。扁平位置是全局物理expert ID，不是随意把每rank最后一个专家重复填满。shared mix另按array_split分组、从后rank补冗余并加共享专家，不能与普通checkpoint布局互换。

静态线性expert map按(EP size,EP rank,N)缓存后clone返回，尝试移到当前NPU的异常会被忽略；不能因返回Tensor就保证device一致。动态初始化建立逻辑→本地slot表；同rank重复逻辑ID会覆盖同一索引，合法placement须提前保证唯一。

generate_log2phy_map按每rank有效槽数形成全局物理offset，默认选择ep_rank%副本数；tp_size>1则用(tp_rank+dp_like_rank+logical_id)%副本数分散。它以rank0有效槽数作为所有rank跨度，隐含均匀槽容量；逻辑ID还被用于长度为已出现专家数的scatter，要求ID域完整连续。JSON expert file在layer_id==moe_layer_count时为MTP/EAGLE返回None但沿第0层统计物理数，超界才显式报错；负层号和文件结构并未在此完整验证。

## 三种算法优化的对象不同

| 策略 | 负载表达 | 放置与触发 |
| --- | --- | --- |
| Default | 把物理副本heat按逻辑ID求和，以平均分摊估计每副本工作量 | 逐次复制最热平均负载专家，再按box负载贪心装卡；总层峰值和预测下降超过5%才changed |
| FlashLB | 多stage逻辑热点先加1平滑，使用均值、方差及协方差，risk=mu+z*std | 深度/邻域搜索副本分配、LPT部署，再用Hungarian匹配与槽内保留减少移动；按预测平均/峰值改善筛层 |
| Swift | 聚合逻辑热度并按副本数分摊，带rank间迁移次数约束 | 先重放冗余槽、再最多100次热冷rank交换；按层不均衡门禁和全局5%预测门禁输出 |

三者都依赖有限、非负且与placement同形的观测、有效rank数、连续逻辑ID和可容纳的副本数，不是任意表的schema修复器。负ID、缺专家、同rank重复、容量不足不能交由NumPy负索引或best_dev=-1“回退”。

Default运行入口用original_compute_balanced_pack_redundancy：先把重复副本分放到各box，再放原专家，避免同rank重复并尽量保留原槽。文件内另一个compute_balanced_pack_redundancy和无冗余compute_balanced_pack是不同helper，不是当前入口统一调用的算法。入口只拒绝冗余总数超过rank数，没有证明每个逻辑专家最终副本数必可分到互异rank；无可用box时min_box_index仍为-1是需要输入约束/校验覆盖的静态点。层优先级按after/before升序，零负载分母无独立guard。

## FlashLB：统计窗口、风险和迁移匹配

缺省z为正态分布75%分位、depth4、width8、sample_size64。min_max每次给当前(mu+z*sqrt(var))/replicas最大的专家加副本；max_delta按这项再除(replicas+1)比较，percentage按风险比例配额及最大余数补齐，零总负载均摊。make_replica缺省走min_max，不能把文件中三种helper都说成同时启用。

FlashTree用样本无偏协方差(T-1分母)，T≤1方差/协方差置0；LPT按mu/replicas降序，在不满且不含同专家的设备上选择加入后risk最小的位置。设备variance包括专家variance/replicas²及成对covariance项，不能用独立专家模型抹掉相关性。没有通用clamp负variance或非法replicas，有限域与可放置性要先验证。

score对每个时间片计算(max_device_load*D+1e-2)/(total_load+1e-2)再平均，越低越均衡；其倒数是average_to_peak。零负载的score稳定化项、先加1热点、按窗口分组求和都会改变统计，不能把数值直接当原始token计数或真实耗时。

register_hotness将physical slot heat按当前逻辑ID np.add.at合并，热度加1后写环形窗口。rebalance把观测stage数设为max_observation_window，sample_size只会向下取min，并把最近数据压成不超过该采样数的分组和。类保存窗口/当前placement/history；改变层数、专家数或窗口长度的重新初始化边界没有完整guard，不能跨不同模型直接复用对象。sliding/incremental统计helper虽已实现，本入口仍按FlashTree重新compute_statistics，不宣称已由增量公式减少所有计算。

首次history=0必更新；通常average_to_peak低于过去的0.9倍或绝对0.85才重新优化；通信组world_size<32后阈值改0.95/0.9，查询组异常则沿旧阈值。候选按改善降序，只取正改善并受可选层数上限；置history不等于设备已提交。候选含-1时回退原deployment，但候选replicas/score的其他状态仍需和最终表一起核验，不能把fallback理解成完整事务回滚。

Hungarian先按每行保留专家多重集合交集匹配目标rank，再在rank内尽量保留原slot；目标是减少逻辑搬迁项，不包含模型scale字节数、实际链路或端到端迁移时延成本。warm_up构造58层、32×9槽、256专家和100stage随机heat运行另一FlashLB实例，用于触发依赖/JIT预热；这不是生产工作负载基准。

## Swift：局部通信约束不等于任意拓扑感知

Swift构造直接读取torch.npu.device_count作为每host die数，num_nodes=num_ranks//die_count；node_redundant按连续rank分段，每段独立重放副本，不能据此推断异构节点/非连续rank拓扑已适配。默认node_redundant=False做全局重放。

重复槽按slot优先、rank次序扫描，第一次出现的逻辑专家保留为原槽，其后为可改冗余槽。副本分配中实际更新式是old_weight*(current_redundancy+1)/(current_redundancy+2)，current_redundancy=已有新增数+1；不要自行替成另一个“理想均分”公式。随后以估计权重放入未满且不含该专家的低负载rank，默认每发送/接收rank对num_max_com=1；未填槽的补充过程另行重算权重并补放，不宣称所有补充都继续受相同pair上限。

交换避免同rank重复及已接收/移动专家，每次考察降低当前峰值的交换，默认最多100次；swap_threshold取第0层平均负载的1%，其他层也用这一个阈值。层初始max/avg<1.01跳过，平均负载近0时局部imbalance为1；最终after_swap_imbalance也使用第0层平均负载，不能概括成每层独立归一。改变模型层间负载差异时，应检查该启发式而非只调全局5%门槛。

## Updator把观测、规划、搬运分成多轮forward

设H=heat collection interval、A=algorithm interval、L=本地MoE层数。H-1轮末汇聚heat并planner_q.put唤醒进程；H+A-1轮开始阻塞取block_update_q结果；H+A到H+A+L-1每轮forward_before弹一个层计划、设置log2phy、构建异步D2D任务。forward_end在非记录模式下才调用update_expert_map_and_weight；具体wait/commit由loader合同负责，不是这里的队列pop已经完成提交。

热度沿dynamic EPLB组all_gather再.cpu，type3多stage会permute(2,0,1,3)后写shared_dict。H阶段计数受eplb_heat_collection_status控制，进入后续阶段后即使不收集也继续推进；周期结束时可导出expert_maps、清负载、计数归0。环境缺VLLM_ALLOW_EXPERT_LOAD_COLLECTING或False时num_expert_load_gather沿H并停periodic flag，不能认为所有版本都固定10次。

有expert_map_record_path时此处跳过forward_end实际映射/权重更新，而在周期结束导出表，属于观测/记录模式，不能用它验证迁移后模型输出。warm_up_eplb向组内其他rank成对isend/irecv同一个单元素buffer并wait，不是全模型迁移预热或已验证无alias通信；shutdown直接terminate/join子进程，没有一般在途事务drain协议。连续周期、进程异常、计划长度不足、层数/PP编号、真实weight/scale及graph引用仍按迁移主合同验收。

性能Agent分别记录观测窗口、原/副本逻辑热度、预测score、有效最终placement、移动字节/链路、foreground等待、commit/lookup代数与模型输出，再做端到端吞吐/延迟比较；本次没有运行任何策略、JIT或通信，也没有写入verified。
