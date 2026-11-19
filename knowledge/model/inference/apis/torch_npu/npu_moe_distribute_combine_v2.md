---
type: API
title: MoE v2 派发与回收配对（torch_npu.npu_moe_distribute_combine_v2）
description: torch_npu.npu_moe_distribute_combine_v2：MoE v2 派发与回收配对。需与torch_npu.npu_moe_distribute_dispatch_v2配套使用，相当于按npu_moe_distribute_dispatch_v2算子收集数据的路径原路返回。 区分发布与主线共享/特殊专家、950DT MX通信、元数据、预归约后端要求及测试缺口。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_combine_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeCombineKernelV2OpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combine_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combineA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeCombineKernelV2OpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combine_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combineA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_moe_distribute_combine_v2
---


# npu_moe_distribute_combine_v2：版本化回收与通信量化

## 版本与范围

前面的基础段依据ascend_26_0_pt28发布来源；后文完整补充主线950DT、预归约开关、共享与图转换差异。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_distribute_combine_v2(expand_x, expert_ids, assist_info_for_combine, ep_send_counts, expert_scales, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, tp_send_counts=None, x_active_mask=None, expand_scales=None, shared_expert_x=None, elastic_info=None, ori_x=None, const_expert_alpha_1=None, const_expert_alpha_2=None, const_expert_v=None, performance_info=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, global_bs=0, comm_quant_mode=0, comm_alg="", zero_expert_num=0, copy_expert_num=0, const_expert_num=0) -> Tensor
```

接收专家计算后的 expand_x，先在适用 TP 域 ReduceScatterV，再通过 EP AllToAllV 返回原路由位置并按 expert_scales 加权求和，返回 FP16/BF16 的 (BS,H) Tensor。dispatch 与 combine 之间仍需专家计算，不是两个算子直接相接即可完成 MoE。

## 参数与组合限制

- expand_x 为 ND、FP16/BF16，shape=(max(tp_world_size,1)*A,H)；不能把 dispatch 的 INT8 输出不经匹配专家/量化处理直接作为本输入。
- expert_ids 与 dispatch 相同；assist_info_for_combine、ep_send_counts、tp_send_counts 分别接收对应 dispatch 的 assist_info_for_combine、ep_recv_counts、tp_recv_counts。内部元素可能随平台/算法/版本变化，必须按同一次匹配调用原样传递。
- expert_scales 是 FP32(BS,K) 的路由权重；A2 的 expand_scales 是必需的对应 dispatch 输出，A3 hierarchy 才支持相应 expand_scales 路径。共享专家、零/拷贝/常量专家只按各自平台和算法约束启用。
- comm_quant_mode=2 的 A2 路径仅支持 hierarchy（或对应旧环境配置）且驱动≥25.0.RC1.1；A3 路径要求 tp_world_size≠2。默认 0 不通信量化，此枚举不能与 dispatch.quant_mode 或主线 MXFP 模式混用。
- 图模式限静态图。组与拓扑、所有 rank 一致性、缓冲区及算法组合见发布版 Guide；本卡不把较新的模型代码调用提升为此发布版的通用支持。

## 验证与模型关联

按全局 token/专家身份核对归并、权重与精度，检查 dispatch 辅助 Tensor 的配套关系；对通信量化单独比较误差和收益。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L640)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [发布版通信组合与容量检查](../../guides/optimization/moe_dispatch_combine_v2_release_contract.md)
- [模型路径选择](../../concepts/techniques/moe_dispatch_combine_v2.md)

## 固定版本、图模式与新增Schema参数

本节完整核对OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布dedc316708372c9a8bfde4527abd2a94b74840f5，以及TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。发布配套为ascend_26_0_pt28，主线配套未知；主线950仅Ascend950系列（包含旧称Atlas A5）的DT、仅UB Memory，不推导PR。

主线实际Schema在文档原型末尾还增加enable_pre_reduce=True，发布没有该参数。主线Eager优先调用ACLNN V6并透传此开关；回退V4/V3/V2都要求True，显式False会要求升级到具备V6符号的CANN。开关名称不构成端到端性能收益证明，不按某个CANN大版本号猜测符号可用性。

主线TorchAir转换器及生成GE接口也新增enable_pre_reduce布尔属性，发布均无；图转换层没有同样按ACLNN V6符号拒绝False。它只证明节点可构建，不认证实际图后端支持，Eager与图须分别验收。

## 配套数据、路由权重与特殊专家

expand_x公开为专家计算后的FP16/BF16二维ND[max(TP,1)*A,H]，支持非连续；返回连续ND[BS,H]、dtype同expand_x。Dispatch的INT8/FP8/FP4通信结果应先经过正确尺度处理和实际专家计算，不能直接cast就当作完整MoE。Combine内部comm_quant_mode与Dispatch输出量化枚举也不同。

expert_ids为同次Dispatch的INT32[BS,K]，行内ID不重复；assist_info_for_combine、ep_send_counts、tp_send_counts分别接对应Dispatch的assist、ep_recv_counts、tp_recv_counts。元数据内部编码可随产品、算法、版本变化，只原样传递。Dispatch实际可能分配max(BS*K,A*128)而非恰好A*128，不据Combine文档形状自行裁剪或重建，更不以V1.expand_idx替代。

expert_scales是FP32[BS,K]路由权重，A2/A3必选；主线950允许空Tensor或有效二维Tensor，空Tensor与None不同，Schema该项不是Optional。共享专家结果按参数段不乘路由权重、直接相加；功能公式却把共享结果也乘expert_scales，不能机械生成共享输出乘K次权重的配方。

特殊专家沿用[Dispatch分段](npu_moe_distribute_dispatch_v2.md)：普通、零、拷贝、常量依次占互不重叠的区间。主线Combine的copy/const ID段却都从E开始，与零专家区间及Dispatch不一致；发布文档区间正确，不据该主线文字重新编号。每类数量非负且小于2^31-1、总数严格小于2^31-1，K不得超过专家总数。

零专家产生0；拷贝产生ori_x；常量产生alpha1*ori_x+alpha2*const_v，再按路由合并。拷贝/常量非0须传同dtype的ND ori_x[BS,H]；常量还须传alpha1/alpha2/const_v各[V,H]，支持非连续。主线A2全部特殊专家和ori_x都标为不支持；发布A2 fullmesh实验支持零/拷贝、拷贝需ori_x，hierarchy不支持、常量两路径不支持。不能从主线通用函数形参恢复发布实验合同。

## 本地共享输入与共享rank分别核对

主线中文及发布均把shared_expert_x限定在R=shared_expert_rank_num为0时使用，英文主线却写R非0，保留冲突。它为与expand_x同dtype的二维[BS,H]或三维前两轴乘积为BS、末轴H；A2不支持，主线另把该本地共享输入范围补到950。

V2两版C++确实把shared_expert_x传给各ACLNN后端，GE转换器及生成接口也保留该输入，Meta有该形参。这与V1消费断层不同，但“参数已透传”仍不等于所有共享组合都已验证，也不据英文一行启用与中文相反的R条件。

独立的共享rank部署为S在0..4、R在[0,P)，R非0须S>0且R%S=0、shard0排前。普通专家E被P-R整除，L=E/(P-R)，共享rank L1，L>1时TP不支持；还须取配套Dispatch的真实容量及分组交集。elastic_info仍公开预留None，不因代码可透传就认证弹性缩容。

## 产品、算法与mask的版本交集

|约束|发布A2/A3|主线变化|
|--|--|--|
|A2 fullmesh P|2/3/4/5/6/7/8/16/32/64/128/256|Combine中英文均缩到16/32/64/128/256，Dispatch仍有小规模，组合不能只看一端|
|A2 hierarchy P/H/BS|P16/32/64；HDK≥25.0.RC1.1时H≤10240且32倍数、BS≤512|H条款保留，BS统一段改≤256|
|A2 fullmesh H/BS|H≤7168且32倍数、BS≤256|不从宽包装INT32推导新输入合同|
|A3 P/H/BS|P2..768、H1024..8192；默认BS≤512、hierarchy≤256|文档算法段改为不支持自选comm_alg，仅默认；EP/BS段仍残留hierarchy文字|
|950 P/H/BS|发布未列|P2..1024、H1024..8192、BS≤512|
|普通E及L*P|E≤1024，A3 L*P≤2048；hierarchy E≤512|950中文E≤2048/L*P≤4096，英文仍通用1024/2048|

K一般1..16且不超过普通加特殊专家总数，还要取配套Dispatch模板的更小上限。A2无TP、size/rank默认0；A3 size0/1无TP、2有TP，启用时rank0/1且同域唯一、EP/TP域名不同；950无TP，Combine参数段传默认0。各EP rank在[0,P)、同组唯一，A3按DIE计数。

A2 fullmesh mask发布支持实验二维[BS,K]，主线仅一维[BS]；A2 hierarchy不支持。A3/950支持一维或二维BOOL ND、可非连续；一维true须连续排在false前，二维按token/专家路由屏蔽，整行false表示该token不通信。不同rank BS不同时必须全部有效。各算法额外禁mask条件仍需取与Dispatch交集。

发布A3 Combine只列""和hierarchy，而Dispatch有fullmesh_v1/v2等名字；主线Combine comm_alg段为不支持、用默认，英文该处还误写TP不支持和数值0。不能把Dispatch的算法字符串逐字复制给Combine，也不能给字符串参数传0。发布A3 hierarchy只TP1/无共享，并禁二维mask/特殊专家/弹性缩容/性能打点；不从主线残留EP范围推导其仍可用。

expand_scales为对应Dispatch输出，A2参数段要求FP32[A]必传，发布A3 hierarchy也要求、默认算法不支持；主线A3/950全部标为不支持None，尽管主线950 Dispatch允许expert_scales产生此输出。两端扩展不同步时不能据单端支持认证闭环。发布/主线通用样例及A2测试未传该项，不代表已验证必传分层路径。

## 通信量化、输出与实现宽分支

A2 comm_quant_mode仅0/2，2需hierarchy或对应旧PCIe/非RoCE环境及驱动≥25.0.RC1.1；A3 2还要求TP≠2。主线950另列3=MX E5M2、4=MX E4M3；这是通信量化表的类型，公开API结果仍FP16/BF16，不能把内部传输dtype当成对外返回FP8的保证。

两版C++额外接受INT32 expand_x并分配BF16结果，但Meta无条件保持expand_x dtype；GE IR也列INT32输入且结果仅FP16/BF16。公开文档没有给出完整INT32输入、尺度或融合反量化协议，这些宽分支不能当作可直接移植的INT32专家输出优化。返回shape的BS由expert_ids首轴、H由expand_x末轴取得，包装仅检查两输入2D及dtype，不验证全部容量/ID/分组/连续性或产品条件。

V2去掉V1三个预留公开参数，但C++仍给ACLNN传三个nulltensor，GE raw也显式插入activation_scale/weight_scale/group_list空槽，以适配底层原型。不能删这些槽后按顺序重连后续输入。主线对elastic_info、ori_x、常量三Tensor、performance_info缺省均留空描述，发布缺省时没有同样占位；保留图版本差异，节点构造不替代后端验证。

发布后端按V4→V3→V2选择，主线前加V6。performance_info仅V4/V6透传，V3显式拒绝；V2回退只拒绝elastic/特殊专家且不透传打点，不认为此时有有效计时。打点为INT64[P]、微秒、记录等待数据的通信时间，调用会累加、开始记录前需清零；不是完整算子/模型时延。

## 容量、Buffer与通信组

global_bs相同BS可0或BS*P，不同BS用max_bs*P；包装把0展开为本地BS*P传给后端。A为容量而非真实token数，MoE容量至少G*min(L,K)，共享文档写BS*P*S/R，实际应与Dispatch的ceil分组分配及显式global_bs共同核对。未初始化尾部不参与业务或精度比较。

各rank、两接口的组/P/E/TP/shard/共享/global_bs保持一致，组/拓扑/global_bs等还须跨层一致。专属EP/TP域不放其他算子；A3同超节点、A2多机只交换机组网、不支持双机直连。group_ep长度[1,128)；发布A2图模式TP组名等于EP，Eager默认，A3有效TP域名与EP不同。

HCCL_BUFFSIZE默认200MB，按具体版本的字节预算换算。令F=H*sizeof(dtype_x)+4*Align8(K)*sizeof(uint32)：A2发布hierarchy至少(E+P/4)*Align512(max_bs*F)+8MB，主线改E*BS*F+4MB+100MB，不能混用；fullmesh均至少2*(BS*P*min(L,K)*H*sizeof(uint16)+2MB)。旧环境变量只在comm_alg=""时选择算法，显式算法覆盖旧开关；hierarchy不再要求普通本地专家上限24。

A3 EP预算为2*(L*max_bs*P*Align512(Align32(2H)+64)+(K+S)*max_bs*Align512(2H))、至少2MB；TP为2*A*(Align512(Align32(2H)+44)+Align512(2H))。950 EP在该式上+10MB。Combine这里+64与主线中文Dispatch的+44/480Align512不同，应同时满足配套两端及实际后端要求，不只复制一端；Align480/480Align512的定义为ceil(x/480)*512，不是480倍Align512。发布A3 hierarchy还限定仅通过HCCL_BUFFSIZE环境配置，不把其他算法hccl_buffer_size入口直接套入。

## 测试证明限度

两版核心V2测试377行逐字节相同，与已全文复核的V1测试完整98物理行差异已核对。测试调用多传elastic_info，但父进程方法仍按V1旧列表解包，参数数量不一致；即使继续修正，子进程直接对elastic_info列表.npu()也不成立。参考沿用V1生成的短idx作为assist，并非真实Dispatch V2辅助信息，不从测试构造推广编码协议。

它只有一个条件设备方法，要求16设备，FP16、EP8/TP2、BS8/H7168/K7/E7、共享rank1、默认非量化；950文档无TP，与该TP2配置冲突。参考还调用NPU routing，不是独立CPU标杆；没有共享本地输入、特殊专家、enable_pre_reduce=False、MX或真实图验收。

A2共享测试两版原文已完整复核，仅V2 fullmesh、FP16、EP16、BS8/H7168/K8/E16、默认非量化，assist仍沿用自行重建idx。性能helper、rank%8、loopback和多个进程成功打印不证明对应独立设备拓扑、实际等待计时或端到端性能。文档图例只dynamic=False并打印，无Eager/图数值比较、真实专家GMM或反量化。

本次无上游执行、NPU/分布式/图/性能实验，无新增verified。实际复核先固定软件组合和后端符号，再用真实同次Dispatch assist、专家结果和路由权重验收有效token/共享与特殊专家；单独比较通信量化误差，最后测完整模型收益。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE v2 派发与回收配对：torch_npu.npu_moe_distribute_combine_v2

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

需与torch_npu.npu_moe_distribute_dispatch_v2配套使用，相当于按npu_moe_distribute_dispatch_v2算子收集数据的路径原路返回。

### 文档签名

```text
torch_npu.npu_moe_distribute_combine_v2(expand_x, expert_ids, assist_info_for_combine, ep_send_counts, expert_scales, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, tp_send_counts=None, x_active_mask=None, expand_scales=None, shared_expert_x=None, elastic_info=None, ori_x=None, const_expert_alpha_1=None, const_expert_alpha_2=None, const_expert_v=None, performance_info=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, global_bs=0, comm_quant_mode=0, comm_alg="", zero_expert_num=0, copy_expert_num=0, const_expert_num=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_combine_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeCombineKernelV2OpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combine_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combineA2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeCombineKernelV2OpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combine_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combineA2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
