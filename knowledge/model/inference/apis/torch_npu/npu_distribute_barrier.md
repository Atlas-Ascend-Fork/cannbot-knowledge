---
type: API
title: _npu_distribute_barrier：V1/V2能力分派与MoE分发前通信栅栏
description: 记录内部通信栅栏入口的双aclnn能力分派、V1对time_out/elastic_info的host拒绝、返回x_ref本身的透传合同，以及MoE分发测试与16卡弹性用例的调用形态。
tags:
- task.lookup
- topic.parallelism
- topic.mixture_of_experts
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DistributeBarrierOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DistributeBarrierOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_distribute_barrier.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_distribute_barrier.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_fake_tensor.py
  role: example
created_at: '2026-11-12T13:14:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# _npu_distribute_barrier：V1/V2能力分派与MoE分发前通信栅栏

## 版本与范围

本卡覆盖OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的内部通信栅栏入口`_npu_distribute_barrier(Tensor x_ref, str group, int world_size, *, Tensor? time_out=None, Tensor? elastic_info=None) -> Tensor`。两pin yaml均登记（主线6662–6663、发布6445–6446，`op_api: all_version`，无acl_op条目、无exposed标注）；两pin derivatives.yaml rg零命中（无反向接线）；两pin docs/目录rg零命中（无公开API页，Python侧以`torch_npu._npu_distribute_barrier`内部名调用，见下述测试）。实现文件DistributeBarrierOpApi.cpp两pin全文读毕：与主线差异仅排版、文件尾缺`// namespace op_api`注释与末行换行（main 51行、release 48行，去空白字符流除该注释外逐字相等）。全部为静态源码阅读，未执行任何上游代码或设备测试；本卡不认证任何安装组合，platforms留空。

## host双路分派

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| 入口先`char* group_ptr = const_cast<char*>(group.data())`，随后每次调用执行`check_aclnn_kernel_available("aclnnDistributeBarrierV2")`（主线33–41、发布33–41同构） | 该检查是普通函数（op_api_common.cpp主线767–774、发布785–792：算子符号与`<name>GetWorkspaceSize`符号同时非空才返回真），**没有**DO_COMPATIBILITY宏展开处那种函数级static缓存——调用点也不缓存，每次进入都重新查表；GetOpApiFuncAddr/句柄管理内部是否另有缓存不在已读来源内，不据此断言重复查表成本 |
| V2可用：`EXEC_NPU_CMD(aclnnDistributeBarrierV2, x_ref, time_out, elastic_info, group_ptr, world_size)`——两个optional Tensor与group/world_size一起透传 | EXEC_NPU_CMD宏（主线op_api_common.h 410–494定向读）在调用点做static符号取址、TORCH_CHECK符号存在、流选择、确定性快照缓存、ConvertTypes打包与workspace申请后异步入队；ConvertTypes对optional Tensor/char*/int64的打包细节未整读，不另立抛错结论 |
| V2缺失：先查静态helper `check_TimeOut_ElaticInfo_param`（22–32：time_out或elastic_info任一有值即真），`TORCH_CHECK(!..., "The aclnnDistributeBarrier do not support time_out and elastic_info", ErrCode::PARAM)`——即任一可选张量传入就抛错；两者都缺省才`EXEC_NPU_CMD(aclnnDistributeBarrier, x_ref, group_ptr, world_size)` | 报错文案原文含拼写"do not support"照录；V1路对弹性/超时参数是host硬拒绝，不是忽略或降级；AclnnOnly开关不参与本分支（本文件无DO_COMPATIBILITY，V1符号若也缺失由EXEC_NPU_CMD的符号TORCH_CHECK兜底） |
| 返回值 | 两个分支都`return x_ref;`——返回传入的同一Tensor对象，本地零分配；x_ref的数值是否被设备侧读写、超时单位与栅栏语义在aclnnDistributeBarrier(V2)侧，不在已读来源内 |

## 调用合同（官方用例）

- MoE分发链（两pin的test_moe_distribute_dispatch.py与test_moe_distribute_dispatch_v2.py，主线70–79/74–79、发布72–75/75–78定向读）：`tp_world_size == 1`分支在分发前调用`_ = torch_npu._npu_distribute_barrier(x_ref=x, group=ep_hcomm_name, world_size=ep_world_size)`——不传time_out/elastic_info（走V1式参数面）。`group`是`ep_group._get_backend(torch.device('npu')).get_hccl_comm_name(rank)`返回的HCCL通信域名原始字符串，不是ProcessGroup对象；与[dispatch卡](npu_moe_distribute_dispatch.md)已记录的"额外barrier不作为专属通信域可混放其他算子的授权"口径一致，本卡不重复展开分发合同。
- 弹性栅栏专项用例（两pin的test_distribute_barrier.py，主线1–156全文读毕，发布同文件仅行尾空白差异）：16 NPU、`@SupportedDevices(['Ascend910_93', 'Ascend950'])`门；仅table2中非-1的本EP内rank调用本入口，其余rank直接返回None不调用。`x_ref = torch.ones(1, dtype=torch.int32)`（引用张量，不承载数据语义）；`time_out = torch.tensor([100000], dtype=torch.int32)`；`elastic_info`为一维int32、长度`4 + 2*ep_world_size`，前四项为[is_elastic, 参与世界数, 共享专家rank数, 本地MoE专家数]，后接table1（ep_rank_id→local_rank_id）与table2（local_rank_id→ep_rank_id）两段映射，-1表示缺席rank。期望输出与x_ref相等（对象透传）。
- FakeTensor（主线test/core_tests/test_fake_tensor.py 2354–2363）：Meta注册（主线_meta_registrations.py 3524–3526、发布3302–3304）`torch.empty_like(x_ref)`直接返回，不校验group/world_size/time_out/elastic_info；用例也只断言result.shape == x_ref.shape。Meta通过不证明设备侧通信语义或参数合法性。

## 验证与失效边界

核对点：实际装载的CANN是否同时含V2与其GetWorkspaceSize符号（决定超时/弹性参数能否传入）、group字符串与world_size是否对应同一已建链通信域（错配的host层无检查——本文件对group内容、world_size数值、x_ref dtype/shape均无TORCH_CHECK）、参与rank集合是否与elastic_info映射一致（官方用例中缺席rank不调用，先于任何host检查达成）。跨rank行为、超时触发与弹性重组数值未运行验证，本卡无数值/性能/verified结论；不把该入口当作通用ProcessGroup barrier或`dist.barrier`的等价替代（其派发与文档口径均未建立）。

## Evidence

- [DistributeBarrierOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DistributeBarrierOpApi.cpp)（primary）：1–51；完整本地小文件。
- [DistributeBarrierOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DistributeBarrierOpApi.cpp)（primary）：1–48；完整本地小文件；与主线差异仅排版、文件尾缺`// namespace op_api`注释与末行换行。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–774；check_aclnn_kernel_available完整函数体。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792；同函数完整函数体，与主线语义相同仅排版。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：90（check_aclnn_kernel_available声明）、343–494（EXEC_NPU_CMD与EXEC_NPU_CMD_V1/V2宏体定向读；DO_COMPATIBILITY宏语义已由[CPU回退与兼容实现指南](../../guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)按同一主线pin读毕，本卡不重复展开）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：6662–6663；_npu_distribute_barrier条目。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：6445–6446；同条目，两pin逐字相同。
- [meta_registrations.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：3524–3526；_npu_distribute_barrier Meta注册。
- [meta_registrations.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）：3302–3304；同Meta注册，与主线同构。
- [test_distribute_barrier.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_distribute_barrier.py)（example）：1–156；完整文件（16卡弹性栅栏用例、elastic_info构造、设备门）。
- [test_distribute_barrier.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_distribute_barrier.py)（example）：1–156；与主线仅行尾空白差异（diff -u核对）。
- [test_moe_distribute_dispatch.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch.py)（example）：70–79；barrier调用形态定向读。
- [test_moe_distribute_dispatch_v2.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_moe_distribute_dispatch_v2.py)（example）：74–79；同上定向读。
- [test_moe_distribute_dispatch.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_moe_distribute_dispatch.py)（example）：72–75；同调用形态。
- [test_fake_tensor.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_fake_tensor.py)（example）：2354–2363；FakeTensor用例与shape断言定向读（发布侧该类用例未逐行核对，Meta注册已按两pin读毕）。
