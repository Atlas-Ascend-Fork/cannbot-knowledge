---
type: Guide
title: DVM融合区成本预测：构组、边界字节与实际融合差距
description: 说明overlap可选DVM区域如何分组并覆盖节点估时，区分逻辑边界传输模型、默认带宽与真实融合/内存性能。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/dvm_fusion_regions.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/overlap_scheduling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/op_emitter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/mlir_fusion.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
created_at: '2026-11-10T12:47:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# DVM融合区成本预测：构组、边界字节与实际融合差距

## 实际消费者和预测身份

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的DVM fusion-region成本预测及overlap收集消费者。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`无同路径`fx_passes/dvm_fusion_regions.py`，只记录准确tree差异，不否定其他版本的成本模型。整卡平台未知，保持draft、空平台，未执行上游、融合或设备实验。

后端加载后安装的overlap适配器在enable_fusion_regions=True时，先以该参数False取得上游普通估时，再调用build_dvm_fusion_regions、estimate_dvm_fused_node_costs，并用返回字典update原节点成本。默认安装将该选项置False。未纳入或估计失败而未返回的节点保留原成本；本段只修改估时字典，不重写FX图、不直接生成融合Kernel。[overlap事件估时与入口门槛](../../../../training/guides/torch_npu_inductor_overlap_runtime_estimation.md)仍须独立满足。

## 连续轻量段再拆依赖连通分量

候选要求call_function、不是_c10d_functional通信、不在显式重算子集合，且补丁后的is_compute_node不将其识别为计算节点；它还必须在DVM注册表中并通过解包出的支持规则。该支持对象组合输入/输出dtype检查及可选自定义rule，不是只按算子名字分组。导入注册表异常时返回空注册表，不能把没有预测区域理解成图上没有算子开销。

显式排除集合包括mm/bmm/addmm以及所列sum、amax、amin重载；其他计算密集节点还受上游/已扩展计算谓词影响。不要将这份局部集合当作全部重算子或全部DVM支持表。

按FX顺序收集连续候选段，遇到任一非候选即结束当前段，不能跨该节点合并前后候选。段内仅沿真实输入依赖、且通过局部边资格的节点做UnionFind连通分量。每个分量至少需要两个非view节点；单个运算加若干view不会得到区域。区域内顺序仍按原FX节点排序。

## 边资格是启发式，不是完整lowering合同

边的一端为已识别aten/prims view时直接通过这项检查，但该view仍须先成为候选。其他边要求双方Meta中各恰有一个Tensor，且能由静态维度或SymInt hint具体化shape；随后接受shape相等或局部尾轴广播判定。

该广播helper按目标shape的尾轴逐一比较，未另加源rank<=目标rank检查；它不是完整PyTorch广播合法性验证。它也未在此检查真实stride、offset、view-load等级或布局转换成本。

实际MLIR DVM规则另检查enable_cat、enable_fusion_permute以及clone的连续性/view-load资格；本预测候选函数没有完整复刻这些开关与布局门槛。不能将预测区域直接当作这些节点在目标DVM模式下一定融合的证明，更不能据此承诺去掉全部中间拷贝。矩阵模板/epilogue的实际规则见[DVM矩阵与view边界](torch_npu_dvm_matmul_epilogue_precision_and_views.md)。

## 成本按每个节点的区域外逻辑字节计

每个区域对象只处理一次，但成本逐节点产生：输入来自区域外且有Meta val时计为external_inputs；该节点有任一区域外用户且自身有val时计一次external_outputs。无这两类边界的内部节点赋0.0。有边界时，遍历其中的Tensor，按shape元素乘dtype.itemsize求逻辑字节和。

这不是按Storage地址去重的区域总工作集。同一个外部Tensor若被多个区域节点读取，可能在各节点分别计入；别名/view的重叠存储也未由这里消重。输出是否计入只看有无区域外用户，不按用户数重复输出；缺少val的边界被跳过。因此不能把这份字节数当作实际峰值显存、物理HBM流量或allocator申请量。

有无法取得hint的维度或异常时，该边界节点估计返回None，于是跳过该节点的成本覆盖；没有边界则可以赋零。一个区域可能同时有覆盖节点和保留原估时的节点，不是整区域必定原子式采用同一模型。零成本在这里表示内部边界传输模型的处理，不表示节点完全不执行或没有launch/计算成本。

## 带宽与时间单位遵守代码算式

默认带宽取2000.0，正值环境项TORCH_NPU_DVM_FUSION_REGION_BW_GBPS可覆盖；非法数字文本告警后回默认，非正值也回默认。最终换算使用：

```text
bytes_per_ms = bandwidth * 1024^3 / 1000
cost_ms = boundary_logical_bytes / bytes_per_ms
```

虽然字段名含GBPS，实际表达式按二进制1024^3换算。默认2000不是本机测量，也没有从每个设备的属性动态获取真实带宽；正无穷虽通过前一正值检查，最终非有限检查仍使边界估计返回None。模型没有在这里加入算术强度、真实带宽争用、launch延迟、转换或workspace成本。

TORCH_NPU_DVM_FUSION_REGION_TRACE精确为1时输出所估区域/节点诊断和结构化artifact；日志里的区域数或estimated_nodes数不是实际融合Kernel数。评估时将预测区域、哪些节点成本被覆盖、带宽取值与实际编译生成物、Kernel数、拷贝、时间线及端到端性能对照，再判断该启发式是否适合负载。本卡没有新增verified、实测带宽或收益数字。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/dvm_fusion_regions.py)（primary）：定向范围25–363。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/overlap_scheduling.py)（implementation）：定向范围397–434, 515–521。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/op_emitter.py)（implementation）：定向范围136–185。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/mlir_fusion.py)（implementation）：定向范围114–141。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py)（implementation）：定向范围455–467。
