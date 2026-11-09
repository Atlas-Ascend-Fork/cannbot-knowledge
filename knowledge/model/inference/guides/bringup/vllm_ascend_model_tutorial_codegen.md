---
type: Guide
title: vLLM Ascend 模型教程：YAML命令生成与适配交付
description: 按model-code元数据选择五种converter，核对YAML配置、位置变量、shell文本和生成脚本身份；结合模型教程模板保存版本、权重、硬件与真实功能/精度/性能证据。
aliases:
- doc_writing.md
- doc_writing.po
- model-code
- GeneratorService
- docs_codegen
- BlockScanner
- external_dp_template
- external_dp_launch
- external_dp_proxy
- Model-Deployment-Tutorial-Template.md
tags:
- task.implementation
- task.testing
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/doc_writing.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/doc_writing.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/_templates/Model-Deployment-Tutorial-Template.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/scanner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/converters.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/sphinx_extension.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/yaml_loader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/cli.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/generator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/errors.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_tools/test_docs_codegen.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/hooks/model_code.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/mkdocs.yml
  role: constraint
created_at: '2026-10-31T03:30:58Z'
updated_at: '2026-10-31T03:35:45Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 模型教程：YAML命令生成与适配交付

## 任务与版本边界

把模型测试YAML中的部署配置转换成可审阅的教程命令，并交付版本、权重、硬件、功能、精度与性能证据。固定Ascend ceac提交的doc_writing.md全497行及71条中文消息已对照，另读docs_codegen八个非空模块、模型教程模板与584行现有单测定义。这里只保存生成协议和断言意图，没有运行生成器、单测、模型或NPU；整项流程的硬件范围未知，保持draft/空平台。

模型实现、权重、CLI及请求身份先按[新模型适配](vllm_ascend_new_model_onboarding.md)核对；本卡不复制其运行时协议。网站源码、中文转换、产物与HTML的对应关系见[渲染证据](../../runbooks/validations/vllm_ascend_document_rendering_evidence.md)。生成文件不是部署成功记录。

## 先确认真正被识别的块

BlockScanner默认扫描docs/source/tutorials/models/下全部.md；显式--doc/--block才选择其他文档。MODEL_CODE_OPEN_RE要求三个反引号后为{model-code}，固定指南示例却写成不带花括号的model-code。这些普通代码围栏不会因为语言名相同就被该扫描器识别；MkDocs hook也要求花括号形式。这是源码差异，没有运行示例来声称失败已复现。

三个必需选项是block_name、converter_tag、test_case_path，可选case_index、host_index；未知/空值拒绝。block_name只允许字母、数字、点、下划线和短横线，同一文档内不能重复。选项只在进入body前解析，空行即开始body；同一选项重复出现会覆盖前值，不是重复错误。不要把body里的文字当作已经生效的metadata。

文档路径须相对且无..组件，这是词法检查，未完成所有符号链接边界校验。YamlLoader对test_case_path解析真实路径并检查仍在仓库内、存在，随后safe_load并按路径缓存；存在检查不是完整文件类型、YAML schema或运行时有效性验证。指南中的your_model和旧tests/e2e/nightly目录是示意，实际用固定提交内存在的配置及内容SHA。

## 五种converter不能互换

| converter_tag | 读取范围 | 生成与限制 |
| --- | --- | --- |
| single_node | test_cases[case_index]，默认0 | envs、model、server_cmd及可选server_cmd_extra；SERVER_PORT为None或DEFAULT_PORT时转8000，不验证真实可用端口 |
| multi_node | deployment[host_index]，必须显式索引 | envs及以vllm serve <model>开头的完整命令；不是自动生成整个多机拓扑 |
| external_dp_template | templates[host_index]及顶层model | 补vllm serve并替换七个已知位置变量；仍需对应launcher、主机与shell参数 |
| external_dp_launch | 整个config列表 | 每节点一行launch_online_dp.py，只传七个规定字段；不完整映射PP/CP/SP、nnodes或headless |
| external_dp_proxy | config及routing.groups | 仅disaggregated_prefill，固定NODE_0_IP:1999，按local DP展开P/D端点 |

single_node与multi_node命令字段可为shell字符串或扁平列表，前者shlex拆词；envs必须mapping且拒绝嵌套dict/list。字符串key归一和部分类型检查并未验证合法shell环境名或所有标量类别。完整vllm serve格式器把后续项当flag和至多一个值，不支持任意多值位置参数；--kv-transfer-config有效JSON可美化，其余参数不进行完整vLLM语义解析。

external_dp_template使用RUN_DP_TEMPLATE_POSITIONALS，把VISIBLE_DEVICES、PORT、DP_SIZE、DP_RANK、DP_ADDRESS、DP_RPC_PORT、TP_SIZE依次映射为$1至$7。未知${变量}和裸$SERVER_PORT保留，与外部DP运行时对未知参数变量的严格拒绝不同。host_index是列表位置，不自动验证YAML node_index一致；不要由文档生成结果推实际每rank配置。

external_dp_launch只读取dp_size、tp_size、dp_size_local、dp_rank_start、dp_address、dp_rpc_port、port_start；没有在这里验证NPU预算、全局rank或launcher是否存在。proxy按组索引范围展开port_start+local_rank，但未完成重复/重叠、非正localDP、PP/headless等运行时schema校验。真实配置与就绪验收另见[多节点测试](vllm_ascend_multi_node_test_contract.md)。

## shell文本仍需逐项审阅

生成器刻意保留$变量和位置参数展开。envs在部分空白/特殊字符场景加双引号，转义反斜杠、双引号与反引号；CLI只对部分空白/JSON条件用shlex.quote。render_cli_command直接连接字段。它们不是对任意输入生成完全字面量、安全可直接执行脚本的证明。

核对最终模型路径、served name、版本宏、JSON、环境变量、设备/主机/端口和重复选项。未展开变量、旧目录或占位参数保持未验证；不要为让模板看起来可运行而随意补硬件、模型或性能参数。本批仅阅读这些字符串，没有执行shell、替换环境或生成上游文件。

## 生成、打印与产物身份

GeneratorService按扫描→YamlLoader→converter→body合并→非空校验→写文件处理。body有{{ generated }}时替换所有出现位置；没有标记时实际是把生成内容追加在body之后，文档“始终放标记”不是此分支的强制错误规则。重复标记会复制命令，非空也不证明shell语法、依赖、模型能力或性能。

默认输出docs/_build/doc_codegen/<doc_stem>/<block_name>.sh；路径只取文档stem，不取完整目录。不同目录同stem和block_name可能覆盖，尽管扫描器分别通过文档内唯一性。写入非原子且未维护源码hash/旧产物清单；读取已有artifact只检查存在，不核对YAML/文档新鲜度。

CLI的--doc与--block互斥，block引用按最后一个::拆分；无选择时扫描默认目录。--stdout只增加打印，不关闭写文件，需--dry-run才不落盘；stdout先打印输出路径再打印内容，不可直接把整个输出当纯shell。入口虽调整Python import路径，默认IO仍按cwd，不保证任意工作目录都正确。

零块文档可返回0；CLI只把DocsCodegenError转为1，其他IO/类型/解析异常不全在统一错误合同内。错误上下文可含doc/line/block/converter/YAML路径，有助定位，不能把“没有捕获错误”解释成目标块实际执行过。Sphinx读取artifact时还会使用GeneratedScript默认shell语言，不能仅凭自定义converter.language保证持久化后高亮一致。

## Agent的模型教程交付

Model-Deployment-Tutorial-Template v2.0要求明确正式支持或0day/POC状态、验证版本、支持表与模型权重来源/实际路径。模板中的版本、DeepSeek/Qwen/GLM表行、NPU数、MLAPO/FlashComm和调优数字都只是例子，不新增当前支持承诺；复用时按真实模型与版本证据重写。

交付单机、多机、PD及特殊任务需要的实际启动步骤、参数单位/范围、有效模型路径与API模型名、预期输出和FAQ。模板示例served-model-name与请求model也不必然一致；实际请求使用当前/v1/models身份。启动日志、功能响应、精度数据与性能结果分别保存，完整例子不能替代实际测量。

性能建议覆盖长上下文、低延迟、高吞吐三类实际需求，记录输入输出长度、前缀命中、精度、P/D配比和完整负载；不将一个调优表声称全局最优。按[基准流程](../optimization/vllm_ascend_benchmark_workflow.md)建立可比结果，模型特殊优化再保留来源和限制。

现有tests/ut/_tools/test_docs_codegen.py的584行定义覆盖metadata、重复块、默认/显式端口、索引、命令/JSON、CLI输出、位置变量与proxy渲染等意图；没有运行这些测试，不把assert存在当通过。指南中tests/ut/tools路径滞后。前端全屏表格的thead/首列/rowspan0和sticky-column=false只影响展示，JS/CSS实现与浏览器效果本批未完整核验，不据此改变模型事实。

验收逐项保留原文/PO、最终YAML、所选块、converter/模板版本、生成脚本SHA、最终展开参数及真实运行结果。网页可见代码、脚本非空、单测定义和CI绿灯是不同证据；缺少目标硬件、完整功能或性能结果时保持未验证。本批无上游生成/安装/build/serve/NPU或Agent A/B执行。
