---
type: API
title: 权重量化矩阵乘：pertensor、perchannel 与 pergroup（torch_npu.npu_weight_quant_batchmatmul）
description: torch_npu.npu_weight_quant_batchmatmul：权重量化矩阵乘：pertensor、perchannel 与 pergroup。此接口用于执行矩阵乘计算中`weight`输入和输出的量化操作，支持pertensor、perchannel、pergroup多场景量化。 说明整数/FP4权重打包、pergroup/MX粒度和ND/NZ差异，保留UINT8扩展参数及Meta边界。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_weight_quant_batchmatmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_weight_quant_batchmatmul.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WeightQuantBatchMatmulV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_weight_quant_batchmatmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_weight_quant_batchmatmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_weight_quant_batchmatmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/WeightQuantBatchMatmulV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_weight_quant_batchmatmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_weight_quant_batchmatmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_weight_quant_batchmatmul.py
  role: implementation
created_at: '2026-11-10T03:38:51Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
- 310p
aliases:
- torch_npu.npu_weight_quant_batchmatmul
---


# npu_weight_quant_batchmatmul：伪量化、产品布局与有效选项

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema及同提交包装/Meta，未执行上游代码、图编译或设备实验。本文描述310P/A2/A3/950的明确分支，具体版本不回推发布基线。

## 接口与运算顺序

```text
npu_weight_quant_batchmatmul(x, weight, antiquant_scale,
    antiquant_offset=None, quant_scale=None, quant_offset=None,
    bias=None, antiquant_group_size=0, inner_precise=0,
    weight_dtype=None) -> Tensor
```

先按(weight+antiquant_offset)*antiquant_scale反量化权重，做x@weight并加bias。可选输出量化在此后乘quant_scale并加quant_offset；不能把前后两种scale或offset当成同一个约定。

本文基础契约为二维x=(M,K)、weight逻辑(K,N)，x支持FP16/BF16及转置视图。weight支持的物理容器和ND/NZ由产品及模式决定，输出无quant_scale时随x dtype，存在quant_scale时为INT8。所有输入非空，bias连续。

## 产品与模式矩阵

|条件|A2/A3|950|
|--|--|--|
|权重与量化粒度|INT8或INT32承载INT4，pertensor/perchannel/pergroup|另有FP4（含FP32承载）、E4M3FN/HiF8；FP8/HiF8仅perchannel，FP4可含MX|
|浮点antiquant尺度|一般与x同FP16/BF16；单算子必须匹配|同x，MX用UINT8承载E8M0|
|特殊INT64 antiquant尺度|仅FP16非转置x、INT8 ND转置weight、perchannel，M≤96、K/N为64对齐|不列该扩展|
|输出量化|仅ND权重；quant_offset不能单独存在|产品页不支持quant_scale/quant_offset|
|权重NZ执行模式|产品页仅图模式|按实际权重分支，INT8 NZ仍仅图模式|

antiquant_scale形状：pertensor(1,)或(1,1)，perchannel(N,)或(1,N)，pergroup/MX为(ceil(K/group_size),N)。pergroup粒度为32倍数且位于[32,K-1]，MX固定32。offset若存在必须同scale shape；950浮点权重/FP4分支禁止antiquant_offset。

## 打包、转置与预处理

INT32或FP32容器每元素承载8个4位值：非转置沿N打包、转置沿K打包；恢复逻辑K/N须同时看stride和打包方向，不通过float()或int()数值cast生成这些容器。INT4/FP4尾轴有8对齐等产品限制。

950同提交C++另有UINT8两值/字节的INT4/FP4扩展路径及NZ_C0_8识别，可表达[权重预处理](npu_weight_quant_preprocess.md)产物；但本产品页的weight_dtype仅列HiF8，与C++允许4位逻辑类型的分支不完全一致。该实现分支应按预处理、真实Tensor dtype、逻辑dtype与下游运行库共同验证，不当作A2/A3通用参数保证。

950 INT32 NZ pergroup要求x和weight均非转置，group_size为32倍数；A2/A3对应路径则要求x转置、weight非转置、group_size为64/128、K按组对齐、N为64对齐，不能跨产品复制布局。950 INT8 NZ pergroup另保留旧式转置x、64/128组和N对齐约束，不与INT4路径混用。

## bias、运行入口和未生效选项

FP16 x要求FP16 bias；A2/A3的BF16 x要求FP32 bias。950 BF16路径可有BF16/FP32 bias，但FP8/HiF8/FP4权重要求BF16 bias，INT8 NZ要求FP32，不能按总dtype名单任意搭配。

950 NZ包装必须存在aclnnWeightQuantBatchMatmulNz并优先走该入口；否则普通FP32 quant_scale会先转换量化参数后调用V2；仅后续分支inner_precise=1会调用V3并传精度模式。因此接受inner_precise=1不表示前两个分支已使用高性能模式。产品页也只建议特定小M、INT32 NZ pergroup场景尝试1，不能全面启用后宣称加速。

## Meta与验证

C++有更宽rank分配代码，但当前产品参数主述二维，Meta也只按二维推导；不据包装的batch代码扩展公开高维支持。Meta不会替代全部模式、format和scale检查。

对照相同反量化顺序、逻辑打包、bias与输出量化的结果；检查真实shape/stride/format，分别测加载期转换与稳态。图中scale dtype自动转换的文档说明也不能免除单算子匹配要求。

## 310P与发布产品范围

主线与发布中文都列Atlas推理系列（310P），但其能力只覆盖FP16左输入、INT8权重和与输入同FP16的反量化scale/offset，bias为FP16；NZ仅图模式，输出quant_scale/quant_offset和weight_dtype扩展均未公开支持。不要把A2/A3的INT4、INT64反量化尺度或950的MX/HiF8搬到310P。发布某INT64尺度样例误把该产品也列入，与参数段仅FP16相冲突，按明确参数限制保留该差异。

发布中文页产品仅310P/A2/A3，没有950；原型没有weight_dtype，但同发布Schema、C++和GE已含这个可选形参。实现签名存在不等于主线公开的950类型和模式已获该发布产品承诺。新UINT8四位载体和NZ_C0_8识别只在主线C++/Meta中出现，发布不具有相同的恢复逻辑。

## 双语布局和有效模式差异

主线中文针对A2/A3/310P限制NZ只图，并另给950按权重类型的分支及FP4 NZ单算子示例；主线英文还保留一条未按产品限定的“NZ不支持单算子”旧式句子。不能把英文这一句或中文一个示例直接当作950全部NZ权重均可Eager。两包装950 NZ都会检查执行入口与GetWorkspaceSize双符号，缺少即报错；不据错误提示推出最低精确CANN版本。

950浮点权重不能带antiquant_offset或输出量化；BF16 bias仍随权重类型细分。bias文字提及E5M2不等于公开weight名单新增E5M2。MX明确要求group_size=32、UINT8承载E8M0；文档FP4 NZ示例却传FP16 scale，不能把该示例当MX编码范例，须先确定实际pergroup/MX分支。

inner_precise只接受0/1，高性能1仅建议M≤16的INT32 NZ pergroup条件；两Cpp的950 NZ优先分支和FP32 quant_scale转换分支都不向内核传该选项，因此设置1不保证使用V3。FP32 quant_scale会先过TransQuantParamV2；若已用npu_trans_quant_param产生编码INT64，应按对应路径传递，不能把编码当数值scale再次量化。

## 图转换与Meta不提供完整输入校验

两GE把INT64 quant_scale转UINT64，将UINT8 antiquant_scale按E8M0作Bitcast，并用节点名包含Transpose的判断处理尺度换轴；weight_dtype也只是逻辑位解释。转换器没有全面校验产品、分组与shape，不能据可构图扩大允许参数或把数值cast当位打包。

真实转置判定的C++ helper只识别2/3维，还检查stride、底层base shape及完整storage；不能只按一个stride推断。主线C++在weight rank大于x时补足输出vector容量，发布没有该resize；Meta两版仍固定二维输出，不支持据内部batch代码承诺高维公开接口。主线UINT8两值/字节分支的Meta与C++也须按真实format、hint及布局共同核验。

## 测试不等于全部产品验收

两版310P测试用四维输入且以torch.randn构造INT8，前者超出公开二维参数，后者本身不是有效的整数随机数构造。HiF8测试用原始FP32权重作为参考，而调用用经HiF8转换的权重，没有构成相同量化还原参考，混合参考dtype也须检查。

NZ INT4测试仅950、M=1、常数权重3的perchannel场景，虽然定义group_size=64却没有传给API。主线另增两例UINT8 INT4 ND正常/转置布局，用非零有符号权重和CPU FP32参考检查shape/dtype；发布无这两例，且主线产品页weight_dtype只列HiF8，测试分支不扩成通用公开支持。

未运行这些测试；没有设备BF16、MX、非零FP4、输出量化、inner_precise收益或310P/A2/A3/950全面正确性与性能证明。

## 包装的完整rank、batch、参数与分配顺序

两版完整包装先调用既有转置helper，再检查x与weight各rank≥2；若两者都大于2则rank必须相同。等rank的所有batch维要求逐项相等，没有在这里按size1实现广播；一方为2维时batch维取较长的那份。公开产品仍按前文二维范围，不能因Host能申请这些尺寸扩大支持。

主线pack_ratio对Int/Float容器固定8，对Byte且逻辑weight_dtype为INT4/FP4_E2M1/FP4_E1M2才为2，其余1。转置时用ratio恢复weight的K，非转置恢复N，并检查x.K等于恢复K；output_size先resize到两rank最大值，再填M/N/batch。发布只对Int/Float按8恢复，没有Byte逻辑四位的同样处理，且输出vector未先resize。主线的形状恢复本身没有另按SoC禁用Byte分支，不能把恢复了shape当成其他产品可执行保证。

四个Optional offset/scale/bias缺失均转undefined Tensor；antiquant_group_size先由int64窄化为C++ int，再检查为0或[32,K-1]内32倍数。随后检查quant_offset不得脱离quant_scale、inner_precise只能0/1。输出dtype只按quant_scale.has_value选择Char或x dtype，而非先按该Tensor已defined或内容合法做验证；没有在这里补全全部公开dtype/format/bias组合。

make_wrapper统一携带weight及逻辑dtype提示；真实内存位解释仍按包装helper及运行库。NZ优先、FP32 quant_scale转换、inner_precise=1的V3、其余V2这一完整顺序不变：前两路即使inner_precise=1仍不传该参数。NZ/V2共有9实参为x、weight_wrapper、antiquant_scale、antiquant_offset、quant_scale、quant_offset、bias、窄化group_size和result，V3在result之前再加inner_precise；FP32尺度转换只用转换后INT64 quant_scale替代该槽，不把quant_offset当成反量化offset。

## 完整测试中的权重打包与参考误差

两版共有的supported_op_exec仅作可选weight+antiquant_offset，再乘antiquant_scale后matmul；custom_op_exec只转发这四项及weight_dtype，不提供输出量化、group_size或inner_precise参数。两版3个共同测试的完整AST相同，主线新增5个方法（3个helper及2个UINT8测试），其余代码一致。

pack_int4_along_n以原int8的低4位为载荷，把偶数N列放低nibble、奇数N列放高nibble；沿K的helper先转置/连续化，偶数K行放低nibble、奇数K行放高nibble，构造物理[N,K/2]后在调用处transpose为[K/2,N]。gen_fp16_exact_values从给定FP16可表示值池采样，并不证明矩阵乘累加与最终输出永远没有舍入误差。

两个主线UINT8测试均标950，M/K/N=16/256/128，x取±0.5/±1、scale取0.5/1/1.5/2，权重为[-8,7] int8，CPU FP32参考；检查shape、FP16 dtype和0.001误差。两版共同的HiFloat8、310P与常数NZ INT4测试的限制沿前文保留；所有数值比较均只是源码中的断言，没有本次通过结果。上述测试也没有覆盖所有broadcast batch、非法group_size、量化输出或精度模式性能。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 权重量化矩阵乘：pertensor、perchannel 与 pergroup：torch_npu.npu_weight_quant_batchmatmul

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

此接口用于执行矩阵乘计算中`weight`输入和输出的量化操作，支持pertensor、perchannel、pergroup多场景量化。

### 文档签名

```text
torch_npu.npu_weight_quant_batchmatmul(x, weight, antiquant_scale, antiquant_offset=None, quant_scale=None, quant_offset=None, bias=None, antiquant_group_size=0, inner_precise=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_weight_quant_batchmatmul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_weight_quant_batchmatmul.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WeightQuantBatchMatmulV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_weight_quant_batchmatmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_weight_quant_batchmatmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_weight_quant_batchmatmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/WeightQuantBatchMatmulV2KernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_weight_quant_batchmatmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_weight_quant_batchmatmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_weight_quant_batchmatmul.py)（implementation）

## 完整实现与测试证据

- [d84e9b1 WeightQuantBatchMatmulV2KernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WeightQuantBatchMatmulV2KernelNpuOpApi.cpp)（implementation）：完整本地文件1–192。
- [d84e9b1 test_npu_weight_quant_batchmatmul.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_weight_quant_batchmatmul.py)（example）：完整本地文件1–149。
- [dedc316 WeightQuantBatchMatmulV2KernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/WeightQuantBatchMatmulV2KernelNpuOpApi.cpp)（implementation）：完整本地文件1–120。
- [dedc316 test_npu_weight_quant_batchmatmul.py](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_weight_quant_batchmatmul.py)（example）：完整本地文件1–84。
