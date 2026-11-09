---
type: Runbook
title: Runtime Guard 配置不生效或 dump 连续触发：启动覆盖、热加载与水位控制
description: 按固定 runtime_config 契约排查启动JSON覆盖、热加载、配额和manual_dump水位，复核中文 runtime_config.po 字段差异、各DP有效值与D2H产物。 区分runtime_dump_dir构造种子、additional_config.runtime_config overlay与dump.dump_dir热加载的生效顺序。
tags:
- task.debugging
- topic.model_serving
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/configuration/runtime_config.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/runtime_guard.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/_defaults.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/schema.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/detector_catalog.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/queue.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/configuration/runtime_config.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/dist.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_bus.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_dump.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/actions.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/__init__.py
  role: implementation
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-11-03T05:29:54Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- runtime_dump_dir
- _merge_bootstrap
- runtime_config_hot_reload
- manual_dump
---

# Runtime Guard 配置不生效或 dump 连续触发：启动覆盖、热加载与水位控制

## 症状与范围

适用于 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 已接入 Runtime Guard 的标准 V2 路径：启动前手改 JSON 被还原、运行时编辑没生效、报告有 dump_attempted 却没有预期 dump，或设置一次 N 后连续产生多轮文件。先核对 Runner/hook，不能仅看到配置文件就判断检测已工作。

## 诊断路径

启动 writer 使用默认值叠加 additional_config.runtime_config 并覆盖文件；需要启动即生效的值放 overlay。`runtime_config_hot_reload` 是启动参数，不是运行 JSON 字段。未启用热加载时，运行中改文件不构成有效变更。

自动 dump 需要 on_trigger 含 dump_kv 且 `auto_max_times` 有配额；默认0关闭自动配额，成功消耗后另有冷却。手动触发绕过自动配额/冷却，但仍受实际队列、dump 条件和 rank 范围限制。

## manual_dump 是水位

服务启动并启用热加载后，将 manual_dump 从 false 改为1；下一次再加到2、3。进程维护内存中的 done，不改写磁盘值；当 done<N 时后续 armed wave 逐次追赶。N=5、done=0 可能产生约五轮，不是“一次抓五个请求”的计数器。

各 DP 副本独立维护 done。连续 true 或大幅提高水位可能增加队列和磁盘压力；同一次 wave 的请求还有去重。排队失败也可能使水位推进，因此水位完成不能替代检查实际产物。

## 验收与处置

核对 live JSON、有效 overlay、启动热加载开关和实际请求窗口，按 incident/request/wave/rank 对齐报告与 .pt。dump_attempted 与动作完成分开；结束请求标志意味着缓存可能已复用。dump_kv 的覆盖为 last PP×all TP，不是整个 PP 模型的完整缓存。

手动一次抓取优先逐步抬高水位；无需求时关闭 detector/dump，保留原 overlay 以便重启恢复。字段拼错、热加载关闭、自动配额耗尽、产物不完整或缓存复用未排除时停止成功/根因结论。本卡是文档流程，不是已执行故障修复。

## Evidence

runtime_config 与 Runtime Guard 两份固定文档给出覆盖、热加载、水位、队列与 rank 语义；未运行真实服务或 dump。


## 平台证据待补

配置/热加载/水位语义无整卡硬件范围；与Runtime Guard相同，不能从标准MRv2代码路径推断A2/A3/950已支持。本卡据此撤回原平台枚举，保持draft、空平台；已有机制与操作条件保留为待验证知识。取得针对本功能的明确硬件范围和组合证据后再更新状态，不能把本次修正解读为这些硬件不支持。


## 旧字段与非法overlay可能让服务回到默认值

固定runtime_config文档称退休的logits_finite.check_every_tokens会被忽略，但当前detector schema不含此项，DETECTOR_KEYS未知字段会触发ValueError；merge保留未知项，normalize主要处理ascend_log，未见针对该字段的剥离。不能按文档一句“ignored”推断保留旧键仍能使能检测。

启动_bootstrap先按defaults与overlay合并并validate；非法overlay会记录startup config rejected，再用defaults与构造种子重试。服务能正常启动可能意味着整份overlay未采用，须读实际落盘和有效值；fallback仍验证，不能宣称任何错误都会被吞。已有JSON不是启动配置权威，启动覆盖语义保持不变。

热加载则以defaults加整份loaded重建，validate通过后才替换_data；非法JSON/字段会reload failed并保留旧有效状态，不是启动时同样的fallback事务。删除字段会回到默认值，startup overlay不重新叠加；这不是保留所有旧值的局部JSON patch。mtime较旧可跳过，同mtime还比较内容digest，不能只看文件大小/触碰时间。

runtime_dump_dir构造种子在_merge_bootstrap中位于overlay之后应用；同时设置overlay的dump.dump_dir时要核对实际生效值，不把“seed”一词理解为绝不覆盖。运行中改dump_dir再走有效热加载另按实际值判断。

## 配额、队列与报告上限分别解释

DumpQuota.try_consume在锁中检查/消费，consume_quota=False绕过自动计数与冷却；refund退回计数并清冷却，但何时refund由实际动作路径决定。manual水位推进、配额消费和D2H完成不是一个计数。

report默认max_per_req=1，成功写达上限会停止该请求所有detector；token_repeat另有_alerted私有锁存。报告写失败会尝试回滚最新计数，report入队还按(wave,req_id)去重。提高上限不保证同类型立刻再报，也不代表所有Incident都各有文件。后台重任务在队列满时会丢，轻report可能内联；stop返回不保证所有任务已落盘。详细状态/回收边界见[请求生命周期](../../guides/integration/vllm_ascend_runtime_guard_request_lifecycle.md)。

上述实现片段现已由后续完整控制面/Host dump阅读补充，见下文；Device行为、全布局与真实服务/硬件验证仍有边界，未执行热加载、D2H或故障注入。


## 完整控制面补充：JSONC、writer与路径

loads_jsonc用字符串感知扫描移除//、/* */及结尾逗号，再交json.loads；字符串内的注释符号/转义保留。它不是任意配置语言，解析通过也仍要走validate。启动schema中的auto_cooldown_seconds实际经int_field要求非负整数（整数浮点可转），与中英文表标float不同；分数字面值、NaN、bool等不能按表推断有效。

ensure_persisted由worker writer一次性覆写生效启动配置；生产构造ensure_file=False不表示永不落盘。writer与last-PP TP0总线来源按[配置同步卡](../../guides/integration/vllm_ascend_runtime_guard_collective_sync.md)区分。启动tmp+os.replace在同一.lock下写入，但没有据此证明任意外部编辑器持锁、跨DP同一overlay或所有文件系统都具备完整事务语义。

默认根取进程cwd/runtime；显式config路径和report根会expanduser/resolve，config父目录名为config时report推导到其上一级，否则取config父目录/report。_reject_unsafe_path对cwd外路径仅warning，并非一概拒绝。不同进程cwd、挂载和显式路径要实际对齐，不能按API侧文件存在推断worker看到相同内容。

## 热变更与manual验收

apply_config_sync_payload不只等价于本地reload；同mtime有效编辑、follower版本判断及首次payload需要核对各rank实际值。所有检测hook由开转关时cascade会清检测Store/波次stamp、退款未claim arms，已deferred D2H保留。详细调用/失败边界见配置同步卡，不能把服务仍响应当作所有控制字段已一致应用。

标准manual local直接_run_kv_dumps，绕过自动prepare中的quota与空间估算，done按armed尝试推进；它不保证每层/每rank文件成功。自动arm则按共用arm_id消费/退款，异步save失败不退款，详见[dump不完整排查](../validations/vllm_ascend_runtime_guard_dump_incomplete.md)。开启取证的实际开销还包括Host文件探测/mkdir、同步D2H、轻任务inline及后台保存，不能笼统称全异步或推理线程无文件I/O。

runtime_config.po的74个有效非空条目已全文对照当前英文，0obsolete/fuzzy，msgid均为当前英文子串。译文也沿用check_every_tokens ignored、小数cooldown类型和省略wave层的简写布局；仍以对应源码/产物阶段限定，不按翻译推断这些差异已修复。此次绑定不证明线上构建/HTML覆盖，未执行生成器、热加载、dump或硬件测试。


## bootstrap公开入口与action导出

补入同提交 runtime_config/__init__.py、runtime_guard/action/__init__.py 的全部AST程序投影。build_runtime_config_from_additional对path/report_dir/dump_dir要求字符串或None，overlay要求dict或None；hot_reload仅接受真bool、整数0/1或None，字符串false/任意非零数字不作为关闭配置。它用ensure_file=False构造RuntimeConfig后立即apply_ascend_log_level并启动非worker后台reload，不能当纯配置解析函数或无副作用探针。

ADDITIONAL_CONFIG_STRIP_KEYS列runtime_config、runtime_config_path、runtime_config_hot_reload、runtime_report_dir、runtime_dump_dir，供外层剥离这些插件参数；枚举存在不表示任意caller已经执行剥离。bootstrap结果分别保path、hot_reload和RuntimeConfig对象，不应把路径相同当有效配置一致。

action包只重新导出ActionExecutor/ActionQueue，导入包名不等于动作已提交、队列已drain或dump成功；实际完成、配额和水位仍按本卡原协议及队列/产物核对。保留原description中的构造种子/overlay/热加载优先级，新增入口不改变该顺序。
