---
type: API
title: SGLang ADA 分块稀疏注意力接口
description: 说明新原生ADA的GQA、掩码与路由限制，并区分旧attentions接口的Host序列数组、null槽、sparseMode和动态ACLNN边界。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/ada_block_sparse_attention.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/ada_block_sparse_attention/op_host/ada_block_sparse_attention_tiling.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/ada_block_sparse_attention/op_kernel/ada_block_sparse_attention.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/ada_block_sparse_attention/CMakeLists.txt
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/ada_block_sparse_attention/op_host/ops_error.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/ada_block_sparse_attention.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/ada_block_sparse_attention.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pytorch_npu_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/CMakeLists.txt
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_plugin.sh
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ops.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ascendc_ops.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/setup.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/env.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/lib.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/build.sh
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
---

# SGLang ADA 分块稀疏注意力接口

## 接口原型

```python
from sgl_kernel_npu.operators.attention import ada_block_sparse_attention

def ada_block_sparse_attention(
    query,
    key,
    value,
    sparse_mask,
    sparse_count_table,
    *,
    input_layout="BNSD",
    sparse_size=128,
    num_heads=1,
    num_key_value_heads=1,
    scale_value=1.0,
    causal=True,
    inner_precise=1,
    pre_tokens=214748647,
    next_tokens=0,
    actual_seq_lengths=None,
    actual_seq_lengths_kv=None,
    impl="auto",
):
    ...
```

## 语义与输入

`ada_block_sparse_attention` 计算块稀疏 `softmax(scale_value * QKᵀ)V`。原生 Ascend C 支持 arch22 的 FP16/BF16；arch35 只能显式选参考实现，不能把参考支持当作原生覆盖。

Q 为 `[B,Nq,S1,D]`，K/V 为 `[B,Nkv,S2,D]`，同 dtype，`Nq % Nkv == 0`；新ascendc后端还要求Nq/Nkv<=64，SetTilingHeadNumRatio的普通if会在超界时返回false并使调用方返回GRAPH_FAILED，不受空OPS_ERR_IF宏影响；一个 KV head 对应一组 query head。多头调用必须显式传入与张量匹配的 num_heads=Nq、num_key_value_heads=Nkv；两参数默认均为1，不会从张量自动推导。num_key_value_heads=0 表示采用 num_heads，仅适用于实际KV头数也等于Nq的情形；调用方必须保证属性与shape匹配；本快照不能保证tiling拒绝所有不匹配值。`input_layout` 只能为 `BNSD`。块宽 `bs=sparse_size` 默认 128；int8/bool 掩码为 `[B,Nq,ceil(S1/bs),ceil(S2/bs)]`，末维可按 32 补齐，补齐区须为零。int32 `sparse_count_table[B,Nq,ceil(S1/bs)]` 必须等于各查询块中有效掩码块数量。

掩码非零表示整个 KV 块可见；`causal=True` 还在最后的对角块内施加逐元素下三角掩码。没有可见 KV 块的 query 块输出全零。结果为与 Q 同 shape/dtype 的新张量。默认分数缩放是 1.0，调用方若需 `D**-0.5` 必须显式传入。

## 实现边界与验证

所有原生输入须位于同一 NPU，非连续输入内部转为连续工作张量。`actual_seq_lengths` 两字段虽然存在，当前仍按定长处理；参考实现只覆盖定长 BNSD 和无窗口限制。不要依据参数存在推导变长或滑窗已实现。`auto` 选 Ascend C，原生不支持或不可用时报错，不重试其他实现。

复核时比较稠密掩码、部分可见块、零可见块和 GQA，另检查补齐区与计数一致性；参考实现覆盖范围外需另建基准。

## 固定快照的路由接线限制

固定Host直接包含本地`op_host/ops_error.h`，其`OPS_ERR_IF(COND,LOG_FUNC,EXPR)`展开为`{}`；放在这些宏中的条件、日志和return均不执行，COND内函数调用也会被擦除。头数属性与shape相等的检查使用此宏，因此不是实际拒绝保证；显式`if/return`仍按源码执行，不能反过来概括为“完全没有校验”。两处宏内`SetInputLayout`虽被擦除，`RunBigKernelTilingWithParams`的普通if短路条件仍会在非310P上调用它；即使末尾`InputLayoutIsTNDLike()`为false，合法BNSD赋值已发生。

公开参数合同不能单独证明每个Host接受的配置都有Device实现。本卡固定提交的独立CANN构建只编译一个`op_kernel/ada_block_sparse_attention.cpp`，router仅声明8个CVDIFF key；其中BNSD的FP16高性能基础key为`1000000000000001012`，BF16为`1000000000000011112`，另有Cube切分加`2000000`的变体。下面的Host路线没有对应router接线：

| 条件 | Host producer | 固定router缺口 |
|---|---|---|
| FP16，`inner_precise=0/2`，selector进入高精度分支；例如采用BNSD、非Cube切分时 | `innerPrecise`取bit0，0/2映射为高精度；CVDIFF在1012上加600，再加`BENCHMARK_TILING_KEY=10^18` | `1000000000000001612`没有声明或高精度模板实例；不能把`inner_precise`参数存在理解为两模式均已接通 |
| Host进入空K/V或空输出分支 | 空张量分支生成`EMPTY_KV_TILING_KEY=20`，设置初始化输出并返回成功，外层加10^18 | `1000000000000000020`未接入；包含空张量头文件不等于调用其body |
| D不按32字节对齐，走CVSAME而非CVDIFF | 对FP16/BF16按16元素对齐记录`isDNoTail=false`；BNSD带tail可生成偏移16/116 | `1000000000000000016`/`1000000000000000116`没有对应router分支 |

这是固定源码中Host key与唯一Device router的静态比对，未在设备复现；可能在代码生成、选核或执行阶段表现为失败，不能补造具体错误码、耗时或输出值。“非空KV中没有可见块时输出零”也不等于上述空KV路线已经接通。调用方应在使用本快照前核对所选key与编译产物，并用目标设备精度用例验证；当前资料不足以保证Host接受的全部形状和精度模式均可用。

证据为`TilingGetTilingKeyAttentionAscendC`、`RunBigKernelTilingWithParams`和`TilingAdaBlockSparseAttention`，以及唯一kernel源的`TILING_KEY_IS`列表。本API卡记录selector与router的已知无匹配终点；没有匹配分支的key不具备可用输出保证，不能把失败终点等同于尚未读取的源码依赖。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关源码知识

- [完整Host/Device路线、错误宏与资源边界](../../operators/aclnn/transformer/attention/sgl_ada_block_sparse_attention.md)

## 旧attentions命名空间的独立wrapper

前文GQA/稀疏mask公式、自有Host错误宏和router无匹配终点限定新 `sgl_kernel_npu.operators.attention.ada_block_sparse_attention`。旧 `torch.ops.attentions.ada_block_sparse_attention` 是独立PrivateUse1插件，最终动态调用 `aclnnAdaBlockSparseAttentionGetWorkspaceSize/aclnnAdaBlockSparseAttention`；同名动态符号不证明装载到前文那一份新Host/Device。

| 旧schema参数 | 默认值/本地行为 |
| --- | --- |
| query/key/value/sparse_mask/sparse_count_table | 必选Tensor，原样转描述符；本wrapper未检查rank、dtype、mask/count一致性、头数整除或同device |
| input_layout | 默认BNSD；唯一明确layout guard为拒绝TND，错误 `input_layout currently does not support 'TND'.`；其它字符串在本层未被白名单检查 |
| sparse_size/num_heads/num_key_value_heads | 128 / 1 / 1，原样传，不由输入shape自动推导 |
| scale_value/causal/inner_precise | 1.0 / True / 1，原样传 |
| pre_tokens/next_tokens | **214748647** / 0；pre_tokens确实少于常见2147483647，必须按注册字面值保留 |
| actual_seq_lengths/actual_seq_lengths_kv | 可选Host int64数组（Torch int[]? / OptionalIntArrayRef），缺省None在wrapper变为空IntArrayRef，再调用aclCreateIntArray；不是device Tensor，也不作为null tensor传入 |
| 内部sparseMode | 固定int64 0，不是公开可选参数 |
| attention_out | 仅一个输出，shape/dtype/options/NPU format均继承query；返回新allocation |

旧调用的参数槽顺序也有独立合同：Q/K/V后先两个null Tensor，再actSeqLen/actSeqLenKv；接着五个null Tensor，然后sparse_mask/sparse_count_table；标量按num_heads、scale、pre/next、inputLayoutPtr、num_key_value_heads、sparseMode=0、inner_precise、sparse_size、causal，最后attention_out。这些null槽没有对旧Torch用户暴露，不能从外部ACLNN可选参数存在推断本wrapper支持设置它们。

旧本地wrapper没有使用序列数组计算路由，也没有把它们删除，而是实际传给动态ACLNN；不能把前文新原生“仍按定长处理”的结论直接移入旧动态实现。旧schema没有impl，缺符号或ACLNN返回非零即抛错，没有新Python参考实现重试。旧接口的实际平台和CANN版本未由本次固定材料确认；本卡A2/A3范围仅对应前文新原生实现。

### 旧插件的加载、描述符与两段式边界

旧独立package名为attentions，import先将包内ops/vendors/aie_ascendc与customize目录置于原ASCEND_CUSTOM_OPP_PATH之前，再在NPU可用时加载plugin/libPTAExtensionOPS.so；TORCH_LIBRARY(attentions)与PrivateUse1注册暴露对应torch.ops.attentions接口。csrc/attentions/csrc/CMakeLists.txt显式编译六个wrapper（la、rain、ada、sparse estimate、layernorm、pool indexer）及注册/find_op_path，使用C++17，ABI宏取USER_ABI_VERSION（仅0/1，缺省0），链接torch/torch_npu/ascendcl/nnopbase/opapi。build_plugin.sh从已安装toolkit配置环境并复制so入Python包，build_ops.sh只选择laser_attention、ada_block_sparse_attention、sparse_block_estimate三项；这个列表不证明LayerNorm或Rain核心也随包提供。构建脚本未固定可核验的CANN版本，不能由其latest路径或其他新接口推导旧wrapper版本。

EXEC_NPU_CMD按“ASCEND_CUSTOM_OPP_PATH中各op_api/lib的libcust_opapi.so → ASCEND_OPP_PATH/vendors/config.ini的load_priority顺序 → 默认libopapi.so”逐符号查找API及GetWorkspaceSize；两者各自解析，未强制来自同一个so。路径列表在共享库初始化时保存，函数指针为模板静态缓存，不会逐次重新探测环境。缺符号TORCH_CHECK失败，没有Python参考fallback。

Tensor转换保留sizes/strides/storage_offset和原storage指针，并按维数选ACL format：3D=NCL、4D=NCHW、5D=NCDHW、其余ND；storageDims为storage字节数/itemsize的一维容量。它不是按input_layout字符串重新转形、转置、连续化或重排数据。未定义Tensor/缺省optional Tensor转nullptr；IntArrayRef调用aclCreateIntArray转换为AclIntArray，空数组也经该创建函数，而非同义的null tensor。包装层支持的dtype映射不单独证明外部算子支持该dtype。

调用顺序为可选InitHugeMemThreadLocal → 转换参数并调用GetWorkspaceSize得workspaceSize/executor → size>0分配Byte NPU workspace（0为nullptr）→ 取当前NPU stream → OpCommand自定义handler调用第二阶段 → 正常返回时ReleaseConvertTypes/ReleaseHugeMem → cmd.Run后UnInitHugeMem。非零两阶段状态用aclGetRecentErrMsg抛错；源码未用RAII覆盖所有异常清理路径，handler按值捕获描述符裸指针但不捕获workspaceTensor本体，不能仅凭本地代码宣称异步或异常生命周期已验证。executor、底层Host/Device算法与流完成语义依赖实际安装库及torch_npu；本卡只记录wrapper，不提供源码级完整Operator闭包或运行通过结论。

旧wrapper证据为[ada_block_sparse_attention.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/ada_block_sparse_attention.cpp)与[register_ops.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp)。未将外部核心调用名冒充完整Operator，未执行编译、插件加载、真机、数值或性能测试，无verified事件。
