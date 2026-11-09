---
type: Guide
title: vLLM Ascend Xlite 运行接线：V1/V2、DP dummy、token预算与回退
description: 沿 XliteModelRunnerMixin、XliteWorker 与 XliteWrapper 核对profile旁路、DP dummy同步、max_m和metadata；区分logger.error、真正raise、原生forward回退及外部runtime初始化。
tags:
- task.implementation
- task.debugging
- topic.model_serving
- topic.compilation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/xlite_model_runner.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/xlite_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/xlite/xlite_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/xlite.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/xlite/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/graph_mode.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/one_card/test_xlite.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/two_card/test_xlite.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/xlite/test_xlite.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/pull_request/utils.py
  role: implementation
created_at: '2026-10-29T23:07:05Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T23:35:28Z'
---

# vLLM Ascend Xlite 运行接线：V1/V2、DP dummy、token预算与回退


## 任务、版本与有效Worker

用于启用Xlite后仍走原生forward、DP步进不同步、metadata mismatch、Sparse SFA/LI C8日志或runtime pool初始化失败。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，参考vLLM v0.32.0。这里只覆盖Host生命周期与选路，整项硬件范围未知，保持draft/空平台。

所读platform.py只在worker_cls为auto、Xlite enabled且hardware profile支持STANDARD_WORKER_PATCHES时自动选择XliteWorker，否则走对应profile默认Worker。这个局部能力门禁不证明所有profile都能用Xlite；显式worker_cls也不能仅由auto分支推断。先核对[实际Runner选择](../../optimizations/rules/vllm_ascend_model_runner_selection.md)，再确认构造类。

XliteWorker按use_v2_model_runner选择XliteModelRunnerV2或V1；V2会警告仍在开发，不应改写成该版本完全没有V2实现。worker共享workspace采用num_ubatches=1，不能外推任意微批/多实例并发合同。

## 模型所有权、旁路与DP dummy

load_model先由原生Runner加载，再保留fallback_model并创建runner_model包装。model setter用isinstance更新runner_enabled。_bypass_xlite_wrapper临时换回原生模型，finally恢复包装；它不卸载Xlite runtime，也不保证多个并发调用共享同一runner时隔离。get_model取未包装模型，Worker的编译/预热有独立外层旁路。

| 调用 | 固定实现选路 | 解释边界 |
| --- | --- | --- |
| V2 _dummy_run | is_profile=True才在此旁路；其他dummy可进入Xlite | DP execute_dummy_batch需要进入相同runtime保持rank同步，不能按通用docstring把所有dummy都旁路 |
| V1 _dummy_run | profile或is_graph_capturing时旁路 | 其他DP dummy仍保留Xlite参与；与Worker外层预热旁路分开核对 |
| V2 uniform_decode_query_len | 返回decode_query_len | 避免旧字段读取fallback导致DP dummy静默退到每rank一个token，不等于所有投机/DP组合已验收 |
| initialize_kv_cache | 原生分配后flatten并register_kv_caches | V1默认检查contiguous；V2明确check_is_contiguous=False，不能把V1局部门禁推广给V2 |

_get_flattened_kv_caches接受tensor或tensor Iterable；对一次性迭代器，all()类型检查可能先消费，再extend读不到原项，这是泛型输入边界。常用tuple/list并不因此自动出错；本批没有运行复现。逐层KV内容合同见[模型适配](vllm_ascend_xlite_model_adapter.md)。

## token预算、跨DP最大值与真正fallback

StandardXliteModel的decode预算先取min(max_num_batched_tokens, max_num_seqs*(1+num_speculative_tokens))，full_mode则从max_num_batched_tokens起算，两者最后都向上取整到TP倍数，作为max_m与wrapper.max_tokens。因此指南简写的decode公式不是所有情况下的最终分配数。

XliteWrapper.__call__优先取_EXTRA_CTX.max_tokens_across_dp，其次DP metadata的num_tokens_across_dp_cpu.max()，没有DP信息才取num_actual_tokens。比较的是跨rank预算；full_mode本身只改变预算，不用是否prefill的标签决定选路。v0.28起小prefill/mixed也可进Xlite，大于预算则调用npu_runnable；full_mode超限还warning_once，warning不是另一个拒绝门禁。

所读平台图配置会结合full_mode、是否投机及V1/V2调整原生mixed/decode cudagraph_mode，并回写enforce_eager。enforce_eager=True或日志Compilation disabled只能说明这条原生编译配置，不能单独证明Xlite已关闭。定位时分别记录Xlite enabled、实际Worker/Runner、预算、各rank token数和本步调用路径。原生回退是否又被ACLGraph捕获仍由其有效图模式决定。

## metadata转换与流顺序

wrapper对metadata list只取第0项，对dict优先model.layers.0.self_attn.attn，否则取首value；这不是遍历所有层/组进行兼容性校验。空/None/新容器可能在选路前失败，不能声称任何不兼容metadata都会自动走原生fallback。

进入Xlite后，当前stream在需要时wait_stream(update_stream)，再用AttnMetadataRouter把长度/块表转到CPU。router识别AscendMetadata、AscendMLAMetadata、AscendSFAMetadata的特定字段；通用getattr候选并非处处都有default，未知接口仍可能AttributeError，不是任意backend协议转换器。

query_lens来自cu_query_lens差分；无投机时cached_lens=max(seq_lens-query_lens,0)，投机时用各请求起始position，避免拒绝token仍被乐观seq_lens计入缓存。num_reqs由块表首列非0项数量并至少置1得到，这是所读约定，需核对新模型的block0/空请求表示，不能当所有分页格式通用真值。

Host将lens/cached_lens/block_tables转换为列表，并重建positions stride；hidden_states工作区按DP最大token切片，最终只返回本rank的num_actual_tokens。inputs_embeds路线另传deepstack输入并按条件清理，compute_logits仍调用原生模型；Xlite forward生效不等于全部模型计算都由其接管。

## 日志、异常与验收判据

| 信号 | 固定Host行为 | 处置依据 |
| --- | --- | --- |
| xlite does not currently support Sparse SFA/LI C8. | V1/V2构造中logger.error，没有在该分支raise | 不因进程继续运行推导C8可用，也不称此日志已硬拒绝启动 |
| Attention metadata mismatch | 只比较首KV组的末attention组builder，logger.error | 不等于遍历所有层后通过或硬拒绝；继续核对实际metadata及adapter类型 |
| xlite wrapper init failed! runtime pool size | init_tensor_pool返回非0时raise ValueError | 区分模型适配构造、内存池与forward超预算回退，不凭pool日志认定模型已运行 |
| architecture not supported / duplicate adapter | 注册或首架构查找raise | 先修映射；该路径没有通用forward自动fallback保证 |

wrapper/adapter/runner存在长寿命引用环；__del__置空部分引用不是完整native资源清理、RL热更新、sleep/HCCL恢复或进程故障回滚契约。不要直接套用默认ACLGraph的生命周期保证。

先核验有效类、外部扩展身份、KV注册和每rank metadata，再对照原生输出；分别覆盖超预算、等预算、小prefill、混合批、投机拒绝、DP dummy与profile。保留各rank步序、真实选路、输出、内存与稳态性能，发生不一致即停止提速结论。没有执行导入、上游测试、模型或NPU，本卡的源码接线和检索通过均不能替代这些验收。


## 已定义测试与实际数值验收分别取证

one_card/test_xlite.py以Qwen3-0.6B、A2/BF16 marker分别调用两种full_mode的compare_logprobs；two_card/test_xlite.py以Qwen3-30B-A3B、A3/BF16 marker和TPDP_SIZES=(2,1)/(1,2)加EP请求最多3 token生成，只assert all(output[1] for output in outputs)。双卡非空断言不检查baseline/logprob或性能，普通TP路线该字符串还包含原prompt；UT的test_xlite_placeholder只有pass，不提供运行接线测试证据。

单卡helper会删除整个additional_config来构造eager baseline，默认decode容差为2*0.0689；top-20 cross-lookup实现是单向，外层zip没有显式等长检查，详见[3-token图后端验收](../bringup/vllm_ascend_graph_logprob_validation.md)。这些是固定源码已定义的检查，没有在本次运行；不据A2/A3 marker补齐本卡整项平台范围，也不把测试函数名当实际Xlite选路证据。
