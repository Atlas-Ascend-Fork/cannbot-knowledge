---
type: Guide
title: 普通排序与TopK：符号路由、索引和旧ACL准备成本
description: 区分TopK V2能力路由、sort稳定性重载与argsort警告，并核对旧ACL非尾轴转置、INT32中间索引及out临时写回。并含 kthvalue/median/nanmedian 的 aclnn 路由、FP16 topk 组合回退与 nanmedian CPU 往返。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SortKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TopKKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArgSortKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TopKKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SortKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SortKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TopKKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArgSortKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TopKKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SortKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KthvalueKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/KthvalueKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MedianKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KthvalueKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/KthvalueKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MedianKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-11T10:35:22Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 普通排序与TopK：符号路由、双输出和旧ACL准备成本

## 固定来源与实际边界

本卡聚合普通sort、argsort、topk的OpAPI入口，以及普通非stable sort/topk兼容到旧ACL时的本地实现。OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`，不是某个已测设备或安装环境的证明。未导入上游、加载符号库、执行排序、搬运、模型或测试，平台范围未知，保持draft与空平台。

[torch公开索引与排序范围](torch_npu_native_torch_index_reduce_scope.md)和[Tensor方法范围](torch_npu_native_tensor_index_reduce_scope.md)保留文档支持矩阵、950DT稳定性及sorted约束；本卡补真实包装路由与准备，不用局部源码参数透传覆盖产品文档限制。[旧npu_sort_v2](../apis/torch_npu/legacy_min_max_and_sort.md)只返回values，不能与本卡sort的(values,indices)混用；MoE gating、group topk及TopKTopPSample是不同入口。

## 主线TopK的V2选择由双符号探测决定

主线topk和topk_out分别在自己的函数局部static bool中缓存check_aclnn_kernel_available("aclnnTopkV2")结果。helper检查API名和API名拼接GetWorkspaceSize的两个符号地址，任一为空即false；它是可查到符号的条件，不是对当前shape/dtype/设备合法性、性能或执行成功的试运行。

V2可用时直接调用aclnnTopkV2，额外传常量SORT_POLICY=1，注释称其为bitonic；不可用时才先做DO_COMPATIBILITY(aclnnTopk,旧ACL表达式)，随后走aclnnTopk。不能把注释当作已经证明硬件内部总使用某算法或V2总比旧实现快，也没有本地捕获V2执行异常后再重试旧路径。static结果不是每次调用重新探测；两个函数也不是共享一个统一可变能力状态。

发布普通topk只使用aclnnTopk及其DO_COMPATIBILITY，没有V2探测和policy参数。DO_COMPATIBILITY中的表达式属于旧ACL分派，不自动表示CPU计算；本卡没有把未知SDK内部路径视为已审设备Kernel。

## TopK输出shape、索引类型与0D特殊分支

通用shape helper先make_wrap_dim，再复制self.sizes；仅当shape非空时，把目标维长度改为k。所读helper没有本地验证k的完整合法范围；外部维度处理与SDK契约另计，不能把最终shape申请成功当作所有参数已验证。OpAPI functional按self选项申请values、按Long申请indices；out则按self dtype检查values、按Long检查indices。

两版topk_out都把self.rank==0且k==0的分支置于兼容检查之前：它要求**values和indices都为Long**，resize_as_(self)，分别fill_(self)和fill_(0)，直接返回两个引用。这里values的检查与普通分支按self dtype检查不同，不应照常规TopK惯例改写源码，更不由分支存在就认证文档未支持的标量输入。

functional的同一特殊分支返回zeros_like(self).fill_(self)和Long的zeros_like。主线在兼容探测及shape helper之前早返；发布先做aclnnTopk兼容检查和shape helper，再执行这个特殊分支。不能将两版都概括为“标量必定免兼容分派与shape准备”，也不能从k=0推导返回的是普通一维空结果。本卡未运行该边界，不将本地fill表达式解释为无Host/设备成本。

## sort与stable重载不能合并路由规则

普通sort functional先做aclnnSort兼容检查，申请values与Long indices，向sort_output传stable=false。普通out也做兼容检查，但check_tensor的dtype实参分别取values自身与indices自身，不在这里显式强制indices为Long；该实参事实不等于任意out dtype均获SDK支持。

接收optional stable的functional/out是独立实现：先明确拒绝self为Double，None默认false，直接EXEC_NPU_CMD(aclnnSort)，局部**没有**普通重载的DO_COMPATIBILITY。functional仍申请双输出，out仍按各自dtype检查。不能因未指定稳定性的一路有旧ACL兼容表达式，就保证stable入口也具备同样回退；也不能由普通重载没有同一Double断言反推它支持FP64。

两版OpAPI都没有在这些sort主体显式把非尾轴转到最后或预先把self转FP32；其下SDK是否再做布局/类型处理另核。stable布尔透传不替代特定产品文档的强制稳定性约束。

## argsort丢弃values结果，不代表没有双输出准备

argsort按是否含stable参数调用at::sort，然后取元组的第1项indices。局部没有另一个只申请索引的专用执行路径；但ATen的最终派发必须结合实际环境判断，不能仅据语法调用就认证每次一定命中本卡OpAPI sort，或据最终只返回indices就省略所选sort的values申请成本。

两版都对Int/Long输入发一次性性能警告，文案称旧路径在AiCPU执行并建议cast到FP32。主线加了GetSocVersion()<Ascend950门槛，发布没有此SoC条件；主线注释说Regbase支持Int/Long排序，仍不构成全产品/所有dtype运行验证。**包装只发warning，没有在此显式转CPU或cast FP32**；不能把这段文案当作测得CPU分派，也不能未经数值与tie顺序验证就自动将整数排序改为浮点排序。

主线argsort Dimname、普通sort的Dimname及旧ACL sort Dimname包装均有!VERSION_BETWEEN(V2R13,VERSION_NEWEST)编译条件，Schema将这些命名维注册限定[v2.1,v2.12]；发布相应命名维Schema为all_version且所读C++没有该保护。stable argsort的OpAPI声明为[v2.1,newest]，stable sort只有OpAPI声明；普通topk两版acl_op/op_api均[v2.1,newest]。这些是精确固定声明，不是未知安装包已导出所有重载的证明。

## 旧ACL非尾轴路线会增加转置与临时输出

旧ACL sort/topk的内部helper都把dim规范化，与最后一轴比较。若不是最后一轴，构造交换这两轴的perm，调用npu_transpose(self,perm,true)，申请转置shape的values和indices临时对象，在最后一轴执行，再分别npu_transpose_out写回两份输出；尾轴则直接调用本地核心命令。shape helper只按perm取输入对应size，不是设备物理复制实现的证明。

旧TopK核心命令名是**TopKV2**，把k放到SmallVector并以Int输入，透传dim/largest/sorted；它不等于OpAPI的**aclnnTopkV2**符号或policy机制。旧Sort命令名Sort，传axis/descending，所读旧入口没有stable参数。不把两个相似名字或参数集合合并为同一后端。

这些都是本地明确的转置、临时申请和写回请求，具体npu_transpose、格式工具、分配器和OpCommand执行内部未在本卡重新核对，不能直接报固定物理复制次数/字节或耗时。改变排序轴、预排布局或只保留indices的模型优化，仍须验证调用者布局、数值和梯度，再比较完整准备与执行成本。

## 旧ACL的INT32中间索引与out写回不同

旧ACL topk先请求CastBackToOriFormat(self)。functional按该对象申请values，indices申请Int、ND格式，核心执行后再_npu_dtype_cast到Long返回。out先CheckOut values与ND/Long indices，将indices cast成Int临时对象，再检查values和临时indices是否check_match；任一不匹配时，仅对不匹配对象请求format_contiguous，执行后按需format_fresh_view。

topk out的末尾原文是将**indices本身**再cast为Long并赋回引用，然后indices.copy_(indices_cp)。不要把它擅自改述为先将indices_cp转Long；该复制是否转换及原storage/别名效果依赖外部实现，本卡没有复现或认证任意别名安全。

旧ACL sort functional按self申请values，Int/NCHW indices，执行后把indices转Long。out按NCHW/Long检查目标索引，同样先cast到Int、check_match、按需format_contiguous与format_fresh_view，但末尾是将**indices_cp**转Long再copy_到indices。两条out路线都不能因返回原引用就视为无临时对象或无复制，也不能把check_match简单替换为Tensor.is_contiguous()或假定format_fresh_view的完整语义。

以上两个旧ACL文件的两版主体除命名维保护与排版等明确差异外按完整文本/token核对；其INT32中间索引、最后转Long、轴转置与out整理同属固定旧路线。它们不证明任意超大维度索引无损，也不能据OpAPI直接申请Long就倒推SDK内部从不用Int。实际评估应记录准确重载、SoC、符号可用性、轴、k、stable/sorted、out dtype/格式与后端，再分离准备成本；本卡没有数值、性能或verified结论。

## Evidence

- [SortKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SortKernelNpuOpApi.cpp)（primary）：1–115；完整本地入口与辅助函数。
- [TopKKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TopKKernelNpuOpApi.cpp)（primary）：1–89；完整本地入口与辅助函数。
- [ArgSortKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ArgSortKernelNpuOpApi.cpp)（primary）：1–52；完整本地入口与辅助函数。
- [TopKKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/TopKKernelNpu.cpp)（implementation）：1–126；完整本地入口与辅助函数。
- [SortKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/SortKernelNpu.cpp)（implementation）：1–130；完整本地入口与辅助函数。
- [op_api_common.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）：767–773；仅所列完整helper/Schema，其他内容保持未核对。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1438–1455；仅所列完整helper/Schema，其他内容保持未核对。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1164–1173、4902–4922、5127–5133；仅所列完整helper/Schema，其他内容保持未核对。
- [SortKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SortKernelNpuOpApi.cpp)（implementation）：1–106；完整本地入口与辅助函数。
- [TopKKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TopKKernelNpuOpApi.cpp)（implementation）：1–73；完整本地入口与辅助函数。
- [ArgSortKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ArgSortKernelNpuOpApi.cpp)（implementation）：1–47；完整本地入口与辅助函数。
- [TopKKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/TopKKernelNpu.cpp)（implementation）：1–149；完整本地入口与辅助函数。
- [SortKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/SortKernelNpu.cpp)（implementation）：1–152；完整本地入口与辅助函数。
- [op_api_common.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）：785–792；仅所列完整helper/Schema，其他内容保持未核对。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1283–1302；仅所列完整helper/Schema，其他内容保持未核对。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1126–1135、4748–4768、4961–4967；仅所列完整helper/Schema，其他内容保持未核对。

## kthvalue/median/nanmedian：aclnn直发、topk组合回退与nanmedian的CPU往返

本节把第k值与中位值两个次序统计入口并入本卡的排序族视角，固定来源仍是OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`，全部为静态阅读；上文sort/topk/argsort结论不因本节改写。kthvalue两份文件与median的aclops文件为手写实现，主线与发布两版本整文件已读（差异见下方证据review_mode）；median/nanmedian的op_api侧由yaml gen_opapi登记，生成包装体不随仓提交——生成器模板语义已由[原生激活卡](torch_npu_native_activation_precision.md)按同一主线版本的struct_codegen.py读取核对，本节不重复物化生成C++，只登记yaml规格与手写acl_op路径。

### kthvalue：手写双路与FP16组合回退

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| op_api主路（主线与发布两版本同构）：每个重载先`DO_COMPATIBILITY(aclnnKthvalue, acl_op::同名实现)`；functional按`reduce_ops_npu_output_size(self,{dim},keepdim)`推导，values用`apply_tensor_without_format`+self选项、indices同helper+Long；out（.values）先`check_tensor({self},values,self.scalar_type(),size)`与`check_tensor({self},indices,Long,size)`，再单次`EXEC_NPU_CMD(aclnnKthvalue,self,k,dim,keepdim,values,indices)`（主线opapi 23–76、发布23–91） | DO_COMPATIBILITY为函数级static双符号探测（aclnnKthvalue与其GetWorkspaceSize）：缺失且Aclnn-only模式TORCH_CHECK抛"Current device only support aclnn operators, but ..."，非Aclnn-only则ASCEND_LOGW后整函数return acl_op实现（主线op_api_common.h 94–119、发布96–110，宏体定向读）。索引两侧固定Long；文件内无显式k/dim/dtype的TORCH_CHECK预检——shape经reduce_ops_npu_output_size、out经check_tensor helper、Dimname重载经dimname_to_position转换，这些helper内部与SDK侧约束路径未核对，不据此断言host侧无其余校验或全部合法性都在SDK |
| Dimname重载 | 主线yaml登记`[v2.1, v2.12]`且C++以`!VERSION_BETWEEN(V2R13, VERSION_NEWEST)`保护；发布同两条目登记all_version（该yaml头部all_version=v2.1..v2.12枚举清单）且C++无该保护，`dimname_to_position`转换后与int重载同构。与上文argsort/sort的命名维边界同构：主线V2R13起无Dimname重载，发布快照始终有 |
| acl_op回退入口：`check_self_dim`先TORCH_CHECK self∈{FP16,FP32,INT32}（原文"the type of input must be float16, float32, or int32"），make_warp_dim后TORCH_CHECK `k>=0且k<=size(dim)`（原文"selected index k out of range"；dim为负时按wrap后轴检查）（主线aclops 100–107、发布96–103） | dtype门槛只存在于这条回退路径；opapi主路文件无此检查，不能反向推断aclnn侧支持更宽dtype，也不能把门槛当成两路共同前置。检查放行k=0而取值索引填k-1，k=0时索引为-1：其下游行为未核对未运行，不断言 |
| 回退计算（kthvalue_out_nocheck/calculate）：self非FP16先`custom_ops::_npu_dtype_cast(self,Half)`（torch_npu 侧实现，来源未核对）；`at::topk(self,k,dim,largest=false,sorted=true)`取最小k个；申请Int单元素index、`acl_op::fill_(index,k-1)`、`acl_op::index_select`取第k个值；非FP16输入的values再cast回self dtype、indices cast到Long；`propagate_names_for_reduction`（主线aclops 72–134） | INT32输入在该路径先变FP16参与topk与选择再cast回Int：FP16尾数有限，大整数不保证位精确，此边界由显式cast链派生、未运行数值验证。`at::topk`经ATen派发，最终命中路径随版本/构建确定；cast、fill、index_select为host侧多段请求，不等于device kernel数，也不在此计成本 |
| out整备（aclops）：functional的indices用`apply_tensor_with_format(...,Long,ACL_FORMAT_NCHW)`申请、values用apply_tensor；kthvalue_out的CheckOut对values取`get_tensor_npu_format(values)`+self dtype、对indices固定ACL_FORMAT_ND+Long；shape_modify对undefined输出才at::empty，defined输出TORCH_CHECK dtype/device后resize_（主线aclops 25–70、137–179） | CheckOut/check_tensor/get_tensor_npu_format内部未核对；NCHW申请与ND检查的格式差异按原文记录，不解释为运行格式转换次数；defined输出的resize_在位扩展不是新分配承诺 |

### median/nanmedian：gen_opapi登记、topk组合与CPU往返

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| Schema登记：median/median.dim/median.dim_values、nanmedian/nanmedian.dim主线与发布两版本均acl_op+op_api all_version并带gen_opapi规格：输出size统一`reduce_ops_npu_output_size(...)`，values dtype=self、indices dtype=at::kLong（nanmedian.dim的值输出块名为`output`）（主线yaml 3510–3538、3704–3722；发布3408–3436、3591–3609，逐字相同） | gen_opapi生成体不随仓提交；按同一pin生成器模板的既有结论，生成路为DO_COMPATIBILITY+按规格申请/校验+单次EXEC_NPU_CMD。规格只声明host侧申请形态，不是device kernel数或dtype支持面的证明 |
| 全局median（aclops）：numel<=0直接`at::full({},quiet_NaN).to(self.options())`返回；否则flatten——主线V2R13保护内`has_names?self.rename(nullopt).reshape({-1}):self.reshape({-1})`、保护外`self.reshape({-1})`（两个编译分支都reshape({-1})，仅rename按has_names条件性，flatten非可选）；发布以has_names三元判断、无保护。k=numel/2，`at::topk(input,k+1)`（largest缺省true降序）取`topk_values[k]`，`acl_op::fill_(result,value)`（主线30–48、发布31–47） | 取降序第k+1个（0起k），偶数个元素取到较小一侧中位值；该组合只描述源码步骤，未与torch中位值语义做运行等价验证 |
| median.dim（aclops）：make_warp_dim后k=(size(dim)+1)/2，`at::topk(self,k,dim,largest=false,sorted=true)`升序k个；Long单元素index（NCHW格式申请）填k-1；values与indices各自`acl_op::index_select`后按keepdim squeeze_、copy_写回，双输出propagate_names（主线51–84） | values/indices取同一topk结果两侧的同序号；host侧两次index_select、copy_为多段请求，不作device kernel计数 |
| median out整备（aclops）：values CheckOut(ND,self dtype)、indices CheckOut(ND,Long)；check_match不匹配者走format_contiguous临时对象执行后format_fresh_view刷新（主线99–126） | CheckOut/check_match/format工具内部未核对（与上文sort/topk旧ACL out整备同族）；匹配分支直接执行不等于零拷贝 |
| nanmedian（aclops）：全局重载`TORCH_NPU_WARN_ONCE("Warning: kernel [nanmedian] is not supported by NPU currently. Now this kernel is running on CPU.")`后`self.to("cpu")`→`at::native::nanmedian_cpu`→`.to(self.device())`；dim重载用`TORCH_WARN_ONCE`（无NPU_前缀）且先按reduce shape申请NPU values/indices再全部`.cpu()`→`at::native::nanmedian_out_cpu`→逐项`.to(self.device())`（主线145–170、发布129–156） | 这是acl_op路线内的固定CPU往返与告警，不是DO_COMPATIBILITY驱动的符号回退；op_api侧仍按gen_opapi登记aclnnNanMedian/aclnnNanMedianDim，实际是否落到CPU往返取决于派发模式与符号可用性，本节未运行。nanmedian_cpu/nanmedian_out_cpu为CPU ATen实现未核对；.cpu()/.to()的拷贝次数、同步与别名行为不作断言；两条告警的宏与文案差异按原文记录 |
| pin差 | 主线aclops对kthvalue/median的rename分支与Dimname包装带V2R13编译保护，发布无保护（发布kthvalue的rename无条件、median按has_names三元）；kthvalue/median/nanmedian的Schema登记除kthvalue.dimname主线与发布两版本版本区间不同外逐字相同 |

### kthvalue/median/nanmedian 补充证据

- [KthvalueKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KthvalueKernelNpuOpApi.cpp)（primary）：1–96；完整本地小文件。
- [KthvalueKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/KthvalueKernelNpu.cpp)（implementation）：1–193；完整本地小文件。
- [MedianKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MedianKernelNpu.cpp)（implementation）：1–171；完整本地小文件。
- [KthvalueKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KthvalueKernelNpuOpApi.cpp)（implementation）：1–92；完整本地小文件；与主线差异仅两对`#if !VERSION_BETWEEN(V2R13, VERSION_NEWEST)`命名维保护（发布无保护），其余token等价（整文件diff -u与去空白字符流核对）。
- [KthvalueKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/KthvalueKernelNpu.cpp)（implementation）：1–180；完整本地小文件；与主线差异为V2R13保护、`#else self_rename=self`分支（发布无条件rename(nullopt)）与尾部空行，主体一致（整文件diff -u核对）。
- [MedianKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MedianKernelNpu.cpp)（implementation）：1–157；完整本地小文件；与主线差异为V2R13保护（发布rename按has_names三元、Dimname nocheck helper无条件保留），其余仅排版（整文件diff -u核对）。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：60–160；DO_COMPATIBILITY/DO_COMPATIBILITY_COMMON宏定义与GetOpApiFuncAddr工具定向读。
- [op_api_common.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：90–118；DO_COMPATIBILITY宏定义定向读。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2874–2888、3510–3538、3704–3722；kthvalue/median/nanmedian所选条目（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2788–2801、3408–3436、3591–3609；同口径。
