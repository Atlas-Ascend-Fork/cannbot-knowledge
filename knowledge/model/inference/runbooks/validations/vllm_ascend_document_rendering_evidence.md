---
type: Runbook
title: vLLM Ascend 文档构建成功仍缺证据：中文转换与生成脚本
description: 沿generate_zh_docs、MkDocs hook与RTD入口定位页面可见代码的生成来源，区分HTML呈现、脚本生成与NPU部署验证；核对英文回退、旧artifact、版本宏及源码/PO/YAML映射。 补充仓库根make入口、双语nav事件、MiniMax局部TOC和zh-cn反馈路径与发布身份边界。
aliases:
- generate_zh_docs.py
- DOCS_LANG
- rtd_build.sh
- mkdocs.yml
- on_page_markdown
- on_pre_build
- Source not found
- model_code.py
- 文档渲染
- MkDocs
- 中文文档构建
tags:
- task.debugging
- task.testing
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/generate_zh_docs.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/contribution/doc_writing.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/contribution/doc_writing.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/mkdocs.yml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/rtd_build.sh
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.readthedocs.yaml
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/Makefile
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/requirements-docs.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/hooks/model_code.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/generator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/scanner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/docs_codegen/sphinx_extension.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/README.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/hooks/nav_titles.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/hooks/minimax_m3_toc.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/overrides/main.html
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/mkdocs.yml
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/.github/vllm-main-verified.commit
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/.github/vllm-release-tag.commit
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/developer_guide/deepseek_v41_qli_candidate.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/performance_and_debug/msprobe_guide.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/release_notes.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/release_notes.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/feature_guide/mooncake_layerwise_adaptation_and_optimization.md
  role: supporting
- resource: https://docs.vllm.ai/projects/ascend/zh-cn/latest/
  role: supporting
- resource: https://readthedocs.org/api/v3/projects/vllm-ascend-cn/builds/?limit=5
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/tree/7d9e52da97606050f61f33275b9d9a0def86881a/docs/source
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/tree/7d9e52da97606050f61f33275b9d9a0def86881a/docs/source/locale/zh_CN/LC_MESSAGES
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/docs/source/tutorials/models/GLM5.2.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/docs/source/tutorials/models/GLM5.3-Flash.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/7d9e52da97606050f61f33275b9d9a0def86881a/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: supporting
created_at: '2026-10-31T03:30:58Z'
updated_at: '2026-11-04T03:05:50Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 文档构建成功仍缺证据：中文转换与生成脚本

## 信号与范围

文档构建或翻译脚本报告完成，网页却出现未替换model-code、旧脚本、英文残留或版本混淆。这里依据固定Ascend ceac提交的generate_zh_docs.py、MkDocs配置、hook、RTD与文档生成链，定位“原文→PO→中文Markdown→生成脚本→HTML”的证据缺口；未执行上游构建；2026-11-03与11-04分别获取163页公开中文HTML并核对正文，历史快照、刷新差异与仍存在的发布缺陷见文末，保持draft/空平台。安装栈按[版本环境](../../guides/deployment/vllm_ascend_versioned_environment.md)，脚本生成按[模型教程](../../guides/bringup/vllm_ascend_model_tutorial_codegen.md)分别处理。

## 当前源码的构建入口

固定Main使用mkdocs.yml和Material，docs/requirements-docs.txt列MkDocs组件；docs/Makefile提供build/build-zh、serve/serve-zh、gen-zh、clean，没有html/intl。doc_writing.md仍列Sphinx make -C docs html/intl及docs/_build/html预览，这些文字不能覆盖真实构建文件。Makefile中的tools/...与根mkdocs.yml依赖工作目录，按实际入口确认，不能只换一个target就宣称make -C docs已验证。

共享.readthedocs.yaml使用Python3.12、docs依赖和tools/rtd_build.sh；当前没有单独.readthedocs.zh.yaml，其注释要求中文RTD项目也用共享配置。pre_build的生成器调用带||true，成功状态不能证明目标脚本生成完整。保留的Sphinx扩展是另一份实现，不证明当前站点仍由Sphinx构建。

rtd_build.sh中显式DOCS_LANG优先于项目slug，未设置时只有vllm-ascend-cn自动选zh；只有精确zh进入中文分支。中文源目录与宏目录为docs/source/zh，站点URL字面量为/zh/latest，实际HTTP证据已补于文末：/zh-cn/latest可访问，/zh/latest根返回404，不能把二者当成功重定向。READTHEDOCS_VERSION_TYPE=tag只决定release banner，不自动验证源码、模型或运行栈。

本地serve走mkdocs serve --livereload；build走--clean --strict，输出SITE_DIR或READTHEDOCS_OUTPUT/html。脚本未自行切换源码根，真实cwd/配置/依赖另存。这里未运行这些命令，也不把--strict解释成所有生成、翻译或内容判据都已覆盖。

## 为什么构建绿灯仍可能缺代码

MkDocs on_pre_build调用generate_all，只捕获DocsCodegenError并打印Warning，没有在该分支重抛。on_page_markdown再次扫描实际源文件，读取预生成脚本失败时catch Exception并原样返回围栏；扫描本身的异常又不全在这个catch内。警告被吞和未生成块不能由总体成功覆盖，原样代码围栏也不是可执行脚本。

hook独立正则替换输入Markdown，scanner另读源文件，两者的options解析和缩进处理不完全相同；body中的类似option文字可能干扰第二轮选择。hook输出硬编码bash，不按自定义language选择。缺块、名字重复、未知选项、路径错误、旧artifact和未替换分别定位，先保存原始日志及对应块，不直接声称模型部署失败。

默认生成只扫描英文models目录；中文树的文档路径不同，但同stem/block_name会读同一artifact路径。路径存在不证明对应当前英文/PO/YAML；跨目录同stem还可冲突。核对实际HTML中的命令文本、源文档/块名、YAML SHA、生成器版本与artifact SHA，不能仅用页面URL或上一次.sh证明新版本内容。

## 中文生成不是“全部译文已覆盖”

generate_zh_docs.py先重建docs/source/zh，遍历locale/zh_CN/LC_MESSAGES下PO，以相同相对路径寻找英文。找不到英文会打印Source not found后跳过；无译文和无PO则复制英文，资产与图标另复制，样式CSS由rtd脚本补。输出数量混含生成和英文回退，不能换算为完整中文覆盖率。

parse_po_file从polib读非空msgid/msgstr组成字典，未在这里显式处理fuzzy、context或plural资格，重复msgid后值覆盖。有效PO、字符串匹配和无空译也不证明中文语义正确、最终替换覆盖或站点映射；按每条资料固定原串/译文并记录差异。doc_writing的71条与当前英文匹配只证明本次源资料对照。

apply_translations尝试保护围栏code、inline code、URL与链接目标；从原文选择最长且不重叠的替换，避免译文再次被短msgid改写。普通多行段落允许单换行重排回退，但不跨空段落，列表/表格/标题续行保持精确结构。未命中仍留英文，不自动报翻译失败。

apply_translations使用_split_by_code_blocks分段，跟踪反引号/波浪字符，却未按开围栏长度验证关闭长度；三反引号可能提前关闭四反引号包住的文档示例。保护检查只跳过完全包含在受保护span的匹配，不等价完整Markdown语法解析。这里是静态边界，需以真实生成Markdown和HTML检查，未运行翻译器来复现。

## 版本宏与正文分别留证

mkdocs.extra中的release/stable默认v0.23.0与main依赖变量分开，宏缺值配置为keep；Native v0.32.0固定资料又是独立身份。页面有版本字符串不证明同一套安装栈或目标模型支持，不能用更新的数字覆盖所有旧教程。模型支持、硬件、量化和调优表继续按对应知识卡的版本与已验证范围裁决。

教程模板及英文无PO文件可出现在中文树，但不等于已经翻译或实际纳入站点nav。前端全屏表格/代码高亮/宏展开成功也不证明命令、环境或性能。现有源配置只说明预期构建路径；源码配置本身不能证明整站HTML与提交映射；本次公开页对照与逐页构建归属的区别见文末。

## 验收与交付

1. 固定源码提交、文档/PO/YAML/模板/生成器SHA、真实cwd、Python与MkDocs依赖、DOCS_LANG、RTD项目与version/attempt。
2. 核对目标块确实被识别、生成artifact唯一且新鲜、目标YAML一致；原始日志的warning、Source not found、未替换围栏与英文回退逐项说明。
3. 对照最终中文Markdown与HTML中的正文、宏、命令、链接、表格和版本；保存页面获取时间与构建身份，缺映射不报告已闭合。
4. 文档内容通过后，再在目标环境按新模型适配/精度/性能合同执行真实验证；网页发布、脚本非空或构建成功不能替代这些结果。

前次源码批次只读英文497行、中文71条与相关测试定义，没有执行上游工具、安装、清目录、构建/预览/发布、模型或NPU/Agent A/B。


## 仓库根make入口、双语导航和局部目录深度

本节全文补读docs/README.md、nav_titles.py、minimax_m3_toc.py及overrides/main.html四文件。当前README明确所有命令从仓库根执行：make -f docs/Makefile serve/build、serve-zh/build-zh/gen-zh；这为前文旧make -C docs冲突补充直接操作入口，但本次未执行构建。MyST toctree搬nav、admonition/tab/代码围栏与宏语法迁移分别核对，不能只改扩展名。

nav_titles的页面标题按file.src_path查双语TITLES，on_page_markdown直接设置page.title、返回原Markdown，不修改H1或正文翻译。section实际按原英文section title查表递归改名，非模块顶部旧docstring所称first-child文件key；页面标题放此事件是避免read_source重建meta覆盖。DOCS_LANG默认en，未列语言/路径保留原title。名称中Experimental或“实验性支持”只作导航文案，仍须实际模型文档/实现/支持矩阵，不能当新增支持记录。

MiniMax-M3 hook只对src_uri精确等tutorials/models/MiniMax-M3.md且有page.markdown时，deepcopy markdown配置、把toc_depth设4，用独立Markdown重建page.toc；返回HTML完全不变。四级TOC可见不证明正文被翻译、命令生成或NPU功能增加，也不改变全站其他页面深度。

## 预览banner与中文反馈URL不是站点等价证明

overrides/main.html按config.extra.docs_lang取i18n，在非is_release时显示preview banner并指向stable版本。反馈路径由zh→/zh-cn/、其他→/en/，拼rtd_version与page.url；它和前文rtd脚本里的/zh/latest字面量是不同生成位置，应以实际公开URL/HTML核对，不能据模板猜自动redirect或整站已发布。

is_release、rtd_version、stable_vllm_ascend_version与页面源码身份是不同字段，banner出现/消失、反馈按钮链接或nav标题都不替代文档来源SHA。模板只构造Issue链接，本次没有点击/提交外部反馈；装饰logo模板仅负责配色资源，不计独立推理知识覆盖。


## 2026-11-03 公开中文站：163 页正文已经取证

本次冻结抓取窗口为2026-11-03 09:22:49–09:23:21 UTC，不追随后续滚动latest。实际入口[中文latest](https://docs.vllm.ai/projects/ascend/zh-cn/latest/)和163个页面均HTTP200、无跳转，HTML lang均为zh，RTD项目为vllm-ascend-cn/latest。旧`/zh/latest/`根实际404；163页canonical与当前sitemap仍使用这条错误路径，不能把URL替换成功计为redirect。当前sitemap的163项与旧映射清单相同，其中150技术页、13导航页；这次保存了每页HTML、主体和源链接，不再只以URL命中代表内容覆盖。

公开RTD API在本次窗口报告latest成功build **35607584**，commit **5f5e25dd94db85b59251be7d3baf7c808475b6d7**，完成于09:17:44.726763 UTC。这是部署元数据，不是每页的不可变构建证明：页面没有逐页build SHA，edit链接仍指main；147页Last-Modified保留11月2日时间也不能单独判旧版本。实际每页分别与固定5f5e25的英文、PO、递归include和宏值对照。没有把latest API的commit自动填成每页已证明的实际构建commit，也没有改ceac checkout。

独立只读对照程序只把Git对象、PO和HTML当数据，没有导入上游转换器或运行MkDocs。1696个围栏代码块在去共同缩进和外层空行后与HTML逐块字面相同，内部空白和标点均保留；另有3个HTML pre块来自源码缩进的两条uv cache clean和一段sleep中文提示，已核到原文。15443个正文行/表格单元中15436个在去Markdown展示格式后匹配，剩余7项全部定位为下表的发布排版损坏。这个归一化计数不是独立的翻译质量证明、完整浏览器执行、模型或NPU验收。

逐页还核对了文档正文/PO/include依赖SHA、宏和source链接：相对ceac有22页依赖改变，相对3164有12页，版本宏变化单独核对；翻译器、RTD脚本、相关hook与模板没有据发布身份推定执行成功。未发现实际教程残留model-code围栏；doc_writing、multi_node_test、using_lm_eval中所见{{…}}分别是生成占位、GitHub Actions和Jinja评测的字面示例，不计未展开版本宏。

## 11-03 快照：中文外壳不等于完整中文模型教程

11-03快照中18页主体没有中文。其中17页实际已是“自vLLM Ascend v0.30.0起停止维护/后续不再获得support或fixes”的短英文通知，指向历史v0.23.0文档；它们不是latest完整教程。旧PO虽然保有较长中文教程，该次英文通知不匹配这些msgid，所以没有把旧教程重新发布到主体。其已有知识入口统一为[历史模型版本边界](../../guides/models/vllm_ascend_retired_model_version_boundary.md)：

| 17个发布通知页面 | 读取规则 |
| --- | --- |
| DeepSeekOCR2、Hunyuan-A13B-Instruct、InternVL3.5、LLaVA-OneVision-Qwen2-0.5B-OV | 按通知所指历史版本部署，不用旧PO补成最新教程。 |
| Minitron-8B-Base、Mixtral-8x7B-Instruct-v0.1、PaddleOCR-VL、Qwen2.5-Math-RM-72B | 保留固定ceac知识的版本条件，不把停止维护推成所有版本/硬件均无法运行。 |
| Qwen3-ASR-1.7B、Qwen3-Coder-30B-A3B、Qwen3-Embedding、Qwen3-Next | 当前站点的导航名称仍可能保留，但不形成latest完整步骤或维护承诺。 |
| Qwen3-Omni-30B-A3B-Thinking、Qwen3-Reranker、Qwen3-VL-Embedding、Qwen3-VL-Reranker、gpt-oss-120b | 先核发布通知与目标版本，再消费历史配置；不借PO条数恢复当前支持。 |

该次第18页MiniMax-M3.1-Flash没有对应PO，因此实际保留英文教程；这项缺PO/全英文判断只适用于11-03快照，11-04已经变化，见后文。实验性导航和lang=zh不使正文自动变成中文，其他页面也有未命中PO的英文段落，不据此宣称整站已经完成中文翻译。

msprobe_guide的5段实际中文对应PO中标为`#~`的obsolete条目；独立对照纳入这些条目后与HTML吻合。原转换循环没有明确排除obsolete，不能把页面已有中文当该条目已获当前翻译资格。遇正文/PO/发布文字不一致时先固定目标revision，按英文来源核对技术事实，保留所见HTML和译文差异；不要把obsolete译文静默当新规范。

## 11-03 快照已解释的发布缺陷

| 页面/层次 | 公开HTML所见 | Agent择源规则 |
| --- | --- | --- |
| deepseek_v41_qli_candidate | quant mode的1/3/4/5/2被显示为⅓/⅘/2；candidate模式1/2/3变½/3。 | 按固定英文源码的枚举1、3、4、5、2和候选1、2、3读取，不能按分数生成参数。 |
| mooncake_layerwise_adaptation_and_optimization | 测试清单TP=1/2显示为TP=½。 | 原意为TP1/TP2测试组合，非TP=0.5；相关协议见[Mooncake条件增量](../../guides/integration/vllm_ascend_mooncake_layerwise_protocol.md)。 |
| user_guide/release_notes | 三段历史wheel URL中的${PYTHON_TAG}/${ARCH}被数学语法破坏，DeepSeek3.1/3.2显示为DeepSeek3.⅓.2。 | 复制命令/URL前读取固定源文件；保留旧release适用范围，不从损坏显示猜包名或模型版本。 |
| 全163页canonical/sitemap | 仍指/zh/latest，而实际可访问入口为/zh-cn/latest。 | 保存请求URL、final URL和HTTP状态，不能把坏canonical当已成功抓取页面。 |
| GLM5.3-Flash发布配方与Main实现 | 发布文档仍在release维护配方中设enable_dsa_cp=true，同5f5e25 Main ascend_config已不声明该键。 | 先定位目标release维护build与schema，不据公开网页直接给Main设置已移除参数；详见[GLM发布条件](../../guides/models/vllm_ascend_glm53_flash_hybrid.md)。 |

因此本次是**163页均已取得主体并解释差异，0未解释页面**；不是HTML与英文技术语义完全等价，也不是上述发布缺陷已修复。没有修改上游站点、提交外部反馈或执行其代码。

## 发布事实变化必须回到对应版本的知识入口

本次真实发布宏为release vLLM/Ascend0.30.0、CANN/NNAL9.2.1、TorchNPU2.10.0.post7、Triton3.6.0.post2、FLA26.9.1；同一源码Native main pin为24420b7a341af37a9bc3186e6fc6062512e0aa58、release-tag文件为v0.32.0。它们是不同字段，不拼成一套已验证安装栈。已增量融合[版本环境](../../guides/deployment/vllm_ascend_versioned_environment.md)、[Mooncake PCP](../../guides/integration/vllm_ascend_mooncake_layerwise_protocol.md)、[DFlash2图接入](../../guides/integration/vllm_ascend_dflash_runner_graph_contract.md)、[投机选型](../../guides/optimization/vllm_ascend_speculative_method_selection.md)、[TITO/RL](../../guides/integration/vllm_ascend_rl_weight_update.md)、[RFork](../../guides/deployment/vllm_ascend_rfork_weight_warmstart.md)和[GLM5.3-Flash](../../guides/models/vllm_ascend_glm53_flash_hybrid.md)。旧ceac/3164正文保留其明确版本适用，不由一次发布抓取覆盖。

其余已解释小差异：Qwen3-30B-A3B把`--served_model_name`修为`--served-model-name`；DeepSeek-V4-Pro/V4.1-Flash、Qwen3.5-397B-A17B删除部分jemalloc preload，Kimi-K3进一步写明A3/950DT不支持jemalloc；KV Pool去掉模板中硬编码toolkit Mooncake库路径。原canonical卡仍按固定ceac/3164版本读取，不能把这些发布修订反写成原版本已有行为。doc_writing/testing、DeepSeek-V4-Flash、GLM5.2、Kimi-K2.6、Qwen3.8-Flash-Next、additional_config和Fine_grained_TP相对ceac的变化在3164已经出现，本次发布正文与该增量相同；仅新的宏展开另行留证。

原始HTTP和机器对照位于ignored `artifacts/ingest/vllm_ascend/review_fixes/site_evidence/`，manifest逐页包含UTC获取时间、HTTP/final URL、HTML/主体/依赖SHA、源revision对照、owner、代码/正文检查、已知缺陷和空的unexplained列表；它记录设施证据，不替代本卡知识结论。没有执行上游转换/构建、安装、模型、NPU、分布式或性能实验。

## 2026-11-04 刷新：翻译补齐与三项技术修订分别读取

本次重新抓取窗口为2026-11-04 02:59:05–02:59:39 UTC，原163页均HTTP200；与11-03主体相比99页不变、64页变化。固定`7d9e52da97606050f61f33275b9d9a0def86881a`的英文、PO、递归include和宏只作数据解析：1696个围栏代码块全部与HTML匹配，15032个归一化正文单位匹配15024个。它们证明本次内容对应关系，不证明每页来自同一个RTD build；未获取逐页不可变构建身份，也没有运行上游翻译器、构建或设备代码。

64个发生变化的主英文文件逐一比较5f5e25与7d9e，只有下表3页存在英文事实修订，其余61页主英文文件相同。61页中17页是退休通知中文化，MiniMax-M3.1-Flash新增中文PO并在正文显示中文，另43页补齐/调整译文。MiniMax-M3.1-Flash的7d9e PO有143条非空译文，因此前文“无PO/全英文”不能继续描述11-04页面。17页通知仍从v0.30.0起停止维护并指向v0.23.0历史教程，中文化不恢复latest维护承诺；163页主体均已有中文字符也不等于全文翻译完成。

| 页面 | 本次实际变化 | 使用入口与边界 |
| --- | --- | --- |
| GLM5.2（合并GLM-5.2/5.3教程） | 950DT单机W4A4C8命令删除`--enforce-eager`及对应参数解释，其余90个代码块未变。 | [GLM缓存与量化](../../guides/models/vllm_ascend_glm52_glm53_cache_formats.md)区分新启动配方与仍为eager的历史短请求记录；删除开关不证明任何特定图模式已通过验收。 |
| GLM5.3-Flash | 撤回A3 INT8 KPool indexer整段说明；代码块未变。 | [GLM发布条件](../../guides/models/vllm_ascend_glm53_flash_hybrid.md)和[7d9e类型门禁](../../guides/integration/vllm_ascend_7d9e_runtime_delta_contract.md)区分中间版本与最终实现，不能从旧网页继续推荐已撤回的INT8路径。 |
| speculative_decoding | RecoverSSM从普遍禁止PCP改为仅允许TP1、Mooncake的Prefill producer PCP，新增P PCP8/DP1与D PCP1/DP8示例及SD卷积state布局条件。 | [7d9e RecoverSSM](../../guides/integration/vllm_ascend_7d9e_runtime_delta_contract.md)保留PP1/DCP1、禁consumer/colocated PCP、每D接收完整head shards和图模式边界；代码块相同不能用来判定正文技术事实未变。 |

8个静态正文残差已逐项裁决：QLI量化/候选枚举2项、历史release wheel URL/模型名4项、Mooncake TP清单1项仍是11-03已经记录的7项发布排版损坏。另1项为DeepSeek-V4-Pro把“vLLM内嵌的LocalService”写成“内嵌于vLLM的LocalService”，语序等义，配置仍要求所有P/D节点创建同一用途的`mmc-local.conf`。没有把这个匹配失败计成新增技术缺陷，也没有宣称前7项已经修复。

独立读取163页原HTML，canonical仍全部指`/zh/latest/`且与11-03相同；本次静态抽取报告的空canonical字段是抽取缺项，不能解释为网站移除了错误canonical。本轮未重新获取sitemap或探测`/zh/latest/`根，相关HTTP结论继续限定11-03窗口。GLM5.3-Flash配方中的`enable_dsa_cp=true`仍存在，而7d9e Main配置不声明此键；FlashComm与图模式的原版本冲突继续按各模型卡裁决，不因补中文消除。

翻译语义复核集中于17份退休通知、全部数字残差、FlashComm/DSA CP表述、三项英文技术修订及8个静态残差，并检查KVPP/PCP、缓存、运行器、安装和EPLB等变化中的限制条件；没有发现这些已复核范围内新增的翻译丢条件。不是逐句人工证明64页全部译文等义，也没有由source到HTML的对应计数推导所有owner卡已经覆盖全部源码。新证据位于ignored `artifacts/ingest/vllm_ascend/comprehensive_review_20261104/live_site/`，`live_docs_refresh_audit.json`逐页记录分类、实际语义复核范围和剩余未知。
