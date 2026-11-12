---
type: API
title: SGLang非量化共享KV滑窗接口
description: 说明共享KV滑窗合同、旧Direct缓存与owner边界，以及非量化CPU metadata的成本分核、1024项ABI和异步生命周期。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/sparse_attn_sharedkv.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_tiling.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_tiling.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_def.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_tiling.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attn_sharedkv/op_host/sparse_attn_sharedkv_tiling.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/ge_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_attn_sharedkv/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attn_sharedkv_metadata/op_host/sparse_attn_sharedkv_metadata.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attn_sharedkv_metadata/op_host/sparse_attn_sharedkv_metadata.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparse_attn_sharedkv_metadata/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_attn_sharedkv/op_kernel/sparse_attn_sharedkv_metadata.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_sparse_attn_sharedkv_metadata_host.py
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T18:03:28Z'
platforms:
- a2
- a3
---

# SGLang非量化共享KV滑窗接口

## 接口原型

```python
from sgl_kernel_npu.operators.attention import sparse_attn_sharedkv

def sparse_attn_sharedkv(
    q,
    *,
    ori_kv=None,
    cmp_kv=None,
    ori_sparse_indices=None,
    cmp_sparse_indices=None,
    ori_block_table=None,
    cmp_block_table=None,
    cu_seqlens_q=None,
    cu_seqlens_ori_kv=None,
    cu_seqlens_cmp_kv=None,
    seqused_q=None,
    seqused_kv=None,
    sinks=None,
    metadata=None,
    softmax_scale=0.0,
    cmp_ratio=0,
    ori_mask_mode=4,
    cmp_mask_mode=3,
    ori_win_left=128,
    ori_win_right=0,
    layout_q="BSND",
    layout_kv="PA_ND",
    return_softmax_lse=False,
    impl="auto",
):
    ...
```

## 当前可消费的子集

`sparse_attn_sharedkv` 的原生Ascend C仅arch22，auto直接选择原生。当前覆盖共享K/V的滑动窗口与分页PA_ND：按页表恢复逻辑KV，对每个query以 `aligned=KV_length-query_length+s` 右对齐，取 `[max(aligned-left,0), min(aligned+right,KV_length-1)]`，做softmax加权；FP32 sinks `[N1]` 是额外零value的标量logit。

Q为FP16/BF16 BSND `[B,S1,N1,D]` 或TND `[T,N1,D]`，原生要求N1=64、N2=1，Q 与共享 KV 的 D 固定为512；共享KV为 `[blocks,blockSize,1,D]` 与Q同dtype。ori_kv、sinks、int32 metadata `[1024]`、int32页表 `[B,maxBlocks]` 和seqused_kv `[B]` 都实际必需。TND需 `[B+1]` query累计边界，BSND禁止该字段。所有tensor同NPU。原生 PA_ND 原始 KV 的 blockSize 必须为16至1024之间的16倍数。这些 D/页大小约束来自原生 Host，不由 torch_native 的数学参考范围替代；参考能计算其他形状也不证明原生可调用。

layout_kv只支持PA_ND，ori_mask_mode只支持4，默认窗口128/0，softmax_scale默认0.0，必须核对调用方是否显式提供所需缩放。接口虽然保留cmp_kv、稀疏索引、cmp_ratio等参数，torch_native仅实现SWA+PA_ND，不是所有压缩模板的golden。

返回 `(attn_out,softmax_lse)`；前者同Q shape/dtype，后者FP32 `[0]`。return_softmax_lse=True不支持。输入不修改。metadata必须与主接口任务划分匹配；本卡不把1024项形状等同于其他量化共享KV调度表的兼容承诺。

复核时选单KV头/64Q头，核对分页映射、query末端对齐、sink分母和窗口边缘。需要压缩KV或其他mask模式时重新检查固定实现，不以参数默认值推导能力。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [SWA/CSA/HCA与配套调度的独立接口](sgl_sparse_flash_mla_and_metadata.md)

## 同名旧Direct Host与新raw ACLNN接入

当前数学、输出和主要shape约束可复用[新raw ACLNN完整实现](../../operators/aclnn/transformer/attention/sgl_sparse_attn_sharedkv.md)，不再建一张重复数学Operator。但同一 `torch.ops.npu.sparse_attn_sharedkv` schema在旧root Torch构建与新CANN adapter构建中绑定不同Host，旧路径的准备和生命周期不能由新pair代替。

| 层级 | 旧Direct路径 | 新raw ACLNN路径 |
| --- | --- | --- |
| 注册/构建 | pytorch_extensions.cpp的npu/PrivateUse1→sglang::npu_kernel::sparse_attn_sharedkv；legacy_kernels.cmake在SGL_KERNEL_ENABLE_A3_ONLY_OPS下编译旧Host/tiling和sparse_attn_sharedkv_kernel | attention/sparse_attn_sharedkv/torch_adapter.cpp→aclnnSglSparseAttnSharedkvGetWorkspaceSize/aclnnSglSparseAttnSharedkv |
| 参数准备 | SASHost::SparseAttnSharedkv→自有ge_helper::TilingContext，按14输入、2输出顺序RegisterTensor；SASInfoParser→SASTilingCheck→DoOpTiling | ACL tensor描述符→CANN query callback，平台来自框架context |
| 属性位宽 | softmax_scale由double转float；ratio/mask/stride/window先检查u32范围再SetAttrAny<uint32_t>，旧parser亦取uint32_t | 框架整数attr为int64，不能直接借用旧std::any<uint32_t>布局 |
| 输出 | attention_out=empty_like(q)，LSE直接empty([0],FP32) | 同逻辑shape，但LSE采用1元素storage的零长view，保证ACL descriptor有底层指针 |
| optional launch | 缺失cmpKV用新分配的q同dtype[1] Tensor；各缺失整数字段用共用INT32[1] Tensor；这些placeholder并非零初始化或nullptr | 缺失optional用null ACL descriptor；defined的零元素Tensor仍视为present |
| workspace/blockDim | context.SetWorkspaceSizes把libAPI与用户区相加，分配Byte workspace；blockDim直接取旧tiling.GetBlockDim，ACLRT_LAUNCH_KERNEL(sparse_attn_sharedkv) | query返回workspace/executor；CANN启动generated kernel节点 |
| owner/stream | 共用EXEC_KERNEL_CMD仅捕获转换后的data_ptr tuple与当前stream，没有在本宏捕获输入/输出/workspace Tensor owners或record_stream | adapter显式DeviceGuard、record_stream，并捕获tensor/descriptor/layout字符串/workspace/executor |

两条路径schema默认仍为scale0、cmp_ratio0、mask4/3、window128/0、BSND/PA_ND与LSEfalse，旧wrapper会逐项SetAttr覆盖SASHost定义中的scale1、ratio1、left127等占位默认；不能因只读OpDef就改写有效调用默认值。旧required/optional的判断用has_value，未统一加入defined检查；空但defined的Tensor不会像SwiGLU量化那样视作None。旧入口实际拒绝缺oriKV、sink、metadata、PA页表/usedKV、非法layout/rank及LSEtrue，检查FP16/BF16、NPU、连续、64Q头、metadata INT32 numel1024和可选INT32数组；TND/BSND对cuQ存在性的要求保持前文合同。

旧RegisterTensor建立的gert::Tensor只供shape/dtype/存在性Tiling使用，不将输入tensor数值内容复制进context；CreateStorageShape只支持rank<=4。optional缺省先在context登记null，之后launch用占位地址，不能据非空GM指针推断该输入在语义上存在。metadata是caller提供的1024项Tensor，wrapper本身没有隐式创建/启动metadata producer。

### 旧ge_helper的Tiling缓存与capture边界

GetTilingTensor走TilingTensorCache<T>：按当前NPU stream的device.index分仓、mutex保护，用完整sizeof(T)序列化字节（含padding）作key；每device最多512个稳定slot。专用cache buffer经aclrtMalloc(HUGE_FIRST)分配、带aclrtFree deleter的from_blob包裹，不是下述KV/Swi旧wrapper的1024项hash-only ATen slab。首次初始化以及新key均要求在capture之外eager warmup；capture只允许命中现有slot。未命中且cache已满时，capture抛错，eager使用该device持有的一块overflow slab并重写内容，不自动扩容为新的稳定graph slot。

上传把Host POD经当前stream的aclrtMemcpyAsync写入GM后调用aclrtSynchronizeStream，以使栈上的源POD在返回前完成上传；memcpy状态有TORCH_CHECK，sync返回值在此处未检查。key依赖POD及padding确定性；mutex保护cache管理不等于保证多个stream对overflow slab的后续Kernel消费彼此隔离。这里记录固定实现与条件，不把源码注释当本次graph或多stream实测。

TorchNpuHelper将Tensor仅转换为data_ptr，EXEC_KERNEL_CMD取当前NPU stream、用OpCommand::RunOpApi运行ACLRT_LAUNCH_KERNEL；lambda未检查launch返回值并固定返回0，没有独立DeviceGuard或自动contiguous。调用方须保持当前设备与Tensor、tiling缓存及stream一致；本段不补造异步完成或allocator生命周期保证，也不把新adapter的owner保护反向移植到旧宏。

这次增量只保存旧Direct wrapper的ABI/准备/缓存事实，复用已有数学卡；未声称旧wrapper整体source_closed，未执行上游、构建、capture、真机、数值或性能测试，无新增verified。

## 旧版纯 Host 元数据生成器（非量化 Reference）

`torch.ops.npu.sparse_attn_sharedkv_metadata_host` 是旧版独立 CPU 调度助手，注册在 `TORCH_LIBRARY_IMPL(npu, CPU, m)`；它不是主注意力内部自动启动的 Device 节点，也不是量化 `kv_quant_sparse_attn_sharedkv_metadata_host`。本节记录固定源码可见的 CPU 算法与 ABI，不扩展主接口的公开平台、布局或压缩功能承诺。源码对 SoC 名含 `ascend950` 的分支也有块大小选择，但这不能证明本卡的非量化注意力公开支持 950。

```python
torch.ops.npu.sparse_attn_sharedkv_metadata_host(
    num_heads_q, num_heads_kv, head_dim, layout_q, layout_kv,
    cu_seqlens_q=None, seqused_kv=None, batch_size=0,
    cmp_topk=0, cmp_ratio=-1, ori_mask_mode=4, cmp_mask_mode=3,
    ori_win_left=127, ori_win_right=0, has_ori_kv=True, has_cmp_kv=True,
)  # 返回 NPU int32[1024]
```

### 输入、检查与实际有效域

两个可选长度张量只在提供时检查 CPU 和 int32，随后直接以连续的 `int32_t*` 索引；wrapper 未检查 rank、numel、stride、累计长度单调性或非负值。实际使用 TND 时，调用方应提供连续 `cu_seqlens_q[B+1]` 和 `seqused_kv[B]`，并保证长度、batch 与后续注意力完全相同。形状属性由 int64 未经范围检查地窄化为 int32；不应把 schema 能表达的任意整数当成安全输入。这里只有 CPU dispatch 实现，两个 Tensor 均缺省时也不能据 schema 推断一定能选中这个实现。

`Run` 拒绝零 AIC/AIV 核数、空输出地址及 `num_heads_kv != 1`。当 `has_cmp_kv=True` 时还要求 `cmp_topk∈{0,512,1024}`、`cmp_ratio∈{4,128}`；关闭压缩 KV 时不做这两项检查。源码未全面校验 head 数为正、layout 枚举、mask 枚举或拓扑容量。`head_dim`、`layout_kv`、`cmp_mask_mode`、`has_ori_kv` 被保存但不改变这份调度计算，不能以这些属性通过调用推导主 Kernel 支持对应功能。

最重要的布局边界是 `GetS1SeqSize` **仅在 layout_q=="TND" 且 cuQ 非空时**返回 `cuQ[b+1]-cuQ[b]`；BSND/BSH 及其余字符串均返回 0，尽管 `isS1G_` 将 BSND/BSH/TND 都归入 S1G 排列。KV 长度只取 `seqused_kv[b]`，缺省即为 0。因此不能把这个旧助手当成能从 BSND tensor shape 自动恢复 Q 长度的通用 producer；全零长度退化输出也不等于为非空 BSND 生成了有效工作表。主接口默认窗口是 128/0，本助手默认是 **127/0**，调用方必须显式统一窗口，不能因名称相近直接混用默认值。

### 分块、窗口和压缩成本

令 `G=num_heads_q/num_heads_kv`，每 batch 的 `S1=cuQ[b+1]-cuQ[b]`、`S2=seqused_kv[b]`。SoC 名转小写后含 `ascend950` 时取 `Mbase=64,Nbase=128`；其余名字（包括未知/空名字）归入 910 分支，取 `Mbase=G,Nbase=512`。M 块数为 `ceil(S1*G/Mbase)`，S2 块数为 `ceil(S2/Nbase)`，两方向分别记录模数尾块。调用方还须保证这些乘加、转换和除法处在所用整数的有效域，尤其 G=0 不会被 wrapper 提前拒绝。

mask 0 直接使用全 KV 范围；mask 3 以 `next=S2-S1` 实现右下因果对齐；其余值在初始化时进入窗口分支，只有实际 mask 4 在后续左右上角变换中应用 `pre=S1-S2+left`、`next=S2-S1+right`。负窗口先替换为 INT64_MAX，源码没有用饱和加法保护后续有符号计算。对于每个 M 块，按 S1G 展平位置除 G 恢复首尾 query token，计算候选 `[s1_first-pre,s1_last+next]`，裁剪至 `[0,S2-1]`；不相交时窗口块数为零。窗口内部 S2 任务重新从 0 编号，记录实际窗口宽度对应的完整块和尾块。

压缩任务接在窗口块序列后。`has_cmp_kv && cmp_topk==0` 选择 CFA；`cmp_topk>0` 选择 SCFA。可见压缩 token 数先取 `floor((ori_last+1)/cmp_ratio)`，SCFA 再与 topK 取 min，按同一 Nbase 分块；这只是调度的可见长度成本，不读取实际压缩索引、页表或 KV 内容，也不替代主 Kernel 的来源支持范围。

窗口和压缩块采用同一整数代价 `6*ceil(m/16)+10*ceil(n/64)`。分别建立正常 M/尾 M × 正常 S2/尾 S2 的成本表；无尾时对应尾成本记零，按窗口与压缩实际块数相加得到每 M 行、每 batch 和全局成本。成本是调度启发式，不是实测延迟。

### 行缓存、贪心分核与 FD 边界

每 batch 缓存 `M块数+1` 行，额外一行是边界 phantom；先构造 batch 缓存和 slot→batch 映射，再一次性计算各行的窗口/压缩区间与成本。总行数小于4096时串行；达到4096时线程数为 `min(16,max(1,floor(total/512)))`，仅在编译有 `_OPENMP` 时使用静态 OpenMP 并行，各迭代独占成本 scratch 和输出行。后续规划直接读取稳定的行缓存引用；它不是跨调用的 tensor 内容缓存。旧构建将这个普通 C++ 文件并入 `libsgl_kernel_npu.so`，并链接 `-fopenmp/gomp`，无需为该助手生成 AICPU Kernel。

非空计划按 batch→M 行→S2 顺序分配连续任务。每个 Cube 核的成本上限为 `max(剩余总成本/剩余核数,最大单M行成本)`；优先整体吃入 batch，再整体吃入 M 行，允许上限加当前末块成本的一半作为容差。把每核的 BN2/M/S2 结束游标保存下来，下一核从前一结束点开始。没有可见工作的全零退化分支仍启用一个 FA 核，将结束 BN2 置为 B、M/S2 置零。

`supportFd_` 成员初值固定 false，完整 body 中没有将其开启的赋值；因此按 S2 单块分配和强制拆块路径被跳过，正常受约束调用按完整 M 行分配，FD 区保持未启用。源码虽保留 RecordFDInfo/SplitFD/FD 字段生成，不能把这些保留代码当成当前启用的跨核 split-KV 归约。与本卡对应的非量化注意力实例 `FLASH_DECODE=false` 的边界一致：不应自行改写表使同一行多核分片后期待隐式归约。

### 4096 字节输出 ABI 与生命周期

返回表以 pinned CPU `zeros([1024],int32)` 初始化，总4096B。固定消费头文件与 producer 的 FA/FD stride 相同：

| 区域 | int32 偏移与容量 | 每条记录 |
|---|---|---|
| FA | `8*c`，c=0..35；共288项/1152B | enable、BN2_start、M_start、S2_start、BN2_end、M_end、S2_end、first_fd_workspace_idx |
| FD | `288+8*v`，v=0..71；共576项/2304B | enable、BN2_idx、M_idx、workspace_idx、workspace_num、M_start、M_num、第8项保留 |
| 剩余 | 864..1023；160项/640B | 保持零初始化 |

BN2 在当前 KV 单头约束下就是 batch；M/S2 为块坐标，结束游标用于相邻核连续分区。只对实际查询到的核数写记录，未使用核 enable=0，其余零来自初始分配。固定容量36/72不是自动扩容：Host 仅检查查询核数大于0，没有检查不超过36/72，调用方环境必须满足容量；超出会访问固定数组边界，不能以1024总长度掩盖这个子数组限制。非量化8-word FA ABI不同于量化 SharedKV 的9-word FA/maxS2协议，也不同于 SparseFlashMLA 的2048项 metadata。

拓扑由函数静态 `ResolveHostTopology` 首次调用缓存：读取当前 device，失败回退device0，再查 AIC/AIV 数与 SoC 名；后续切换 device 不会按设备重查。结果拷贝目标却是调用时的 `at::Device("npu")`，因此多设备调用必须保证缓存拓扑与目标设备相容，不能假设已做 per-device 缓存。

CPU 规划完成后仅调用 `metaDataHost.to(at::Device("npu"),non_blocking=true)` 返回设备 tensor，不启动注意力 Device 数学。固定 README 将 pinned 拷贝说明为当前流异步 H2D：同流后续消费者依流序读取，跨流读取需事件或等价依赖；pinned staging 的复用依赖 torch_npu/caching host allocator 对异步拷贝的生命周期管理。本自有 shim 没有额外实现完成回调，也没有在返回前显式同步；本次未提取或验证外部 allocator 实现，不能把 README 的验证声明写成本次完成的运行结果。

固定专属测试定义了输出 shape/dtype/device、FA连续前缀与最终 batch 覆盖、FD禁用、非法压缩参数及可选 live AICPU decode 比较。它们是可复核方法，未在本次执行；README 中“byte-identical”和性能数据是上游陈述，不扩大为所有布局或所有外部 AICPU 版本的保证。


配套阅读：[非量化完整注意力实现](../../operators/aclnn/transformer/attention/sgl_sparse_attn_sharedkv.md)、[ABI不同的量化CPU metadata](sgl_kv_quant_sharedkv_metadata.md)、[2048项SparseFlashMLA metadata](sgl_sparse_flash_mla_and_metadata.md)。
