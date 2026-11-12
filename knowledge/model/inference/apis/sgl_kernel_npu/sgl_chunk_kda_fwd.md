---
type: API
title: SGLang chunk_kda_fwd 的门控、布局与十一项输出
description: 说明 KDA 融合prefill的逐通道门控、packed边界、K/V状态顺序和固定11项返回值，避免与GDN标量门控混用。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/kda/chunk_kda_fwd.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk_kda_fwd.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_kda_fwd/op_host/chunk_kda_fwd.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_kda_fwd/op_host/arch35/chunk_kda_fwd_tiling_impl.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_kda_fwd/op_kernel/chunk_kda_fwd.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_kda_fwd/op_kernel/chunk_kda_fwd_tiling_data.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_kda_fwd/op_kernel/catlass/kda_catlass.hpp
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/chunk_kda_fwd/op_kernel/chunk_kda_fwd.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/chunk_kda_fwd/op_kernel/chunk_kda_fwd_tiling_data.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: header
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
---

# SGLang chunk_kda_fwd 的门控、布局与十一项输出

## 接口原型

```python
from sgl_kernel_npu.operators.attention.kda import chunk_kda_fwd

def chunk_kda_fwd(
    q, k, v, g, beta, *,
    a_log=None, dt_bias=None, initial_state=None,
    cu_seqlens=None, chunk_indices=None,
    layout="BSND", scale=1.0, chunk_size=64,
    safe_gate=False, lower_bound=-5.0, use_gate_in_kernel=False,
    state_v_first=False, output_final_state=True,
    output_gk=False, output_w=False, output_u=False,
    output_qg=False, output_kg=False, output_v_new=False, output_h=False,
    impl="auto",
):
    ...
```

## 计算与形状

`chunk_kda_fwd` 执行逐通道衰减的Kimi Delta Attention融合prefill：块内累计门控、因果系数与delta变换、跨块状态更新、输出重建。Q/K/V为BF16；Q/K有H头、V有HV头，HV须为H整数倍，二者<=128。K/V维在16..256内且16对齐，块宽C=64或128，T>0。

输入布局可为BSND `[B,T,H,K]`、BNSD `[B,H,T,K]`、TND `[T,H,K]` 或NTD `[H,T,K]`；V相应换为HV/V。g为与V同布局但末维K的FP32/BF16逐通道gate，beta为去掉末维后的FP32/BF16已激活系数，算子不对beta做sigmoid。默认scale=1.0，并非自动K^-0.5。

`use_gate_in_kernel=False` 时g已经是对数衰减；为True时必须给FP32 `a_log[HV]`，可给 `dt_bias[HV*K]`，默认用 `-exp(a_log)*softplus(g+dt_bias)`。safe_gate分支改用 `lower_bound*sigmoid(...)`，两开关都开时lower_bound须在[-5,0)。初始状态默认零，FP32 `[N,HV,K,V]`；state_v_first=True时交换为V,K，最终及chunk状态也相应交换。

packed用int64 `[N+1]` cu_seqlens，从0到T非递减，N<=1024且B=1。可选int64 chunk_indices为按序列/块顺序的 `[total_chunks,2]`，仅在提供边界时有效；缺省自动推导。

## 固定返回协议

返回长度始终为11：0为BF16 attention输出、1为可选FP32最终状态、2为可选FP32累计log2 gate、3/4为始终返回的BF16 aqk/akk系数、5/6为可选w/u、7/8为qg/kg、9为v_new、10为各块进入状态h。未请求项保持None，不能通过过滤None重解释位置。

attention输出始终序列优先，即四维 `[B,T,HV,V]` 或三维 `[T,HV,V]`，不会照搬BNSD/NTD输入顺序；中间gk/w/qg/kg为head优先，h是每块进入状态，不是最终状态。输入不原地修改。Ascend C覆盖arch22/35；torch_native以FP32计算并保留BF16中间边界。验证应逐位置检查输出开关、packed尾块、state_v_first以及gate激活方式，避免仅比较输出0而漏掉状态契约。

## 旧 fla 直接启动入口的接入差异

固定树另有 `sgl_kernel_npu.fla.chunk_kda_fwd.chunk_kda_fwd`。其 Python 函数直接向 `torch.ops.npu.chunk_kda_fwd` 转发 25 个参数，没有 `impl`、Python 形状校验或布局转换；C++ Host 才分配输出、准备元数据并通过 `EXEC_KERNEL_CMD` 启动。它仍保持十一项位置及未请求项的 None。以下是旧入口的源码参考，不为该入口另行扩张公共平台支持，也不将其整条 Torch 启动链声明为源码闭包。

旧 `csrc/chunk_kda_fwd` 和新 `csrc/attention/chunk_kda_fwd` 的对应实际计算 helper、arch22/arch35、prepare、PostWU、FwdH、finalize、varlen 与布局文件相同；独立数学实现见 [A2/A3 KDA 源码卡](../../operators/aclnn/transformer/attention/sgl_chunk_kda_fwd.md) 与 [950 KDA 源码卡](../../operators/aclnn/transformer/attention/sgl_chunk_kda_fwd_950.md)。Host 启动协议仍不同，不能用共享 Device 计算替代以下接入差异。对应 entry 的差异集中在调度属性；POD 的字段类型、次序和 pack 一致，但 namespace/comment 不同；旧 CATLASS 包装另在 `__CCE__ && L2_CACHE_HINT && CATLASS_BUILD_LEGACY` 下定义 `g_opSystemRunCfg`，其中 L2_OFFSET 为 0。由此不能称两个完整编译产物逐字节相同。

### Host 顺序、布局与校验边界

旧 Host 要求 Q/K/V 为 BF16、g/beta 为 FP32 或 BF16；可选 a_log、dt_bias、initial_state 为 FP32，内核门控要求 a_log。四种布局、Q/K 相等、Q/V/g/beta 的对应轴、H/HV 整除及上限、K/V 的 16 对齐范围、正 S/块数和 C=64/128 均有检查。初始状态检查 `[N,HV,K,V]` 或 V-first 的相反末两轴。仅两种 gate 开关同时为 True 才检查 lower_bound∈[-5,0)。这些检查不涵盖所有输入设备一致性、a_log/dt_bias 元素容量、数值有限性或全部整型溢出前提。

`ResolveShapeInfo` 先调用 `CountChunks`，后检查 cu_seqlens 的 dtype 和内容：前者已把边界 contiguous 后复制到 CPU 并按 int64 解释，后者再读回 CPU 检查 int64、首 0、末 S、非递减、N≤1024。故不能承诺无效 dtype 在读取前总能被拒绝，也不能把一次 Device kernel 启动解释为无 Host 同步或自动可捕获。packed 的公共 B=1 合同保持不变；旧实现中写着 rank4 B=1 错误信息的条件是 `!isRank3 || info.batch == 1`，实际并未拒绝 rank4 B>1。chunk_indices 只检查提供 cu、int64 和 `numel==2*totalChunks`，未核对 rank、内容或每个 `(seq,chunk)` 的合法顺序；旧 Python 注释的一维 `2*NC` 不产生另一种已保证的索引排序。

BSND 的 Q/K/V/g contiguous 成序列优先，beta 转置 1/2 后 contiguous；BNSD 全部 contiguous 成头优先。TND 先转置 token/head、contiguous 再补 B=1；NTD 只 reshape 补 B=1，没有显式 contiguous，reshape 是 view 还是拷贝依赖实际 stride。V-first 初始状态交换最后两轴并 contiguous。attention 仍总是序列优先；aqk/akk 为 `[B,HV,S,C]`（rank3 去掉 B），其他中间输出保持前述头优先协议。h 内部 `[B,HV,NC,K,V]`，返回前置换为 `[B,NC,HV,K,V]`、contiguous，并按 rank3/V-first 去轴或交换末轴；最终状态是新分配结果，不原地更新输入状态。

### 直接启动 ABI、调度与 workspace

23 个 GM 参数依次是 `Q,K,V,g,beta,a_log,dt_bias,initial_state,cu_seqlens,chunk_indices,attn,final,gk,aqk,akk,w,u,qg,kg,v_new,h,workspace,tiling`。entry 标为 MIX_AIC_1_2，将 POD 从 GM 复制到 alignas(8) 栈上，再调用 `GetUserWorkspace(workspace)`。C=64、K=V=128 进入特化：编译架构 310 调 arch35，其他架构调对应泛化模板；其他几何进动态维模板，safeGate 两值分别实例化。共享 helper 在 950 上将 `computeGateInPrepare` 限于 Q BF16、g FP32、有 a_log、内核 gate 与 safeGate 全满足；denseFwdH 还需非 packed、S 整除 C。融合 PostWU 要求 dense、BF16、safeGate、HV 偶数；合入 FwdH 又要求 prepare 门控成立且不返回 QG/Vnew/H，不能从仅一个 flag 推断融合。

旧全局 entry 使用 `__schedmode__(1)`，原因是 FwdH 的 SyncAll 要求请求的全部 core 可调度；生成 inline 副本时省去该属性。新 ACLNN 用框架 schedule mode 配置，不能将两者当成同一 Host 行为。旧专用构建目标 `chunk_kda_fwd_kernel` 定义 HAVE_WORKSPACE/HAVE_TILING、关闭 `--cce-auto-sync`，950 增加 `ENABLE_CV_COMM_VIA_SSBUF=true`。Host 在 arch22 用物理 AIC 数，950 用 `min(物理AIC数,max((packed?N:B)*HV,1))`，平台查询的 AIC 数先取至少 1。

pack(8) 的 POD 为 37 个 int64、2 个 float、19 个 bool；按这些普通类型的 8 字节 ABI 推导为 328 字节、align 8，bool 后填充 5 字节，betaDataType 在偏移 320。Host 先清零结构体并复制到 352 字节运输 tensor；entry 复制 41 个 uint64，即前 328 字节，末 24 字节不是 Device 读取的字段。前十个 int64 为维度，随后 scale/lowerBound、19 个状态/融合/返回 flag、5 个 dtype/core 字段、21 个 workspace offset，末项 betaDataType。gate dtype FP32=2/BF16=1，beta dtype FP32=0/BF16=1；不能交换两个编码。

令 A=blockDim、U=B*HV*S、N=序列数、NC=totalChunks，所有算法 slice 起点按 512 字节对齐。NC 在 dense 是每序列块数，在 packed 是所有序列块数。各项输出开关为False时，gk/final/W/U/QG/KG分别需要 `4UK / 4N*HV*K*V / 2UK / 2UV / 2UK / 2UK` 字节 scratch；不返回不表示该阶段不计算。output_final_state默认True，默认final_state使用正式输出存储，只有storeFinalState=False时才申请对应状态scratch，不能将它计入默认workspace。缺省 Vnew/H 一般仍需 `2UV` 与 `2*(packed?NC:B*NC)*HV*K*V`，denseFwdH 时分别收缩为 `2B*HV*C*V`、`2B*HV*K*V`。另有始终分配的 qgScaled `2UK`，FP32 aqk/akk 各 `4UC`，求解 scratch `A*(safeGate?4:1)*5*C*C*4` 对齐后接 score scratch `A*4*3*C*K*2`。没有任何 PostWU 融合时再分配 `4B*HV*NC*C*K` scratch；这里索引按 padded chunk，而非直接将 NC*C 换为 S。

FwdH base 内的相对 slice 也按 512 对齐：V/Vupdate 各 `8ACV`、Kdecay `8ACK`、H `8AKV`，numSeq/numChunks 各 `8*(tokenBatch+1)`，tokenBatch 为 packed 的 N 或 dense 的 1；最后 output scratch `8UV`。总申请是 `GetLibApiWorkSpaceSize()+align512(userEnd)`。系统区与用户区如何对应实际 launch 参数依赖匹配 SDK/生成 stub；这里不假定固定 16MiB，也不把 user offset 直接加到未经 `GetUserWorkspace` 处理的 GM 基址。

### 异步所有权限制

Q/K/V/g/beta 规范化 tensor、状态和元数据由 Host 局部变量持有至函数返回，但转换成裸指针下发并不证明返回时 stream 已完成。a_log/dt_bias 使用 `optional->contiguous().data_ptr()` 的临时结果，未显式保存可能新分配的 contiguous tensor 所有者；非 contiguous 输入下存在额外临时生命周期边界。能否安全回收依赖未固定的 Torch NPU allocator、生成 stub 与 stream 约定，不能从这段源码判为已经观察到悬空访问，也不能宣称已闭合异步所有权。调用层还未提供显式 DeviceGuard、跨 tensor 同设备检查或 record_stream 证明。部署时需保持实际 stream 中使用的输入、输出、workspace 与必要拷贝存活，并分别检查 Host 回读、返回后 contiguous/permute 开销及其捕获限制。

## 证据与复核范围

本卡依据固定提交的第一方 API 说明，并增量核对同树旧 fla Python、直接启动 Host、POD、entry、arch35 helper、构建目标及 Torch helper。平台列表对应公共 API 合同；旧 Direct 的源码参考不单独推出平台覆盖或完整 launch 链闭包。架构编号按同提交构建说明映射为 A2/A3（arch22）及 950（arch35），具体子功能仍受正文限制。POD 尺寸是字段与 ABI 推导，未执行目标编译验证。本次知识提取未执行编译、真机、数值或性能测试，未记录 verified 事件。
