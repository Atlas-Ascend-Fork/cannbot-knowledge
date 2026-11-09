---
type: Guide
title: vLLM Ascend Nightly CI：命令派发、PR矩阵与回归证据
description: 用/nightly、workflow_dispatch与nightly_config定位实际测试，区分PR SHA、工具和模型配置，核对维护窗口、all/560T筛选、accuracy组及profiling参数缺口，再按真实run与产物验收。
aliases:
- Nightly CI
- /nightly
- Nightly-A2
- Nightly-A3
- Nightly-A3-560T
- nightly_ci_test.md
- nightly_ci_test.po
- pr_nightly_command.yml
- nightly_config.yaml
- resolve_nightly_tests.py
- NIGHTLY_COMMAND_BLOCK_WINDOW
tags:
- task.testing
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/nightly_ci_test.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/nightly_ci_test.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_nightly_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/configs/nightly_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/resolve_nightly_tests.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_a2.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_a3.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_a3_560t.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/slash_command_dispatch.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/update_good_table.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/conftest.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/aop_capture.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/aop_classify.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/aop_commit_age.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/aop_process.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/aop_skip.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/bisect_args.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/scripts/rules-env.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_e2e_nightly_single_node.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_e2e_nightly_single_node_560t.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_e2e_nightly_single_node_models.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_e2e_profile_parse.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_nightly_wait_for_pods_ready.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_selected_tests.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/_selected_tests_upstream.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/configs/daily_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/configs/weekly_config.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/labeled_download_model_dataset.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_supplement_new_tests.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_test.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_daily_test.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_doc_getting_started_test.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_doc_linkcheck.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_doc_translate.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_e2e_upstream_test.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_main2main.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_310p.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_nightly_test_a5.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_test_coverage.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_weekly_test_310p.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_weekly_test_a2.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_weekly_test_a3.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_weekly_test_a3_560t.yaml
  role: implementation
created_at: '2026-10-31T02:43:03Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T05:13:26Z'
---

# vLLM Ascend Nightly CI：命令派发、PR矩阵与回归证据

## 任务与证据范围

为新模型适配或性能回归选择Nightly测试、确认运行了哪份PR代码与模型配置，并定位可复核的结果。主来源是固定Ascend ceac提交nightly_ci_test.md全717行及中文219条，另全文读命令工作流962行、矩阵386行、解析器159行和Slash broker；A2/A3/A3-560T只读输入、矩阵与下述作业选段，不声称完整复用工作流、安装、部署或硬件执行闭合。

当前矩阵含a2、a3、a3-560t、310p、a5五类；这些是CI选路，不是所有硬件/模型组合支持或已通过证据。整套控制面与目标设备的适用集合未完成验证，保留draft/platforms=[]。通用CPU/NPU、精准CI与/e2e见[测试证据选择](vllm_ascend_test_evidence_selection.md)；本卡不扩大当前会话的提交、评论或触发授权。

## 评论、事件与执行层鉴权

实际链路是created issue_comment中的User/PR上下文，经Slash Command Dispatch产生repository_dispatch(nightly-command)，pr_nightly_command.yml再以gh workflow run、--ref main触发各Nightly-*的workflow_dispatch。broker的permission:none只描述转发层；执行层仍按GitHub API role_name精确允许triage/write/maintain/admin，公开贡献记录或CODEOWNERS链接不证明调用者已有权限。这里的Nightly鉴权也不沿用/e2e允许PR作者的规则。

下游已读on只有workflow_dispatch，没有原生cron；schedule_是流水线族名前缀。指南表里的Cron daily与其另一个“外部automation调度”说明不一致，保留实际已读触发面；外部定时器未验证。指南所称push后synchronize自动复用评论，在这条已读链中没有闭合额外hook证据，不保证仅推新提交就会重跑。普通PR CI的synchronize存在也不能替代Nightly运行记录。

## 命令参数以解析器为准

指南将/nightly等同/nightly all，但固定工作流先拒绝空ALL_ARGS，解析后也拒绝空TEST_CASES。因此要提供明确测试名或all；单独--profile也不能补出测试范围。--branch默认main，用来选择测试分支/镜像路径；--vllm-ref另指定Native SHA/tag/branch，语法合法不证明实际安装身份或ABI兼容。

--aop_enabled必须放在至少一个测试名之后；good/bad/retries/timeout等二分参数又必须在它之后。good只接受7–40位hex，bad允许HEAD或7–40位hex，额外失败重测为非负整数、timeout为正数。AOP是捕获、环境/代码分类再定位的外层入口，不替代[二分工具合同](vllm_ascend_regression_bisect_contract.md)的端点、依赖和可判定性。不同SoC实际转发的bisect/download/profile字段不完全相同，不把一个入口的接受字段当所有后端已接通。

本快照存在明确的静态解析缺口：PENDING_OPTION等于--profile-benchmark-names时，分支只写benchmark_names、没有清空PENDING_OPTION；后续flag或循环结束的缺值检查仍会报错。此结论来自源码控制流，没有运行命令、CI或NPU；不能因此说全部profiling都失效，也不能默默改写文档示例后宣称已验证。先核对目标提交是否修正该路径，再采用对应接口；下游profile_options_json与normalize是另一层，不能用其字段存在证明评论解析已通过。

--log-path尾部缺值有显式检查；--branch的NEXT_IS_BRANCH路径没有同样的EOF检查。未知--选项会拒绝，但不能据此推断所有不完整参数都被完整校验。Bash set -f避免把*或?展开为runner本地文件，resolver仍是精确集合匹配，不提供模糊测试名选择。

## 维护窗口与测试范围

NIGHTLY_COMMAND_BLOCK_WINDOW按北京时间UTC+8解释HH:MM-HH:MM，可带true/1/yes/on或false/0/no/off，大小写不敏感、空格或逗号分隔。已读有效范围分支是start inclusive、end exclusive，跨午夜用两段OR；相同起止为空窗口。未设、明确关闭及到达格式/越界校验的非法值会放开，不将任意输入或工具错误都承诺为fail-open。命中窗口只使本评论路径不派发并回复窗口，不说明其他外部调度已经停止。

Nightly all默认置A2、A3、310P、A5四个派发标志，不含A3-560T；all --a3-560t则只置560T。指定名字时，默认在a2/a3/310p/a5里精确匹配；--a3-560t改查其命名空间，accuracy斜杠选择有独立例外。不要把这些Nightly分支直接推广为weekly全套或各后端实际资源均可用。

nightly_config.yaml是当前源数据，文档测试名称表已经滞后。例如文档的multi-node-glm-5.2与实际multi-node-GLM-5.2-w8a8-A3不是已证明别名；文档MiniMax-M3-W8A8-A3与矩阵EAGLE3后缀项也分别核对。文档A3 multi-node空表不能覆盖当前4条配置；矩阵列出用例本身不证明其权重、模型名或性能已验收。

外层先选SoC工作流，随后生成该SoC矩阵，以完整的逗号包围name做should_run过滤。矩阵作业存在、should_run字段存在或一个SoC被派发，都不证明目标pytest/模型实际执行。保留name、os/runner、tests或config_base_path+config_file_path、size及最终有效YAML，再读具体模型与场景定义。

A3输入映射仍暴露single_node/multi_card，作业也存在；因此不能仅因当前矩阵没列a3.multi_card就判“新增该节”的操作示例无效。已读策略中multi-node max-parallel2、double-node4、single-node9分别属于不同阶段，multi-card未显式设同一上限；它们不构成全局NPU资源容量或所有场景的固定节点数保证。

## accuracy组与单模型选择

accuracy-group-1/Qwen3-8B在resolver里按首个/拆成group和model；只检查group是否在A2名称集合，不在这里验证model确实属于该组。它重写test_cases为group,model并立即break，后续选择不再处理；之前置出的其他SoC标志可能仍保留。按当前实现不要将多个这种选择器或普通用例混作一个已验证组合，最终看下游model_list、model_filter与实际收集结果。

A2的pr_only作业按filter!=all且包含相应group来决定，不是仅按PR事件或request_id。因此PR上显式all也跳过pr_only；非all的手动调用不因缺PR SHA就在这一条件被排除。组名中的pr或运行显示PR均不是执行来源证明，具体模型过滤实现仍需对应复用工作流证据。

矩阵获取、base64/YAML/类型等错误在dispatch解析器里可被转换为空名字集合；无匹配意味着未选中，不是模型不受支持或测试已通过。mode=matrix的缺路径/非list会输出[]，其解析错误与dispatch模式的容错又不同，先区分配置问题和业务失败。

## 四种身份与运行链接

分别保存工作流定义SHA、实际vllm_ascend_ref、矩阵blob/配置SHA、Native vllm_ref及最终安装身份。--ref main选择工作流定义；模型测试PR SHA来自PR head查询；外层矩阵随后从pull/<number>/head动态读取，连续push可能使两次取值漂移。这是源码路径上的并发风险推断，未复现竞态，不把PR分支名当不可变配置身份。

下游setup-vars把PR configs检出到./pr，普通分支代码/解析器另行检出；profiling工具明确来自github.sha的profile-source，不因模型测试使用PR SHA就自动覆盖为PR里的工具代码。request_id还影响显示名和并发组：同ref/SoC/request_id可cancel-in-progress，其他PR仍可并发。显示Nightly-* (PR)不能单独证明源码真的来自PR。

派发后用sleep8再查该工作流最新一条run来生成链接，没有按PR SHA/request_id严格关联；并发运行可能导致链接指向其他run，这是静态风险而非已观测事故。核对实际run输入、提交、attempt、job与配置。post-links在失败路径也可运行，Bot消息、rocket或任务已派发不代表NPU测试成功。

## 结果、剖析与回归交付

YAML驱动测试的AISBench outputs与benchmark_results JSON、框架/plog归档、profiling小索引和OBS大trace分别追踪。指南称AISBench输出artifact保留7天、profiling索引90天，OBS另按桶生命周期；存在的节点才进入产物，不以一个下载链接证明全部目标齐全。多节点stdout主要是首节点，其他节点按归档与拓扑逐项核对。

Nightly的--profile选项只面向YAML/AISBench performance，不给任意pytest或accuracy增加采集，weekly profile不支持。三种名称、采集窗口、raw/parsed和部分完成判定见[定时剖析产物](../optimization/vllm_ascend_aisbench_profile_artifacts.md)；profiling改变负载时间，正式性能仍用不启用采集的可比运行。

保留pytest退出、实际case数/skip/失败、配置与原始预测/性能、顶层和task判据，再按[benchmark结果合同](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)判断。退出0、没有派发、SKIP、上传成功或profile成功分别不是适配完成。新模型先建立可复核正确性基线，再验证量化/图/并行/投机组合及性能；AOP嫌疑提交也需实际复测。

219条msgid均匹配当前英文、0空译/历史上下文，另保留未进入PO的DeepSeek-V4.1-Flash-W8A8-DSpark-PCP表行，该名字确实在当前a3-560t.single_node中，但CI登记不证明部署通过；字符串匹配不消除文档与实现差异。20项文档限定和22项实现限定在生产证据中保留，完整复用工作流、外部Action、集群、SDK/存储及真实执行仍未闭合。本批没有评论、派发CI、安装、运行上游代码、服务或NPU/Agent A/B。


## good_table与设备测试超时的真实边界

update_good_table.py用soc+scene+标准化完整yaml/path作为替换key；旧七列记录无soc/scene时按路径迁移，显示name相同不会自动合并不同场景。写入持有跨进程文件锁，临时文件flush/fsync后os.replace发布；SoC占位符、空路径和非法scene拒绝。

CLI自身直接构造status=success，不读取pytest退出、模型结果或阈值。只有调用方确认真实测试成功后才可据此更新；CSV中的success不是脚本独立验证的运行证据。配置base/path、Native与Main实际SHA、run链接和场景共同保存；目录存在不保证对应依赖可运行。

nightly算子conftest在import阶段初始化Triton device properties并enable_custom_op，不作为当前Agent只读导入入口。singlecard测试完成后尝试同步并恢复原default device，CPU通过set_default_device(None)移除dispatch mode。它还记录每文件超过120秒的case；达到5个后，该文件后续case会pytest.skip。故总退出与测试数需同时看PASS/FAIL/SKIP及实际参数，不能把后续跳过当算子已验证。上述机制仅源码阅读，未执行测试或NPU。


## AOP日志分类与基线新鲜度不能替代复现

aop_capture把任一上游outcome=failure判failure；没有failure时，只要任一路success即可判success，其余情况才skipped。它从日志最后一条pytest summary与FAILED计数提取展示，缺日志可直接返回，不能以汇总success证明所有YAML/pytest目标都执行齐全。

aop_classify只扫描已标失败的路径，用rules-env.txt正则匹配，将Timeout/engine启动超时等判env_failure；这是基于日志字符串的启发式，不证明根因一定在环境，也不排除代码造成相同错误。aop_skip只是展示为什么未继续二分，不能改写原始失败。

aop_commit_age要求明确soc及single_node/multi_node，缺CSV、无success行、日期不可解析会输出is_old=true和age99。它按显示name、SoC/scene筛选success，再按日期字符串选最近记录，按整天年龄与阈值比较；legacy无维度行仍可能参与。注意这与新good_table writer按完整path+soc+scene替换的key不同，同名跨path需核原始记录，不能只取显示name认定正确基线。

aop_process将场景、bad commit、good table及可选config/name/node协调参数交auto_bisect。bisect_args按Bash数组转发参数并强制native-check=since-build；函数显式return0，避免set-e因最后一个可选空参数提前中断。禁验good/bad等flag是取证强度变化，不因为可传入就推荐省略端点验证。本次只读脚本，没有二分、清环境、部署或运行测试。


## 固定其余调度文件：事件与实际Job分开

下表来自当前YAML的on与jobs声明，不执行外部Action或推导所有shell已成功。workflow_call是复用入口；workflow_dispatch/repository_dispatch/schedule/pull_request分别保留，不从schedule_文件名推cron。weekly/daily配置是选择数据，与前述nightly矩阵、实际模型YAML和运行结果分层。

| 来源 | 声明事件 | Jobs/复用入口 |
| --- | --- | --- |
| _e2e_nightly_single_node.yaml | workflow_call | e2e-nightly |
| _e2e_nightly_single_node_560t.yaml | workflow_call | e2e-nightly |
| _e2e_nightly_single_node_models.yaml | workflow_call | e2e-nightly |
| _e2e_profile_parse.yaml | workflow_call | prepare; parse; finalize |
| _nightly_wait_for_pods_ready.yaml | workflow_call | poll |
| _selected_tests.yaml | workflow_call | selected-tests; upload-coverage-to-obs |
| _selected_tests_upstream.yaml | workflow_call | e2e-upstream_pr |
| daily_config.yaml |  |  |
| weekly_config.yaml |  |  |
| labeled_download_model_dataset.yaml | pull_request | download-models |
| pr_supplement_new_tests.yaml | pull_request_target | upload-merged-new-tests |
| pr_test.yaml | pull_request | pre-commit; cpu-ut→./.github/workflows/_selected_tests.yaml; recommend-tests; select-tests; prepare-csrc-cache→./.github/workflows/_ensure_csrc_cache.yaml; run-selected-tests→./.github/workflows/_selected_tests.yaml; run-selected-tests-upstream→./.github/workflows/_selected_tests_upstream.yaml; run-selected-tests-a5→./.github/workflows/_selected_tests.yaml; ci-gate |
| schedule_daily_test.yaml | workflow_dispatch,repository_dispatch | select-all-tests; ensure-csrc-cache→./.github/workflows/_ensure_csrc_cache.yaml; run-all-tests→./.github/workflows/_selected_tests.yaml; daily-select-tests; daily-dispatch-a2; daily-dispatch-a3; daily-dispatch-a3-560t; daily-dispatch-a5; update-estimated-times |
| schedule_doc_getting_started_test.yaml | workflow_dispatch,pull_request | plan; quickstart; installation |
| schedule_doc_linkcheck.yaml | schedule,pull_request,workflow_dispatch | linkcheck |
| schedule_doc_translate.yaml | schedule,workflow_dispatch | translate |
| schedule_e2e_upstream_test.yaml | schedule | resolve-tag; ensure-csrc-cache→./.github/workflows/_ensure_csrc_cache.yaml; e2e-upstream_singlecard; e2e-upstream_multicard; e2e-upstream_online |
| schedule_main2main.yaml | workflow_dispatch | resolve-source; ensure-csrc-cache→./.github/workflows/_ensure_csrc_cache.yaml; main2main |
| schedule_nightly_test_310p.yaml | workflow_dispatch | parse-trigger; setup-vars; build-image→./.github/workflows/_nightly_image_build.yaml; single-node-tests→./.github/workflows/_e2e_nightly_single_node.yaml; parse-single-node-profiles→./.github/workflows/_e2e_profile_parse.yaml; merge-benchmark-artifacts |
| schedule_nightly_test_a5.yaml | workflow_dispatch | parse-trigger; setup-vars; build-image→./.github/workflows/_nightly_image_build.yaml; multi-node-tests→./.github/workflows/_e2e_nightly_multi_node.yaml; single-node-tests→./.github/workflows/_e2e_nightly_single_node.yaml; parse-multi-node-profiles→./.github/workflows/_e2e_profile_parse.yaml; parse-single-node-profiles→./.github/workflows/_e2e_profile_parse.yaml; clear-pre-logs; merge-benchmark-artifacts |
| schedule_test_coverage.yaml | workflow_dispatch | select-full-tests; ensure-csrc-cache→./.github/workflows/_ensure_csrc_cache.yaml; run-full-tests→./.github/workflows/_selected_tests.yaml |
| schedule_weekly_test_310p.yaml | workflow_dispatch | parse-trigger; setup-vars; build-image→./.github/workflows/_nightly_image_build.yaml; single-node-tests→./.github/workflows/_e2e_nightly_single_node.yaml; merge-benchmark-artifacts |
| schedule_weekly_test_a2.yaml | workflow_dispatch | parse-trigger; setup-vars; build-image→./.github/workflows/_nightly_image_build.yaml; single-node-accuracy-tests→./.github/workflows/_e2e_nightly_single_node_models.yaml; single-node-accuracy-tests-pr-only→./.github/workflows/_e2e_nightly_single_node_models.yaml; clear-pre-logs; merge-benchmark-artifacts |
| schedule_weekly_test_a3.yaml | workflow_dispatch | parse-trigger; setup-vars; build-image→./.github/workflows/_nightly_image_build.yaml; multi-node-tests→./.github/workflows/_e2e_nightly_multi_node.yaml; double-node-tests→./.github/workflows/_e2e_nightly_multi_node.yaml; single-node-tests→./.github/workflows/_e2e_nightly_single_node.yaml; clear-pre-logs; merge-benchmark-artifacts |
| schedule_weekly_test_a3_560t.yaml | workflow_dispatch | parse-trigger; setup-vars; build-image→./.github/workflows/_nightly_image_build.yaml; single-node-tests→./.github/workflows/_e2e_nightly_single_node_560t.yaml; multi-card-tests→./.github/workflows/_e2e_nightly_single_node_560t.yaml; merge-benchmark-artifacts |
