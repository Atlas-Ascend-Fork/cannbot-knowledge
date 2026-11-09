---
type: Guide
title: vLLM Ascend SigLIP2：310P 文本与图像独立 Embedding 验收
description: 在 Atlas 300I DUO 使用 pooling/FP16 路径，分开构造文本与图像请求，核对64 token padding、单卡限制和
  ImageNet 标签顺序。 补充中文100条、HTTP计时/成功分母、实际模板与三组调参起点。
tags:
- task.implementation
- topic.multimodal
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/SigLIP2.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/SigLIP2.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/transformers_utils/chat_templates/template_basic.jinja
  role: constraint
created_at: '2026-10-29T09:52:40Z'
updated_at: '2026-10-30T11:21:27Z'
platforms:
- 310p
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend SigLIP2：310P 文本与图像独立 Embedding 验收

## 范围与模型身份

来源只验证Atlas 300I DUO的siglip2-base-patch16-224、FP16。它是独立文本/图像encoder的对比embedding模型，使用runner=pooling、llm.embed或/v1/embeddings，不生成文本。TP与多节点PD不支持，MTP不适用；不把其他pooling模型的支持推给SigLIP2。

## 输入与启动契约

max_model_len=64匹配文本padding=max_length/max_length=64；离线tokenization_kwargs明确传入。图像请求用空prompt+multi_modal_data.image，HTTP经messages需template_basic.jinja及image limit1。文本和图像必须分成不同请求，不能将多模态生成消息混入同一个embedding样本。

served-model-name与请求model一致。310P硬件streams有限，来源capture_sizes=[64,32]且禁用npugraph_ex；pooling可能走MRv1，需核对实际Runner。默认/旧图配置不能照搬生成式服务。

## 正确性与性能

先用相同processor/权重对齐embedding维度、范数和浮点参考，再分别对文本、图像测HTTP。零样本ImageNet需L2归一后cosine与1000类text embedding比较，class name与ground truth均使用相同PyTorch索引；近0% Top1可能是标签顺序，不是NPU算子精度。

来源文本/图像吞吐建议分别是seq32/token512和seq16/token256，低延迟seq8/token128；它们是候选，不代表已测最优。客户端concurrency和服务max-num-seqs分开记录，预热、失败率和p99一起统计。停止在线服务后才在同卡做离线评测，避免资源竞争。

## 停止与回退

混合请求、错误padding/模板、TP/PD配置或数值不符时先修正输入并回单卡最小路径；降低batch恢复内存余量后重测。本次未运行310P、ImageNet或benchmark，来源约69% Top1不作为本仓结果。


## 中文教程与固定模型条件

SigLIP2.po 的100条有效译文匹配当前英文；原文代码块仍要单独读取。来源自述基于2026-09-03 main，不把日期当精确commit或所有后来release都支持。模型为google/siglip2-base-patch16-224，教程和权重表的完整配方只到Atlas300I DUO单卡FP16；普通“多节点需逐节点装环境”段不解禁TP/PD，MTP不适用。支持表模型✅与W8A8🔵是两个维度，本配方没有把量化也验成稳定。

在线配方给capture_sizes=[64,32]、enable_npugraph_ex=false、image limit1、max-model-len64及pooling/FP16。这是输入配置，不证明所有列出的shape都已capture/replay；离线示例没有显式传同一dtype/图选项，不据此默认两条路径完全相同。API响应示例仅截取两个浮点数，不是模型真实维度=2的声明。

文本用“This is a photo of {}.”并按64-token padding；图像转RGB，以空prompt和multi_modal_data.image，HTTP走messages/base64 data URI。文本/图像分两次编码。template_basic.jinja在固定Native仓的vllm/transformers_utils/chat_templates下，当前str加载器先尝试给定路径，失败后可查内置目录；裸文件名不必只依赖当前目录。该模板仅拼content，不自行处理image_url/标签/模型能力，见[Pooling契约](vllm_ascend_pooling_task_contract.md)。

## ImageNet 评测需固定标签与分母

来源代码按class id 0..999从imagenet1000_clsidx_to_labels.txt取1000类名称，再与PyTorch索引的val_label.txt对应图像stem做top1；不把devkit ground-truth编号与另一顺序类名拼接。文本与图像向量各做L2归一后点积取argmax。需检查非零有限范数、完整样本收集和标签覆盖，不能用“返回了向量”关闭质量验收。

约69%只是该来源的近似参考，没有本次结果或统一阈值。缺失/错误图片、空评测集、坏label及零范数在示意脚本里没有完整健壮性处理；适配Agent应保留实际成功/失败分母并核验数据，不能静默丢失败再对参考值比较。离线与在线同卡竞争需在实验设计里避免，本次没有停止任何服务。

## HTTP benchmark 的真实计时和成功定义

英文内联示例默认NUM_REQUESTS200、CONCURRENCY8、WARMUP10、MODE=both、随机224×224 JPEG、TIMEOUT_S=120。both依次跑text再image，是两个独立阶段，不是每个请求混合文本和图像。每阶段先构造210个payload；JPEG生成/base64及请求JSON序列化不都在报告时延里，不能将该E2EL直接称完整用户预处理时延。

post_json在JSON编码/Request构造之后启动单请求计时，覆盖urlopen及响应read，不解析/校验embedding schema或数值，只把HTTP200当成功。线程池排队也不在每个worker开始后的请求计时里；wall则包含测量阶段线程池调度、所有成功/失败完成。热身结果被丢弃，没有由热身失败自动中止的门槛。

吞吐=成功数/wall，mean/median/p99只取成功请求；失败数另报，不能把丢失败后的低p99当全部请求满足SLO。p99对排序值用(len-1)*0.99线性插值，不是nearest-rank，也没有输出文本生成的token/s或TTFT/TPOT。这里都是代码定义，未执行HTTP脚本或NPU。

| 来源DUO单卡起点 | max-num-seqs | max-num-batched-tokens | max-model-len | 客户端并发参考 |
| --- | --- | --- | --- | --- |
| 文本高吞吐 | 32 | 512 | 64 | 16–32 |
| 224×224图像高吞吐 | 16 | 256 | 64 | 8–16 |
| 低时延 | 8 | 128 | 64 | 4–8 |

前两列是服务启动参数，客户端并发是独立负载旋钮，不是TP卡数，也不是实测收益。来源的“接近max-num-seqs/超过后趋于平缓”是调优参考，仍按真实请求大小、批处理和p99测量，不泛化成所有硬件的饱和定理。
