---
type: Guide
title: vLLM Ascend MRv2 输入坐标：AscendInputBatch、Host计数与kernel块表
description: 沿 AscendInputBatch、AscendInputBuffers、AscendRequestState 与 AscendBlockTables 区分持久请求slot、乐观Host计数、逻辑query和图padding，核对dummy作用域、manager到kernel块展开、int32 slot及独立Native的DCP分组边界。
aliases:
- AscendInputBatch
- AscendInputBuffers
- AscendRequestState
- AscendBlockTables
- dummy_num_tokens
- _block_table_window_size
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.kv_cache
- topic.graph_execution
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/input_batch.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/states.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/block_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/v2/block_table/compute_slot_mappings.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_states.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_block_table.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_v2_block_table.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_v2_dummy_padding.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/block_table.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/states.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/input_batch.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/compute_slot_mapping.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/v2/block_table/compute_slot_mappings.md
  role: constraint
created_at: '2026-11-02T07:21:45Z'
updated_at: '2026-11-03T06:14:54Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MRv2 输入坐标：AscendInputBatch、Host计数与kernel块表

## 接入任务与固定范围

新模型在 MRv2 接入后出现请求重排错位、投机拒绝后长度陈旧、dummy 改变图形状或 KV 写到旧块时，先分清持久请求状态、当前批次和物理缓存三层坐标。输入 shape 正确、CPU 两个 view 数值相同，以及图地址稳定，分别只检查了其中一部分。

Main 固定 ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2：全文阅读 states.py 51 行、input_batch.py 166 行、block_table.py 166 行、slot mapping kernel 113 行、四个 UT 文件 51/58/230/409 行和一行配对 pin。regular Runner 仅阅读 217–260、812–1070、1164–1258、1336–1435 行。独立 Native 5df63a7203cdb9328d824a27b682e77c7b9928be 的 RequestState 133 行与 BlockTables 353 行全文，InputBatch 只读 1–221 行；其余输入准备、分布式执行及父类生命周期未全文闭合。

Main 的实际配对 pin 是 544f182d9f0c9bfe8bd7645525951d5e3692a542，独立 Native 不是该配对提交。源码、CPU mock 和 kernel 定义不构成全硬件/全模型或安装 ABI 验证，保持 draft、空平台与 framework=vllm 的部分 Scope。本卡提取框架输入和 kernel 调用边界，没有进行完整 Device Operator 生产或实机验证。

[输入元数据概念](../../concepts/frameworks/vllm_ascend_input_attention_metadata.md)保存文档示例与量纲，[UVA 元数据](vllm_ascend_uva_metadata_contract.md)保存映射和 staged-write buffer 的实现，[CP 缓存映射](../../concepts/frameworks/vllm_ascend_cp_cache_mapping.md)保存拓扑和分片设计。这里进一步核对 regular MRv2 的实际状态与输入桥接；[310P 状态](vllm_ascend_310p_model_state_contract.md)和[310P MTP 输入](vllm_ascend_310p_mtp_proposer_contract.md)是另外的实现路径。

## 先建立坐标表，再检查值

| 坐标或数量 | 所有者与含义 | 不能直接代替的值 |
| --- | --- | --- |
| req_id 与 req_state_idx | RequestState 的持久请求 slot，随加入/删除分配和复用 | 当前 batch 行号 |
| idx_mapping | batch 行到持久 slot；NumPy/device 两种载体需同轮一致 | token 位置或物理块号 |
| expanded_idx_mapping / expanded_local_pos | 对应采样 logit 行，投机时与普通每请求一行不同 | 原始 batch 行数 |
| query_start_loc | 当前请求的 query 边界；逻辑有效 token、图补齐 token 和补齐请求数分开 | 任意 seq_lens 或模型输入长度 |
| num_computed_tokens_np | Host 的乐观计数，可作为 device 值的上界 | 拒绝修正后的精确 device 状态 |
| manager / kernel block | 缓存管理块与 kernel 寻址块；Main 显式展开二者映射 | scheduler token 数或原始 block ID |
| slot_mappings | 按 KV group/token 排列的写入位置，含 PAD | 词表 token ID 或请求 slot |

## RequestState：共享 CPU 存储不等于 device 同步

独立 Native RequestState 维护 req_id_to_index、index_to_req_id 和 free_indices。add_request 从空闲列表取 slot，记录 prompt_len、prefill_len、total_len、token history、computed 数量和最大序列长度，并清空该 slot 的 draft_tokens。prefill_len 是本轮送入 Runner 的已有 token 数，抢占恢复时可以包含输出，不能简单等同 prompt_len。

token history、total_len 和 device computed 数使用 staged write；apply_staged_writes 才提交这些暂存与 UVA 复制。remove_request 释放映射并把 slot 放回空闲列表，没有逐个清零所有历史、KV 或外部模型状态。加入过程包含分步赋值和断言，也不是任意失败都原子回滚的事务。复用 slot 时要核对请求映射、后续 staged 提交和各自模型资源的退役。

AscendRequestState 在父类构造后用 torch.from_numpy 包装 num_computed_tokens_np，得到 num_computed_tokens_cpu；它们共享 CPU 存储，没有建立 CPU 与 NPU 双向实时一致性。对该 NumPy 数组重新绑定新对象也不等于原 torch view 自动换了 backing storage。

其构造只在 vllm_version_is("0.31.0") 为真时省略 use_dense_all_token_ids，其他分支按关键字传给父类。这个精确分支不是任意旧版本签名兼容表。独立 Native 用该选项控制 all_token_ids 的 UVA/密集设备驻留选择；Main Runner 的已读构造片段为 ngram/ngram_gpu 设置它，在替换请求状态后重新构造所需 speculator，再创建 AscendInputBuffers。不能继续让旧 speculator 持有已经被替换的 RequestState。

## Host 长度校正与 device 精确状态

Main Runner 用独立 pinned CPU staging、copy stream 和 event 接收纠正后的 device computed 数。_copy_num_computed_tokens_to_cpu 在需要时让复制流等待默认流，发起非阻塞 D2H 并记录 event；_update_seq_lens_cpu 在对应 producer 会运行的条件下先同步 event，再按 scheduled_cached_reqs 的 req_id 找持久 slot，写回共享 Host 视图。

随后按当前 req_ids 的 batch 顺序生成 seq_lens_cpu：对应持久 slot 的 computed 数加该请求本轮 scheduled 数。不能把 staging 的 slot 顺序直接拷成 batch 顺序，也不能只发起 D2H 就提前读取。是否可跳过同步由实际 _can_skip_spec_cpu_length_sync 与调用条件决定；本卡未全文读取该判定，不扩写成通用“无 CPU 同步”条件。

device 位置与长度仍由 prepare_pos_seq_lens 读取精确 device computed 状态。seq_lens_cpu_upper_bound 则由乐观 Host computed 与原 scheduled 上界相加，在自适应验证压紧后也不能当成精确实际长度。Main 在特定 adaptive/FIA 分支另有实际 seq_lens 读回；名字中包含 CPU 或 upper_bound 的字段必须按真实生产点解释。

输入准备还按实际 computed-prefill 与 prefill_len 的比较决定是否填 prompt 输入。图 dispatch 将短 prompt 尾部归为 decode，不代表数据来源已经从 token history 切换为 last sampled tokens；只按图模式选择输入会丢 prompt 尾或 MTP lookahead。

## AscendInputBuffers 与逻辑 query、图 padding

AscendInputBuffers 重建 query_start_loc 为 max_num_reqs+2 的 int32 device buffer，为 FIA 添加 dummy 请求留空间；seq_lens_cpu 是 CPU int32，seq_lens_np 是它的 NumPy 共享视图。它们与 RequestState 的 computed CPU 视图是两套不同缓冲，不能混淆所有者或有效前缀。

AscendInputBatch 继承当前父类 dataclass，增加 seq_lens_np、attn_state、is_dummy 和 is_cpp_profile。make_dummy 先保存模型输入的 padded token 数；若 dummy_num_tokens 非 None，则用它作为逻辑 query 数交给 Native InputBatch.make_dummy，且要求不超过 padded 数。已读 Native 要求 0 < num_reqs <= num_tokens，按商和余数均分 query，若有 max_query_len 则核对该承诺覆盖最大分段。

两数量不同时，Main 只把 input_ids、positions、is_padding 的视图扩展至 padded token 数，补齐区 token/position 清零并标 padding；query 边界、scheduled 数量和普通 logit 索引仍由逻辑 query 生成。Main 按同样商/余数填写 CPU seq_lens，容量尾部清零，更新 RoPE 后按 fields(InputBatch) 复制父类字段构造子类。不能用模型输入视图长度覆盖逻辑 query 末项，也不能假定任何新增父类字段都可由旧硬编码构造兼容。

regular Runner 的 _preserve_dummy_query_tokens 仅在配置为 PIECEWISE 且无 PCP manager 时设置逻辑 override；uniform_decode 时至少取 decode_query_len。finally 恢复进入前的值，允许嵌套作用域恢复外层状态。FULL 请求 padding 和 PCP 自己的 dummy 布局不适用这项 token-only 补丁。

CPP profiling 的独立作用域暂时置 profile_cpp=True、speculator=None、max_num_reqs=1，finally 恢复原值。相应 dummy 标记为 fresh PrefillNoCache，prefill 计数/已计算数、position 与 padding 按新 prompt 准备。它模拟目标 prefill，不是通过普通 decode dummy 推导校准延迟；真正 CPP 采集与拟合复用[校准诊断](../../runbooks/performance/vllm_ascend_cpp_calibration_timing_missing.md)。

## FULL FIA 请求形状与有效数量

_pad_query_start_loc_for_fia 为 TND 输入行数与 query 长度末项建立一致关系。它先看各请求 query 是否统一为指定 query_len，并检查 descriptor 请求数乘 query_len 是否匹配 padded token 数；该检查不读取请求 phase，短 prefill 也可能满足，需要图 dispatch 排除不兼容情况。

uniform 图保留 descriptor 请求形状并按 query_len 追加请求边界；mixed 分支要求当前请求数与选定 padded 请求数相等，再追加一个 dummy 请求边界覆盖剩余 token。不是把最后一个真实请求边界直接改成图大小。max_num_reqs+2 的容量、真实与 padded 请求数、均匀 query 宽度和 descriptor 需要一起核对；GDN 等请求粒度元数据不能仅因 token 总量相等就交换拓扑。

adaptive verification 的压紧、重分配和 FIA 特殊 padding 有另外分支，本文只保留已读调用关系，不据普通分支公式证明其完整正确性。PCP partition 也发生在输入批次构造后；完整 global/local 恢复协议继续由 PCP 实现与既有 CP 卡承担。

## AscendBlockTables：manager 块到 kernel 块

kernel_block_sizes 缺省为 block_sizes。Main 以 manager block_size // kernel_block_size 得到 blocks_per_kv_block，按比例扩大每组行容量，再调用 Native 父构造；不将 kernel_block_sizes 传给新父类。append_block_ids 将 manager block b 展开成 b*r+k 的 kernel block 列表，例如 r=2 时 b=7 变成 [14,15]，然后委托父类 staged 写入。

这是 Main 为自身 kernel 恢复的局部布局，与独立 Native 保留 manager-block 表的合同不同。调用方应先验证组数、正 block size、整除比例、ID 和容量；整数除法与 zip 不是完整配置校验。独立 Native 的 append 对每组检查行容量，但这些分步检查也不是任意多组写入的全局预检事务。

父构造只在 caller 提供 dcp_sharded 时转发该参数；“父类字段保存成功”不能证明本地 kernel 已消费相同语义。Main 另建 kernel_block_sizes_tensor，把 slot_mappings 从父类 int64 重建为 int32，形状为 KV groups × max_num_batched_tokens。真实消费者、物理 slot 上限及自定义 out 的 dtype/stride/容量都需核对，不能只靠返回 slice 成功验收。

compute_slot_mappings 的 launch 为 (num_groups,num_reqs+1)，末个 program 负责清逻辑 query 末项到输出容量末尾的 PAD；其他 program 按请求和 group 计算。无 KV group 时直接返回零行前缀视图，_block_table_window_size=1，不启动 kernel，这为 encoder-only 缓存空组保留接口，但不是完整 encoder 模型验证。

## PAD、窗口与 DCP 的迁移边界

Main kernel 对负 idx_mapping 输出 PAD，屏蔽旧请求块表行读取；slot_mapping_enabled=False 的组直接把本请求区间置 PAD，不按 token 位置索引 circular state 表。dummy 和容量尾部也不能沿用前次真实 slot。Native get_dummy_slot_mappings 填充整个持久 buffer 再返回前缀，get_dummy_block_tables 清空用于 forward 的持久输入行，使 dummy 不经过已退役的旧块。

Main 的 token tile 为1024，_block_table_window_size 由最小 kernel block size 算出窗口上界再取2次幂；kernel 根据有效位置中的最小 block index 暂存连续窗口，再 gather 当前 tile 的相对索引。它减少整行 staging，不构成任意稀疏 positions、任意 group size 或非法索引都有动态 guard 的证明。要验证实际位置跨度、块号表达、窗口边界和输入 dtype，不把框架 launch 审阅当完整 kernel 数值闭包。

CP_SIZE>1 时 Main kernel 按虚拟块与 interleave 求 owner 和 local position，再用 kernel block size 寻址；非本 rank 的 slot 为 PAD。独立 Native kernel 另外消费每组 dcp_sharded，对不分片组保留全局 position；所读 Main launch/kernel 没有接这项 mask。不能因为父构造接受参数，就宣称所有分组沿同一 CP 语义运行；实际 backend、组划分、replicated cache 与真实分布式结果仍需验证。

## Agent 验收与测试边界

先固定 Main、配对 Native、模型/Runner 与缓存组规格，再记录每轮 req_id→slot→batch→logit 映射、Host staging 与事件、device 精确计数、query 边界、descriptor、manager/kernel 块和 slot。覆盖请求重排、加入/删除/复用、抢占恢复、chunked prefill、投机拒绝、未采样 prefill chunk、grow/shrink batch，以及相同 token 总数而请求形状不同的图桶。

分别检查逻辑 dummy/补齐视图、CPP 作用域正常/异常/嵌套恢复、FULL uniform/mixed、零 KV group、多个 block size、manager/kernel 比例、disabled group、负 idx、custom out、尾部 PAD 和 CP owner。发生越界、旧长度或旧 KV 写入时，保留上述坐标与原始缓冲，恢复明确配对的执行配置；不要直接覆盖 query 末项、删掉 event 等待或改 PAD 来消除表面错误。

UT 定义 CPU 共享 view、版本关键字转发、int32 slot、kernel launch/out、空组构造及 dummy/padding/CPP 恢复的断言；依赖 mock、CPU tensor 和被替换的设备设施。mock kernel 没有验证实际 slot 数值，假 collective 没有验证跨设备执行，本次也没有运行这些 UT。

所有来源仅按数据阅读，没有导入上游、执行 UT、JIT/编译、NPU、真实模型、图/CP、精度、性能或 Agent A/B；未填写 verified。先完成多步数值与生命周期验收，再比较 Host 同步、输入准备、块表 staging、峰值内存、TTFT/TPOT 与吞吐，不能把少一次复制的设计动机当实测收益。


## Triton 槽位映射文档的版本与可执行性补充

同一固定 Main 的 `compute_slot_mapping.md` 与 `docs/v2/block_table/compute_slot_mappings.md` 已原文读取。前者记录 V1 的 `(num_reqs+1,)` grid、最后 program 清 padding、虚拟 allocation block 与 interleave ownership；后者记录 MRv2 `(groups,num_reqs+1)`、持久 idx_mapping、manager/kernel block size 分离。两文档不是可互换的 kernel 签名。V1 示例中 `max_num_blocks_per_req` 后缺逗号，不宜直接作为可执行验收命令；以实际 wrapper 绑定签名为准。

窗口上界取 `next_pow2(ceil(1024/min(kernel_block_sizes))+1)`，是依据连续位置 tile 的跨度估计；真实 positions 必须满足窗口覆盖，而不只是长度够。MRv2 文档中的位置转换为 int32、query 边界非降且不超容量、有效 block index 在请求行内，均是 caller 前置条件。CP 的 allocation-size 虚拟块与 kernel-size 最终寻址必须同时保留；不能把 `block_sizes_tensor` 与 `kernel_block_sizes_tensor` 名称相似解释成相同单位。文档列出的 Native v0.28 对照与 CP=1/2/4 NPU 测试是历史复现入口，本次未执行，也不覆盖独立 Native 的所有新分组语义。
