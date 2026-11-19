---
type: API
title: MoE v2 路由初始化与动态量化（torch_npu.npu_moe_init_routing_v2）
description: torch_npu.npu_moe_init_routing_v2：MoE v2 路由初始化与动态量化。MoE（Mixture of Experts）的routing计算，根据torch_npu.npu_moe_gating_top_k_softmax的计算结果做routing处理，支持不量化和动态量化模式。 说明路由统计与有效区，区分950量化物理容器、310P返回协议、旧CANN回退及Meta/图差异。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeInitRoutingV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_init_routing_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeInitRoutingV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_init_routing_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_init_routing_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_init_routing_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T03:38:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
- 310p
aliases:
- torch_npu.npu_moe_init_routing_v2
---


# npu_moe_init_routing_v2：分组统计、有效映射与量化模式

## 版本与范围

发布A2/A3依据ascend_26_0_pt28；主线新增950PR及DT和310P按独立快照记录，软件配套与返回协议分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_moe_init_routing_v2(x, expert_idx, *, scale=None, offset=None, active_num=-1, expert_capacity=-1, expert_num=-1, drop_pad_mode=0, expert_tokens_num_type=0, expert_tokens_num_flag=False, quant_mode=-1, active_expert_range=[], row_idx_type=0) -> (Tensor, Tensor, Tensor, Tensor)
```

按专家重排并展开 token，返回 (expanded_x,expanded_row_idx,expert_token_cumsum_or_count,expanded_scale)。dropless 输出 (N*K,H)，active 输出 (min(active_num,N*K),H)，drop/pad 输出 (expert_num,expert_capacity,H)。发布公开的0/1量化模式返回INT8，非量化保持x dtype；主线新量化和310P第四返回另见下文。

## 参数与组合限制

- x 为二维 ND、FP16/BF16/FP32/INT8，expert_idx 为二维 INT32 (N,K)，专家 ID 需落在有效专家域；active_expert_range=[start,end) 且 end≤expert_num。
- expert_tokens_num_flag=True 才请求专家统计：type=0 为前缀和，1 为各专家独立 count，2 为非零专家的 (ID,count) 对。参数段将 count 写成“累计值”，与返回说明及同页参考逻辑不一致；本卡按后两者区分，不把 count 与 cumsum 混用。
- row_idx_type 的来源命名为 0=gather、1=scatter，映射方向还须与下游配套核对。type=1 时只有前 available_idx_num 个映射有效，尾部未初始化；type=0 的无效位置为 -1。
- quant_mode 公开参数只列 -1/0/1：非量化、静态、动态。静态必须提供 FP32 单元素 scale/offset；动态可选 scale=(end-start,H) 或 (1,H)，不传 offset。非量化可携带每 token FP32 scale=(N,) 重排。参考代码出现 MX 模式，不据此扩大公开参数支持。
- active_num 默认 -1 与正文“校验≥0”存在差异；应显式选择 0（dropless）或符合业务的正数，并核对运行包。drop_pad_mode=1 时 expert_capacity>0 且小于 N，专家范围必须为 [0,expert_num)。
- expanded_scale 及映射必须按有效路由范围消费；量化路径输入为 INT8 时来源明确 expanded_x 值无意义，不能当作再次量化成功。特化性能模板还依赖完整 shape/属性组合，不由单个开关保证。

## 验证与模型关联

以小规模专家排序与直方图作参考，分别测试 count/cumsum、局部专家范围、active 截断、drop/pad 和 scale 重排；把有效区外数据排除在后续 GMM/恢复计算之外。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L516)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [专家并行中的阶段与通信选择](../../concepts/parallelism/expert_parallel.md)

## 完整发布契约、索引与性能模板

发布A2/A3与主线新增950PR及DT、Ascend310P系列按版本分别限定。主线软件配套尚未确认，不能把新增产品和量化路径并入ascend_26_0_pt28发布组合。两个固定schema已经都有x_dtype=None，发布公开原型遗漏它；代码存在不扩充发布产品表。

本接口参考先把expert_idx按token优先展平，槽位为t*K+k，不能与旧初始化路由的t+k*N混用。row_idx_type=1返回排序后的原槽位，type=0是原槽位到排序位置的逆映射；来源分别称scatter/gather，使用时应核对实际方向。type=1只有有效前缀可读、尾部未初始化，type=0无效项为-1。主线修正active_num=-1/0都处理全部token、count为独立数量、key_value为(ID,count)对；发布文字冲突仍保留，均不代表所有分配行都有有效数据。

expert_num在key_value模式为0..5120，其他统计模式为0..10240；专家范围为左闭右开，drop/pad需完整范围。低时延模板需同时满足x=(1,7168)、expert_idx=(1,8)、scale=(256,7168)、BF16、范围[0,256]、quant_mode=1、统计type=2、expert_num=256。大batch模板需N为384..8192、K=8、expert_num=256、范围长度≤32、quant_mode=-1、row_idx_type=1、统计type=1。主线将这些条件放在A2/A3段，不能直接推广到950或310P。全载模板要求drop_pad_mode=0，但不表示仅此条件就保证命中或加速。

## 主线950量化与物理输出

以下只按主线950PR及DT记录，R为包装分配的展开行数：dropless为N*K或min(active_num,N*K)，drop/pad为E*C。局部专家范围的有效路由可能更少，分配容量不是有效数量。非量化与INT8动态的scale缓冲按R分配，不能统一按文档概述的原始N行分配。

| quant_mode | 展开数据与scale的固定包装形状 |
| --- | --- |
| -1 | 保持物理输入类型和尾长；原生FP8或带标记FP4携带scale时，scale为(R,ceil(H/64),2)的E8M0字节容器，H按逻辑元素数 |
| 0/1 | INT8(R,H)；静态量化的第四缓冲不保证有效，动态scale为FP32(R,) |
| 2/3、16/17 | FP8 E5M2/E4M3FN(R,H)，scale为E8M0(R,向上对齐到偶数的ceil(H/32))；16/17额外启用Amax钳位 |
| 4/5、14/15 | FP8 PerGroup，scale为FP32(R,ceil(H/128))；14/15启用Amax下限 |
| 6/7/8 | HIF8直转、per-tensor、per-token；物理数据为UINT8(R,H)，第四项的有效性分别按模式核对 |
| 9 | MXFP4，物理数据为UINT8(R,H/2)，scale为E8M0字节容器(R,ceil(H/64),2) |
| 11/12 | FP8 PerBlock，scale为FP32(R,ceil(H/256),2) |
| 13 | INT4动态量化，物理数据为UINT8(R,H/2)，scale为FP32(R,) |

这些量化编号不含10，不能把编号连续性当作支持。q13仅支持dropless、FP32/BF16输入、不传offset、H为偶数；可选scale必须FP32(1,H)，x_dtype只能INT4或None。q1配INT4标记明确被拒绝，应使用q13。q9也有公开H偶数约束，包装的整除分配不是奇数H合法的证据。

x_dtype按枚举解释非原生类型，不执行数值转换：非量化可为HIF8/FP4，q13可为INT4；原生FP8直接用输入dtype。FP4输入物理尾长为逻辑H/2，主线C++先恢复逻辑H，透传输出仍保持物理尾长，不能把UINT8元素数当成逻辑FP4元素数。q2/3/16/17的E8M0类型还受PyTorch编译版本≥2.7的包装条件约束，不是新硬件配套的完整最低版本声明。

950的drop/pad只允许非量化、row_idx_type=0、完整专家范围、统计type=1，输入限三种float、INT8和HIF8，不把普通dropless的FP8/FP4量化表应用于这一分支。

## 310P与旧CANN回退的返回协议

主线310P产品只公开FP16/FP32、非量化及dropless。两个固定C++都在310P1..310P7选择ACLNN MoeInitRoutingV2，强制capacity和drop_pad_mode为0、按cumsum计算；第三项实际分配INT32，第四项为INT32(expert_num,)的expert_tokens_before_capacity缓冲，不能按FP32量化scale解包。文档称第四项为裁剪前计数，但包装把对应计算flag设False，分配本身不保证有有效统计值。

两个固定C++还会在H=2048、E=128、范围[0,128]、非量化、count模式且CANN比较低于8.5.0.alpha003时选择同一旧路径；这使第四项变化不只出现在310P。该条件来自缓存的版本比较调用，未运行版本探测或验证实际库行为。其余正常路径调用ACLNN V3，不能按Python函数名V2推断底层版本。

两个固定默认专家范围辅助函数都把首次空范围调用的expert_num保存在static vector，后续空范围调用不会随新E重建；CheckV2Case又读取原始active_expert_range而非已补齐范围，E=128时存在访问空列表元素的静态风险。显式传入与本次E一致的[0,E]可避开这里的默认路径，不代表所有其他条件已验证。

## Meta、GE与测试参考边界

两个Meta未模拟310P或旧CANN回退，仍返回INT64统计和scale协议；expert_tokens_num_flag=False时第三项shape是标量()，不是None或零元素Tensor，C++却仍分配完整统计容量。q0/6/7时Meta的第四项也为标量()，C++一般分配R行。bs=0的C++提前分支只明确清零统计项，不能扩为所有返回缓冲均有有效零值。

主线FP4/FP8透传及MXFP4的scale在C++中可为UINT8物理容器配E8M0后端标记，Meta直接声明E8M0类型；读取字节或比较dtype时要区分两层。主线q13的形状与输入约束单独处理，不能把Meta接受所有量化编号理解为每个平台都支持。

两个GE Converter都调用MoeInitRoutingV3，不复现上述Eager旧V2选择。主线补充FP4解包尾长乘2、输出重新打包除2，及FP8/FP4 scale的E8M0 Bitcast；发布只做较简单的dtype标记。GE节点文件存在不证明310P第四返回、旧运行库分支或全部可选组合与Eager一致。

公开动态量化公式在有scale时写用原x除量化scale，静态参考却先乘输入scale再量化；CPU参考还硬编码E=32、key_value仅追加一对零、缺少通用零幅值和空输入处理。发布测试的active_num=-1参考按负切片而非全部行，主线继承；它们不是所有输入的可执行金标准。

发布876行测试全文与主线1307行测试的完整760行差异已静态审阅。多个测试跳过drop/pad、flag=False和cumsum，遇到none_scale即退出整个测试方法；静态量化测试被skip。主线INT4只检查shape/dtype并测试旧模式拒绝，未比较打包数值。主线MX参考改用RoundScale算法，PerBlock参考仍有未定义变量及二维scale访问第三轴的问题；比较助手还忽略Inf符号。不能把测试参数笛卡尔积当作已验证覆盖，本次未运行设备、导入上游或新增verified。

## 已有 OpPlugin 7.3.0 文档与版本边界

### MoE v2 路由初始化与动态量化：torch_npu.npu_moe_init_routing_v2

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE（Mixture of Experts）的routing计算，根据torch_npu.npu_moe_gating_top_k_softmax的计算结果做routing处理，支持不量化和动态量化模式。

### 文档签名

```text
torch_npu.npu_moe_init_routing_v2(x, expert_idx, *, scale=None, offset=None, active_num=-1, expert_capacity=-1, expert_num=-1, drop_pad_mode=0, expert_tokens_num_type=0, expert_tokens_num_flag=False, quant_mode=0, active_expert_range=[], row_idx_type=0) -> (Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

本接口的非量化模式为 `quant_mode=-1`，动态量化为 `quant_mode=1`。该固定版本的签名默认值 `quant_mode=0` 表示静态量化，但参数与约束说明均声明暂不支持，调用时应显式选择支持的模式；不能套用 MC2 dispatch_v2 的 `0/2` 编码。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_moe_init_routing_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing_v2.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_moe_init_routing_v2.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeInitRoutingV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_init_routing_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeInitRoutingV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_init_routing_v2.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_init_routing_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_moe_init_routing_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）
