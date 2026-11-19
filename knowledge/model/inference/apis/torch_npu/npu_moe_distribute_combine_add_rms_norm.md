---
type: API
title: 专家回收与残差归一化融合（torch_npu.npu_moe_distribute_combine_add_rms_norm）
description: torch_npu.npu_moe_distribute_combine_add_rms_norm：与 dispatch_v2 配对回收 MoE token，并融合残差加法和 RMSNorm；通信元数据须来自相匹配的派发调用。 限定BF16、V2辅助信息和三维残差，区分发布与主线合同、参数默认冲突及融合数值验证缺口。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_combine_add_rms_norm.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_add_rms_norm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_add_rms_norm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_add_rms_norm.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeCombineAddRmsNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combine_add_rms_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeCombineAddRmsNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combine_add_rms_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_add_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_add_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
- '950'
aliases:
- torch_npu.npu_moe_distribute_combine_add_rms_norm
---


# npu_moe_distribute_combine_add_rms_norm：V2回收与残差归一化

## 固定版本与融合计算

固定OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda；TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013与主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c。发布属于ascend_26_0_pt28，主线配套未知。发布仅列A3；主线增加Ascend950系列（包含旧称Atlas A5）DT、仅UB Memory。不推导A2、950PR或任意混用版本。

接口用于推理、Eager与静态图，将同版本[Dispatch V2](npu_moe_distribute_dispatch_v2.md)的专家结果回收，随后加残差并做RMSNorm。令combine_out为按路由权重归并后的token，则x=combine_out+residual_x；y=x*gamma/sqrt(mean(x²,末轴)+norm_eps)。norm_eps公开默认1e-6。返回顺序为(y,rstd_out,x)，x是加残差后、归一化前的结果，不能把它当第二份y。文档未进一步给出rstd_out的数值公式，本次测试也没有独立验证该输出，不凭名称补造精确数值合同。

必传位置参数依次为expand_x,expert_ids,expand_idx,ep_send_counts,expert_scales,residual_x,gamma,group_ep,ep_world_size,ep_rank_id,moe_expert_num；其后参数均为关键字。不能按普通Combine的位置顺序插入residual/gamma而错位组参数。

## BF16输入、输出与真实配套

|输入/输出|公开合同|
|--|--|
|expand_x|专家计算后的BF16 ND二维[A,H]；主线中文为此形状，英文及发布另保留max(tp_world_size,1)*A写法|
|expert_ids|INT32[BS,K]，与同次Dispatch V2路由对应，行内ID不重复|
|expand_idx|名字虽为idx，内容是Dispatch V2.assist_info_for_combine，INT32[A*128]|
|ep_send_counts|同次Dispatch V2.ep_recv_counts，INT32一维；原样透传|
|expert_scales|FP32[BS,K]路由权重；不是动态反量化scale|
|residual_x|必传BF16[BS,1,H]三维，不以广播假定二维[BS,H]有效|
|gamma|必传BF16[H]|
|y、x|BF16连续ND[BS,1,H]，dtype公开与residual_x相同|
|rstd_out|FP32连续ND[BS,1,1]|

输入上述ND Tensor支持非连续。路由辅助信息必须来自同次、同版本、同组Dispatch V2，不能改用[V1 Dispatch](npu_moe_distribute_dispatch.md)的INT32[BS*K] expand_idx，也不能照测试手写其内部编码。发布参数个别交叉引用仍指V1，但功能与形状明确要求V2；主线已修正文档引用。不要把容量A中的未写区域都当有效token。

## 规模、TP与共享参数的版本边界

P=ep_world_size在2..768，rank在[0,P)且同组唯一；E=moe_expert_num在1..1024，E%(P-R)=0，其中R=shared_expert_rank_num，本地MoE专家L=E/(P-R)。H在1024..8192，BS在1..512；主线中文清楚列出H，英文对应行的变量名缺失。完整链路还要取所选Dispatch V2产品与算法的交集，不能把V2较宽的E、P、MXFP参数自动带入本融合。

发布K≤8；主线中文K≤16，英文同时出现K≤16与K≤8两条，且K≤E+Z+C+V。保留这一冲突，公共使用先限共同范围K≤8；K9..16须核对实际产品、CANN及后端，不能声称两种语言已一致认证。

主线公开不支持TP：tp_send_counts=None、group_tp=""、tp_world_size=0、tp_rank_id=0。发布A3仍描述size0/1/2、TP counts和L>1时不支持TP；这是发布分支合同，不能当主线TP支持证明。group_ep非空且长度[1,128)、与group_tp不同。

两版说明均把shared_expert_num与R保留为仅0，但原型、Schema、GE默认shared_expert_num=1、R=0。依公开无共享rank路径应显式传shared_expert_num=0、shared_expert_rank_num=0，不能把省略参数视为说明中的0。expert_shard_type只0。shared_expert_x是本地共享结果，可在R=0时传入，与expand_x同dtype；中文列[BS,H]，它不同于共享专家rank通信。C++、GE均实际传递它；功能公式给共享结果也乘expert_scales，而参数段写共享不乘权重、直接相加，须分别验证，不凭公式机械重复加权。

## mask、特殊专家与保留参数

x_active_mask为BOOL[BS]或[BS,K]、支持非连续。一维true必须在false前；二维按路由项控制参与，整行false表示该token不参与；各rank BS不同时全部token必须有效。

Z/C/V分别为zero/copy/const专家数，各在[0,2147483647)，E+Z+C+V严格小于2147483647。英文、发布和配套Dispatch使用半开段[E,E+Z)、[E+Z,E+Z+C)、[E+Z+C,E+Z+C+V)。主线中文此处写右闭段，会在相邻边界重叠、计数0仍似含元素，属于文档冲突；不能据此新增末端ID。

zero输出0；copy输出ori_x；const输出alpha_1*ori_x+alpha_2*const_v。C或V非0时ori_x必传BF16[BS,H]；V非0时const_expert_alpha_1、const_expert_alpha_2、const_expert_v均必传BF16[V,H]，ND且支持非连续。对应路由权重与完整token身份仍由原Dispatch配套信息决定。

activation_scale、weight_scale、group_list、expand_scales均保留None；elastic_info也公开保留None。out_dtype=0、comm_quant_mode=0、group_list_type=0、comm_alg=""保持默认。不因普通Combine V2具备量化/MX通信、弹性或算法选择，就推导本融合已支持。特别不能将INT8 Dispatch输出直接cast为BF16当作完整专家和反量化过程。

## 一致性、容量与通信Buffer

文档明确要求expert_ids、x_active_mask、elastic_info这些Tensor的取值以及group_ep/P/E、TP组与规模、shard、共享数/R、global_bs、Z/C/V、HCCL_BUFFSIZE在所有rank、网络各层及配套Dispatch保持一致。中文一致性列表含comm_alg，英文改列comm_quant_mode；不能自行把这些强约束弱化为仅shape一致或仅组配置一致。随机每rank样例也不证明任意不同路由都满足合同。

global_bs在同BS时可0或BS*P，不同BS时用max_bs*P；C++会把0展开为当前BS*P，不会跨rank求和。MoE容量A≥G*min(L,K)，G取展开后的global_bs。中文残留共享rank容量G*S/R，但公开R仅0，不应在当前路径直接执行除0公式，也不能据其推断共享rank已支持。

HCCL_BUFFSIZE单位MB、默认200，也可用对应hccl_buffer_size配置；至少2MB。EP公式为2*(L*max_bs*P*Align512(Align32(2*H)+64)+(K+S)*max_bs*Align512(2*H))。公式项是按字节尺寸写的，原文却直接和配置大小比较，部署时按固定CANN实现核对单位换算，不能将字节数直接填成MB。发布另列TP需求2*A*(Align512(Align32(2*H)+44)+Align512(2*H))；主线不支持TP，不能机械复用。AlignN为整数向上对齐；英文列出的Align480是ceil(x/480)*512，不是通常的480倍数。

模型内Dispatch V2与本融合仅用同一专属EP域，域内不放其他算子；A3要求同一超节点、不能跨超节点，rank按DIE理解。发布另有TP域约束，按发布部署核对。Buffer值、容量和这些组约束要与配套Dispatch共同核对，不能只通过单端分配检查就认为通信安全完成。

## Eager、Meta与图构造不能代替公开合同

两版C++仅检查expand_x/expert_ids二维和有限dtype；内部还接受FP16/INT32，输出分配沿用expand_x，INT32时由out_dtype转BF16/FP16。Meta却始终沿用expand_x dtype。公开只列BF16且输出跟residual_x，不能把宽C++分支和Meta描述器当FP16、INT32或融合反量化已经受支持。

C++优先aclnnMoeDistributeCombineAddRmsNormV2；缺少该符号时回退基础版本，并拒绝elastic_info和非0特殊专家计数。主线将norm_eps显式转float后调用，发布直接传double变量，这是实现类型边界，未做运行实测不能断言实际精度故障。Meta形参norm_eps默认0，与公开Schema/GE的1e-6不同；Meta只造形状、不计算归一化，不以Meta默认值替代数值合同。

TorchAir转换器把expand_idx映射为GE assist_info，并转发全部输入及attrs、返回三输出。主线生成GE对None elastic/ori/const追加空输入描述，发布在这些后部可选项None时省略；二者都不是本地ACLNN可用性或产品支持检查。本融合没有performance_info参数，不从其他Combine版本推导打点接口。

## 样例错误与实际验证范围

主线Eager和图样例回退成调用V1 Dispatch，再传其短expand_idx，违背本融合要求V2 assist的合同；Eager residual_x还构造二维[BS,H]，图样例虽三维仍有错误Dispatch。发布样例用V2和三维残差，作为阅读入口更一致，但也仅将量化结果cast、没有完整专家反量化、独立精度标杆或图/Eager对照。

两版核心测试仅有一个A3/950条件方法，声明需16设备、实际EP8/TP1产生8进程，使用BS8/H7168/K7/E7、共享rank1和默认共享数1，与公开R0和主线无TP有冲突。它自建V1风格短idx，没有真实Dispatch V2 assist；随机elastic_info通过[0,1)生成整数全0，不能证明保留弹性路径可用。

参考只算普通Combine，未加residual、gamma或RMSNorm；子进程另行随机残差/gamma，仅队列返回out[0]的三维y，却与二维普通Combine参考比较，没有检查rstd_out与x。因此它不构成融合数值正确性的独立验收，更不证明主线950或图性能。发布测试与主线的差异仅空白。

真实复核应连接同版本Dispatch V2与真实专家结果，以明确残差、gamma和eps建立独立融合参考，分别验收(y,rstd_out,x)、dtype/shape、mask/特殊专家/本地共享路径，再测端到端内存和时延。本次只做固定源码与文档静态审查，未执行上游、设备、分布式或性能实验，无新增verified。

- [普通Combine V2](npu_moe_distribute_combine_v2.md)
- [发布版配套](../../guides/optimization/moe_dispatch_combine_v2_release_contract.md)
- [Buffer错误观测](../../runbooks/runtime/moe_dispatch_combine_hccl_buffsize.md)
- [固定软件栈](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### 专家回收与残差归一化融合：torch_npu.npu_moe_distribute_combine_add_rms_norm

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

与 dispatch_v2 配对回收 MoE token，并融合残差加法和 RMSNorm；通信元数据须来自相匹配的派发调用。

### 文档签名

```text
torch_npu.npu_moe_distribute_combine_add_rms_norm(expand_x, expert_ids, expand_idx, ep_send_counts, expert_scales, residual_x, gamma, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, tp_send_counts=None, x_active_mask=None, activation_scale=None, weight_scale=None, group_list=None, expand_scales=None, shared_expert_x=None, elastic_info=None, ori_x=None, const_expert_alpha_1=None, const_expert_alpha_2=None, const_expert_v=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, global_bs=0, out_dtype=0, comm_quant_mode=0, group_list_type=0, norm_eps=1e-06, int zero_expert_num=0, int copy_expert_num=0, int const_expert_num=0) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_combine_add_rms_norm.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_add_rms_norm.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_add_rms_norm.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_combine_add_rms_norm.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeCombineAddRmsNormKernelOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_combine_add_rms_norm.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeCombineAddRmsNormKernelOpApi.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_combine_add_rms_norm.py)（example）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_add_rms_norm.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_combine_add_rms_norm.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
