---
type: API
title: MoE token 派发通信（torch_npu.npu_moe_distribute_dispatch）
description: torch_npu.npu_moe_distribute_dispatch：需与torch\_npu.npu\_moe\_distribute\_combine配套使用，执行MoE的并行部署下的token dispatch与combine。 派发按可选量化、EP 的 AlltoAllv、可选 TP AllGatherV 的顺序组织；量化模式、EP/TP 通信域以及返回给 combine 的元数据必须配套。 限定A2/A3发布与主线950DT的EP/TP、共享专家、容量和INT8尺度，保留Meta及测试冲突。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeDispatchKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatchA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeDispatchKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatchA2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_formulaimage_0000002244554688.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_formulaimage_0000002244394892.png
  role: constraint
created_at: '2026-11-10T03:38:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_moe_distribute_dispatch
---


# npu_moe_distribute_dispatch：V1分发、量化与配套元数据

## 固定版本与V1边界

本卡覆盖OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布dedc316708372c9a8bfde4527abd2a94b74840f5；TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。发布属于ascend_26_0_pt28组合，主线配套未知。发布支持A2/A3，主线另列Ascend950系列（包含旧称Atlas A5）的DT，仅UB Memory通信；不扩到950PR。

接口为torch_npu.npu_moe_distribute_dispatch(x,expert_ids,group_ep,ep_world_size,ep_rank_id,moe_expert_num,*,scales=None,x_active_mask=None,expert_scales=None,group_tp="",tp_world_size=0,tp_rank_id=0,expert_shard_type=0,shared_expert_num=1,shared_expert_rank_num=0,quant_mode=0,global_bs=0,expert_token_nums_type=1)，返回七项。先可选量化，再EP AllToAllV，受支持时再TP AllGatherV；用于推理、Eager及静态图，必须配套同版本V1 Combine。

它的第三槽为expand_idx，与[V2](npu_moe_distribute_dispatch_v2.md)的assist_info_for_combine不同；V1没有comm_alg、elastic/performance_info、特殊专家或MXFP模式参数，不从V2或模型的通信量化策略推导V1能力。

## 输入、分组与各产品矩阵

x为FP16/BF16 ND[BS,H]；expert_ids为INT32 ND[BS,K]，ID在[0,E)、同一行K个ID不重复，E=moe_expert_num在1..512。两输入支持非连续，但scales须连续FP32。EP rank在[0,P)、同组唯一，P=ep_world_size；R=shared_expert_rank_num在[0,P)，E须被P-R整除。本地MoE专家数L=E/(P-R)，共享专家rank的L=1。

|条件|A2两版|A3发布→主线|主线950DT|
|--|--|--|--|
|EP规模P|16/32/64|8/16/32/64/128/144/256/288|2/4/8/16/32/64/128/144/256/288|
|BS|1..256|1..512|1..512|
|H|1..7168且32倍数|发布7168；主线H段1024..7168|7168|
|K|1..16且≤E|1..8且≤E|1..8且严格<E|
|共享专家|R=0，其余相关参数用默认|发布shared_expert_num仅1；主线0..4|shared_expert_num仅1|
|TP|不支持，size=0|size=0/1无TP，2有TP|不支持，但size明确传1、rank传0|

主线英文约束段还残留一行未标明对象的A3“仅7168”，中文对应行实际说明一物理卡包含双DIE，H段中英文均为1024..7168；不把孤立英文行当作统一H合同。发布A3以DIE为通信rank单位。A3/950仅expert_shard_type=0，共享rank排前；R非0时P%R=0，R=0表示无共享专家。L>1不支持TP。

group_ep为长度[1,128)的实际HCCL通信域名。A3的有效TP域名长度[1,128)、与EP不同，TP rank为0/1且同TP组唯一；无TP时rank=0。主线A2和950不用TP域名；发布A2却要求Eager默认空、图模式group_tp=group_ep，而主线写两个域名不能相同，必须保留版本/产品差异，不机械跨版本复用模板。

A3主线x_active_mask可用BOOL[BS]、支持非连续，默认全有效；不同rank的BS不同时必须全有效。发布A3及两版A2、主线950均将该参数保留，传None。expert_scales是token的TopK权重FP32[BS,K]，支持非连续，仅A2分层路径可用；A3/950不传，不能与scales混为一物。

## 动态INT8与尺度方向

quant_mode仅0或2。0不量化，不传scales，expand_x保持x dtype；2动态INT8：先以可选专家scales缩放FP32 x，再算量化乘子127/absmax，转INT8；输出dynamic_scales是随token传输的反量化尺度，即乘子的倒数。公开公式把dynamic_scales_value与dynamic_scales混写，不能把127/absmax直接作为下游反量化乘数。全零、溢出、NaN和取整边界没有本次设备验证。

发布scales为[E,H]，有共享专家时[shared_expert_num+E,H]，主线A3/950另允许[H]。A2在HCCL_INTRA_PCIE_ENABLE=1且HCCL_INTRA_ROCE_ENABLE=0路径要求scales默认None。两种尺度分别对应专家预缩放与token动态反量化，不等于路由expert_scales，也不等于专家GMM的权重尺度。

实际专家计算必须消费INT8与dynamic_scales配对数据；文档示例只将INT8 cast为浮点就直接Combine，未做专家GMM或正确反量化，因此只是通信调用骨架，不是数值等价的完整MoE实现。不能忽略尺度就宣称量化前后输出一致。

## 输出、有效区与不透明元数据

返回顺序为(expand_x,dynamic_scales,expand_idx,expert_token_nums,ep_recv_counts,tp_recv_counts,expand_scales)。expand_x最大分配[max(tp_world_size,1)*A,H]，有效token前缀须按实际接收统计消费，不能把容量A全部当作有效token。dynamic_scales为FP32，公开文档写[A]，两版C++/Meta在TP非0时实际分配[A*tp_world_size]；非量化即使占位存在也没有有效尺度语义。

expand_idx为INT32[BS*K]，传给Combine.expand_idx。expert_token_nums为INT64[L]，type=0表示每专家累计数，type=1为独立数；这些含义不能与其他路由接口的标号互换。ep_recv_counts传给Combine.ep_send_counts，tp_recv_counts传给Combine.tp_send_counts；expand_scales随A2 expert_scales通信，传给对应消费路径。

A3/950公开EP counts形状[P*max(tp_world_size,1)*L]，A2分层文档为[E+2*G*K*server_num]，G为global_bs或BS*P，server_num单机1、多机2/4/8。A2的额外区域是Combine的提前归约/通信偏移，不是普通每rank token计数；包装层按expert_scales是否给值选择扩展分配，并使用P/8，不按产品自动修正。

以上expand_idx、EP/TP counts、expand_scales的内部元素可随硬件、通信算法、软件版本变化，必须原样交给配套Combine，模型业务不要解析、重建或跨版本持久复用。无TP时TP输出不可用，A3/950的expand_scales文档为None；C++实际仍分配Tensor、Meta无expert_scales时为空[0]，不可据返回对象存在认定数据有效。

## 容量、全局BS与通信域一致性

各rank BS相同时global_bs可0或BS*P；不同时用max_bs*P，global_bs是容量依据，不是把不同rank实际BS求和。A2另允许256*P，但文档不建议固定此值以免阻碍后续更大BS。

MoE rank容量A按G*min(L,K)分配，G=global_bs非0值，否则本地BS*P。共享rank两版包装层按G/R分配，未乘主线新增的shared_expert_num；文档共享容量公式为global_bs非0时G*shared_expert_num/R、为0时BS*shared_expert_num/R，与实现存在差异。主线多个共享专家、global_bs=0或异构BS不能只根据文档公式自行分配后宣称兼容，须核对实际后端输出。

组名、P、E、TP规模、shard、共享专家数/共享rank数及global_bs在所有rank保持一致；组名、P、E、TP规模、shard、global_bs还须跨层并与Combine对应。中文主线跨层条款漏列E，英文及发布均列出，采用完整共同约束。一个模型中的这对算子使用相同专属EP域及受支持的专属TP域，域内不放其他算子；A3限制同一超节点，A2多机仅交换机组网、不支持双机直连。

## Buffer与静态图配套

HCCL_BUFFSIZE单位MB、默认200；按最大BS、MoE rank的L及实际产品/算法选择公式，不能将某模型阈值外推。下式中的容量乘法为字节表达，配置值仍按MB换算并留余量；主线A3新式未在原文显式写出MB换算，部署时须与对应CANN检查一致。

- A2普通路径至少2*(BS*P*min(L,K)*H*sizeof(uint16)+2MB)。
- A2 PCIe/非RoCE路径至少E*BS*(H*sizeof(dtype_x)+4*ceil(K/8)*8*sizeof(uint32))+4MB+100MB；该路径不再要求L≤24，普通A2仍要求L≤24，其他约束保留。
- 发布A3 EP及主线950：BUFFSIZE≥2，且2^20*(BUFFSIZE-2)/2≥BS*2*(H+128)*(P*L+K+1)。发布A3 TP另至少A*(2*H+128)*2字节，且文档还列hccl_buffer_size配置入口。
- 主线A3换为2*(L*max_bs*P*Align512(Align32(2*H)+64)+(K+shared_expert_num)*max_bs*Align512(2*H))，至少2MB；不能用旧公式覆盖所有新场景。

静态图末节点Meta与inferShape强校验可能暴露CANN/TorchNPU配套或单Dispatch输出形状差异。发布文档写起于8.0.0、主线写7.1.0，不把冲突文字变成已确认的统一最低版本。优先核对固定软件栈、实际输出和配套CANN；不能通过解析不透明counts来绕过。

## 包装、图转换及验证缺口

两版V1 C++字节相同，仅检查输入2D/dtype、共享rank范围及token_nums_type，不能据此推导产品规模、ID去重、BS/H/K、域隔离或buffer均已校验。传scales或quant_mode非0就分配INT8，宽分支不授予quant_mode=1等未公开模式。两版Meta重复容量计算且缺少完整参数验证，C++总分配expand_scales[A]、Meta无expert_scales时[0]，存在输出描述差异。

两版TorchAir转换器透传参数到GE MoeDistributeDispatch，生成接口创建七槽、为缺省可选输入留空描述，未完整校验产品或量化范围。转换器存在不等于部署编译/通信成功。

A3/950测试各一个条件设备方法、需16设备，只测FP16、quant_mode=0、H7168、BS8、K4、EP8、TP2及1、共享rank1或0；参考路由还调用NPU，不是独立CPU数值标杆。950设备装饰器允许进入TP2用例，与公开950仅TP1冲突，不用测试扩展产品范围。测试只比较有效expand_x，不验证七项、量化、mask、图或真实专家Combine；其中额外barrier也不作为专属通信域可混放其他算子的授权。

A2文件含V1与V2两个方法，V1只测BF16、quant_mode=0、无scales、EP16、H7168/BS8/K8、本地专家1。rank%8映射不证明16个独立设备拓扑。动态参考helper比较127/absmax而公开输出需倒数，且当前不运行动态分支；scales helper也未被当前方法选中。L=1不能区分累计数与独立数，不把测试参考的内部counts编码写成跨版本协议。

图/多进程文档样例没有独立数值参考、未检查所有子进程退出码，打印success不等于通信及精度验收。本次未执行上游、NPU、进程或端口，无新增verified。部署复核应先验证版本/域/拓扑及容量，再检查真实有效token、尺度和配套Combine，最后测量完整专家计算的精度与通信收益。

- [V2发布组合](../../guides/optimization/moe_dispatch_combine_v2_release_contract.md)
- [模型通信量化策略](../../optimizations/rules/moe_dispatch_combine_comm_quant.md)
- [Buffer错误观测](../../runbooks/runtime/moe_dispatch_combine_hccl_buffsize.md)
- [软件栈来源](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE token 派发通信：torch_npu.npu_moe_distribute_dispatch

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

需与torch\_npu.npu\_moe\_distribute\_combine配套使用，执行MoE的并行部署下的token dispatch与combine。

### 输入、输出与行为

派发按可选量化、EP 的 AlltoAllv、可选 TP AllGatherV 的顺序组织；量化模式、EP/TP 通信域以及返回给 combine 的元数据必须配套。

### 文档签名

```text
torch_npu.npu_moe_distribute_dispatch(x, expert_ids, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, scales=None, x_active_mask=None, expert_scales=None, group_tp="", tp_world_size=0, tp_rank_id=0, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, quant_mode=0, global_bs=0, expert_token_nums_type=1) -> (Tensor, Tensor, Tensor, Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_distribute_dispatch.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_distribute_dispatch.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeDistributeDispatchKernelOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatchA2.py)（example）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeDistributeDispatchKernelOpApi.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch.py)（example）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatchA2.py)（example）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/moe_distribute_dispatch.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_formulaimage_0000002244554688.png)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/figures/zh-cn_formulaimage_0000002244394892.png)（constraint）
