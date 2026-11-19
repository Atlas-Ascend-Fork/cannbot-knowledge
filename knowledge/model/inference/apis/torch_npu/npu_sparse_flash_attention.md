---
type: API
title: SFA 长序列稀疏注意力（torch_npu.npu_sparse_flash_attention）
description: torch_npu.npu_sparse_flash_attention：SFA 长序列稀疏注意力。sparse_flash_attention（SFA）是针对大序列长度推理场景的高效注意力计算模块，该模块通过“只计算关键部分”大幅减少计算量，然而会引入大量的离散访存，造成数据搬运时间增加，进而影响整体性能。 限定发布来源的 MLA-absorb 模式，说明 D=512/64、有效索引、TND 长度及输出占位。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_sparse_flash_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_flash_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_flash_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SparseFlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_sparse_flash_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SparseFlashAttentionGradKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_sparse_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SparseFlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SparseFlashAttentionGradKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_sparse_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/sparse_flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/sparse_flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-10T03:38:50Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_sparse_flash_attention
---


# npu_sparse_flash_attention：MLA 稀疏索引与分页契约

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_sparse_flash_attention(query, key, value, sparse_indices, scale_value, *, block_table=None, actual_seq_lengths_query=None, actual_seq_lengths_kv=None, query_rope=None, key_rope=None, sparse_block_size=1, layout_query='BSND', layout_kv='BSND', sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1, attention_mode=0, return_softmax_lse=False) -> (Tensor, Tensor, Tensor)
```

只对 sparse_indices 指定的 KV 位置计算 Attention，返回 (attention_out,softmax_max,softmax_sum)。本提交只支持 attention_mode=2（MLA absorb），虽然签名默认写 0，调用时必须显式指定 2。推理与图模式保持 return_softmax_lse=False，后两项不能作为有效统计消费。

## 参数与组合限制

- Q/K/V 连续 ND、同为 FP16/BF16；Q 头数为 {1,2,4,8,16,32,64,128}，KV 头数只为 1。Q/K/V 的 D 固定 512，query_rope/key_rope 的 D 固定 64；MLA-absorb 模式要求 K/V 共享底层数据，不能从同页 clone 示例推定任意独立 V 都可用。
- sparse_indices 为连续 INT32，BSND 下 (B,Sq,1,sparse_size)，TND 下 (Tq,1,sparse_size)；每行有效索引在前、无效在后，sparse_size>0。
- Q 布局 BSND/TND，KV 为相同布局或 PA_BSND。TND 长度为必传 INT32 累计边界，分页 KV 使用真实独立长度并提供二维 INT32 block_table。
- sparse_block_size 为 [1,128] 内 2 的幂，且整除分页 block_size；后者为 16 倍数、≤1024。稀疏块与缓存页大小不是同一参数。
- sparse_mode=0 或右下因果 3；pre/next 仅最大 INT64，Python 写 (1<<63)-1。规模和稀疏布局仍需与 Indexer 配套，不由减少计算量保证整体加速。

## 验证与模型关联

以相同稀疏位置、因果方向和 scale 构造参考，分别验证分页与 TND、有效索引尾部、RoPE 拼接及输出；精度和搬运时间单独验收。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py#L1660)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线CANN门槛、950与sinks

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 将value声明为允许None但无省略默认值的位置参数，C++及Meta均要求value=None时CANN≥9.2；原CANN9.0发布基线不能直接使用该分支。输出统计关闭时C++/Meta返回两份FP32[0]空Tensor，不是有效LSE。

主线新增sinks可选参数：存在且defined时直接调用aclnnSparseFlashAttentionV2，没有相同的符号探测回退；A2/A3推理系列专节明确不支持sinks，不能因函数有此参数就启用。950列FP32[Nq] sinks，并把Nq扩展到1..128，但sparse_block_size只1。A2/A3仍为原离散头数和1..128的2幂稀疏块。

950只在PA_BSND时允许key/value/key_rope的第0轴非连续，A2/A3仍连续；其他轴或非分页布局不能从总参数段的宽说明扩展。sparse_mode=0只取消额外因果mask，仍按sparse_indices选择KV；mode=3在所选KV上叠加右下因果j≤Lkv-Lq+i，不意味着先选索引便已满足因果。

value=None的共享KV解码与sinks的新分支应分别核对运行库和实际布局，不把各自参数可用推定成任意联合组合已验证。attention_mode默认0与只支持2的限制、D=512/64及return_softmax_lse推理关闭仍适用。

## 完整版本与索引选择语义

以上发布合同及主线扩展分别绑定OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5与d84e9b1d6a558e5f27973cd4329f62968e46fdda。发布属于ascend_26_0_pt28，只有A2/A3公开推理产品；主线增加Ascend950系列（包含旧称Atlas A5）PR/DT。主线产品与新增nullable value/sinks不能倒推为发布CANN9.0可用。

sparse_indices中的b是**稀疏块号**，选中从b*sparse_block_size开始的一段token，不是PagedAttention物理页号。先用逻辑稀疏块选择KV，再由分页表映射存储；稀疏块大小与缓存页block_size分别管理。每行有效项连续在前、无效项在后，不要求有效项恰好占一半数量；测试用-1后缀并遇首个-1停止，不能让无效项插在有效项中间。

主线补上lightning_indexer→索引格式化→SFA的完整流程，random.sample仅为示例，不能当模型重要性选择算法。mode0取消额外因果约束，仍只对所选KV计算；mode3进一步按j≤Lkv-Lq+i做右下因果。指数归一化只在相同有效集合上可比较，选得更少不等于输出与稠密Attention等价，也不保证离散访存总耗时下降。

## 参数、产品与连续性细节

Q连续FP16/BF16、D512，RoPE两项D64；Nkv固定1。A2/A3的Nq为1/2/4/8/16/32/64/128，sparse_block_size为[1,128]的2幂，分页时整除16倍数且≤1024的缓存页大小。950的Nq为1..128，但sparse_block_size只1；非分页KV仍连续，只有PA_BSND的K/V/K_rope允许第0轴非连续。英文主线K总参数段写“不支持非连续”，中文及950专节给出分页例外，按专门条件限定，不扩大到其他轴。

BSND长度Tensor是逐batch真实长度，TND则为INT32非负单调累计前缀，用元素数确定batch；PA_BSND的KV长度必传且为逐batch真实长度。分页表INT32[B,ceil(S2max/block_size)]或更宽，Q与KV普通布局需相同，分页KV可搭BSND/TND Q。不要拿IFA的INT64 Python列表或训练V3的CPU INT64 Tensor替换本接口INT32 Tensor合同。

value仍是第三个位置参数，主线可显式None但不能省略；只有CANN≥9.2.0允许。C++缓存数值版本谓词，Meta使用get_cann_version字符串比较，两处实现不能替代部署配套核验。传Tensor时仍需满足公开同dtype/shape及共享KV语义；包装未逐项检查不意味着允许空V或任意独立V。

attention_mode默认0但文档仅允许2，明确传2；pre/next只允许INT64最大值，发布原型的2^63-1是数学表示，在Python不能写成异或运算，使用(1<<63)-1。主线没有把窄硬件约束自动写入包装检查，不能从Schema的all_version或宽参数类型推导所有后端版本、产品及组合可用。

## 后端参数顺序与图适配

发布与主线前向都调用同名aclnnSparseFlashAttention，但传参次序不同：发布把scale_value放在sparse_indices之后、block_table之前；主线把scale_value移到key_rope之后。主线sinks非空时又直接走aclnnSparseFlashAttentionV2，未通过缺符号探测回退。该静态差异要求TorchNPU/OpPlugin与CANN严格配套，不能因符号同名、Python原型接近就只替换共享库或某个源码文件；本次未编译或观察ABI故障。

两个固定TorchAir转换器分别为主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013，均用custom_op("SparseFlashAttention")构图，透传索引、长度、布局等属性并保留三个输出，主线另按需传sinks。转换器不执行稀疏索引选择、不校验全部产品/长度值，也不从Tensor类型注解就证明value=None图分支可运行。

统计关闭时后两项是FP32[0]Tensor，不是LSE值、概率或None；打开时是max与sum两张统计，BSND[B,Nkv,Sq,Nq/Nkv]，TND[Nkv,Tq,Nq/Nkv]，名字return_softmax_lse不代表直接输出logsumexp。公开文档只在训练且非PA场景允许打开，并明确图模式不支持；整页产品又以推理为主，不能凭内部梯度存在扩展训练产品支持。

发布Meta明确拒绝return_softmax_lse=True的torch.compile，主线移除了这条检查但公开图限制未变。Meta分配出统计shape不表示图模式已认证；PA路径也不能因为包装能按key尺寸分配统计就启用训练统计。

## 内部反向的数据依赖

两版Autograd对Q/K/V/Q_rope/K_rope生成五个梯度，保存前向输出和max/sum；不会自动把return_softmax_lse从False改True，也不把block_table带到梯度算子。因此不能直接对推理缺省的空统计或分页路径求导并期望自动补齐有效中间值。sinks不在梯度输入列表，没有dSinks；主线sinks产品承诺应按其推理用途使用。

主线value=None时d_value为shape[0]空Tensor，D/KV合并计算的梯度由后端处理；两版无RoPE时对应梯度也用空Tensor占位。梯度包装固定deterministic=True，attention_mode虽在接口中接收，却没有作为后端调用参数转发；不能据这些字段推导任意attention_mode训练等价性。这里记录内部数据依赖，不构成对未公开训练组合的推荐。

## 测试参考与真实覆盖

主线测试全文451行、发布通过完整215行差异核对。发布只有两个方法，均因旧CANN而无条件skip；主线保留这两项，新增一个950 sinks方法及一个value=None方法，None方法也无条件skip。未执行其中任何方法，无新增verified。

CPU参考将value直接设为key.copy()，不使用传入的任意V；它验证共享KV含义，不能认证独立V路径。PA恢复helper只遍历length//block_size的完整页，未处理余数尾页；普通TND辅助函数不构成所有KV TND路径已覆盖。测试调用均为FP16 BSND、B4/Sq1/Nq128、D512+RoPE64、sparse_block_size1，未实际调用PA/TND、块稀疏、BF16、统计输出或反向。

基础和sinks方法只要求超过99%的元素满足rtol0.005/atol0.0001，不是所有元素误差门槛。名为sparse_size_zero的skip测试还把空索引当正常计算比较，而当前包装明确拒绝空sparse_indices，不能据测试名称放宽输入。None测试只检查shape/错误文案，假设支持范围为Soc220..259；它不是950 None支持的运行证据，也不覆盖精度或梯度。

文档两个调用例子无数值断言；图例Network忽略传入block_table、pre/next而写None/最大值常量，不能当分页或窗口更新示范。部署需按真实稀疏集合、因果位置、缓存布局和目标软件版本验证输出，训练另核有效统计和五项梯度，性能拆分选择算法、离散搬运及Attention总耗时。

## 已有 OpPlugin 7.3.0 文档与版本边界

### SFA 长序列稀疏注意力：torch_npu.npu_sparse_flash_attention

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

sparse_flash_attention（SFA）是针对大序列长度推理场景的高效注意力计算模块，该模块通过“只计算关键部分”大幅减少计算量，然而会引入大量的离散访存，造成数据搬运时间增加，进而影响整体性能。

### 文档签名

```text
torch_npu.npu_sparse_flash_attention(query, key, value, sparse_indices, scale_value, *, block_table=None, actual_seq_lengths_query=None, actual_seq_lengths_kv=None, query_rope=None, key_rope=None, sparse_block_size=1, layout_query='BSND', layout_kv='BSND', sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1, attention_mode=0, return_softmax_lse=False) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_sparse_flash_attention.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_flash_attention.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_sparse_flash_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SparseFlashAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_sparse_flash_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SparseFlashAttentionGradKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_sparse_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SparseFlashAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SparseFlashAttentionGradKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_sparse_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/sparse_flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/sparse_flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
