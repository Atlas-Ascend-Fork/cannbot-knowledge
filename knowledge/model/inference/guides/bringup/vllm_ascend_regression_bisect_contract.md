---
type: Guide
title: vLLM Ascend auto_bisect 回归定位：端点、依赖、构建与多节点判据
description: 按固定二分工具追踪整份 YAML、first-parent 提交、依赖漂移、构建身份、跨节点屏障和状态恢复，区分已确认回归与 SKIP 嫌疑区间，避免只按
  first_bad_commit 或退出码下结论。
tags:
- task.debugging
- task.testing
- topic.compilation
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/auto_bisect.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/git_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/good_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/build_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/version_compat.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/coordinator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/worker_agent.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/verdict.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/USAGE_zh.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/bisect/good_table.sample.csv
  role: example
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/dp_mode.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/common/multi_node/test_multi_node.py
  role: implementation
created_at: '2026-10-29T17:03:39Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T17:03:39Z'
---

# vLLM Ascend auto_bisect 回归定位：端点、依赖、构建与多节点判据


## 范围与使用前提

固定来源为 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的`tools/bisect`。本卡追踪工具本体、配置、git/build/version helper、runner、协调与报告；nightly服务/DP运行时、AISBench执行、AOP外层和实际集群另有边界。`--soc`只是Good表查询维度，不证明模型或工具已在任意硬件上验证，故保持draft/空平台。

目标是定位固定工作负载从通过转为失败的候选提交。工具会强制detached checkout、清理构建目录、安装依赖，还会按进程名清理当前驱动进程树以外的vLLM服务。应在专用测试容器、可恢复的隔离checkout及独立输出目录运行，先保存实际源码、二进制、依赖和负载身份；不能把它当成只读查询。本次未运行二分、构建、安装或NPU测试。

## 搜索对象与端点

| 对象 | 实际合同 | 需要保留的边界 |
|---|---|---|
| 一轮试验 | 当前`CONFIG_YAML_PATH`整份文件的全部test_cases；不传pytest -k选单case | 结果是整份YAML的回归，不能自动归因某个内部case |
| 候选序列 | `git log --first-parent --reverse good..bad`，good排除、bad包含，按主线commit原子搜索 | PR号只从subject末尾`(#NNNN)`提取作显示；不是按PR内所有commit逐一验证 |
| 区间合法性 | good必须是bad祖先，候选不能为空，仓库不能仍为shallow | 提交可解析不代表中间历史完整；工具显式拒绝残留shallow候选列表 |
| 端点复核 | 默认先bad必须FAIL，再good必须PASS；SKIP或不符合期望中止 | 禁用端点复核会直接注入假设；单机恢复时缓存的PASS/FAIL也可跳过真实试跑 |
| 失败复测 | 默认额外1次；首次FAIL后任一次复测不是FAIL就转SKIP | 不仅复测PASS，复测SKIP也不成为可信FAIL边界 |

二分还依赖目标回归在所选区间内可用单一好坏边界解释。工具没有证明任意非单调性能变化都满足这一前提；输出候选后应重新验证相邻边界，并固定模型、数据、采样、并行与环境。

## Good 表、版本与数据身份

`--scene`、`--config-yaml`和`--soc`在当前CLI中必填。显式`--good-commit`跳过表查询；否则按name（若给出）、YAML路径/文件名、soc、scene匹配。YAML匹配允许路径后缀或basename相同，因此还需确认确实是同一配置内容。

GoodEntry接受success/pass/passed/ok的状态别名。九列表含name、yaml/path、link、status、vLLM及Ascend Git信息、soc、scene、time。优先选完整soc+scene精确匹配行，再取其中最新成功时间；只有没有精确行才带warning回退到soc和scene都缺失的旧七列行，半缺键的行不匹配。旧表不能证明硬件和场景等价。

时间带时区时转为UTC比较，无时区时保留原值，不可解析时间排最旧。时区不明确、路径同名或旧行来源含糊时，不应把“最新行”直接解释为当前条件下最可靠基线。样例CSV只是schema/格式示例，其中的占位提交和任务不能充当真实Good。

nightly与weekly的流水线表分开；工具CLI本身默认读取`BISECT_GOOD_TABLE`或其默认路径，并不会仅凭scene自动选择某个weekly表。调用者应传正确表与配置，保留实际工作负载revision。

`_resolve_good`保存表中的paired vLLM commit，但当前工具没有据该字段强制切换到那份精确SHA。真正的依赖适配读取每个候选的`.github/vllm-release-tag.commit`、requirements.txt中的torch-npu约束，后者可回退到pyproject build-system。

- 两端pin不同的包逐候选检查；两端pin相同但安装环境漂移的包也会启用适配。
- vLLM版本检测先看`VLLM_VERSION`环境覆盖，之后才看distribution；公共版本比较忽略local build suffix，不是完整commit或二进制身份核验。
- vLLM优先在配置源码目录checkout候选pin并以empty target安装，无目录时回退pip；torch-npu会按目标约束重装。安装成功后的内部override不替代源码/制品核验。
- 单机先build prepare再ensure版本；多机master发布version_targets/version_checks给worker，各节点适配后才ready。`rebuilt=false`仅描述该轮C++重编译决策，不表示依赖和环境完全未变。

## 构建决策与跳跃风险

BuildManager默认假设容器已在当前HEAD构建，bad==HEAD可直接判already built；`--force-initial-build`或`--no-assume-built-head`可撤销这个假设。editable安装只解释Python源码生效，不保证切换后的native库匹配。

| 模式/条件 | 实际行为 | 诊断限制 |
|---|---|---|
| per-commit（默认） | 仅看候选自身相对父提交的改动 | 二分跳跃可能跨过native变化，目标自身纯Python也不代表已装库与其一致 |
| since-build | 对上次成功构建commit与目标做累计diff | 更适合需要确认native差异的跳跃；仍需确认初始构建身份 |
| 无已知构建基线 | 保守重建，但不自动假定所有requirements都需重装 | 环境配套另由依赖策略检查，不能等同完整干净镜像 |
| native/build命中 | 清理build、csrc/build、egg-info、dist及Python缓存，再editable安装 | 真实glob还包括c/cxx、hxx/inc/cmake、so及pyproject/setup.cfg等，不能只照旧文档的cpp/h简表 |
| requirements命中 | 单独重装开发依赖 | 不等于只发生一个源码变量变化 |

成功重建后才推进last_built_commit；纯checkout不会把不同源码误记为新二进制基线。CMake排障日志关注HI_PYTHON、Python3_EXECUTABLE等路径及配置失败尾部；短期uv构建环境路径不能跨轮盲目复用。nightly用例自身的special_dependencies也可能安装包，必须记录有效环境。

## 多节点协议与失败边界

```text
master每次实际部署递增round
  -> 发布command(commit,action,rebuild,version_targets,version_checks)
  -> 全节点deploy/适配 -> ready(node,head)
  -> master等待ready并检查提交前缀 -> start
  -> master/worker各自运行所选pytest入口
  -> verdict 或 DONE；异常路径也发布结束/中止信号
```

所有节点都必须运行二分agent，共享同一轮协调目录；只让worker跑模型用例不会加入ready屏障。节点数优先取显式参数，multi_node否则从YAML的num_nodes读取；不以LWS_GROUP_SIZE代替这个来源。node-index取显式值或LWS_WORKER_INDEX，0为master。

协调文件通过临时文件+rename发布，避免读取半份JSON。master启动清除旧DONE和round目录；worker非run-scoped目录按启动时刻过滤旧DONE/release。不要让不同运行共用会互相重置的目录。State.save另用普通write_text，不能把协调消息的原子写保证扩展为所有状态文件。

master部署失败发布SKIP让worker继续；worker部署失败写不一致ready标记，不启动部分部署测试。没有任何外部worker曾ready而屏障超时会整体abort/退出2；曾加入后死亡的worker仍留下标记，后续可能逐轮SKIP，这不是心跳存活检测。屏障检查的是ready计数和提交前缀，不代替全节点的依赖、制品和实际拓扑一致性验收。

单机/多机复用当前common入口，旧提交可回退legacy入口。当前多机dispatcher按YAML的dp_load_balancing选internal/external，旧配置缺字段才按路径回退。DP运行时、健康端点和AOP日志/释放包装没有在本卡闭合，不把它们的等待时间混作工具CLI默认值。

## PASS、FAIL、SKIP与嫌疑提交

一轮先看基础设施标记和pytest退出码，再读benchmark JSON，详细合同见[结果判据排查](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)。部署/依赖失败和集合错误归SKIP；SKIP表示不能按工具当前判据判断，不证明提交没有引入代码或配置回归。

单机恢复只复用缓存PASS/FAIL，SKIP重新试；多机禁用这个缓存以免省略部署导致round不同步。state按good/bad端点校验，目录键为scene::config_yaml；没有完整硬件、YAML内容、依赖和负载指纹。改变这些条件应新开独立work-dir并重新验证，不能凭端点一样复用过去结论。

当区间内全是SKIP而无法继续收窄时，`_bisect`仍可返回最早嫌疑candidate；run只打印warning，仍可写first_bad_commit、显示FIRST BAD并返回0。JSON没有独立confirmed/suspect字段。下游必须结合trials和已确认PASS/FAIL边界，不能把非空first_bad_commit或退出0等同已确认根因。单机缓存命中也不会生成新的TrialResult，因此本轮trials未必含所有曾经验证记录，需保留state与原始日志。

## 当前默认值与文档差异

| 项目 | 当前代码 | 来源差异及消费方式 |
|---|---|---|
| soc | CLI required，valid_soc拒绝空/unknown等，未注册硬件能力集合 | 中文说明仍写None默认；按CLI与实际表键使用 |
| trial-timeout-s | CLI/Options均7200秒 | 中文参数表5400为旧说明；不是当前默认 |
| native识别 | 更完整glob及build-def列表，默认per-commit | BuildManager概述偏向since-build，不能替代实际模式 |
| vLLM依赖 | 候选pin/环境漂移可触发切换 | 中文前置条件“仅切Ascend、不改vLLM”与现实现不一致 |
| weekly调度 | 工具本体不定义外部定时器 | 中英文对调度的说明有差异；实际dispatcher/外部scheduler未核验，不承诺当前运行时间 |

本次只读源码和文档，没有运行bisect、pytest、服务、fetch/checkout候选、包安装、编译或NPU精度/性能实验。按[模型验收合同](vllm_ascend_accuracy_evaluation_contract.md)和实际制品身份复核后，才将嫌疑提交归为已确认的适配或性能根因。
