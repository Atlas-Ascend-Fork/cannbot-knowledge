---
type: Guide
title: vLLM Ascend静态接口门禁：版本区间、调用与返回协议及skip语义
description: 使用固定接口分析器的公开合同解读Native区间对Ascend的override、import、direct-call和返回值影响，区分新增破坏、历史不兼容与unknown；核对fail-on和pytest将introduced
  break转skip的边界。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/analysis_plans.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/test_vllm_pr_interface_compatibility.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/__main__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/call_contracts.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/cli.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/generator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/models.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/range_analysis.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_interface_contracts/vllm_ci.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/vllm_interface/vllm_test.cfg
  role: supporting
created_at: '2026-11-03T05:04:28Z'
updated_at: '2026-11-03T05:07:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend静态接口门禁：版本区间、调用与返回协议及skip语义

## 适用范围与未展开边界

本卡提取ceac接口分析器的公开计划、CLI、报告模型和被选中的MRO/调用/返回/分类路径。大文件generator、call_contracts、range_analysis按所列函数有界阅读并遍历AST结构，未宣称全部解析器算法、分支绑定、别名或Python语义已穷尽。分析器将源代码作为AST和Git快照，不导入目标包、不要求NPU；本次也没有运行该工具、pytest、Git fetch或上游源码。

## 先固定比较的三个身份

记录Ascend实际SHA、Native old/base和new/head；verify_range解析不可变提交并要求old是new祖先，verify_head要求checkout HEAD与预期Ascend身份相等。CI wrapper用Native HEAD及fetch main后的merge-base构造区间，浅克隆可unshallow，因此该wrapper包含网络/Git副作用，不作为资料读取时的自动探针。对本地未提交修改的语义仍需另核，不能仅拿分支名代替版本身份。

计划版本4仅支持vllm-interface场景：inheritance MRO是前置，不单独产生finding；override、direct_import和direct_call被分析；monkey_patch明确跳过。继承信息用于找到override真正owner，不等于所有继承变更都直接判破坏。不能把整个工具名称理解为所有Ascend补丁或Native API兼容已检查。

## 调用参数与返回值必须分别判定

call_shape计位置参数、关键字名及动态*args/**kwargs；不含嵌套star的字面list/tuple可展开，字面dict同一展开内重复key按dict语义去重，而跨展开重复仍保留。精确调用用signature.bind，动态调用只可bind_partial：已能证明的重复关键字/绑定错误为False，动态展开阻止精确证明时为None，不能误报兼容。签名无法表示也保持unknown。

返回替代要求上下游返回合同均exact、正常返回可观察且protocol相同；下游每个变体要落入上游接受范围。未证明的名义类型或动态shape返回None，不能把unknown当兼容。返回使用另检查await、同步/异步迭代及context manager协议；把awaitable当普通值消费、await非awaitable或不匹配context协议可形成明确不兼容。未结构消费的结果可不施加返回shape约束；结果逃逸/动态消费仍是unknown。

MRO解析遇cycle、未解析base或无法线性化会保留complete=False与reason，不拼造完整父类序。relation按exact key去重并合并证据、描述符、签名合同和override path；不同描述符变体可降为unknown，不能从一个代表节点推所有分支。完整绑定解析仍需阅读对应实现或实际目标版本。

## 区分新增破坏与历史问题

| old / new兼容状态 | 分类含义 |
| --- | --- |
| True → False | introduced_break，区间引入明确破坏。 |
| False → True | fixed。 |
| False → False | preexisting，不应当作本区间新增回归。 |
| True → True且合同变化 | compatibility_warning。 |
| 无法证明、动态或其他未闭合状态 | analysis_unresolved。 |

新引入合同单独按new=False/True/None映射introduced_break/warning/unresolved。报告保留old/new SourceEndpoint、签名/描述符/返回合同、downstream位置、confidence、evidence、gates、方向和建议；建议不能替代源证据，也不自动授权改代码。

CLI fail-on=never默认不以finding失败；introduced只对actionable_introduced_break返回1；unresolved把新增破坏或analysis_unresolved都纳入失败。其余分析异常走错误路径。门禁退出0必须连同fail-on和summary解释，不能单凭退出码宣布全面兼容。

## pytest桥接有意把破坏转成skip

固定CI测试在缺/workspace/vllm时skip，存在checkout却无Git元数据时fail；它用analysis_workers=3/index_workers=4构造fail-on=introduced的命令并保留stdout/stderr。分析器返回1时，该pytest用例调用pytest.skip而不是fail；其他非零才pytest.fail。因此出现introduced interface break时，外层测试可显示skip而非红灯，必须检查分析报告和原始返回码，不能用CI绿色证明没有接口破坏。

静态接口分析不证明二进制ABI、NPU算子、数值、通信、模型权重或性能通过；结合[模型适配证据](vllm_ascend_test_evidence_selection.md)补真实目标环境验证。


## CI呈现、快照读取与环境身份

README明确该检查只把选定版本和phase timings及Markdown finding写入pytest stdout，不产生持久JSON/CSV/Markdown报告、不自动上传artifact；分析范围不是main2main。三个分析分支保持各自base/head cache，四worker索引后按源顺序合并并做全局finalization；Git blob通过长度分隔cat-file读取，失败不能当symbol缺失。prefix memo和别名优化是单run内部缓存，不跨版本、worker或CI运行复用。

README将NPU job标soft-fail，这再次说明CI呈现不是强制合并门禁或设备验证。vllm_test.cfg固定了构建测试镜像的CANN9.1.0-910b Ubuntu22.04/Python3.12基座名称；这是该文件的环境输入，不自动等于ceac发布fragment的CANN9.2基座或实际运行镜像，须分别记录。
