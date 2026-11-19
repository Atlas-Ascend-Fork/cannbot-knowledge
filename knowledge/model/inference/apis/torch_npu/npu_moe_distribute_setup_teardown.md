---
type: API
title: npu_moe_distribute setup/teardown：发布独有两段式MoE EP通信协议
description: 成组记录dispatch/combine四schema的setup预发comm_cmd_info、teardown消费回收的两段式调用合同，输出shape/dtype推导、host检查矩阵与Meta/C++实现差异，及16卡URMA测试的静态证据。
tags:
- task.lookup
- topic.mixture_of_experts
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputDtype.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch_combine_urma.py
  role: example
created_at: '2026-11-12T07:01:42Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# npu_moe_distribute setup/teardown：发布独有两段式MoE EP通信协议

## 版本与范围

本卡依据 OpPlugin 发布 pin `dedc316708372c9a8bfde4527abd2a94b74840f5`：四个 schema（`npu_moe_distribute_dispatch_setup/teardown`、`npu_moe_distribute_combine_setup/teardown`）登记于 op_plugin_functions.yaml 6377–6443 并全文阅读；实现为 `gen_opapi` 生成（仓内无手写包装 .cpp），host 合同即 yaml 生成块 + `KernelNpuOutputSize.cpp` 2295–2444 的四个输出推导函数 + `KernelNpuOutputDtype.cpp` 142–147 的 dtype helper；发布 Meta 注册 3102–3299 与官方测试全文另读。四个 schema 均为发布独有：主线 pin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的 yaml、Meta 注册、`KernelNpuOutputSize.cpp` 经全 pin 定向 rg 均零命中，测试目录无同名用例。登记 `op_api: all_version` 仅为注册证据。无官方 API 文档页、无 `derivatives.yaml` 接线。单次式 v1/v2 入口见[dispatch](npu_moe_distribute_dispatch.md)/[dispatch v2](npu_moe_distribute_dispatch_v2.md)与[combine](npu_moe_distribute_combine.md)/[combine v2](npu_moe_distribute_combine_v2.md)；本卡只覆盖 setup/teardown 两段式协议组。950 设备层语义（URMA window、commType 取值）由[设备层四卡](../../../../ops/ascendc/operators/aclnn/transformer/mc2/moe_distribute_dispatch_setup_950.md)承接。全部结论为静态源码阅读，未执行任何上游代码。

## 两段式调用合同

| 阶段 | 入口 | 职责（本层视角） | 输出 |
| --- | --- | --- | --- |
| 分发 setup | `npu_moe_distribute_dispatch_setup(x, expert_ids, group_ep, ep_world_size, ep_rank_id, moe_expert_num, *, scales?, x_active_mask?, expert_shard_type=0, shared_expert_num=1, shared_expert_rank_num=0, quant_mode=0, global_bs=0, comm_type=0, comm_alg="", y_dtype?)` | 预发本轮 EP 通信命令，产出供 teardown 消费的 `comm_cmd_info` | `y`、`expand_idx`、`comm_cmd_info` |
| 分发 teardown | `npu_moe_distribute_dispatch_teardown(x, y, expert_ids, comm_cmd_info, group_ep, …, expert_token_nums_type=1, comm_type=0, comm_alg="")` | 消费 setup 预发的通信窗口完成回收 | `expand_x`、`dynamic_scales`、`assist_info_for_combine`、`expert_token_nums` |
| 回收 setup | `npu_moe_distribute_combine_setup(expand_x, expert_ids, assist_info_for_combine, group_ep, …, comm_quant_mode=0, comm_type=0, comm_alg="")` | 对专家计算后的 `expand_x` 预发回收方向通信命令 | `quant_expand_x`、`comm_cmd_info` |
| 回收 teardown | `npu_moe_distribute_combine_teardown(expand_x, quant_expand_x, expert_ids, expand_idx, expert_scales, comm_cmd_info, group_ep, …, x_active_mask?, shared_expert_x?, comm_quant_mode=0, comm_type=0, comm_alg="")` | 消费回收窗口，还原本 rank 的 token 序 | `x` |

数据流：setup 的 `y` 与 `comm_cmd_info` 必须原样供同侧 teardown 消费；`expand_idx`（dispatch 侧）与 `assist_info_for_combine`（dispatch_teardown 产出）分别供 combine_teardown/combine_setup 消费；`expert_scales` 来自门控侧。四条 ACLNN 入口为 `aclnnMoeDistributeDispatchSetup/Teardown`、`aclnnMoeDistributeCombineSetup/Teardown`，生成代码按 yaml exec 顺序把全部标量（含 `expert_shard_type/shared_expert_num/shared_expert_rank_num/quant_mode 或 comm_quant_mode/global_bs/expert_token_nums_type/comm_type/comm_alg`）透传。两段式的完成语义在设备层：setup 提交 URMA SQE 后立即返回、不等待本轮通信完成，完成确认与后处理交给配套 teardown（见设备层卡）；因此 `y`/`expand_x` 等中间张量的生命周期须覆盖真实 DMA 完成，本层无"返回即可释放"的保证。

## 实际门槛与输出推导（C++ host 层）

已读来源（yaml 生成块与四个输出推导函数）中可见的 host 检查全部位于输出推导函数内，均为 fail-closed `TORCH_CHECK`（类别 PARAM）；`gen_opapi` 生成器本身不在已读来源内，不能证明生成代码的全部 host 检查仅此：

| 检查 | 适用入口 | 事实 |
| --- | --- | --- |
| x 2 维 | dispatch_setup/teardown | 报错含实际维度 |
| expert_ids 2 维 | dispatch_setup/teardown、combine_teardown | 同上 |
| expand_x 2 维 | combine_setup/teardown | 同上 |
| ep_rank_id ∈ [0, ep_world_size) | dispatch_setup/teardown | 报错含两个值 |
| shared_expert_rank_num ∈ [0, ep_world_size/2] | dispatch_setup/teardown | 同上 |

输出 shape 推导（`KernelNpuOutputSize.cpp`，令 x=(bs,h)、expert_ids=(·,k)、P=ep_world_size、S=shared_expert_num、R=shared_expert_rank_num、E=moe_expert_num、G=(global_bs==0 ? bs*P : global_bs)、L=本地专家数、AlignX=向上取整对齐）：

| 输出 | dispatch_setup | dispatch_teardown | combine_setup | combine_teardown |
| --- | --- | --- | --- | --- |
| 主输出 | `y=(bs*(k+S), hs)`，hs 按 quant_mode：0=Align(Align(2h,32),512)/2；1=Align(Align(h,32),512)；2=Align(Align(h,32)+4,512)；3=Align(Align(h,128)+Ceil(h,128)*4,512)；4=Align(Align(h,256)+Align(Ceil(h,32),2),512) | `expand_x=(a,h)`；a：rank<R（且 R≠0）时=G/R，否则=G*min(L,k)；L 同 setup | `quant_expand_x=(a, Align(Align(h,32)+Align(h,8)/8*4, 512))` | `x=(expert_ids.size(0), h)`，即 (bs,h) |
| 通信命令 | `comm_cmd_info=((bs*(k+S)+P*L)*16,)`，L：rank<R 时 1，否则 E/(P−R) | — | `comm_cmd_info=((a+P)*16,)` | — |
| 其他 | `expand_idx=(bs*k,)` | `dynamic_scales`：mode2 为 (a,)；mode3 为 (a,Ceil(h,128))；mode4 为 (a,向上补偶的 Ceil(h,32))；mode0/1 落 (a,) 初值；`assist_info_for_combine=(a*128,)`；`expert_token_nums=(L,)` | — | — |

输出 dtype（yaml gen_opapi 生成块字面）：`y` 缺省继承 `x.scalar_type()`、显式 `y_dtype` 经枚举转换；`expand_idx/comm_cmd_info` Int32；teardown 的 `expand_x` **继承输入 y 的 dtype**；`dynamic_scales` 缺省 Float、`quant_mode==4` 时 Float8_E8M0；`assist_info_for_combine` Int32；`expert_token_nums` Int64；`quant_expand_x` Int8（kChar）；combine_teardown 的 `x` 继承 `expand_x`。`comm_type/comm_alg` 本层只透传不解释；950 设备层只接受 `commType=2`（URMA）与空 `commAlg`（设备层卡口径，不自动外推到其他芯片）。

## Meta 与 C++ host 实检的分层

发布 Meta 注册（3102–3299）与 C++ 推导**不重合**，图/Meta 路径的推导结果不能当 Eager 分配合同：

| 差异点 | Meta 行为 | C++ 行为 |
| --- | --- | --- |
| dispatch_setup 的 L | 仅 `expert_shard_type==0` 时计算，否则保持 0，`comm_cmd_info` 长度随之不同 | 无 expert_shard_type 条件，无条件计算 |
| dispatch_setup 的 y dtype | `scales` 非空或 `quant_mode!=0` 时查 `y_dtype` 枚举映射，**缺省会以 None 作键失败**；否则用 x.dtype | 缺省 `x.scalar_type()`，显式才转换 |
| dispatch_teardown 的 a | 有 `expert_shard_type!=0` 分支（共享 rank 排在尾部：rank ≥ P−R） | 无该分支，恒按 rank<R 判定 |
| dispatch_teardown 的 expand_x dtype | `quant_mode!=0` 强制 Int8，否则 x.dtype | 继承 y 的 dtype |
| dispatch_teardown 的 dynamic_scales | 恒 `(a,)` Float | mode3/4 为二维 shape，mode4 dtype 为 E8M0 |
| combine_teardown 签名 | Meta 函数缺 schema 中的 `comm_alg` 形参（静态疑点：带该 kwarg 的 Meta 调用可能绑定失败） | 生成包装按 schema 透传 |
| 错误类别 | 维度检查用 VALUE | 维度检查用 PARAM |

`combine_setup` 的 Meta 形状/dtype 推导与 C++ 一致（其 `y_dtype=0` 形参为 schema 外死参数）；`combine_teardown` 的 Meta 输出 (bs,h)、dtype 继承 expand_x，与 C++ 一致。

## 官方测试与静态疑点

`test_moe_distribute_dispatch_combine_urma.py`（143 行全文阅读）：`@SupportedDevices(['Ascend910_'])` + `skipIfUnsupportMultiNPU(16)`，hccl 16 卡；quant_mode=2（动态量化）、E=16、P=16、bs=8、h=1024、k=8、R=0，scales FP32 (1+E,h)=(17,1024)，四阶段按协议顺序链式调用并把 `comm_cmd_info` 在 dispatch/combine 两侧各自 setup→teardown 传递。静态疑点（未执行，不作行为结论）：

- 测试调用**未显式传 `comm_alg`/`comm_type`**（用缺省空串/0）；文件名表明 URMA 场景，但取值映射在设备层，不在用例文字。
- 取通信域名的语句引用了未定义的 `comm_group`（定义的是 `ep_group`），按源码字面会在运行期 NameError；该用例不能当作已跑通证据。
- 全程无数值金标断言，仅回传 `.cpu()` 后打印，不构成精度或协议正确性验收。
- teardown 后测试把 `expand_x.to(input_dtype)` 转回 BF16，与 Meta 的量化强制 Int8 推导一致，而 C++ 让该输出继承 y 的 dtype（缺省路径下即 x 的 BF16）——三方静态不一致，运行时实际 dtype 以分配路径为准，本卡不裁决。

## 失败与版本边界

- 已读来源中可见的 host 门槛只有上表维度/rank/共享数检查（生成器不在已读来源内，不排除生成框架层的其他检查）；`expert_ids` 取值域、K 与专家数的上限、量化模式合法性等在已读的本层来源中不检查，由设备层 Route/Tiling 与产品表约束（设备层卡记录 950 公开范围）。
- `comm_cmd_info`/`assist_info_for_combine` 内部编码未公开，两段式协议将其按同侧 setup 产出、配套 teardown 原样消费使用；本层来源未给出关于复制/复用的硬性保证或禁止，设备侧精确约束未核验。
- 版本边界：四个 schema 仅发布 pin 存在（主线 rg 零命中）；发布配套 ascend_26_0_pt28 的组合验证不在本卡范围；`all_version` 登记不证明所有 CANN/torch_npu 组合可用。
- 设备层完成语义、URMA window/SQ-CQ 协议与平台矩阵见[设备层四卡](../../../../ops/ascendc/operators/aclnn/transformer/mc2/moe_distribute_dispatch_teardown_950.md)；该链接记录的是 950 canonical ACLNN 设备合同，与本发布软件对（固定 commit 的 yaml/生成包装）的设备侧配对相互独立，不能由跨卡链接推断本组合已有可用的匹配栈。无运行验证，无模型归属与整模型收益承诺。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（primary，6377–6443 四 schema 与 gen_opapi 生成块）

- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（primary，2282–2293 对齐 helper + 2295–2444 四个输出推导函数）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputDtype.cpp)（implementation，142–147 setup 输出 dtype helper）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation，3102–3299 四个 Meta 函数）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch_combine_urma.py)（example，1–143 全文逐字阅读）
