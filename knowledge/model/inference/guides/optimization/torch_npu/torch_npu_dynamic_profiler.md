---
type: Guide
title: dynamic_profile：热配置、显式触发与断点步数
description: 说明三种启动路线、start_step、rank 过滤、start 文件路径和恢复训练的计数边界。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/dynamic_profile.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/PROF_CONFIG_PATH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/KINETO_USE_DAEMON.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/KINETO_USE_DAEMON.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/PROF_CONFIG_PATH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/dynamic_profile.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_config_context.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_config_context.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_non_intrusive_profile.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/module_loader.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_non_intrusive_profile.py
  role: implementation
created_at: '2026-11-09T02:54:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# dynamic_profile：热配置、显式触发与断点步数

## 版本与范围

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的相应接口文档，限定 A2/A3。主线配套仍需核验，不回推为 26.0/PyTorch2.8 已支持所有选项。未运行采集或分析实验。

## 选择一种启动路线

不手动添加dynamic_profile的PROF_CONFIG_PATH自动注入方式仅训练使用，依赖原生 Optimizer.step 划分迭代，不支持自定义 Optimizer，也不采 step0。需要训练或在线推理自行划步时，用 dynamic_profile.init(目录) 创建/监视 profiler_config.json，每轮业务后调用 step()。缩小到指定代码窗口则在 init 后显式 start(config_path)，业务放在 start 与 step 之间。不要同时用多条自动注入路线。

init 接收目录，start 接收具体 JSON 文件；start 的示例省略文件名不能照抄。start 文件缺失或无效时回退 init 目录配置，不代表此次采用了预期配置。

## 生效与排队

JSON 的 start_step 默认 0 表示不采，-1 为保存配置后的下一 step，正整数为指定步。热配置通常在未来步设置，需考虑业务持续推进和轮询延迟；采集中修改配置不会立即打断当前窗口。监视日志与 dp 日志分别记录配置加载和实际采集动作，不用文件保存时间直接当作实际起点。

显式 start 只触发一次，不持续感知其配置文件修改。init 采集正在生效时 start 不生效，结束后才可另起；start 期间的 init 配置更新在当前采集完成后处理。

## Rank、恢复与解析

is_rank=True 时按 rank_list 选择有效 rank；列表为空不采集，指南对此路线建议离线解析；具体实现还区分async_mode，见下文。JSON analyse 默认 False，与普通 trace handler 默认自动解析不同，不能混用默认值。

恢复训练前用 dynamic_profile.set_state({"cur_step":已完成步数})，值为非负整数；若不设，重启位置被当作 step0。固定实现确认该字典结构，不能只传一个整数，也不能把绝对训练步和当前进程相对步混用。set_state 的产品页没有 950，本卡不据 init 的 950 支持扩大恢复接口范围。

路径规则在指南与接口页对连字符描述不同，按实际安装版本检查，使用无软链接的可读写路径。异常终止可能残留 DynamicProfileNpuShm 共享内存，须先确认残留对应已退出任务，再依运行环境处理，不批量清理其他进程资源。


## 使用后核验

先检查采集窗口、rank、线程、活动类型与配置是否生效，再核对实际产物和业务开销；缺少数据不等于该阶段耗时为零。关闭调试配置后再测正常性能。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)

## 环境变量启动页的补充约束

固定 PyTorch 主线的 PROF_CONFIG_PATH 页要求目录可读写且不为软链接，路径组成按文档采用字母、数字和下划线；它会在目录中创建 profiler_config.json 模板。该文档与接口页对路径描述存在差异，部署时仍应核对实际版本，不能根据模板文件存在认定本次配置已被采集器采用。

KINETO_USE_DAEMON=1 用于 msMonitor nputrace 触发 dynamic_profile；不手动改脚本的路线限训练，手工 init/step 后可用于非训练场景。需要明确选择环境注入、显式模块或外部触发的实际路径，避免把训练自动划步规则套到推理。

## 环境页的默认值与路径文字边界

中英文KINETO_USE_DAEMON页只给值1的启用示例，没有声明该变量的默认值，不由示例推定默认已启用或关闭。两语言也都允许手动导入dynamic_profile、init目录并逐步step后用于非训练；因此“环境变量方式仅训练”的限制指无脚本改动的自动注入路线。

PROF_CONFIG_PATH页一面称路径由字母、数字、下划线组成，一面示例包含`/home/...`路径分隔符；保留这处文字与例子的差异，不据该句实现拒绝所有斜杠的新校验。目录可读写、无软链接和训练自动创建profiler_config.json模板是明示条件；950DT出现在这两份环境页不覆盖set_state等其他接口的产品限制。

## 轮询、日志老化与共享内存身份

两语言长指南明确初始每2秒轮询，检测修改后按相邻step间隔调整、最小1秒；不是保存文件即刻生效或每次修改都排队一份。配置文件模式下当前采集中多次修改后只处理最后一次状态；主线Dynolog队列另见下文，实际起点继续看执行日志。

dp日志记录AI任务进程动作，monitor_dp日志记录配置加载和监控进程，文件名中的OS/PID/rank分别归属；各主日志及一个.1备份上限均为200KB，旧记录会老化，缺少早期日志不能证明当时未执行。原文列表torch_npu-profiler.dynamic_profile.set_state的连字符是排版差异，不新增一个Python模块名。

来源按Py3.7将DynamicProfileNpuShm+时间文件放配置目录的shm，≥3.8放/dev/shm；正常退出清理，异常终止可能残留并影响短时间内复用同配置路径。该历史Py3.7说明不扩展当前主线安装范围；识别任务与已退出状态后处理具体残留，不执行批量删除或把目录存在当故障。

## 配置文件模式与Dynolog队列不能合并

完整读取两版dynamic_profile.py后确认：发布维护一个待执行cfg_ctx，主线配置文件模式同样以新配置替换待项；主线Dynolog模式另有上限5的队列，使用非空REQUEST_TRACE_ID去重、最多保留10000个历史ID后淘汰最旧项。已过start_step才到达的项可被丢弃；截止前入队但被前项延误的配置可延迟执行并告警。这些不是所有采集路线统一“只处理最后一次”的合同。

两版ConfigContext.valid均在rank命中且async_mode=False时关闭_analyse；主线/发布实现没有对异步解析也无条件关闭的同等分支。因此上文“rank路线自动解析不生效”按指南的保守用法消费，实际代码条件需分清，不能据它宣称异步解析必然可用。配置默认、rank与产物仍须核验。

set_state仅主线新增，字典cur_step写入计数，不加载训练checkpoint，不重置其他采集状态。请求trace ID用于配置状态，不直接作为profile的custom_trace_id_callback；详见[动态接口](../../../apis/torch_npu/profiler_dynamic_control.md)和[trace ID](../../../apis/torch_npu/profiler_trace_id.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/dynamic_profile.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/PROF_CONFIG_PATH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/KINETO_USE_DAEMON.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/KINETO_USE_DAEMON.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/PROF_CONFIG_PATH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-init.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-set_state.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-start.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-dynamic_profile-step.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/dynamic_profile.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_config_context.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_config_context.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_dynamic_profiler/_dynamic_profiler_utils.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_non_intrusive_profile.py)（implementation，1-71 全文）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/module_loader.py)（implementation，:92-101、:160-185）

## 非侵入入口的静态实现链（主线增补）

上文「不手动添加dynamic_profile的自动注入方式」的实现锚在主线 `_NonIntrusiveProfile`：`torch_npu/_init/core/module_loader.py:175` 在 `_C` 子模块就绪后的初始化序列里调用 `_initialize_profiler_if_needed()`（:92-101）——要求 `torch_npu._C._profiler` 已初始化（否则 RuntimeError），随后 `_NonIntrusiveProfile.init()`（`profiler/_non_intrusive_profile.py:41-71` 全文）。该入口随 torch_npu import 执行，不依赖用户手动调用 profiler 模块。

`init` 的门链：读取 `PROF_CONFIG_PATH` 与 `MSMONITOR_USE_DAEMON`；检测到 `KINETO_USE_DAEMON` 时打印弃用告警（请改用 MSMONITOR_USE_DAEMON）；daemon 值不能转 int 时打印错误并按 0 处理；配置路径为空且 daemon 不为 1 即返回、不注册任何钩子。配置了 `PROF_CONFIG_PATH` 时经 `PathManager.check_input_directory_path` 校验，无效则打印错误并放弃启用（有效时 `is_dyno=False`）；无路径且 daemon=1 时 `is_dyno=True`，把 `DynamicProfilerUtils.DYNAMIC_PROFILER_MODEL` 设为 `DYNO_CONFIG`。最后 `dp_init(prof_config_path)` 并注册 optimizer step post hook（:31-39，hook handle 非空即返回，幂等；重新注册会先清零计数）。主线环境页目前只有 KINETO_USE_DAEMON 的文档，MSMONITOR_USE_DAEMON 是代码层新名，旧名仍被接受。

钩子语义（:23-29）：按 optimizer 实例在 WeakKeyDictionary 中维护各自累计步数；当某个 optimizer 的累计步数超过 `_profiler_step`（初始 0）时调用一次 `dp_step()`，并把 `_profiler_step` 推进到该 optimizer 的当前步数。分步因此从第一个原生 Optimizer.step 完成后开始（step0 不采）；多个 optimizer 时由最先超过当前 profiler 步的那个驱动；自定义 Optimizer 不经 `register_optimizer_step_post_hook` 的 step 不触发——这正是上文「依赖原生 Optimizer.step 划分迭代、不支持自定义 Optimizer、不采 step0」的实现依据。

版本边界：发布 pin f3ecfe4a 同名文件 diff 级全文对照为另一套实现——发布版改写 `torch.optim.Optimizer._patch_step_function`（PyTorch<2.0 走 `_hook_for_profile`）包装类级 step 并记录最后使用的 optimizer id，dynolog 模式另有 Python≥3.8 检查；主线重构为 torch 的 `register_optimizer_step_post_hook` + 每实例计数。本节为静态阅读，未启用任何 profiling；上文 KINETO_USE_DAEMON 的文档合同在两 pin 仍分别核对。
