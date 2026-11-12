---
type: API
title: SGLang稀疏FlashAttention的分离RoPE与索引契约
description: 说明DSA/MLA分离RoPE、稀疏索引和max/sum，并限定固定原生分支复用K作为MM2右矩阵时独立V的语义风险。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/sparse_flash_attention.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.h
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch22/sparse_flash_attention_kernel_mla.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch22/sparse_flash_attention_service_cube_mla.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch22/sparse_flash_attention_service_vector_mla.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_cube_mla.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_vector_mla.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_flash_attention/op_host/sparse_flash_attention.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_flash_attention/op_kernel/sparse_flash_attention.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/sparse_flash_attention.py
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T17:58:17Z'
platforms:
- a2
- a3
- '950'
---

# SGLang稀疏FlashAttention的分离RoPE与索引契约

## 接口原型

```python
from sgl_kernel_npu.operators.attention import sparse_flash_attention

def sparse_flash_attention(
    query,
    key,
    value,
    sparse_indices,
    scale_value,
    *,
    block_table=None,
    actual_seq_lengths_query=None,
    actual_seq_lengths_kv=None,
    query_rope=None,
    key_rope=None,
    sparse_block_size=1,
    layout_query="BSND",
    layout_kv="BSND",
    sparse_mode=3,
    pre_tokens=9223372036854775807,
    next_tokens=9223372036854775807,
    attention_mode=2,
    return_softmax_lse=False,
    impl="auto",
):
    ...
```

## 主接口

`sparse_flash_attention` 的auto调用Ascend C（Torch注册 `torch.ops.npu.sparse_flash_attention`），arch22/35均声明支持；不可用时报错，无自动回退。接口只在调用方给出的稀疏KV分块上计算，既不生成TopK也不把共享KV格式自动转换为其他MLA入口格式。

Q为FP16/BF16 BSND `[B,S1,N1,512]` 或TND `[T,N1,512]`，分离query_rope末维64；K/V可为BSND、TND或PA_BSND `[blocks,blockSize,1,512]`，key_rope相应末维64。非分页KV为BSND或TND时必须与Q布局一致，只有PA_BSND允许搭配两种Q布局。原生KV头固定1，Q头为1..64或128，attention_mode固定2。所有张量同NPU且连续。

int32 sparse_indices为 `[T,1,K]` 或 `[B,S1,1,K]`，乘sparse_block_size展开位置；该值须为[1,128]内的2次幂，950/arch35仅支持1。分页blockSize须为16的倍数、在(0,1024]且能被sparse_block_size整除；-1是终止哨兵，不是任意可跳过空槽，超有效KV长度的位置忽略。分页PA_BSND必须给int32页表，其余布局必须None。TND query必须提供actual_seq_lengths_query，其为`[B]`累计结束位置，不是 `[B+1]` 含零边界；TND KV长度同为前缀和，分页/BSND KV则为有效长度；TND KV和PA_BSND均必须显式提供actual_seq_lengths_kv，分页不能只给页表。不要与flash_mla的cu_seqlens接口混用。

## 输出与验证边界

结果为 `(attention_out,softmax_max,softmax_sum)`，out同Q shape/dtype；后两项是FP32 max/sum，TND形状 `[N2,T,N1/N2]`、BSND为 `[B,N2,S1,N1/N2]`，不是直接LSE。开启时 `max+log(sum)` 得自然对数LSE；关闭时都是空tensor。

原生sparse_mode只接受0或3：0以有效KV长度为可见上界；3（默认）以KV有效长度减Q有效长度加query位置构造右下对齐的逐行因果边界。pre_tokens和next_tokens均必须保持INT64_MAX（9223372036854775807），不支持由此请求自定义窗口。独立torch_native仅覆盖生产DSA组合 sparse_mode=0、attention_mode=2，其他模式不能直接用此参考验收。验证应分开检查NoPE/RoPE合成logits、-1终止、分页表和长度语义，以及由max/sum重建的LSE。

## 固定原生实现的独立V边界

公开说明按`softmax(QKᵀ)*V`描述数学合同，但本快照独立CANN入口`aclnnSglSparseFlashAttention`的下列实际分支没有按该通用合同消费独立value内容：

| 平台/分支 | 已读源码数据流 | 适用边界 |
|---|---|---|
| A2/A3的V_TEMPLATE，正常非空KV时由sparse_block_size<=4选择 | Vector的MergeKv只合并key/key_rope；`ComputeMm2`在V_TEMPLATE从kvMergeGm读取右矩阵，独立valueGm在C_TEMPLATE中才用于搬运 | 不能把独立K与V内容不同的通用attention视为该分支已正确实现；不把较大block的C_TEMPLATE误列为同一数据流 |
| 950原生非空MLA路径（公开sparse_block_size=1） | `InitGlobalBuffer`虽接收value形参，却只绑定key/key_rope等；MM2以共享inputRightBuf的NoPE区作为右矩阵，P复用其RoPE位置 | 实际相当于消费K的NoPE载荷；接口允许传入独立value不等于该value参与计算 |

对K/V共享同一MLA潜在载荷的用途，这一数据流与独立K/V的一般用途必须分开核对。不能仅凭接口具有value参数、输出shape正确或文档列出dtype，就保证独立V情形正确。这里是固定源码的静态追踪，未给出NPU数值复现或验证过的替代方案，也不推广成其它提交、发布wheel或旧`aclnnSparseFlashAttention`入口的行为。

完整Route、POD和内存/同步证据见[A2/A3源码草稿](/model/inference/operators/aclnn/transformer/attention/sgl_sparse_flash_attention.md)与[950源码草稿](/model/inference/operators/aclnn/transformer/attention/sgl_sparse_flash_attention_950.md)。

## 旧Direct Host的实际准备与返回协议

固定树旧legacy注册的 `torch.ops.npu.sgl_sparse_flash_attention` 定义在 `csrc/sparse_flash_attention/op_host/sparse_flash_attention.cpp`，以ge_helper完成Tiling后调用 `EXEC_KERNEL_CMD(sgl_sparse_flash_attention,...)`，不是先调用独立`aclnnSglSparseFlashAttentionGetWorkspaceSize`。前文新Python入口调用的不带sgl_的torch.ops.npu.sparse_flash_attention与此属于不同构建注册，不能用相同C++函数名混淆。下述为已读旧Direct Host事实，公开接口数学及前述K/V风险仍分别按对应入口/Route核对。

### 连续化、校验与输出

旧Direct对query/key/value/sparse_indices先各自`contiguous()`，对有值的block_table、actualQ/K、query_rope/key_rope同样连续化；缺省optional保留None用于Host校验。已有连续storage可能复用，不保证每次创建副本。这条raw调用链的连续化是自有准备机制，不应写成原始非连续输入一定在此函数首部被拒绝。

随后要求Q/K/V和indices均非空，indices为INT32；K/V dtype与Q相同，metadata为INT32，rope dtype匹配对应Q/K；对所有实际输入检查与Q同NPU设备/编号并连续。make_outputs另外检查Q为FP16/BF16 NPU、Q layout只BSND/TND、对应rank4/3，key非空。完整KV layout/head/稀疏属性等检查仍交后续SFAInfoParser/SFATilingCheck处理，不能把局部检查列表当作全部合法域。

| 条件 | attention_out | softmax_max/softmax_sum |
|---|---|---|
| Q=TND | 同Q shape/dtype | 开启时FP32[Nkv,T,Nq/Nkv]；Nkv为PA_BSND key.axis2，否则key.axis1 |
| Q=BSND | 同Q shape/dtype | 开启时FP32[B,Nkv,Sq,Nq/Nkv]，Nkv取key.axis2 |
| return_softmax_lse=False | 同上 | 两个FP32空Tensor[0]，仍返回三项tuple |

开启max/sum时检查key最低rank、Nkv>0及Nq%Nkv==0。这里变量名return_softmax_lse不改变返回的是**max、sum两份Tensor**，不是单独算好的LSE。旧Direct在进入Tiling前拒绝空Q/K/V/indices，因此不能用独立ACLNN卡中可见的EMPTY_Q/EMPTY_KV body推导此旧包装器会把空输入下发成有效no-op。

### Tiling、144B序列化与placeholder

Host用SFAHost::SparseFlashAttention创建OpDef，显式写scale、block size、两个layout、sparse mode、窗口、attention mode和return flag，再依次注册9个输入与3个输出，optional仍占原槽。执行SFAInfoParser::Parse→SFATilingCheck::Process→SFAMlaTiling::DoOpTiling，任一步失败TORCH_CHECK终止，不下发正常body。

成功后创建zero-initialized `std::array<uint8_t,144>`，检查TilingData.GetDataSize恰好144，SaveToBuffer到该数组，再`GetTilingTensor(serializedTilingData)`。这是真实定长序列化ABI，不是按输出Tensor元素数估计tiling字节；generated tiling与Device POD必须保持一致。类型/设备分区、完整字节键、捕获预热、容量和overflow地址复用边界见[GE Helper缓存机制](../../guides/integration/sgl_kernel_npu/sgl_ge_helper_tiling_cache.md)。

workspace按context返回字节数在Q设备分配byteTensor。缺省block_table/actualQ/actualK在**完成Host解析之后**才替换为未初始化INT32 Tensor[1]；缺省query_rope/key_rope替换为Q dtype Tensor[1]。它们提供有效launch地址，不代表拥有合法metadata/rope数值；只能在所选Device分支不读取对应位置的条件下使用。不能把placeholder当作含零长度值的设备数组或自动生成sin/cos。

最终DispatchSparseFlashAttention以tiling.GetBlockDim和同一stream helper下发，返回attention/max/sum三Tensor。旧entry的dispatchKey从GM tiling指针reinterpret读取；新独立ACLNN入口用REGISTER_TILING_DEFAULT/GET_TILING_DATA读相同dispatch字段。固定文件对比中这一entry读法有差异，未把旧native桥改名成新ACLNN ABI；Device核心数学、精度与同步事实按已读对应源码卡复用。

### Meta与异步生命周期

旧`sparse_flash_attention_meta`独立调用make_meta_outputs，用SymInt形成相同逻辑输出shape，关闭max/sum时形状[0]。它检查Q layout/rank与部分key rank，但没有重放runtime路径的dtype/NPU/非空、同设备、Nkv正值或整除等全部校验；meta成功不是实际Device参数可用证明。

contiguous结果、workspace、placeholder、输出与cached tiling的所有权不同：tiling由GE cache维持GM地址，其它Tensor依赖Torch/launch helper与caller的异步storage合同。GetTilingTensor未命中可能上传后同步当前流，命中不等于算子已完成；不能把Direct返回、Meta返回或raw ACLNN下发成功写成完成/验收。捕获前须按完整序列化配置预热；overflow slab的多流复用限制不由此Host自动消除。

本节补齐旧Direct可见Host准备，不新建重复数学Operator，也不把连续化、placeholder或cache helper外部生命周期推定成已验证保证。完整Device Route仍可对照前文两张固定源码草稿；独立K/V内容是否参与MM2须保留其精确平台/selector边界，本次没有数值复现。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
