---
type: Guide
title: vLLM Ascend RoPE接入：缓存所有权、图地址与旋转分派
description: 核对RoPE派生buffer的named_buffers所有权、first-wins全局缓存和MLA固定地址，区分Q-only的out_dtype丢弃、offsets未传递、FP8头宽推断、Gemma4比例旋转、M-RoPE三条件分派及ApplyRotaryEmb的配对与透传尾部，保留图与真机数值待验。
aliases:
- get_cos_and_sin_mla
- _record_cos_and_sin_cache_interleaved
- AscendRotaryEmbedding.forward_oot
- AscendMRotaryEmbedding.forward_oot
- AscendApplyRotaryEmb.forward_oot
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/rotary_embedding.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_rotary_embedding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_apply_rotary_emb.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_rotary_flat_gather.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/register_custom_ops.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/544f182d9f0c9bfe8bd7645525951d5e3692a542/vllm/model_executor/layers/rotary_embedding/common.py
  role: constraint
created_at: '2026-11-03T02:07:12Z'
updated_at: '2026-11-03T02:07:12Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend RoPE接入：缓存所有权、图地址与旋转分派

## 任务与来源边界

本卡用于新模型的普通/比例/多模态RoPE、Q-only草稿、部分head旋转及sleep后输出变化的接入诊断。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取rotary_embedding.py及三份直接UT；另读custom-op注册/fake、Worker备份恢复与硬件能力的明确片段。ApplyRotaryEmb父类只读取Main实际paired544的common.py113–213行，未以独立5df快照替代配对版本。

这里闭合的是Python缓存所有权和选定Host调用合同；Triton设备体、torch_npu实现、全部原生父类、注册工具的alias处理和图runtime仍未闭合。未导入或运行上游、UT、模型、NPU或图，不宣称全平台支持、完整Operator或性能收益。

## 派生位置表也必须有可恢复的所有者

`_record_cos_and_sin_cache_interleaved`把合并表按cos/sin拆成重复后的交错存储。全局`_cos_cache`与`_sin_cache`同时作为构造模块的`_rope_derived_cos_cache`、`_rope_derived_sin_cache`注册，persistent=False；全局引用与buffer是同一Tensor对象。`_cos_sin_flat`是同一存储的连续view，偶数行为cos、奇数行为sin。

Worker在Level2进入allocator sleep之前对`model.named_buffers()`逐名CPU clone；weights阶段wake后copy回当前同名buffer。由此，派生位置表不能仅藏在模块全局变量中：地址仍有效不代表被丢弃/重映射的内容已恢复。该实现注释说明了此类历史所有权问题；本次没有复现它或测量sleep后数值。

persistent=False使buffer不进入state_dict，不能据此认为它不在named_buffers、无需备份或可以任意重建。图捕获后替换Tensor或storage也不同于原地址copy。完整sleep、tags和图重捕获顺序见[Sleep生命周期](vllm_ascend_sleep_wakeup_lifecycle.md)，权重reload另见[配对原生加载链](vllm_ascend_paired_native_weight_loader_contract.md)。本卡不由注册标志推断全部reload实现都会保留内容。

## 全局缓存不是按模型配置自动分键

三类注册的覆盖规则不同，接入多模型、target/draft或失败重试时要核对实际构造顺序。

| 入口 | 固定Main的行为 | 接入检查 |
| --- | --- | --- |
| `_record_cos_sin_cache` | 合并表首次非None后直接返回 | 后建模块的base、dtype或旋转宽变化不会在这里自动替换旧表 |
| `_record_cos_and_sin_cache_interleaved` | 任一半表已存在就返回 | 不能假定每个模块都拥有一套新派生buffer |
| `_record_cos_and_sin_cache` | 覆盖两张半表，并清空flat view | DeepSeek连续表路线不能继续读上次交错flat表 |
| `set_cos_and_sin` | 任一持久工作buffer已存在就返回 | 这不是按模型、dtype、device或容量重新校验的缓存工厂 |

MLA工作buffer按max_num_batched_tokens分配为[T,1,1,R]；普通非VL且有RoPE时为[1,T,1,R]，R取head宽并应用partial_rotary_factor或rotary_dim。参数max_num_reqs与decode_token_per_req在此函数体未参与容量计算，不能按它们推导已覆盖所有批次上限。

`update_cos_sin`从全局合并表按position取行，写入普通持久buffer并发布切片；没有工作buffer时直接返回，`get_cos_and_sin_slice`自身不保证返回值已初始化或属于当前请求。调用方仍须约束position范围、token容量、旋转宽和初始化时序。RFork失败恢复维护特定全局快照，见[RFork加载接线](vllm_ascend_rfork_processed_weight_loading.md)，不能把它推广为任意模型构造都自动隔离。

## MLA取表：临时返回不能冒充图内固定地址

交错注册从连续flat表按2×position和2×position+1取行；连续注册直接索引两个半表。代码给出的动机是避免对strided半表逐次索引时物化整张表，本次没有测量实际分配或速度。两路布局互斥，不应删掉其中一路作为“统一优化”。结果增加两个轴为[T,1,1,R]。

use_cache=False返回本次gather结果。use_cache=True且持久MLA宽匹配时，先copy进预分配buffer，再返回其前T行；固定地址依赖该buffer和存储继续存活。若buffer未建或宽不匹配，函数仅warning并返回临时cos/sin，源码明确说明这不安全于ACL graph capture；它没有在capture内强制抛错。因此warning后结果存在，不是图回放安全的证据。

NoPE工作buffer末维为0时提前返回零宽切片，不把indexer的非零RoPE宽写进零宽MLA。它也不是所有NoPE/索引分支的统一校验。新模型必须分别确认attention与indexer的R，以及empty、重复和边界position。

## 普通wrapper、Q-only与FP8不是同一合同

`AscendRotaryEmbedding.forward_oot`允许is_neox_style_override覆盖实例值。仅draft上下文、method=mtp且enable_sp同时成立时all_gather positions；不满足三条件时没有该通信。这里没有证明query/key在所有调用者中均已按同一布局恢复。

key存在时走`torch.ops.vllm.npu_rotary_embedding`，可显式传out_dtype。key=None时构造throwaway key：Triton路径为零head空Tensor，非Triton路径为一个实际head，调用本地helper后返回(query,None)。该分支**没有传入out_dtype**，不能因wrapper接受FP8参数就认为Q-only输出已成为FP8。

普通wrapper的offsets形参也未传入底层调用；DeepSeek的forward同样未消费offsets。相反，直接调用`rope_forward_oot`且offsets非None会抛NotImplementedError。YaRN/Gemma4的测试确认参数传给了普通wrapper，并不证明最终offset已用于位置计算。需要offset的新模型必须检查实际callee，不能靠签名兼容验收。

本地helper只接受out_dtype=None或float8_e4m3fn；FP8要求Triton，直接传key=None会ValueError。非FP8的直接key=None也不符合其函数体要求：它会读取key.shape；Q-only支持由外层dummy key实现。FP8头宽按每token的query/key总宽推断，任一不整除配置head_size时尝试key_width作为head_size，再要求query_width可整除，并将rotary_dim夹到head_size。该推断不是任意GQA布局的证明，空token、零key宽、非contiguous view和新模型宽度都需独立核对。

无Triton时helper将q/k contiguous后展平，调用npu_mrope；NeoX模式字符串为half，另一模式为**interleaved**。ApplyRotaryEmb及自定义Partial RoPE使用的**interleave**是另一个接口的拼写，不能互换。

选定custom-op fake只检查输出dtype，并返回原q/k或empty_like的FP8输出；注册声明mutates_args=[]。fake没有执行offsets、head宽、Triton可用性或真实设备检查，故fake/图追踪成功不能证明真实调用成功；实际kernel的mutation/alias与编译器处理仍需沿具体实现验证。

## 派生类的cache构造与M-RoPE分派

Gemma4保留原生Gemma4构造和inv_freq处理，以全head宽cache表达比例旋转，未旋转pair由cos=1、sin=0保持。它只共享Ascend普通forward；不能因forward相同就替换成普通RotaryEmbedding构造。UT定义了全宽cache和未旋转pair检查，但没有在本次执行。

YaRN把beta_fast/beta_slow、mscale/mscale_all_dim、attention_factor、truncate传给父类；仍接受的extrapolation_factor、attn_factor、apply_yarn_scaling未进入这里的extra_kwargs。签名参数存在与参数实际生效应分别核对，尤其升级原生版本时。DeepSeek重建FP32频率再转目标dtype的位置表，并单独注册连续cos_cached/sin_cached；非NeoX输入先把相邻pair重排成half布局，再以NeoX调用底层。输出shape相同不证明配对顺序仍是原模型要求。

当前Main M-RoPE选择如下，与[旧PR选型规则](../../optimizations/rules/mrope_triton_ascend_vs_npu_mrope_decode.md)的历史版本分开消费：

- 只有HAS_TRITON、positions.ndim==2、mrope_interleaved三条件同时成立，才走本类forward_triton。
- 否则mrope_section不等于[16,24,24]时调用原生父类forward_oot；该父类的完整行为不在本卡内。
- 剩余路线才调用npu_mrope，1D position把section改成[0,0,0]；必要时移动/转换cache到query的device/dtype，可能产生新Tensor。

forward_triton要求key存在，每次先将self.cos/self.sin设为None，再按positions gather并contiguous，不能按属性存在就视为跨请求复用。query第0维大于65535时会把进程环境TRITON_ALL_BLOCKS_PARALLEL设为1，函数内没有恢复；这是固定实现的启发式保护，不是所有形状或并发模型的安全/性能保证。当前版本条件和进程副作用不能由旧benchmark推导，未复测其收益。

## ApplyRotaryEmb：配对、部分维与精度

paired544父类preprocess对3D x加batch轴；enable_fp32_compute时把x/cos/sin升为FP32，postprocess恢复原rank和dtype。Main据cos末维计算R=2×cos宽，拒绝R>head_dim；未在这里完整检查所有cos/sin广播、长度和模型配对语义。

NeoX采用前后半配对，cos/sin各自cat重复；GPT-J/Kimi相邻pair采用repeat_interleave(2)。两者虽输出shape相同，频率与维度配对不同。非NeoX且缺少FUSED_ROTARY_MUL_INTERLEAVE能力时用父类静态公式，只旋转前R维；其余路径调用npu_rotary_mul，部分旋转后cat原尾部，再恢复rank/dtype。能力只代表该精确调用合同，不能从硬件名称推导全部RoPE支持。

固定UT用复数乘法参考、patched npu_rotary_mul与能力档案，定义了3D/4D、strided、FP32/BF16、全维/部分维和兼容路线的比较及尾部不变断言。这是可选验证设计，不是实际NPU kernel或图已通过。自定义原位算子的mode、slice、Host tiling另见[Partial RoPE Host合同](vllm_ascend_partial_rotary_host_contract.md)，不能把npu_rotary_mul的测试当作该自定义算子的测试。

## Agent应收集的最小证据

记录实际Rotary类和配置、target/draft构造顺序、position的rank/范围/offset、q/k head宽与R、配对方式、cache dtype/device、全局表来源、derived buffer owner与data_ptr。对use_cache=True保存capture/replay前后的持久地址和内容，对sleep Level2保存named_buffers名单及weights恢复阶段；不要仅看指针有效或无异常。

分别对Q-only/有key、FP8/普通输出、比例旋转尾部、M-RoPE三条件、动态token容量、重复/空position和sleep/wake做模型参考比较，再检查图/eager、真实分配与端到端时延。发现临时缓存warning、错误配对、offset丢失或first-wins表不符时，先暂停该优化并回到已确认的模型参考，不通过改shape、清全局变量或吞warning宣告正确。

三份UT本次仅全文读取：普通wrapper测试大量mock构造/底层算子；flat-gather测试定义相同存储、重复/空/边界position和两路等价；ApplyRotary测试使用替身kernel。它们均未在本次执行；真实设备数值、图地址、全部父类及性能继续保留未知。
