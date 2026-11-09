---
type: Guide
title: vLLM Ascend Runtime Guard 报告消费：token截断、计数与文件证据
description: 按 sanitize_report_detail、ReportWriter 与 dumps_report_json 解析异常报告，区分完整计数、每行截断、解码文本、降级值和pair限流，避免把JSON文件或dump_dir当成完整取证。
tags:
- task.debugging
- task.testing
- topic.model_serving
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/report.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/actions.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/queue.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/io.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/state.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/spec_acceptance.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_bus.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/configuration/runtime_config.md
  role: supporting
created_at: '2026-10-29T19:31:47Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T19:31:47Z'
---

# vLLM Ascend Runtime Guard 报告消费：token截断、计数与文件证据


## 任务与固定范围

后续适配/优化Agent消费Runtime Guard JSON时，需要解释缺少token IDs、文本不全、计数与数组长度不同、相同请求不再写报告或dump路径为空。依据Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的report、动作与I/O链；整项硬件集合未定位，保持draft/空平台。仅解释源码合同，没有生成或解析本次实际服务报告。

## 先分清证据来自哪个时点

detector detail可记录窗口/当前步信号；_handle_alert在报告前用use_cache=False取得当时请求I/O，再merge覆盖同名字段并附当前block_ids。ReportPrepared浅拷贝detail字典供commit，ReportWriter控制字段还可被配置cascade修改；不能把后台写入时间、采样arm wave、窗口统计与累计输出当作同一冻结事务。

dump_count/dump_max_times在ReportAction.prepare取quota快照，report动作通常排在dump_kv之前，因而不保证已包含随后本次arm的配额消费。dump_attempted表示动作意图；manual per-request report即使仅覆写report动作也可置True。它们都不证明D2H或保存完成。

## token字段识别与默认输出

sanitize_report_detail识别已知token字段和字符串后缀_token_ids；例如prompt/output/window/current/recent_token_ids会匹配。save_sensitive_info=False时删除这些字段，并在需要时推导*_token_count，其他字段继续保留。block_ids不是该后缀，会保留并可能提升到顶层；计数缺失或0不单独证明实际请求没有数据。

遍历只递归dict和**全部元素都是dict的非空list**。混合list不会按相同策略深入，已存在的*_text、自定义不匹配名字或其他非token字段也不会自动清理。因此该函数是此报告schema的字段处理器，不是通用任意对象/任意内容清理机制；新增detector必须核对自己的detail结构，不假定一个开关覆盖所有自定义字段。

计数字段通常已有则保留，缺失才从列表推导；列表嵌套时按行长度求和。推导不证明token本身有效、来自正确请求或与window_steps的accepted_count同口径。尤其spec_acceptance顶层accepted_count为输入A，而window_steps[].accepted_count为slice后IDs长度，坏元数据下可能不同，不能据同名字段强行相等。

## 截断是每字段、嵌套每行的上限

save_sensitive_info=True时先truncate_token_id_fields，prompt字段/以prompt_开头的匹配字段走max_prompt_token_ids，其余走max_output_token_ids，默认各100000；<=0不截断。平铺int列表保留前N，嵌套int列表对**每个step分别**保留前N，并不限制所有step之和。不是请求全局100000 token预算，更不是Store累计内存上限。

计数在截断前保留/推导，数组可短于*_token_count；真正发生截断时加`<key>_truncated`和`<key>_max`。原detail已带的计数/标志不构成验证过的一致性证据。数组长度、完整计数、每步计数和请求累计计数必须按来源分别解释。

decode_token_id_texts在截断后进行：平铺列表生成*_text，嵌套列表生成*_texts，空step对应空字符串；没有tokenizer时保留原detail，不凭decode_token_ids顶层布尔就推断每个字段已有文本。加载tokenizer可能失败/缓存失败，decode异常只warning。解码文本可能反映截断与tokenizer设置，不能替代原ID流或业务质量判断。

## JSON序列化、文件名与持久化

dumps_report_json将int数组紧凑放一行，其他结构按递归格式输出；_json_default对不可直接编码值依次尝试.item()、.tolist()，最后repr。数值对象被降级为字符串、数组或标量时，Agent应检查实际JSON类型，不能一概按原Tensor精度/shape推断。它没有给所有自定义key/异常值建立完整schema保证。

ReportWriter以incident_type子目录、毫秒时间戳、可选req_id和pid命名。pid降低跨进程碰撞，但文件以w模式打开，不是排他创建；同进程同毫秒同名写入并非由命名逻辑绝对排除。_pair_lock保护pair计数，不覆盖完整序列化/文件写入。这里是静态边界，未观察碰撞或文件损坏。

report写入没有本卡可证明的fsync/原子replace；写失败返回None且记录error，尝试回滚仍为最新一次的pair计数。部分文件可能已存在；进程退出、返回path或非空JSON都不证明所有rank/全部内容已持久化。config的tmp+os.replace属于另一条路径，不能套到report writer上。

## pair配额、退避与请求停检

ReportWriter以(incident_type,req_id)记last_wave/write_count，默认max_per_req=1；首次记录可用wave0占位，后续缺wave会跳过。SAME_PAIR_BACKOFF_BASE_WAVES=64，第二次至少64波，之后128、256…，位移最多20。达到上限时可停该请求**全部**detector，和token_repeat私有_alerted、ActionQueue的(report,wave,req)去重不是同一机制。

tracking dict达到8192时按旧wave裁到约4096，不是永久逐请求审计账本。报告数不能作检测总数或请求异常发生频度；提高上限不会解除所有私有锁存/停止状态，排队/写入丢失也需分别追踪。详细生命周期见[请求状态](vllm_ascend_runtime_guard_request_lifecycle.md)。

## dump目录是提示，不是文件清单

ReportWriter每次写时调用dump_root_provider取当前根目录；dump_dir是`<root>/<type>/<req>`，**不带wave层**，多请求可带dump_dirs。实际request_info位于`wave_<N>`，各rank的.pt更深；根目录热变更时，不同阶段的根也需按真实job/配置时点对齐。

顶层request_finished_at_dump只在dump_attempted且该标志为True时加入；字段没出现不证明缓存仍归原请求。dump_arm_wave是arm提示，不能替代实际drain与文件选择。读取正确文件还须核对[KV dump完整性](../../runbooks/validations/vllm_ascend_runtime_guard_dump_incomplete.md)中的layer/component、block group、分片和失败标记。

下游Agent应保留原JSON、版本/配置、字段类型、计数/截断标志、request/wave/rank和实际文件证据；缺字段、降级值、混合时点或映射不清时保留不确定性，不能据此自动判模型根因或性能收益。本次没有服务采集、NPU复现或Agent A/B结果。
