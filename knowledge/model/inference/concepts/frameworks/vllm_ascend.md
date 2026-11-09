---
type: Concept
title: vLLM Ascend 插件架构：平台、通用注册与多进程初始化
description: 解释平台与通用插件注册、Worker与EngineCore补丁的进程安装、VLLM_VERSION版本门控及判断缓存；按真实符号、依赖和初始化时机核对。
  对照旧指南核对惰性 ModelRegistry、debug 覆盖和 KV dtype 检查。 补充孤儿 getting_started.po 的插件定位和旧导航边界。
  明确旧 Getting Started 的孤儿译文、同路径英文缺失与导航身份。
tags:
- task.design
- topic.architecture
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/__init__.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/setup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/plugins/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/platforms/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/index.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/index.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/patch.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/patch.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_engine_core.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/envs.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/modeling/adding_a_new_model.po
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/registry.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-10-29T08:35:04Z'
updated_at: '2026-11-04T02:53:33Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 插件架构：平台、通用注册与多进程初始化

## 适用范围与执行分层

本文分别分析 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与独立 vLLM `v0.32.0` / `5df63a7203cdb9328d824a27b682e77c7b9928be` 的入口与调用点。**这不是一套已验证的安装组合**：该Ascend提交的`.github/vllm-main-verified.commit`实际指向Native `544f182d9f0c9bfe8bd7645525951d5e3692a542`，独立5df只用于上游接口对照；pin文件也不能代替当前机器的安装与运行验收。实际环境先按[版本化环境卡](../../guides/deployment/vllm_ascend_versioned_environment.md)记录双仓commit、包版本和设备，再选择对应代码段。RL rollout的历史集成另见[训练场景卡](../../../training/concepts/frameworks/vllm_ascend.md)。

vLLM 负责推理框架，Ascend 通过平台、Worker、后端及算子适配执行链。源码仍有 patch，安装插件并不意味着整个实现完全没有上游替换。新增能力先定位已有扩展点，再核对目标版本的实际接口。

## Agent按任务进入知识链

| 任务 | 首读入口 | 读完应能回答 |
| --- | --- | --- |
| 新模型从零适配 | [新模型接入](../../guides/bringup/vllm_ascend_new_model_onboarding.md) → 本卡注册与进程时序 | checkpoint架构字符串解析到哪个类；哪个进程安装patch；权重、processor和缓存接口分别还缺什么 |
| 确定硬件与Runner | [硬件能力](vllm_ascend_hardware_profiles.md) → [Runner选择](../../optimizations/rules/vllm_ascend_model_runner_selection.md) | 实际设备、有效Runner及后端是什么；示例硬件声明是否覆盖当前组合 |
| 判断正确性证据 | [测试选择](../../guides/bringup/vllm_ascend_test_evidence_selection.md) → [精度验收](../../guides/bringup/vllm_ascend_accuracy_evaluation_contract.md) | 哪些是mock、静态配置或真实运行；用什么断言判断权重/数值/接口正确 |
| 吞吐或时延回退 | [性能基准流程](../../guides/optimization/vllm_ascend_benchmark_workflow.md) | 基线与改动的环境/负载是否可比；瓶颈证据与优化收益是否分开记录 |
| PD、外部缓存或重试异常 | [PD传输生命周期](../../guides/integration/vllm_ascend_pd_transfer_lifecycle.md) → [代理请求生命周期](../../guides/bringup/vllm_ascend_example_proxy_orchestration_contract.md) | 缓存何时可读、谁持有/释放资源、首包后是否会重试；不能只看HTTP状态 |
| 迁移到固定7d9e | [运行时迁移](../../guides/integration/vllm_ascend_7d9e_runtime_delta_contract.md) | 采样、存储、权重、PCP、TopK、KPool、回放、MLA、QSA及PLE哪些行为已变；未列差异仍须按目标源码核对 |

卡片中的固定版本结论只适用于所列源码。文档声明、静态调用链与运行结果分别使用，遇到未读依赖或未知硬件组合时回到具体入口补证；不把一处未知扩展成整条链不可用，也不把注册成功当成整模型验收。

## 两类入口承担不同职责

| Entry point 组 | Ascend 插件名称 | 入口职责 |
| --- | --- | --- |
| `vllm.platform_plugins` | `ascend` | `register()` 返回 `vllm_ascend.platform.NPUPlatform` 的类路径 |
| `vllm.general_plugins` | `ascend_kv_connector` | 注册 KV/encoder-cache connector 及权重传输 engine |
| 同上 | `ascend_model_loader` | 注册 netloader 和 rfork loader |
| 同上 | `ascend_service_profiling` | 准备 service profiling 配置 |
| 同上 | `ascend_model` | 调用 Ascend 的模型注册函数 |

通用插件由上游 `load_general_plugins()` 执行，进程内有已加载标记；平台类通过 `current_platform` 的惰性解析取得。`VLLM_PLUGINS` 按插件名称过滤 entry points。若显式过滤，必须核对实际留下了哪些平台与通用入口；平台激活不能替代模型、connector 或 loader 注册。

vLLM 平台解析要求至多一个已激活的树外平台插件，多于一个会报错；没有可用平台时可得到 `UnspecifiedPlatform`。显式 `VLLM_TARGET_DEVICE=cpu` 在该 vLLM 版本有独立优先路径，不能用 CPU 环境里的平台结果证明 NPU 注册正确。

## 配置、patch 和 Worker 的时序

`NPUPlatform.pre_register_and_update()` 提前调用平台 patch，并补充 Ascend 量化和缓存 dtype 的 CLI 选择；量化注册还按硬件实现族分支。`check_and_update_config()` 应用 Ascend Runner 选择、同步扩展配置，执行模型/并行/图等检查后调整有效配置。用户输入值不一定等于最终值。

`adapt_patch(is_global_patch=True)` 导入 platform patch；默认调用导入 worker patch。通用入口中的 `_ensure_global_patch()` 在 connector、loader 和 profiling 注册之前应用进程级 patch 和 Runner 配置补丁，进程内防重复。模型注册入口本身不调用该函数，不能假设任意一个通用入口都完成相同初始化。

Worker 接收序列化配置后，重新应用 Runner property patch、同步扩展参数并加载 Worker patch；随后注册算子、初始化 AscendConfig、校验构建与运行时设备。配置对象的序列化不会自动携带对类定义作出的 monkey-patch，这是需要跨进程重新初始化的原因。

## 新能力应从哪里接入

模型架构映射进入模型注册；模块级 NPU 替换进入已有 CustomOp 机制；设备操作、Attention 和通信后端分别沿平台返回的接口；connector 与 loader 使用其通用入口。平台差异沿[硬件能力契约](vllm_ascend_hardware_profiles.md)确认，Runner 决策见[选择规则](../../optimizations/rules/vllm_ascend_model_runner_selection.md)。

必须使用 patch 时，标明目标上游版本、进程、原始符号、导入时机和退出条件，验证每个真正消费该符号的进程。只在测试进程导入补丁，不足以说明独立 EngineCore/Worker 进程已生效。

## 验证与边界

先查看已安装包的 entry points 和插件日志，再确认实际平台、Worker、Runner、后端及注册类；分别测试离线和在线、多进程启动。注册成功只说明入口可解析，后续还要验证权重、缓存、正确性和性能。本次核对源码与上游文档，没有执行 NPU 运行测试。

## Evidence

- Ascend `setup.py` 与 `__init__.py`：插件组、名称、注册函数和进程级初始化。
- Ascend `platform.py`、`utils.py` 与 `worker/worker.py`：配置、patch、Worker 初始化调用点。
- vLLM `plugins/__init__.py` 与 `platforms/__init__.py`：插件过滤、执行和平台解析。


## 用实际架构字符串定位接入点

固定模型注册文件有29个architecture映射。下表按同一惰性目标合并别名，用于从checkpoint config或drafter配置定位实现；它不是支持模型表，也没有逐类证明硬件能力。大小写、`CausalLM`/`ConditionalGeneration`以及`DeepSeek`/`Deepseek`均按真实字符串匹配，不能由展示名称自动拼接。

| config/草稿 architecture | 惰性目标（公共前缀 `vllm_ascend.models.`） |
| --- | --- |
| `Gemma4ForConditionalGeneration` | `gemma4_mm:AscendGemma4ForConditionalGeneration` |
| `KimiLinearForCausalLM`、`KimiK3ForCausalLM` | `kimi_k3:AscendKimiLinearForCausalLM` |
| `KimiK3ForConditionalGeneration` | `kimi_k3:AscendKimiK3ForConditionalGeneration` |
| `KimiK3MTPModel` | `kimi_k3_mtp:AscendKimiK3MTP` |
| `K3DSparkModel` | `kimi_k3_dspark:AscendK3DSparkForCausalLM` |
| `DeepseekV4ForCausalLM` | `deepseek_v4.model:AscendDeepseekV4ForCausalLM` |
| `DeepseekV4ForConditionalGeneration` | `deepseek_v4.vl_model:AscendDeepseekV4ForConditionalGeneration` |
| `DeepseekV41ForCausalLM` | `deepseek_v41.vl_model:AscendDeepseekV41ForCausalLM` |
| `MiniMaxM3SparseForCausalLM` | `minimax_m3:MiniMaxM3SparseForCausalLM` |
| `MiniMaxM3SparseForConditionalGeneration` | `minimax_m3:MiniMaxM3SparseForConditionalGeneration` |
| `DeepSeekV4MTPModel` | `deepseek_v4.mtp:DeepSeekV4MTP` |
| `DSparkDraftModel` | `deepseek_v4.dspark:DSparkDeepseekV4ForCausalLM` |
| `DeepseekV41DSparkModel` | `deepseek_v41.dspark:DSparkDeepseekV41ForCausalLM` |
| `LlamaForCausalLMVwnEagle3` | `llama_eagle3_vwn:Eagle3VwnLlamaForCausalLM` |
| `Qwen3DSparkModel`、`Qwen3OmniDSparkModel` | `qwen3_dspark:AscendQwen3DSparkForCausalLM` |
| `Glm5DSparkForCausalLM` | `glm5_dspark:Glm5DSparkForCausalLM` |
| `DFlash2DraftModel` | `qwen3_dflash2:DFlash2Qwen3ForCausalLM` |
| `DeepSeekMTPModel`、`DeepseekV32MTPModel` | `deepseek_mtp:AscendDeepSeekMTP` |
| `GlmMoeDsaForCausalLM` | `deepseek_mtp:AscendGlmMoeDsaForCausalLM` |
| `Qwen3_5ForConditionalGeneration` | `qwen3_5_vl:AscendQwen3_5ForConditionalGeneration` |
| `Qwen3_5MoeForConditionalGeneration` | `qwen3_5_vl:AscendQwen3_5MoeForConditionalGeneration` |
| `Eagle3LlamaForCausalLM`、`LlamaForCausalLMEagle3` | `llama_eagle3:AscendEagle3LlamaForCausalLM` |
| `Glm5NextForCausalLM` | `glm5next.model:Glm5NextForCausalLM` |
| `Glm5NextForConditionalGeneration` | `glm5next.model:Glm5NextForConditionalGeneration` |
| `Glm5NextMTPModel` | `glm5next.mtp:Glm5NextMTP` |

KimiK3ForCausalLM是旧checkpoint的兼容别名，与KimiLinearForCausalLM落到同一个文本实现；KimiK3ForConditionalGeneration单独映射多模态包装。DeepseekV41ForCausalLM的名字不能证明纯文本路径，目标位于vl_model，具体能力须读其实现。Qwen3_5的两项注册显式覆盖上游同名映射，注册文件说明其NPU图像预处理目的；仍要验证实际加载类与processor。

MTP/DSpark/DFlash2/Eagle3条目用于相应投机路径，不能把草稿架构当主模型替代项；Qwen3OmniDSpark与Qwen3DSpark共享目标不意味着两个target模型的所有输入/KV协议相同。GlmMoeDsaForCausalLM的实际目标也须按表确认，不能只按文件名或MTP后缀分类。

排查“架构未找到/加载了上游类”时，依次保存config.architectures、已启用的ascend_model通用入口、实际消费进程与最终惰性目标，再检查类解析/权重。别名能解析仅关闭“注册名”这一层缺口；完整模型实现、权重加载、图/并行及精度仍是独立验收项。


## 中文首页定位声明的使用范围

固定index.md与index.po将vllm-ascend定位为社区维护的Ascend硬件插件，沿硬件可插拔接口将NPU接入与vLLM解耦。中文7条业务译文中6条msgid对应当前英文；剩余一条是英文设备名称补入Huawei后的字符串差异，社区维护/Ascend后端这层定位未改变。此处没有复核首页链接的上游Hardware pluggable RFC正文，也不把DeepWiki当作实现证明。

首页将Transformer类、MoE、Embedding和多模态列为模型类别介绍；这是入口定位，不是对每个checkpoint、SKU或功能组合的支持承诺。实际架构解析、权重、后端与硬件范围仍沿本卡执行链和模型矩阵分别确认。首页有这些独立定位事实，不能只因文件名是index就当纯导航跳过。


## 中文补丁设计与当前进程安装点

patch.md与patch.po的16条有效业务msgid均连续匹配当前英文；这只确认译文对应源码字符串，设计里的历史版本/路径示例仍须与目标提交核对。文档要求尽量使用上游扩展点，必要的patch记录原符号、Why、How、上游PR或暂缺原因、Future Plan移除条件，并添加UT/E2E；这些是贡献要求，不等于本次执行了测试或所有存量patch已有完整验收。

最小接入顺序是确定目标上游版本与消费进程，选platform/worker目录，加入真实导入点，再在patch/__init__.py登记。仅创建patch_xxx.py不让它自动生效；只有父目录导入、相应硬件/依赖条件满足并且消费进程执行到该入口，才有安装可能。该登记文件内的旧环境变量备注也不能覆盖当前读取代码。

| 已读安装点 | 作用与边界 |
| --- | --- |
| pre_register_and_update → adapt_patch(is_global_patch=True) | 导入patch.platform，并按parser实际存在的choices补量化/dtype；不是遍历并运行所有补丁文件。 |
| NPUWorker.__init__ → apply_v2_model_runner_config_patch、sync_v2_extra_kwargs、adapt_patch() | Worker重装Runner类修改并导入patch.worker，之后还有按配置调用的RecoverSSM patch及算子/配置初始化；序列化VllmConfig不携带父进程类定义修改。 |
| platform/worker的__init__.py | 导入含硬件能力、HAS_TRITON等分支；310P草稿graph manager在通用安装后另覆盖。仅看到目录或通用导入，不能推导每个子patch都在所有硬件执行。 |
| patch_engine_core.py | 当前已导入的模块将EngineCoreProc.run_engine_core替为staticmethod包装，初始化AscendConfig，按CPP开关装profiling补丁，按DyntraLB优先、否则balance选择DPEngineCoreProc，再调用捕获的原入口；有进程内_PATCHED防重。 |

旧设计称默认只修Main/Worker，并建议完整替换EngineCoreProc/DPEngineCoreProc；当前所读EngineCore包装已给出特定子进程接线，不能机械照抄“完整重写”。同时，这个包装不是所有EngineCore API均已适配的证据：还需沿真正spawn/反序列化路径、具体类和进程检查。_PATCHED标记也不证明任意reload、异常中断或多个第三方patch的组合安全。

## VLLM_VERSION只改变版本判断输入

vllm_version_is优先读VLLM_VERSION，否则读vllm.__version__；使用packaging.Version并去掉PEP440 local段后比较public版本。因此0.32.0+empty的local构建标识本身不改变与0.32.0的相等判断，不能笼统把所有源码构建后缀都当“不匹配”。dev/pre-release等public部分仍参与比较，非法版本抛ValueError。

该helper带functools.cache；环境变量改变后已经缓存的目标判断不能假设自动更新。VLLM_VERSION不会安装正确源码、恢复改动或证明ABI/接口兼容，也不代表所有补丁均受这个helper控制。排查版本门槛时同时保留真实commit、原始版本串、覆盖值和消费进程；在新进程核对目标符号，避免通过伪装版本强行绕过接口差异。本次仅阅读静态实现，没有导入patch、修改环境或启动进程验证。


## 历史模型注册指南与当前平台入口

adding_a_new_model.po的55条历史译文无同名当前英文，其中模型登记阶段需按当前入口重读。Ascend的register_model函数转入models.register_model，当前29个映射传module:class字符串，不按旧示例在顶层eager导入全部模型类。architecture必须取实际config字符串，类展示名与兼容别名不能自动拼接；别名能登记也不证明模型/硬件/任务受维护。

所读原生_ModelRegistry.register_model在覆盖已有architecture时使用logger.debug，然后登记新映射。旧PO的warning、models_executor路径和“补一行日志即确认新模型成功”不当当前诊断合同：静默可能只是日志级别，真正闭合点仍是实际消费进程的最终类和后续检查。原生支持类对象及惰性字符串两种入口，Ascend采用后者不代表第三方插件一律必须eager或lazy。

平台backend路径的返回、外部包导入、KV dtype校验和模型forward各自留证。当前get_attn_backend_cls在ImportError时返回路径，只有类自身声明supported_kv_cache_dtypes才问supports_kv_cache_dtype，不执行对所有selector轴的通用validate_configuration。跳过某项不是支持声明；compatibility默认回退也不扩展稀疏/MLA能力。具体旧/新嵌入与权重接口见[新模型接入](../../guides/bringup/vllm_ascend_new_model_onboarding.md)。本批只读源码与译文，不执行任何插件或模型导入。


## 无同名英文的旧入门入口

getting_started.po共6条业务译文完整读取，其中有独立技术定位：vllm-ascend是社区维护的Ascend NPU硬件插件，通过硬件可插拔接口与vLLM集成解耦。同路径getting_started.md已不存在；这里保留的是旧PO的入口身份，不补造当前英文页，也不将文件缺失判断为网站渲染失败。该定位不等于全部开源模型、每个SKU或功能组合可用，具体入口/patch仍按前述当前源码核对。

旧导航把quick_start.md、installation.md、模型/特性教程和FAQ串联；它不能证明这些旧相对路径如今仍有效，也不构成独立安装命令。优先使用[版本环境指南](../../guides/deployment/vllm_ascend_versioned_environment.md)和[首次推理验收](../../guides/bringup/vllm_ascend_first_inference_acceptance.md)的已有当前来源。旧入口有独立定位事实，因此按技术资料融合，未按纯导航跳过；没有从该文件获得新的模型/硬件支持或运行结果。


旧PO原题为Getting Started；这里的孤儿是同路径英文缺失，不是插件架构本身失效或旧链接仍有效的证明。
