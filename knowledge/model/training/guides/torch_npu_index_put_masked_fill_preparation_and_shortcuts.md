---
type: Guide
title: 索引写入与掩码填充：复制、动态定形和快捷路径
description: 聚合index_put与masked_fill的连续克隆、主线掩码快捷分支、布尔索引NonzeroV2同步、临时dtype转换和索引设备搬运边界。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexPutKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedFillKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/AdvancedIndex.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexPutKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedFillKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/AdvancedIndex.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
created_at: '2026-11-11T10:29:43Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 索引写入与掩码填充：复制、定形和标量快捷路径

## 固定入口与版本边界

本卡聚合OpAPI的index_put、index_put_、_index_put_impl_与masked_fill_两种value重载。OpPlugin主线固定`d84e9b1d6a558e5f27973cd4329f62968e46fdda`，发布固定`dedc316708372c9a8bfde4527abd2a94b74840f5`；两版所列Schema对这五个入口均声明acl_op/op_api为all_version。这是固定注册声明，不是任意dtype、设备、别名、产品或安装组合的支持证明。

通用SYNC与标量复制的框架证据复用[动态选择与Where](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)已经核对的两仓固定来源。TorchNPU分别是主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`；这些是各仓独立快照，不认证并列提交可直接组成已验证安装环境。本文没有运行上游、设备、数值或性能实验，保持draft与空平台。

## 函数式写入先保留self，CPU分派也有顺序

两版index_put先执行DO_COMPATIBILITY，然后请求`self.clone(MemoryFormat::Contiguous).index_put_(...)`。因此函数式入口包含保留原值与连续布局克隆请求，不能只按一次索引更新估算准备成本。index_put_本身不clone，而是调用`at::_index_put_impl_(self,indices,value,accumulate,false)`；直接内部入口还接收unsafe。

内部入口同样先执行DO_COMPATIBILITY，之后才在self设备为CPU时委托at::native::_index_put_impl_。兼容表达式指向旧ACL实现，不等于CPU回退；没有展开旧ACL实现或把外部ATen派发直接调用视为已运行证明。functional与inplace的别名、后续消费者和梯度条件也不能因局部更新相同就互换。

## 主线掩码快捷路径：提前读取value，检查次序不同

发布IndexPut包装没有以下快捷分支。主线在CPU委托之后，对self内部overlap为YES只发expanded Tensor弃用警告，随后仅在`!accumulate`、self与value各自dtype均属于Float/Half/Int/Long/Char/Bool/BFloat16集合时尝试masked_fill；这里是分别检查集合成员，不要求两者dtype相等。

canDispatchToMaskedFill要求value.numel()==1，不要求rank为零。每个缺省或undefined索引占一个维度；defined索引必须是同self设备的Byte/Bool，且此前还没有defined mask，其维度大小须匹配self相应维度。末尾对剩余self维度追加unsqueeze(-1)。它限制的是**至多一个defined mask**，没有结束前mask.defined()断言，不能把全None/空索引等外部合法性概括成“本地已验证恰好一个有效掩码”，也没有在本卡复现这些边界的运行结果。

成功返回后直接`self.masked_fill_(mask,value.item())`：value可以是一元素NPU Tensor，代码没有把.item()限定为CPU读取。这个Host Scalar求取位置应纳入性能定位，实际派发、等待及耗时另测。该return发生在通用索引展开、空Tensor占位与后面的self/value/index overlap检查之前；不能把通用路径检查保证机械套给此快捷路径。

主线通用路径的check_no_overlap仅明确拒绝PARTIAL或FULL，并未笼统拒绝所有无法判定的重叠状态；它对value及has_value的索引执行检查。unsafe继续传给SDK，不取消上述本地流程。发布没有新增的内部overlap警告、此快捷路径及这些显式check_no_overlap调用，不能回填主线拒绝条件。

## 布尔索引展开是动态输出工作，不是静态shape换算

两版通用路径checkIndexTensorTypes允许Long/Int/Byte/Bool，只有已定义索引之间dtype不同时才将needCast置真；不是看到Int就无条件转换。npu_expand_tensors先把已定义且设备不同的索引to(self.device())；Byte发弃用警告，Byte/Bool逐维检查mask大小，再按每个mask维度生成一条Long坐标索引。

当前入口传flag_aclnn=true，选择AdvancedIndex.cpp内部的npu_nonzero_aclnn。它与普通nonzero包装的布局不同：上界是`[mask.dim(),mask.numel()]`，输出按Long申请，调用**aclnnNonzeroV2**，再取每个维度的`nonzero.select(0,j)`。缺少该算子的兼容表达式指向本文件npu_nonzero_aclop，后者用同样上界、OpCommand NonZero、transpose=true与Sync({0})请求执行；本卡不将旧ACL的Sync实现进一步等同于某个固定设备等待协议。

NonzeroV2路径缓存并检查aclGetViewShape地址，使用EXEC_NPU_CMD_SYNC，再以holder.Get<1>()查询实际shape，resize输出，正常路径delete[]并置空返回维度。该SYNC宏通过已审RunOpApiV2(...,true)明确请求末尾当前流同步；它不能仅解释为Host任务入队。这里的主线deterministic snapshot与发布SetDeterministic差异沿用已有证据，不能说宏全token同一，也不由同步请求推出所有流/设备/捕获场景已支持。异常清理没有在此新增统一RAII核对证明。

因此高阶布尔索引可能包含索引设备迁移、按mask数量的动态Nonzero与定形请求。最终写入元素少或self/value为空，都不自动证明这些准备已被跳过。needCast为真时，展开结果中仍为Int的索引to(Long)；全Int且未触发混合dtype时，这个循环不改它们。

## 形状验证的临时cast，不等于传给SDK的索引

make_info还调用外部expandTensors，并在本地npu_expand_outplace中归并广播shape。该helper忽略undefined，shape已经相同则复用句柄；需要expand且索引dtype为Long时，先to(Int)再expand，其他dtype直接expand。仅这次npu_expand_outplace调用由局部std::exception捕获并转换为广播shape错误，不是整条索引执行出错后自动回退协议。

随后make_info补undefined索引到self维数，必要时调用外部hasContiguousSubspace/transposeToFront，并再次将异设备索引to(self.device())；这些外部ATen helper的完整行为没有在本卡核对。AdvancedIndex构造记录被索引维度的size/stride，在replacement_shape不包含0而indexed_sizes包含0时提前报错；restride_src去掉被索引维度、插入替换shape与零stride并as_strided，reshape_indexer在前后追加单维reshape，非Long时再to(Long)。这些是形状验证临时对象中的真实转换请求，不由方法名认定都是纯metadata操作。

外层用info.src.sizes()验证value能否广播：value rank不得超过目标，尾部维度须相等或为1。**实际aclnnIndexPutImpl参数仍是原self、由indices_after构建的列表与原value，不是info.src/info.indices。** 因而不能把make_info内部Long→Int→Long的临时路径描述成SDK入口必定接受或统一改为某一索引位宽，也不应未经验证把这些检查和临时转换直接删掉。

## None占位、末尾空输入判断与MaskedFill Tensor复制

通用路径在make_info之前无条件请求shape为{0}的emptyTensor作为None占位，之后将indices_after的undefined替换成该对象；即使这次全为defined索引，局部申请表达式仍已求值，但零元素申请不证明存在正数设备storage字节。最终列表还有一次异设备索引to(self.device())循环，**它不迁移value**。

仅在完成上述展开、占位、形状验证和列表准备后，才判断self.numel()!=0且value.numel()!=0并调用aclnnIndexPutImpl，原accumulate/unsafe继续透传。不要据最后跳过SDK就声称空输入没有clone、同步、cast或检查成本。

masked_fill_的Tensor重载先计算输出names，再做DO_COMPATIBILITY。value命中OpPreparation::IsCPUScalar时先.item()，然后copy_scalar_to_device(value dtype,self.device())，再传临时Tensor给aclnnInplaceMaskedFillTensor；否则传原value，没有在此把所有value或mask统一搬运/改型。该谓词实际为rank0且非NPU，而非wrapped-number标志或严格CPU设备白名单；已经审过的复制helper包含目标NPUGuard、dtype准备、pinned Host Tensor和PrivateUse1复制请求，non_blocking请求不认证复制与计算重叠。

Scalar重载则把Scalar直接交aclnnInplaceMaskedFillScalar，局部没有Tensor物化，两种重载末尾都传播names并返回self引用。主线index_put掩码快捷路径传入value.item()得到的Scalar，不能把Tensor重载的额外copy_scalar流程机械加到它。实际设备性能评估需保留正确入口、dtype/设备、mask形状、accumulate及别名约束，分别记录clone、值读取、mask定形与写入；本卡没有固定复制次数、耗时或verified结论。

## Evidence

- [IndexPutKernelNpuOpApi.cpp op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/IndexPutKernelNpuOpApi.cpp)（primary）：1–168；完整本地小文件。
- [MaskedFillKernelNpuOpApi.cpp op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedFillKernelNpuOpApi.cpp)（primary）：1–44；完整本地小文件。
- [AdvancedIndex.cpp op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/AdvancedIndex.cpp)（implementation）：25–150、163–345、377–394；仅所列完整相关helper/Schema，其他内容不提升完成。
- [op_plugin_functions.yaml op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：627–629、2756–2762、3360–3366；仅所列完整相关helper/Schema，其他内容不提升完成。
- [IndexPutKernelNpuOpApi.cpp op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/IndexPutKernelNpuOpApi.cpp)（implementation）：1–87；完整本地小文件。
- [MaskedFillKernelNpuOpApi.cpp op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedFillKernelNpuOpApi.cpp)（implementation）：1–47；完整本地小文件。
- [AdvancedIndex.cpp op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/AdvancedIndex.cpp)（implementation）：25–136、150–298、330–346；仅所列完整相关helper/Schema，其他内容不提升完成。
- [op_plugin_functions.yaml op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：612–614、2670–2676、3255–3261；仅所列完整相关helper/Schema，其他内容不提升完成。
- [op_api_common.h op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：744–812；同字节复用54已读且root独审的精确范围，不新增整文件资格。
- [op_api_common.h op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：677–736；同字节复用54已读且root独审的精确范围，不新增整文件资格。
- [OpPreparation.cpp pytorch ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：106–116、122–124、392–411、521–526；同字节复用54已读且root独审的精确范围，不新增整文件资格。
- [CalcuOpUtil.cpp pytorch ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation）：250–260；同字节复用54已读且root独审的精确范围，不新增整文件资格。
- [OpCommand.cpp pytorch ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp)（implementation）：234–282；同字节复用54已读且root独审的精确范围，不新增整文件资格。
- [OpPreparation.cpp pytorch f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：110–121、128–128、385–408、517–523；同字节复用54已读且root独审的精确范围，不新增整文件资格。
- [CalcuOpUtil.cpp pytorch f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation）：214–226；同字节复用54已读且root独审的精确范围，不新增整文件资格。
- [OpCommand.cpp pytorch f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp)（implementation）：232–283；同字节复用54已读且root独审的精确范围，不新增整文件资格。
