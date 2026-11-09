---
type: Guide
title: vLLM Ascend Pooling 适配：Embedding、Reranker 与任务验收
description: 按 vLLM v0.32 核对 PoolerConfig、embed/classify/token 任务、MaxSim/余弦评分、模板、归一化和维度；用于
  Ascend 适配拆解，硬件运行范围待验证。 另核对 basic模板、内置文件加载和processor/tokenizer后备优先级。
tags:
- task.implementation
- topic.model_serving
- topic.architecture
status: draft
sources:
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/models/pooling_models/README.md
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/models/pooling_models/embed.md
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/docs/models/pooling_models/scoring.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Embedding.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-Reranker.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-VL-Embedding.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3-VL-Reranker.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3_embedding.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Qwen3_reranker.po
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/transformers_utils/chat_templates/template_basic.jinja
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/transformers_utils/chat_templates/registry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/transformers_utils/chat_templates/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/renderers/chat_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/renderers/hf.py
  role: implementation
created_at: '2026-10-30T10:34:53Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T11:21:27Z'
---

# vLLM Ascend Pooling 适配：Embedding、Reranker 与任务验收


## 输入任务与输出合同

本卡取固定原生vLLM v0.32.0文档，只作为Ascend框架适配的任务拆解，未闭合具体硬件与模型运行组合，保持draft/未知平台。Qwen3历史模型维护限制见[历史模型边界](vllm_ascend_retired_model_version_boundary.md)；原生文档的模型表、LoRA/PP勾选不转换成Ascend支持承诺。上游明确不保证Pooling比直接用Transformers/Sentence Transformers更快，收益必须在相同输入和质量目标下测量。

| 任务 | 粒度/输出 | 入口与评分含义 |
| --- | --- | --- |
| embed | 每个sequence一个向量 | LLM.embed或LLM.encode(pooling_task="embed")；bi-encoder两向量余弦评分。 |
| token_embed | 每个token一个向量 | LLM.encode指定任务；late-interaction以MaxSim等后处理评分，不能当sequence单向量。 |
| classify | 每个sequence分类输出 | LLM.classify；num_labels=1的子集可用cross-encoder scoring，分类激活按模型确定。 |
| token_classify | 每个token分类输出 | 显式token任务，可用于NER/reward等；不是通用文本生成。 |

LLM.score是API，不等于仍存在score任务：文档称score task在v0.21移除，改用classify；旧encode任务拆成token_embed/token_classify，但LLM.encode方法仍在。v0.21移除pooling multitask默认行为后，目标不是默认任务时显式指定PoolerConfig(task=...)或pooler-config.task，不靠一个checkpoint名猜任务。plugin任务另有IO processor合同，不在本次实现范围。

## Pooler 与转换配置

VllmModelForPooling使用Pooler提取最终hidden states；runner pooling与Ascend的Model Runner V1/V2是不同维度，见[Runner规则](../../optimizations/rules/vllm_ascend_model_runner_selection.md)。auto通常能选Runner，VLM2Vec/DSE-Qwen2等同生成架构例要求显式pooling；不能把这些例的参数通配给Qwen3或全部多模态。

原生convert可将相应架构转embed或classify：*ForTextEncoding/*EmbeddingModel/*Model及所列Reward命名默认走embed，分类命名走classify，具体仍按真实配置和接口。转换能力不证明模型接受过对应任务训练或质量达标。CLS取首token、LAST取末token、MEAN聚合、ALL保留token、STEP按returned_token_ids过滤；token顺序/padding和真实模型定义必须一致。

pooling_type和use_activation逐字段解析：显式PoolerConfig优先Sentence Transformers metadata，再到架构/任务默认，未设字段继续走后续层。ST的Pooling模块由modules.json定位，compact pooling_mode和旧布尔pooling_mode_*均有处理。仅在没有ST Pooling模块时才走文档所列任务归一化默认；存在Pooling但没有Normalize模块的false不可忽略。自定义pooler可有不同实现。

当前PoolerConfig没有normalize或activation字段，PoolingParams.normalize也已移除，使用use_activation。标准embed/token_embed构建L2-normalization head，classify/token_classify构建分类激活；开关控制是否应用head。分类激活函数选择还遵循HF problem_type、ST activation、label数的优先级，不能用不存在的activation配置任意指定。false可返回未归一化向量或分类logits，不能把它们与归一化余弦/概率阈值结果直接比较。文档的ModelConfig检查示例并非本次执行结果，也不能当完全离线、无配置/remote-code副作用的通用验收命令。

## Score、Rerank 与模板

/score与/v1/score的queries/document输入：单字符串配单字符串为1对；单query配documents列表为N对；两列表按对应位置类似zip，不是全笛卡尔积。列表长度/错误行为仍按实际protocol验证，不能从示例补出任意广播保证。Score响应data[].score与Rerank的results[].relevance_score分开；Rerank默认top_n为documents长度，按相关性排序，index回指原文档顺序。来源示例省略/截取结果不作为精确输出长度的实际测试。

cross-encoder才应用score template；用embedding模型评分不应用它。Scoring文档的请求级use_activation只对cross-encoder生效，不从前文通用Pooler开关反推三种score类型接受相同覆盖。模板messages的query/document语义角色比固定下标可靠，额外instruction和模型规定格式需按真实模板核验。原生Qwen3 Reranker示例使用Qwen3ForSequenceClassification、classifier_from_token=[no,yes]与is_original_qwen3_reranker；VL对应Qwen3VLForSequenceClassification。仅修改architectures不证明classifier/模板/权重和yes/no取值均正确。

原生文档说明Qwen3-VL的qwen_vl_utils与vLLM使用transformers video_processing_qwen3_vl可有不同结果。多模态验收分别固定processor版本、图像/视频采样与chat template、模态token及score转换，不能拿文本成功覆盖图片/视频。其他模型的HF override、trust_remote_code或同族结构只作该模型的条件，不当全局部署默认。

## Embedding API 与尺寸

/v1/embeddings、/v2/embed与/pooling的输出schema不同；/pooling可以是任意嵌套数据，不强制一维浮点。chat-like embedding使用messages及模型对应模板，多模态请求不假定OpenAI SDK有同名高层方法；来源使用底层post不等于所有客户端版本均接受。

Cohere形态/v2/embed以texts、images或inputs之一提供内容；embedding_types可请求float、binary、ubinary、base64。这里是输出表示：binary/ubinary为bit-packed，base64为little-endian float32编码，不能因此推导模型weight或NPU算子量化。input_type取该模型task_instructions或ST prompts中的有效key，其他模型传入会校验失败，不强制统一用query。

truncate=END保留前部、START保留后部、NONE超长报错。输出dimension裁剪属于Matryoshka训练能力；非MRL模型更改dimensions应报错，不能靠is_matryoshka或matryoshka_dimensions覆盖把任意模型“训练成MRL”。这些override仅用于确已支持但未被识别的模型；维度变化后单独验证语义质量、范数和检索排序。

## 分阶段验收产物

先记录checkpoint/architecture、任务、pooling方式、head/激活、模板、processor和输入/输出schema；再比较同输入的真实参考向量/score及下游排序，按任务选择MTEB等数据、版本、split、指标和容差。HTTP200、字段存在、固定维度和服务启动各自留证，均不能代替检索质量。性能固定请求/文档对数、token与视觉负载、并发、预热和统计口径；本卡没有统一更快的承诺或NPU结果。

本批只读三个原生文档正文与所列Ascend历史资料。图、include的protocol/PoolingParams源码、所有池化实现和真实权重仍是独立待闭合范围；没有运行其中代码或调用API。


## template_basic.jinja 的实际作用

固定Native v0.32的vllm/transformers_utils/chat_templates/template_basic.jinja只有三行：逐message拼接message['content']并剥模板空白。没有role标记、轮次分隔或image_url分支；它不负责解码图片、替换多模态placeholder或证明模型支持混合输入。不能把调用前原始content列表与经serving层整理后的模板输入混为一层。

SigLIP2教程中的文件名须解析到实际同版本文件；正确使用还依赖消息预处理、空图像prompt和模型自己的处理规则。通用basic模板不是各类reranker的专属score模板，不能因都叫chat-template就互换。

### 文件加载、内置目录与解析优先级

固定renderers/chat_utils.py的str路径校验/加载会在给定路径不存在或打不开时，按条件尝试CHAT_TEMPLATES_DIR内同名文件；因此template_basic.jinja不必复制到CWD才可使用。Path对象与str分支不同，Path加载失败直接抛错，不走同一内置目录后备。包含{}或换行的字符串可作为字面模板；is_literal=True不读文件且不接受Path，不等于验证所有Jinja可执行。加载器由lru_cache包装，改同名文件不表示每次请求重新读取；记录实际内容与版本。

CLI文件加载与tokenizer中的模板名是两层。hf.resolve_chat_template先取显式模板交给tokenizer.get_chat_template；没有显式值时，仅tools is None才尝试AutoProcessor模板，再尝试AutoTokenizer，尝试失败后才查预定义fallback。空tools列表与None不能机械互换。AutoProcessor结果缓存键含tokenizer身份/revision、code_revision和trust_remote_code，失败None也缓存，静默fallback不代表所有加载层都成功。

chat_templates/registry.py给siglip/siglip2、clip/colpali/paligemma用basic，blip-2、DeepSeek OCR/ocr2与unlimited两种拼写、DeepSeek-VL-V2有各自映射。minicpmv/minicpmv4_6/minicpmv4_7用回调，tokenizer名含4.5或4_5取专属minicpmv45，否则chatml。register_chat_template_fallback_path注册相同model_type会warning后覆盖，get_chat_template_fallback_path对未登记项返回None；映射存在不是Ascend模型维护或硬件支持。包__init__只re-export getter，不是另一次模型/模板全面注册。

内容格式检测还依实际解析后的Jinja，所读缓存键区分tools是否None而不是完整tools内容；具体AST判据未在本批闭合。不要只凭模板文件名猜string/openai content格式，或以为换tools一定重做检测。这里没有渲染模板、构造tokenizer/AutoProcessor、联网获取模型或执行API。
