---
type: API
title: 量化 KV 稀疏注意力（torch_npu.npu_kv_quant_sparse_flash_attention）
description: torch_npu.npu_kv_quant_sparse_flash_attention：`kv_quant_sparse_flash_attention`在`sparse_flash_attention`的基础上支持了[Per-Token-Head-Tile-128量化]输入。 该版本面向长上下文稀疏注意力，支持量化 KV 的 Per-Token-Head-Tile-128 路径。 区分发布INT8与主线950低精度扩展，核对混合存储、512维输出、图适配和测试边界。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_kv_quant_sparse_flash_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_quant_sparse_flash_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvQuantSparseFlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kv_quant_sparse_flash_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_quant_sparse_flash_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KvQuantSparseFlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_kv_quant_sparse_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_kv_quant_sparse_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/kv_quant_sparse_flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/kv_quant_sparse_flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
created_at: '2026-11-10T03:38:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_kv_quant_sparse_flash_attention
---


# npu_kv_quant_sparse_flash_attention：混合存储与 512 维输出

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_kv_quant_sparse_flash_attention(query, key, value, sparse_indices, scale_value, key_quant_mode, value_quant_mode, *, key_dequant_scale=None, value_dequant_scale=None, block_table=None, actual_seq_lengths_query=None, actual_seq_lengths_kv=None, sparse_block_size=1, layout_query="BSND", layout_kv="BSND", sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1, attention_mode=0, quant_scale_repo_mode=1, tile_size=128, rope_head_dim=64) -> Tensor
```

使用 INT8 KV 和内嵌反量化参数执行稀疏 MLA。返回一个 Tensor，不是普通 SFA 的三返回。文档称输出同 query shape，但同提交构造输出的实现明确从 query 尾维减去 rope_head_dim：输入 Q 尾维 576、rope=64 时实际输出尾维 512，与其示例一致。

## 参数与组合限制

- 发布公开的Q为连续ND、FP16/BF16，由nope512+rope64拼接，Q头数取{1,2,4,8,16,32,64,128}，KV头数1；K的INT8字节混合存储尾维656=512+64*2+4*4，V形状的文档/示例差异及主线类型扩展见下文，不能对整个Cache做普通int8数值解释。
- 必须显式传 key_quant_mode=value_quant_mode=2（per-tile）、attention_mode=2（MLA absorb），quant_scale_repo_mode 只支持 1（混合存储），tile_size=128、rope_head_dim=64。两个单独 dequant_scale 参数为预留，保持默认。
- Q 支持 BSND/TND，KV 支持同布局或 PA_BSND；TND 必传 INT32 累计长度，分页 KV 必传真实长度和二维 INT32 block_table，block_size 为 16 倍数且≤1024。
- sparse_indices 为连续 INT32，shape=(B,Sq,1,sparse_size) 或 (Tq,1,sparse_size)，有效索引在前、无效在后。sparse_block_size 为 [1,16] 内 2 的幂且整除 block_size，不能沿用浮点 SFA 的最大 128。
- sparse_mode 只支持 0/3，pre/next 保持最大 INT64；Python 显式实参写 (1<<63)-1。输出由实现按 Q 布局分配，并要求 Q/Key/indices 非空。

## 验证与模型关联

先按字节布局拆出 nope、RoPE 与 FP32 scale 构造反量化参考，再比对稀疏 Attention；独立核对输出尾维 512，不能依文档概括分配为 576。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py#L1653)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 完整版本与产品边界

发布来源OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5属于ascend_26_0_pt28，文档公开A2/A3、INT8 KV。主线d84e9b1d6a558e5f27973cd4329f62968e46fdda另公开Ascend950系列（包含旧称Atlas A5）PR/DT、HiF8及float8_e4m3fn；950的Q头数可用48，A2/A3仍排除48，不能把主线列表整体回填发布产品合同。

两版Schema、C++及Meta其实都已包含key_dtype/value_dtype，发布中文原型没有列出这两个尾部可选参数。实现存在HiF8分支与发布文档公开INT8范围分别保留；同一函数名或可绑定参数不足以证明发布CANN9.0已支持950/HiF8。主线950的sparse_block_size只1，A2/A3仍限[1,16]内2的幂并在分页时整除缓存页大小，不能沿用参数概述中的上限128。

主线950仅允许INT8、HiF8、E4M3 KV，A2/A3仅INT8。HiF8时sparse_size固定2048；其他类型不能据这个用例推断也只支持2048。Q始终为FP16/BF16，尾维576；返回Tensor尾维512。通用参数段允许PA_BSND的K/V第0轴非连续，950专节仅重申K，A2/A3专节禁止K非连续；现有文案不足以替任意产品及轴上的V非连续组合认证。

## 混合存储与输出约束的证据边界

量化形式为Per-Token-Head-Tile-128，K存储包含512维nope、同Q类型的64维RoPE和4个FP32反量化scale，按一字节载体计为656。英文主线仍把k_nope写为INT8，而中文及产品专节已列HiF8/E4M3，不能把所有载体一律按有符号INT8数值解释，也不能把全段普通cast成另一个dtype。

文档限制段把KV_D概括为656，但两个文档示例和测试均先克隆未拼接的512维K作为value，再把RoPE/scale附到key上；value参数段本身只明确N=1、类型与key一致。两版包装仍将value原样传后端，没有删除该实参。这里保留文档与示例的形状差异，不能把value称作无用参数、自动补齐656或用任意独立V替换共享KV语义；部署应核对匹配版本的底层合同。

两版C++及Meta按query末维减rope_head_dim分配BSND/TND输出，故576-64=512；不是输出中再附回RoPE。文档“输出同query shape”的概述与实现、示例不符。图例把单Tensor结果取[0]后打印，却展示四维shape，这一打印不一致不能作为单Tensor/tuple或batch维合同的依据。

## 稀疏索引、长度与因果集合

索引INT32连续且非空，元素是逻辑稀疏块号，从编号乘sparse_block_size开始选择token，再通过block_table取分页存储；不是物理页号。有效项应连续在前、无效项在后，并非恰有一半项有效。mode0仍计算所选集合，只是不再加因果屏蔽；mode3在集合内按j≤Lkv-Lq+i保留右下因果位置。

BSND长度是逐batch值，TND长度为单调非负的INT32 Tensor累计前缀；TND两侧分别必传相应长度，PA_BSND必传KV长度。普通Q/KV布局应相同，分页KV另由二维INT32映射表和实际长度解释。映射表宽度至少ceil(最大真实KV长度/block_size)，缓存页大小为16的倍数且≤1024，不能把它与稀疏块大小混为一个参数。

key_quant_mode/value_quant_mode必须2，attention_mode必须显式2而非其默认0；quant_scale_repo_mode只1，tile_size128、rope_head_dim64。pre/next只允许INT64最大值，Python实参使用(1<<63)-1，不能照数学记法写异或。独立dequant_scale两项预留None，scale已混合存储不意味着可以任意另传两个Tensor改变反量化合同。

## HiF8标记、图转换与检查差异

key_dtype/value_dtype只允许HiF8标记或None，显式传INT8/E4M3枚举也会被当前C++拒绝；普通类型靠Tensor推导。C++仅以key_dtype是否HiF8控制分支：成立才把K/V一起交给make_wrapper，否则直接传原Tensor。两个标记需按文档保持一致，不能只设value_dtype期待C++单独变更V解释。

make_wrapper只检查载体itemsize与目标ACL类型一致，再返回Tensor和ACL类型，没有数值量化或字节重排。把uint8标成HiF8不是把任意uint8数值自动量化；测试中的编码函数仅为该测试参考，不构成可移植缓存格式生产方案。两个C++都调用同名aclnnKvQuantSparseFlashAttention，无HiF8缺符号回退或产品完整校验。

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013均对K/V的HiF8标记分别做GE Bitcast，生成KvQuantSparseFlashAttention custom_op单输出，并透传量化/布局/长度属性；Bitcast同样不完成量化校准。主线转换器另外接收sinks，但两版OpPlugin公开Schema均没有sinks参数，不能据转换器局部签名在公开Python接口中直接传sinks。

Meta两版都要求Q/K/V/索引非None且非空，C++只显式检查Q/K/索引非空；图/eager检查差异不构成空V支持。输出形状能推导不表示所有dtype、产品、TND/PA或量化组合可运行。两个仓库的主线也未证明相互配套，应按精确软件组合验证。

## 测试覆盖与模型验证方式

主线558行与发布253行测试全文静态审阅。两版各两个方法，其中基础INT8 BSND方法均无条件skip。主线另一个方法限定950，使用BF16 Q、HiF8 KV、BSND Q/PA_BSND KV、B4/Sq1/Nq48、sparse_size2048、块稀疏大小1；代码有超过99%元素满足rtol0.005/atol0.0001的数值断言，本次未执行，不能写成精度认证。

主线PA参考改为向上取整，并按最后一页有效长度复制，用例3904/256带64 token尾页；发布参考只遍历完整页，忽略余数。两版CPU参考都从K恢复共享KV并覆盖传入value，不能验证任意独立V。主线HiF8参考按uint8识别载体，不覆盖E4M3；没有TND、FP16、其他头数、块稀疏大小或图执行的实际测试结果。

发布另一个950限定方法名含TND，但CPU参考仍访问query.shape[2]并以四维BSND拼接/转置；传入三维TND时存在维度访问风险。该用例还直接生成随机uint8且没有传HiF8标记，不能当正确HiF8编码或发布950支持证明。它的存在与发布文档A2/A3公开范围分别记录，不据此扩展产品声明。

文档示例的随机索引、随机正负scale及混合字节拼接只展示调用，图例只打印无数值断言；不是量化校准或模型质量基准。验证时固定稀疏选择集合、真实长度和因果位置，按精确载体恢复nope/RoPE/scale参考，分别核512维输出、尾页、有效索引及量化误差；性能同时计入选择、缓存构造、离散搬运和Attention总耗时，不能从“量化减少搬运”直接承诺端到端加速。仅公开推理/图使用，没有在此建立训练梯度合同。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 量化 KV 稀疏注意力：torch_npu.npu_kv_quant_sparse_flash_attention

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

`kv_quant_sparse_flash_attention`在`sparse_flash_attention`的基础上支持了[Per-Token-Head-Tile-128量化]输入。

### 输入、输出与行为

该版本面向长上下文稀疏注意力，支持量化 KV 的 Per-Token-Head-Tile-128 路径。稀疏选择减少计算，但离散访存仍可能增加搬运时间；这里不推导通用加速比。

### 文档签名

```text
torch_npu.npu_kv_quant_sparse_flash_attention(query, key, value, sparse_indices, scale_value, key_quant_mode, value_quant_mode, *, key_dequant_scale=None, value_dequant_scale=None, block_table=None, actual_seq_lengths_query=None, actual_seq_lengths_kv=None, sparse_block_size=1, layout_query="BSND", layout_kv="BSND", sparse_mode=3, pre_tokens=2^63-1, next_tokens=2^63-1, attention_mode=0, quant_scale_repo_mode=1, tile_size=128, rope_head_dim=64) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_kv_quant_sparse_flash_attention.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_quant_sparse_flash_attention.md)（primary）
- [补充版本或约束](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/KvQuantSparseFlashAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_kv_quant_sparse_flash_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_kv_quant_sparse_flash_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/KvQuantSparseFlashAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_kv_quant_sparse_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_kv_quant_sparse_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/kv_quant_sparse_flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/kv_quant_sparse_flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）
