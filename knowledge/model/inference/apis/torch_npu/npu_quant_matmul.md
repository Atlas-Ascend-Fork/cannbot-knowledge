---
type: API
title: 量化矩阵乘的二维至六维输入（torch_npu.npu_quant_matmul）
description: torch_npu.npu_quant_matmul：量化矩阵乘的二维至六维输入。执行量化的矩阵乘计算，最小支持输入维度为2维，最大支持输入维度为6维。 区分发布和主线A2/A3、310P及950的INT8/INT4、FP8/FP4、分组尺度、ScaleNZ、bias位置和图模式边界。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_matmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/hyvideo/modules/mxfp8_a8w8.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quantmatmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quantmatmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-10T03:38:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- 310p
- '950'
aliases:
- torch_npu.npu_quant_matmul
---


# npu_quant_matmul：版本化量化模式、尺度编码与布局

## 版本与范围

前面的基本路径依据ascend_26_0_pt28发布来源的A2/A3 INT8浮点输出；后续另补发布其他模式、310P和固定主线950。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_quant_matmul(x1, x2, scale, *, offset=None, pertoken_scale=None, bias=None, output_dtype=None, group_sizes=None) -> Tensor
```

前面的基本范例聚焦INT8×INT8到FP16/BF16的推理路径；INT4、分组二维scale、INT32和主线950另见后续专节。返回量化矩阵乘的 Tensor。INT32 bias 在缩放前相加，BF16/FP32 bias 在缩放后相加，不能把两者按相同顺序构造参考。

## 参数与组合限制

- x1/x2 同为 INT8，ND、2–6 维、非空，末维不超过 65535；K 轴匹配，batch 按矩阵乘广播。scale 一维长度 1 或 N。
- FP16 输出且 pertoken_scale=None：scale 为 INT64 编码或 FP32，bias 为 INT32/None，offset=None；图模式此组合不能直接传 FP32 scale，应使用 npu_trans_quant_param 编码。
- FP16 输出且有 pertoken_scale：scale=FP32、pertoken_scale=FP32(M,)、bias 为 INT32/BF16/FP32/None，offset=None。
- BF16 输出：scale 为 FP32/BF16，pertoken_scale 为 FP32(M,) 或 None，bias 为 INT32/BF16/FP32/None，offset=None。
- bias 通常为 (N,)；仅三维输出可用广播后的 (batch,1,N)。output_dtype 默认 None 对应 INT8，不是输入 dtype，要求浮点结果时必须显式指定。
- 前面的INT8基本范例不混用INT4专有group_sizes及二维scale/offset，其他模式和后端差异见后文。

## 验证与模型关联

分别验证无 pertoken 的编码 scale、带 pertoken 和 BF16 bias 三条路径；以显式 INT32 累加和正确的缩放/偏置顺序检查数值与输出 dtype。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/hyvideo/modules/mxfp8_a8w8.py#L62)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 发布与主线的产品和接口差异

本节分别依据OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布dedc316708372c9a8bfde4527abd2a94b74840f5，以及TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。发布配套为ascend_26_0_pt28，主线配套未知。发布公开A2/A3与310P，主线新增Ascend950系列（包含旧称Atlas A5）的PR/DT；不能由发布实现里出现新类型推导发布文档已保证950支持。

主线原型在既有参数上增加x1_dtype、x2_dtype、pertoken_scale_dtype、scale_dtype与y_scale。两固定Schema实际都已有这些参数，output_dtype为int?，因此发布文档的简化原型不等于实现只接收旧参数。默认None仍输出INT8；FP16/BF16/FP32/INT32都需显式指定并符合对应组合。

一般输入/输出为2～6维，输出batch按输入广播，M来自逻辑x1、N来自逻辑x2。发布要求输入末维不超过65535且不能空；主线950 ND允许M或N为0返回空，WeightNZ仅列M=0特例，不能据此允许K或scale为空。bias通常[N]，仅3维输出列[batch,1,N]；主线950的2维输出还列[1,N]，但Meta的通用分支仍只验1维/3维，需按实际后端核对。

310P只用INT8×INT8，scale为FP32或已编码INT64，bias为INT32/None、pertoken_scale=None；输出FP16时offset=None，输出INT8时offset可FP32。weight先转置为连续[N,K]再转FRACTAL_NZ，与A2/A3推荐非转置转格式的路径分开。主线公式小节把310P叫K-C且写带x1Scale，参数和组合表却明确不支持pertoken_scale；按窄表使用，不据模式名称开放token尺度。类似地，INT4附加说明虽把310P列入适用文字，310P产品类型表仍只INT8，不扩展成INT4支持。

## 尺度、偏移和偏置的运算位置

静态量化的INT32 bias在整数矩阵乘后、乘weight scale前加；有激活尺度时还需再乘pertoken_scale。浮点bias在所有相关缩放后加，不能将INT32 bias直接改为浮点而沿用原参考。静态INT8输出的offset是输出偏移；A8W4整数分组的offset也是先加到分组结果、再乘激活尺度的输出偏移；A4W4非对称分组的offset则对应weight零点，出现在X@(W-offset)内部。这些offset不互换。

A2/A3基本INT8路径另有FP16 bias的主线组合：BF16输出配FP32/BF16 scale，FP16输出带FP32 token尺度时配FP32 scale；bias需与目标输出和有无token尺度一致。发布旧表没有列这些FP16 bias组合。INT32输出只配INT8输入、FP32/BF16 scale与INT32/None bias，不能按一般浮点反量化公式自行解释结果。

INT64/UINT64 scale是编码，不是把普通FP32尺度数值cast为整数。公开入口要求使用npu_trans_quant_param；静态INT8/FP16且无token尺度的图模式不能直接用FP32 scale，950 FP8/HIF8无token尺度也有同样图限制。C++ Eager在scale=FP32、无token尺度、输出非INT32且符合BF16/use_aclnn_v5条件时会自行编码；图转换器没有替调用者做同等编码，不能用Eager成功证明图可直接接收FP32。

A4W4的发布文档还列二维scale[ceil(K/groupK),N]、同形FP16 offset、FP32 token尺度[M,1]和FP16/BF16输出。主线仍描述非对称K-G公式，却在参数段主要给一维token尺度，表中省去这一行。两个版本Meta都要求offset一维FP32；发布Meta还对所有A4W4限定FP16输出，主线只对没有token尺度的A4W4限定FP16。因此保留文档与编译前检查的差异，不把这个旧分组配方推广到所有后端。

A8W4整数路径在两版C++和测试中为INT8 X、INT32承载INT4 W、编码二维scale[K/256,N]、FP32 pertoken[M,1]、可选FP32输出偏移和FP16/BF16输出。测试用group_sizes=[0,0,256]；输出[M,N]，不沿用A4W4把两侧都解包。它与950的FP8×FP4伪量化是不同模式。

## 950各量化模式的合法组合

下表的B表示各输入自己的batch前缀，K/N/M均为解包后的逻辑矩阵维度，不能拿打包后的Tensor轴长度替代。G-B、B-B、MX对K切片后各片乘各自尺度再求和，支持尾片，不能先把所有分组尺度合成一个矩阵乘后标量。

| 模式 | 主要输入/尺度与输出边界 | 非转置逻辑尺度形状与分组 |
| --- | --- | --- |
| T-T/T-C静态 | INT8配编码INT64，INT4双INT32配INT64/UINT64仅FP16输出；FP8/HIF8配编码INT64，可FP16/BF16/FP32。INT8输出只有INT8窄组合支持输出offset | scale[1]/[N]，token None或[1]；INT4 weight仅2维 |
| T-T/T-C动态 | FP8 E4M3/E5M2可组合或HIF8双路，FP32 scale与FP32 token[1]，FP32/None bias，输出FP16/BF16/FP32；INT8/INT4不支持动态T-T/T-C | scale[1]/[N]，token[1] |
| K-C/K-T | INT8/INT4配FP32/BF16 weight scale及FP32 token，bias依输出用INT32或对应浮点；FP8/HIF8配FP32双尺度，FP32/None bias | scale[N]/[1]，token[M]；WeightNZ时X不转置 |
| G-B | FP8/HIF8配FP32双尺度、无bias，输出FP16/BF16/FP32；INT8 G-B表中配FP32 bias和BF16输出，不据公式段扩为任意FP16组合 | weight scale[B,ceil(K/128),ceil(N/128)]；token[B,M,ceil(K/128)]；[1,128,128] |
| B-B | FP8/HIF8配FP32双尺度、无bias，输出FP16/BF16/FP32；不接受INT8，不保证batch一致性开关的结果一致 | weight尺度同G-B；token[B,ceil(M/128),ceil(K/128)]；[128,128,128] |
| MX全量化 | FP8 E4M3/E5M2或双方E2M1 FP4、双E8M0尺度、FP32/None bias，输出FP16/BF16/FP32 | weight[B,ceil(K/64),N,2]；token[B,M,ceil(K/64),2]；[1,1,32] |
| MX伪量化 | E4M3 X、FP4 W或FP32打包W，双E8M0尺度，bias为[1,N] FP16/BF16且同输出类型 | X[M,K]，转置W逻辑[N,K]，其字节/FP32承载[N,K/2]或[N,K/8]；weight尺度[N,K/64,2]、token[M,K/64,2]；[1,1,32] |
| T-CG伪量化 | E4M3 X、FP4 W或FP32打包W，FP16/BF16 weight尺度决定输出类型；token、offset、bias均None，y_scale[1,N]为编码INT64 | 字节转置承载[N,K/2]与尺度[N,K/32]，或非转置FP32承载[K,N/8]与尺度[K/32,N]；[1,1,32] |

group_sizes的0维表示自动推导，不表示任意分组大小。两版C++及GE限制每项[0,65535]、长度3，常规打包为(groupM<<32)+(groupN<<16)+groupK；GE的A8W4特例只传groupK。T-T/T-C若要求跨M的batch一致性，非空token尺度不能随X变化；B-B无此保证。

HIF8静态量化的ND weight可静态/动态图，WeightNZ仅静态图。MX全量化的双方FP4要求内轴偶数、K>2；FP4 WeightNZ只允许X非转置。ND双方FP4可静态/动态图，WeightNZ只静态图。MX动态图的ND尺度还要求K>64、两输入batch轴不为1；WeightNZ的MX只列双方E4M3或双方FP4。ND尺度与输入转置对应，MX scale/token的batch也须各自对应输入；图中的转置节点须显式保留。

MX伪量化仅X非转置、W转置：字节ND承载要求K为8倍且仅Eager；WeightNZ要求K/N为8倍且图中K>64。FP32承载只支持WeightNZ和相同K/N约束。T-CG字节ND要求X非转置、W转置，FP32 WeightNZ则两者非转置，K为32倍且不等于32，FP32 NZ的N为8倍；这些维度上限为2^31-1。不能把示例里的随机字节值当作普通FP4浮点数。

## 数据承载、ScaleNZ与布局

INT32的每元素承载8个INT4；连续X为[M,K/8]，W可连续[K,N/8]或从[N,K/8]转置得到[K/8,N]。FP4字节/原生float4_e2m1fn_x2每字节承载2值，FP32打包权重每元素承载8值。这些是位编码，.to(float32)、reshape和声明x_dtype不会完成解包、量化或物理NZ转换。HIF8/FP4的覆盖参数要求8位载体；E8M0覆盖也要求单字节并且载体已编码。

主线中文文档新增ScaleNZ，英文未同步：仅950 MX全量化Eager，weight必须WeightNZ，双方数据同为E4M3或同为FP4，两个尺度都是E8M0，token尺度保持ND。scale固定逻辑[B,ceil(K/64),N,2]，底层存储[B,ceil(N/16),ceil(K/64),16,2]；只有无batch或一个batch轴的3/4维格式转换。scale不随weight的转置再次转置，须连续逻辑stride、storage_offset=0。

原始scale若为[B,N,ceil(K/64),2]，先transpose(-3,-2).contiguous()真实重排，再npu_format_cast；不能只reshape。UINT8/INT8承载E8M0时，格式转换同时指定customize_dtype和input_dtype为E8M0，矩阵乘再声明scale_dtype/pertoken_scale_dtype；这些覆盖不把普通整数变成尺度编码。FP4非转置字节weight[B,K,N/2]仍对应逻辑N完整的ScaleNZ。除ScaleNZ外，MX的ND scale/token仅最后三轴允许非连续。

主线C++明确拒绝ScaleNZ配ND weight；E8M0且WeightNZ+ScaleNZ时豁免weight/scale转置一致检查，仍保留X/token转置检查。发布没有这些检查和豁免，MX尺度batch轴的转置起始索引也仍为0，不能回推新ScaleNZ协议。两版皆先检查aclnnQuantMatmulWeightNz或ND的V5符号，缺失即拒绝，不代表自动回退旧接口；A4W4无编码分支仍可能走V5而非WeightNz。

主线C++新增E4M3×UINT8/原生FP4权重识别，按stride区分N打包与K打包并恢复输出N；发布没有这一专门分支。PyTorch>=2.8的主线显式原生x2_dtype会先归一化，或由原生weight自身识别；MX双方FP4分支、Meta与GE还各有自己的判断条件，不据某一个入口成功概括所有省略覆盖参数的图调用。

## Meta与TorchAir的独立边界

两Meta除shape/batch外还检查bias、scale、offset、group_sizes；提供group_sizes会改变一维尺度检查的分支，不能视为完全验证数据与尺度对应。950一般INT8的二维bias与旧A4W4二维offset在公开文档中出现，而通用Meta仍较窄，不能由Eager协议推导编译必过。主线新增INT8+INT4字节载体分支；该分支也没有在本卡的公开产品表里构成通用新模式，仍需明确后端和产品依据。

TorchAir按is_arch35选择QuantBatchMatmulV4，否则V3；非arch35类型guard只排除两侧都不在INT8/INT32的情况，不构成所有混合输入合法性的检查。V3没有group_size/y_scale等新参数传递，不能把Eager的整数A8W4分组、950伪量化尺度或任何缺省组合无条件复用到V3。

INT4图路径做Bitcast并扩展承载轴，转置需要在图中；主线FP4根据batch单例轴、scale单例轴及转置选择keep_dim或展开，并对X/token与weight/scale补成对转置。发布统一展开、没有这些新单例判断。主线MX A8W4按字节K<=32或FP32承载K<=8拒绝K<=64图模式；发布仅对字节K==32拒绝，不表示其他更小K已被保证支持。

V4把offset接x2_offset，y_offset=None；C++整数A8W4却将其接y_offset，不应混淆两种模式。主线graph_pass的V4融合按成对尺度处理转置，V3另有weight的Transpose/Bitcast换序；不能只看转换器最终transpose属性False就断言没有转置。生成V3/V4接口是手工构图，窄类型docstring不是实际IrDef类型验证，不能用它证明FP8全面拒绝或全面可用。

## 测试质量与验收方式

主线测试文件38个方法、发布28个；分别3/2个无条件skip，原生FP4另有条件skip。A4W4非对称分组和INT32输出均跳过；主线batch MX参考也跳过。许多旧950 FP8/HIF8/MX测试在scale_clone赋值前引用自身，HIF8 helper又是实例方法却裸名调用；部分参考矩阵未转置、token长度不等于M，NumPy对象调用.to，以及直接把FP4/E8M0字节当普通数值。它们不能计为设备精度已验证。

新增T-CG字节NZ/ND、原生FP4与ScaleNZ测试更明确地区分位解码、尺度分组、转置和输出；T-CG参考还包含weight按FP16反量化后舍入FP8，再矩阵乘与y_scale。仅数学公式不保证逐步舍入相同。ScaleNZ测试用非均匀尺度、N==ceil(K/64)防轴交换、ND weight拒绝和X/token转置负例；比常量/只验shape更能检查语义，但本次没有运行。

未执行上游源码、设备、图、梯度或性能测试，也未新增verified。模型验收应按固定版本与产品分别选合法模式，核对逻辑解包、尺度轴顺序/编码、bias和offset位置、输出dtype/batch/空形状；图模式还检查GE转换与转置结构，最后测量完整模型收益。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 量化矩阵乘的二维至六维输入：torch_npu.npu_quant_matmul

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

执行量化的矩阵乘计算，最小支持输入维度为2维，最大支持输入维度为6维。

### 文档签名

```text
npu_quant_matmul(x1, x2, scale, *, offset=None, pertoken_scale=None, bias=None, output_dtype=None, group_sizes=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_matmul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_matmul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_matmul.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quantmatmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quantmatmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
