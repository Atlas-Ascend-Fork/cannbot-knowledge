---
type: API
title: MoE token 回收通信（torch_npu.npu_moe_distribute_combine）
description: torch_npu.npu_moe_distribute_combine：先进行reduce\_scatterv通信，再进行alltoallv通信，最后将接收的数据整合（乘权重再相加）。 回收顺序是先 ReduceScatterV，再 AlltoAllv，最后乘权重后求和。 限定同次Dispatch元数据、A2/A3及950DT组合，揭示shared_expert_x消费断层与未公开INT32分支。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_combine.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeCombineKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combine.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combineA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeCombineKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combine.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combineA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_moe_distribute_combine
---


# npu_moe_distribute_combine：V1回收、路由权重与通信量化

## 固定版本与数据流程

固定OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布dedc316708372c9a8bfde4527abd2a94b74840f5；TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。发布属于ascend_26_0_pt28组合，主线配套未知。发布列A2/A3，主线另列Ascend950系列（包含旧称Atlas A5）的DT，仅UB Memory，不推导950PR。

接口torch_npu.npu_moe_distribute_combine(expand_x,expert_ids,expand_idx,ep_send_counts,expert_scales,group_ep,ep_world_size,ep_rank_id,moe_expert_num,*,tp_send_counts=None,x_active_mask=None,activation_scale=None,weight_scale=None,group_list=None,expand_scales=None,shared_expert_x=None,group_tp="",tp_world_size=0,tp_rank_id=0,expert_shard_type=0,shared_expert_num=1,shared_expert_rank_num=0,global_bs=0,out_dtype=0,comm_quant_mode=0,group_list_type=0)返回一个Tensor。

它在受支持TP域做ReduceScatterV，再在EP域AllToAllV，按路由权重聚回原token。用于推理、Eager和静态图，必须接同版本[V1 Dispatch](npu_moe_distribute_dispatch.md)及实际专家计算。第三输入expand_idx不同于[V2](npu_moe_distribute_combine_v2.md)的assist；V1没有MXFP通信模式、算法选择或特殊专家参数，不套用较新模型/V2调用。

## 输入与反向路由映射

expand_x公开仅FP16/BF16 ND二维[max(tp_world_size,1)*A,H]、支持非连续，表示专家计算后数据；不是直接接Dispatch INT8再cast就完成专家与反量化。expert_ids为同次路由的INT32[BS,K]，普通ID在[0,E)、行内不重复；expert_scales为FP32[BS,K]路由权重，不能替换为动态反量化尺度或权重量化scale。

expand_idx=Dispatch.expand_idx，INT32[BS*K]；ep_send_counts=Dispatch.ep_recv_counts，tp_send_counts=Dispatch.tp_recv_counts。A3/950 EP counts公开形状[P*max(tp_world_size,1)*L]；A2分层为[E+2*G*K*server_num]，后部是Combine提前归约/通信偏移，server_num文档仅列2/4/8，样例单机1不据此扩成经过验证的全产品拓扑。

expand_scales是随Dispatch.expert_scales返回的对应不透明权重数据，A2参数段要求FP32[A]必传；A3/950不支持、保持None。文档通用例及A2测试却未传入，说明样例覆盖不能代替A2分层路径合同核验；不能自造全零或ones占位填补未知编码。

上述元数据元素可随产品、通信算法和软件版本变化，应同一次配套调用原样传递，不解析、重建或跨版本持久保存。它们不是跨平台的通用路由索引格式。业务可以按公开接收统计管理有效token，但不能把最大容量A内的未写区域全部视作有效数据。

## 产品、共享专家与通信组交集

E=moe_expert_num在1..512；P=ep_world_size；R=shared_expert_rank_num；E%(P-R)=0，本地MoE专家L=E/(P-R)，共享rank的L=1。EP rank在[0,P)、同组唯一；L>1时TP不支持。

|条件|A2两版|A3两版|主线950DT|
|--|--|--|--|
|P|16/32/64|8/16/32/64/128/144/256/288|2/4/8/16/32/64/128/144/256/288|
|H|1..7168且32倍数|仅7168|仅7168|
|BS|1..256|1..512|1..512|
|K|1..16且≤E|1..8且≤E|1..8且严格<E|
|TP|size=0、不支持|size0/1无TP、2有TP|不支持但明确传size1、rank0|
|共享专家|R=0，相关参数用默认|发布shared_expert_num仅1、主线0..4|shared_expert_num仅1|

完整Dispatch/专家计算/Combine组合应取各入口限制交集，不能因主线Dispatch的H段更宽而扩大本Combine仅7168的合同。A3的rank按DIE计，一物理卡双DIE。A3/950 shard仅0、共享rank排前；R非0时P%R=0。发布A3 R范围[0,P)，主线Combine却写[0,P-1)，Dispatch仍写[0,P)；保留差异，不自行放宽到边界P-1。

group_ep长度[1,128)。A3有效TP组长度[1,128)、与EP不同、TP rank为0/1且同组唯一；无TP rank0。发布A2 Eager空TP组、图模式TP组与EP相同；主线A2/950不用TP且通用文本要求组名不同，按产品与版本核对，不照搬发布图模板。

主线A3 x_active_mask可为BOOL[BS]且支持非连续，false表示不接收对应token；不同rank BS不同时必须全有效。发布A3及两版A2/主线950保留此参数，传None。shared_expert_num=0与R=0的组合还须对应实际部署，不能凭参数默认值推断多个共享专家的容量和路由均已落地。

各rank的组、P、E、TP规模、shard、共享数/R、global_bs保持一致；组、P、TP规模、shard/global_bs还须跨层及与Dispatch配套，发布还明确跨层E一致。专属EP/TP域内不放其他算子；A3同一超节点、不跨超节点，A2多机仅交换机组网、不支持双机直连。

## 共享分支的文档与消费断层

公开expert_scales段规定共享专家结果不乘路由系数、直接相加；功能公式却把shared_expert_x也乘expert_scales，应以参数分支语义区分，不把公式机械当作共享结果乘K次权重的配方。

主线A3文档为shared_expert_x补充本地共享专家路径：仅R=0时、dtype同expand_x，二维[BS,H]或三维前两轴乘积为BS、末轴H；A2/950仍不支持，发布则全列预留。两个版本Schema虽均有此参数，两版C++形参接收后没有传给ACLNN、没有随后执行add；两版GE转换器同样忽略它，生成GE接口无该输入，Meta函数签名甚至没有shared_expert_x。

因此不能仅据主线文档或Schema就宣称此固定实现已完成本地共享专家融合；显式共享输入的绑定、计算和图路径须另行验收，也不能在外部盲目补加以免未来版本重复相加。这与已有共享专家rank的通信归并是两个不同路径，后者的测试不验证前者。

## 通信量化与公开dtype范围

comm_quant_mode=0不做通信量化，2是内部INT8通信，外部expand_x和结果仍为FP16/BF16。A2模式2还需HCCL_INTRA_PCIE_ENABLE=1、HCCL_INTRA_ROCE_ENABLE=0、驱动≥25.0.RC1.1；A3及主线950要求tp_world_size≠2。不能将Dispatch.quant_mode、Combine.comm_quant_mode及MXFP枚举交换。

activation_scale、weight_scale、group_list、out_dtype、group_list_type仍是公开预留参数，保持默认。C++额外接受INT32 expand_x，out_dtype=0分配BF16、其他值分配FP16；但Meta无条件沿用expand_x dtype、公开文档与GE IR只列FP16/BF16。这个宽分支不是已公开的INT32/融合反量化合同，不能看到C++接受就把其作为优化入口或图支持证明。

## 容量、Buffer与结果

global_bs在各rank BS相同时可0或BS*P；不同时用max_bs*P，A2也允许256*P但不建议硬编码。C++把0展开为本地BS*P后传给ACLNN，不是跨rank求实际BS总和。文档MoE容量为G*min(L,K)，共享容量主线直接写global_bs*shared_expert_num/R、未解释0；发布则分0时BS*shared_expert_num/R与非0时G*shared_expert_num/R。不要在0分支直接推导零容量，应与配套Dispatch的实际输出描述共同核对。

HCCL_BUFFSIZE单位MB、默认200。A2普通路径至少2*(BS*P*min(L,K)*H*sizeof(uint16)+2MB)；A2 PCIe/非RoCE路径至少E*BS*(H*sizeof(dtype_x)+4*ceil(K/8)*8*sizeof(uint32))+4MB+100MB，且仅该路径取消普通L≤24约束。

发布A3与主线950要求BUFFSIZE≥2，且2^20*(BUFFSIZE-2)/2≥BS*2*(H+128)*(P*L+K+1)；发布A3 TP另至少A*(2*H+128)*2字节并列出hccl_buffer_size配置。主线A3改为2*(L*max_bs*P*Align512(Align32(2*H)+64)+(K+shared_expert_num)*max_bs*Align512(2*H))字节、至少2MB。原主线A3文字没有显式写MB换算，配置时按对应CANN的检查核对单位，不能把字节表达式直接当MB或跨版本混用公式。L均取MoE rank的本地专家数。

结果公开为连续ND[BS,H]、dtype同expand_x。C++只校验expand_x/expert_ids为二维及有限dtype，输出BS取expert_ids首轴、H取expand_x末轴，没有验证全部路由、容量、buffer或共享条件。Meta只建同shape/dtype空输出，不做这些条件验证；生成GE函数仅构建输入描述、attrs和一个输出节点，没有消费shared_expert_x或认证产品组合。

## 测试覆盖与实际验证

两版C++和A3/950测试均逐字节相同。该测试一个条件设备方法、要求16设备，只测FP16、EP8/TP2、共享rank1、BS8/H7168、K7=E7、通信量化默认0。950的TP2和K=E都与公开限制冲突，不作为950产品覆盖证明。参考还调用NPU routing，并自行构造内部metadata；它不是独立CPU标杆，也不授权模型按同样编码重建跨版本协议。

A2文件含V1与V2两个方法，V1仅FP16、EP16/无TP、BS8/H7168/K8/E16、默认非量化。声明的sharedExpertRankNum=1没有实际传给算子，实际仍默认R0；rank%8与loopback配置不证明16个独立设备的部署拓扑。它用纯参考重建路由、FP32加权求和后按输出dtype设置容差，没有验证真实Dispatch连接、A2 expand_scales必传路径、动态通信量化、主线mask或本地共享输入。

多进程文档样例只cast Dispatch INT8再调用，没有完整反量化和专家计算、独立参考或子进程退出码验收；图样例只用dynamic=False并打印结果，没有图/Eager数值对比。测试文件与示例的存在均不提升为实测。本次无上游执行、NPU/分布式/图/性能实验，无新增verified；真实复核应使用同次Dispatch元数据与专家结果，检查token身份、有效前缀和路由权重，再分别评估通信量化误差与端到端收益。

- [V2发布组合](../../guides/optimization/moe_dispatch_combine_v2_release_contract.md)
- [模型通信量化策略](../../optimizations/rules/moe_dispatch_combine_comm_quant.md)
- [Buffer错误观测](../../runbooks/runtime/moe_dispatch_combine_hccl_buffsize.md)
- [软件栈来源](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE token 回收通信：torch_npu.npu_moe_distribute_combine

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

先进行reduce\_scatterv通信，再进行alltoallv通信，最后将接收的数据整合（乘权重再相加）。

### 输入、输出与行为

回收顺序是先 ReduceScatterV，再 AlltoAllv，最后乘权重后求和。与 npu_moe_distribute_dispatch 配对，沿派发路径原路回收；不能将 v2 的配对协议静默混入此接口。

### 文档签名

```text
torch_npu.npu_moe_distribute_combine(expand_x, expert_ids, expand_idx, ep_send_counts, expert_scales, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, tp_send_counts=None, x_active_mask=None, activation_scale=None, weight_scale=None, group_list=None, expand_scales=None, shared_expert_x=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, global_bs=0, out_dtype=0, comm_quant_mode=0, group_list_type=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_combine.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeCombineKernelOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combine.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combineA2.py)（example）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeCombineKernelOpApi.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combine.py)（example）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combineA2.py)（example）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
