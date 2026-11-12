---
type: Guide
title: SGLang Ascend KDA：V-first状态、ragged验证与步态提交
description: 说明KDA原生chunk/persistent状态布局、门控预激活、卷积转置及投机中间态搬移，避免照搬通用连续状态mover。
tags:
- task.implementation
- topic.attention
- topic.speculative_decoding
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_kda_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_hybrid_linear_attn_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/linear/kda_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/linear/kernels/kda_triton.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_prefill.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_chunk_delta_h.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_target_verify.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_kda_prefill_pool_layout.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_kda_target_verify.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/run_kernel_tests.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_gate.py
  role: implementation
created_at: '2026-11-08T12:07:58Z'
updated_at: '2026-11-09T15:10:26Z'
platforms: []
aliases:
- AscendKDAAttnBackend
- state_v_first
- kda_target_verify_npu
---

# SGLang Ascend KDA：V-first状态、ragged验证与步态提交

## Prefill状态与门控

NPU KDA persistent SSM为[N,H,V,K]，按slot gather初态转FP32；负padding slot用clamp0占位读取，再以valid_mask过滤最终写回，不能把padding写进slot0。Q/K先l2norm且contiguous，g是已经激活的FP32，beta是已sigmoid的FP32；native chunk_kda_fwd为chunk64、BSND、state_v_first=True、use_gate_in_kernel=False、safe=False，避免重复激活。

最终state转回池dtype后scatter；可按需读取中间h以跟踪prefix边界。卷积池布局[layers,pool,window,channels]，给通用跟踪方法提供转置视图，不能当连续的[channels,window]缓存。权重只在首次使用转置并转输入dtype，FP32 checkpoint权重可缓存为BF16调用权重。

## Decode与verify

decode先causal_conv，再按kernel_dispatcher.supports_packed_decode分支。标志为True时要求token数等于请求数，否则断言失败而非回退；标志为False时走dispatcher.decode。当前TritonKDAKernel在NPU将该标志设为False，即使每请求单token也走decode。extend需要extend_prefix_lens，run_mode0只取最后历史窗口、执行后写回；native gate预激活配beta.float.sigmoid。

target verify必须分配spec scratch；ragged候选可先scatter成bs*draft_width固定矩阵，空位使用额外sentinel行，然后调用 kda_target_verify_npu 包装入口并选择回原有效行。gates_are_preactivated=True，所有候选SSM写入中间态，卷积接受数按完整draft宽处理，最终仍需接受后提交。

## 接受后恢复

专用KDA hybrid覆写SSM mover，支持V,K转置/strided池；通用move_intermediate_cache假设连续，会写错地址。使用int32 slot和h_block_size1。当前supports_speculative_conv_state_snapshots=False，卷积通过窗口rollback恢复；future snapshot分支另用scatter，不能提前描述为现有默认行为。跟踪copy用where选择源/自身避免nonzero同步。

建议测试K/V维不对称、非连续state视图、负padding slot、ragged验证、跨prefix track边界和接受后连续两轮；仅看本轮输出不能发现错误状态提交。布局转换、dense化padding与scratch增加内存开销。此处不提供真机精度/吞吐结论，平台范围未逐项证实。

## 固定 kernel 来源的旧 Triton 组件

前文是 SGLang 提交 dadff253c0aa8c7456b351cb9d2c282a8e513958 的集成行为；本节另固定 sgl-kernel-npu 提交 dda6d36b0cdb4081e102d14c0a2fb276fc416e69。两者不能仅凭同名函数就推定部署时源码版本相同。这里的三个 prefill 子程序含实际 tl.dot，targetVerify则是逐元素乘和归约的Vector算法；不是新注册 ACLNN chunk_kda_fwd 的ABI，也不是普通标量GDN的WY/DeltaH/output别名。本节保存可读的算法、寻址、资源和状态边界，不作为完整Operator闭包或芯片支持声明；整卡继续draft、platforms=[]，不推测CANN版本。

以下 prefill 的连续逻辑布局为 k:[B,T,Hg,K]、w:[B,T,H,K]、u/v:[B,T,H,V]，每token的gk/g为逐key [B,T,H,K]；个别函数要求Hg=H的实际寻址，不能把三个签名统一成任意GQA支持。变长常用B=1打包，cu为[N+1]边界，A为[B,T,H,C]，C是chunk宽；调用者需要提供已构造的A，三个组件本身没有恢复其上游构造/求逆全过程，因此不把此参考描述成端到端KDA算子。

### WY：返回W、U和末态衰减后的KG

fla.kda_prefill.recompute_w_u_fwd_npu(k,v,beta,A,gk,cu_seqlens=None,chunk_indices=None) 分配w=empty_like(k)、u=empty_like(v)、kg=empty_like(k)，返回三者。C=A.shape[-1]，BK=BV=64，STORE_KG=True，grid=(num_chunks,B*H)。dense时num_chunks=ceil(T/C)；变长时用chunk_indices的长度，并在每个program读取(request,local_chunk)二元组来取得bos/eos与局部块号。

对一个head/chunk，A以基址 (bos*H+h)*C、shape(T,C)、stride(H*C,1)读C×C块；beta以bos*H+h和stride H读C项。K/V/gk分别以 (bos*H+h)*特征宽 为基址、token stride H*特征宽、末维stride1。Host不读取Tensor实际stride，也没有input_guard，不能把任意非连续view当成这些逻辑布局。

每个V64片先算 U=A @ cast_V(beta[:,None]*V)，tl.dot显式input_precision="ieee"，写回u.dtype；每个K64片计算 X=beta[:,None]*K*exp2(gk)，先cast为K.dtype，再算 W=A @ X，W的tl.dot未显式传input_precision，不能把U的ieee属性移植给W。KG=K*exp2(gk_last−gk)，last=min(chunk_start+C,T)-1，按有效K维加载末行，写为kg.dtype。gk是该块内的逐key累计log2量；不要向此接口再传未累计gate或自然对数却期待相同衰减。

当前局部逻辑tile包含A的C²项、beta的C项、每片C×64的K/V及gk/中间矩阵，dot默认FP32 accumulator并在store处转输出dtype；这里没有显式GM workspace或跨program锁。GM新增容量为2*B*T*H*K*e(k)+B*T*H*V*e(v)，不含已有A/beta/gk及编译器临时。boundary_check约束有效T/K/V，读取调用没有显式padding_option="zero"，不能用边界检查本身补造dot所有无效lane已清零的精度保证。物理UB/L1/L0与barrier由Triton编译器降低，源码不能给出实际分配总字节或容量通过结论。

### Chunk状态：VK外部池、KV私有计算与回写

fla.kda_chunk_delta_h.chunk_gated_delta_rule_fwd_h_npu(k,w,u,g=None,gk=None,initial_state=None,initial_state_indices=None,save_new_value=True,cu_seqlens=None,chunk_indices=None,use_exp2=False) 固定BT=64、BV=32，K>128显式失败；use_exp2=True且同时提供标量g也直接assert。H=u.shape[-2]、Hg=k.shape[-2]，key head为h//(H//Hg)，Host未验证整除/正数，必须由调用方保证。

dense的N=B、NT=ceil(T/64)；变长N=len(cu)-1、NT=len(chunk_indices)，另从prepare_chunk_offsets得到每请求首chunk位置。这里chunk_indices只用于计数，不在JIT内消费其pair内容。h分配为k.dtype的[B,NT,H,K,V]；v_new在save=True时为empty_like(u)，否则None。grid=(ceil(V/32),N*H)，num_warps4、num_stages2；每program串行处理一个请求、head、V32片，K<=64用一个[64,32]FP32状态，64<K<=128用两个，状态逻辑payload分别8192/16384B。另有BT×64的w/k和BT×32的残差tile，不能把单一payload当成实际UB峰值或并发buffer总量。

有初态时，source_indices=initial_state_indices[:N].long()；先从外部[pool,H,V,K]按slot index_select，transpose末两轴并contiguous成为[N,H,K,V]的kernel_state，再使用arange(N)内部槽号。kernel结束后反向transpose/contiguous，并index_copy_回原VK池。有初态却无indices立即失败；此路径没有targetVerify那样的负索引zero mask，不能将-1 sentinel直接推广给index_select。重复slot的并发请求和正向容量由调用方控制。无初态时仍分配[max(N,1),H,K,V]的私有FP32最终态scratch供kernel写，USE_INITIAL_STATE=False保证不把其empty内容当初态读。

令H_c为FP32的K×V进入态、R为块残差，实际顺序为：

    h[c] = cast_k(H_c)
    R = u_c - dot(w_c, cast_w(H_c))
    v_new[c] = cast_u(R)             # 仅save=True，store在衰减之前
    if g存在:
        R *= safe_exp(g_last-g_c)[:,None]
        H_c *= exp(g_last)
    if gk存在:
        H_c *= E(gk_last)[:,None]   # use_exp2选择exp2，否则exp
    H_(c+1) = H_c + dot(k_c.T, cast_k(R))
    kernel_state[request] = cast_state(H_final)

伪码中的v_new表示源码的store位置：它在两个门控分支之前存R，之后局部R才衰减并转K.dtype参与状态增量。没有save时该算术和指针操作均由真实SAVE_NEW_VALUE guard保护，不能套用普通GDN另一版本的None算术风险。状态跨chunk保留FP32局部值，h仅是进入态快照；dot输入会转低精度，不等于全FP32矩阵乘。scalar safe_exp来自utils：正参数映射exp(-inf)=0，非正参数才正常exp；不是将正值截成exp(0)=1。gk只取当前chunk末行作为K方向的状态衰减，token内部gk影响由调用方准备好的w/k等产物承担。

dense用boh=request*ceil(T/64)，变长用chunk_offsets[request]；h地址为((boh+c)*H+h)*K*V+k*V+v。k基址按bos*Hg和GQA映射，w/u按bos*H；末块NT由长度ceil，block_ptr boundary_check处理时间/特征尾；Host未完整检查这些输入的dtype、stride、同设备、cu内容或乘法溢出。外部KV/VK转换及index操作的完整数学kernel属于Torch边界。GM新增h为B*NT*H*K*V*e(k)，可选v_new为B*T*H*V*e(u)，另有N*H*K*V的私有状态及反转复制；不能忽略可变池gather/scatter的副本/生命周期成本。

### Output：直接消费K×V快照和调用方out

fla.kda_prefill.chunk_gla_fwd_o_gk_npu(q,v,g,A,h,out,scale,cu_seqlens=None,chunk_size=64,chunk_indices=None) 返回同一个out；不分配输出、不检查其容量/alias。BK=BV=64、H_LAYOUT_VK=False，grid=(ceil(V/64),num_chunks,B*H)。每K64片将q先乘scale并转q.dtype，再乘exp2(g)并再次转q.dtype，dot该C×64片与从h读取的64×64 KV片，FP32累加到C×64 b_o。h按dense全局chunk号或变长chunk_indices原始全局编号寻址，基址(i_tg*H+h)*K*V，不在内部做VK转置。

局部项读A的C×C块，含对角下三角以外设0，再cast为V.dtype，计算dot(A_causal,V_c)并加入b_o；该局部项没有额外scale因子。不能在函数外无条件再乘一次scale，也不能假设任意未按调用约定预缩放的A都会得到目标数学结果。最终store转out.dtype。显式源没有中间GM workspace，局部逻辑payload包括FP32 C×64 accumulator、C×C A和每次C×64输入/64×64 h；编译后物理内存与同步仍未知。out与输入或跨program区域重叠时没有额外同步保障，调用者应避免不符合数据依赖的alias。

### 变长元数据和精度开关

三个组件实际命中fla.utils：prepare_lens先将cu转int64求差；prepare_chunk_indices通过各长度ceil/C生成局部chunk序列，再以indices.eq(0).cumsum−1恢复request id，最后转回cu的device/dtype；prepare_chunk_offsets前置0后对各ceil累积。indices生成中的tolist有设备回读/Host控制成本。缓存最多4项，Tensor参数以对象is匹配，不检查_version或内容；同一cu原地更新可能复用旧lens/indices/offset，须保持该对象内容不变或显式提供与当前边界一致的元数据。prepare_chunk_indices按“出现一个局部chunk0”计request，零长请求没有chunk0；存在零长请求后再接非空请求时，自动生成的request id会压缩，不能当成任意含零长cu的正确映射。cu没有任何序列、即N=0时，构造torch.cat空列表还有独立Host失败边界；N>0但各长度都0与此不同。

FLA_USE_FAST_OPS在模块导入时选择exp/exp2来自libdevice或tl.math；safe_exp的正值归零语义不随之消失。源码未显式设定Triton生成的cross-pipe同步或UB容量，不能把逻辑tile表变成已确认硬件字节账；调用顺序是三个独立Host调用，跨调用stream/event与owner须由上层保持，不是一个已经证明融合的MIX kernel。

## Target verify的完整状态推进边界

固定kernel中的fla.kda_target_verify.kda_target_verify_npu是一个Triton JIT，不是同名C++/ACLNN。它将每请求固定S=cache_steps步放在同program顺序循环，tokens=B*S；q/k/v均须[1,tokens,Hq/Hk/Hv,K/K/V]，输入token数一致且可被正S整除。Hv须分别被Hq/Hk整除；a挤掉可选leading singleton后为[tokens,Hk,K]，b为[tokens,Hv]。持久池[pool,Hv,V,K]只读，中间池[scratch,S,Hv,V,K]每步存更新后的状态；两个index数组为至少B项的int32/int64，同设备。Host检查这些shape及state/snapshot dtype相同，未完整约束q/k/v/gate dtype、正head/维数、正向index容量或所有alias。

gates_are_preactivated=None时，由a为4D且b为3D的成对leading singleton推断True；一方有而另一方没有会失败。显式flag可覆盖推断，随后squeeze仅去掉值为1的首维。preactivated模式a是log-decay、b已sigmoid，直接gate=exp(a)、beta=b，A_log/dt_bias在JIT中不读；raw模式要求A_log.numel()==Hk、dt_bias[Hk,K]，逐key计算gate=exp(-exp(A_log)*softplus(a+dt_bias))，softplus阈值20，beta=sigmoid(b)。输入b为logit还是系数不能混用。scale缺省K^-0.5且必须正。

每program属于(request,value_head,V片)，q_head=hv//(Hv/Hq)、k_head=hv//(Hv/Hk)，gate沿k_head取；state=seed或负seed时零。每步先按精确路线归一化q/k，再按gate衰减VK状态，delta=beta*(v−state@k)，state+=outer(delta,k)，out=state@(scale*q_norm)，并把当前状态写对应snapshot。snapshot索引负时仅跳过快照写，仍计算out；seed索引负时零初态但后续照常递推。局部FP32状态跨step保留，不从低精度snapshot重新加载，因此BF16 snapshot舍入不会反馈给下步；返回out是V.dtype。

K=V=128路线把K拆两个64列half，q/k使用x*rsqrt(sum(x²)+1e-12)，两个half乘积先相加后做64路归约；其他维度使用x/(sqrt(sum(x²))+1e-6)，BK=next_power_of_2(K)<=256，用static_range展开S，BV=min(64,nextPOT(V))。这些norm在零/近零和舍入上不同，不可只因数学名称相同就互换。128路线autotune的4配置为BV64/128×multibuffer False/True，key仅含Hq/Hk/Hv/K/V；grid=(B,Hv,ceil(V/BV))。其他尺寸走kernel.fn绕过autotune，不把4配置当通用支持矩阵。

q/k/v/a/b及两状态池均按显式stride寻址：token=request*S+step，q/k用各token/head/dim stride，state用slot/head/v/k四stride，snapshot用slot/step/head/v/k五stride；仅A_log、dt_bias和index被contiguous，因此可消费packed QKV view和转置呈现的VK池。out是新连续[1,tokens,Hv,V]，按((token*Hv+hv)*V+v)写。seed实际载入两块或单块FP32 tile，逻辑状态payload为4*128*BV或4*BK*BV字节；额外q/k/gate向量与归约临时未固定物理分配，无显式workspace/cross-program barrier。外部snapshot容量为scratch_slots*S*Hv*V*K*e(state)，新out为tokens*Hv*V*e(v)；有意重复snapshot slot或与seed池alias会破坏并发/重复执行前提。

autotune会反复执行调用，故snapshot不得alias只读seed。应按源码建议在图捕获前warmup实际输入配置；不把这写成本次已验证的图能力。test_kda_target_verify.py定义BF16/F32状态、packed/连续view、S4/8、分组head、负seed/负snapshot、int64索引、零/近零norm、两门控及warmup后graph replay比较；这些是测试定义，本次全部未执行。test_kda_prefill_pool_layout.py以K=V=64、两条变长序列对照连续VK与转置view，脚本打印PASS/FAIL而非对每个结果抛assert，不能仅按进程退出码宣称通过。固定run_kernel_tests.sh的活动FLA列表不含这两项，不能由组级A3/950 CI或源码“A3/A5”注释推导这些旧KDA入口整个平台支持。

### 旧KDA组件的固定源码索引

| 固定文件 | 事实范围 |
| --- | --- |
| [python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_prefill.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_prefill.py) | WY/output实际dot、layout、精度与tile |
| [python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_chunk_delta_h.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_chunk_delta_h.py) | KV递推、VK池转换、guard与状态回写 |
| [python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_target_verify.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_target_verify.py) | 固定步VV、两norm/门控与stride |
| [python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py) | exp/safe_exp、元数据与对象缓存 |
| [tests/python/sgl_kernel_npu/test_kda_prefill_pool_layout.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_kda_prefill_pool_layout.py) | pool布局参考定义与打印结果边界，未运行 |
| [tests/python/sgl_kernel_npu/test_kda_target_verify.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_kda_target_verify.py) | 误差、只读池/快照及graph测试定义，未运行 |
| [scripts/run_kernel_tests.sh](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/run_kernel_tests.sh) | 实际FLA测试列表/过滤 |

## 配套知识

[分块KDA接口](../../../apis/sgl_kernel_npu/sgl_chunk_kda_fwd.md)。

## 独立旧KDA gate预激活：softplus与有界sigmoid两数学

固定kernel的fla.kda_gate.fused_kda_gate_npu不是上述verify内联raw gate的无条件别名。其签名为(gate,A_log,head_dim,gate_bias=None,beta=1.0,threshold=20.0,lower_bound=None)，返回FP32 **log-decay激活量**，不是已经exp后的衰减系数，也不对另一个beta logit做sigmoid。A_log.numel为H，hidden必须H*D，bias存在时numel必须hidden；gate先reshape(-1,原末轴)，T为其首轴，最终输出view为[*gate原leading shape,H,D]。

令u[t,h,d]=FP32(gate[t,h,d])+可选FP32(bias[h,d])，a[h]=exp(FP32(A_log[h]))，实际两条独立数学为：

| 选择 | 输出FP32 g[t,h,d] | inactive参数 |
| --- | --- | --- |
| lower_bound is None | −a[h] * (u if beta*u>threshold else log(1+exp(beta*u))/beta) | lower_bound |
| lower_bound is not None | lower_bound * sigmoid(a[h]*u) | beta、threshold不参与该body |

默认softplus分支与verify的raw gate在beta=1/threshold20、相同bias且相同输入域时可连接；有界分支不能按相同raw公式处理。常用负lower_bound使结果落在该负界与0之间，但Host未要求lower_bound为负或有限，也未检查beta正值/有限值；beta0等没有合法fallback。下游若要求已激活log-decay，应传此g而不再次softplus；若消费衰减系数，另按真实consumer执行exp，不把两种表示混用。

唯一Triton Vector launch的grid=(ceil(T/BT),H)，BT32/64/128三autotune配置，key仅H/D；BD=nextPower2(D)。每program固定head和BT个token、BD列，gate block_ptr实际shape(T,D)、stride(H*D,1)，bias masked到d<D，A_log逐head标量；store对T/D边界检查。局部主要逻辑tile是BT*BD FP32 gate/activation及BD bias，不等于编译后物理UB总量；无显式GM workspace、跨program通信或状态池原地写。输出新分配，autotune重复写同一输出没有自有输入状态累积，但不据此声称图捕获已经验证。

Host仅有上述hidden/bias元素数检查；没有input_guard、NPU/同device、dtype、连续性、Tensor实际stride、正H/D/T、输出物理布局或A_log/bias索引容量的完整校验。reshape可能复制或保留可兼容view，kernel仍按dense H*D寻址；empty_like(dtype=float32)的框架layout行为不能替代stride检查。这里保存完整可见预激活算法与边界，平台和CANN版本仍未证实，保持本页draft/platforms=[]，不创建声称已闭包的特定芯片Operator。

固定来源：[fla/kda_gate.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/kda_gate.py)。本次未执行上游、编译、真机、数值或性能测试。
