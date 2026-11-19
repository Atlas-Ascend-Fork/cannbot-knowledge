---
type: Guide
title: DVM矩阵融合：epilogue门槛、BF16中间值与view边界
description: 追踪矩阵模板注册到pointwise融合与生成，区分950外部mm、内部BF16提升、转置识别和实际view-load资格。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/template.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/mlir_fusion.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/op_emitter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/fx_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/util.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/graph_build.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/op_emitter.py
  role: implementation
created_at: '2026-11-10T12:32:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# DVM矩阵融合：epilogue门槛、BF16中间值与view边界

## 固定入口与范围

本卡补充TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的DVM矩阵模板调用链，侧重lowering、epilogue资格及生成中的中间精度/布局。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`不含同路径`dvm/template.py`、`dvm/config.py`、`dvm/util.py`；另对照发布mm_rule，不将主线模板当成发布能力，也不据路径缺失否定发布版其他融合。整卡平台未知，保持draft、空平台；未运行上游或设备实验。

DVM loader导入mlir_fusion，enable在enable_matmul_fusion为真时调用patch_dvm_matmul_template_fusion；它注册二维npu_linear及其反向分解、保留addmm、替换相关图处理并注册mm/bmm/addmm/baddbmm lowering。开关在所选配置导入时精确读取`INDUCTOR_DVM_ENABLE_MATMUL_FUSION=='1'`，默认关闭。后端生成与FX回退总路线见[DVM执行指南](torch_npu_dvm_mlir_codegen_and_fallback.md)，本卡不重复该路线或把开关当作匹配成功。

二维npu_linear分解为input×weight.T，有bias时用addmm；二维反向分解为grad×weight及grad.T×input。任一所需Tensor不是二维时返回NotImplemented；被disable_decomp_list明确禁用的重载或packet不注册。不能将这个分解说成任意batch维linear都已直接支持。

## 模板与矩阵规则的门槛

mm/bmm helper在C++ wrapper或缺少current_node/val时走所选fallback；常规情况下构造带输入绑定的DvmTemplateBuffer，生成前仍需mm_rule。K==1时有单独的expand后mul改写；addmm的K==1另走mul/add并保留alpha、beta缩放，不能概括为所有baddbmm也走同一特例。

主线mm_rule只接受选定四个准确target，检查输出Meta dtype为FP16/BF16，两个矩阵输入rank在2到4之间。对`is_ascend950`为假的分支，所检查内轴不能是SymInt且不能超过65280；这里的内轴会按已识别的末两轴转置计算。不能把这项表达式简化为所有输入都按同一个逻辑K上限检查，也不据本层没有完整输入类型校验认证任意混合dtype。

`matmul_fusion_rule`若非None，以(n,m,k)调用，只有返回对象严格为False才否决；其他返回值不替代已有规则。该回调不是允许绕过rank/dtype门槛的后门，也没有提供性能最优保证。

## Epilogue不是任意后续算子

纵向融合在前节点为DvmTemplateBuffer时调用can_fuse_dvm_epilogue。它要求Inductor的epilogue_fusion开启、后节点不是另一个DVM模板且不是reduction、两侧group的numel/rnumel相等；所有后续输出的元素数还必须能静态证明等于矩阵输出，并且确实读取该模板的buffer。

后续每个子节点都须是SchedulerNode上的ComputedBuffer/Pointwise。仅load/store/output/index_expr的view-only链被拒绝，不因名字含view就算完成有效epilogue融合。对于输出rank>2，额外检查读取buffer与外层维度：无法取得输入shape、输入rank更高，或外层shape不能静态证明相同且访问确有广播时拒绝。输出rank<=2绕过这一额外广播函数，不应将它改写成“所有广播都拒绝”或“任意广播都支持”。

因此形状元素数相同只是多个条件之一；中间view、归约、批维广播或另一个模板都可能改变可融合性。保留实际FX/调度子节点和shape证据，比只看一段linear+activation Python代码更能解释未命中。

## 没有Epilogue时可能继续调用外部矩阵算子

代码生成明确拒绝DVM Matmul模板的prologue_nodes。若`is_ascend950`为真、没有epilogue且op为mm或bmm，直接codegen_unfused，用原packet.out生成ExternKernel调用并释放调度缓冲；这不是生产DVM融合builder的路径。该SoC判断在所选代码为枚举>=260，不是本卡产品支持表。

其他所选DVM模板路径把模板与epilogue重建为FX，再生成DVM代码；只将scheduler允许移除的buffer加入removed_buffers。开启融合不等于所有中间存储都已移除，也不证明减少的搬运超过编译或布局开销。

## BF16中间提升和最终输出分开观察

主线在非950分支为一组选定vector操作安装包装，包括add/sub/mul/div、若干超越函数、比较、select和归约等；遇到NDObject的BF16参数时先cast为FP32。只有内部bf16_vector_keep_promoted为真且曾提升参数，包装才再cast回BF16；该字段默认False，不按名称猜测相反行为。此处没有把matmul本体加入这份vector包装清单，不能据此描述矩阵核心的全部累加精度。

DvmCodegenInterpreter在私有深拷贝图中，按非950或该字段为真的条件给BF16 cat输入插入cast，以处理其生产者可能为FP32的情况；最终store表达式另携带输出节点Meta dtype。因此看到FP32中间值不等于公开输出dtype被改成FP32，也不能只看最终BF16输出认定没有中间提升/回落。数值、峰值内存与cast开销仍需结合完整训练或推理负载验证。

## View-load资格不能直接推广到矩阵mix

通用can_use_view_load先要求view_fusion_level非0且元素大小为2或4字节；level2直接通过该局部检查，其他非0等级要求尾stride=1且尾维不为1。codegen_maybe_view_load满足时发view_load并标记可跳过连续化，否则发load并返回False。它是局部代码生成资格，不是任意stride/offset的设备认证。

矩阵图的mix模式又把view_fusion_level设0；spec/含concat及split模式最多level1。对placeholder的严格末两轴转置形态，先标trans并按mT形状发load，调用参数随后可追加`.mT`；其余非连续输入仍受上述资格约束。不能仅把level设2就承诺矩阵mix任意stride零复制，本卡也没有闭合所有运行库对连续化标志的消费者。

发布mm_rule本身还无主线的950豁免/回调和baddbmm target分支，所选内轴要求静态且不超过同一上限。验收应固定revision，分别记录模板/外部out路线、epilogue匹配、batch广播、转置和实际拷贝、BF16中间cast、数值与关闭调试后的端到端性能；本卡没有新增verified或收益数字。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/template.py)（primary）：定向范围60–82, 96–275, 278–362。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/mlir_fusion.py)（implementation）：定向范围284–302, 350–426, 531–562。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/op_emitter.py)（implementation）：定向范围75–133, 533–551, 564–568。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/fx_pass.py)（implementation）：定向范围26–57。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/util.py)（implementation）：定向范围39–73。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/graph_build.py)（implementation）：定向范围31–81, 106–144, 158–226。
- [固定实现来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/__init__.py)（implementation）：定向范围28–32, 141–201。
- [固定实现来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/config.py)（implementation）：定向范围19–38。
- [固定实现来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）：定向范围141–158。
- [固定实现来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/dvm/op_emitter.py)（implementation）：定向范围100–130。
