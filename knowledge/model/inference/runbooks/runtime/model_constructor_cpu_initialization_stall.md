---
type: Runbook
title: 模型构造看似卡在 HCCL：CPU 随机初始化与瞬态词表内存
description: 加载权重前 CPU 一直忙于 Embedding 随机初始化或 post_init，HCCL init 后 HBM 不增长时，定位模型构造与瞬态全词表分配，区分通信等待和残留进程。
tags:
- task.debugging
- topic.model_adaptation
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-runtime-debug/SKILL.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: supporting
created_at: '2026-11-09T09:23:50Z'
updated_at: '2026-11-10T03:51:43Z'
platforms:
- agnostic
---

# 模型构造看似卡在 HCCL：CPU 随机初始化与瞬态词表内存

## 症状与快速检查

最后一条日志停在 HCCL init 附近，HBM 不增长，进程 CPU 持续繁忙。按 rank 查看日志、进程状态、CPU/RSS 和调用栈，确认是否已经进入模型构造。高 CPU 不证明没有死锁，低 CPU 也可能是 IO；最后一条 HCCL 日志不证明根因是通信。

## 诊断路径与修复

nn.Embedding 的随机填充、PreTrainedModel.post_init 对大参数的初始化，可能在权重马上会被 checkpoint 覆盖前消耗大量 CPU 时间。对确实会完整加载的模块，可使用匹配 transformers 版本的 no_init_weights 上下文跳过无用初始化。若仍有未加载参数，跳过初始化会暴露未定义值，必须先验收加载覆盖，不能把它当通用提速开关。

VocabParallelEmbedding 的某些历史实现先通过 nn.Embedding 创建全量词表再替换成本地分片，引发远高于最终驻留的瞬态 CPU 内存。固定版本 module/linear.py 已用 input_size_per_partition 构造本地 Embedding，并本地化 padding_idx；不能把旧故障当成当前实现仍在分配全量词表。只有实际发现那条构造路径时，才改为直接分配本地分片并保持参数和 loader 契约；仅修改最终 tensor 大小不能消除之前的全量分配。

若调用栈实际在 HCCL 建组或等待，转查各 rank 首错、集合通信和残留进程。只确认并处理本次失败任务的进程及端口，不能按 infer.py 名称批量终止其他任务。重启前用 npu-smi 核对目标设备释放，不按固定休眠秒数认定已清理。

## 验证、回退与风险

保存构造阶段耗时和 CPU 峰值，确认实际权重全部加载并完成 post-load，比较修改前后的 eager 输出。不能跳过训练需要的初始化；缺权重或数值异常时恢复原初始化路径。没有真机测量时只报告代码路径诊断，不能声称已降低启动时延。

## Evidence

- [.agents/skills/model-infer-runtime-debug/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-runtime-debug/SKILL.md)
- [module/linear.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py)
- [executor/core/model_worker/model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)
