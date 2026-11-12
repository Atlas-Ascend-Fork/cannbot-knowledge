---
type: Guide
title: SGLang legacy因果卷积与recurrent GDN的状态接入
description: 区分causal_conv1d原生与Python布局，说明线性verify候选窗口、BF16 recurrent_gated_delta_rule门控及状态提交边界。
tags:
- task.implementation
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d/op_host/causal_conv1d.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d_update/op_host/causal_conv1d_update.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d_update/op_kernel/causal_conv1d_update.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d_verify.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/recurrent_gated_delta_rule/op_host/recurrent_gated_delta_rule.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule_kernel.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_conv1d_update.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_conv1d_prefill.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule_vs_triton.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/chunk_gated_delta_rule/op_host/chunk_gated_delta_rule.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/fused_sigmoid_gating_recurrent.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/run_kernel_tests.sh
  role: supporting
created_at: '2026-11-09T05:59:36Z'
updated_at: '2026-11-10T07:03:17Z'
platforms: []
aliases:
- causal_conv1d_update
- causal_conv1d_linear_verify_npu
- recurrent_gated_delta_rule legacy
---

# SGLang legacy 因果卷积与 recurrent GDN 的状态接入

## 先按入口区分布局与写入

本页针对 sgl-kernel-npu 固定提交 `dda6d36b0cdb4081e102d14c0a2fb276fc416e69` 的 legacy Python 模块及 `torch.ops.npu` 注册入口，不经过新 `operators.*` 的 `impl` 分发。`causal_conv1d`、`causal_conv1d_update` 和 `recurrent_gated_delta_rule` 均在 legacy 注册表中绑定原生实现；构建脚本将这三项放在双架构基础来源集合中。编入来源或注册成功并非各芯片已验收，本页没有整组产品矩阵，保持平台未定位草稿。现有 [recurrent概念](../../../concepts/kernels/recurrent_gated_delta_rule.md) 使用 cann-recipes 的 Next 自研扩展及 Qwen3.5 原生调用来源；本页专门保存此 sgl-kernel-npu 提交的 legacy Torch ABI、Python 布局与可变状态接入。SGLang 调用方的阶段和图限制见 [Ascend GDN状态指南](../sglang_ascend/sglang_ascend_attn_gdn_state.md)。

| 入口 | 输入和状态轴 | 返回与状态所有权 |
|---|---|---|
| `torch.ops.npu.causal_conv1d` | dense X `[B,T,C]` 或 packed X `[total_T,C]`；weight `[K,C]`；state `[pool,W,C]` | 返回新 `empty_like(X)` 输出；state 是 schema 标记的可变输入。`run_mode=0` 为 fn/prefill，1 为 update。 |
| `torch.ops.npu.causal_conv1d_update` | X `[B,T,C]`；weight `[K,C]`；state `[pool,W,C]` | 返回新输出，原地更新状态；不要把其参数顺序或布局套给下列 Python 同名 helper。 |
| `mamba.causal_conv1d.causal_conv1d_update_v2` | dense X `[B,T,C]` / 单步 `[B,C]`，或带 query_start_loc 的 packed `[total_T,C]`；weight `[K,C]`；state `[pool,W,C]` | Triton 路径先将 X 转 state.dtype，在转换结果上写输出，再恢复原 X dtype；同 dtype 时可能覆盖原 X，不能保证输入只读。 |
| `mamba.causal_conv1d.causal_conv1d_update_npu` | X `[B,C]` / `[B,C,T]`；weight `[C,K]`；state `[pool,C,W]` | 与 v2 轴顺序不同；无 cache_seqlens/num_accepted_tokens 时走 Torch 分支，常规 W=K-1 的状态协议下该分支仅处理 T=1（二维单步输入会扩为一项）；它把整段历史与 weight 相乘后归约为一项，不能据三维形状推定支持 T>1。多步输入须另行核对选中的 Triton 分支，不能按名字当作原生 Torch op 的薄包装。 |
| `mamba.causal_conv1d_verify.causal_conv1d_linear_verify_npu` | X `[B,C,T]`，state `[pool,C,W]`，weight `[C,W+1]` | 返回零初始化的新输出，逐步写独立 scratch；默认不提交 persistent state。 |

最后一项应从 `sgl_kernel_npu.mamba.causal_conv1d_verify` 导入。接入前记录调用的完整模块名、shape、stride 和状态池所有者；仅统一函数名会掩盖两套轴约定。

## 原生卷积的条件与 scratch 副作用

`torch.ops.npu.causal_conv1d(x, weight, conv_states, bias=None, query_start_loc=None, cache_indices=None, has_initial_state=None, num_accepted_tokens=None, activation_mode=0, pad_slot_id=-1, run_mode=0)` 检查 X/weight/state 的 BF16 或 FP16 dtype 一致、全部连续，weight 和 state 的通道维与 X 一致；原生 unified 入口只允许 K=2..4。packed X 需 query_start_loc 至少含两个元素，边界、request 数、状态索引和值域仍由调用方按实际任务保证。Host 将 query_start_loc/cache_indices/has_initial_state 转 int64，将接受数转 int32；不能以原始 dtype 不同推断不经过转换，也不能据已检查 shape 推定设备值域已完整验证。

独立原生 update 入口强制三维 X、二维 weight、三维 state，并强制 BF16/FP16 同 dtype 和连续。Host 在 `W>T` 时仅把旧 state 的 `[T:W]` 复制到前缀 `[0:W-T]`；Host 注释所述完整 `[old[T:W], X]` 滚动窗口还取决于 Device 的实际写槽，不能作为所有入参的保证。Device 的 `inStateOffset_` 初值为0，仅存在接受数时改为 `accepted-1`；首段循环把当前 X 写到 `inStateOffset_+K-2`，后段循环写到 `inStateOffset_+K-1+j`。已读活动原生用例具体为 `K=4,T=accepted=4,W=6`，其 Device 写槽与 Host 预移的前缀相接；不能只凭 `accepted=T,W=(K-1)+(T-1)` 将该结论推广到任意短T。Host 预移目标 `[0,W-T)` 若与后续初态窗口 `[accepted-1,accepted+K-2)` 相交，会先改变 Device 读取的历史；例如K4/T1/W3/accepted1先复制旧行1/2到前缀，随后不再读取原来的前三行。没有接受数且 W>K-1 的多步调用同样不具有整段保证。上述为 [Host 预移](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d_update/op_host/causal_conv1d_update.cpp#L106-L128) 与 [Device 两段循环](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d_update/op_kernel/causal_conv1d_update.h#L193-L269) 的静态条件分析，未执行数值或状态验证。C>4096 时沿通道切连续临时副本，启动后拼回输出和 state，因此宽通道并非一次无副本更新。pre-shift 对索引执行 clamp_min(0)，padding 索引可令 slot0 参与预移；不要将 kernel 的 pad_slot 跳过约定扩大为整个 Host 调用对 slot0 完全不写。

Python `causal_conv1d_fn_npu` 仍有自己的 Torch conv1d/packed padding 路径，最后以 cache_indices 做 index_copy_；签名虽然带 pad_slot_id，函数体没有据它过滤索引。它不能替代原生入口的 padding 语义。该 wrapper 还直接读取 query_start_loc 并写 conv_states，签名中的 Optional 并不代表这些状态与长度可任意省略。Python v2 的大部分额外检查由 validate_data 控制，默认 False，也不代表输入已全面校验。

## 线性 verify 的候选窗口

`causal_conv1d_linear_verify_npu(x, conv_state, weight, bias, conv_state_indices, intermediate_conv_window, intermediate_state_indices, activation="silu", update_persistent_state=False)` 只描述固定宽度线性链。K=W+1 且 K=2..6，scratch 为 `[scratch_slots,T,C,W]`，数据 Tensor 同设备且连续，X/state/scratch dtype 相同；bias 为 `[C]`，activation 只能 None/silu/swish。两类索引均为 `[B]`、同输入设备，内部转 int32 连续。

kernel 对 state_idx 与 snapshot_idx 均非负的行才读写；wrapper 未校验它们的正向容量上界，调用方必须保证合法且没有并发覆盖。每消费一步写一个候选卷积历史。默认只写 scratch，update_persistent_state=True 才把最终完整候选历史写回 persistent state；这不是“按接受结果提交”。接受部分候选时，上层须选择正确步历史，不能把完整 verify 后的状态直接留作下轮 decode。

## Recurrent GDN 的 dtype、门控和索引

```python
torch.ops.npu.recurrent_gated_delta_rule(
    mix_qkv, recurrent_state, beta, scale,
    actual_seq_lengths, ssm_state_indices, nk, nv,
    intermediate_state=None, cache_indices=None,
    num_accepted_tokens=None, g=None, gk=None)
```

Host 强制 mix_qkv/beta/recurrent_state 为 BF16。mix 为 `[B,S,2*nk*dk+nv*dv]`，按 Q、K、V 拼接；beta 为 `[B,S,nv]`，state 为 `[pool,nv,dv,dk]`，ssm_state_indices 为 `[B,S]`，返回新 BF16 `[B,S,nv,dv]`。注意 state 的末两轴是 V,K，不同于本库 legacy Triton chunk 所用的 K,V；新公开原生 [chunk API](../../../apis/sgl_kernel_npu/sgl_chunk_gated_delta_rule.md) 同样使用 V,K。必须按实际入口比较，不能因名称含 chunk 就额外转置。测试和 Device 调用协议使用 int32 请求实际长度 `[B]`、int32 状态索引；Host 不会替全部必选元数据做完整 dtype/连续性/值域检查，调用方应准备同设备连续且容量合法的缓冲。

Q/K 在 kernel 内归一化，beta 是 sigmoid 前的 logit，g 为逐 value head 的 log-decay，内部执行 sigmoid(beta) 与 exp(g)；不能把已经 sigmoid 的 beta 或实际 decay 再当成原始输入。g 缺省时没有 log-decay 衰减；提供的 g 由 Host 转 FP32 连续。gk 虽保留于 schema、Host 参数及 Device 入口，固定 Device 函数未进一步消费它，不能据形参存在宣称实现 KDA 的逐 key 门控。

无 intermediate_state 时直接在 recurrent pool 的 ssm_state_indices 目标槽写状态。提供 intermediate_state 时 Host 将初态与写出指针都改为该 scratch，同时把 recurrent pool 作为独立 seed 来源。kernel 先按接受数选择 stateOffset：有 num_accepted_tokens 时取该行第 accepted-1 个 ssm 索引，否则取首项；只有 stateOffset%S==0 时从 recurrent_state[cache_indices[b]] 取得 seed，其余情况从所选 scratch 槽读取初态。该模式会直接解引用 cache_indices，调用方必须提供有效的请求到 persistent seed 槽映射。固定测试以 cache_indices[b]*S+步偏移 构造 scratch 槽号，并据此区分首步 seed 与中间候选历史；容量合法但不符合此槽号协议的索引不具有等价含义。接受数须与该协议一致，不能无条件送0或包含 bonus 的长度。每步候选状态写 scratch，persistent 最终提交仍由上层接受流程承担。

intermediate_state 必须 BF16；Host 会对它 contiguous() 后取指针，若原输入不连续可能写入临时副本而没有回写原视图，调用方应直接提供连续 scratch。内部资源按 MAX_MTP=8 预算，所列测试定义 S=1/2/8；Host 未对所有步数和值域执行显式边界检查，不能将任意 S 视为可用契约。

## 验证入口与停止条件

`test_conv1d_update.py` 定义 FP16 四步 v2 与顺序 decode 的逐位输出/尾部状态比较；另有 BF16 C=12288 的原生 update 比较代码。该脚本部分缺设备/缺注册路径直接返回或打印信息，脚本退出不等同所有比较已执行。`test_conv1d_prefill.py` 定义 dense/packed、FP16/BF16、K2/3/4、bias/activation、初态与 padding，以及负例的原生 fn 检查。不能由这些定义补造 linear_verify 的专属测试覆盖。

`test_recurrent_gated_delta_rule.py` 定义 BF16、S1/2/8 的输出与状态 reference；`test_recurrent_gated_delta_rule_vs_triton.py` 在恢复两侧状态后对齐 log-decay、beta logit 和实际写槽，只比较被消费的槽。跨路线比较必须同时核对状态轴、seed 槽、每步 scratch、接受后提交以及下一轮输出；只比本轮 attention 输出不足以验收状态机。上述均为本次只读提取的测试定义，没有运行、编译、图捕获或真机结果；未分析完整 Device 算法闭包。

缺少注册、dtype/布局不匹配、状态容量或接受数协议未确认时，停止切换并回到原有已验收的同入口配置；不要以强制 cast 或临时复制可变状态掩盖语义问题。

## 旧 Triton recurrent 的两种门控语义

本节入口是 fla.fused_sigmoid_gating_recurrent.fused_sigmoid_gating_delta_rule_update_npu，不是前文 torch.ops.npu.recurrent_gated_delta_rule，也不是新的单token fused_gdn_decode。它将raw门控激活和逐token Delta更新放在同一Triton program中，实际body仅逐元素乘、sum和outer，没有tl.dot；is_kda=False为每value-head标量衰减，True为逐key衰减，数学域不同，不能把True当成原生入口未使用的gk已经实现。

Host从k/v得到B,T,H,K,V、Hv=v.shape[2]；dense N=B，变长N=len(cu)-1。BK=nextPOT(K)，BV=min(nextPOT(V),64)，NK=ceil(K/BK)并assert NK==1，NV=ceil(V/BV)。BHV固定2、NHV=Hv//2，grid=(NV,N,NHV)，num_stages3、num_warps1、multibuffer=False。每program负责一个V片、一个请求和两个value-head，顺序处理两head；head映射为hv//(Hv//H)，Host没有验证head数正值或Hv%H==0。scale缺省K^-0.5，显式值要求>0。输出按源码q.new_empty(NK,*v.shape)分配、最后squeeze(0)，继承Q的dtype/options；Host未完整检查Q/K/V一致、输入shape或设备，不能把这种分配意图扩成任意dtype/布局的运行保证。

dense的bos=request*T，变长从cu[request:request+2]转int64读bos/eos，循环步数为eos−bos；不自动生成chunk metadata。连续Q/K的地址为((bos+i)*H+qh)*K+k，V/b/output按Hv寻址。持久state是[pool,Hv,V,K]，slot=initial_state_indices[request]，地址slot*Hv*V*K+hv*V*K+v*K+k。K/V有效lane有mask，index只检查负值，没有slot容量或重复slot并发检查。

标量模式要求A_log/dt_bias按Hv、a按token×Hv组织；KDA模式a基址为(bos*Hv+hv)*K+k，dt_bias为hv*K+k，A_log仍按value head读取。其激活与状态数学意图为：

    x = a + dt_bias
    sp = log(1+exp(softplus_beta*x))/softplus_beta
         if softplus_beta*x <= softplus_threshold else x
    log_gate = -exp(A_log)*sp
    beta = sigmoid(b)
    q_norm/k_norm = x/(sqrt(sum(x*x))+1e-6)  # 仅use_qk_l2norm_in_kernel=True
    D[v,k] = S[v,k]*exp(log_gate)            # KDA时log_gate[k]
    delta[v] = beta*(V[v]-sum_k(D[v,k]*K[k]))
    S_new[v,k] = D[v,k]+delta[v]*K[k]
    O[v] = sum_k(S_new[v,k]*(scale*Q[k]))

Q/K/V、b、A_log、a及dt_bias的load结果均显式转FP32，状态计算也在FP32；标量及KDA模式都沿用这两处a/dt_bias转换，不能将门控表达式描述成依赖其原始输入dtype。exp/log的具体primitive近似和融合仍由Triton工具链决定。每次向pool写会转pool.dtype，输出写转Q.dtype；不能宣称低精度pool时整段递推不舍入，也不能套用其他recurrent的rsqrt(sum+eps)归一化。softplus_beta正值/非零、阈值与输入finite均未被Host完整验证。

### 覆盖、状态生命周期与静态边界

重要的是实际b_h=zeros([BV,BK],float32)位于每个token循环内部。有初态且slot>=0时，每步重新load该slot，更新后立即store回同slot；跨步carry通过池中的舍入后值实现，不是保持一个全程FP32局部态。initial_state_source=None或slot<0时，每步从零开始，负slot也不写池；T>1时不能把这个分支解释为“零初态但仍跨token递推”。USE_INITIAL_STATE启发式只看h0_source是否None，并未验证对应indices一定有效。

BHV=2配合Hv//2而无尾head guard：奇数Hv的最后head没有program覆盖；Hv=1时NHV=0，源码没有另一个替代body处理它。输出用empty分配，未覆盖区不是已保证为0。它不影响偶数Hv且其他前提成立的域，不能泛称全部recurrent都少写。

IS_KDA=True时，token i的a实际读基址+i*Hv，符合常规连续[token,Hv,K]应有的+i*Hv*K只在i=0或K=1等退化条件重合。故K>1且请求长度>1时存在逐key门控token步进偏差；不是标量False路线的缺陷。KDA的a/dt_bias向量load也没有mask_k，BK>K时会越过该head的逻辑K域，实际是否越过分配还取决于head/缓冲容量。不要用Q/K/state的mask来补造gate向量已安全padding。

input_guard把所有Tensor参数contiguous，并从第一个Tensor选择NPU context；它不校验所有Tensor同设备。尤其可变initial_state_source若为非连续view，kernel更新的是临时连续副本，wrapper只返回O，没有copyback或返回新pool。调用方需要连续、正确VK存储且无并发覆盖的池；静态缺陷来自此具体helper和路由，不能外推到使用显式stride的targetVerify或原生recurrent。

每program状态逻辑tile为BV*BK个FP32、即4*BV*BK字节，q/k向量BK、v/delta/output向量BV；KDA gate也有BK项。两head顺序处理，不能把BHV2直接当成同时两份状态物理分配；Triton可能保留额外表达式/多buffer临时，源中没有物理UB总量、L1/L0或跨pipe同步显式预算。新输出逻辑容量NK*B*T*Hv*V*e(Q)，pool为外部所有，input_guard还可能产生多个连续副本。program之间无显式barrier/atomic；不同请求复用slot会破坏递推和跨步读写，需由调用者禁止冲突，不能按一次Host launch推导无竞争。

test_recurrent_gated_delta_rule_vs_triton.py专门把Nv约束为2的倍数，在is_kda=False下桥接raw softplus/log-decay并重置两侧池、只比较实际消费槽；它不覆盖奇数head、True逐key步进、无初态多步等上述边界。活动FLA列表仅有原生recurrent基础测试，没有该对照脚本，不能以组级A3/950矩阵宣称旧Triton两语义都已验收。这里只保存固定源码事实，维持平台未知Reference。

## Linear conv verify 的窗口推进与地址

前文线性verify的实际kernel是 _causal_conv1d_linear_verify_kernel。令W=state.shape[2]、K=W+1=2..6、S=X.shape[2]，BLOCK_C=min(256,nextPOT(C))，grid=(B,ceil(C/BLOCK_C))；一个program负责一个请求的一段channel，所有S步在同program按static_range顺序展开。HAS_BIAS、SILU与UPDATE_PERSISTENT_STATE按Host参数选择，虽然kernel还有K=1代码，当前wrapper明确拒绝K=1，不能列作可用路线。

先读取state_idx、snapshot_idx并设active=(两者均>=0)，再和channel<C组合为mask。历史加载、X加载、O和snapshot/persistent写受这个mask保护；weight/bias仅按channel mask加载。任一index负值时该请求的输出保留Host zeros_like(X)的零，scratch/pool不写；这与KDA targetVerify的“负snapshot仍生成输出”不同。正向index容量、重复槽和int64转int32前的值域没有检查，窄化不是容量验证。

每channel维护最旧到最新的W个历史FP32值，从state读一次；weight为[C,K]，按每channel顺序读K项并转FP32，bias可选。每步计算：

    y_t = bias + sum(j=0..W-1, history[j]*weight[j]) + X_t*weight[W]
    history = history[1:] + [X_t]
    out_t = silu(y_t)或y_t
    snapshot[request_slot,t] = 更新后的history
    # 循环结束后才按UPDATE_PERSISTENT_STATE写最终history到原slot

SILU实际为acc/(1+exp(-acc))，不是额外Torch activation launch；没有激活时直接写acc。history保留FP32并跨步移动，不从低精度snapshot回读，低精度store舍入不反馈到下一步；和旧recurrent的每token池reload不同。默认False时持久池只读，True时提交整个S步后的窗口，仍不是接受a步候选后的选择性提交。

所有传入stride单位为元素：X地址b*sx0+c*sx1+t*sx2；state为slot*ss0+c*ss1+j*ss2；weight为c*sw0+j*sw1；snapshot为snap*sn0+t*sn1+c*sn2+j*sn3；out同样按三维stride写。Host当前强制数据Tensor连续，不能因kernel有stride形参便宣传wrapper可接受任意非连续视图。X/state/snapshot须同dtype；weight/bias只检查同设备、shape及连续，不强制同dtype，浮点计算以load.to(float32)为边界，不补造所有整数/复数或其他dtype可编译承诺。Host也未完整校验正B/C/S和资源上限。

每program有效历史逻辑payload为4*W*BLOCK_C字节，最多5120B；权重逻辑payload为4*K*BLOCK_C，最多6144B，另有bias/current/acc等向量。源码声明最多5历史和6权重向量，编译期guard/活跃区间决定是否消除，不能把这些逻辑值相加冒充实际UB峰值。源码注释用8步场景说明BLOCK_C限制256、512可能超过192KiB UB；这是tile设计依据，不证明任意S或某芯片已安全。此算法没有tl.dot、显式workspace、跨programbarrier或atomic，物理UB和跨pipeordering留在Triton编译器边界。

GM新out容量B*C*S*e(X)，外部scratch容量scratch_slots*S*C*W*e(state)，持久池pool_slots*C*W*e(state)；index转换还可分配B项int32临时。输出zero初始化、每步history快照和可选最终池写是不同生命周期；别把snapshot当成只含卷积输出，也别在上层提交前覆盖仍供verify读取的seed。data/scratch/pool若互相alias或多个请求写同slot，source没有建立额外同步来解决，调用者需保证合法所有权。常规conv1d_update/prefill测试不能替代此独立linear verify的专属数值/状态验收。

## 完整实现与集成证据的分工

[原生recurrent A3源码卡](../../../operators/direct/transformer/attention/sgl_recurrent_gated_delta_rule.md) 与 [950源码卡](../../../operators/direct/transformer/attention/sgl_recurrent_gated_delta_rule_950.md) 负责固定BF16 native Host/POD/AIV闭包；[causal update v2源码卡](../../../operators/direct/nn/conv/sgl_causal_conv1d_update_v2.md) 的dense/packed与有无复制规则也不能套给本节[B,C,T] verify。本页保留两种旧Triton算法和状态机事实，不把Reference的未知平台变成已完成VV Operator。上述所有测试、编译、图、真机、数值与性能验证本次均未执行，未添加verified事件。

### 增量算法的固定源码索引

| 固定文件 | 对应事实 |
| --- | --- |
| [python/sgl_kernel_npu/sgl_kernel_npu/fla/fused_sigmoid_gating_recurrent.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/fused_sigmoid_gating_recurrent.py) | 两门控、逐tokenreload、head/stride与tile |
| [python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py) | input_guard连续化与device context |
| [python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d_verify.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d_verify.py) | 卷积窗口、全stride、active与post-step快照 |
| [scripts/run_kernel_tests.sh](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/run_kernel_tests.sh) | 活动MAMBA/FLA列表与过滤 |
| [tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule_vs_triton.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule_vs_triton.py) | 偶数head/标量门控对齐与实际写槽对照，未运行 |

## 旧[B,C,T]卷积Host与独立update body补充

以下只对应同一kernel commit的mamba/causal_conv1d.py，保留Reference/platforms=[]，不改变前文native075/standalone精确rolling限制，也不把v2的FP16历史转换、APC/packed布局或A3 formal覆盖转移到这些旧函数。

### Torch prefill、packed准备与末态提取

causal_conv1d_fn_native输入X[B,C,T]、weight[C,K]，先X.to(weight.dtype)，无初态用F.conv1d(X,weight.unsqueeze(1),bias,padding=K-1,groups=C)，有初态则cat(initial_states,X)后padding0，再只取输出前T项；可选F.silu，最后转回原X dtype。它是外部Torch depthwise conv1d数学，未在本仓提供这些Torch core的自有Device闭包。return_final_states=False返回(out,None)；True还用seqlens和has_initial_state算：

```text
base=seqlens-(K-1)*(~has_initial_state)
positions=base[:,None]+arange(K-1)
final=working_X.gather(2,clamp_min(positions,0))
final[positions<0]=0
final=final.to(original_X_dtype)
```

seqlens/has_initial_state在True时实际必需，Optional签名不是可随意省略的保证；上界positions未clamp。working_X在任何initial_states存在时已对**全部请求**cat历史前缀。prepare_data若一批has_initial_state有True、有False，会对所有请求构造initial_states（False行先乘0），而上述base仍按False行减K-1，形成与“该行未cat前缀”的公式相同的偏移。条件例K4/T4、False行cat为[0,0,0,x0,x1,x2,x3]时，base1提取[0,0,x0]，不能称为最后三输入；若整批False使initial_states=None，则同公式在无前缀的X上可以正确取[x1,x2,x3]。这是条件化静态地址差异，未执行运行复现，不能将其泛化成所有初态调用都失败。

prepare_data先在has_initial_state非None且.any()为True时index_select池slot，再乘每行flag；否则initial_states=None。无论dense/packed都读取query_start_loc相邻差为长度。dense rank3直接返回原X/初态/长度；packed预期[C,totalT]，按weight.dtype/device分配zeros[C,B*maxT]，通过请求内mask形成indices，index_copy_把X前query_start_loc[-1]列放入分请求padding区，再view/transpose/contiguous为[B,C,maxT]。这些.any、max、动态mask/shape与Torch索引不是一个已经证明无Host读回的图安全准备流程。

causal_conv1d_fn_npu在末轴stride!=1时连续化X，并连续化bias；无条件assert query_start_loc[-1]<=X.shape[-1]，dense也执行。随后调用prepare_data及return_final_states=True的native函数，**无条件**conv_states.index_copy_(cache_indices,final_states)，并不按pad_slot_id过滤；kwargs/pad_slot_id不参与该body。缺query/池/index/flag时可能在实际读取/索引处结束，不能按Optional/default宣称无状态模式已实现。packed输出反向transpose/flatten后index_select有效indices，再用F.pad补回原X末轴多余容量，未消费尾补零；dense直接返回conv结果。没有自有slot去重、跨stream协议或native C++转发。

### 旧update wrapper的真实路由

causal_conv1d_update_npu输入X[B,C]会unsqueeze末轴成[B,C,1]，weight[C,K]、pool[P,C,W]。activation bool转silu/None，字符串只接受silu/swish；validate_data默认False，只有True才运行若干shape/stride/state容量检查，并assert cache_seqlens is None。metadata形参未消费。out初设为X，之后分两条：

| selector | 实际执行与返回/副作用 |
|---|---|
| cache_seqlens=None且num_accepted_tokens=None | 先conv_state[conv_state_indices] gather，再torch_causal_conv1d_update_npu，最后indexed assignment回池；out是Torch新结果，不保证复用/覆盖原X |
| 其余 | 调用独立_causal_conv1d_update_kernel，grid=(B,ceil(C/128))、BLOCK_N128，out=X原地覆盖；可写intermediate_conv_window |
| intermediate_conv_window | 只在JIT路线消费；Torch路线未把它传给helper，不能据提供参数保证已保存snapshot |

上表JIT符号实际拼写为 `_causal_conv1d_update_kernel`。虽然docstring称cache_seqlens启动环形缓存，body只是把该ptr作为形参接收，**从未load或用其数值**；存在该参数只足以改变Host route，不能称实现按cache_seqlens%W寻址。validate_data=True还先拒绝非None cache；该输入触发的raw路线需与文档冲突分层。

Torch helper将[旧state,X]先cat并转weight.dtype，可选逐步snapshot参数只属于helper自身签名，wrapper未传。无snapshot参数时末state为cat末W项；输出却把整个cat与weight转FP32逐元素相乘、沿末维sum成[B,C,1]，再加bias、转X.dtype后可选F.silu。常规W=K-1下T1匹配K项；T>1不能据“输入3D”推导逐步卷积，实际可能shape不兼容或只归约出一个结果。conv_state_indices=None还会进入Torch的None索引语义，不是自动按batch逐行slot映射的显式实现。索引/临时copy/数值primitive属于外部Torch边界。

### 可达JIT的有效状态长、地址与快照

wrapper从实际pool读stride后将传入state_len**重写**为L=K-1+(T-1)=K+T-2，NP2_STATELEN=nextPOT(L)；并不按实际W限制，故实际池窗口至少需容纳所有被访问位置。accepted存在时a=accepted-1，否则a=0；无accepted值范围clamp。每program先按indices或batch确定slot，只在slot==pad_slot_id时return；其它负slot/正向越界无完整保护。

对K2/3/4、非empty输入、有效slot和可表示地址，以n为窗口坐标、c为channel，实际顺序是：

```text
history[j]=load(pool[slot,c,a+j]), j=0..K-2
old[n,c]=load(pool[slot,c,a+n+1]),
          mask=(slot<num_cache_lines)&(n+T<L)&(c<C)
newX[n,c]=load(X[b,c,n-(L-T)]),mask=0<=n-(L-T)<T且c<C
tl.debug_barrier()
pool[slot,c,n]=old[n,c] if n+T<L else newX[n,c], mask=n<L且c<C
for t=0..T-1:
    acc=bias+sum(history[j]*weight[c,j])+X[b,c,t]*weight[c,K-1]
    history=history[1:]+[X[b,c,t]]
    X[b,c,t]=silu(acc)或acc
    snapshot[slot,t,c,j]=history[j]         # 仅SAVE_INTERMEDIATE
```

故persistent写入的是旧[a+1:a+K-1]的K-2项再拼全部T个候选，长度L；不是无条件按实际W滚动，也不是接受后只提交a步。初态history在池覆盖前加载；X用于池更新也先load，再由debug_barrier位于同program读写之间。该barrier不是跨program/跨stream发布或重复slot去重。source旧数据load的slot上界mask不保护随后store或先前history load，不能据局部mask宣称非法slot整体安全。

snapshot用persistent slot作为第一轴，按真实四stride[slot,t,c,j]写K-1项；不接收独立snapshot_indices，不等同linear_verify的独立scratch映射。False时不读写snapshot ptr。旧JIT没有把历史/weight统一显式转FP32，bias/accumulator是FP32；乘法promotion/融合和存回X、pool、snapshot的舍入由primitive/compiler决定，不能套v2的明确FP16历史规则。

Host没有K2..4范围guard。K1缺少后续使用的col0/w_col0 producer；K>=5时j循环只有K2/3/4的选择分支，实际一直沿用初始col0/w_col0，history也没有相应推进（K5额外col3 load未被该乘加分支消费）。不能把这种源可达域宣传为一般K阶卷积；未执行编译，不编造具体错误码/特定输出数值。batch/stride/runtime scalar与NP2/arange等仍须满足实际Triton准入。

### 参数、资源与生命周期

可达JIT的9ptr为X/weight/bias/pool/cache_seqlens/indices/accepted/snapshot/out，runtime batch及constexpr C/T/L/num_cache_lines；16个stride覆盖X、weight、pool、indices、snapshot、out，另有pad_slot_id与HAS_BIAS/KERNEL_WIDTH/SILU/IS_CONTINUOUS_BATCHING/IS_SPEC_DECODING/NP2_STATELEN/USE_PAD_SLOT/BLOCK_N/SAVE_INTERMEDIATE。各stride单位为元素；输入/输出按[B,C,T]真实stride，pool按[slot,C,W]真实stride，snapshot按四stride。实际batch越界有earlyreturn，channel tail由c<C mask；snapshot/slot/accepted容量仍由调用者保证，重复slot可竞争。

每program旧state/newX逻辑矩阵为NP2_STATELEN×128项，各按实际load dtype；history为K-1个128项向量，weight至多4个128项，FP32acc/bias各512 B；where/转型/临时由compiler安排，不相加冒充物理UB峰值。有效池写L*C个元素/request，snapshot可选T*(K-1)*C，X原地写T*C。无自有GM workspace、L1/L0/queue/event或atomic，tl.debug_barrier只给可见的本program读写顺序节点；Torch分支则有gather/cat/FP32等临时。调用方需保持X、pool、metadata/snapshot到异步消费结束，不并发复用slot，不将snapshot发布等同persistent接受后提交。

### 无Host绑定的另一raw JIT

同文件还定义 `_causal_conv1d_update_kernel_no_cache_len_no_mtp`（22形参），本文件Host没有调用它，不能把它列作上述wrapper的fallback或正式Route。它按pid取slot并可跳pad，DIM_BLOCK循环整channel块，无channel tail mask；将[Cblock,W]与[Cblock,T]经reshape/trans组合成token-major一维cat，再extract末W项回写state，weight也转同token-major次序。参数align_val要求DIM_BLOCK可按其整除，arange/reshape和实际packed内层布局均无Host验证。

width==W+T时归约整个cat×weight成一输出；否则对每个t提取K项滑窗（起点conv_begin=W-K+1+t）做FP32乘积/归约、可选SiLU。但循环中的store始终使用同一个 `(doffs+arange(DIM_BLOCK))*out_len` 地址，未加t偏移，故若外部Direct实例确实T>1且走该循环，各t覆盖同一位置；不能宣称生成完整T输出。它的W/T/K长度、索引/stride均不由任何已定位Host producer保证。当前保存raw算法/地址/资源（cat=(W+T)*DIM_BLOCK、state W*DIM_BLOCK、weight K*DIM_BLOCK元素）作为Reference，不补造grid、平台或完整VV闭包。

固定增量证据：[Torch prefill与准备](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d.py#L654-L815)、[未绑定raw body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d.py#L818-L974)、[实际可达update body](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d.py#L977-L1239)、[Torch update与Host](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d.py#L1242-L1450)。以上是源码事实/条件化静态推导，本次未执行任何编译、测试或状态验证。


## 固定来源

- [python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d.py)（primary）。
- [csrc/pytorch_extensions.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp)（implementation）。
- [cmake/legacy_kernels.cmake](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake)（constraint）。
- [csrc/causal_conv1d/op_host/causal_conv1d.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d/op_host/causal_conv1d.cpp)（implementation）。
- [csrc/causal_conv1d_update/op_host/causal_conv1d_update.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d_update/op_host/causal_conv1d_update.cpp)（implementation）。
- [csrc/causal_conv1d_update/op_kernel/causal_conv1d_update.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/causal_conv1d_update/op_kernel/causal_conv1d_update.h)（implementation）。
- [python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d_verify.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/mamba/causal_conv1d_verify.py)（implementation）。
- [csrc/recurrent_gated_delta_rule/op_host/recurrent_gated_delta_rule.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/recurrent_gated_delta_rule/op_host/recurrent_gated_delta_rule.cpp)（implementation）。
- [csrc/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule_kernel.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule_kernel.cpp)（implementation）。
- [tests/python/sgl_kernel_npu/test_conv1d_update.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_conv1d_update.py)（evidence）。
- [tests/python/sgl_kernel_npu/test_conv1d_prefill.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_conv1d_prefill.py)（evidence）。
- [tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule.py)（evidence）。
- [tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule_vs_triton.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_recurrent_gated_delta_rule_vs_triton.py)（evidence）。
