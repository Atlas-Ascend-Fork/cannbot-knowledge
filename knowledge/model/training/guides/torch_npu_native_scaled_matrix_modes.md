---
type: Guide
title: 原生scaled矩阵乘的NPU模式：ScalingType与文档边界
description: 区分scaled_mm和scaled_grouped_mm的FP8/MX模式、A2/A3产品表及委托scale形状，不按其他量化API外推。并含 主线950包装层输入合同：_scaled_mm/_scaled_grouped_mm及v2的SoC门、FP8 dtype/scale/bias/scale_result/out_dtype与NZ/V5符号可用性检查。
tags:
- task.optimization
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_mm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_mm_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_grouped_mm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_grouped_mm_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledMmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledMmV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledGroupMmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledGroupMmV2KernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-09T10:26:00Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 原生scaled矩阵乘的NPU模式：ScalingType与文档边界

## 固定来源与收录版本

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的原生functional支持页。scaled_mm与scaled_grouped_mm在同提交PyTorch2.11、2.12、2.13、2.14四页收录，条目语义相同，父级条件及产品表均为A2/A3训练系列。其余三个版本页本卡未找到这些条目；缺少收录不等于对实际安装包作绝对不可用判断。

这份中文原生入口清单未列950，不能由OpPlugin其他FP8/GMM API的950支持补齐该范围。本文仅为模式选择与支持度核对指南，不提供尚未核对的完整API调用配方，也未执行上游、导入包或设备实验。

## 已明确的模式

| 原生入口 | FP8模式 | MXFP8模式 |
| --- | --- | --- |
| torch.nn.functional.scaled_mm | ScalingType为tensorwise、rowwise或BlockWise1x128 | ScalingType为BlockWise1x32的排布 |
| torch.nn.functional.scaled_grouped_mm | 仅列rowwise | 列MXFP8排布，但未在本条目写出同一份ScalingType细表 |

ScalingType描述的是scale粒度/排布，不能只按FP8 dtype相同就交换两种入口，或将BlockWise1x128与BlockWise1x32共用一组scale。grouped条目未列tensorwise/1x128，不按普通scaled_mm的并集扩展。

## scale形状与外部依赖仍待单独确认

固定页面将MXFP8的scale_a/scale_b条件分别委托aclnnQuantMatmulV5与aclnnGroupedMatmulV5文档，链接指向三仓之外的ops-nn/ops-transformer。该条目本身没有完整列出scale张量轴、padding、转置、输出dtype、分组及反向合同；不能从上述模式名自行生成这些规格，或把其他npu_quant_matmul/grouped_matmul的参数直接移入。

本卡保留这两个依赖入口，不把外部仓实现或全部委托参数算作已摄取。具体接入还需核对目标包的实际签名、所用ScalingType、数据/scale物理形状、Kernel和产品，再做数值与性能验收。原生支持表也不独自证明torch.compile/特定图后端或训练反向均已实现。

## 选择与验证

先固定目标版本和入口，再区分普通/分组、FP8/MX、scale粒度和布局，最后核对真实参数合同。没有这几项时，保留为待确认的接线，而非套用已有量化模型例子。本文提供四版本中这两个条目的限定知识，不替代完整委托参数与设备验证。

## 英文产品表与MX措辞

对应四份英文页对scaled_mm/scaled_grouped_mm明确950DT不支持；前文“未列950”指中文表，不用其他FP8接口覆盖这个明确标记。

英文grouped条目把rowwise与“fp8 mode and mxfp8 mode”写在同一句，中文则分别列FP8的rowwise与MX排布、没有给同一份MX ScalingType细表。保留这处措辞/范围差异，不能只凭英文连词就补造MX scale张量轴和完整布局合同；外部aclnnGroupedMatmulV5委托规格仍未计入三仓已摄取范围。

## 私有根入口和v2门槛

同提交中英文private_apis对torch._scaled_mm/_scaled_grouped_mm明确PyTorch2.7.1及之后，对各自_v2明确2.10.0及之后；四者均列A2/A3支持、950暂不支持。它们不同于前述functional公开入口的四版本收录范围，不用一个命名空间为另一个补版本或参数。

普通_mm的FP8列tensorwise/rowwise/BlockWise1x128，MXFP8列BlockWise1x32；grouped的FP8列rowwise，MX仍委托aclnnGroupedMatmulV5。两种v2额外要求swizzle_a/swizzle_b为None。scale_a/scale_b仍委托三仓之外文档，未在本卡摄取完整规格，也不由模式名补shape、分组和反向合同。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（primary）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）

## 主线950包装层输入合同：_scaled_mm/_scaled_grouped_mm 及 v2

本节补齐OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的opapi包装实现与配套合同测试所揭示的**主机侧输入合同**；发布版本`dedc316708372c9a8bfde4527abd2a94b74840f5`无ScaledMm/ScaledMmV2/ScaledGroupMm/ScaledGroupMmV2四个包装文件（负向核实，名字账本main_registered=true/release_registered=false同口径）。上文文档面（private_apis四页列A2/A3、950暂不支持）与主线950门控实现并存，本节按原文记录两边，不用文档否定实现，也不用实现改写文档收录范围。四个测试文件均为`@SupportedDevices(['Ascend950'])`且逐条断言下表错误串；本卡未执行任何测试或设备实验。

| 入口 | 主机侧合同（TORCH_CHECK 原文语义按原文记录） |
| --- | --- |
| 四者公共SoC门 | `GetSocVersion() >= Ascend950`，原文"_scaled_mm is supported only on the Ascend950 platform and after."（ScaledMm/V2/Grouped/V2 四包装同构声明） |
| _scaled_mm 数据dtype | mat_a/mat_b必须Float8_e4m3fn或Float8_e5m2（"mat_a/mat_b must be float8 type…"）；**两侧同为e5m2拒绝**（"Multiplication of two Float8_e5m2 matrices is not supported"） |
| _scaled_mm scale dtype | scale_a/scale_b必须Float32或Float8_E8M0（"scale_a/scale_b must be float32 or float8_e8m0 type"） |
| _scaled_mm bias | bias存在时numel必须等于mat_b.sizes()[1]；out_dtype=Float时拒绝bias（"Bias is not supported when out_dtype is set to Float32"）；bias dtype限BFloat16/Float16且须与out_dtype匹配（BF16输出要求BF16 bias、Half输出要求Half bias） |
| _scaled_mm scale_result | 仅接受空（"scale_result is not supported currently, as output float8 type is not enabled."） |
| _scaled_mm out_dtype | 仅Float32/BFloat16/Float16；mat_a/mat_b必须2D且K对齐（"mat_a and mat_b shapes cannot be multiplied"） |
| rowwise传递 | e4m3×e4m3且两侧scale为FP32 2D（scale_a形如[M,1]、scale_b形如[1,N]）时squeeze后要求mat_a末维连续、mat_b首维连续（TORCH_CHECK） |
| x2 NZ格式 | NZ时要求aclnnQuantMatmulWeightNz可用，否则报"only aclnnQuantMatmulWeightNz support X2's format is nz, please upgrade CANN."；非NZ要求aclnnQuantMatmulV5（"only aclnnQuantMatmulV5 support A8W4, please upgrade CANN."） |
| _scaled_mm_v2 | group参数范围[0,65535]；mat_a/mat_b必须矩阵；scale_a/scale_b非空；contraction_dim恰两元素；mat_a末维连续、mat_b首维连续（各条TORCH_CHECK） |
| _scaled_grouped_mm(_v2) | mat_a/mat_b 2D或3D；scale 2D输入（KC模式）须1D、3D输入须2D且size[0]等于batch维G；scale须连续（末维）；2D mat_a/mat_b缺offs报错；offs维数/dtype受检；bias与scale_result不支持；单weight不支持k_split；MX路scale_a/scale_b同样FP32或Float8_e8m0fnu |

边界：本表只闭**主机侧检查与传递**；包装内向npu_quant_matmul族参数映射的深段（A8W4/A4W4载体检测、trans标志、group_size解析）不在本节展开，归实现文件分账。测试为合同断言源，未执行；950设备侧数值等价、scale物理排布与分组的完整规格仍按上文委托边界处理，不由本节补齐。

### scaled 950 补充证据

- [test_npu_scaled_mm.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_mm.py)（example）：全文308行；dtype/scale/bias/scale_result/out_dtype合同逐条断言（SupportedDevices Ascend950）。
- [test_npu_scaled_mm_v2.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_mm_v2.py)（example）：全文477行；v2合同与基本功能断言。
- [test_npu_scaled_grouped_mm.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_grouped_mm.py)（example）：全文531行；offs/bias/scale_result/k_split合同与FP8/MX功能断言。
- [test_npu_scaled_grouped_mm_v2.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_scaled_grouped_mm_v2.py)（example）：全文670行；同v2口径。
- [ScaledMmKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledMmKernelNpuOpApi.cpp)（implementation）：140–330；SoC门、dtype/scale/bias/scale_result/out_dtype检查、rowwise传递、NZ/V5可用性检查（其余行未逐行读）。
- [ScaledMmV2KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledMmV2KernelNpuOpApi.cpp)（implementation）：340–430；SoC门与v2合同TORCH_CHECK段。
- [ScaledGroupMmKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledGroupMmKernelNpuOpApi.cpp)（implementation）：110–160；mat/scale/offs合同TORCH_CHECK段。
- [ScaledGroupMmV2KernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledGroupMmV2KernelNpuOpApi.cpp)（implementation）：152–330；同v2口径检查段。
- 负向证据：发布版本 `op_plugin/ops/opapi/`无Scaled*四文件（ls核实）；canonical活树与主线与发布两版本测试路径均无既有引用收据（对照唯一来源为本节）。
