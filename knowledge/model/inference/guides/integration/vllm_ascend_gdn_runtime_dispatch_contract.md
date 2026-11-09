---
type: Guide
title: vLLM Ascend GDN执行接入：后端分派、索引与状态布局
description: 适配GDN执行层时核对投影和卷积phase、beta激活、FLA/CANN/chunk前提、state行与布局及connector顺序，区分分派测试和真实dtype约束。
aliases:
- GDN执行接入
- _get_fla_gdn_prefill_op
- _probe_fused_chunk
- _flatten_recurrent_state_indices
- _rearrange_decode_qkv
tags:
- task.implementation
- topic.model_adaptation
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/gdn.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fused_gdn_gating.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/chunk.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/fla/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_recurrent_state_indices.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_decode_qkv.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_layout.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_mixed_batch.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_chunk_meta.py
  role: evidence
created_at: '2026-10-31T11:26:02Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: "2026-11-04T02:54:15Z"
---

# vLLM Ascend GDN执行接入：后端分派、索引与状态布局

## 任务与证据范围

为新GDN模型接入实际执行层时，按投影、卷积、gate、prefill/recurrent分派、state写回和输出顺序核对。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，主来源ops/gdn.py915行；本批13份全文及DeviceOperator选定函数只作数据阅读，未导入上游、运行测试、torch.compile、NPU probe或模型。整项硬件交集未知，保持draft/空平台。

元数据生产先沿[GDN字段接入](vllm_ascend_gdn_metadata_builder_contract.md)核对；本卡补实际consumer的限制。Native父类、custom-op注册、配对ABI和310P core未闭合，不能从同名类或CPU fixture推出支持。版本身份见[框架记录](../../concepts/frameworks/vllm_ascend.md)。

## 输入、profile与输出

forward按层属性选择独立qkv/ba/z投影、非交错qkvz split或GQA交错的fused split。b/a经模型split_ba或chunk(2)，再contiguous。创建全0的[T,local value heads,value dim] core buffer，调用Native qwen_gdn_attention_core后执行norm(core,z)与out_proj；可选output仅复制有效T行，返回值仍为out。

_forward_core在metadata为None时直接返回，forward的全0缓冲用于profile路径；metadata为dict但缺本层prefix时直接索引，不沿GLM KDA的缺层跳过逻辑。不能把两种“没有metadata”混为一种安全空批协议。

connector的wait和compute记录放在custom op内部，随后读取self.kv_cache，使延迟收到的conv/SSM state对本层可见。状态推进和输出合并后调用maybe_save_kv_layer_to_connector；该调用顺序不证明异步传输已完成。

## state索引与QKV布局

_normalize_causal_cache_indices将一维来源contiguous，或将矩阵首列contiguous；其他维度拒绝。卷积的每请求vector与recurrent按token展开的state IDs不是同一接口。

_flatten_recurrent_state_indices对一维来源取[:total_tokens]，可保留strided view；二维完整均匀槽直接reshape/contiguous。ragged模式要求query_start_loc，query长度裁到0..num_slots，经累计边界和searchsorted为每个token映射对应请求/槽位。输出长度由调用者的total_tokens给定，不能把局部clamp当完整输入校验。

_rearrange_decode_qkv分别split q/k/v，再各自contiguous().view(1,T,H,D)，不先torch.cat重建packed数据。单token可能保留alias，多token或strided输入仍可能复制；本卡没有测得零拷贝或时延收益。

prefill conv只有Q/K与V的每head维度相等（`head_k_dim == head_v_dim`），且该共同维度能被16整除时输出head-first；这里不要求`num_k_heads == num_v_heads`。卷积head总数另按`(2*num_k_heads+num_v_heads)//tp_size`组织。_split_head_first_conv_output沿head维拆分，再返回[1,T,H,D]视图。其他布局使用flat来源与原rearrange。head counts、每head宽度、TP分片和物理stride须分别核对。

## 卷积的phase与gate合同

普通decode与prefill混批、PCP1时，conv分别处理decode前缀UPDATE与prefill尾部FN，连同query offsets、state rows、initial-state mask、投影和gate一起切片。仅切tensor不切state/offset会错位。spec UPDATE另外传accepted与max_query_len=K+1；普通decode为1。

公共GDN卷积null_block_id=0，prefill的PAD_SLOT_ID和fresh history按实际参数传递；这与GLM staging用request count作null是不同consumer，不能套统一index0修法。PCP>1另有W-1历史提取和rank尾部all-gather，当前只读调用链，没有通信结果。

DeviceOperator.fused_gdn_gating输出g为FP32、beta为sigmoid(b)且回到b.dtype，shape均[1,T,H]。x=a+dt_bias，g=-exp(A_log)×softplus(x)，softplus beta参数默认1、threshold20。GDN后续recurrent消费已激活beta，不照搬KDA raw-beta再激活。

gate wrapper与Triton源码99行只用于确认调用、dtype和公式；kernel容量、调度、数值与真实性能仍需完整算子分析。

## 后端选择分三层核对

| 层次 | 固定源码条件与限制 |
|---|---|
| _get_fla_gdn_prefill_op | lru_cache(maxsize=1)导入FLA fla_npu.ops.ascendc.chunk_gated_delta_rule_fwd，仅ImportError返回None；导入失败结果也会缓存 |
| _supports_host_metadata_prefill | profile允许FLA且导入成功，或内置CANN探针成功；不检查本轮activation dtype |
| runtime FLA | q为BF16、PCP1、FLA capability和导入均满足 |
| runtime CANN fused | 未选FLA、q为BF16、非CPU、PCP1、_probe_fused_chunk成功 |
| 其余 | 调用chunk_gated_delta_rule，仍必须满足其真实入口约束 |

_probe_fused_chunk会实际发起最小NPU算子并synchronize，结果按类缓存；此处没有执行。一次BF16/T64/head1/D128 smoke也不是全shape、全软件栈验收。源码A5不支持的TODO注释没有对应硬编码拒绝分支，不把注释升级成支持矩阵。

HardwareProfile对A2/A3/A5列有FLA_GDN_PREFILL；310P走兼容patch。capability只表达窄合同，仍需模型、dtype、shape、安装产物和运行条件，不能因此给本卡填满硬件平台。

## 回退路径仍有强制前提

真实chunk_gated_delta_rule要求q/k/v同dtype，明确assert拒绝FP32，beta必须3D；可变长输入要求B=1、初态数等于len(cu_seqlens)-1。head_first=True会raise DeprecationWarning对象，不能依赖其后转换继续执行。

test_non_bf16_prefill_falls_back_to_triton_pipeline_with_strided_ssm_cache使用FP32 fixture，但替换了整个chunk函数；它证明分派选择，不证明FP32可执行。FP16也不能仅凭未被入口assert拒绝就标为已验证。

所谓Triton pipeline仍在chunk内部调用torch.ops._C_ascend的h/o算子，部分中间张量转BF16；它不是无扩展或CPU执行替代方案。模型dtype、内部算子dtype与返回到q.dtype要分别记录。若问题落在本地分块数学或packed元数据，继续按同一ceac的[FLA分块执行合同](vllm_ascend_fla_chunk_state_contract.md)核对cumsum、KKT、solve、WY、chunk前state与输出O；该入口不替代外部FLA/CANN二进制或实际DeviceOperator派发的验收。

fallback先按有效state IDs选行，VK→KV transpose/contiguous，清fresh请求初态，再调用chunk，最终KV→VK、转回state dtype并只写所选pool行。FLA和CANN同样先gather、后scatter；未选行必须保持原值。

## DeviceOperator与分块元数据

Base的FLA包装外部norm q/k，传BNSD、KV state、state_v_first=False、use_exp2=False、use_qk_l2norm=False。A5包装按输入连续性选BNSD/BSND，保持VK state、state_v_first=True、use_exp2=True且kernel内qk norm。这些flag和layout应整体匹配，不能只交换一个参数。

两者都按keep_meta压缩空段并恢复未参与段初态。DeviceOperator在模块导入时按profile实现族选择；这里仅有界读取相关方法，没有触发检测或设备初始化。

chunk消费host tuples与六项可选device字段；缺host tuple时可能从device tensor调用tolist。已有tuple的mock测试禁止tolist，不代表所有Host-only字段回退、H2D与同步路径均闭合。各leaf helper和实际shape仍需追踪。

PCP递推为s_i=s_local_i+Phi_i@(s_prev-s0)，必须减原初态避免重复贡献。actual_num_decodes优先取prebuilt metadata；rank>0只改prefill尾部的rerun初态。CPU测试替换collective/kernel验证公式，不是HCCL实测。

## 接入验收和交付

已读27个测试函数定义覆盖索引、QKV布局、mixed phase、FLA包装、权重和connector；没有执行。先验证请求/token坐标、selected/unselected state、fresh/history、输出token顺序，再在目标环境测实际dtype、prefill/decode/spec、PCP、eager/graph和连续步状态。

Agent应交付投影布局、conv sentinel、gate激活归属、后端各层条件、state layout及gather/scatter所有者。失败恢复匹配模型、builder、权重和完整状态，再验证已确认的基线；不以移除dtype guard、统一padding或测试mock代替兼容性证明。卷积重载问题另沿[注册权重诊断](../../runbooks/precision/vllm_ascend_gdn_registered_conv_reload.md)处理。
