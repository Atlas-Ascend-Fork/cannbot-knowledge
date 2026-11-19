---
type: API
title: MoE v2 派发与归一化回收配对（torch_npu.npu_moe_distribute_dispatch_v2）
description: torch_npu.npu_moe_distribute_dispatch_v2：MoE v2 派发与归一化回收配对。按路由专家分发 token，与 combine_v2 或 combine_add_rms_norm 配对，量化和通信配置按本版接口核对。 区分发布与主线A2/A3/950DT的算法、mask、FP8/FP4尺度、容量、后端回退及验证缺口。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeDispatchV2KernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatchA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeDispatchV2KernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatchA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-10T03:38:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_moe_distribute_dispatch_v2
---


# npu_moe_distribute_dispatch_v2：版本化路由与量化矩阵

## 版本与范围

前面的基础段依据ascend_26_0_pt28发布来源；后文完整补充主线950DT、量化、路由、包装与图转换差异。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_distribute_dispatch_v2(x, expert_ids, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, scales=None, x_active_mask=None, expert_scales=None, elastic_info=None, performance_info=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, quant_mode=0, global_bs=0, expert_token_nums_type=1, comm_alg="", zero_expert_num=0, copy_expert_num=0, const_expert_num=0) -> (Tensor, Tensor, Tensor, Tensor, Tensor, Tensor, Tensor)
```

先按专家路由 token，在 EP 域执行 AllToAllV，并按受支持的 TP 组合做 AllGatherV。返回顺序为 expand_x、dynamic_scales、assist_info_for_combine、expert_token_nums、ep_recv_counts、tp_recv_counts、expand_scales；必须与同版本 combine_v2 配套。

## 参数与组合限制

- 本卡描述发布版 0/2 量化模式：0 不量化，2 动态 INT8；不能沿用 init_routing_v2 的 1=动态标号，也不覆盖 950 主线 MXFP 模式。
- x=(BS,H)、FP16/BF16、ND；expert_ids=(BS,K)、INT32，同一 token 的 K 个专家 ID 不能重复。普通专家 ID 在 [0,moe_expert_num)，特殊专家另有 ID 区间，不可混入普通模式。
- expand_x 的最大形状为 (max(tp_world_size,1)*A,H)，非量化保持输入 dtype，动态量化变为 INT8；dynamic_scales 仅在动态量化时有效。
- expert_token_nums 为本地专家的 INT64 统计，type=0 是前缀和、1 是独立 count；三种路由接口的表示标号不能直接互换。
- assist_info_for_combine 为 INT32(A*128,)，区别于 v1 的 expand_idx。assist 与 EP/TP 接收计数应原样保留到 combine，不在业务中解析其内部布局。
- A3 的普通 fullmesh 路径不支持传 expert_scales，expand_scales 返回 None；hierarchy 路径及 A2 的约束不同。elastic_info 是预留参数，保持 None；performance_info 为 INT64(ep_world_size,)，记录前需显式清零，其内部会累加。
- 通信组、rank、容量、H/BS/K、mask 和算法的完整组合前提见下方发布版 Guide；签名中存在某个参数不表示所有平台/算法都支持。

## 验证与模型关联

检查七个输出的顺序和有效区，保留辅助 Tensor 给匹配的 combine；量化路径应连同实际专家计算验证 scale 传递，不能仅将 INT8 转为浮点当作完成反量化。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L603)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [发布版通信组合与容量检查](../../guides/optimization/moe_dispatch_combine_v2_release_contract.md)
- [模型路径选择](../../concepts/techniques/moe_dispatch_combine_v2.md)

## 完整版本复核与配套边界

本节完整核对OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布dedc316708372c9a8bfde4527abd2a94b74840f5，以及TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。发布配套为ascend_26_0_pt28，主线配套未知。主线950仅Ascend950系列（包含旧称Atlas A5）的DT、仅UB Memory，不推导PR或旧发布兼容。

两版实际Schema和C++均已有y_dtype/x_dtype/scales_dtype，主线文档补列不等于首次增加实现参数。V2必须配套Combine V2或受支持的CombineAddRmsNorm；不是把V1.expand_idx换个名字即可迁移，第三槽的分配和内部编码不同。

## 发布范围与主线文档变化

普通发布A2/A3的组、拓扑、H/BS/K、算法、共享和容量条件见前面的[发布Guide](../../guides/optimization/moe_dispatch_combine_v2_release_contract.md)。其中发布A3明确支持hierarchy、要求TP1/无共享，禁二维mask/特殊专家/弹性缩容/性能打点；发布A2 fullmesh支持实验性二维mask及零/拷贝专家，hierarchy不支持，常量专家两路径均不支持。

主线A2把mask缩到一维、零/拷贝/常量专家全部写为不支持；主线A3参数列表只列""、fullmesh_v1、fullmesh_v2，expert_scales也改为不支持，但EP和BS条款还残留hierarchy文字。不据残留行把发布hierarchy组合无条件迁移到主线。主线文档A2 BS全局上界256，发布hierarchy配HDK≥25.0.RC1.1则可512，亦不能合并成统一版本上限。

主线A3/950的fullmesh_v2明确只在TP size1生效，且不支持各rank BS不同、传x_active_mask或特殊专家。950 TP参数段却写无TP用默认0；默认0与模板要求1分别保留，使用该模板须明确核对实际版本，不能从“无TP”一词推导二者等价。fullmesh_v1/默认不启用v2模板。

主线中文与英文还有以下差异，均不记为实测：

|条件|主线中文|主线英文|
|--|--|--|
|950普通专家E|1..2048|通用1..1024|
|950本地专家L*EP规模P|≤4096|A3/950合写≤2048|
|950 fullmesh_v2 K/BS|K≤16、BS≤512|通用v2行K≤12，BS段≤512|
|A3 fullmesh_v2 BS|≤256|BS段通用≤512|
|默认comm_alg的K|≤16|前后重复段分别≤12/≤16|

中文产品细化用于记录新增范围，部署前仍须验证后端；未知组合不把较宽的一列当作保证。主线A3一般P在2..768，950在2..1024；A2 fullmesh P∈{2,3,4,5,6,7,8,16,32,64,128,256}、hierarchy仅16/32/64。主线A3/950 H在1024..8192，输出FP4要求逻辑H为偶数；K同时不得超过普通与特殊专家总数，BS仍按产品与模板取交集。

## mask、特殊专家与共享专家

主线A2 fullmesh一维BOOL[BS]要求true连续位于false前，hierarchy用None；A3/950支持一维[BS]或二维[BS,K]，后者按每个token的每个专家路由选择，整行false则不通信。支持非连续mask不等于任意布尔排列都合法。各rank BS不同时所有token必须全有效；fullmesh_v2的更窄禁mask条件仍适用。

特殊专家在允许的A3/950路径中依次占ID区间：普通[0,E)，零[E,E+Z)，拷贝[E+Z,E+Z+C)，常量[E+Z+C,E+Z+C+V)。每种数量在[0,2^31-1)，总数严格小于2^31-1，行内K个ID仍不重复。零专家输出0，拷贝输出ori_x，常量输出alpha1*ori_x+alpha2*const_v；这些是配套Combine的语义，Dispatch不执行普通专家GMM或凭空生成常量参数。

共享专家数S在0..4、rank数R在[0,P)，R非0须S>0且R%S=0；不再套V1的P%R条件。包装还允许默认S1/R0或明确S0/R0，其他组合须S≤R并整除；shard仅0、共享rank排前。普通E须被P-R整除，L=E/(P-R)，L>1不支持TP。各rank及两接口的组、P、E、TP、共享和global_bs保持一致，跨层组/拓扑/global_bs也一致；专属通信域不混其他算子，A3同超节点、A2多机交换机组网限制保留。

## A2打包INT4透传与主线950量化矩阵

主线A2额外公开INT32 x：每元素装8个INT4，按位透传，仅quant_mode0/fullmesh，H在1..5120且32倍数，scales必须连续FP32[BS]并随token通信，dynamic_scales有效前缀对应实际接收token。不能将INT32数值cast为8个INT4，也不能用专家[ E,H ]平滑scale代替每token尺度。此路径虽Meta有分支，本次没有真实打包数值/设备验收。

A2/A3普通FP16/BF16只有quant_mode0/2；0不传scales，2可选连续FP32[E,H]，有共享时[E+S,H]，输出INT8及FP32逐token反量化尺度。主线950按以下组合选择，不能把一列dtype集合任意交叉：

|mode|输出expand_x|输入scales|有效dynamic_scales|
|--|--|--|--|
|0|FP16/BF16|None|无|
|0|透传HiF8|与x一致时FP32[BS,d]，否则按分支None|[A,d]、dtype同scales|
|0|透传FP4；中文还补原生E4M3/E5M2|E8M0[BS,d]，d<H|[A,d]，保持输入尺度轴/类型|
|1|INT8|FP32[1]或[H]或[E+S,H]/[E,H]|无|
|1|HiF8|FP32[1]|无|
|2|INT8/E4M3/E5M2|None或FP32[E+S,H]/[E,H]|FP32[A]|
|3|E4M3/E5M2|None或FP32[E+S,H]/[E,H]|FP32[A,ceil(H/128)]|
|4|E4M3/E5M2或FP4两格式|None|E8M0[A,ceil(H/32)]，组数为偶数|
|5|E4M3/E5M2|None|E8M0[A,ceil(H/32)]，组数为偶数|

静态INT8的[1]表示量化系数，[H]为共享平滑权重，二维为融合的专家平滑尺度。原生FP8输入和透传mode0范围以中文新增表为限定，英文尚未列全。950 mode0参数通行段写d≤H而详细表为d<H；保留更细条件，不用通行段放宽等号。HiF8仍按其自身表行核对。

mode2/3公式先可选FP32预缩放，再按每token/每group的absmax和目标dtype最大值形成量化乘子；返回给消费端的尺度方向不能与乘子的倒数混用。mode4公式的max(x)、指数及输出倒数命名并不完整定义负数、特殊值或精确舍入，不据该简式编造通用离线MX量化配方。mode5明确absmax至少夹到1e-4，再ceil(log2(absmax/fp8_max))形成2的幂尺度后转FP8；它不是mode4的别名。E8M0为尺度编码，不是任意UINT8整数或普通float cast。

y_dtype在主线950非0模式应按矩阵显式指定，缺省为INT8，不能在mode3/4/5忽略参数后期望自动选出合法FP8/FP4。x_dtype/scales_dtype用于非原生逻辑dtype解释，容器内容必须已按正确位模式准备；参数不自动完成量化或校准。

## 输出分配、共享容量与Meta差异

global_bs相同BS可0或BS*P，不同BS为max_bs*P。包装把0展开为本地BS*P；MoE容量A=G*min(L,K)。共享rank实际分配为(G/P)*ceil(P/(R/S))，文档发布写BS*S/R、主线写BS*P*S/R；非整除共享分组、显式global_bs或异构BS必须按真实包装与后端核对，不照搬一个近似公式。elastic_info虽有分配扩容分支仍为公开预留None，不因此认证弹性部署。

expand_x首轴分配max(A,A*tp_world_size)，只消费实际有效token；第三槽实际分配INT32[max(BS*K,A*128)]，不是永远恰好[A*128]。expert_token_nums是INT64[L]，type0累计、type1独立count；assist、EP/TP counts和expand_scales仍只原样传给配套Combine，不解析内部编码。

普通EP counts分配P*L、仅TP2再乘2。expert_scales给值时，发布扩为P*L+2*G*K*(P/8)，主线只在非AclnnOnly路径扩；主线950按正常长度处理。expand_scales的有效性仍按产品/算法，C++总分配[A]、Meta无expert_scales时[0]，占位Tensor存在不能当作有效结果。

主线C++在AclnnOnly路径对TP0/1都用完整动态尺度helper，传首轴max(A,A*TP)；发布TP0仅[A]，TP非0且AclnnOnly才用helper。mode0带二维scales时发布helper将尺度展平为[A*d]，主线改[A,d]；主线Meta对TP≤1也改完整shape，并专门处理INT32+一维scales，而C++该通用helper仍要求至少二维，需按产品执行分支区分。

mode4/5的helper将ceil(H/32)向上补到偶数，不能把物理补齐槽全部当有效逻辑组。主线C++的dynamic_scales dtype会读取scales_dtype覆盖，Meta helper只看Tensor dtype，逻辑类型与容器dtype需另外检查。

## FP4容器和图路径的演进

主线C++/Meta仅在y_dtype为FP4且scales=None时检查H偶数、将输出末轴分配为H/2；发布没有此分配处理。主线mode0也应用显式y_dtype覆盖，发布C++/Meta/GE则先按mode0沿用x dtype、忽略该覆盖；两版都已有dtype参数不代表所有条件都相同。

TorchAir主线在x_dtype=296/297时把逻辑末轴扩成容器的2倍再Bitcast/Reshape；输出FP4再以UINT8按末轴/2打包，发布只Bitcast并修改描述，没有同样形状往返。296/297分别映射FLOAT4_E2M1/FLOAT4_E1M2，OpPlugin Meta用UINT8容器；不能把元素数与逻辑标量数混为一谈，也不能用普通reshape代替真实打包。

两版GE都先对显式x/scales逻辑dtype做Bitcast后透传至MoeDistributeDispatchV2；缺省scales=None时仍给scales_dtype会尝试Bitcast空输入，不作为合法用法。主线生成GE对缺省elastic/performance追加空槽与无效描述，发布这两项省略时未同样留槽。生成IR说明仍只列BF16/FP16输入和旧输出类型；实际动态创建/Bitcast存在不等于全产品组合与精度已经验证。

## ACLNN选择、性能打点与测试缺口

两版Eager均按符号先选ACLNN V4，再V3，最后V2；API名V2不表示固定只调用后端V2。V4透传performance_info；只有V3时显式拒绝该参数。再退到V2时只拒绝elastic/特殊专家，performance_info没有被传入，也未在同一分支明确拒绝，不得据调用返回认定打点已生效。公开performance_info为INT64[P]、微秒、每次累加不清零，开始新记录前需调用者清零；它是等待通信时间，不等于完整算子或端到端模型时延。

主线核心测试295行、发布251行完整差异有实质问题：发布父进程未传elastic_info，而子函数仍按含该项解包；主线改为传入，却是Python Tensor列表，子进程直接对列表.npu()，不能作为成功数值验收。原条件方法只测FP16、EP8/TP2及1、BS8/H7168/K4、非量化，参考还调用NPU routing，只比较有效expand_x。

主线950新增方法使用K16但E仅7或8且无特殊专家、生成ID0..15，越过公开普通ID范围；公共helper仍固定创建双TP组并启16进程，与该方法TP1/8设备要求不一致。它还依赖np.bfloat16，环境兼容未核对，不能把此文件当作950 FP4/MX/大头数或通信量化已测试证明。

A2共享测试两版原文已完整复核，V2只选BF16、quant0、无scales、EP16/fullmesh、H7168/BS8/K8、L1，引用的rank%8和loopback配置也不证明16独立设备；没有打包INT4、2D mask/特殊专家、hierarchy数值、FP8/FP4或mode1/3/4/5验收。

文档图样例没有Eager/图精度对比，也没有真实专家GMM/反量化；Eager样例有零/拷贝ID而没有常量ID，图例ID均为普通专家，不能只看特殊专家数量非0就认定各分支覆盖。warmup的global_bs硬编码16、与正式BS8的全局容量不同，不能作为任意拓扑通用预热方案。

## Buffer公式也须固定语言与版本

HCCL_BUFFSIZE默认200MB，字节表达式换算后按对应后端约束留余量。令F=H*sizeof(dtype_x)+4*Align8(K)*sizeof(uint32)，A2发布hierarchy至少(E+P/4)*Align512(max_bs*F)+8MB，主线却写E*BS*F+4MB+100MB；不得混用。主线A2 INT32 fullmesh的普通公式每token还多32B，其他输入仍2*(BS*P*min(L,K)*H*sizeof(uint16)+2MB)。显式算法优先于旧环境开关，旧开关只在comm_alg=""时决定fullmesh/hierarchy。

A3发布hierarchy另写E*BS*F+4MB+400MB；主线未列该算法完整合同，不从这个旧公式推导主线支持。fullmesh_v1/默认及v2的主线中英文也不同：中文EP token描述为Align32(2H)+44，英文+64；v2使用480Align512，定义ceil(x/480)*512，并非480乘普通Align512。950中文还把Combine侧token项改用480Align512，英文仍Align512，且两者都额外+10MB。

具体中文主线EP预算为2*(L*max_bs*P*D+(K+S)*max_bs*C)，A3的D按v1/v2分别Align512/480Align512(Align32(2H)+44)、C=Align512(2H)；950的D同前、C=480Align512(2H)，再+10MB。英文对应D内+64、C=Align512(2H)。TP另为2*A*(Align512(Align32(2H)+44)+Align512(2H))。这些是来源差异，不是可在未知CANN上任选的等价预算，应与配套Combine及后端实际检查取满足条件的配置。

文档写自8.0.0起图末节点Meta/inferShape强校验，单独Dispatch图形状不一致时先核对软件配套及实际输出，不重建不透明assist来掩盖。完整集成仍需逐项验收产品/算法、位打包、尺度、mask、专家语义、配套Combine和静态图，最后测通信及端到端收益。本次无上游执行、设备/多进程/图/性能实验，无新增verified。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE v2 派发与归一化回收配对：torch_npu.npu_moe_distribute_dispatch_v2

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

按路由专家分发 token，与 combine_v2 或 combine_add_rms_norm 配对，量化和通信配置按本版接口核对。

### 文档签名

```text
torch_npu.npu_moe_distribute_dispatch_v2(x, expert_ids, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, scales=None, x_active_mask=None, expert_scales=None, elastic_info=None, performance_info=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, quant_mode=0, global_bs=0, expert_token_nums_type=1, comm_alg="", zero_expert_num=0, copy_expert_num=0, const_expert_num=0) -> (Tensor, Tensor, Tensor, Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

本接口的非量化模式为 `quant_mode=0`（默认），动态量化为 `quant_mode=2`。前者返回的 `dynamic_scales` 为 `None`，后者返回动态量化 scale；不能套用 routing_v2 的 `-1/1` 编码。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeDispatchV2KernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatchA2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeDispatchV2KernelOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatchA2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）
