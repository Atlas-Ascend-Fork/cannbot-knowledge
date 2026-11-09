---
type: Runbook
title: vLLM Ascend 斜杠命令：重跑、取消与回退的执行证据
description: 斜杠取证区分PR命令鉴权、SHA选择、API受理和真实结果，定位重跑fallback、取消范围、回补撤销与日志归档缺证据。
aliases:
- slash-commands.md
- /rerun
- /cancel
- /cherry-pick
- /revert
- collect_download.py
- rerun-failed-jobs
- force-cancel
tags:
- task.debugging
- task.testing
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/community/slash-commands.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/community/slash-commands.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/slash_command_dispatch.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_rerun_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_cancel_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_cherry_pick_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/pr_revert_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/scripts/collect_download.py
  role: implementation
created_at: '2026-10-31T03:56:56Z'
updated_at: '2026-10-31T03:58:16Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 斜杠命令：重跑、取消与回退的执行证据

## 触发场景与范围

适配或性能Agent看到/rerun、/cancel、/cherry-pick、/revert的Bot成功回复，却无法确认执行范围、实际attempt、代码身份或测试结果时使用。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整读取slash-commands.md及86条中文消息、broker、四命令工作流和collect_download.py；相关社区治理按[贡献与Issue合同](../../guides/bringup/vllm_ascend_contribution_issue_contract.md)。本卡为静态来源合同，无整项设备/模型验证，draft/platforms=[]。

源码里的安装、curl、gh、git push和创建PR都只作资料读取，未执行。上游可用命令不代表本会话已获评论、取消任务、改分支或创建PR授权；Bot反应、API请求受理、工作流完成和NPU业务验收分别取证。

## 斜杠取证：派发与权限探针

slash_command_dispatch.yml仅issue_comment created、comment.user.type=User，PR上下文或以/wait-feedback开头才进入。八命令e2e、rerun、cancel、nightly、cherry-pick、revert、weekly、wait-feedback；配置前七个PR-only、wait-feedback issue-only。permission:none和issue-type:both属于转发层，repository_dispatch后每个执行层还有检查，不能解释成任意人可执行。

四个本卡PR工作流均允许payload中的PR作者，或GitHub collaborators permission接口role_name精确为triage/write/maintain/admin。文档的triage+应按实际枚举理解，不自行把自定义角色名、贡献名录或公司身份当授权。Nightly仅角色鉴权，/e2e允许作者，/wait-feedback固定名单，不能把一个命令的规则推广到全部命令；第三方Slash Action实现和实时权限没有在本批验证。

文档六命令Scope表均PR-only，却又说Nightly --branch主要用于Issue评论；以当前broker限定解释，保留图文/实现差异，不凭该注释承诺Issue也能派发/nightly。/weekly虽未列六项表但在broker登记，完整weekly执行合同尚未闭合。

## 斜杠取证：/rerun的真实选择

查询actions/runs使用payload PR head SHA、per_page=100和created倒序，没有翻页循环或事件类型筛选；total_count缺失默认0，No workflow runs消息不独立证明API健康或确实无运行。保留repo、PR head、run id、workflow name、event、status、conclusion、attempt及请求时间。

先按workflow.name分组取最大run id，再检查状态；同名工作流可能合并，新成功/运行中记录会遮住旧失败。非completed会跳过并写FAILED提示稍后重试；event=workflow_call跳过，由caller重跑。其余只接受failure/cancelled/timed_out/startup_failure/action_required，不选择success等结论。

先POST rerun-failed-jobs，HTTP201计入受理数；其他返回码会尝试POST rerun，HTTP201计为整条工作流重跑。因此文档“成功任务不动”仅符合失败任务重跑路径，fallback可能重跑已成功job，不能把文档句子提升为保证。原失败和新的attempt分别保留，不混用同run不同attempt产物。

两次API都失败会进FAILED列表，源码没有仅因该列表非空就最终exit1；末尾仍可hooray。rerun_count是HTTP201计数，不是完成/通过次数；No failed jobs也可能是按name去重、状态或conclusion过滤所致。实际验收看新的attempt是否开始、收集哪些测试、skip/失败、业务精度和性能，不能用评论completed覆盖原失败。

## 斜杠取证：/cancel的实际边界

同样仅查PR head SHA的第一页100条；选择status!=completed并排除SELF_RUN_ID，POST force-cancel。HTTP202只表示源码计为成功受理，没有轮询终态；409/410被源码当已终态跳过，其他状态写FAILED，最终可正常评论hooray。cancel_count不等于已终止任务数或资源已回收。

文档“不影响Slash和Nightly/weekly”解释依赖它们通常在main工作流SHA运行。当前cancel实现没有按名称、event或Nightly族显式排除；若手动等其他事件恰为相同SHA，也可能进入选择，这是静态范围推断，未实际取消任务。反过来，下游模型使用PR代码不代表其run head_sha就是该PR head。

出现“取消成功但仍运行”时核对查询SHA、100条上限、实际run/attempt、202与终态、并发创建的新run以及各下游身份，不重复把命令名当作用范围。取消不是适配失败根因或模型不支持证据，原日志和产物是否保存另验。

## 斜杠取证：/cherry-pick不是逐提交复制

目标参数仅经xargs处理并检查非空，未在此明确校验单一合法分支语法；随后fetch目标及payload base/head，错误可被忽略，rev-parse验证origin/target。没有要求PR已合并；PR base...head三点diff从merge-base到head生成补丁，git apply --3way后以PR标题和元数据做一个提交，区别于文档笼统“cherry-pick PR commits”。

DIFF_FILE为空时消息称already_included，但该diff不比较目标分支内容；空PR差异本身不独立证明目标已含预期修复。apply冲突设置conflict并失败，目标存在也不证明依赖、构建或模型行为兼容。

fork仓固定为PAT owner/vllm-ascend，分支cherry-pick/pr-<number>-to-<target中的/转->；先git push -f，再查open PR。重复调用可刷新原PR分支；并非总创建新PR，也不是合并。实际标题是[Cherry-pick][<target>]前缀，区别于文档少目标标记的例子。

PR list失败被忽略，create失败还会从错误文本提取首个GitHub pull URL当既有PR。success/refreshed/返回URL均需核对真实repo/base/head/commit、PR状态、review和测试，不能以字符串或hooray判回补完成。

## 斜杠取证：/revert与Bash控制流

先gh pr view取实时state、mergeCommit、baseRefName等，要求MERGED和非空merge SHA；目标为原base分支，验证origin/base及cat-file对象存在。它不在这里验证完整祖先链，也不枚举rebase合并的全部PR提交；不能承诺一个mergeCommit就完整逆转所有历史改动。

源码意图先git revert -m 1，捕获错误后abort，在文本含is not a merge时尝试普通revert。实际默认shell为bash -el，REVERT_OUTPUT=$(git revert ...)没有放入if等条件保护；在-e语义下非零可能先退出，来不及执行$?捕获、abort、fallback和revert_status。此为静态控制流风险，未在上游执行复现，不把注释当已实现且可靠的回退合同，也不保证冲突专用评论一定触发。

后续若到达push/PR路径，使用revert/pr-<number>-to-<base>、PAT fork、force push及既有open PR刷新，与cherry-pick一样需要核对真实分支。即便PR创建成功也仅是待审查的撤销建议，需验证目标修复范围、反向依赖、正确性与性能，未自动合并或回滚部署。

## 斜杠取证：下载请求解析与节点身份

/nightly --log-path的模型选择、Native ref、AOP与profile入口按[Nightly合同](../../guides/bringup/vllm_ascend_nightly_ci_dispatch_contract.md)和[剖析产物](../../guides/optimization/vllm_ascend_aisbench_profile_artifacts.md)。当前文档仍只概述A2/A3，实际B81矩阵已有五SoC；测试例名、release v0.24.0/Native v0.29.0示例不证明当前安装版本、别名或模型支持。/e2e仅PR测试路径及实际runner优先级见[测试证据选择](../../guides/bringup/vllm_ascend_test_evidence_selection.md)，不接受任意nightly/models/doctest目录。

collect_download.py的parse_request使用object_pairs_hook=_DownloadObject保留重复node键，区别于普通json.loads覆盖重复键。接受裸路径/JSON字符串、node到单路径字符串的对象、或每项只有一个node/path的对象列表；同node重复累积。{"node1":["a","b"]}不是支持的路径列表值，嵌套对象或非字符串也拒绝。外层单引号可剥一层；前缀判定前不主动strip空白，文档要求紧凑无空格JSON仍要遵守实际评论前端约束。

node键必须node0、node1等无前导零，只有提供--node-count时才校验范围；默认node0是逻辑映射，不自行认作某个物理host/rank。相对路径基于/vllm-workspace/vllm-ascend，绝对路径在测试容器内，不在调用者工作站。--list数值排序节点并打印路径JSON数组；--path-for-node对缺失节点可无输出而成功，空stdout不等于已收集。

## 斜杠取证：路径检查与归档完整性

validate_path拒绝空/控制字符、..路径分量、根目录、受保护根及其祖先/子孙；保护包括/proc、/sys、/dev、/run、/etc和若干/root凭据目录、/tmp/kubeconfig。还排除路径中的.git/.ssh/.aws/.kube、.env及.pem/.key文件。parse/list/check-only的require_exists=False不检查存在性或符号链接；实际采集另要求文件/目录存在且路径及父目录非symlink。

archive_path对多输入增加path-1/、path-2/，单输入保留原布局。os.walk不跟随symlink，跳过常见凭据目录/文件、非普通文件和输出归档自身；空目录没有独立归档项。此处没有端到端文件清单SHA、大小预算或所有节点完成证明，过滤也不等于已经检测任意敏感内容。

--check-only不写tar，缺目标节点、路径无输出、已有归档或一次上传成功都不能替代预期文件清单。文档单节点download-artifact.tar.gz、多节点nodeN.tar.gz及Artifacts入口是定位约定；完整runner接线、取消时保留和所有节点上传未在本批闭合。保留请求原串、解析映射、实际node/容器路径、排除/缺失说明、tar成员和run/attempt，再与模型/性能结果关联。本批没有运行collector、下载、压缩、上传或任何GitHub写动作。

## 验收与停止条件

| 原始信号 | 不能直接得出 | 需要补的证据 |
| --- | --- | --- |
| eyes/hooray、Bot completed、workflow绿色 | 命令范围正确、所有API成功、测试通过 | 鉴权/输入、原始状态码、每个目标及run/attempt和退出原因。 |
| HTTP201/202、count>0 | 重跑完成、任务终止、资源释放 | 目标运行终态、新attempt与实际job记录。 |
| PR URL、success/refreshed | 修复已回补、完整回滚、已合并/部署 | 真实repo/base/head、diff、review、业务回归。 |
| 空diff、无失败任务、空stdout | 目标已包含修复、原失败解决、日志齐全 | 原始选择集合与过滤、目标树/请求、预期节点和文件。 |
| artifact非空、CI通过 | 新模型正确或性能获益 | 固定配置、完整模型精度、可比NPU基线与原始结果。 |

无法证明目标身份或范围时先记录未决项，不以修改阈值/删失败/扩大平台来完成验收。四PO165条的原串匹配、来源固定和检索通过均不是外部Action、HTML、真实CI或NPU/Agent A/B执行证明。
