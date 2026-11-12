---
type: API
title: "旧版SparseBlockEstimate的块掩码估计与接口边界"
description: "保存旧attentions稀疏块估计的采样Matmul、半精度归约、阈值选块、POD和资源同步，并限定TND包装器、输出容量及全局tile状态风险。"
tags: [task.implementation, topic.attention, topic.memory, topic.precision]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/sparse_block_estimate.h
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/sparse_block_estimate.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pytorch_npu_helper.h
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_def.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_proto.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_tiling.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_tiling.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/CMakeLists.txt
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_kernel/sparse_block_estimate.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_kernel/sparse_block_estimate.h
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/CMakeLists.txt
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/CMakeLists.txt
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build.sh
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ops.sh
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ascendc_ops.sh
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_plugin.sh
    role: supporting
created_at: "2026-11-09T17:50:39Z"
updated_at: '2026-11-10T07:03:17Z'
platforms: []
aliases: [sparse_block_estimate, aclnnSparseBlockEstimate, torch.ops.attentions.sparse_block_estimate]
---

# 旧版 SparseBlockEstimate 的掩码估计与原生接口边界

本卡保存固定 dda6 源码中 `torch.ops.attentions.sparse_block_estimate` 的可得接口、算法、Host/POD、搬运和静态边界。它是独立的**块掩码与保留数估计**，不计算attention输出，也不同于LightningIndexer返回TopK位置。这个旧Torch命名空间独立于sgl_kernel_npu.operators的register_operator注册表。

这是`draft` API Reference，平台未知、不填写CANN版本，不声明完整Operator闭包或已验证安全复用。已读源码包含Cube Matmul与Vector阶段；但公开平台表、可靠版本、实际生成ACLNN桥与所装工具链身份没有在此旧发布路径给出。本次未执行构建、安装、真机、数值或性能测试。

## 实际入口与构建范围

```python
torch.ops.attentions.sparse_block_estimate(
    query, key, actual_seq_lengths=None, actual_seq_lengths_kv=None,
    input_layout="BNSD", stride=8, sparse_size=128,
    num_heads=1, num_key_value_heads=1, scale_value=1,
    threshold=1, causal=True, keep_sink=True, keep_recent=True, row_sparse=1
) -> (sparse_mask, sparse_count_table)
```

`register_ops.cpp`注册`TORCH_LIBRARY(attentions)`及PrivateUse1实现；`plugin/sparse_block_estimate.cpp::sparse_block_estimate`以字符串`aclnnSparseBlockEstimate`进入自有`EXEC_NPU_CMD`。后者拼接`GetWorkspaceSize`并动态解析两阶段符号，不能把本树没有的生成header补成已知固定C签名。实际输出张量由Torch wrapper准备；raw OpDef的InferShape与InferDtype函数均只返回GRAPH_SUCCESS，没有在函数内设置输出shape/dtype。

独立旧构建为`csrc/attentions/build/build.sh`→`build_ops.sh`→`build_ascendc_ops.sh`，同时选择laser_attention、ada_block_sparse_attention、sparse_block_estimate，并传入ascend910/ascend910b/ascend910_93；SparseBlockEstimate OpDef本身只AddConfig ascend910b、ascend910_93。这两项是**构建/注册证据**，不提升为本接口公开A2/A3支持。旧脚本寻找环境或系统`latest` CANN，不给可靠固定版本，CMake中8.3与8.5兼容include注释也不是版本支持声明。没有950配置依据。

Host插件CMake构建PTAExtensionOPS，链接Torch/torch_npu/ascendcl/nnopbase/opapi；算子CMake把OpDef、tiling、proto加入对应库，关闭cce-auto-sync。外层工程生成ACLNN源码并安装custom vendor库，plugin复制到另一个`python/attentions/attentions/plugin`发布目录。不能将这个独立旧工程等同于当前SGL默认wheel的实际加载身份。

## 输入输出、属性与真实Host守卫

| 参数 | 源码合同或实际准备 | 边界 |
|---|---|---|
| query/key | OpDef各自允许FP16/BF16 ND | Host分别检查属于两dtype，**不检查彼此相同**；Matmul两侧模板都随query dtype，混合dtype会被按query类型解释 |
| query布局 | wrapper初始化BNSD、BSND、BSH的b/nq/s/d；raw Tiling另接受TND | raw TND不等于Torch包装器可用TND，见失败边界 |
| actual_seq_lengths / kv | Torch optional Host IntArrayRef→aclIntArray；OpDef optional ValueDepend INT64 | raw Host可读常量数据；非TND缺省用shape长度、单值广播或逐batch值；TND必须两个非空累计终点数组 |
| stride | schema默认8，OpDef默认8，Host读int32再放POD u32 | wrapper没有非零/正值校验；后继多处除模，0不是合法安全输入 |
| sparse_size | schema/OpDef默认128，Host读int32 | wrapper只检查不等于0，不能据此推断正值、2次幂或整除stride已校验 |
| num_heads | schema1；Host qHeadNum来自attr | wrapper只检查非零，负值未全面拒绝 |
| num_key_value_heads | schema1；Host kvHeadNum来自attr | 后继Nq/Nkv、索引映射需Nkv正且整除，未见相应完整guard |
| scale_value/threshold | float attr，默认1 | scale在FP32logit上Muls；threshold进入半精度块mass累计选择，未检查有限/合法区间 |
| causal | Torch默认True，OpDef默认false | 必须区分两个入口默认；编译key保留0/1 |
| keep_sink/keep_recent | 默认True/True | 对应setFirstCol/setDiag；实际选择逻辑还有无条件首块行为，不能将flag解释为完整禁用保证 |
| row_sparse | 默认1 | 源注释说0..1有效，实际没有值域检查；非正值可使kk−1索引无效 |
| sparse_mask | Torch分配INT8[B,Nq,Qb,Align32(Qb)]，Qb=ceil(Sq/P) | Device按Kb=Align32(ceil(Sk/P))寻址；Sq/Sk不同造成真实分配/地址合同差异 |
| sparse_count_table | Torch分配INT32[B,Nq,Qb] | 每有效Q块输出mask中选中数；Device SetGlobalBuffer声明了Align8(Qb)长度，实际写地址仍用未对齐Qb跨度，不能把声明长度当caller已额外分配 |
| 两个输出format | empty_with_format继承query NPU format | 不做自动布局转换或完整shape/rank/dtypeguard |

包装器先检查num_heads与sparse_size非零，再根据layout提取维度、分配输出、准备actual数组并调用两阶段API。对其它layout（包括TND）只向cerr打印“不支持BNSD/BSND/BSH以外格式”，**没有return/throw**，随后仍以未初始化的b/nq/s计算输出大小。这是C++静态读前未初始化边界；不能给未初始化值编造确定维度，也不能把raw Host接受TND反推包装器安全支持。

BSND在raw Host按[B,S,N,D]提取维度，但编码到与BSH相同的kernel布局枚举；BNSD按[B,N,S,D]；BSH按[B,S,Nq*D]并用整除推D。原生代码未全面校验rank、Q/K head维一致、GQA整除、实际长度范围/单调性、SQ/SK关系与storage容量；调用方前提不能写成Host保证。

## 可得计算语义与精度顺序

定义s=stride、P=sparseSize、R=P/s（源码整数除法），M=sOuterFactor、N=sInnerFactor。该实现先将连续s个Q token倒序重排并按sD展平，以Matmul得到采样组之间的FP32logit，再softmax、两次块归约与阈值选择。它不是对完整每个Q/K token对逐项计算后再聚合的精确dense attention。

对连续BNSD、或head映射/内存步长与实际读取一致的子域，Q组行的显式搬运为：

```text
A[row,j,d] = Q[q_outer + row*s + (s-j-1), d]   # 超出当前Q尾行补0
B[rowK,j,d] = rawKeyGroup(rowK,j,d)            # 从传入K指针按Matmul实际OrgShape读取
L[row,rowK] = FP32_Cube_accum_j,d A[row,j,d]*B[rowK,j,d]
L = L * FP32(scale_value)
for K inner tile i:
    SoftmaxFlashV2<float,nonFirst> -> FP32局部exp量、running max/sum
    Ehalf_i = CAST_ROUND_half(局部softmax中间量)
    V1_i[row,blockK] = half RowSum over R列
全K完成:
    coeff_i[row] = FP32 exp(max_i[row]-max_final[row]) / running_sum_final[row]
    coeffHalf = CAST_ROUND_half(coeff_i)
    每V1_i乘coeffHalf，再对每R个Q组行做half ColumnSum
    -> 每个P-token Q块到每个P-token K块的half mass
ScoreCompute(mass,threshold,rowSparse,keep*) -> INT8 mask 与INT32 count
```

K的raw矩阵B按实际Matmul参数及pointer解释，BSH/TND存在head交错、sD拼接和GQA地址条件；不能只看函数名就给未经步长推导的任意multi-KV-head数据保证。FP32 Cube内部累加、SoftmaxFlashV2、Sort等通用库实现依赖实际工具链，本卡只记录当前实例参数与可见运算顺序，不跨版本补造内部L1/L0分配。

K尾与因果的源码行为需单列：

- 非因果内循环实际`computeSize=floor(klen/s)`，Matmul tail N同该整数域；虽然最后一片mm1SingleCoreN为可能K尾加1再Align32，代码没有相应有效尾列计算/注入，不能把容量padding当完整K尾参与数学。
- 因果先覆盖当前klen为`qOuterOffset+floor(qOuterLength/s)*s`，再用它决定inner loops，忽略该Q尾块不足s部分对应的K尾；并不依据独立actualKV长度计算通用右下对齐因果。
- Q倒序重排对不足s的Q尾填0；尾行数量由ceil(qOuterLength/s)产生。尾组中的0参与近似group logit，不是原完整token级mask。

### 阈值、强制稀疏率与保留块

ScoreCompute逐Q块按`actColCount`（因果：rowStart/R+localBlock+1；非因果：ceil(klen/P)）处理：

1. 初始化固定stride mask行及half count；因果且有效块≤2时直接选全部，跳过排序/threshold/rowSparse。
2. 其它情况将无效/padding、按flag排除的sink与diagonal候选以**int16位型乘0或1**清理half mass；这不是对FP16数值乘一个重新cast的权重。setDiag或非因果均将最后有效列排除出排序；setFirst排除首列。
3. half RowSum取候选和rs，`Sort<half,true>`及Extract得到降序值/位置。threshold<1时先每16项half和，标量FP32累计定位piece，再逐最多16项找到累计≥threshold*rs的scoreGuard；threshold≥1直接cnt=actColCount、guard0。
4. 若`cnt > actColCount*rowSparse && actColCount>=10`，取`kk=int(actColCount*rowSparse)`，guard改为sortedValue[kk−1]；没有kk≥1等完整检查。rowSparse≤0能进入无效索引域，不能把注释值域当guard。
5. guard减1e−5；按keep_sink将首mass设为guard+1；按keep_recent**或非因果**将最后有效mass设guard+1。随后FP32 `relu(mass−guard)/(relu(mass−guard)+0.001)`→half→CAST_CEIL INT8。
6. 在这个普通分支中，最终ceil之前另有**无条件**`Duplicate(maskHalf,1,1)`，首块因此强制选中，不能承诺keep_sink=False关闭首块保留。非因果最后块同样即使keep_recent=False也被显式保留。
7. count以生成的int8 mask回cast half再half RowSum；MaskCopyOut对重复count做WholeReduceMax、CAST_CEIL int32并DataCopyPad。不是独立精确TopK稳定排序合同。

阈值减epsilon可让同阈值的多项共同入选，所以rowSparse不能仅由k=int(act*rowSparse)推为严格最多k；half舍入、ties、NaN/Inf及Sort稳定性不由本可见源码保证。threshold≥1分支guard=-epsilon的后续比较也可能保留零mass项，不等于按累计覆盖率的最小集合。

## Host分核、Key与POD

### mutable tile producer与Matmul实例

namespace级`SINGLE_CORE_MBASE=128`、`SINGLE_CORE_NBASE=1024`是可变全局，函数中没有每次重置：

```text
while Sk < s * 2 * previousN: N /= 2
N = max(N,512)
tasks = ceil(Nq*Sq / V)
M = min(previousM, floor(ceil(tasks/P)*P/s))
```

V=GetCoreNumAiv；只显式检查V!=0。一次小shape调用降低M/N后可能影响后续大shape，数值和资源必须按当前全局值而非初始128/1024推导；并发Host调用也没有锁。stride/sparse_size0或负值、空shape及整数窄化/乘法溢出并未全面拒绝。

MatmulApiTiling选A GM/ND/query dtype、不转置，B GM/ND/同query dtype、转置，C GM/ND_ALIGN/FP32，无bias；`SetOrgShape(ceil(Sq/s),ceil(Sk/s),D*s)`，`SetShape(M,N,D*s)`，`SetFixSplit(min(M,128),min(N,128),128)`，buffer space(-1,-1,-1)，GetTiling失败返回GRAPH_FAILED；成功后强制TCubeTiling dbL0C=2。Device默认`Matmul<GM-ND-Q_T,false; GM-ND-Q_T,true; GM-ND_ALIGN-float; GM-ND-float-bias>`通过REGIST_MATMUL_OBJ注册当前cubeTilingData，不实例化其它自有Cube算法。kernel entry没有显式KERNEL_TASK_TYPE_DEFAULT；不能仅凭同图有Vector就补造一个确定MIX1:2任务声明。

分核函数`PromptFlashAttentionSplitNSNew`把(Nq,batch,Q outer blocks)线性任务按权重分成最多V段。非因果权重为KV inner loop数，因果为outerIndex+1，target=总权重*Nq/V；超过target且当前任务更靠近下一核时结束本段。临时vector至少max(V,64)，最终写回的六数组**固定64项**。GQA!=1只把useBalanceTiling设false，相关accum数组重置并不代替全部地址/长度校验。实际usedCoreNum=curCore+1，blockDim却为C=GetCoreNumAic，Device又使用GetTaskRation推总workspaces，三者职责不能混同。

TND raw Host对actualQ做相邻累计差，但同一else分支**没有填actualSeqLengthsKV vector**，其resize后的值仍为0并用于Host分核权重；Device仍从传入KV累计Tensor读取真实长度。因此TND Host负载估计和Device长度域不一致，不推定所有输入数值必错；非因果KV cost为0、因果cost又另算，必须分别观察。Torch wrapper的TND本身还先触发未初始化维度边界，不能把后续raw Host推为可安全调用。

### 精确dispatch

令B0=1000000000000000000，l=0(BNSD)、10(BSND/BSH)、20(TND)，d=0(FP16)或100(BF16)，c=0/1(causal)。Host key为`B0+l+d+c`。Device列出的12个key全部对应这三个layout×两dtype×两causal；BSND没有独立枚举，使用BSH body。

| layout selector | FP16 noncausal/causal | BF16 noncausal/causal | 实际实例 |
|---|---|---|---|
| BNSD | B0 / B0+1 | B0+100 / B0+101 | INVOKE_TYPE<BNSD,half或BF16,c> |
| BSND或BSH | B0+10 / B0+11 | B0+110 / B0+111 | INVOKE_TYPE<BSH,half或BF16,c> |
| TND raw Host | B0+20 / B0+21 | B0+120 / B0+121 | INVOKE_TYPE<TND,half或BF16,c>；不等于Torch支持 |

除这12个compile-time分支外entry没有补充fallback body。q/k类型混合时Host仍按qDataType选同一个key，不能把它解释为混合精度实例。

### 逐字段参数流

本POD用TILING_DATA_FIELD宏和TCubeTiling，生成布局随实际构建工具链；固定树没有该生成产物，**不声称sizeof/align/固定offset**。以下保存可见字段类型、producer与consumer，不把字段名注释当真实语义。

| 字段 | 类型/单位 | Host producer | Device consumer与边界 |
|---|---|---|---|
| actualCoreNums | u32/任务核数 | SplitNSNew curCore+1 | Process中AIV无任务核早返；ComputeEachCore数组下标仍需有效 |
| coreNumAic | u32/core | GetCoreNumAic | 记录Cube核数；不等同数组长度或usedCoreNum |
| batchSize | u32/batch | SetDataShape layout或actual长度 | batch循环/actual读取 |
| seqLenQ | u32/token | Query shape | Q地址、Qb、wrapper分配基准 |
| seqLenK | u32/token | Key shape | K地址、Kb与mask实际stride |
| actualSeqLengthsSize | u32/元素 | optional有效data时shapeSize | 0缺省，1广播，TND累计 |
| actualSeqLengthsKVSize | u32/元素 | optionalKV有效data时shapeSize | 同上；Host TND未填KV估计vector |
| headNumQ | u32/head | num_heads attr | loopN、Qoffset/MultiHeadQ |
| headNumKV | u32/head | num_key_value_heads attr | ratio=Nq/Nkv、Khead映射 |
| dim | u32/元素 | layout提取或BSH宽/Nq | Matmul K=sD、reorder与步长 |
| stride | u32/token | int32 stride attr | 除模/倒序组/采样M/N |
| sparseSize | u32/token | int32 sparse_size attr | R=P/s、输出块和mask stride |
| sInnerFactor | u32/采样列 | mutable N | inner tile/UB shape/GMdb |
| sOuterFactor | u32/采样行 | mutable M | Qouter=sM、临时slab/queue |
| scaleFactor | float | scale_value attr | FP32logit Muls |
| threshold | float | threshold attr | ScoreCompute累计gate |
| causal | bool | causal attr | key c、runtime标记；真实分支用模板CAUSAL |
| setFirstCol | bool | keep_sink | 排除sink/guard+1；最终另有无条件首mask1 |
| setDiag | bool | keep_recent | 最后一项排除/保留；非因果另强制 |
| rowSparse | float | row_sparse | cnt cap、kk−1标量索引 |
| sparseBlockEstimateSeqParams | 六数组嵌套 | 下表 | per-core [head,batch,outer)工作段 |
| cubeTilingData | TCubeTiling | MatmulApiTiling+dbL0C2 | REGIST_MATMUL_OBJ/SetOrgShape/IterateAll |
| coreHeadNumTail[64] | u32/head start | coreNidStart | ComputeEachCore nLoopStart，字段名不代表tail head数量 |
| actualS1[64] | u32/head end | coreNidEnd | nLoopEnd，非实际S1长度 |
| actualCoreNums[64] | u32/batch start | coreSidStart | sIdStart，不是外层actualCoreNums scalar |
| singleCoreHeadNumSize[64] | u32/batch end | coreSidEnd | sIdEnd，不是head数量 |
| coreSeqPosStart[64] | u32/Qouter start | coreSposStart | outerLoopStart |
| coreSeqPosEnd[64] | u32/Qouter end | coreSposEnd | outerLoopEnd |

每core Device私有`SPFAEstParam`另存bIdx、batchNOffset、sOuterLoopIdx、sInnerLoopIdx、singleProcessSOuterSize、sOuterOffset、mm1SingleCoreN、actualSeqLengthPerBatch、actualSeqLengthKVPerBatch、sInnerLoopTimes、singleProcessSInnerBmmTail、tensorAOffset/u64、tensorBOffset/u64、gmPingpong。它是4槽软件队列而非Host传入POD；CopyParamsAttrOutOfInnerLoop复制外层上下文及部分内层状态，包括sInnerLoopIdx、mm1SingleCoreN、singleProcessSInnerBmmTail和tensorBOffset；sInnerLoopTimes由内层循环设置，gmPingpong在该函数外单独翻转，不能把私有字段误当Host ABI。CompileInfo的l0A/B/C、l1、ub、maxAic/Aiv、defaultSysWorkspaceSize只是结构声明，TilingPrepare返回SUCCESS并未在此函数填值。

## 任务图、流水和同步

```mermaid
flowchart LR
  H["Torch分配/动态ACLNN/Host POD"] --> R["Q倒序reorder → 两份GM Qtmp"]
  R --> M["Cube Matmul → FP32 GM双buffer"]
  M --> V["Vector FP32 Softmax → half第一归约"]
  V --> G["各inner的half GM结果 + FP32 max历史"]
  G --> S["全inner第二归约 → half块mass"]
  S --> K["Sort/threshold/rowSparse/forced块"]
  K --> O["INT8 mask / INT32 count"]
```

ComputeEachCore按分核数组遍历head/batch/Qouter，SInnerLoopFunc把inner任务推入4槽队列，pending上限2。headParams/tailParams是可更新引用；不能将copy后的旧pointer当下一槽。满队列时消费一个并推进head/tail，末尾逐个drain。

首任务先ReorderQKTail并启动Matmul；若lookahead属于新Qouter则提前reorder其Qtmp（Qouter奇偶选bank）。WaitIterateAll等待当前Cube提交完，再IterateAll启动next GM pingpong，随后将当前GM结果MTE2搬到UB，Vector与下一Cube工作重叠。相邻任务GM输出bank交替；不是同一片边写边无保护读。

- 两个MTE2_V event ID在AllocGlobalResources申请，在FreeGlobalResources释放。Bmm1VecInputCopyIn搬首chunk并set，Res1VecCompute提前搬next chunk到另一40KiB UB bank，wait当前event后计算，以V_MTE2控制覆盖。
- softmax当前/历史max/sum由SoftmaxFlashV2 nonFirst模板选择；FirstReduce的V_MTE3发布、SecondReduce的双MTE2_V与V_MTE2、末尾MTE3_V/MTE3_MTE2保护GM/UB复用。
- scalar读sorted值前有V_S等待，改guard/强制项后S_V等待；最后V_MTE3等待再写mask/count。没有本body自定义CrossCoreSetFlag协议，Matmul内部Cube/Vector服务、L1/L0和硬件task调度保留库边界，不能拿别的attention模式2flags替代。
- Process只对`g_coreType==AIV && blockIdx>=usedCoreNum`早返；其它core类型行为依赖所装Matmul执行模型。entry未显式声明任务比率，GetTaskRation不能仅由通用MIX惯例填成2。

## 分层资源、地址与生命周期

### GM workspace字节账

令C=Host AIC数，V=Host AIV数，Z=Device `GetBlockNum()*GetTaskRation()`，Q_T宽2B。Host：

```text
W = L_libapi + V * [ 16M(N+32) + 4M*s*D ]
```

Device从传入workspace的offset0开始，offset是**u32**，对每个blockIdx独占一份slab：

| 片 | 总extent | 当前block起点/范围 | producer→consumer |
|---|---|---|---|
| BMM FP32 bank0 | Z*4M(N+32) | 0 + blockIdx*4M(N+32) | Cube→Vector |
| BMM FP32 bank1 | 同上 | 前一总片末+同block偏移 | Cube→Vector双buffer |
| Qtmp bank0 | Z*2M*sD | 前两总片末+blockIdx*2M*sD | Vector reorder→Cube |
| Qtmp bank1 | 同上 | 前片末+同block偏移 | 同上，Qouter奇偶 |
| firstReduce GM | Z*4MN | 前四总片末+blockIdx*4MN | 非末inner的half归约→末inner SecondReduce |

总声明片为`Z*[12MN+256M+4M*sD]`。当且仅当实际Z=V时，可与Host公式直接比较得到保留量`V*(4MN+256M)+L`；本Reference没有把未声明task ratio当成已证等式，也没有擅自从Device每片再跳过L。Host W与实际library system workspace owner/偏移需匹配实际生成bridge，不能仅按两个公式都“够大”宣布安全。u32 offset推进、规模乘法与真实storage容量均需不溢出。

BNSD的Q源元素offset为`(b*Nq+head)*Sq*D+qOuter*sM*D`，K为`(b*Nkv+head/(Nq/Nkv))*Sk*D+inner*N*s*D`。BSH按token交错head，以`b*Sq*Nq*D+qOuter*sM*Nq*D+head*D`起Q；K按对应KV-head起点，TND把batch起点替换成前一累计终点*N*D。Qtmp每行按j从0到s−1写`qtmp[j*D+loopM*D]`，从当前UB的`(s−j−1)*D`读取、源/目的重复步长均为(s−1)*D*2/32个block。这些真实地址而非“支持某layout”标签决定raw实例可用域。

### UB固定片与阶段高水位

所有TBuf均从同一TPipe顺序申请，无TQue。数值是源码请求容量，非运行测量：

| UB片 | 容量B | lifetime/使用 |
|---|---:|---|
| mmResBuff | 81920（80KiB） | 两个40KiB bank；FP32 softmax输入与half压缩结果、SecondReduce目标复用 |
| firstReduceBuff | 20480（20KiB） | half当前inner的每行块归约 |
| tmpBuff1 | 49152（48KiB） | Softmax scratch→归约scalar/broadcast→Sort/阈值scratch |
| maskBuff | 8192 | 每Q块固定MAX_QK_LEN/P字节stride；reorder阶段亦声明keyUb view但未使用 |
| QKTailBuff | 1024 | 两bank的half view，当前没有实际K尾注入计算 |
| countBuff | 1024 | half重复计数，末尾reinterpret int32输出 |
| softmaxMaxBuff | 4096 | FP32 running max，32B广播行 |
| softmaxExpBuff | 4096 | FP32 exp correction |
| softmaxSumBuff | 4096 | FP32 running sum |
| maxLocalBuff | 8192 | 各inner的每采样Q行max历史 |
| 合计 | 182272（178KiB） | 不是所有硬件均已证明有此可用UB |

源码注释让前三块同时作为Qtmp大slab，三块合计148KiB；Reorder从mmResBuff的Q_T view搬入，单循环Mcopy=`4*32KiB/(2D)`，名义128KiB，再可能补(s−tail)*D*2字节。该view跨过单个80KiB TBuf声明范围而依赖后两块相邻/phase互斥；记录这一可见设计，不把单TBuf越界视图默默扩大为安全API保证。实际连续分配、SDK范围检查、补零总span与148KiB容量都要满足。

令r=当前采样Q行数、R=P/s、I=inner loop数、U=Align32(actColCount)。逐阶段必要范围：

```text
softmaxChunk = 8*floor(8192/(8*min(mm1SingleCoreN,N)))
每FP32 UB bank需 4*chunkRows*mm1SingleCoreN <=40960
firstReduce需 2*r*(N/R+16) <=20480
max历史需 4*M*I <=8192
SecondReduce目标需 2*ceil(r/R)*(N/R*I+16) <=40960
mask需 ceil(r/R)*(131072/P) <=8192
Sort最高显式view末址为42*U，需 <=49152
count重复half需 32*ceil(r/R) <=1024
```

Sort的实际typed offset值得保留：sortedLocal在tmp0，indexLocal在8U字节；`dstIndexLocal=indexLocal[sizeof(int32_t)*U]`是u32元素索引，额外**16U字节**；sortedValueLocal再经同样u32索引到40U字节，half U元素结束于42U。不能将这两个sizeof乘法误简化为4U字节；Sort primitive还可能需要其它内部临时条件，本式只计源码可见view高水位。默认P128、s8、M128、N1024、Sk≤128Ki时这些设计常量相互关联，但Host没有完整强制这组上界；此前调用把N降到512后，大Sk令I增多还可能突破max历史条件。不是所有允许输入都已证明满足资源式。

mask写出以Kb为每行GM宽、每个local mask行固定1024B（当P128）stride；MaskCopyOut的DataCopy源stride写为`32−Kb/32`（32B单位）。Kb>1024时可发生负差转u16，不能当自动长KV支持。半精度ColumnSum二分归约依赖R、行数及2次幂分解的真实条件，Host没有把这些条件全部筛掉。

## 适用边界与复用方式

- 首先区分Torch wrapper可达域和raw Host/Device静态selector。TND wrapper的未初始化变量、Query/Key不同dtype、Qb与Kb容量差异不能以输出schema或12key存在掩盖。
- s、P、Nq、Nkv、D、seq长度、实际数组与所有tile/资源公式必须合法；尤其除0、R=0、固定64核数组、非法rowSparse索引、空输入、全局M/N调用历史没有完整Host防护。源可见不表示已验证正确。
- mask不是严格TopK位置列表，也不是一般attention结果；两次half归约、阈值epsilon、无条件首mask、非因果尾mask与causal小列快路均属于当前实现语义。
- 与[AdaBlockSparseAttention接口](sgl_ada_block_sparse_attention.md)组合时仍须核mask/count布局、P、长度、head、dtype及stream完成，不能因名字相近而宣称两者已被此批数值组合验证。
- 与[LightningIndexer候选接口](sgl_lightning_indexer_v2_candidates.md)的按head ReLU加权位置TopK不同，不复用其candidate/metadata格式。
- 本卡不提供CANN版本/硬件支持承诺；generated ACLNN、Matmul/Softmax/Sort与普通SDK原语保持所装包边界。没有把平台未知当“无技术知识”，也没有把Reference记成完整Operator。

## 共同库解析与异步所有权

`pytorch_npu_helper.h`按符号缓存GetWorkspaceSize与execute；`find_op_path.cpp`先取ASCEND_CUSTOM_OPP_PATH各项加/op_api/lib解析libcust_opapi.so，再按ASCEND_OPP_PATH/vendors/config.ini的load_priority解析默认vendor库，最后libopapi.so。选择的是环境/安装文件，不校验其Git commit或是否就是本源码build产物。

普通Tensor转换记录sizes/strides/storage_offset、底层storage基址；storageDims仅用总storage元素数一维，rank3/4/5设置NCL/NCHW/NCDHW format。actual Host数组转换成aclIntArray，undefined optional转换nullptr；未自动对所有输入做contiguous、同设备或dtype一致检查。wrapped-number scalar辅助会pin/copy到device0，但不是本普通Q/K Tensor路径。

执行顺序为ValidateApiAddresses→可选InitHugeMem→workspaceSize0/executor=null→ConvertTypes/query→AllocateWorkspace byteTensor→当前NPU stream→OpCommand自定义callback execute→ReleaseConvertTypes→ReleaseHugeMem→Run后UnInitHugeMem。workspace分配使用当前NPU设备，未设基于query的DeviceGuard；caller应保持当前设备/stream与输入storage一致。

callback捕获ACL描述符tuple和raw workspace地址等，不捕获workspaceTensor/输入输出Tensor、未record_stream；executor/queue/allocator的存活由框架合同承担。query失败的TORCH_CHECK在返回convertedParams之前，execute失败检查也位于ReleaseConvertTypes之前，不能承诺失败路径已全部释放。原始来源不包含对应框架的全生命周期实现，不能由lambda静态观察断言必然UAF；也不能承诺自动保留了所有storage。调用方须维持数据、输出、workspace与流完成关系。

## 固定源码索引

| 文件 | 支撑内容 |
|---|---|
| [csrc/attentions/csrc/plugin/sparse_block_estimate.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/sparse_block_estimate.h) | 接口/schema/注册/输出/失败合同 |
| [csrc/attentions/csrc/plugin/register_ops.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp) | 接口/schema/注册/输出/失败合同 |
| [csrc/attentions/csrc/plugin/sparse_block_estimate.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/sparse_block_estimate.cpp) | 接口/schema/注册/输出/失败合同 |
| [csrc/attentions/csrc/plugin/pytorch_npu_helper.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pytorch_npu_helper.h) | 动态库解析/描述符/异步所有权 |
| [csrc/attentions/csrc/plugin/find_op_path.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.h) | 动态库解析/描述符/异步所有权 |
| [csrc/attentions/csrc/plugin/find_op_path.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.cpp) | 动态库解析/描述符/异步所有权 |
| [csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_def.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_def.cpp) | 接口/schema/注册/输出/失败合同 |
| [csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_proto.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_proto.cpp) | 接口/schema/注册/输出/失败合同 |
| [csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_tiling.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_tiling.cpp) | Host分核/POD/参数 producer |
| [csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_tiling.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/sparse_block_estimate_tiling.h) | Host分核/POD/参数 producer |
| [csrc/attentions/csrc/ops/sparse_block_estimate/op_host/CMakeLists.txt](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_host/CMakeLists.txt) | 旧独立构建/生成桥边界 |
| [csrc/attentions/csrc/ops/sparse_block_estimate/op_kernel/sparse_block_estimate.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_kernel/sparse_block_estimate.cpp) | 自有Device入口/完整body与搬运/资源 |
| [csrc/attentions/csrc/ops/sparse_block_estimate/op_kernel/sparse_block_estimate.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/sparse_block_estimate/op_kernel/sparse_block_estimate.h) | 自有Device入口/完整body与搬运/资源 |
| [csrc/attentions/csrc/CMakeLists.txt](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/CMakeLists.txt) | 旧独立构建/生成桥边界 |
| [csrc/attentions/csrc/ops/CMakeLists.txt](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/ops/CMakeLists.txt) | 旧独立构建/生成桥边界 |
| [csrc/attentions/build/build.sh](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build.sh) | 旧独立构建/生成桥边界 |
| [csrc/attentions/build/build_ops.sh](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ops.sh) | 旧独立构建/生成桥边界 |
| [csrc/attentions/build/build_ascendc_ops.sh](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ascendc_ops.sh) | 旧独立构建/生成桥边界 |
| [csrc/attentions/build/build_plugin.sh](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_plugin.sh) | 旧独立构建/生成桥边界 |
