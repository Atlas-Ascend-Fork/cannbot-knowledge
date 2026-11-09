---
type: Guide
title: vLLM Ascend Dots3 Note：模态规划、显式 KV 与图捕获峰值
description: 按A3专用验证环境分开启用文本/图像/音频，区分KV容量和FusedMC2/捕图峰值，避免把默认profiling成功当运行期容量保证。 补齐dots3_note的TP16、EP16权重分片与三模态配方：文本/音频MTP3，image在Runner V1禁MTP；APC、chunked
  prefill、async scheduling分别留证，草稿eager不决定目标图模式，batch token与总context分开核对，保存2816M/4G、capture sizes及EvalScope请求。 核对target的FULL_DECODE_ONLY与draft的enforce_eager=true；草稿eager不等于关闭目标图。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/Dots3-Note.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/Dots3-Note.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-11-03T11:17:29Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- Dots3-Note
- dots3_note
- Dots3-Note.md
- Dots3-Note.po
---

# vLLM Ascend Dots3 Note：模态规划、显式 KV 与图捕获峰值

## 范围和交付环境

来源A3单节点、16logical chips、64GB/chip、Ascend0.22.1rc1/vLLM0.22.1参考，专用dots3-note-prev-a3-openeuler镜像。版本以后稳定的概述不能替代最新build复验，不扩A2/950。MoE+MLA外带audio/vision encoders，模态可同时启用但启动后不能动态切换，需重启。

## 模态与请求契约

text-only使用language-model-only；image参考<=7张且video/audio为0，audio模式设置对应limit。输入与服务启动form一致，切换前确认旧进程退出/端口释放/NPU内存回收。served name、容器权重/media可见性与local path allowlist分别核对；base64 URL不需本地路径白名单。

## 显存与峰值

来源图像16并发下2816MB KV与FusedMC2峰值相关，升到>=3072MB可OOM；音频显式4G KV也为保留图峰值。它们是特定build/模态预算，不能推到任意模型或将MB/GiB混算。自动profile可能分配足够KV却低估graph capture峰值，Worker died要查捕图阶段；关闭估计的实验变量不是已验证默认回退。

## 验收与优化

先每种模态单请求，对齐图像/音频预处理、positions和输出，再逐步混batch/图/MC2，记录实际KV容量、capture峰值和稳定运行峰值。TTFT包含媒体处理需拆分；增KV前先查计算工作区与并发，不能盲增memory utilization。模态或数值失败恢复相同form最小配置，保留可复核环境。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。

## 教程全文、旧译文与环境身份

补读Dots3-Note.md全559行、Dots3-Note.po全149条：147条msgid匹配当前英文、2条旧活动译文仅历史上下文、0空译，19项来源限定分别保留，另保留PO未覆盖的17行英文技术表格（不是17条额外PO）。PO63/69仍描述jemalloc/LD_PRELOAD，当前英文已无对应设置/安装步骤；残留“确认预加载库”的引导语不补出必需preload命令，也不否定其他版本的独立调优合同。此对照不是网站HTML或gettext构建验证。

来源验证的是单节点Atlas 800I A3/IT22HMDA_4_S、ascend910_9391、八块双die卡共16芯片、每芯片64GB；驱动26.0.rc1、固件9.0.0.0.205、CANN9.0.0、torch-npu2.10.0、Ascend0.22.1rc1配vLLM0.22.1。镜像目录同时列A2/Ubuntu/openEuler，不能据此扩展TP16配方的硬件范围；“后续版本稳定”概述与文档自己不覆盖全部组合的限定并存，实际build仍需复验。这里不把Main0.32文档快照、0.22.1配方与当前安装包混为一套运行身份。

容器模板映射16个davinci及管理设备、挂宿主驱动和只读权重目录；shm-size=1g只是模板值。核对镜像digest、真实版本/设备、容器内MODEL_PATH与媒体路径，再做最小请求；包可导入、pip show或npu-smi各有范围，均不代替权重/通信/推理通过。本批未拉镜像、安装、导入模型、终止进程或操作NPU。

## 三种模态的完整启动预算

服务名为dots3_note，客户端必须与实际served name一致；default名称只有在与当前服务不匹配时才会404，不当所有模型的固定禁用名。text/image/audio能力可同时开启，但本教程三条命令每次选择一种form，启动后不能动态切换。切换应先正常退出并确认旧worker、NPU内存和8000监听已释放；来源的广域pkill模板不等同于本批执行或对任意共享host的操作授权。

| form | 总context / max-num-seqs / batch token | KV配置与权重参考 | 执行与模态条件 |
| --- | --- | --- | --- |
| text-only | 32768 / 4 / 8192 | utilization .92，权重36.26GB/worker | language-model-only，MTP3，thinking=false |
| image | 32768 / 16 / 1024 | 显式2816M，权重约48.8GB/worker（+12.5GB） | image7/video0/audio0，无MTP，processor cache0、skip-mm-profiling |
| audio | 4096 / 4 / 4096 | 显式4G，权重37.88GB/worker（+1.62GB） | image0/video0/audio1，MTP3，thinking=false |

三者均TP16、enable-expert-parallel、enable_fused_mc2=1、lazy safetensors、APC、chunked prefill、async scheduling、generation-config=vllm、API8000。来源特性表把FusedMC2对应到dispatch_ffn_combine、mega_moe；APC可复用相似prompt的KV，实际kernel选路、cache命中和收益仍需验收。MoE专家分片与非MoE TP各自核对，不从EP16推导权重每层均匀切16份；lazy降低启动峰值是来源说明，不是本批内存测量。

text/audio的speculative method为mtp、num_speculative_tokens=3、draft enforce_eager=true；不改成GLM5.1的deepseek_mtp，目标图模式须单独验收，不由草稿eager推断。图像关闭MTP属于文档所述Model Runner V1视觉限制；三条命令未显式Runner选择，不能外推所有Runner/未来版本图像都禁MTP。通用方法与版本要求另见[方法选择](../optimization/vllm_ascend_speculative_method_selection.md)和[Runner裁决](../../optimizations/rules/vllm_ascend_model_runner_selection.md)。

## 图捕获与KV、计算峰值分别核算

target compilation mode为VLLM_COMPILE、cudagraph_mode=FULL_DECODE_ONLY。text只列capture sizes[16]且max capture16；image列[16]、未显式max；audio列[4,8,16]且max16。4请求×(1+K3)=16是该配方投机扩展token/capture预算，不是16个并发请求或16个生成token。文档称TP16+序列并行需16倍数，audio[4,8]启动时会被剔除；实际序列并行开关、有效capture集合和回退仍核对具体build日志，不能凭CLI列表当已捕图。

来源给image16并发2816MB，文字称>=3072MB会OOM、表里举3328MB失败；这些不写成通用硬上限，也不混算2816M与MiB。FusedMC2约3.64GiB和graph capture约3.76GiB属于不同峰值描述，不能相加为同一时刻保留量。若增KV，来源建议先将并发降8，仍需复验相同输入、图与MC2路径；不能用其他模型的可用比例覆盖本配方。

来源audio在自动profiling .92/.95时分别给21565/25686 KV tokens，却可能在捕图阶段worker died。显式4G保留峰值余量属于此环境的稳定参考，不保证任意模态组合都能运行。VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0是文档明确尚未验证的实验项，不当默认OOM修复。通用[profile未覆盖路径](../../runbooks/performance/profile_run_peak_memory_underestimate_untraversed_path.md)保存其0.10/0.11实现条件，不能直接把旧dummy_run补丁套到本0.22.1或Main0.32。

audio预算例1131 tokens=文本360+音频259+输出512，1GB容量2220 tokens、4GB8956 tokens及2.19倍是来源特定统计；静态算术8956/4096约2.19，不能解释成4G对1GB只增2.19倍容量；不能当所有请求的线性bytes/token公式。功能curl却设max_tokens1024，需重新核输入加输出和4096总context，不能仍声称1131预算覆盖。max-num-batched-tokens只管batch工作预算，不扩充总context或保证所有序列同时满长。

image/audio的mm-encoder-tp-mode=data会复制encoder到各rank并增加HBM，须计入权重、媒体激活、工作区和capture峰值。limit某模态0、language-model-only和skip-mm-profiling的有效加载/规划行为按实际版本核实；跳过profiling不表示不分配encoder或能自动避免OOM。

## 输入合同、功能与评测

本地图片需在容器内MEDIA_DIR、allowed-local-media-path白名单及真实挂载范围内，单请求image_url对象用file URL；base64 data URL通过HTTP传入，不需本地路径白名单。本地音频的MEDIA_ROOT也需是实际容器挂载内目录；audio例使用audio_url里的data:audio/wav;base64和GNU base64 -w0，不与另一模型的input_audio payload直接互换。实际读取进程、codec/采样率、processor与模型配置需对齐；文件存在或HTTP200不证明媒体内容正确。

先等权重加载、KV容量和capture完成，再查/v1/models中的真实模型名/形态长度、worker/OOM/重启日志。随后按当前form发一条真实请求：text max_tokens640、image256、audio1024、temperature0，核对choices文本与图像/音频语义相关、无路径/解码400；这些是功能参考，不是本批测量或模型质量验收。

GSM8K仅参考text-only EvalScope：5条smoke后1319条full、4-shot、boxed答案提取、eval-batch-size4、temperature0/max_tokens2048，保持服务名dots3_note；文档用eval-type=openai_api，不能不核工具版本就与另一指南server模式混换。数据自动从ModelScope下载，实际实验要固定工具/数据revision、split、模板和解析，完整记录预测/指标；本批没有安装、下载或运行。MMMU/MMAR只是应用场景，没有给出对应完整精度结果；AISBench/vLLM benchmark仅链接入口，没有本批TPS/TTFT/TPOT基线。

环境变量expandable_segments、TASK_QUEUE_ENABLE=1、CPU_AFFINITY_CONF=1和HCCL AIV是来源配置及解释，不当已实测优化收益。性能优化先保留相同form、checkpoint、输入长度/媒体数量、并发、有效图/MTP/MC2与KV预算，再逐项A/B，分开媒体预处理、prefill、decode、capture峰值和持续运行峰值。失败回到同一版本与form的已验证最小配方，不借A2镜像名或“后续版本”概述跳过硬件/正确性验收。
