---
type: Guide
title: logsumexp/logaddexp/gcd：amax组合回退、ACE命令与注册CPU往返
description: 区分logsumexp的aclnn直发与amax组合回退、logaddexp(2)的gen_opapi登记与LogAddExp命令、gcd.out的注册CPU往返，并核对Dimname版本边界与整数dtype提升。并含 logcumsumexp/logdet 零登记边界与 slogdet 双路实现。
tags:
- task.optimization
- topic.compute.reduction
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogSumExpKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSumExpKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogAddExpKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogAddExp2KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GcdKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogSumExpKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSumExpKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogAddExpKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogAddExp2KernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GcdKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SlogdetKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlogdetKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SlogdetKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlogdetKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/unsupported_ops_info_base.yaml
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/unsupported_ops_info_base.yaml
  role: constraint

created_at: '2026-11-12T21:19:30Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# logsumexp/logaddexp/gcd：amax组合回退、ACE命令与注册CPU往返

## 固定来源与实际边界

本卡聚合g17_reduction_scan账本中log域归约与相邻的gcd.out入口的op-plugin包装路由：logsumexp四个Schema（含Dimname两变体）、logaddexp/logaddexp2各两Schema（gen_opapi登记+aclops手写回退）、gcd.out单Schema。OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`，全部静态阅读：五个C++文件×主线与发布两版本整文件已读，pin差逐文件核对（见Evidence）。未导入上游、执行算子、模型或测试；平台范围未知，保持draft与空平台。归约shape与全轴dim列表推导复用[方差卡](torch_npu_variance_std_correction_and_cpu_roundtrips.md)已核对的reduce_ops_npu_output_size/get_dimlist_for_tensor结论；文档支持表行见[原生归约范围](torch_npu_native_torch_index_reduce_scope.md)与[特殊函数页](torch_npu_native_special_functions.md)（logsumexp的dtype表行，docs来源）；broadcast shape由broadcast_ops_npu_output_size推导（helper内部未在本卡展开）。CANN内核侧LogAddExp的base/scale/shift简化路线见[log_add_exp_950](../../../ops/ascendc/operators/aclnn/math/math/log_add_exp_950.md)、gcd的设备侧直接算子见[gcd_950](../../../ops/ascendc/operators/direct/math/math/gcd_950.md)——均为不同层，不与本卡重复。

## logsumexp：aclnn直发、整数Float提升与amax组合回退

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| Schema登记：logsumexp/logsumexp.out主线与发布两版本均acl_op+op_api all_version；logsumexp.names/.names_out主线登记[v2.1,v2.12]且C++以`!VERSION_BETWEEN(V2R13,VERSION_NEWEST)`保护，发布登记all_version（=其yaml头部枚举的v2.1..v2.12清单，非未来版本承诺）且C++无保护、Dimname无条件保留（主线yaml 3299–3313、发布3197–3211） | 与sort/argsort/kthvalue的命名维边界同构：主线V2R13起无Dimname重载，发布快照始终有 |
| op_api functional（主线36–48）：`DO_COMPATIBILITY(aclnnLogSumExp,acl_op::logsumexp)`后reduce shape推导；self为整型（isIntegralType含Bool）时dst_type提升**Float**、否则self dtype；`apply_tensor_without_format`申请后单次`EXEC_NPU_CMD(aclnnLogSumExp,self,dims,keepdim,result)` | 整数提升方向是Float（对照[方差卡](torch_npu_variance_std_correction_and_cpu_roundtrips.md)nansum小节：未显式给dtype时整数提升Long——同族归约不同提升方向，不互推）；DO_COMPATIBILITY为static双符号探测：缺失且Aclnn-only模式TORCH_CHECK抛"Current device only support aclnn operators, but ..."、否则ASCEND_LOGW后整函数return acl_op（主线op_api_common.h 94–119、发布96–110，宏体定向读） |
| op_api out（主线22–28）：DO_COMPATIBILITY后reduce shape，`check_tensor({self},result,result.scalar_type(),outputSize)`以**result自身dtype**校验，单次EXEC | check_tensor内部未核对；文件内不强制out为self dtype或Float，不保证host层无其余校验 |
| Dimname重载（主线30–34、50–54，保护内）：`dimnames_to_positions`转换后委托int重载 | 转换helper内部未核对 |
| acl_op functional/out（主线67–90）：out的CheckOut以self为参照（与op_api路以result自身为参照形成差异）；check_match不匹配走format_contiguous执行+format_fresh_view回写；nocheck核心（numel!=0）：`acl_op::amax(self,dims,true)`（keepdim=true逐位置最大）→keepdim?maxes:squeeze_multiple(maxes,dims)→`masked_fill_(|maxes|==INFINITY,0)`→ACE命令"ReduceLogSumExp"（Input=self.sub(maxes)与dims、attr keep_dims）→`result.add_(maxes_squeezed)`；numel==0走`at::sum_out(result,at::exp(self),dims,keepdim)`+`result.log_()`；末尾propagate_names_for_reduction | 显式log-sum-exp trick组合：amax/sub/masked_fill_/add_/exp/sum/log_均为ATen派发调用（各自最终路径未核对），ACE"ReduceLogSumExp"内核语义未核对；±INF max的masked_fill_0是包装侧数值保护，未运行数值验证；空输入走exp+sum+log组合而非ReduceLogSumExp命令；host命令数不作device kernel数 |
| pin差 | opapi与aclops两文件的差异均为两对V2R13 Dimname保护（主线有、发布无）+排版+文件尾注释（去注释去空白字符流等值）；其余token一致 |

## logaddexp/logaddexp2：gen_opapi生成路与ACE LogAddExp命令

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| Schema登记（主线3175–3207、发布3076–3108，逐字相同）：四条目acl_op+op_api all_version+gen_opapi规格——functional的out size=`broadcast_ops_npu_output_size(self,other)`、dtype=`at::native::result_type(self,other)`，`.out`条目只有size；exec分别为aclnnLogAddExp/aclnnLogAddExp2 | aclnnLogAddExp/aclnnLogAddExp2符号在主线与发布两版本全树rg仅命中yaml的gen_opapi exec登记、无手写op_api文件——op_api路为gencode生成体，不随仓提交 |
| 生成op_api路（模板语义推导，不物化生成C++）：按已核对生成器模板（DO_COMPATIBILITY仅登记acl_op时生成+按out规格申请/校验+单次EXEC，见[旧极值卡](../apis/torch_npu/legacy_min_max_and_sort.md)amax/amin小节的重读结论）：`DO_COMPATIBILITY(aclnnLogAddExp(2),acl_op::logaddexp(2))`后broadcast size、按规格dtype=result_type(self,other)申请、单次EXEC | dtype规格为`at::native::result_type(self,other)`调用表达式——该表达式在ResInfo中的解析细节未在重读，生成体不逐字物化；未运行gencode认证 |
| acl_op out/functional（主线两文件同构：out 39–50、functional 53–57）：broadcast shape后`apply_tensor(self,output_size)`——**dtype跟随self、无result_type升位**；out：logaddexp的CheckOut({self,other},result,self,output_size)与logaddexp2的CheckOut({self},result,self,...)——参照张量列表不对称按原文记录；check_match不匹配走format_contiguous/format_fresh_view | 混合dtype输入时：生成op_api路输出result_type（按规格推导）vs acl_op回退输出self dtype——两路输出dtype可观察差异（与[all/any卡](torch_npu_all_any_bool_reduction_routes.md)同族现象、方向不同）；CheckOut内部未核对 |
| ACE命令（两文件核心同构）：`cmd.Name("LogAddExp")`，attr base=-1（logaddexp）/base=2.0（logaddexp2）、scale=1、shift=0 | base/scale/shift为命令参数按原文记录；base==-1&&scale==1&&shift==0的内核简化路线见[log_add_exp_950](../../../ops/ascendc/operators/aclnn/math/math/log_add_exp_950.md)，本卡不重复其内核结论 |
| pin差 | 两aclops文件与主线去空白字符流相同（仅排版） |

## gcd.out：注册的CPU往返与生成路委托

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| Schema登记（主线2413–2419、发布2338–2344，逐字相同）：仅`gcd.out`登记（acl_op+op_api all_version+gen_opapi：size=broadcast_ops_npu_output_size(self,other)、exec aclnnGcd）；`gcd` functional在两份yaml均rg零登记 | 负证据限定这两份OpPlugin YAML：ATen把torch.gcd路由到何处（经gcd.out或组合）未核对，不外推为主线NPU整体无gcd能力 |
| acl_op gcd_out（主线与发布两版本逐字节相同，主线21–31）：`TORCH_NPU_WARN_ONCE("Warning: kernel [gcd.out] is not supported by NPU currently.Now this kernel is running on CPU.")`后self/other/out全部`.cpu()`、`at::gcd_out`计算、`out.copy_(out_cpu)`回写 | 注册的acl_op路本身是CPU往返（与[排序卡](torch_npu_sort_topk_routing_and_legacy_output_costs.md)nanmedian小节同模式：告警+往返+回写）；这是登记回退，不是DO_COMPATIBILITY符号回退；at::gcd_out的CPU实现未核对 |
| 生成op_api路（模板语义推导）：`DO_COMPATIBILITY(aclnnGcd,acl_op::gcd_out)`后broadcast size、out按缺省ResInfo解析（out自身dtype）校验/申请、单次EXEC_NPU_CMD(aclnnGcd,...) | aclnnGcd符号缺失时：Aclnn-only模式TORCH_CHECK抛错、否则ASCEND_LOGW后落入上行的CPU往返路——生成路的回退目标就是该CPU往返；aclnnGcd内核语义未核对 |

## 优化与验收边界

logsumexp在attention统计与损失合并中高频出现：迁移或性能定位先核对实际派发（aclnn符号可用性、Aclnn-only开关）——acl_op回退是amax+sub+ReduceLogSumExp+add_的多段host组合（空输入另走exp+sum+log），计入端到端测量。logaddexp混合dtype输入先核对派发路再预期输出dtype。gcd.out默认即告警CPU往返，热路径应显式记录该成本而非假设NPU执行。本卡静态口径，无数值、性能或verified结论，不把任一路径写成推荐配置。

## Evidence

- [LogSumExpKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LogSumExpKernelNpuOpApi.cpp)（primary）：1–56；完整本地小文件。
- [LogSumExpKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogSumExpKernelNpu.cpp)（primary）：1–92；完整本地小文件。
- [LogAddExpKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogAddExpKernelNpu.cpp)（primary）：1–59；完整本地小文件。
- [LogAddExp2KernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LogAddExp2KernelNpu.cpp)（primary）：1–59；完整本地小文件。
- [GcdKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GcdKernelNpu.cpp)（primary）：1–33；完整本地小文件；与发布逐字节相同。
- [LogSumExpKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LogSumExpKernelNpuOpApi.cpp)（implementation）：1–56；完整本地小文件；与主线差异为两对V2R13 Dimname保护（发布无）+排版+文件尾注释（去注释去空白字符流等值，整文件diff -u核对）。
- [LogSumExpKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogSumExpKernelNpu.cpp)（implementation）：1–95；完整本地小文件；与主线差异为两对V2R13保护（发布无）+排版（去注释去空白字符流等值）。
- [LogAddExpKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogAddExpKernelNpu.cpp)（implementation）：1–63；完整本地小文件；与主线去空白字符流相同（仅排版）。
- [LogAddExp2KernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LogAddExp2KernelNpu.cpp)（implementation）：1–63；同上口径。
- [GcdKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GcdKernelNpu.cpp)（implementation）：1–33；与主线逐字节相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2413–2419、3175–3207、3299–3313；gcd.out/logaddexp族/logsumexp族条目完整字段（含各末行exec/op_api）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2338–2344、3076–3108、3197–3211；同口径（gcd/logaddexp族与主线逐字相同；logsumexp.names/.names_out版本字段不同——主线[v2.1,v2.12]、发布all_version，按原文记录）。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：94–119；DO_COMPATIBILITY宏定义定向读。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：96–110；同口径，语义相同仅排版差异。

## logcumsumexp/logdet：零登记名与 slogdet 已登记实现的对照

本节处理g17/g23账本中log域的未登记名。per_name_index 1151名核对：logcumsumexp与logdet均不在登记面。两份yaml全文rg零命中（“logdet”字样的命中全部来自slogdet/logabsdet子串，无独立`- func: logdet`条目）；主线与发布两版本无对应手写opapi/aclops文件。logcumsumexp在主线与发布两版本全树的唯一命中是测试侧`test/unsupported_ops_info_base.yaml`的跳过声明（主线7444–7452、发布7431–7439，内容逐字相同：test_conj_view complex64、test_neg_conj_view complex128、test_neg_view float64、test_out float32）。该文件按算子名列“测试类别→跳过dtype”，与`__rmul__`等条目同构，是测试配置不是支持或能力声明。ATen把torch.logcumsumexp/torch.logdet路由到何处（组合分解、torch_npu侧注册或CPU回退）在op-plugin源集内不可见：保持未确认，不据零注册断言NPU整体无该能力，也不把测试跳过项当实现证据。

slogdet是同族已登记名（g23表行已映射至[矩阵信号卡](torch_npu_native_torch_matrix_signal_scope.md)），本节补其包装层实现：主线与发布两版本 yaml均登记`acl_op+op_api all_version`（主线4759–4761、发布4605–4607），仅functional一个Schema（返回sign/logabsdet二元组，无out变体）。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api slogdet（主线23–39、发布23–38，主线与发布两版本去空白字符流等值）：`DO_COMPATIBILITY(aclnnSlogdet, acl_op::slogdet(self))`后TORCH_CHECK ndimension>=2（原文“Expected nonempty least 2D tensor, but got a tensor with sizes ...”），输出size=self.sizes()去末两维，`apply_tensor`按self options申请sign/log两个同形输出，单次`EXEC_NPU_CMD(aclnnSlogdet, self, sign, log)` | apply_tensor（非without_format变体）内部格式策略未核对；包装层无dtype检查——矩阵信号卡表行“input=FP32/COMPLEX64/COMPLEX128”与“slogdet可能CPU回退”提示是docs支持表口径，不在本层强制；aclnnSlogdet对复数等dtype的实际处理未核对 |
| acl_op slogdet（主线32–41、发布39–48）：TORCH_CHECK dim>=2（文案不同：“input must be at least 2 dimensions”），同一“去末两维”输出规则，`apply_tensor`申请sign/y后经ACE命令"LogMatrixDeterminant"（Input self，Output顺序sign在前、log在后） | host命令名≠device kernel；LogMatrixDeterminant内核语义与dtype支持面未核对；该路无DO_COMPATIBILITY（自身即回退终点） |
| pin差 | opapi/aclops两文件主线与发布两版本均为排版差异（去空白字符流等值），无行为差；yaml条目逐字相同 |

logdet与slogdet不互推：ATen是否把torch.logdet组合到slogdet未核对；即使组合成立，最终分发落到NPU还是CPU由torch_npu/ATen侧决定，不在本卡断言。

### logcumsumexp/logdet/slogdet 补充证据

- [SlogdetKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SlogdetKernelNpuOpApi.cpp)（primary）：1–42；完整本地小文件。
- [SlogdetKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SlogdetKernelNpu.cpp)（primary）：1–43；完整本地小文件。
- [SlogdetKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SlogdetKernelNpuOpApi.cpp)（implementation）：1–40；完整本地小文件；与主线去空白字符流等值（仅排版）。
- [SlogdetKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SlogdetKernelNpu.cpp)（implementation）：1–50；完整本地小文件；与主线去空白字符流等值（仅排版）。
- [unsupported_ops_info_base.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/unsupported_ops_info_base.yaml)（constraint）：7444–7452；logcumsumexp条目（文件头部结构1–20同读：按算子名列测试类别→跳过dtype的配置）；其余条目未核对。
- [unsupported_ops_info_base.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/unsupported_ops_info_base.yaml)（constraint）：7431–7439；同口径，内容与主线逐字相同。
- 负向证据：logcumsumexp/logdet在主线与发布两版本的`op_plugin/config/op_plugin_functions.yaml`全文rg零命中（logdet仅slogdet/logabsdet子串命中）；主线与发布两版本 `op_plugin/ops/`全树无对应实现文件（logcumsumexp全树唯一命中上述测试yaml）；per_name_index 1151名零登记。
