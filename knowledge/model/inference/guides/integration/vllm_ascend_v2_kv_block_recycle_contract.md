---
type: Guide
title: vLLM Ascend MRv2 KV回收：多组件清零、静态V scale恢复与退役
description: 以AscendV2KVBlockZeroer与C8KVBlockZeroer接入MRv2缓存页回收，核对tuple/list非空组件、runner_only_attn_layers、mxfp8静态V
  scale的清零与恢复顺序、物理页到kernel块ratio及初始化/关闭，保留独立Native版本与真机边界。
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_kv_block_zeroer.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_attn_utils_v2.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_c8_mxfp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_worker_v1.py
  role: evidence
created_at: '2026-11-02T07:25:51Z'
updated_at: '2026-11-02T07:33:08Z'
platforms: []
aliases:
- AscendV2KVBlockZeroer
- C8KVBlockZeroer
- zero_block_ids
- runner_only_attn_layers
- fill_mxfp_v_scale_cache
- _c8_mxfp_v_scale_caches
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MRv2 KV回收：多组件清零、静态V scale恢复与退役

## 接入任务与版本边界

为新模型增加tuple/list KV布局，或接入Attention与Mamba共享物理页的模型时，应把分配后的初始填充、回收页的动态清零、checkpoint静态scale恢复和视图退役串成同一生命周期。只检查cache dtype或某个zeroer对象存在，不能证明复用页已经准备好被当前Attention读取。

本文固定Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`。`worker/v2/utils.py`249行与专项UT82行全文；Main Runner只读390–590、Worker只读1310–1375、Runner UT只读1710–1968、Attention UT只读710–960、Worker UT只读2110–2193、MXFP8填充helper只读311–340，公共utils只核对mxfp8常量和判定helper。所读文件中的其他主题仍不由本文闭合。

独立Native `5df63a7203cdb9328d824a27b682e77c7b9928be`只对照`worker/utils.py`105–296及GPU Runner783–833、1204–1266。Main的实际配对pin是`544f182d9f0c9bfe8bd7645525951d5e3692a542`；独立5df不能替代paired544的生产调用链或ABI验证。全部源码、测试定义均只作数据阅读，未导入、执行UT、触发JIT或运行NPU。整项模型/硬件范围未知，保持draft/空平台。

## 先对齐Worker与scheduler的清零条件

Main Worker先初始化KV transfer并调用Runner.initialize_kv_cache，再依据needs_kv_cache_zeroing决定是否调用`_init_kv_zero_meta`。MRv2直接遵循该标志；MRv1还要求有Mamba层、Eagle3且num_speculative_tokens大于1。不能把MRv1的窄条件继续套在MRv2上，也不能把MRv2规则扩成所有MRv1缓存都初始化zeroer。

清零metadata的记账缓冲位于可丢弃的sleep KV池之外，避免只恢复backing却丢失控制数据。该局部顺序不等于完整sleep/wake或所有流用户已闭合；资源池与传输所有权继续沿[Sleep生命周期](vllm_ascend_sleep_wakeup_lifecycle.md)核对。

独立Native5df的update_requests在new_block_ids_to_zero非空时要求已有kv_block_zeroer并调用zero_block_ids，之后进入copy-on-write块复制分支。这是该Native快照的有界调用证据，不证明Main paired544已经执行相同接口，也不代表所有scheduler分配都自动清零。

## 为每个非空KV组件建立delegate

`AscendV2KVBlockZeroer`先把attention group迭代器物化。它按组件位置建立多套上游KVBlockZeroer：单tensor只进入组件0，tuple/list分别取相应元素；只有实际torch.Tensor且numel大于0的组件才加入该套group/context。不存在可用组件时不建立delegate，zero_block_ids与warmup遍历空列表成为noop。

每套delegate通过dataclass replace保留group字段、替换layer_names，并提供只含该组件的kv_cache视图；不修改原group列表。相同backing上的多个逻辑组件应分别核对，不能因为一个空RoPE视图也指向该storage，就漏掉非空latent组件。嵌套容器或任意对象不因此获得递归支持。

适配器接受`runner_only_attn_layers`并在组件收集和group构造时排除对应层；所读Main Runner调用没有显式传入该集合，使用默认空集合。不能把类的排除能力写成所有实际Runner路径已经自动排除了这些层。

独立Native5df父类仅遍历tensor绑定，按AttentionSpec、device及物理segment信息建立清零metadata；它还涉及manager/kernel block映射与地址跨度。本文没有全文阅读其Device kernel，更没有验证NPU执行。新的shape、stride、storage_offset和page padding仍需独立检验；物理布局原则见[非连续KV接入](vllm_ascend_non_contiguous_kv_cache.md)。

## 将动态清零与静态V scale分开

Main适配器仅在cache_dtype恰为`mxfp8`、kv_cache是tuple且长度为4时，截取前三个组件交给动态zeroers，保留第四个checkpoint静态V scale。四元list不满足这个tuple专属条件；其他dtype或组件数量也不自动套用。不能推广成所有C8、INT8 KV或所有scale都不清零。

Runner的`_fill_c8_mxfp_v_scale_caches`先重建entries；num_blocks不大于0时返回。对实际AscendC8MXFPAttentionBackendImpl层，它取kv_cache[3]，断言首维可被物理num_blocks整除，保存`(v_cache_scale, value_scale_cache, kernel_blocks_per_page)`，并初始化整份V-scale cache。该列表`_c8_mxfp_v_scale_caches`保留的是实际视图，必须随backing变化重新建立。

`fill_mxfp_v_scale_cache`从cache读取head数和V维度分片，将checkpoint的E8M0逐通道scale reshape后copy_并广播到页、token组及偶奇轴。V head dim可与K不同，不能按K维度硬编码。源值、shape、dtype与布局仍应真实匹配，不能用任意零值或常数替代checkpoint scale来消除报错。recipe开关与scale名称映射见[ModelSlim KV选择](../../runbooks/precision/vllm_ascend_modelslim_kv_recipe_selection.md)。

静态checkpoint只说明值的来源，不保证共享backing中的字节永久不变。物理页曾由Mamba组拥有时，其状态写入可能覆盖静态V-scale区域；页回到Attention后需要恢复，而非只在首次分配时填一次。

## 先验证整批ID，再清零并恢复页

`C8KVBlockZeroer`是组合包装器。实际Runner先创建tuple-aware delegate，mxfp8使能时再包装它；helper本身也允许delegate为None，用于restore-only组合，不能据此声称实际Runner总是没有动态清零。

1. block_ids为空时立即返回，不调用delegate或fill。
2. entries非空时，针对每个entry以cache.shape[0]除以ratio得到物理页数，逐个检查整批ID；遇负值或越界抛`IndexError`，所有这些检查先于delegate设备写入。
3. delegate存在时先调用其zero_block_ids清理动态组件。
4. 每个物理block以start=block_id×ratio定位kernel页范围，对`[start:start+ratio]`调用fill恢复静态V scale。

entries为空时没有上述逐entry范围检查，不能宣称包装器已经验证任意ID；ratio为正且与实际cache布局一致也是调用前提。重复ID会重复处理，没有在这里去重。预检查失败可避免本轮delegate/fill写入，但后续delegate或fill中途异常没有事务回滚保证。

Agent应记录物理block ID、每层ratio、视图shape/stride/offset及checkpoint scale，验证manager页与kernel页的对应关系。不要把token slot、kernel block ID或逻辑请求行号直接作为物理block ID传入。V4.1的共享池与页面规划另见[缓存规划](vllm_ascend_v41_cache_pool_contract.md)，请求/slot坐标见[MRv2输入坐标](vllm_ascend_v2_request_input_coordinates.md)。

## 分别验收初始化、warmup和关闭

`_init_kv_zero_meta`用当前attn_groups、kernel_block_sizes、forward context及num_blocks重建delegate；mxfp8再绑定当前entries和fill。重新初始化后应观察新的backing和entry列表，不能继续保留上一轮wrapper的视图。

包装器warmup只在delegate有warmup方法时转发；它不额外恢复V scale。独立Native5df warmup可能调用清零kernel并触发JIT，这些仅是所读定义，本次没有执行。warmup成功日志不能代替初始化fill或每轮页复用restore的观测。

Main shutdown先清Runner保留entries，再清wrapper的entries、将kv_block_zeroer还原为delegate，最后调用parent.shutdown。这个局部清理减少保留packet视图；没有证明尚在执行的图、stream或其他owner均已退役。不能用列表已空或对象已替换宣称所有设备用户都已停止。

## 验证设计、性能测量与停止条件

所读CPU/mock测试定义覆盖tuple/list空组件、同backing的非空视图、runner-only排除、MXFP8前三组件清零与第四组件保留、ratio为1/2/4、K/V宽度不同、非零offset与guard区域，以及validate-before-delegate、初始化包装和shutdown解包。Attention UT使用CPU仿真kernel检查segment写入；这些定义没有被本次执行，也不证明真实Triton/NPU、图或完整模型精度。

新模型先固定版本、KVCacheSpec、全部原始buffer和每组件视图；构造分配→Attention使用→其他hybrid组覆盖→同一物理页归还→zero/restore→再次Attention读取的序列。比较动态payload清零、V scale精确恢复、未选页与page padding/guard不变，覆盖空列表、空组件、边界ID、batch增长缩小、重新初始化和关闭。取得paired版本与目标硬件后，再加入prefill/decode、图捕获回放、prefix/COW、sleep/wake及真实并发。

只有正确性与隔离通过后才比较每步delegate次数、清零/恢复字节数、kernel启动、同步等待、TTFT/TPOT和吞吐。多组件会建立多套delegate，恢复也可能增加写入；本文没有测量收益或成本，不能据“高效zeroer”的命名宣称加速。

发生越界、scale错位、未选页被写、陈旧视图或输出偏差时，停止该布局接入，恢复已验证的完整KV格式与版本；重新生成正确metadata和entry，保留失败现场。不要跳过清零、删除静态scale、吞IndexError或改变block编号来获得表面通过。真实NPU、数值、性能和Agent任务验收仍待执行。
