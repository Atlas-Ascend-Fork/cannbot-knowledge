---
type: API
title: 分组矩阵乘与 SwiGLU 量化融合（torch_npu.npu_grouped_matmul_swiglu_quant_v2）
description: torch_npu.npu_grouped_matmul_swiglu_quant_v2：将 GroupedMatmul、SwiGLU 与量化组合，减少中间结果的独立处理。 链路按矩阵乘结果进入 SwiGLU 门控激活后再量化理解，不能将单独的浮点 GMM 输出当成融合链最终输出。 逐版限定A2/A3整数与950 MXFP8/MXFP4及per-token路径，区分逻辑N、字节打包、Meta和GE的列表与类型限制。
tags:
- task.optimization
- topic.precision
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulSwigluQuantV2NpuOpapi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulSwigluQuantV2NpuOpapi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_swiglu_quant_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_swiglu_quant_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-10T03:38:44Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_grouped_matmul_swiglu_quant_v2
---


# npu_grouped_matmul_swiglu_quant_v2：分组融合量化、MX尺度与图边界

## 版本与入口

V2融合专家分组矩阵乘、反量化、SwiGLU及输出量化，返回(output,output_scale)两个Tensor，没有V1的预留output_offset。固定OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda与发布dedc316708372c9a8bfde4527abd2a94b74840f5分别核对；TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013也分别限定。发布来源组合为ascend_26_0_pt28，主线尚未确认为配套组合。

前五个必填位置参数依次为x、weight列表、weight_scale列表、x_scale、group_list；后续关键字参数为smooth_scale、weight_assist_matrix列表、bias、dequant_mode、dequant_dtype、quant_mode、quant_dtype、group_list_type、tuning_config，主线文档还列x_dtype、weight_dtype、weight_scale_dtype、x_scale_dtype。发布文档未列最后四项，但发布Schema和C++已有这些参数；不能把文档漏列等同于实现不存在，也不能据实现存在扩展发布产品能力。

发布页列Atlas A2/A3；主线列A2/A3与Ascend950系列（包含旧称Atlas A5）的PR/DT。没有310p支持证据。训练/推理与发布默认确定性的文字是来源声明，本次没有梯度、设备或性能复现。

## 分组、SwiGLU与尺度方向

x为二维[M,K]，group_list为INT64[E]，E为1..1024。group_list_type=0表示累计边界，末值不得超过M；=1表示独立行数，总和不得超过M。两者必须按实际模式解释，不能把[128,128]在默认累计模式下误读成两个非空专家。返回分配M行，只消费分组指定的有效前缀，未指定行不更新；不要读取或用尾部作数值比较。

各专家先做GMM并乘激活和权重反量化尺度，沿输出总宽N拆成两半，前半做SiLU后乘后半。整数per-token输出反量化尺度为行absmax/127，INT8输出为相应取整量化值；950浮点per-token页写absmax/max(type)，不能固定用127。MX输出每32个元素共享指数，公式以round(log2(absmax))-emax生成指数再量化到目标元素类型。emax：E4M3为8、E5M2为15、E2M1为2；中文另列E1M2为1。全零/极端值的舍入饱和细节应依实际后端验证，不能从简化公式补造规则。

dequant_mode=0是激活per-token、权重per-channel，=1是权重per-group，=2是MX；quant_mode=0是per-token、=2是MX。枚举中存在1不等于产品支持输出per-group。tuning_config第一个值为各专家预期token数，后续预留，它不替代真实group_list或改变分组语义；GE把None或空列表规范为[0]。

## A2/A3发布协议与主线双语差异

发布明确A8W8、A8W4 MSD、A4W4。A8W8为INT8 x/weight，weight仅NZ，不支持ND；weight_scale为FP32/FP16/BF16，per-channel[E,N]。A8W4的激活INT8、权重INT4或INT32打包8值，weight_scale表列UINT64，per-channel[E,N]或per-group[E,K_group,N]，需要FP32辅助矩阵。A4W4的x/weight为INT4或INT32打包，发布表列FP32 weight_scale，需FP32 smooth_scale[E,N/2]或[E]广播。x_scale为FP32[M]，输出INT8[M,N/2]与FP32[M]。

A8W4对激活拆高低4bit并用离线辅助矩阵重建，辅助矩阵不能替换成普通bias；A4W4在SwiGLU后乘smooth_scale。bias预留且必须None。发布A8W4的dequant_mode可0/1，其他0；quant_mode只有0。N<=10240，A8W8 K<65536，A8W4/A4W4 K<20000；这些上界来自发布分支，不给950无条件套用。

主线中文的A2/A3参数和类型表只明确INT8权重、二维FP32 scale、dequant_mode=0，并把smooth_scale和weight_assist_matrix限定为None；英文却保留A8W4的0/1、A4W4平滑和辅助矩阵说明。两版公式也仍保留旧低比特场景，NZ段甚至混入FP8/FP4布局示例。因此保留此处双语与发布差异，不把发布低比特表、英文旧说明或测试拼成主线统一支持清单。主线低比特路径应逐项核对实际包、CANN与接口契约。

发布文档把dequant_dtype=0称FP32、quant_dtype=0称INT8，而发布Schema的quant_dtype默认1、dequant_dtype默认0；主线Schema把dequant_dtype改为6，quant_dtype仍1，中文则推荐torch.float32/torch.int8。Torch与GE枚举不同：C++把Torch 6/5/15映射为GE 0/1/27，不能直接搬数字。集成时显式传正确的dtype对象并核对绑定；显式None也不等同于省略，C++某些分支仍读取quant_dtype.value()。

## 950 per-token路径

主线950的per-token可INT8、FP8或HIFLOAT8，但仍以类型组合表为准：INT8权重尺度可FP32/FP16/BF16，FP8/HIFLOAT8权重尺度可FP32/BF16；激活尺度为FP32[M]。中文对该路径明确dequant_mode=quant_mode=0、dequant_dtype为FP32/FP16/BF16，仅单权重和单尺度列表，x不转置、weight可转置；ND的N为偶数，NZ的N须正且为64倍数，N为SwiGLU后宽度的两倍。

中文NZ参数范围增加INT8/HIFLOAT8，并把FP8 per-token的ND与NZ组合分开，NZ权重只列E4M3；英文NZ段更窄。不能以输入总类型列表做任意x/weight/quant_dtype的笛卡尔积。HIFLOAT8使用对应dtype覆盖和8bit承载，不把uint8承载当数值已转换。

## 950 MX布局与输出存储

MX使用E8M0尺度，每块32元素但尺度按两块打包：x_scale为[M,ceil(K/64),2]；单权重weight_scale非转置为[E,ceil(K/64),N,2]，转置为[E,N,ceil(K/64),2]；output_scale为[M,ceil((N/2)/64),2]。末轴2是尺度打包，不是逻辑N。两固定生成GE定义的真实IrDef有FP8/E2M1/HIFLOAT及E8M0范围，旧docstring只列INT8，不应只读注释判类型；IrDef也未列主线转换器新增的E1M2，不据转换器存在宣称该图类型已支持。

ND MXFP8可E4M3/E5M2，N对齐2；ND MXFP4为E2M1，N对齐4。NZ MXFP8表仅E4M3，N对齐64；NZ MXFP4有E2M1/E1M2，N对齐128。MXFP4要求实际K为偶数且不为2。混合MxA8W4指E4M3激活配E2M1权重，权重必须NZ、K对齐32、N对齐128，与整数MSD A8W4分开。

单单单NZ的FP8物理view可为[E,N/32,K/16,16,32]，FP4表列[E,N/64,K/16,16,64]；转置轴顺序相应交换。多权重列表时每专家权重少E轴、尺度少E轴，中文明确四维NZ view/三维MX尺度，但参数段又写尺度列表只支持1，与多列表形状表和主线Eager分支不同。以具体调用及执行模式限定，不能静默消除冲突。

FP4实际元素数与8bit字节shape不同：自定义FP4以8bit承载时一字节装两个值，x_dtype/weight_dtype和实际内轴一起决定解释；原生torch.float4_e2m1fn_x2与自定义E1M2/E2M1的返回包装也有差异。页中的[M,N/2]是逻辑宽，不足以预测每种返回的字节shape。主线FP4测试中同一逻辑输出，FP8返回宽N而打包FP4返回N/2；多权重FP4例返回N/4字节宽，必须同时核对该例的实际逻辑N、承载类型和尺度形状，不按变量名N统一reshape。

## Eager、Meta与版本实现不能互相代替

主线NZ的逻辑N优先由尺度推导：MX要求四维scale并取轴2，非MX取末轴；匹配的多列表NZ MX分支要求SoC>=950、weight/scale列表等长非空、单项2D/3D，并取scale轴1。发布只允许列表1；五维NZ末轴32时取scale轴1，否则由weight轴1*64推N，旧Meta却从weight轴2推N。主线Meta已改尺度推N，但仍强制两列表长度1，因此Eager多列表不等于Meta或图模式兼容。

主线C++专门识别混合MxA8W4 NZ，允许只给weight_dtype；其他分支要求x_dtype与weight_dtype同时有值或同时没有。E1M2仅主线类型检查新增，不能回推发布。MX输出分配依据weight_scale_dtype是否有值，而不是单独检查quant_mode；这些参数必须一致，不能仅改mode不提供匹配尺度与类型。

发布C++把mxfp4_input声明为依赖首次调用参数的static const，主线改为逐次判断，并区分PyTorch<2.8显式覆盖与>=2.8原生FP4。混合dtype调用序列在旧版本需另行验收；这只是静态差异，未报告成已复现故障。主线转置识别同时检查末两维和batch stride，不是任意非连续即转置。

NZ路径先检查CANN是否有aclnnGroupedMatmulSwigluQuantWeightNzV2；ND走aclnnGroupedMatmulSwigluQuantV2。五维view也会被识别NZ，部分分支clone后改存储描述，这不构成任意ND内容到NZ的数值重排。调用前应提供真正符合约定的存储，不能仅靠view或元数据获得正确布局。

## 图模式边界与打包变化

主线文档明确950 WeightNZ的MXFP4/MXFP8支持静态图、不支持动态shape图；单多单MXFP4/MXFP8只支持Eager、不支持图。普通“支持TorchAir图模式”不能覆盖这两个例外。

两GE转换器初始传transpose_weight=False，主线graph_pass需同时匹配weight和scale的Bitcast/Reshape/Transpose相关模式才折叠并改True。没有匹配就保留原图，不依据Python里有transpose便宣布成功消除；实际应检查生成图。

转换器按覆盖类型Bitcast，只有成对FP4覆盖时才对所有weight项做FP4转换，而普通覆盖和scale覆盖只改第0项；不能把多列表Eager支持视为所有列表项已在GE重解释。发布FP4输入会显式扩shape再Bitcast/Reshape，主线改keep_dim=True；输出依torch是否有原生FP4及E1M2/E2M1分别保原生或打包UINT8，不能跨版本复用同一个物理reshape。

输出scale描述也按quant_mode和quant_dtype改为FP32或E8M0。主线Meta对MX返回UINT8承载尺度，而Eager及GE语义为E8M0；核对的是相同编码及实际存储，不把Meta的UINT8当普通整数尺度。

## 测试证据与实际验收

发布文件5个数值/形状方法均无条件skip，其余3个只查dtype路径能否给二维输出或抛异常。主线20个方法中4个无条件skip（两MX数值、两默认dtype），另3个FP4按类型存在性条件skip。新增多项用torch.empty仅验shape/dtype，包括A2低比特和950 MX多列表，不能登记为数值正确。

主线A2有两个未skip的A8W8 CPU数值参考，均只比较有效前缀；一个INT8绝对容差1，另一个RTol1e-2且output_scale容差prec=1.0。A4W4仍只验shape，测试编码出INT64 scale也不能覆盖发布表FP32或主线中文None限制。950 MX参考保留numpy调用遗漏、未定义group_list、错误weight.float32等静态缺陷且已skip，不能作为可运行黄金结果。

主线两默认dtype skip仍写“默认uint8(0)”，但现Schema默认6，不能照旧注释宣布新主线默认必然失败。模式不匹配异常、FP16/BF16/FP32有效dtype等只体现测试意图，本次均未执行。验收需分别检查有效前缀、量化/反量化误差、尺度字节编码、Meta与真实返回形状、目标静态图和部署CANN；没有新增verified或端到端加速承诺。

- [V1接口协议](npu_grouped_matmul_swiglu_quant.md)

## 已有 OpPlugin 7.3.0 文档与版本边界

### 分组矩阵乘与 SwiGLU 量化融合：torch_npu.npu_grouped_matmul_swiglu_quant_v2

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

将 GroupedMatmul、SwiGLU 与量化组合，减少中间结果的独立处理。

### 输入、输出与行为

链路按矩阵乘结果进入 SwiGLU 门控激活后再量化理解，不能将单独的浮点 GMM 输出当成融合链最终输出。

### 文档签名

```text
torch_npu.npu_grouped_matmul_swiglu_quant_v2(x, weight, weight_scale, x_scale, group_list, *, smooth_scale=None, weight_assist_matrix=None, bias=None, dequant_mode=0, dequant_dtype=0, quant_mode=0, quant_dtype=0, group_list_type=0, tuning_config=None) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant_v2.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulSwigluQuantV2NpuOpapi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant_v2.py)（example）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulSwigluQuantV2NpuOpapi.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant_v2.py)（example）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_swiglu_quant_v2.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_swiglu_quant_v2.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
