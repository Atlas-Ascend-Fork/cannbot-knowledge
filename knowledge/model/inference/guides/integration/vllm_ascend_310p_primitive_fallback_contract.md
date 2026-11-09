---
type: Guide
title: vLLM Ascend 310P原语适配：RoPE缓存、视觉Attention与递推fallback
description: 核对310P专用activation、RMSNorm、Conv3d、词表NZ、普通/MRoPE、MM Encoder及GDN参考递推的实际分支、精度与Host同步，避免把回退存在、历史310P限制或模块级缓存误当完整模型支持。
aliases:
- AscendMRotaryEmbedding310
- set_mrope_apply_rotary_slices
- AscendMMEncoderAttention310
- AscendRMSNormGated310
- fused_recurrent_gated_delta_rule_pytorch
- prepare_chunk_indices_310
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/activation.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/conv.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/fused_recurrent_gated_delta_rule.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/idex.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/layernorm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/mm_encoder_attention.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/qwen3vl_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/rotary_embedding.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/vocab_parallel_embedding.py
  role: implementation
created_at: '2026-11-03T06:03:31Z'
updated_at: '2026-11-03T06:03:31Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 310P原语适配：RoPE缓存、视觉Attention与递推fallback

## 任务与固定版本

固定Main ceac1a2，完整静态阅读`_310p/ops`10份剩余来源，将9份实际实现聚合到本卡；FLA __init__仅重导出已具独立来源的函数，作包装skip。类名仅表示专用实现，是否由模型/CustomOp实际注册选中仍须沿真实调用核对。没有运行上游、NPU、图、模型或测试，保持draft/空平台；TorchNPU、Native父类、l2norm和tensor_cache实现仅作为外部依赖，不宣称算子数值已验收。

历史[310P bringup规避卡](../../optimizations/anti_patterns/ascend_310p_bringup_unusable_ops_and_nz_layout.md)来自较早PR。固定Main已有下面的unpad调用和MRoPE缓存实现，不能把旧版本“不调用unpad”“统一强制eager”陈述自动套到本卡所有分支。普通语言Attention仍按[310P phase/Host长度合同](vllm_ascend_310p_attention_backend_contract.md)，视觉Encoder与其不是同一接口。

## 小原语替代并不意味着等价的全模型支持

| 专用实现 | 实际选择与数值边界 |
| --- | --- |
| AscendSiluAndMul310 | 最后维可被32整除才用npu_swiglu；否则按一半切开，用F.silu(left)*right。未另验偶数尾维，不能把任意宽度称为已支持 |
| AscendConv3dLayer310 | forward_oot直接调用父forward_native，避开公共Ascend Conv3d的BatchMatMulV2路线；不是本函数另实现全部卷积 |
| AscendRMSNorm310 | 有residual走npu_add_rms_norm并返回更新residual；无residual走npu_rms_norm，bias均在norm之后原位加 |
| AscendGemmaRMSNorm310 | weight按1+weight，residual先转x dtype参与加法，再将加后值转回原residual dtype；不应按普通fused residual的舍入顺序解释 |
| AscendRMSNormGated310 | 有group_size走父native；否则只支持sigmoid/silu/swish gate，按norm_before_gate决定乘gate在norm前后；无z不计算gate |
| 未量化embedding/LM-head方法 | 加载后另存maybe_trans_nz(weight)为weight_nz，apply用F.linear(x,weight_nz,bias)；仅quant_config=None替换方法，不能据此改量化层加载协议 |

如果权重在加载后再次更新，应核对weight_nz是否同storage或需要重新转换；本方法没有自动监听旧weight变化。embedding lookup与LM-head实际调用哪一个方法仍由父类与注册决定，不由本卡的F.linear一处推导全部词表行为。

## 普通RoPE与MRoPE使用不同的缓存发布合同

普通AscendRotaryEmbedding310显式拒绝out_dtype，offsets也被_rope_forward_oot拒绝。half/interleave由neox风格或override选择；head128且cache宽128优先npu_apply_rotary_pos_emb，partial rotary_dim64也走该接口，其余partial/完整宽度走旧_npu_rotary_embedding。partial路径只改rotary前缀，再拼回pass-through尾部，不能对整个head重复旋转。

普通路径把本实例cos_sin_cache移到query的device/dtype；但npu_apply路线用公共get_cos_and_sin_slice取得的另一组视图。草稿class flag为真时先update_cos_sin(positions)，默认false。必须证明runner/草稿及时发布了与当前positions一致的切片，移动本实例cache本身不完成这项发布；class级flag也不提供并发请求隔离。

MRoPE set_mrope_apply_rotary_slices接受一维token位置，或[3,T]的T/H/W位置；后者要求mrope_section，并按interleaved helper或split后取相应轴片段合成。cos/sin再各自复制一份扩到完整rotary宽，变为[1,T,1,D]连续视图。half/interleave的旋转风格与T/H/W片段交错是两项不同约定。

模块级_mrope_cos_slice/_mrope_sin_slice第一次按max(capacity_tokens,T)分配，其后只向活动前缀copy，不检查后续容量增长、device/dtype或rotary宽度变化并重新分配。runner helper查找第一个AscendMRotaryEmbedding310并缓存到runner，使用runner.max_num_tokens作初始容量；不能从这个缓存推断多模型、多线程或异构层天然隔离。每次模型forward前必须刷新，不能用相同T作为内容未变的证据。

MRoPE forward未初始化则明确报错，rotary_dim64/128走npu_apply，其他宽度走ApplyRotaryEmb.forward_static的Torch路径；partial同样拼回未旋转尾部。Torch fallback只取当前切片的half宽cos/sin，正确性仍取决于前面的轴合并、布局和真实父API。图重放应核对地址稳定以及每轮活动前缀内容，不能只看一次分配成功。

Qwen3VL的rot_pos_emb_310另将pos_ids以non_blocking=False搬到device，再索引cos/sin；源码标注避免RC异步H2D与后续索引竞态。这是该函数的明确同步选择，不能将其无条件改为异步来优化CPU时间，也不是整个视觉pipeline已无竞态的证明。

## 视觉MM Attention：实际函数没有使用注释中的CPU cache

AscendMMEncoderAttention310把Q/K/V整理为[token,head,dim]，按Q/KV head整数比repeat_interleave K/V；真实整除条件、重复后的head数与仍传入的num_kv_heads属性必须按TorchNPU接口复核。仅64<head_size<128时补到128，输出再裁回；64和128不进入这一补齐分支，其余宽度也未被本函数逐一验证。

scale_value直接设head_size**-0.5；构造传入的scale虽给父类，实际unpad调用用本地scale_value，适配自定义缩放需核对这一差别。函数没有把max_seqlen或sequence_lengths参数转给设备算子。

模块注释写了seq_lens_cpu_cache，但forward每次实际执行torch.diff(cu_seqlens).to('cpu')，未读写该global cache；缺cu_seqlens时按均匀q_len构造CPU累计长度。不能根据注释宣称每层免D2H、跨层缓存已经生效，也不能在图捕获中忽略这项Host读取。这里只生成一套Q差分长度，不提供任意每请求cross-attention Q/KV长度的独立映射。

接口探测仅用hasattr(_npu_flash_attention_unpad_v2)，有符号就调用v2并传kernel_type=2，否则调用旧unpad。源码的TorchNPU 2.10.0注释不是当前安装版本或实际数值结论；符号存在也不证明目标SoC/shape支持。输出按输入是否四维恢复[b,s,h,d]或[b,s,h*d]并contiguous。该类没有公共Encoder graph manager的任务更新/Host累计终点逻辑，不能把[普通Encoder图合同](vllm_ascend_encoder_aclgraph_lifecycle.md)直接搬到此专用实现。

## GDN Torch参考：accepted选择初态，不截短当前query

fused_recurrent_gated_delta_rule_pytorch处理q/k[B,T,H,K]、v[B,T,HV,V]、state[N,HV,V,K]，HV须能按整数倍扩展相关head。变长模式要求B=1，按cu_seqlens逐序列、逐token循环；item/tolist等Host标量读取不适合作为无需同步的高性能kernel替代。输出先zeros_like(v)，空序列跳过。

有initial_state时按inplace_final_state决定复用还是clone，否则按推断pool大小新建state，dtype沿q。num_accepted_tokens仅在有初态且二维索引时选择accepted-1的resume槽，不裁剪当前序列token数；一维state索引只按seq取槽。没有显式拒绝accepted0对应的负列索引，caller应提供合法接受数与索引，不能把Python负索引语义当协议缺省。

每token先把q/k转FP32再可选l2norm，q乘K^-0.5；state可乘exp(g)，再计算delta=v-sum(state*k)，可乘beta，更新state+=delta外积k，输出sum(state*q)。g/beta缺省分别不衰减/不加beta；beta可按head或head×V广播。输出转v dtype，每步state按其pool dtype写回，不能等同于全序列始终保存FP32历史。

初态索引负值会跳过该序列并保持零输出；写回索引负值只跳过存储，当前token输出仍已计算。正索引越pool显式IndexError，序列共用或重复槽的依赖须按遍历顺序分析。本函数不是原生NPU实现、也没有由本次执行成为Golden；验收层差别见[GDN数值证据](../bringup/vllm_ascend_310p_gdn_numerical_validation.md)。

idex.py的chunk indices用num_chunks.tolist逐序列构造arange，依每段0的位置累积推请求号；全空输入、空序列混入或非法chunk_size没有在helper完整校验。chunk offsets则为[0,num_chunks]的cumsum。tensor_cache来自Native依赖，本卡未证明其失效条件或输入原位变化安全性；分块索引和持久state应与本轮真实cu_seqlens一起核对。

新模型先锁定实际注册、dtype/残差舍入、head与rotary维、缓存发布/容量、Host同步以及state索引协议，再比较eager与目标图路径。源码的fallback存在和张量shape一致均不足以证明整模型、量化或性能已适配。
