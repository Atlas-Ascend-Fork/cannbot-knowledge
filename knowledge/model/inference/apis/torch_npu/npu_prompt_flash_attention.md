---
type: API
title: 全量注意力（torch_npu.npu_prompt_flash_attention）
description: torch_npu.npu_prompt_flash_attention：对 Prompt 输入执行全量注意力计算。 区分A2/A3与310P全量注意力，说明稀疏量化、输出布局及固定版本图默认和验证限制。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_prompt_flash_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prompt_flash_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_prompt_flash_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prompt_flash_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_prompt_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_prompt_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_prompt_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_prompt_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- 310p
aliases:
- torch_npu.npu_prompt_flash_attention
- PromptFlashAttention
---


# npu_prompt_flash_attention：全量注意力与稀疏量化组合

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，本卡覆盖A2/A3及310P受限推理。固定发布页 `dedc316708372c9a8bfde4527abd2a94b74840f5` 已独立核对，差异见下文；不从同名或文案修订推断旧栈运行行为完全一致。主线C++与TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter均显式拒绝950。

## 接口与布局

```text
npu_prompt_flash_attention(Tensor query, Tensor key, Tensor value, *, Tensor? padding_mask=None, Tensor? atten_mask=None, Tensor? pse_shift=None, int[]? actual_seq_lengths=None, Tensor? deq_scale1=None, Tensor? quant_scale1=None, Tensor? deq_scale2=None, Tensor? quant_scale2=None, Tensor? quant_offset2=None, int num_heads=1, float scale_value=1.0, int pre_tokens=2147483647, int next_tokens=0, str input_layout="BSH", int num_key_value_heads=0, int[]? actual_seq_lengths_kv=None, int sparse_mode=0) -> Tensor
```

公开入口为torch_npu.npu_prompt_flash_attention。A2/A3的query/key/value用相同FP16/BF16/INT8、连续ND；310P仅FP16。常用BSH/BSND/BNSD；BNSD_BSND将输入BNSD转输出BSND。TND在长度参数与实现中另行支持，输出[T,N,Dv]，不能只按“同query shape”处理Dv不同的路径。

num_heads是Python整数。显式num_key_value_heads须等于KV真实N并整除query头数，比例≤64；默认0表示同头数。发布页曾反写整除方向且参数类型有List/int混写，主线Schema是整数头数和int[]长度列表。

A2/A3页面上限B≤65536、N≤256、S≤20971520、D≤512，BSH/BSND还要求N*D<65535；D未32字节对齐时B最多128，页面末尾又称不支持维度不对齐，本卡采用满足对齐的路径，不从局部上限扩展非对齐支持。20M上限不是时延保证，长序列可能超时；切分时需保持全局Softmax与mask语义，不能把独立分块输出直接拼接。

## 长度和mask

非TND时actual_seq_lengths及actual_seq_lengths_kv是每batch有效Q/KV长度，单元素可供所有batch使用，或至少B项取前B项，其他长度不支持，不能大于真实长度。TND必须分别传累计结束位置，非负且单调不减，用列表项数确定batch；这与[IFA](npu_incre_flash_attention.md)的独立KV长度不同。

padding_mask预留不用。atten_mask用连续BOOL/INT8/UINT8，常见形状[Sq,Sk]、[B,1,Sq,Sk]等，额外padding列填1。pse_shift为[B,N,Sq,Sk]或[1,N,Sq,Sk]、FP16/BF16并遵守query类型组合；FP16输入带pse强制高精度。

|sparse_mode|mask及窗口条件|
|--|--|
|0 default|不传mask时忽略pre_tokens/next_tokens，二者按INT_MAX处理；不是默认因果|
|1 allMask|传完整mask；参与计算部分不能整行全遮蔽|
|2 leftUpCausal / 3 rightDownCausal|传2048×2048下三角压缩mask，可带前导1轴；窗口参数忽略|
|4 band|同样需2048压缩mask，结合窗口值；量化路径另有限制|
|5..8|页面明确未支持|

实现另将10..14映射到0..4并设高精度，但公开约束只列0..4；该实现分支不当作已完备验证的公开参数范围。不能只设next_tokens=0而省mask就声称得到因果结果。

## 量化组与输出

|输入→输出|必须存在|必须为空/额外条件|
|--|--|--|
|INT8→INT8|deq_scale1、quant_scale1、deq_scale2、quant_scale2|quant_offset2可选默认0|
|INT8→FP16|前三个中间因子|quant_scale2、quant_offset2必须None|
|FP16/BF16→INT8|quant_scale2|前三个中间因子必须None，offset可选|

deq_scale1/2为UINT64或FP32 pertensor，quant_scale1为FP32 pertensor。输出scale/offset支持pertensor/perchannel；offset的dtype/shape与scale一致，BF16输入可用BF16或FP32，否则仅FP32。perchannel元素积等于输出H或N*D，不支持左padding、Ring Attention和D非32字节对齐。INT8输出不支持band模式的负窗口。

INT8输出带非空offset时，某些整行未计算的组合会被拦截：mode0带mask且Lq-Lkv-pre_tokens>0或next_tokens<0；mode3且Lkv<Lq；mode4且pre_tokens<0或next_tokens+Lkv-Lq<0。mode1/2页面称不触发这组拦截，不表示其他约束免检。KV伪量化参数分离暂不支持。

空query按空输出处理；非空query遇空KV（Sk=0）页面要求全零输出。Meta仅按layout及量化因子推导shape/dtype，不能替代这些运行条件。主线GE Converter拒绝以Tensor传actual_seq_lengths/kv，设备长度路线见[独立封装接口](../torchair/device_length_attention_wrappers.md)。


## 验证边界

按实际软件栈验证目标shape、dtype、mask语义和输出，再比较稳态性能。本次只做固定文档与实现的静态审阅，未执行上游代码或NPU数值/性能测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 两版产品范围与310P限制

完整依据为OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文页及发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页。两版均列A2、A3和Atlas推理系列加速卡（310P），本卡补齐此前漏收的310P；C++两版和TorchAir两版都明确拒绝950。

310P只能用Q/K/V全FP16；不支持PSE、实际Q/KV长度列表、任何列出的量化因子/输出scale-offset，num_key_value_heads只允许默认0，sparse_mode只允许0，pre_tokens只允许2147483647，next_tokens只允许0或2147483647。轴上限B128、N256、S65535、D512。不能将A2/A3的INT8、BF16、GQA和TND能力随平台标签一起推广到310P。

发布属于ascend_26_0_pt28，主线软件配套另核对。发布页曾将num_heads写List[int]、actual_seq_lengths_kv写int，并将GQA整除方向反写；两版Schema都是int头数/int[]长度列表，主线文档修正这些错误。并非发布Python入口真改过类型或整除方向。

## 文档歧义、对齐与稀疏边界

input_layout参数段称BNSD输入输出BSND，但返回段、示例及两个C++分支均表明：只有"BNSD_BSND"把[B,N,S,D]变[B,S,N,D]，普通"BNSD"保持原序。不要因该句省略了复合布局名而给普通BNSD结果再做一次转置。TND虽未在通用布局列表列出，A2/A3长度段及实现均有专门路径；实际前后长度语义应按布局判断，不能从IFA迁移后继续使用独立KV长度。

mask文案用“上三角负无穷”，但公开dtype为BOOL/INT8/UINT8，多余padding列要求填1。数值logit加性mask的解释与后端布尔遮蔽存储分开处理，不能把-inf cast成UINT8当作已验证的mask。稀疏2/3/4的2048固定压缩矩阵还可带1或1,1前导轴，不能任意裁成真实Sq×Skv；mode3文字称rightDownCausal却同时写左顶点，是来源歧义，不据此合并左右因果。

PSE与mask的KV轴不满32字节时建议padding：PSE冗余值不限定，mask冗余值必须1。PSE的Q_S/KV_S必须覆盖实际Q/KV长度，FP16输入带PSE强制高精度。文档对非对齐B上限给局部说明，末尾又称维度不对齐不支持；不能拿建议padding或宽Meta推导任意非对齐路径有效。

量化输出的非空offset与无计算行组合会拦截，中文明确是计算误差风险，英文对应句不完整；按本卡量化条件表及中文列出的四种模式分别判断。mode1/2不触发这一条不表示允许整行全遮蔽或免除其他量化检查。

长序列20M只是轴上限。文档明确列可能超时示例，包括B1/QN20/QS=KVS1048576/D256/KVN1、B1/QN=KVN2/QS=KVS10485760/D256、B20/QN=KVN1/QS=KVS1048576/D256，以及B1/QN10/QS=KVS1048576/D512/KVN1。这些是来源风险示例，没有在本次执行；切S需要保留全局归一化及mask语义，不把分块MatMul相加或独立Softmax拼接当作等价优化。

## C++、Meta和GE构图的版本边界

两版C++分别保留V2R1与V2R2+的PFA函数，主要语义一致；主线增加空layout检查。都调用aclnnPromptFlashAttentionV3，padding_mask预留不传后端，按quant_scale2及QINT8选择输出dtype，按BNSD_BSND/TND选择输出shape。输入空与空KV的全零要求由后端实现，不是包装中显式zero填充，不能仅看到empty分配就判定运行结果未初始化。

两版Meta的两个条件分支文本相同：Torch2.1路径枚举布局且含SH/NSD，新版更宽地按Q/TND/复合布局分配。Meta接受或分配SH/NSD不表示当前公开API新增这些布局；Meta按dtype和shape推导也不能验证零填充、分页/长度值或量化参数互斥。

两个TorchAir转换器固定主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013，语义相同。两种实际长度输入若为Tensor会明确拒绝，列表提升为INT64后送GE；FP16 mask会转UINT8，这个内部兼容分支不能扩大公开浮点mask或赋予-inf cast的正确语义。

C++与Converter都把内部sparse_mode10..14减10并设inner_precise0；公开Schema没有inner_precise参数，文档只允许0..4。转换器签名多出的inner_precise不等于torch_npu公开可调用参数，内部编码不当作已认证的公开模式。

三层默认常量不同：Schema/文档pre_tokens=2147483647，Converter签名为2147473647，生成GE函数为214748647；GE的num_key_value_heads默认1而公开/Converter默认0。正常框架可能显式传入默认值，因此不能只凭常量差就声称所有图执行错误；但直接使用低层函数或迁移构图路径必须检查实际生成属性，不能省略后假定等同公开入口。

生成IR注释还只列FP16/FP32 QKV和输出、浮点mask及UINT64 deq因子，与当前公开BF16/INT8/布尔mask及FP32 deq兼容描述不同。不能以旧IR枚举覆盖产品合同，也不能按通用数值cast推导打包因子解释。

## 测试、示例与验收

custom/base测试主线全文40/47行，发布逐字节一致。每文件仅一个910B方法，FP16 BNSD、B1/N32/S2048/D128，参考MatMul/Softmax/MatMul也在NPU执行。custom使用1/sqrt(128)，base使用1/0.0078125=128且参考相同；后者是本地一致性测试，不是模型通用缩放示范，也不是独立CPU golden。

两方法都有输出近似断言，但没有310P、A3、BF16/INT8量化、PSE、TND、复合输出布局、空输入及稀疏窗口测试。主线单算子示例增加显式因果mask，发布单算子示例没有mask；不能将两者随机输出拿来直接比较。图示例函数并未传mask，却打印“with mask”，且只打印没有相等断言；TORCHDYNAMO_VERBOSE/TORCH_LOGS仍只是局部变量，不等同os.environ日志设置。

本次未执行上游、设备或性能测试，无新增verified。实际部署需分别验目标产品、图/Eager、长度与输出布局、量化和mask组合；吞吐/时延收益单独测量，不以来源示例文本替代通过记录。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 全量注意力：torch_npu.npu_prompt_flash_attention

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

对 Prompt 输入执行全量注意力计算。

### 文档签名

```text
torch_npu.npu_prompt_flash_attention(query, key, value, *, pse_shift=None, padding_mask=None, atten_mask=None, actual_seq_lengths=None, deq_scale1=None, quant_scale1=None, deq_scale2=None, quant_scale2=None, quant_offset2=None, num_heads=1, scale_value=1.0, pre_tokens=2147483647, next_tokens=0, input_layout="BSH",num_key_value_heads=0, actual_seq_lengths_kv=None, sparse_mode=0) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_prompt_flash_attention.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prompt_flash_attention.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_prompt_flash_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_prompt_flash_attention.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_prompt_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_prompt_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_prompt_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_prompt_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
