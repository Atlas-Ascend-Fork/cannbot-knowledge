---
type: Guide
title: vLLM Ascend AISBench 定时剖析：采集窗口、raw/parsed 与产物完整性
description: 追踪 ProfileSpec、ProfileController 和 profile_manifest，核对正式请求触发、跨节点端点、raw
  打包、逐 rank 解析上传和离线合并，区分采集完成与模型性能验收。 补Nightly profiling入口与benchmark键选择、7/90天保留期和GitHub/OBS定位，保留评论解析缺口，分别验收完整trace与性能基线。
tags:
- task.optimization
- task.debugging
- task.testing
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/profiling/capture.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/profiling/parse.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/profiling/storage.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/profiling/artifacts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/profiling/aisbench_request_marker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/profiling/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/aisbench.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/single_node/test_single_node.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/internal_dp/test_multi_node.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/test_external_dp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/external_dp/runtime.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/nightly_ci_test.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/nightly_ci_test.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_nightly_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_a2.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_a3.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_a3_560t.yaml
  role: implementation
created_at: '2026-10-29T17:44:54Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T02:54:20Z'
aliases:
- Nightly profiling
- profile-artifact
- profile-capture
- profile-shard
- AISBench outputs
---

# vLLM Ascend AISBench 定时剖析：采集窗口、raw/parsed 与产物完整性


## 任务与边界

固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`：为 AISBench performance benchmark 在实际负载中采集指定时间窗，追踪本地 trace、raw/parsed 归档和离线索引是否完整。此流程是[服务剖析](vllm_ascend_service_profiling.md)的自动控制与产物层，不替代性能基线、精度验证或 msprobe 数值采集。

已完整阅读 tools/profiling 的六个文件、tools/aisbench.py 与 tools/spec_decode_metrics.py；只读取单机及内/外部 DP 的 profiling 接入片段，不宣称全部 DP、请求或 KV 生命周期闭合。外部 AISBench、torch_npu analyse、HTTP 服务和 OBS SDK 实现未在本批闭合。没有整项功能的全硬件支持证据，保持 draft/空平台；未执行采集、解析、请求、下载或上传。

## 配置、实例与命令注入

`ProfileSpec` 从 `ASCEND_PROFILE_*` 环境读取字段；也由 CI JSON 的 from_options 统一归一化。默认 enabled=False、start_after=60秒、duration=8秒、with_stack=False、output=parsed、benchmark_names为空。start_after 与 start_after_requests 两个键同时出现即拒绝，不靠 None 消除互斥；start_after 可为0，duration须正数，成功请求阈值须正数。时间/计数只接收 int/str，拒绝 bool 和其他类型；enabled/with_stack 接收布尔或大小写不敏感 true/false 字符串，未知键拒绝。

benchmark_names 必须是单行逗号分隔字符串，strip 后按完整 benchmark 名选择；不是 case_type、服务实例名或模糊模式。仅 enabled 且 case_type 恰为 performance 的选中 benchmark 采集。raw/parsed 两种 output 控制后续阶段；选 parsed 时仍先保留 raw 并走独立离线解析，不是在请求路径中直接解析 trace。

`ASCEND_PROFILE_ROOT` 默认解析为绝对路径 profile_artifact。initialize 在 root 已存在时失败，初始 `profile_manifest.json` version=2、status=skipped；每个 case 准备独立目录和 version=1 的 serve_manifest，先登记 partial/capture_not_completed，保留中断尝试。benchmark_artifact_name 应在该 run 内唯一；文件名规范化不是身份唯一性的证明，应保留原始 run/attempt/job/case 映射。

`ServeInstance` 记录 name、endpoint、raw_trace_dir、node_index。configure_profiler_command 对命令的 `--profiler-config` JSON 保留其他键，但覆盖 profiler=torch、每实例 torch_profiler_dir、with_stack、ignore_frontend=True、max_iterations=0；它设置采集能力，不立即调用 start，也不验证服务已接受配置。不支持的参数拼法、坏 JSON 或版本不兼容要先处理，不能据命令被重写就判定采集开启。

## 服务拓扑与真正的控制端点

单机普通服务登记 serve-0 的本地 API；单机 EPD 分支明确警告该自动 profiling 不支持并移除 serve_manifest，不能和“某 EPD 代理支持手动广播端点”混为一项支持结论。

internal DP 接入为每个 node 登记 prefill/decode/dp 名称，headless 节点关联相应 leader API；master 写全实例表，各节点注入本地 trace 目录。external DP 根据 rank 的角色/dp_rank、host、port 和 node_index 建实例，由 master 写清单，并在各 rank 命令注入配置。这里仅记录所读接入片段，不证明部署和代理均已连通。

ProfileController 按**完全相同 endpoint 字符串**去重，并发调用一次后把结果分配到该 endpoint 的 target 名。headless 与 API 目标可能共享控制端点，但各自 raw 产物仍要单独检查。相同服务的不同 URL 拼法不自动等价，也没有全节点同步屏障；多目标采集时间窗不应当作逐时刻完全重合。

## 请求时钟、成功计数与状态判定

定时适配器 TimedGenInferencer 在 warmup 前后设置 _warming_up，使 warmup 请求不写起点。正式 do_request 在限速/并发等待之后、实际模型请求之前用 O_EXCL 一次写 perf_counter marker。marker路径由 `ASCEND_PROFILE_REQUEST_MARKER` 传入。此起点是首次正式请求发起附近的时点，不是首次成功响应，也不是服务开始时间。

按成功请求数触发时，每个 AISBench worker 在 inference_with_shm 中后台每1秒发布自己的 status_counter.get_req；临时文件 replace 为 PID.count，结束后再发布一次。Controller 汇总 completed_requests/*.count；源码注释将 get_req 定义为成功输出计数，外部计数器行为仍需对应 AISBench 版本。marker/计数来自新 case 目录，不能混用旧 run；采样/轮询和 RPC 有延迟，阈值不保证精确在第 N 个响应瞬间开始。

Controller 每1秒等 marker，再等首请求+start_after 或成功数达到阈值。start_profile 的 HTTP timeout=30秒；所有 start 返回后才记 duration 起点。达到 duration 或 benchmark 提前结束后，对**全部目标** stop，含 start 返回失败的目标，因为失败响应不证明服务没有启动采集。stop timeout=900秒，finish join 最多960秒；仍存活则 ArtifactError，不把线程超时视为已释放 trace。

| 状态/原因 | 判据与下一步 |
| --- | --- |
| no_request_before_benchmark_end | 没等到有效 marker，检查正式请求是否真的进入适配器 |
| benchmark_ended_before_start | 时间触发前 benchmark 已结束，调整足够长且可比的 workload |
| benchmark_ended_before_request_threshold | 成功计数未达到阈值；保留失败请求和最终计数 |
| start_failed / per-target start_error | 至少某端点失败，核对实例与 profiler 配置；仍检查 stop 与实际目录 |
| benchmark_ended | 时长不足，即使目录存在也为 partial |
| duration_reached | 只有所有目标 start/stop 无错误且 actual_duration>=duration 才为 capture success |

actual_start_after 在 start RPC 前测量；actual_duration 在所有 start 返回后、stop RPC 前测量，不包含完整 stop flush 时间。Controller success 只证明自身控制条件，不能证明每个 rank 的 trace 已覆盖所有目标步骤。

## raw：先归档再释放原目录，上传是后续阶段

collect_raw_artifacts 为每个 target 检查 raw_trace_dir 存在且非空；gzip level=1，最多4个压缩任务。tar 关闭后写 archive/size_bytes/output=raw，再清空该 target 的原始目录子项。这里没有检查必需 *_ascend_pt、预期 rank 数或目标请求事件；任意非空目录不能作为完整采集的最终证明。

case 状态同时保留 Controller 结果及 start_error/stop_error/artifact_error，job 对任意非 success case 为 partial；先保存 manifest 再抛 ArtifactError。即使控制 partial，存在的 trace 仍可能被归档，故“有 tar”不能覆盖采集错误。打包成功后原目录已清理，上传失败的重试依赖本地 raw tar；不要只保留已清空的 trace 路径。

upload_raw_artifacts 以2任务并发传到 prefix/raw，设置 storage 元数据，SDK报告成功后才写 obs_url；记录各 target upload_error。缺 target 或缺任何 raw obs_url 会把状态置 partial，已有 capture partial 不会因上传成功自动变 success。上传不是数据持久性/权限/覆盖正确性的全部证明，size_bytes 用于记录和进度，本实现没有额外端到端内容哈希验真。

## parsed：按 node 分片，逐 trace 解析、发布并清理

plan_artifact_shards 从 manifest target.node_index 集合生成排序分片；非 skipped 且无目标会失败。node 是解析分工，不等于 GPU/NPU rank。解析需 storage、raw archive 与 raw obs_url；下载对象解包后搜索该 target 下全部 *_ascend_pt。

每个 trace 调用外部 `torch_npu.profiler.profiler.analyse`，要求 ASCEND_PROFILER_OUTPUT/analyse.done 存在，且 trace_view.json 存在并非空。该检查未解析 JSON 语义、核对事件窗口或预期 rank 数；非空 trace_view 不能单独证明目标工作负载已采到。没找到任何 trace 是错误；发现的 rank 全通过也不证明未列出的 rank 没丢失。

rank 包包含解析目录及 profiler_info*.json/profiler_metadata.json，发布到 prefix/parsed。主线程解析与单发布线程重叠；在继续下一轮前等待上一发布完成，限制本地排队。解析失败记 parse_error；压缩/上传失败记 upload_error；成功或失败后都会清理该 rank 的本地 trace/parsed tar，整个 target 最终也清理下载与解包工作区。失败后要从仍保留的远端 raw 重做，不能假设本地失败目录还存在。

每个 shard 按原 benchmark_index/target_index 保存 record，并聚合 target/rank 的 parse_error/upload_error。finalize 以位置合并 shard，缺 target 记录写 Parsed shard result is missing；原 capture/upload partial 会继续 partial，不被一次解析成功洗掉。重复 shard 的同一位置由后读记录覆盖，没有完整配置身份/重复位置证明，合并前需核对 run/manifest 与节点清单。某 benchmark 原先已 partial 时，即使 parse failures=0，最终仍可能抛“incomplete: 0 parse/upload failures”；原因应回看 raw/control 阶段。

## 可下载索引与最终验收

artifacts.py 产物只打包 manifest、serve_manifest、下载说明、summary.txt 和 download.sh，不把大 trace 树装入小索引。只有有 obs_url 的 raw/rank 项生成下载链接；HTTP URL 由 endpoint 转为未签名地址，依赖对象现有读权限，不自动授予访问。download.sh 按 all/raw/parsed 选择，以 curl 的 .part 文件完成后 mv；脚本存在不代表已经下载或内容验真。

package 会对无目标或 raw 未上传补 partial/错误，即使 summary 能生成也不等于采集完成。若只请求 raw，说明可省 parsed 展示；不能因此把 raw-only 任务判为缺解析失败，也不能把空 parsed 列表解释成已解析全部目标。

验收应列出预期服务/节点/rank、实际目录与目标事件、触发/持续时间、所有阶段状态、原始/解析对象、工具版本与 workload，并逐项解释缺失。恢复采集配置后再按[基准流程](vllm_ascend_benchmark_workflow.md)比较性能；工具/JSON 的结果判据另见[benchmark 漏检排查](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)。本卡没有运行工具、创建云对象或证明性能收益。

## Nightly入口、benchmark键与采集窗口

补读nightly_ci_test.md及219条中文消息，Nightly的PR身份、命令解析和矩阵选择先按[触发合同](../bringup/vllm_ascend_nightly_ci_dispatch_contract.md)核对。profiling工具来自workflow github.sha的profile-source，与模型测试PR SHA是不同身份，修改PR里的采集工具不自动证明本轮使用了该实现。本卡原有ProfileSpec/Controller、主来源、draft与空平台保留，不以CI用例名补出硬件支持。

/nightly <test> --profile明确启用选中YAML驱动AISBench performance采集；其他profile选项单独出现不启用，任意pytest/accuracy及/weekly --profile不在此能力范围。benchmark选择只决定哪些performance键被采集，不改变YAML原本执行的精度或其他benchmark。入口字段映射为--profile-start-after→start_after、--profile-start-after-requests→start_after_requests、--profile-duration→duration、--profile-output→output、--profile-with-stack→with_stack和--profile-benchmark-names→benchmark_names，保留JSON归一化与前端解析的分层边界。名字分三层：nightly_config的test name、benchmarks下的键（如perf）、生成的artifact name（如case__perf），不要互换。

文档的--profile-benchmark-names要求不带空格的逗号分隔精确键，但所读pr_nightly_command.yml分支未清PENDING_OPTION，后续参数或EOF校验可能失败；按静态源码限制核对目标提交，不将文档示例视为已跑通。下游JSON归一化与本卡ProfileSpec的benchmark_names规则是独立层次，字段可解析不证明评论前端成功。

默认时间触发是每个benchmark第一个正式请求后60秒，成功完成数触发则不再额外等60秒；100只是示例阈值。排除AISBench内部warmup和失败请求。名为warmup的独立YAML performance benchmark仍会被默认“所有performance”选择覆盖，要单独区分。成功计数发布和控制轮询各约1秒，约2秒再加调度/RPC开销且可超过阈值，不承诺精确起点；长请求无完成时用可比负载的时间窗参考。

默认duration8秒从start调用返回后计时，不包含全部stop flush、压缩、上传或离线解析。manifest中的completed_requests和actual_start_after核实际起点，端点/Worker/事件窗口仍分别验收。没有rank/node选择项，按记录拓扑控制全部serving instances；内部DP共享端点含headless worker，P/D独立组分端点，不能只按API数量推trace数量。

## GitHub索引、AISBench输出与OBS内容

指南的aisbench-outputs-<scene>-<job>-<run-id>-<attempt>包含各实验outputs，保留原目录结构；多机按node-N分层。它与benchmark摘要JSON、plog和profile索引不同。文档保留期7天，只收集已产生输出的节点；失败后尝试保存不保证取消、runner/Pod丢失时仍可取齐，实际下载时核对当前run和存储状态。

profiling最终索引是profile-artifact-<key>，parsed模式处理中间索引为profile-capture-<key>，逐node结果为profile-shard-<key>-node-N。key区分repo/run/attempt/scene/branch/job，不跨重跑拼接。指南给GitHub索引90天保留期；OBS大归档按桶生命周期及对象读权限，拥有GitHub index不授予OBS权限，7天与90天也不是同一种数据的承诺。

raw/和parsed/目录放下载说明，不装大trace；raw-only省parsed属正常。每benchmark的serve_manifest保存当时拓扑，后续部署不应覆盖早先采集对应关系。Finalize的summary和捕获任务在可生成索引时的summary是访问线索，下载链接仅确认已有上传，不抹除partial、缺node/rank或控制失败。

download.sh需要Bash/curl，按all/raw/parsed逐项下载、重试、失败停止并保留.part，默认目标profile-download，不负责解压。obsutil递归-j=4属于另一条需要list/read权限的路径，不据打印命令就判有访问权。解析产物的trace_view/kernel/operator/communication/metadata文件依profiler版本与活动生成；重做analyse需匹配采集镜像/软件，本次没有下载、解压或调用工具。

## 基线失败与采集失败分别解释

profiling会影响吞吐、延迟和停止时间，Nightly仍启用原性能基线；基线失败可能同时留下有效trace，不能反过来用trace成功覆盖失败指标。benchmark_ended_before_start、benchmark_ended_before_request_threshold和benchmark_ended分别区分未启动、计数不足和时长不足，目录非空不抹除这些不完整状态。raw存在但parsed缺失先看requested output，再检查Plan/Parse/Finalize和每target/rank错误。

文档给的是控制、取证和入口合同，不是当前CI已执行或全节点数据齐全。核对预期工作负载/节点/rank、实际manifest、请求与控制时点、已上传归档、解析事件和缺失说明；捕获/上传/解析失败按本卡原有分阶段判据保留，最终性能按关闭profiling的可比运行验收。219条译文均匹配及额外英文V4.1用例行，只提供版本化资料对照，不证明模型支持或NPU收益。
