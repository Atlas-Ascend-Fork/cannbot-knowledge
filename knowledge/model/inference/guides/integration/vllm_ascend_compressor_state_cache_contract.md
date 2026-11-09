---
type: Guide
title: vLLM Ascend DeepSeek 压缩器接线：AscendCompressorStateCache 与 V4.1 环输出
description: 解释 AscendCompressorStateCache、Compressor 和 DeepseekV41Compressor 的接入，区分 V4 C4/C128 与 V4.1 C2/直接投影；核对 FP32 状态、page padding、cache/state 元数据、设备等待及环输出，保留 Native 后端和版本边界。
aliases:
- DeepSeek 压缩器接线
- AscendCompressorStateCache
- AscendCompressorMetadata
- DeepseekV41Compressor
- prepare_ring_compressor
- pool_projected
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v4/compressor.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/compressor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_deepseek_v4_compressor.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/models/deepseek_v4/compressor.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-10-31T21:29:10Z'
updated_at: "2026-11-04T02:54:15Z"
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DeepSeek 压缩器接线：AscendCompressorStateCache 与 V4.1 环输出

## 接入任务与三个实现边界

新模型接入压缩缓存时，先分清“谁拥有投影权重”“谁生成请求元数据”“谁保存状态”“谁最终写回 KV”。本卡描述 Python 框架接线，不是完整 Device 算子卡。算法与 cann-recipes-infer 的 C4A/C128A 原理复用 [Compressor 概念](../../concepts/kernels/compressor.md)，不能把那份来源的量化 epilog、Hadamard 和 tiling 直接当作当前 vLLM 实现。

Main 固定 ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，已全文阅读 V4 compressor.py 232 行、V4.1 compressor.py 71 行、V4 UT 188 行；对照 Native 5df63a7203cdb9328d824a27b682e77c7b9928be 的 compressor.py 全文 499 行。Main 配对 Native pin 是 544f182d9f0c9bfe8bd7645525951d5e3692a542，独立快照不是该配对提交。整项模型/硬件与实际 kernel ABI 未验证，保持 draft/空平台；profile 能力分支不能替代整卡硬件支持表。

| 实现入口 | 输入/责任 | 输出/边界 |
|---|---|---|
| Main V4 Compressor | 接收 hidden_states、显式 state_cache、cache/state 两组元数据，把投影权重交给 _C_ascend.compressor。 | 返回 compressed_kv 和 slot_mapping；后续 KV/Indexer 写入不在该 forward 内闭合。 |
| 独立 Native DeepseekCompressor | 接收已投影的 kv_score、positions、rotary_emb，从 forward context 查状态与 KV。 | 保存部分状态并调用对应后端压缩/归一化/RoPE/存储，forward 返回 None。 |
| Main V4.1 DeepseekV41Compressor | 普通 forward 直接投影后 norm；ratio=2 的 pool_projected 消费已投影 KV/score 和 C2 ring metadata。 | 环输出写入预分配 buffer，再 norm；不是 V4 C4/C128 的可互换入口。 |

## V4 权重、overlap 与 FP32 状态

Compressor 记录 hidden_size、head_dim、qk_rope_head_dim 和压缩比。compress_ratio=4 时 overlap=True、coff=2；128 时 coff=1。ape 的 shape 为 `[ratio,coff*head_dim]`，dtype FP32；wkv/wgate 是两个 ReplicatedLinear，各输出 coff*head_dim，bias=False、return_bias=False。

当当前硬件 profile 声明 DSV4_COMPRESSED_CACHE 能力时，两个线性层显式 quant_config=None；其他分支传入 quant_config。无论该分支如何，两个权重都设置 skip_weight_nz_conversion=True，来源理由是 custom compressor 消费 ND 权重。norm_weight 使用 FP32 RMSNorm，是该融合接口的约束，不可随整模 BF16 cast 习惯无条件改掉。

C4 state_dim=2*coff*head_dim，保存 KV state 与 score state；C128 state_dim=2*head_dim。状态 dtype 均 FP32，state block_size 分别取 DSV4_BLOCK_SIZES[cache block_size][0][2] 与 [0][3]。其他压缩比会显式 ValueError；完整坏配置、非法 head 宽度和数值输入校验不能只靠这一分支推导。

rotate 参数在这个 Main 类中保存，但所读 forward 没有按它分支或调用 Hadamard。不能因为 recipes-infer 或 Native 其他路径出现旋转，就把它补写成这里已发生的行为；实际调用方是否另行旋转需独立来源。

## AscendCompressorStateCache：块行数与 padding 独立核对

该类继承 Native CompressorStateCache，super 接收 state_dim/dtype/ratio/prefix，随后用 Main 传入值覆盖 compress_ratio 和 block_size。独立 Native 基类会建立空 kv_cache、按 prefix 注册到 static_forward_context、拒绝重复层名，要求 FP32 与 ratio 4/128，并用 coff*ratio 设置 sliding_window。这是独立快照的实际父类行为，运行环境仍需核对对应版本。

get_kv_cache_spec 用 dsv4_block_sizes(vllm_config)[cache_config.block_size][1] 取得 pads：只有 state_dim==2*256 且 ratio==4 时取 pads[0]，其他取 pads[1]。它返回 AscendSlidingWindowMLASpec，含当前 state block_size、单 KV head、state_dim、dtype、sliding_window、alignment=None 与显式 page_size_padded。

构造时取静态 DSV4_BLOCK_SIZES 的 state block 行数，与 spec 时取 dsv4_block_sizes 的 padding 是两个调用，不应混成一个常量表。不要只按 ratio 决定 padding，也不要把 head_size、逻辑 block rows、物理 page stride 和实际字节数当成同一量。完整容量和视图责任见 [V4 KV 计划](vllm_ascend_dsv4_kv_plan_contract.md)。

get_attn_backend 保持 lazy import：ratio 4 选 AscendDSAC4StateBackend，128 选 AscendDSAC128StateBackend，其他值报错，避免模型检查时的循环导入。独立 Native 使用自己的 CompressorBackend 和支持 head 集合，不能把它的后端列表直接套在 Ascend state_dim 上。

Native 基类 bind_kv_cache 对传入缓存 squeeze(1)，而 Main forward 对显式 state_cache 使用 squeeze(-2)。这两处属于不同接口阶段，不能只因都去掉一个单例维就任意交换张量布局。squeeze 在该维不为 1 时也不自动报布局错误，接入方要检查真实 shape/stride。

## cache/state 元数据与设备阶段等待

AscendCompressorMetadata 是 frozen dataclass，只封装 cache 与 state 两个对象。forward 分别取得 cache.req_metadata 和 state.req_metadata 并断言非 None；它不是完整字段 schema，也没有把两套请求坐标合成同一对象。

_compute_metadata 若发现预计算 compressor_metadata，要求 compressor_metadata_group_id 非 None，先 wait_for_device_metadata(DeviceMetadataStage.COMPRESSOR,group_id)，再原样返回预计算结果。缺少预计算时调用 dsa_v1.get_or_compute_compressor_metadata(metadata,ratio,vllm_config)。存在 tuple 不是数据已在正确 stream 就绪的证明，不能删除该等待后以 shape 相同验收。

cache 组提供压缩位置、query_start_loc、start_pos 以及 cos/sin/slot mapping；state 组提供实际 state block table。完整 helper、设备 metadata worker 与并发同步机制在本卡之外，相关地址/分组原则见 [SFA 缓存视图](vllm_ascend_sfa_replicated_cache_views.md)。

## V4 forward 的参数路由

forward 把 hidden_states、wkv.weight、wgate.weight、state_cache.squeeze(-2)、ape、norm.weight 交给 _C_ascend.compressor。_compute_metadata 返回 cos/sin/slot_mapping；sin 和 cos 分别 view(-1,last_dim)，传参顺序为 sin 再 cos，不能只检查两者 shape 一样。

关键 kwargs 为：state_block_table 取 state.req_metadata.block_table；cu_seqlens 取 cache.req_metadata.query_start_loc；start_pos 也来自 cache；seqused=None；rope_head_dim、cmp_ratio、norm_eps 来自模块；coff 按 overlap 取 2/1；rotary_mode=2、cache_mode=1。该函数返回 custom op 结果与原 slot_mapping，没有在这里完成全部压缩 KV 的量化/存储。

同一ceac的[Compressor metadata与执行合同](vllm_ascend_compressor_metadata_execution_contract.md)继续解释Main C4/C128的槽位生成、投影、Gate+APE、按组softmax、norm与RoPE；它不覆盖本卡独立Native或V4.1 C2接口，也不表示后续量化writer与运行时已验收。

因此需要同时记录 cache/state group、累计 query 边界、绝对 start_pos、state 块表、位置 tensor 的展平方式及返回 slot 的坐标。只按名字把 attention 的 block table 填到 state 参数，或把预计算 slot 当作已经完成 epilog 的结果，会丢失接口职责。

## 独立 Native 的缓存与 kernel 分支

Native get_kv_cache_spec 根据 cache_dtype==fp8_ds_mla 选择 alignment=576，否则 512，并显式 max_tp_shards=1；Main 方法使用 alignment=None 与 page_size_padded。只凭两个类都叫 CompressorStateCache，不能继承另一套页面几何或构造默认值。

Native DeepseekCompressor 用 fused_wkv_wgate（MergedColumnParallelLinear，disable_tp=True、quant_config=None）拥有投影参数，而 forward 的 kv_score 已经完成投影。它按 coff*head_dim 拆 KV/score，取得 forward context；profiling 的非字典 attn_metadata 直接返回。真实路径先保存带 APE 的部分状态，再压缩、norm、RoPE 和 KV store。

CUDA、head_dim=512、ratio=128、非 FULL graph 且 c128_boundary 明确 False 时，压缩后半段可提前返回，但前面的部分状态保存已发生；不能把它解释成整个 forward 无状态更新。metadata builder 仅在特定 block_size 和非异步投机条件计算该 CPU 边界，None 不是 False。FULL graph 不按每步 CPU 边界分支。

Native 关闭相关 CUDA PDL launch 的源码理由是 save-partial 与后续 kernel 存在 RAW 依赖、没有配套 grid dependency primitive；ROCm/XPU 的 kwargs 另行选择。它是该后端源码的同步说明，不是 Ascend stream 性能或正确性实测。

后端按 CUDA head512 的 CuTeDSL、ROCm 偏好的两阶段 scratch 路径及其他 Triton 路径分派；head128 的 indexer cache 与 head512 的普通/full-cache 还有独立量化格式 guard。这些 kernel、warmup 注册和缓存 writer 的完整 Device 实现未在本卡阅读或执行，不能把 Native GPU 优化选项直接移植成 NPU 开关。

## V4.1：C2 ring 与直接投影

DeepseekV41Compressor 的 ratio=2 使用 FP32 wkv 与 wgate，其他值的 wkv 为 BF16；norm 为 BF16 RMSNorm。普通 forward 只是 norm(wkv(x))，ratio=2 的环池化由 pool_projected 消费已投影的 KV/score。构造只按 ratio==2 分支，没有对其他所有 ratio 做完整白名单验证，不能将“典型配置为 1/2”写成此类已经拒绝了所有坏值。

当 ratio=2 且提供 vllm_config 时，在 profiling 前注册非 persistent 的 _ring_pooled，shape 为 `[scheduler.max_num_batched_tokens,width]`、BF16、device 跟随 wkv；读取容量字段缺省 4096。该持久输出在内存预算前存在，避免 cache 分配后再临时增加 footprint。vllm_config=None 时并不建立这些运行 buffer，不能直接调用 pool_projected 假设它会按需补齐。

state cache 使用 DeepseekV41CacheLayer。uses_a5_packed_cache() 决定 AscendCircularBufferSpec 或 Native CircularBufferSpec；字段为 STATE_RING_ROWS、单 KV head、head_size=2*width、FP32、head_size_v=0。物理共享池与 packed 页的具体布局复用 [V4.1 缓存规划](vllm_ascend_v41_cache_pool_contract.md)，不由 C2 的 ring 名称推导任意缓存都能别名。

prepare_ring_compressor(max_tokens,device) 在 capture 前取得 _cube_core_num() 并保存 _ring_num_cores；所读函数没有根据两个形参自动扩容输出。pool_projected 调用 compressor_from_projected，传 KV/score、state_cache.kv_cache[0].squeeze(-2)、metadata.c2_ring_metadata、_ring_pooled[:kv.shape[0]]、max_query_len 和已准备 core 数，最后 norm(pooled)。这里的缓存容器索引不能直接解释成物理 block 0。

调用前应验证已准备 core 信息、实际 token 行数不超过 buffer 容量、投影宽度和 ring metadata 一致。超容量切片不会自行保证仍与输入行数相等；helper 是否提供额外 guard、其 kernel 数据布局与图重放契约仍需对应来源，不能只看输出 shape 宣称 C2 数值正确。

## Agent 验证与测试证据

按实际模型/版本先选接口，再检查 ratio/head/coff、两类权重布局与 norm dtype、state spec/page padding、prefix 唯一性、cache binding 的 shape/stride。分别覆盖预计算/即时 metadata、正确/缺失 group ID、cache/state 不同块表、C4/C128、V4.1 直接投影/C2、空 batch、buffer 容量边界与捕获前准备。不要用删除等待、改写 block size 或复制 GPU 页面布局消除表面报错。

V4 UT 通过 mock compressor_metadata、compressor 和 plan 验证预计算等待、cos/sin 展平、cache/state 路由、coff 与 padding 选择；数值张量是测试替身，不构成融合 kernel 或完整 KV 推进结果。未覆盖的独立 Native GPU kernel、V4.1 ring helper、CP/PP、图重放、多 stream、量化 epilog与真实模型行为继续留作验证边界。

失败时保留原 spec、页地址/stride、各请求坐标、metadata readiness 和实际 op 绑定，恢复明确配对的框架/模型/算子组合。完整 Device 路径需专用算子 producer，实际性能需受控 workload。本次没有执行上游导入、UT、JIT/warmup、编译、模型、NPU、精度、性能或 Agent A/B，未填写 verified 事件。
