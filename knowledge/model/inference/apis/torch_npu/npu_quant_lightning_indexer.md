---
type: API
title: SFA 量化稀疏 token 索引（torch_npu.npu_quant_lightning_indexer）
description: torch_npu.npu_quant_lightning_indexer：使用量化 Q/K 及配套 scale，选出稀疏注意力所需的关键 token 索引。 这是 SFA 的稀疏 token 前处理：接收量化 query、key 的 INT8 数据和配套 scale，通过内积、尺度恢复、ReLU、weights 加权及 TopK 生成索引。 区分发布版与主线A3/950的dtype、头数、scale组合及显式HiF8参数限制。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_lightning_indexer.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_lightning_indexer.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_lightning_indexer.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantLightningIndexerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_lightning_indexer.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_lightning_indexer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantLightningIndexerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_lightning_indexer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_lightning_indexer.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_lightning_indexer.py
  role: implementation
created_at: '2026-11-10T03:38:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_quant_lightning_indexer
- QuantLightningIndexer
---


# npu_quant_lightning_indexer：发布INT8与主线产品矩阵

## 版本与范围

基本INT8段依据ascend_26_0_pt28发布来源；主线产品矩阵及两版实现/图转换差异在后文限定。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_quant_lightning_indexer(query, key, weights, query_dequant_scale, key_dequant_scale, query_quant_mode, key_quant_mode, *, actual_seq_lengths_query=None, actual_seq_lengths_key=None, block_table=None, layout_query='BSND', layout_key='BSND', sparse_count=2048, sparse_mode=3, pre_tokens=9223372036854775807, next_tokens=9223372036854775807) -> Tensor
```

接收已经量化的 INT8 Query/Key，使用各自反量化 scale 计算相关性并选 TopK，返回 INT32 索引 Tensor。它不负责从浮点 Q/K 生成量化值和 scale，不能把“量化 Indexer”解释为内部自动完成全部量化。

## 参数与组合限制

- Q/K 连续 ND，D=128，Q 头数固定 64、K 头数固定 1；weights、query_dequant_scale、key_dequant_scale 都为连续 FP16。Q scale/weights 为 (B,Sq,64) 或 (Tq,64)，分页 K scale=(blocks,block_size,1)。
- query_quant_mode/key_quant_mode 都必须传 0，仅支持 per-token-head；签名没有默认值，不因参数段称“可选”而省略。
- 布局与长度：Q=BSND/TND，K=BSND/TND/PA_BSND；非分页布局一致，TND 长度必传累计 INT32，分页 K 必传实际长度与二维 INT32 block_table。block_size 为 16 倍数、≤1024。
- sparse_count 仅 [1,2048]，不能沿用浮点 Indexer 的更大离散取值；sparse_mode=0/3，pre/next 仅最大 INT64，Python 写 (1<<63)-1。
- weights*query_dequant_scale 的结果必须处于 FP16 表示范围，TopK 对 NaN 的排序未定义。

## 验证与模型关联

对比同一反量化尺度下的相关性和索引，检查 scale 轴、FP16 溢出及 NaN；再验证选出的索引可被目标 SFA 消费。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py#L548)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线产品矩阵与逻辑dtype限制

OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 在文档中补列query_dtype/key_dtype并扩展产品矩阵；两版Schema与实现本来均有这两个参数，具体产品不共用一个宽dtype集合。

|主线分支|Q/K|weights、Q scale、K scale|头数|
|--|--|--|--|
|A3|INT8|FP16、FP16、FP16|Q为1..64、K为1|
|950 INT8|INT8|FP16、FP16、FP16|Q只8/16/24/32/64，K为1|
|950 FP8|E4M3FN|BF16、FP32、FP32，或三者均FP16|同950头数限制|
|950 HiF8|hifloat8|BF16、FP32、FP32|同950头数限制|

A3允许PA_BSND的key和K scale第0轴非连续，其他轴连续。A2产品表仍列支持，但没有相同的主线专属扩展矩阵，本卡不把950 FP8/HiF8范围扩大给A2。D=128、sparse_count≤2048、两个quant_mode必传0及NaN排序未定义仍适用。

虽然参数页称query_dtype/key_dtype可指定INT8/FP8/HiF8，C++对显式有值参数只接受HiF8；INT8/原生FP8应保持None，由实际Tensor dtype决定。HiF8 wrapper分支由query_dtype是否HiF8触发，不能只设置key_dtype就认为两边都完成了逻辑解释。dtype声明不做量化或数值cast，真实8bit容器与scale必须配套。Meta不检查这些显式dtype限制，不能据构图占位成功绕过Eager检查。

## 固定来源与接口演进边界

本节完整核对OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda和发布dedc316708372c9a8bfde4527abd2a94b74840f5，以及TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c、发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013。发布配套为ascend_26_0_pt28，主线配套未知，不以独立仓同名API推导兼容。

两版Schema和C++实际均已有query_dtype/key_dtype，发布文档原型未列出它们；主线文档补列与产品矩阵扩展不代表这两个实现参数首次出现。query_quant_mode/key_quant_mode在两版Schema中均无默认值、必须传0，即使参数段称其可选也不能省略。

两版C++要求必选Tensor存在、Q/K非空且每个shape轴为正、sparse_count>0，再由key布局取Nk并分配INT32索引；Meta检查非空/正K并按Q布局分配。它们没有完整验证文档的产品dtype三元组、D128、头数、K上界、scale形状/范围、NaN或分页连续性；Meta成功不等于真实产品支持，也不意味着已经量化或校准输入。

## 反量化尺度、TopK位置与分页消费

公式描述量化Q/K的相关性，经逐token/head反量化尺度、ReLU、query/head权重和跨头归约后，沿key token维选TopK。说明文字出现“沿g方向”时，须结合公式和参考实现区分头维归约与token候选选择；索引不是物理页号，也不是每头独立选出一个专家。

query_dequant_scale/weights按query token/head对应，key_dequant_scale按key token/head对应。分页时KV和K scale都必须按同一个block_table恢复逻辑token顺序，再以各batch有效K长度裁剪；不能只重排KV或直接使用物理cache顺序。主线允许的PA首轴非连续仍须保留其余轴连续和产品矩阵条件。

BSND及分页长度是各batch独立长度，TND是INT32累计Tensor；不要与KL训练接口的SymInt列表混用。非分页Q/K布局保持一致，分页还需真实有效K长度和block_table，block_size为16倍数且不超过1024。sparse_count只在1..2048内，不从浮点Indexer的更大K集合推导支持。

FP16可表示范围约束作用于weights*query_dequant_scale，不能只检查两者各自有限。负scale、溢出及NaN必须按真实量化合同处理，NaN排序没有定义；不能任意跨越ReLU移动乘法来构造所谓等价优化。此接口只返回索引，没有分数/损失或普通评分梯度，不因此获得量化训练反向。

## Eager与TorchAir的HiF8处理差别

两版C++均只接受显式HiF8逻辑dtype；原生INT8或E4M3用Tensor dtype并保持显式参数None。Eager是否创建两侧逻辑Tensor包装由query_dtype触发，单独设置key_dtype不会走同样包装分支。

两版TorchAir转换器也只接受显式HiF8，但分别判断query_dtype/key_dtype，对每侧独立Bitcast为GE的HiF8，随后用custom_op生成QuantLightningIndexer并透传长度、block_table、scale与属性。Bitcast只解释已有位模式，不生成量化值或scale，也不是浮点数值cast。单独设置一侧参数时与Eager分支条件不同，须在实际版本单独核对，不能据转换器存在断言所有路径语义一致。

转换器没有完整实现公开产品矩阵检查；静态图节点生成不构成950所有dtype组合、A2扩展范围或部署兼容的验收。主线产品矩阵中的PR/DT标记仍分别适用，不扩大到旧发布组合。

## 被跳过参考测试与图样例的限度

两版测试各只有一个方法且无条件skip。实际遍历只选BSND、B24/Sq4/Sk512、Nq64/Nk1/D128、block128、模式0、K2048；TND、模式3等helper分支虽存在，没有被这一方法选择。发布只用INT8；主线按950设备名增加原生E4M3与FP32参考分支，但没有覆盖HiF8，也没有遍历主线全部weights/scale类型组合或全部头数。

参考实现先在FP16形成weights*Q scale，QK经ReLU后除1024、转FP16再回FP32，随后加权并乘K scale；正的全局缩放在理想实数下不改TopK次序，不代表中间舍入、溢出或任意负scale也等价。参考排序stable不构成后端并列分数的排序合同。

主线比较先将输出indices沿最后轴按数值排序再展平，阈值0.999，只比较近似集合、忽略排名且允许少量不一致；发布比较方式更严格。不能把主线断言表述成全部索引及顺序完全相等。helper给不足槽预填-1、模式3另屏蔽部分位置，实际模式0方法不验证因果边界或全屏蔽行。

文档图样例只有调用和打印，没有Eager/图结果比较或精度断言；发布样例缺少其调用所需的torchair导入，主线补齐。示例forward直接对可选长度和block_table调用.npu()，仅适用于实际传入Tensor的示例，不能原样当作允许None的通用封装。测试参考helper还会读取NPU设备属性，不能把其CPU标签当作无设备离线执行保证。

本次仅静态阅读，无上游执行、图/设备/数值/性能验收，无新增verified。复核应先按部署产品和固定版本选dtype矩阵，再使用同一量化数据、scale、分页顺序及有效长度比较索引集合与排名，最后验证目标稀疏Attention消费和端到端收益。

## 已有 OpPlugin 7.3.0 文档与版本边界

### SFA 量化稀疏 token 索引：torch_npu.npu_quant_lightning_indexer

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

使用量化 Q/K 及配套 scale，选出稀疏注意力所需的关键 token 索引。

### 输入、输出与行为

这是 SFA 的稀疏 token 前处理：接收量化 query、key 的 INT8 数据和配套 scale，通过内积、尺度恢复、ReLU、weights 加权及 TopK 生成索引。文档“存8算8”指该索引内积路径，不能据此宣称后续 SparseFlashAttention 全链路也采用 INT8 计算。

### 文档签名

```text
torch_npu.npu_quant_lightning_indexer(query, key, weights, query_dequant_scale, key_dequant_scale, query_quant_mode, key_quant_mode, *, actual_seq_lengths_query=None, actual_seq_lengths_key=None, block_table=None, layout_query='BSND', layout_key='BSND', sparse_count=2048, sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_quant_lightning_indexer.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_lightning_indexer.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_lightning_indexer.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantLightningIndexerKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_lightning_indexer.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_quant_lightning_indexer.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantLightningIndexerKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_lightning_indexer.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_lightning_indexer.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_lightning_indexer.py)（implementation）
