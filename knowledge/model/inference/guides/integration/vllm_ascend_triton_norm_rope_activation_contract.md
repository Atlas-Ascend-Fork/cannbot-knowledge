---
type: Guide
title: vLLM Ascend Triton归一化、RoPE与激活融合合同
description: 比较Q-RMS、QKV/TP/MRoPE、MiniMax缓存融合、SwiGLU量化和Step激活的实际形状、舍入、输出别名及文档漂移，供Agent选择融合路径。
aliases:
- triton_q_rms
- rope_forward_triton
- rope_forward_triton_siso
- swiglu_quant
- swiglustep_forward_triton
- minimax_qknorm_rope_cache
tags:
- task.implementation
- task.optimization
- topic.attention
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/rms_norm.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/activation/swiglu_quant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/activation/swiglustep.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/layernorm_gated.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/linearnorm/fused_eh_norm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/linearnorm/split_qkv_rmsnorm_mrope.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/linearnorm/split_qkv_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/linearnorm/split_qkv_rmsnorm_rope_simt.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/linearnorm/split_qkv_tp_rmsnorm_rope.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/rope.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/msa/minimax_qknorm_rope_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/mul_add.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/muls_add.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/fused_eh_norm.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/minimax_qknorm_rope_cache.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/rms_norm.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/rope.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/rope_siso.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/split_qkv_rmsnorm_rope_vnorm.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/swiglu_quant.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/swiglustep.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/layernorm.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/rotary_embedding.py
  role: implementation
created_at: '2026-11-03T05:54:55Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Triton归一化、RoPE与激活融合合同

## 来源和使用条件

固定 ceac 的13个Python程序完整AST结构与8份算子文档。AST不执行导入、JIT或kernel，文档测试/性能叙述不是本次测量；平台能力仍由实际profile、接入gate与设备证据共同确定。本文不把同名函数、fake实现或Triton可导入等同数值/图验收。

## RMS与Gate归一化

`triton_q_rms` 将[batch,heads,dim]展平，拒绝dim>2048；BLOCK_M按运行时UB减6144字节、dtype宽度与5/7倍活跃数据估算，取每core batch与资源上界中较小值向下2幂，最低1。只支持2/4字节元素；没有weight。其kernel直接以载入dtype的x计算x*x，再归约，与batch_invariant/rmsnorm.py的显式FP32两遍加权RMS是不同实现。docs/rms_norm.md中“同一kernel”概括不能代替该区别。

layer_norm_fwd_npu按group_size分组，可选bias、RMS或LayerNorm、门控前/后归一。norm_before_gate=False先乘z*sigmoid(z)再统计；True在归一+weight/bias后乘，次序不交换。只校验末轴stride1及部分shape，group必须整分；每组上限65536/元素字节，BLOCK_M=64。mean只LayerNorm有，rstd按group×row存FP32；out存在不证明其device/dtype已完全校验。

fused_eh_norm对positions==0只清embedding输入，不清previous_hidden，各自独立FP32 RMS+独立weight后拼[N,2H]。H而非padding宽度作为均方分母，row stride分别传入，channel/weight/position连续性与同device由调用者满足。文档列H513和GLM形状、24组合、输入保留及不同dtype容差；这些是来源验收设计，未在此重跑或扩成图支持。

## QKV融合并非同一个数值合同

| 变体 | 实际归约/位置表/输出 | 适配重点 |
| --- | --- | --- |
| qkv_rmsnorm_rope | Q/K按head RMS，norm结果先转BF16再NeoX RoPE；按positions在kernel gather表；V只复制 | 固定约85KiB UB模型、bias开关只由q_bias是否None决定，K bias也须配齐 |
| qkv_rmsnorm_rope_simt | 先独立SIMT gather FP32 cos/sin，再在FP32 norm+RoPE，末尾存回 | 不是普通版本无损换调度；额外buffer/launch与舍入位置不同，partial token mask也需核验 |
| triton_split_qkv_rmsnorm_mrope | T/H/W三个token表区按section或interleaved规则组合；可拆每head交错Q/gate，V原值 | cos/sin是预先按token排列的三组表，不是普通全局position cache；partial rope只替换前缀 |
| split_qkv_tp_rmsnorm_rope | 每rank对本地整个Q/K宽度求均方，TP all_reduce后再乘1/tp_world，广播至各head归一与RoPE | 不是每head独立RMS；要求各rank分片宽度与统计权重一致，TP参数与真实组相符 |

这些wrapper输出空分配和fake实现仅维护形状；fake不检查完整dtype/布局或执行collective。TP路径处理空token直接返回，其他入口不都有同等empty guard。维度整除、even RoPE、同NPU、positions范围、Q/K权重与完整stride由调用链逐项保证，不能从宽松Python签名推导接受任意输入。

MRoPE gate非空时输入按head的[Q,gate]交错展开，不能直接当全行Q后接全行gate；mrope_section长度与分区须同模型。普通QKV的cache gather存在padding行读取条件与SIMT预gather的输入load遮罩差异，新的尾batch和非法position需专项验证，不能只检查最终store mask。

docs/split_qkv_rmsnorm_rope_vnorm.md描述另一种Q/K/V都归一、V无weight/no-RoPE的Gemma4融合，不能用上表“V复制”入口替代。来源要求bf16、compiled pass与单token UB可容纳，A2验证、A3未验证、950无SIMT vnorm；共享KV层不匹配，交替shape需不同pattern key。性能意图与文档测试定义不提供本次运行结果。

## RoPE原位、SISO和FP8输出

普通rope_forward_triton对连续Q/K原位旋转，非连续则生成副本，必须消费返回值；RoPE外尾部保留。支持NeoX半分和GPT-J偶奇两种布局，以及positions+原始cache或预选cos/sin；同时传两套时实际优先cache，不按文档“严格二选一”假定会拒绝。

当前源码按UB的50%预算、活跃tensor数量与pad_rope_dim自适应head block，上限NeoX64/GPT-J32，不是docs里“head_dim>=256固定降16”。当前sin起点为rope_dim//2，不是文档旧述pad_rope_dim//2；不能照旧描述强加所有cache模式RoPE宽度必须2幂的限制，实际padding/非2幂仍须目标编译器验证。

SISO一次处理全部padding heads，没有普通版head分块；它在默认-1推断之前计算pad_rope_dim，因此调用方需显式有效rope_dim。函数实际返回一个tensor，类型注解的tuple不构成返回ABI。large heads×rope宽度必须单独预算UB。

FP8必须显式out_dtype=float8_e4m3fn、positions+cache、rope_dim与NeoX；输出独立缓冲，先FP32旋转，再±448饱和后直接E4M3转换，非RoPE尾也转换，固定scale=1不返回动态scale。wrapper检查输出dtype/连续性，但未完整检查外部输出shape/容量、正rope_dim或所有device一致，不能把文档要求误写成代码已严格验证。文档将该FP8执行路径限定950，不扩展到A2/A3。

## MiniMax融合Cache写入

minimax_qknorm_rope_cache对Q/K/index Q/index K做Gemma RMS（乘1+weight），FP32统计后先舍入BF16，再partial NeoX RoPE；主K写cache前再按模型dtype舍入。仅Q/index Q物化返回，K/V/index K直接用各自实际block/token/head stride写cache，主与index块长可不同。

packed可含全部投影或单独index_packed；BF16输入、相同head维，kernel wrapper允许64/128/256，而文档模型接入guard给128与最多262144含padding token，不能混成算子已验证全维度。负slot或超出num_actual_tokens不写cache，但仍计算padded query；正slot容量/重复目的地由调用者保证。FP8主/索引cache各自±448截断，不进行动态scale。

num_actual_tokens是do_not_specialize运行时标量，stride保留constexpr；文档的fresh JIT和九种layout回访测试分别验证请求长度变动复用与布局新增编译，不等于捕获bucket/已capture标量自动变化。文档夜间对照交替五样本、20次capture调用×10replay排除编译，不提供通用微秒阈值；这些仍需实际产物证明。

## SwiGLU、Step与简单融合

swiglu_quant仅严格检查group_list_type=0/1与INT32/64元数据dtype。实际行数取最后累计count或counts之和，未核对等于分配S；未处理行保留未初始化。量化scale=maxabs/127无zero guard，激活结果除scale后先转输入dtype再饱和INT8；need_quant=False返回的scale未写，不可消费。sigmoid前显式FP32转换为Triton Ascend3.6 BF16 exp限制的规避，不是原生BF16 sigmoid能力。

swiglustep严格在silu(gate)之后只做上界min(limit)，up双边clamp再乘；不是clamp gate再silu。wrapper使输入连续，检查偶数末维和半宽32字节对齐，默认limit7；limit/core/列宽constexpr、M运行时，改变limit可能改变特化。来源A2/A3/950与graph描述仍以实际版本测试为界。

mul_add.py与muls_add.py包含同一x*scale+y扁平kernel，wrapper只断言shape一致，用末维选block≥1024；没有通用stride支持或空batch保证，不能把任意非连续视图当逐元素逻辑等价。重复实现不形成两项独立性能证据。

## Agent验证顺序

先按模型的归约轴、Gemma权重语义、V是否归一、RoPE布局/舍入、TP统计与cache side effect选择入口，再验证dtype/strides、零值、非2幂、尾batch、偏置成对、partial RoPE、负/重复slot及输出别名。比较数值、cache未触区域与编译特化次数后才测launch/UB/HBM和端到端收益；文档容差与来源设备记录是验证起点，不是本次通过结论。


## 3164 Python 入口补充：activation 传播与无 key 的 RoPE

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

AscendRMSNormGated现在将self.activation传到LayerNormFn，再传layer_norm_fwd，不能沿ceac入口假定任何activation都被忽略；实际Triton是否实现该值要同时核对新kernel，传参本身不等于所有activation支持。MRotaryEmbedding的Triton入口另传is_neox_style，避免只按interleaved flag推旋转配对。

positions一维且key=None时直接RotaryEmbedding.forward_static，以query承载DFlash fused context keys，不分配dummy key；二维MRoPE等其他分支仍断言key存在。不能把key optional注解推广为全部positions布局无key可用。
