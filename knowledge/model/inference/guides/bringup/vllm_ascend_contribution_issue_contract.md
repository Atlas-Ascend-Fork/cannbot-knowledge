---
type: Guide
title: vLLM Ascend 社区贡献：Issue分类、治理角色与交付
description: 社区协作中核对Issue状态、类型、owner、治理与历史名录，按实际标签和反馈工作流解释进度，为适配与性能任务保留独立验收证据。
aliases:
- issue-workflow-guidelines.md
- governance.md
- contributors.md
- triage review
- wait-feedback
- issue_label_workflow.png
tags:
- task.implementation
- task.testing
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/community/issue-workflow-guidelines.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/community/governance.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/community/contributors.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/community/issue-workflow-guidelines.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/community/governance.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/community/contributors.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/community/images/issue_label_workflow.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/issue_wait_feedback_command.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/bot_issue_manage.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/schedule_stale_manage.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/issue-labeler.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/workflows/slash_command_dispatch.yml
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

# vLLM Ascend 社区贡献：Issue分类、治理角色与交付

## 消费任务与证据范围

为新模型适配、框架改动与性能问题准备上游讨论材料，识别该找谁审查、Issue还缺什么以及什么可以作为交付依据。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整对照governance、issue-workflow-guidelines、contributors及对应中文消息，完整查看Issue流程图，并读取本卡列出的自动化工作流与标签配置。资料中的规则是上游项目知识，不授予本次会话评论、改标签、派发CI、提名、提交或发布权限。

社区控制面没有整项全硬件/全模型的验证证据，保持draft/platforms=[]。模型支持与真实验收分别看[新模型适配](vllm_ascend_new_model_onboarding.md)和[测试证据选择](vllm_ascend_test_evidence_selection.md)；政策、人员名录或Issue状态均不能替代实现与运行结果。

## 社区协作先分角色与实际权限

上游目标是在Ascend NPU上提供易用、快速、低成本LLM serving，并向vLLM贡献；行为准则引用vLLM社区，角色任命最终由vLLM社区决定。Contributor承担新人接入、社区答疑、RFC和代码评审；至少一项贡献是政策门槛，积极参与也包括Issue/review/社区活动。文档说明Contributor授予Triage，但不能从某人贡献一次或出现在名单中推断当前GitHub角色已经生效。

Maintainer负责方向、路线图、持续代码改进、评审和社区参与；要求深入理解两仓代码、持续高质量贡献、至少一个重要功能及高质量review，由现有Maintainer认可并由vLLM社区最终决定，文档授予write/合并相关权限。成员资格属于个人，不属于公司；同公司或CODEOWNERS/公开贡献记录都不是实时权限查询结果。

任何人可提名新人或提议移除，包括自荐/自行退出，需提供技术贡献、review质量、社区参与或长期不活跃等依据，由现任维护者评估。emeritus可由本人或其他维护者发起，活跃Maintainer简单多数确认；政策保留历史认可与维护权限，欢迎无需重新确认地回归。该政策不证明任何具体账号现在仍拥有权限；本卡没有读取实时协作者接口或发起提名。

## 社区协作中的名录快照

contributors.md标记Updated 2026-09-03、last_commit 3546357838389aa7201d9b44e234f831e98b2fd4；这与本次来源ceac提交是不同身份。源头列18位committers、3位emeritus；573条贡献行只有571个大小写原样GitHub ID，csoulnd和YangShuai52各出现两次，不能说573位不同的人，也不能据此恢复所有现任维护者或Triage账号。

完整573行的用户名、日期、提交显示标签已对照，完整40位目标保留为来源数据，未访问外部用户/提交。源文件第297行、贡献序号319的显示ff43537实际链接170dcbda6260b819b8b16f4630fb3b1a75373500，二者不应规范化成同一提交。需要复核个人贡献时回到固定原始链接与实际仓库记录；历史日期/名单不替代当前权限或适配能力证明。

## 社区协作的Issue分类

| 类别 | 固定标签 | Agent应保留的解释 |
| --- | --- | --- |
| 状态 | triage review、triaged、wait-feedback | 待初审/详细审查、可分类或完成分类、等待外部依赖或反馈；不是执行质量结果。 |
| 状态 | resolved、stale | resolved可来自合并、问答或配置建议；stale表示长期无活动，关闭不等于修复。 |
| 状态 | duplicated、invalid、wontfix | 重复、报告无效/不清晰/不可复现、范围外或近期不做；不自动推出模型不受支持。 |
| 类型 | feature request、RFC、new model、performance、bug | 新能力、重大架构讨论、新模型请求、回退/瓶颈/优化、异常行为。可按实际内容分类。 |
| 类型 | usage、question、documentation、installation | 使用/一般问答、文档、安装部署；问题可能无需代码修改。 |
| 可选priority | high、medium、low | 当前/下一周期优先、常规、可延后；high不是精确日期或服务承诺。 |
| 可选贡献 | help wanted、good first issue | 欢迎社区参与；新手标签要求范围清楚、复杂度低，不说明问题已有人负责。 |

首次响应可加triaged和module标签转给模块维护者，或保留triage review做进一步分析。详细审查还需明确类型、可选priority/贡献标签、owner，最终用triaged替换triage review。正文一处triaged表示已完成评估，第一阶段又用它表示可分类并路由；保存阶段和沟通内容，不从单标签推断owner、根因和分类都已完成。

重复问题解释并链接既有Issue/PR，在无进一步疑问时关闭。英文正文对invalid要求解释、invalid+resolved并关闭，允许作者追问/申请重开；实际流程图的invalid/wontfix分支是解释+resolved后等待作者反馈、无疑问再关闭。流程图第一阶段还含review failed关闭分支。保留图文差异，不据其中一条构造所有场景的强制自动关单策略。

正常处理追踪到实现/已确认的非代码解决，再写resolved并附合并PR或说明；标签表把resolved描述为已关闭，而下述自动化又处理仍open的resolved Issue。状态标签是沟通信号，不能把resolved解释成“完整模型精度与性能通过”，也不能把未resolved解释成无人处理。

## 社区协作的实际标签自动化

bot_issue_manage.yaml只监听issues opened/edited，并要求标题以[Bug]:、[Installation]:、[Usage]:、[Doc]:、[Misc]:之一开头；github/issue-labeler@v3.4配置include-title=1、include-body=0、enable-versioned-regex=0。因此任意RFC/new model/performance标题及正文中的模型名不能靠这条工作流保证自动分类。

.github/issue-labeler.yml完整86行提供的是模块/模型字符串规则：core-features下PD disaggregation、KV cache pool、aclgraph、CPU binding、quantization；advanced-features下long sequence/DPC/PCP、MTP/speculative decode、EPLB；architecture-features下async scheduler、DPLB、post-processing/sampling、FlashComm、RL/verl。模型族还含DeepSeek、Kimi K2/K2.5、GLM5/GLM-4、Qwen3-Next、Qwen3-MoE/Dense、MiniMax、Seedance/Seedream/Wan/Hunyuan/Flux/Qwen-Image、GLM-4V/Qwen3.5/DeepSeek-OCR、Qwen3-TTS、Qwen3-Omni、Emu，以及paddle和310p。

这些是特定正则的标签配置，存在重叠，不是所有新模型的完整分类，也不等于类型/priority/owner/支持矩阵。匹配遵循原JS Action与正则，不能把其中.、\b、负向前瞻等简化成任意子串或用Python模拟结果冒充实际GitHub标签。本批未执行Action或核对实时标签。

## 社区协作的等待反馈与失活处理

Slash broker允许User的PR评论或以/wait-feedback开头的评论进入，并将wait-feedback配置为issue-only。执行工作流不是通用Triage鉴权：固定ALLOWED_USERS为bowgneo、lilinsiman、SOMEONEUNSEEN、ZT-AIA、Dawn952、earthmanylf、LoganJane、Tflowers-0129、evakang777、wangzhishenghw，实际用grep -qw检查。这里保留原检查方式，不把它提升成已审计的严格集合成员验证。授权后仅加wait-feedback标签；不关闭Issue、不证明已解决。

schedule_stale_manage.yaml的issue_comment.created路径，只要Issue标签含wait-feedback就尝试移除；所读job条件没有限定必须作者、User或维护者回复。标签消失因此不证明作者补齐了模型、环境或性能证据。

定时路径cron字面量为0 6,14,22 * * *，分别对resolved与wait-feedback调用actions/stale@v11：每次预算1000操作、days-before-stale=7、days-before-close=14、stale标签、更新后移除stale，并在unstale时移除对应resolved或wait-feedback；PR两个计时均为-1。该配置不是所有Issue从创建起固定21天关闭的保证，实际计时、活动、预算和第三方Action实现/运行还要复核。stale或关闭不能作为修复、无缺陷或取消性能需求的证明。

## 社区协作的适配与优化交付

提交讨论材料时列清新模型/RFC/性能/bug的任务、固定Ascend与Native身份、真实硬件和拓扑、权重/量化/请求负载、复现步骤、原始失败、已做检查与待验项；这些是为下游Agent组合现有适配/性能合同的交付建议，不是声称上游模板强制每个字段。

把owner、标签和讨论结论与代码/配置/测试结果分开存储。重复或非代码解决链接原证据；回退/优化仍要求可比NPU基线，PR合并也不能替代每个硬件/模型组合的精度和性能。命令的权限、API受理和重试结果按[斜杠命令执行证据](../../runbooks/validations/vllm_ascend_slash_action_evidence.md)核对。

四份社区英文共1030行、四PO共165条均匹配当前原串，无空译或历史上下文；这只关闭当前文本对应，不证明全部译文语义、网站HTML或GitHub实时行为。完整贡献行和PNG作为版本化来源保留，没有运行上游命令、CI、NPU或Agent A/B。
