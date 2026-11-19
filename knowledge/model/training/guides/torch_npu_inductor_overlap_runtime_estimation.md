---
type: Guide
title: 计算通信重叠估时：NPU事件、合成分组与调度门槛
description: 解释overlap适配器的真实调用门槛、事件估时与GMM均衡group_list，区分缓存元数据、零占位值及端到端通信收益。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/overlap_scheduling.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/dvm_fusion_regions.py
  role: implementation
created_at: '2026-11-10T12:32:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 计算通信重叠估时：NPU事件、合成分组与调度门槛

## 安装适配器不等于每个图都运行调度

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`对上游Inductor计算通信overlap的估时与入口适配。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`无同路径`fx_passes/overlap_scheduling.py`，只记录准确tree差异，不否定其他通信优化。上游完整调度算法、跨rank对齐、HCCL运行库不在本卡范围；DVM fusion-region成本实现的本地公式补于后文，整卡保持draft、空平台，未运行任何上游、通信或设备实验。

`_load_backend()`在所选backend loader返回后安装patch_overlap_scheduling；patch用模块属性防止重复安装，替换上游的计算节点识别、benchmark、通信估时、收集及schedule入口。它把aten_distributed_optimizations的compute_estimator/collective_estimator设为benchmark，enable_fusion_regions和pre_bucketing_fsdp_collectives设为False。这里设置适配器和默认估时方式，没有单独证明上游overlap pass已经被触发，更不能把它与[Cube/Vector并行调度](../../inference/guides/optimization/torch_npu/torch_npu_parallel_scheduler_consumer_constraints.md)或[通信零拷贝](torch_npu_communication_buffers_and_zero_copy.md)当作同一个开关。

计算节点识别保留上游判断，额外纳入已注册的npu_grouped_matmul、npu_fused_matmul、FAv3前反向及其unsafe代理packet；缺失packet会剔除。名称被纳入只表示估时/调度识别，不认证所有重载参数或融合已实现。

## 确定性和analytical在入口直接拒绝

被包装的schedule_overlap_bucketing先绑定原函数参数/默认值，再检查：Inductor config.deterministic为真时直接NotImplementedError；compute_estimator或collective_estimator等于analytical也分别报错。即使另提供custom_runtime_estimation，只要这些入口条件仍成立，代码仍先报错，不能用“有自定义函数”跳过这个门槛。

这是该overlap适配入口的限制，不是整个TorchNPU后端不支持确定性的结论。调试时保留实际入口参数、加载后被设置的配置与堆栈；修改估时方式、关闭确定性或开启优化可能改变实验前提，不能仅以编译通过判定数值策略未变。

## 两类NPU事件测量有不同准备过程

通用do_bench要求NPU可用，先执行5次warmup再同步，测3次NPU start/end Event并同步end，返回torch.median得到的毫秒值。它用于本适配层的GMM等可调用对象估时，不是Host wall-clock编译耗时。

通信专用helper先把FakeTensor按shape、stride、dtype、device合成真实输入，非Tensor的SymInt用optimization_hint及配置fallback具体化。缺少Tensor维度/stride hint则报错，不在此假设真实动态值已知。它同步后先执行一次通信并对结果Tensor调用wait_tensor，再同步；计时循环也在end Event前等待通信结果，返回中位毫秒值。所选collective estimator调用它时传nruns=5；其他消费者若另给次数应分别核对。不可用NPU时这个helper返回None，与通用do_bench的报错不同。

因此估时准备会真实申请输入、执行设备算子/collective并同步，不能当成纯静态成本模型或“编译阶段不需通信”。事件时间反映这些合成参数与等待位置下的测量，不能直接代替原模型的通信竞争、真实rank顺序、Host开销和训练步吞吐。

## GMM用均衡group_list，不能代表真实MoE偏斜

GMM专用benchmark在自定义估时返回非None时直接采用它；Fake参数提取失败返回0.0/无key。正常路径按Tensor元数据物化随机输入；遇到kwargs中的同一个group_list对象时，尝试构造有效均衡数据：

- group_type=0用首个x的第0维总量，group_type=2用其最后一维总量；group_type=-1不在此合成分组。
- 将总量按组数商余分摊，前若干组多1。group_list_type=0生成累积末端偏移，1生成每组计数，2且原Tensor为二维时生成[id,count]。
- 不满足该helper的shape、组数、类型或参数条件时返回None，随后走普通随机Tensor物化，并未由本helper保证随机值是所有GMM形式的合法分组。

这里是用于估时的合成均衡负载，既没有读取真实token路由偏斜，也不是把模型中的group_list永久改写成均衡数据。对于MoE，均衡下的估时不能自动代表真实专家分布；应保留分布、空专家、group_type/编码与端到端执行对照。

## 局部缓存与零值不能被误读

GMM key在本函数中由target字符串及各Tensor的shape、stride、dtype拼成，不加入Tensor内容，也未追加group_type等非Tensor标量/设备身份字段。命中上游时间缓存即复用该数值；Tensor维度/stride无法具体化时可能以该key返回0.0。不能把这层key当作真实group_list内容、跨设备负载或所有属性完整身份，也不能将0当成“该算子无成本”。上游缓存的全局作用域与其他外层隔离不在本卡范围。

通信估时先尊重自定义结果，再尝试benchmark；缺结果则返回0.0。roofline估时也固定返回0.0，源码注释将其用于后续benchmark/跨rank对齐前的占位。这里未核验上游全流程一定完成替换，诊断应检查最终估时记录和真实时间线，不能把占位当作零通信成本证明。

## DVM fusion-region仍是独立的可选成本模型

若收集入口收到enable_fusion_regions=True，包装器先将该参数置False调用上游估时，再用build_dvm_fusion_regions与estimate_dvm_fused_node_costs的结果更新节点成本。它改变的是调度用估计，不代表这段代码已经完成实际DVM融合或验证预测命中；该预测实现的静态公式与边界见后文，外部DVM生成和运行仍独立验收。默认安装保持False，不能从主线存在这条分支推导所有图都采用DVM融合区估时。

验收时分别保存配置加载时机、schedule是否触发、估时来源/缓存key、真实与合成分组差异、最终跨rank成本和实际计算通信时间线。单节点事件变快、bucket顺序改变或估时缓存命中，都不足以证明真实训练重叠和端到端收益；本卡没有新增verified。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/overlap_scheduling.py)（primary）：定向范围21–133, 143–350, 397–523。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）：定向范围455–474。

## DVM区域候选由注册与连续span筛选

依据同主线dvm_fusion_regions.py的363行，说明本地融合区域预测；发布f3ecfe4同路径Git树为空，只记录路径差异。没有导入DVM registry、调用rule、构建FakeTensor或执行设备估时，平台适用性及验证状态不由这些源码推导；上游实际融合、代码生成和通信对齐不因本文件完整读取而获得资格。

候选仅call_function，排除_c10d_functional命名空间、明确列出的mm/bmm/addmm/sum.dim_IntList/sum.default/amax/amin，以及被延迟读取的上游is_compute_node判为计算的节点。DVM_OP_REGISTRY导入任意Exception时返回空字典，所有节点遂不入选；命中注册项后取其rule(node)的bool，但没有在这层捕获rule抛错。注册和谓词参与资格，不是仅凭轻量算子名字就必定融合。

沿FX顺序只在连续候选span内做并查集：存在输入边且边可融合才合并连通分量，遇非候选节点就flush，不能跨任意重计算/通信节点建立一个大区域。每个分量至少两个非view节点才建立区域，同区域各Node映射到同一OrderedSet；构建函数不修改FX图，也不发射融合Kernel。

## view和广播边的检查强度

view识别要求OpOverload、target.is_view且namespace为aten/prims；只要边一端为view就直接允许，不在这个helper再次核完整shape或别名。非view两端的meta.val分别必须经pytree只找到一个Tensor，多Tensor结果不自动选第一项。

shape中的SymInt必须有hint，取其hint并int化；没有或转换抛异常即不给边资格。相等shape可以连接，其他情况按末尾对齐逐个遍历目标shape，源维为1或等于目标维则通过。该本地广播helper没有额外拒绝“源rank多于目标且高维非1”，因此不能改写成完整等价的torch广播合法性校验；真实DVM emitter仍有独立约束。

## 成本公式仅计区域边界字节

对每个区域Node，外部输入只收all_input_nodes中不在区域且meta.val非None的值；只要有区域外用户，就将本节点val计为一次外部输出。pytree遍历其中所有Tensor，以shape各维（SymInt取hint）乘dtype.itemsize计字节，没有按Storage/别名或不同边跨节点去重；同一个外部Tensor被区域内多个节点消费可能重复计入。它也不是按stride、实际访问子集或压缩格式计算总线事务。

传输毫秒估计为bytes / (bandwidth × 1024³ / 1000)。TORCH_NPU_DVM_FUSION_REGION_BW_GBPS可用float正数覆盖，未配、非正数或无法解析则回到2000.0；ValueError会记warning，非正值直接回退。变量名虽写GBPS，表达式用1024³。2000来自源码本地roofline常量及910B3注释，不是每次查询设备的实测带宽，不推成全部产品都具相同值。

字节数为0直接返回0.0；带宽换算后非finite或非正则返回None（例如正无穷先被参数入口接受，实际估计时仍跳过）。缺hint或字节计算异常也返回None。该公式没有算术FLOPs、launch、同步、缓存命中、带宽竞争或实际通信成本，不能单用它预测所有模型的端到端重叠收益。

## 0与缺省Meta不代表真实零开销

某节点没有被收集到外部输入或输出时成本写0，即使因缺meta.val而遗漏边界也不会由此层补齐。边界字节无法估计的节点则不写costs，留待外层估时结果；整个字典是逐节点覆盖项，不是每个区域一个已测Kernel耗时。区域按OrderedSet对象id去重，不按集合内容或独立运行缓存key去重。

TRACE只有环境字符串严格为'1'时启用；此时可记录被跳过节点及已估计区域，并用trace_structured发npu_dvm_fusion_region_estimations JSON诊断。诊断记录不执行数值或设备验收。接入时保留hint、边界Meta、带宽配置及实际外层最终成本，对照真实DVM融合结果与时间线；不要把内部0、候选区域或诊断artifact当作已实现的融合和提速。
