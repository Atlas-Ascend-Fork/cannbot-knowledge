---
type: API
title: LinearQuant与旧A8W8类：参数装载、INT4打包与scale转换
description: 保存推理与图模式、dtype组合和模块状态，区分包装可接参和底层完整能力。
tags:
- task.lookup
- topic.compilation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearA8W8Quant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearQuant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearQuant.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearQuant.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/linear_a8w8_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/linear_a8w8_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/linear_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/linear_quant.py
  role: implementation
created_at: '2026-11-09T19:49:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# LinearQuant与旧A8W8类：参数装载、INT4打包与scale转换

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页、主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及各自实际收录范围。TorchNPU实现分别为发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b与独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把两个仓库main当已配套。

默认A2/A3只指页面所列训练系列；推理产品及其他入口的扩展另说明，旧Atlas不自动映射新型号。此批contrib页面没有950DT确认，不由底层算子或框架总览扩展。这里只做静态阅读，没有导入上游、加载模型、运行设备、反向或性能实验；stable不表示运行verified。


## 类及初始化

`LinearQuant(in_features,out_features,*,bias=True,offset=False,pertoken_scale=False,device=None,dtype=None,output_dtype=None)`包装npu_quant_matmul；旧LinearA8W8Quant计划废弃并建议前者。旧文档原型未列device/dtype，但实际两固定构造均接收且不消费；不能据参数存在判断已在目标device/dtype创建。

weight、scale和可选bias/offset/pertoken_scale均为requires_grad=False的torch.empty Parameter，没有按docstring所述均匀分布完成有意义的量化初始化。调用方须装载实际量化权重、scale等；不是给一个浮点训练模型就会自动量化。pertoken初建长度out_features，而合同要求长度m，m不同需显式设置正确实际Tensor。

## 输入、布局与参数

页面支持A2/A3训练/推理及旧Atlas推理卡，限定推理与图模式；旧Atlas只INT8输入和INT8/FP16输出，不支持pertoken。A2/A3的LinearQuant支持INT8或以INT32打包的INT4，x/weight同dtype，ND输入2..6维，INT32权重限定二维、连续；每INT32存8个INT4。逻辑K与N需8对齐，实际x=(m,k/8)、weight=(n,k/8)；发布中间例误写(k,n/8)，主线中英文已修，不据错式实现打包。

两固定forward将weight最后两维转置后调用底层。旧A8W8源码虽也接受两INT32，不据此扩展其发布A8W8产品合同；它还不接受INT32输出，LinearQuant页面则列该输出。

scale为ND一维1或n，A2/A3可FP32/INT64/BF16，INT64须由npu_trans_quant_param产生；offset为FP32同样1或n。bias一维n，输出三维时还可(batch,1,n)，batch为广播后值；输出其他2/4/5/6维时仅一维。pertoken为FP32长度m，旧A8W8页只允许FP16/BF16输出时非空；不能把可选dtype独立排列成全部组合可用。

## 组合矩阵的限定

| 输入/weight | scale | offset | bias | pertoken | output |
| --- | --- | --- | --- | --- | --- |
| INT8 | INT64/FP32 | None | INT32/None | None | FP16 |
| INT8 | INT64/FP32 | FP32/None | INT32/None | None | INT8 |
| INT8 | FP32/BF16 | None | INT32/BF16/FP32/None | FP32/None | BF16 |
| INT8 | FP32 | None | INT32/FP16/FP32/None | FP32/None | FP16 |
| packed INT32，仅LinearQuant | INT64/FP32 | None | INT32/None | None | FP16 |
| INT8，仅LinearQuant | FP32/BF16 | None | INT32/None | None | INT32 |

旧Atlas推理只前两行；None表示相应参数关闭。None输出等同INT8，x/weight/scale不得空，最后维上限65535；不能从矩阵推出任意布局、批次或训练梯度支持。

## 自动转换和图示例

当scale为FP32、无pertoken、output非BF16/INT32时，两固定包装在forward调用trans_quant_param；不是始终一次预处理或自动缓存转换结果。图例还使用[TorchAir选定模块权重转换](../torchair/use_internal_format_weight.md)，会改变weight/scale.data，需按基线先装载再转换/编译，不把单次调用成功当收益。

INT4示例直接randint生成承载整数，只展示形状，不证明已经把真实INT4量化值正确打包或校准。底层[npu_quant_matmul](npu_quant_matmul.md)、[INT4打包](npu_convert_weight_to_int4pack.md)和[量化参数转换](npu_trans_quant_param.md)各自合同独立，不推950或运行验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearA8W8Quant.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearQuant.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearQuant.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-contrib/torch_npu-contrib-module-LinearQuant.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/linear_a8w8_quant.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/linear_a8w8_quant.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/linear_quant.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/linear_quant.py)（implementation）
