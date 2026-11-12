---
type: Guide
title: SGLang legacy GDN的chunk、mega与三角逆调用路线
description: 说明GDN_USE_MEGA_GDN分派、chunk64与mega128状态几何、FP16中间转换、构建范围及triangular_inverse单位三角布局。
tags:
- task.implementation
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/mega_chunk_gdn.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk_delta_h.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mega_chunk_gdn/op_host/mega_chunk_gdn.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/tri_inv/op_host/tri_inv.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/tri_inv/op_kernel/kernel_tri_inv.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/tri_inv/README.md
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_chunk_gdn_pto.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_chunk_gdn_triton.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_triangular_inverse.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk_gated_delta_rule_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_host/chunk_gated_delta_rule.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_apt.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_tiling_data.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_tiling_key.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage1.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage2.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage3.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_utils.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage1.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage2.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage3.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_utils.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/vf/chunk_gated_delta_rule_stage1_vf.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/chunk_gated_delta_rule/op_host/chunk_gated_delta_rule_tiling.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/chunk_gated_delta_rule/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mega_chunk_gdn/op_kernel/chunk_h.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mega_chunk_gdn/op_kernel/chunk_o.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/layernorm_gated.py
  role: implementation
created_at: '2026-11-09T05:59:36Z'
updated_at: '2026-11-09T16:24:29Z'
platforms: []
aliases:
- GDN_USE_MEGA_GDN
- run_mega_chunk_gdn
- triangular_inverse
- chunk_gated_delta_rule_npu
---

# SGLang legacy GDN chunk、mega 与三角逆的调用路线

## 路线与实际入口

本页仅记录 sgl-kernel-npu 固定提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的 `sgl_kernel_npu.fla.chunk`、mega 包装及 legacy Torch 注册，不是新公开 `operators.attention.chunk_gated_delta_rule` 的同义 API。新接口已有 [独立API卡](../../../apis/sgl_kernel_npu/sgl_chunk_gated_delta_rule.md)，应按所用入口核对返回值、状态方向与 chunk 几何。

`chunk_gated_delta_rule_npu(q,k,v,g,beta,scale=None,initial_state=None,output_final_state=True,cu_seqlens=None,head_first=False,use_qk_l2norm_in_kernel=False)` 实际返回 `(o, final_state, h)` 三项；docstring 只列两项，默认 final-state 描述也与签名不同，调用者应按实现解包。head_first=True 会直接抛 DeprecationWarning 异常，后面的转换不可达，不是仍可使用的布局选项。

Q/K/V dtype 须相同且不能 FP32，beta 须三维；默认布局为 `[B,T,H,K/V]`，g/beta 是逐 value head 的 `[B,T,Hv]`。packed 变长要求 B=1、cu_seqlens `[N+1]`，initial_state 若存在须有 N 行。scale 缺省 K^-0.5；可选 Q/K L2norm 在进入具体路线前执行。input_guard 将传入 Tensor 连续化并切换 NPU device context，故应把复制成本计入接入测量。函数明确禁用 torch.compile。

分阶段 chunk64 的状态核也有固定几何边界：`chunk_delta_h.py` 只处理 K 的0–127及 V 的两个64列块，并仅写回这些 h/final_state 区域。K或V超过128时，不能保证覆盖分配的完整状态；函数的 K<=256 断言不能作为更大维度已支持的依据。该状态核可确认的覆盖上界是 K<=128、V<=128，其余子核条件仍需单独核对；已有测试定义采用 D=128，不由此推导所有更小维度均已验证。

`GDN_USE_MEGA_GDN=1` 才选择 `run_mega_chunk_gdn`，其他值默认进入分阶段路线：chunk64 的 log-g cumsum → scaled KKT → solve_tril → WY w/u → chunk state/h → output。内部 fwd 返回7项，GDN_RECOMPUTE_SUPPRESS_LEVEL<3 时 w/v_new 返回 None，公开 wrapper 仍只返回 o/final_state/h。不能因7项内部返回而推定每次都保留全部中间值。

固定 Python 来源树没有 `GDN_ATTN_BACKEND_TRITON` 的消费者，尽管 Host 错误提示和旧测试 fixture 写出此名称；它不能替代本文件实际读取的 GDN_USE_MEGA_GDN。选择回退时应核对实际调用分支。

## Mega 的硬限制与精度转换

legacy 构建根据 SoC 将 arch22 对应 A2/A3、arch35 对应950；SGL_KERNEL_ENABLE_A3_ONLY_OPS 默认在950关闭、其他该构建族开启。mega_chunk_gdn 和 triangular_inverse 的 schema/实现均置于该宏下，Host/Device 来源也仅在该开关开启时加入。不能依据 Python helper 可导入推断950默认制品已注册它们；强行开启构建宏也不构成产品支持证明。本页覆盖的组合缺少完整产品验收表，保持平台未定位草稿。

mega Host 要求：packed B=1，Q=K shape `[1,T,Hk,128]`，V `[1,T,Hv,128]`；Hv 必须为8/12/16/24/32/48/64之一且为 Hk 的整数倍，即 Hv%Hk=0。g/beta `[1,T,Hv]`。原生调用 Q/K/V/beta 必须 FP16，g FP32，cu_seqlens int32，全部连续；有初态时为连续 FP16 `[N,Hv,128,128]`，N=cu.numel()-1。Host 还要求 batch_size=N、seq_len=total_tokens=T、block_dim 为正 uint32 范围，num_matrices 在 uint32 范围。不能只满足 shape 而忽略边界数组的起点、终点、单调性、正向容量和 workspace 所有权，这些未被 Host 全面验证。

`run_mega_chunk_gdn` 会把 Q/K/V/beta 及初态转 half；原本 BF16 输入因此经过 FP16 中间数值路线，不是保留 BF16 积累协议。g 不会在包装层自动转 FP32，需调用方提供正确 dtype。CHUNK_SIZE=128；包装把 cu 转 int32，并通过 cpu().tolist() 计算 `sum(ceil(seq_len/128))`，设备边界含 D2H/Host 控制成本，不应仅按原生单次 launch 估算整条路线。

包装分配 mask、A/A_inv、w/u、每 chunk h、v_new、final_state 及多组 workspace，mask 按设备缓存。底层 op 原地填这些预分配 Tensor 并返回空；包装再把 out 乘 scale、转回原 Q dtype，A/w/h 转原 K dtype，v_new 转原 V dtype。输出 h 为 `[1,num_chunks,Hv,128,128]`，final_state 若请求则为 FP32 `[N,Hv,128,128]`，否则 None。即使不请求 final_state，包装仍分配相应底层缓冲，不能据 None 推定没有成本。

## Triangular inverse 是受限子程序

`torch.ops.npu.triangular_inverse(x)` 的 Host 只检查至少二维、末两维方阵，并按 FP16/FP32 分发，返回新的 empty_like；没有完整检查连续性、三角方向、单位对角线、矩阵尺寸/非空值域。README 声明的尺寸是16/32/64/128，不能把 Host 未拒绝更大方阵当作已支持。

Device 注释和列扫描步骤假设单位对角三角矩阵，实际没有除以对角元；它不是任意非单位三角矩阵或一般矩阵求逆接口。测试从单位下三角矩阵出发，先转置末两轴作为输入，再按测试约定解释输出与 reference；原始存储及 stride 参与语义，不能只看逻辑方阵 shape 或重新 contiguous 后假定结果相同。集成时应沿固定测试的布局与输出解释验证，再考虑其他视图。

`fla.chunk.fast_inv_tril(A)` 构造 FP32 `I-A` 后调用该 op，再转回 A dtype；`inv_tril_inplace` 是另一 Torch 数学 helper。默认 chunk64 执行流调用 `solve_tril`，并不自动调用 fast_inv_tril。三者不可因都含 inverse/tril 就当作相同 ABI、精度或布局合同；需要启用 fast helper 时另核对单位对角与存储约定，不从存在该函数推定完整 chunk 路线已验证。

## 定向验证与代价

`test_chunk_gdn_pto.py` 定义无初态 T129、Hv/Hk 分组组合、变长 `[0,22,1333]` 及初态的 mega 输出/final-state 对照，输入 FP16；其误差判定先接受 max_abs<=1e-2，否则检查相对 RMSE<0.05，不能写成逐位相同。`test_chunk_gdn_triton.py` 定义 H4/8、D128、短序列、非整chunk及变长、多种gate mask的分阶段输出/final-state 对照；fixture 的旧环境名不证明它覆盖 GDN_USE_MEGA_GDN 的所有路由。

`test_triangular_inverse.py` 定义 FP16/FP32、矩阵16/32/64/128、随机与全一单位下三角的布局转换和 reference 比较。它没有建立任意非单位对角/任意stride/任意尺寸的支持结论。

接入验证先固定同一初态、Q/K归一化、scale、g/beta语义、cu边界与输出状态方向，分别核对 o/final_state/h；切换 chunk64/mega128 时，h 的 chunk 数与索引不能互换。测量需覆盖 Python dtype/连续化、边界回读、workspace峰值和最终输出转换。缺注册、head组合不合法、边界/workspace不明或误差不能接受时，恢复原已验收路线；不要靠错误提示中的旧环境名假定已回退。本次只读源码和测试定义，未执行上游、编译、模型、数值、图或性能测试，也没有完整 Operator/Device 闭包结论。

## 同名薄包装的旧 Direct native 入口

另一个文件 fla/chunk_gated_delta_rule_npu.py 的同名函数与前文 fla.chunk.chunk_gated_delta_rule_npu 不同：它原样转发到 torch.ops.npu.chunk_gated_delta_rule，仅返回 (out,final_state)。其 Q/K 为 BF16 [T,Nk,K]，V 为 BF16 [T,H,V]，beta 为 BF16 [T,H]；初态/终态为 [B,H,V,K]，lengths 为 int32 每序列长度 [B]。beta、初态、lengths 虽有 None 默认值，Host 均强制提供。它不经过 Triton chunk64 或 mega；前文三返回值、K×V 状态及 GDN_USE_MEGA_GDN 开关不适用于此入口。

应以实际 Host/Device 修正旧薄包装 docstring 的两项冲突：Host 的 scale=None 实际取1.0f，显式0仍保留，并非 K^-0.5；输入 g 是逐 token 的 log-decay，Stage1 自行求每个64-token块内的 G_i=cumsum(g)_i，不能预先传累计 G 再让它累计。beta 是直接系数，此入口不做 sigmoid；Q/K 不在 kernel 内归一化。其数学意图与新公开 chunk API 一致：

    D_i = exp(g_i) * S_(i-1)          # g=None时D_i=S_(i-1)
    delta_i = beta_i * (v_i - D_i @ k_i)
    S_i = D_i + outer(delta_i,k_i)    # S[V,K]
    out_i = scale * (S_i @ q_i)

Host 检查正 T/B/Nk/H/K/V、Nk/H<=64、K/V<=128、H%Nk==0并匹配各形状；g 存在时必须 FP32 [T,H]。BF16 状态走 arch22 或 arch35，FP32 状态仅允许实际 SoC 为 ASCEND950；out 继承 Q 的 options，final 继承初态 options。Host 没有检查全部输入均在同一 NPU，只为可选 chunk_state 检查与 Q 同 device。调用方仍须提供同设备、合法 lengths 与足够容量；shape 检查不能替代这些前提。

### 三阶段核心与共享实现

固定提交中，旧 csrc/chunk_gated_delta_rule/op_kernel 下两架构的 controller、stage1/2/3、utils 以及 arch35 的32阶 VF 逆，共11个文件，与 csrc/attention/chunk_gated_delta_rule/op_kernel 对应文件逐字相同，后者仅新增三行 provenance 注释。POD 字段及 pack8 相同，新副本另显式 include cstdint。ComputeTilingData 字节切片和 Matmul 配置也相同。因此复用 [A2/A3 ACLNN 三阶段源码卡](../../../operators/aclnn/transformer/attention/sgl_chunk_gated_delta_rule.md) 与 [950 ACLNN 三阶段源码卡](../../../operators/aclnn/transformer/attention/sgl_chunk_gated_delta_rule_950.md) 的 Device 机制；入口 ABI、校验及异步所有权仍须分别核对。

实际是一次 KERNEL_TYPE_MIX_AIC_1_2 launch。令 A 为平台 AIC 数、C=64、P=4 为 Stage1 每 AIC 并行槽数、S=2AC 为最大 token group 长；每序列串行分 group，各组执行 Stage1→SyncAll→Stage2→SyncAll→Stage3→SyncAll，stage返回前 Reset TPipe。Stage1任务域是 chunk×H，沿 AIC均匀分配，每批最多4项；两个AIV各32行。中间GM按实际 group 的 Sp=ceil(group_length/64)*64 作为 head stride，S只是容量上界。

Stage1把Q/K按源head跨行stride搬为BF16连续C×K，AIC计算KKᵀ、QKᵀ。AIV以beta、严格下三角mask、exp(G_i−G_j)构造单位三角系统，两AIV各解32阶对角块，AIC两次32³乘补下左逆块；还产生 qPrime=scale*exp(G)*Q、gBK=-beta*exp(G)*K、kg=exp(G_end−G)*K，再以块逆乘gBK/vBeta得到kCumDecay/vInner。Vector用FP32计算，BF16物化处CAST_RINT；无g时kg直接取K。

Stage2对每head沿chunk串行：先用进入态生成vInner修正和跨块out，保存可选pre-decay chunk_state，Vector衰减状态，Cube再以修正后的vInner和kg累加新状态。Stage3对有效m×m QKT施加scale、exp差及含对角因果mask，再乘vInner并accum=1加到out。尾块m<=64的QKT紧密存m×m，不能用固定64 stride消费。950 FP32状态仍先RINT生成BF16 state/vInner镜像作为Cube乘数，不能称为全FP32计算。

### 资源、交接与 Direct 生命周期

以下均为字节。Host分配16MiB+I+J，J=2*C*(2*C+3*K+V)*4*A。I按表顺序紧排，无逐片额外align；可选chunk_state是外部Tensor，不属于workspace。

| I片段 | BF16状态 | 950 FP32状态 |
| --- | --- | --- |
| gCum / kCumDecay | 4HS / 2HSK | 同左 |
| vInner及BF16镜像 | 2HSV | 4HSV+2HSV |
| qPrime / attnInter / kg | 2HSK / 2HSV / 2HSK | 同左 |
| qkt | 2HSC | 同左 |
| 状态辅助区 | arch22为4BHVK；950 BF16无此片 | 2HVK的BF16镜像 |
| 两种mask | 合计16AC² | 同左 |

Matmul producer读取实际UB/L1/L0C大小，A/B为GM ND BF16且允许transpose，C为BF16，base/org/fixSplit均128³、dim1、无bias；dbL0C、depthA1/B1、stepKa/Kb/M/N强制1。950 FP32状态另有相同配置但C为FP32的实例。GetTiling失败直接TORCH_CHECK，这不能替代Vector UB容量或整数溢出检查。Stage1每AIV两队列共32768B、scratch143360B、g活跃另256B，合计176128+256·hasG；scratch高水位arch22为130496B、arch35为130368B。Stage2 BF16最大131104B，950 FP32最大196640B；Stage3最大98304B。这些是源码公式，非运行成功证据；各stage串行，不能简单相加，也不能据此断言任意平台容量足够。

flag保护pack→KK(9)、KK→inverse(8)、inverse→Cube(7)、gBK→Cube(6)、vBeta→Cube(5)、QKT→Vector(A)；arch22按一批最多4槽交接，arch35逐槽交接，轮次不可混用。Stage2用FIX/MTE3旗标保护旧态消费、衰减/镜像和更新；Stage3用4/3保护maskedQKT临时区及下次覆盖。阶段SyncAll保护J在Stage3覆盖Stage1片段和组间I/J复用。上述两张共享Device卡保留完整offset、局部事件和各精度路线。

Direct Host将pack8 POD memset0并memcpy到32B向上对齐的CPU byte Tensor，pin_memory后以当前NPU device进行nonblocking copy；entry以ceil(sizeof(POD)/8)个uint64从GM复制到alignas8栈。950按stateIsFp32/hasGamma四组合选择实际模板；arch22为BF16/float模板、g是runtime分支。12个GM参数顺序是Q/K/V/beta/state/length/g/out/final/chunk_state/workspace/tiling；新ACLNN有13参数，chunk输入与chunk_result输出分开，不能互换launch签名。

输入先contiguous；非连续chunk_state仅写临时连续副本，无copyback且不返回该副本。lengths的正值/sum==T、chunk_state第0维容量及正向索引上界没有检查；零长度跳过该序列，empty final未写。实际capture写入sum ceil(L_b/64)个衰减前进入态，不能套用Torch reference的零长初态返回规则。

公共torch_helper.h的EXEC_KERNEL_CMD先把Tensor转raw data_ptr，再捕获stream、blockDim和指针tuple；lambda没有捕获这些Tensor owner，并忽略ACLRT_LAUNCH_KERNEL返回值后返回0。此处没有新ACLNN adapter的record_stream和逐调用返回码检查。它们是源码可证明的所有权/失败传播边界；在未读框架和allocator实际保证、未运行的情况下，不宣称每次都发生释放后使用或launch失败。

legacy_kernels.cmake将Host/Torch schema/impl放在基础集合，按SoC选择arch22或950 apt entry；该段注释明示A3/A5，顶层arch映射另含A2/A3/950。薄包装docstring也提及950 FP32状态，但未找到旧Direct专属测试调用。FLA CI的A3/950组矩阵和新ACLNN产品表不能单独证明旧Direct在A2上的完整支持/验收。本页继续platforms=[]，不声明整卡CANN版本。

## 配套完整实现与边界

[单launch PTO mega源码卡](../../../operators/direct/transformer/attention/sgl_mega_chunk_gdn.md) 展开固定kernel/PTO/SDK的七个逻辑阶段、head/n路线、内存和同步；本页保留Python cast、scale、cu回读和接入分派。PTO的C128、FP16及K×V状态，与上述Direct的C64、BF16及V×K不同。原生recurrent是逐token Vector更新、beta logit和内部Q/K归一化，也不等同这里的chunk入口。

PTO完整卡还限定静态风险：空序列H阶段在chunk循环前处理首快照，尾空序列chunk_offset==总chunk数时可形成h越界地址；O阶段显式flag图不能单独证明QS读取在同址workspace被QKV覆盖前完成，默认编译auto-sync能否补足需实际编译证据。前者不是所有长度分布均越界，后者不是已观测竞争。Torch cast/index/gather/连续化、编译器及Runtime/allocator内部继续属于本页外部边界。本次仅摄入已读固定源码，未执行上游、编译、数值、真机或性能测试，本Guide不声明完整Operator闭包。

### 增量源码索引

| 固定文件 | 读取与复用范围 |
| --- | --- |
| [python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk_gated_delta_rule_npu.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk_gated_delta_rule_npu.py) | 薄包装docstring与真实转发 |
| [csrc/chunk_gated_delta_rule/op_host/chunk_gated_delta_rule.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_host/chunk_gated_delta_rule.cpp) | Direct Host校验与分配 |
| [csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule.cpp) | arch22 Direct entry |
| [csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_apt.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_apt.cpp) | 950 Direct router |
| [csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_tiling_data.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_tiling_data.h) | POD/selector或资源producer |
| [csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_tiling_key.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_tiling_key.h) | POD/selector或资源producer |
| [csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage1.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage1.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage2.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage2.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage3.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_stage3.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_utils.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch22/chunk_gated_delta_rule_utils.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage1.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage1.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage2.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage2.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage3.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_stage3.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_utils.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/chunk_gated_delta_rule_utils.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/chunk_gated_delta_rule/op_kernel/arch35/vf/chunk_gated_delta_rule_stage1_vf.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_kernel/arch35/vf/chunk_gated_delta_rule_stage1_vf.h) | 与ACLNN副本共享的Device算法/资源/同步 |
| [csrc/attention/chunk_gated_delta_rule/op_host/chunk_gated_delta_rule_tiling.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/chunk_gated_delta_rule/op_host/chunk_gated_delta_rule_tiling.cpp) | POD/selector或资源producer |
| [csrc/attention/chunk_gated_delta_rule/torch_adapter.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/chunk_gated_delta_rule/torch_adapter.cpp) | ACLNN owner/record_stream对照 |
| [csrc/utils/torch_helper.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h) | pin/nonblocking与raw pointer launcher |
| [csrc/mega_chunk_gdn/op_kernel/chunk_h.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mega_chunk_gdn/op_kernel/chunk_h.cpp) | PTO空序列快照条件 |
| [csrc/mega_chunk_gdn/op_kernel/chunk_o.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mega_chunk_gdn/op_kernel/chunk_o.cpp) | PTO同址workspace显式同步边界 |

## 旧Torch GDN参考的完整算法与参数失效边界

本节仍固定fla/chunk.py，不属于新registered attention/gdn或上面的legacy Direct native ABI。inv_tril_inplace、chunk_gated_delta_rule_native、chunk_gated_delta_rule_npu_native均为Torch参考/组合入口；名字含native不代表调用本仓C++实现。自有Python地址、循环、公式可读，Torch normalize、matmul、reduce、pad/索引等核心Device primitive留在外部边界，不冒称完整Operator/source_closed或扩大平台。

### strict-lower逆的原地中间量

inv_tril_inplace(A)只assert最后两维方阵，要求调用者保证严格下三角及有效dtype/shape。对i=1..C-1，先clone row=A[...,i,:i]和sub=A[...,:i,:i]，再写A[...,i,:i]=row+sum_j(row[j]*sub[j,:])。此前较小row已被更新，构成逐行三角级数递推；返回A+eye(C)是另一个Tensor，**输入A的严格下三角已被修改，但没有原地加上对角I**。若原A不是严格下三角、对角非0或含上三角值，代码不清理这些域，不能当一般矩阵逆。

合法严格下三角下，返回意图为(I-A_original)^-1。default使用该helper的chunk参考会先构造负的严格下三角attn，故这里对应(I+M)^-1而非(I-M)^-1。不能忽略符号。clone防止本次row/sub被赋值过程覆盖，但没有跨stream/alias/并发访问的事务保证。可选tri_inv_fn也可由调用者换成其他callable；fast_inv_tril是FP32 I-A→另一个torch.ops.npu.triangular_inverse→转回dtype，布局与单位对角限制仍按前文，不能说默认Torch参考自动调用它。

### dense参考的实际轴与逐chunk递推

chunk_gated_delta_rule_native(query,key,value,g,beta,chunk_size=64,initial_state=None,output_final_state=False,use_qk_l2norm_in_kernel=False,tri_inv_fn=inv_tril_inplace)预期输入Q/K:[B,T,H,K]、V:[B,T,H,V]、g/beta:[B,T,H]。没有GQA复制、packed边界、shape/dtype/正C/finite等完整检查。g/beta必须是Tensor，None会在transpose/FP32转换处结束。

若use_qk_l2norm_in_kernel=True，先调用外部F.normalize于输入dtype的Q/K，再将Q/K/V/beta/g各transpose(1,2).contiguous().to(float32)。不能把“后续FP32”倒推成该normalize之前已显式转FP32；不同dtype和Torch primitive精度仍须区分。变为[B,H,T,K/V]后，源码解包变量sequence_length其实是H、num_heads其实是T；后续padding/loop确实沿这个T轴分chunk，不应只因变量名误称而判它按head分chunk。

令C=chunk_size，Tp=ceil(T/C)*C，Q/K/V沿time补零，beta/g也沿time补零。Q乘K^-0.5（无外部scale参数），再reshape成[B,H,Nc,C,K/V]；g在每chunk内cumsum，令G_i为其自然对数累计值，D_ij=exp(G_i-G_j)且只保留下三角含对角。此参考用普通exp，不像某些Triton safe_exp把正差归零，不能对任意正gate差宣称两者同一数值定义。

```text
M = strictly_lower(diag(beta) * (K @ K.T) * D)
R = tri_inv_fn(-M)                     # 默认返回(I+M)^-1并修改-M临时
U = R @ (beta[:,None] * V)
W = R @ (beta[:,None] * K * exp(G)[:,None])
S = zero[B,H,K,V] if initial_state is None else initial_state.to(U)
for each chunk:
    residual = U_chunk - W_chunk @ S
    local = lower_including_diagonal((Qscaled @ K.T) * D)
    O_chunk = (Qscaled * exp(G)[:,None]) @ S + local @ residual
    S = S*exp(G_last) + (K*exp(G_last-G)[:,None]).T @ residual
```

FP32 chunk状态S跨块保留；R/U/W、decay与Q等在Torch Tensor中物化，不模拟Triton中间低精度store再load的所有舍入。Torch FP32 matmul是否采用特定硬件近似/TF32等不由此文件显式控制，不给位级IEEE保证。初态K×V布局，不是native V×K池。没有原地提交persistent池；last_state是新的表达式结果。output_final_state=False最后将其设None，但前面状态计算仍发生。

O按time拼回[B,H,Tp,V]，裁前T，再transpose/contiguous并转原query.dtype，返回(O,last_state)。g尾补0只延续已有块累计值，K/V/beta尾补0使数学无效token不引入新状态增量；这是Torch参考的显式padding，不可用于证明另一个block_ptr load缺省padding的Device实现安全。

### packed参考wrapper的实际忽略参数

chunk_gated_delta_rule_npu_native(q,k,v,g,beta,scale=None,initial_state=None,output_final_state=False,cu_seqlens=None,head_first=False,use_qk_l2norm_in_kernel=False)实际先取Hq=q.shape[-2]、Hv=v.shape[-2]。只有floor(Hv/Hq)>1才沿dim2 repeat_interleave Q/K，未检查Hv%Hq==0，亦不保证K的head数与Q相同；不能把floor倍率当任意GQA支持。

它随后无条件读取initial_state.shape[0]为请求数N，分配empty_like(initial_state)终态，并按cu[b]:cu[b+1]从输入time轴截各请求。逐请求调用dense参考时**固定**output_final_state=True、use_qk_l2norm_in_kernel=True、chunk_size默认64。因此外层scale、head_first、output_final_state及use_qk_l2norm_in_kernel参数都没有控制实际计算；传scale0/其他值不改内层K^-0.5，传False也不关闭Q/K normalize或最终态返回。initial_state/cu虽有None默认，实际不可随意省略。

每个cur_state为initial_state[b].unsqueeze(0)，dense返回的FP32状态写入外层empty_like，可能再舍入为初态dtype；O是原q.dtype。外层先保存各request输出list，再从第0项取得dtype/device/shape，用cu[-1]作为总time分配empty，并以相同边界slice逐段赋值，返回(packedO,last_state)。N=0会访问core_attn_out[0]，缺少空batch早退；边界有gap、重叠、越界或初态请求数不一致也没有完整验证。slice标量/shape依赖cu的Torch索引行为，不能当纯Device异步metadata路径或无条件graph可捕获。它不返回各chunk h，也不是前文fla.chunk.chunk_gated_delta_rule_npu的三返回值wrapper。

### 资源、生命周期与Reference分工

dense参考会产生transpose/contiguous/FP32副本、padding Tensor、beta加权K/V、分块R和decay矩阵、U/W、O及递推状态，不是单Kernel融合。主要逻辑容量为：每个[B,H,Nc,C,C] FP32矩阵4*B*H*Nc*C*C B，FP32状态4*B*H*K*V B，O的4*B*H*Tp*V B，Q/K各4*B*H*Tp*K B；还有各阶段中间值与最后低精度输出。clone在逆中逐row分配row/sub，实际活跃峰值由Torch allocator及求值顺序决定，不能把所有表达式简单相加或当成确定UB/L1/L0预算。packed外层还保留输出list/终态和最终packed copy，存在请求串行Host循环成本。

无自有workspace、queue/event、atomic或跨Kernel显式barrier；Torch当前流依赖和allocator负责普通算子顺序，未提供跨stream/alias/池提交协议。调用方保持输入/初态/边界及输出直到消费结束，不能把default final_state=None当成不计算state，也不能用参考代码未检查值域扩大正式API支持。

本节用于保留旧参考的矩阵公式、低精度转换位置、可变inverse临时和wrapper实际参数语义；正式Triton stage、PTO与旧Direct native分别消费各自卡片/章节，不按共同“GDN”名称合并生命周期或完整闭包。固定来源：[fla/chunk.py的逆及两个Torch参考](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk.py#L30-L202)。本次未执行任何Torch参考、编译或数值/状态验证。


## 固定来源

- [python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk.py)（primary）。
- [python/sgl_kernel_npu/sgl_kernel_npu/fla/mega_chunk_gdn.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/mega_chunk_gdn.py)（implementation）。
- [python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py)（implementation）。
- [python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk_delta_h.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/chunk_delta_h.py)（implementation）。
- [cmake/legacy_kernels.cmake](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake)（constraint）。
- [csrc/pytorch_extensions.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp)（implementation）。
- [csrc/mega_chunk_gdn/op_host/mega_chunk_gdn.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/mega_chunk_gdn/op_host/mega_chunk_gdn.cpp)（implementation）。
- [csrc/tri_inv/op_host/tri_inv.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/tri_inv/op_host/tri_inv.cpp)（implementation）。
- [csrc/tri_inv/op_kernel/kernel_tri_inv.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/tri_inv/op_kernel/kernel_tri_inv.h)（implementation）。
- [csrc/tri_inv/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/tri_inv/README.md)（constraint）。
- [tests/python/sgl_kernel_npu/test_chunk_gdn_pto.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_chunk_gdn_pto.py)（evidence）。
- [tests/python/sgl_kernel_npu/test_chunk_gdn_triton.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_chunk_gdn_triton.py)（evidence）。
- [tests/python/sgl_kernel_npu/test_triangular_inverse.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_triangular_inverse.py)（evidence）。

## Qwen投影输出的QKV/Z/B/A布局分离

固定fla.utils另有两个可直接调用的Vector数据重排入口，以及一个Torch参考。它们只做拆分/拷贝，不执行QKV投影、归一化或门控激活，不能归入chunk GDN递推本体。两个Triton函数都分配四个新输出mixed_qkv:[B,2HqDq+HvDv]、z:[B,Hv,Dv]、b/a:[B,Hv]；QKV/Z继承mixed_qkvz dtype/device，b/a继承mixed_ba dtype/device，数据载入后原dtype写回，无FP32数学中间态。

令r=Hv//Hq、Vg=r*Dv，合法交错格式需要正Hq、Hv整除Hq及相符的物理连续输入：

| 入口 | 输入每行布局 | 精确搬运 |
| --- | --- | --- |
| fused_qkvzba_split_reshape_cat | Qwen3-Next每QK head组依次[Q_g(Dq),K_g(Dq),V_g(Vg),Z_g(Vg)]；BA每组[B_g(r),A_g(r)] | Q/K目标按全部Hq heads相连，V/Z按g*Vg，b/a按g*r写；源head offset=g*(2Dq+2Vg)，BA offset=g*2r |
| fused_qkvzba_split_reshape_cat_contiguous | Qwen3.5全局[allQ,allK,allV,allZ]，BA=[allB,allA] | Q/K/V分别拷到mixed_qkv对应全局段；Z从2HqDq+HvDv后开始；b来自BA首Hv，a来自后Hv |

两个入口不能仅因返回shape相同就交换。交错版本若Hv不整除Hq，floor得到的r会使实际V/Z/b/a覆盖不足分配的Hv区域；Host没有整除检查。Tensor每行stride按这些传入head参数计算，不读取实际Tensor stride或核对shape末轴。两输入同device、dtype、连续、rank、head参数、容量等也未统一校验，b/a可以被分配到与QKV/Z不同设备，而同一launch仍拿全部指针；合法域须由调用者提供。

### 交错格式的持久行划分

gridSize=max(1,min(首次缓存vectorCore数,B))，rowsPerVec=ceil(B/gridSize)；program p负责[p*rowsPerVec,min((p+1)*rowsPerVec,B))。每次处理R行，头组用tl.static_range(Hq)展开。Q/K列分别tl.arange(Dq)，V/Z列tl.arange(Vg)，BA列tl.arange(r)，仅行维mask，列没有补齐mask；这些arange尺寸及R需满足Triton编译约束，Host没有统一保证二次幂。

R的实际Host公式为 min(nextPower2(max(1,floor((85*1024/e0)/Erow))),rowsPerVec,64)，其中e0=mixed_qkvz.element_size，Erow=输入QKVZ宽+输入BA宽+输出QKV宽+输出Z宽+2*Hv。nextPower2向上取整、再min任意rowsPerVec，不能当成严格UB容量证明，甚至可能得到非二次幂R。85KiB注释来自A3 192KiB考虑double buffer的启发值，未查询实际UB；BA若dtype更宽，该单一e0估算还不能准确反映真实byte。B=0没有Host早退，grid仍1且rowsPerVec/R可能0，不能按一般空输出推导有效launch。

交错kernel对total_rows/rows_per_vec显式do_not_specialize，其他layout/head/tile为constexpr；每批按row_mask只拷有效行，输出覆盖与输入组映射一一对应，program间无共享workspace或显式barrier。无dot/Cube，物理UB/寄存器与同步由Triton编译器产生，不能由Host启发值推导已经过容量校验。

### 全局连续格式的分列与尾mask

block_size_col默认1024。Host取R=min(nextPower2(max(1,int(floor((85*1024*0.4/e0)/block_size_col)))),64)，rowsPerVec=max(ceil(B/gridSize),R)。program按p*rowsPerVec切不重叠行段，尾部按真实B保护。对Q、K、V、Z分别用tl.static_range按block_size_col分列，col<对应总宽与行mask共同保护，因此无需Dq/Vg本身为二次幂；但block_size_col的arange及一次读BA的tl.arange(Hv)仍有编译形状约束，Host未校验。两输入的rowstride是公式推导的紧密全局段宽，未用Tensor stride。

R使用40%启发再向上取二次幂，不是实际分配TBuf，也不保证所有编译临时均落在该预算。相比交错版本，该入口不按head组分解每列，而分列复制全局段；输出与每个有效输入元素值完全对应，无量化或额外舍入。B=0依旧构造并尝试launch，不声明真机空域支持。四输出总新增GM为(2HqDq+2HvDv)*B*e0+2Hv*B*e1，e1=mixed_ba.element_size，不包含输入或编译临时。

Torch参考fused_qkvzba_split_reshape_cat_torch只实现交错拆分：view分组、slice/reshape Q/K/V/Z、cat全部QKV、BA按组slice/reshape。cat输出为新Tensor，其他reshape可能是view或copy，不能将该参考的alias/分配语义等同Triton明确四个新输出。两个Triton入口都不经过input_guard；此模块的input_guard会连续化Tensor并切到第一个Tensor的device，装饰器存在不代表本函数已被装饰。旧utils.triton_utils.get_device_properties为无参数@cache，首次设备core数之后跨device仍可复用，不能因当前输入device不同就推导grid已重新查询。

prepare_position_ids对每个cu长度生成局部arange后cat，prepare_sequence_ids由位置==0的cumsum−1恢复请求号；零长请求不产生局部0，和chunk_indices一样可能压缩后续请求编号。tensor_cache按Tensor对象身份、非Tensor值及类型匹配，最多4项，命中移到最近位置；不检查Tensor内容版本，原地改cu会留下过期metadata。safe_exp、FLA_USE_FAST_OPS等导入时开关含义仍按KDA组件指南核对，不将gather缺失时返回None的编译占位当成实现了gather数学。

固定来源：[fla/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py)与[旧device helper](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py)。缺少针对这两个旧重排入口的完整平台/版本公开合同，本节保持Reference、draft/platforms=[]，不借单条A3 UB注释建立正式平台Operator；本次未执行编译、真机、数值或性能测试。

## 旧FLA的分组LayerNorm/RMSNorm与SiLU门控

fla.layernorm_gated提供layer_norm_fwd_npu_simd与layer_norm_fwd_npu两个不同Vector分块实现，均返回(out,mean,rstd)。它们与先把归一化结果舍入BF16、再调用独立gate_multiply不同：此处归一化、weight/bias、可选SiLU(z)在FP32局部完成，最终只在store转out.dtype，不能无条件拆成先存低精度norm再乘门值。

输入x:[M,F]，group_size默认F，要求F%group_size==0；G=F/group_size。每行每组独立统计，weight/bias各[F]按组偏移g*group_size，x/out/z行stride来自Tensor，末维要求1。可选z必须与x同shape；可选out只检查shape和末维stride，否则empty_like(x)。没有统一检查所有dtype、NPU/同device、alias、正group_size/eps或数值范围。group_size0会在Host取模失败；不从未拒绝的输入推导支持。

令n=group_size，s(z)=z*sigmoid(z)。若HAS_Z且norm_before_gate=False，先令u=x*s(z)，否则u=x。LayerNorm用mean=sum(u)/n、var=sum((u−mean)²)/n；RMSNorm用var=sum(u²)/n且不分配/写mean。rstd=1/sqrt(var+eps)，y=(u−mean)*rstd*weight+bias或RMS下u*rstd*weight+bias；HAS_Z且norm_before_gate=True再乘s(z)，最后store。bias/z两有无由实际指针heuristics，RMS与LayerNorm、gate前/后是独立数学，不能按一个公式省略。mean/rstd是FP32 [G*M]，地址g*M+row，group-major而非[M,G]逐行交错；out默认x dtype，caller out可不同而Host未限制。

| 入口 | 精确分核和分块 | 实际body/精度 |
| --- | --- | --- |
| layer_norm_fwd_npu_simd | grid=(ceil(vectorCores/G),G)，program(core,g)以row=core+j*numPrograms0持久遍历 | 每行load group，FP32统计/affine/gate，实际逐行store；multibuffer=True |
| layer_norm_fwd_npu | BLOCK_M固定48，grid=(min(ceil(M/48),vectorCores),G)，rowblock=pid*48+j*48*numPrograms0 | 一次48×BLOCK_N逻辑tile，weight/bias在外层载一次并广播各行；activation参数未读取、不会切换门控类型 |

两Host同取MAX_FUSED_SIZE=65536/x.element_size()，BLOCK_N=min(MAX_FUSED_SIZE,nextPower2(group_size))，group_size>BLOCK_N抛错，无多pass/大维度fallback。所谓64KiB只是单特征行输入量的门槛，不是统计/weight/z/output和multibuffer全部物理UB之和，也不是已验证的硬件预算；48行实际Triton tile和编译准入应保持原值记录，不能擅自替成常见32/64声称相同实现。物理UB/寄存器及跨pipe顺序由编译器生成，自有源码无workspace/barrier/atomic；各程序按行组独立写，非预期重叠out/weight/z别名仍由调用方避免。

尾部风险须按body区分。SIMD载x显式other=0，但gate-before-norm载z仅masked未显式other，不能把padding乘法后仍为零作为来源保证；其LayerNorm mean=sum(x)发生在xbar的列mask之前。48行版本载x也未显式other，LayerNorm mean同样先sum未经显式补零的tile；RMS的xbar则先where(cols<n,x,0)再求平方和。故非二次幂尾列不能仅凭最终store mask推导LayerNorm统计一定正确；这是缺少显式padding保证的静态边界，不是本次已复现的数值故障。

新增GM容量为out（若caller未提供）及4*G*M字节的rstd，LayerNorm另有4*G*M字节mean；临时FP32的n或48×BLOCK_N逻辑tile不代替实际UB峰值。M0未专门早退，SIMD仍按core/group配置launch、48行版可能得到grid0；空域与编译器处理未被本次验证。core helper仍为无参数首次device缓存。固定来源：[fla/layernorm_gated.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/layernorm_gated.py)。缺少此旧入口的逐平台公开支持和版本证据，保持本Guide Reference/platforms=[]，不借新注册RMSNorm或BF16门乘的产品表建正式Operator。
