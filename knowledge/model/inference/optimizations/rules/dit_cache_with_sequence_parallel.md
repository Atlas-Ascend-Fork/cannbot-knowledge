---
type: Optimization
title: DiT 缓存与 SP：一致决策和当前通信组边界
description: 最新Hunyuan缓存共存入口、Ulysses子组与完整SP分母风险，以及Wan当前多卡强制NoCache边界。
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/hyvideo/inference.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/sp8.yaml
  role: example
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:09:27Z'
platforms:
- agnostic
---

# DiT 缓存与 SP：一致决策和当前通信组边界

## 规则

FBCache/TeaCache的数据相关判据来自本地序列分片。若参与后续集合通信的rank选择不同跳步路径，会导致通信不匹配或结果错误；判据、累计状态、重置与分支归属都必须保持一致。TaylorSeer按固定步计划决策，但仍要求所有rank的采样步/层计数一致。

公共BaseCache在sp_group存在且sp_world_size>1时，对本地ratio执行all_reduce(SUM)，再除sp_world_size。TeaCache在同步后才做非线性多项式和累计。它是本地相对量的算术汇总，不是全局加权L1比值，尤其不应将不等长分片视为等价。

## HunyuanVideo 当前实现

旧sample_video.py多卡+缓存硬失败检查已移除。cache_manager.set_sp_group可在创建方法前后透传组信息；重算路径使用SP attention。纯Ulysses、ring_degree=1时，当前sp8.yaml提供Ulysses8配置。

必须注意实际绑定：hyvideo/inference.py传入的是get_sp_group().ulysses_group，分母却来自get_sequence_parallel_world_size()。源码注释称覆盖混合情况，但在Ring>1时，Ulysses子组并不自动等于完整SP组；仅组内汇总不能证明所有Ring伙伴决策一致，分母也须核对。不能据此宣称FB/Tea与任意Ulysses+Ring组合正确。

在核验混合组成员、归约分母、所有相关rank命中序列及真实通信前，采用已核对的纯Ulysses配置或NoCache。不要仅因入口不再抛异常就判定该组合已验证。

## Wan2.2 当前边界

Wan generate.py在world_size>1时仍记录禁用日志，并将cache_method替换为NoCache；缓存加速不会生效。单卡只接入FB/Tea首块。旧Hunyuan硬失败和当前Wan静默回退不能混为统一算法约束。

## 验收

逐rank采集缓存决策、真实实算路径、组成员和输出；固定seed对照NoCache验证质量、超时与耗时。相关配置见[Hunyuan部署](../../guides/models/hunyuan_video_deployment.md)，本次仅核对源码。


## Evidence

- [cache_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py)（primary）
- [inference.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/hyvideo/inference.py)（implementation）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（constraint）
- [generate.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py)（constraint）
- [sp8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/sp8.yaml)（example）
