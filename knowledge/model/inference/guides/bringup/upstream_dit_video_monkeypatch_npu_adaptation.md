---
type: Guide
title: 上游 DiT/视频生成模型搬昇腾：运行时 monkey-patch 层替代 fork + 版本门控融合算子替换
description: 当前Sana导入兼容补丁、必传quant_type的方法注入时序、加载后权重同步与量化替换。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/__init__.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/inference_video_scripts/inference_sana_video.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:16:27Z'
platforms:
- a2
---

# 上游 DiT/视频生成模型搬昇腾：运行时 monkey-patch 层替代 fork + 版本门控融合算子替换

## 适用场景

把一个**上游持续更新的开源扩散/DiT 模型**（如 [DiT](../../concepts/modules/dit.md) 生成模型）搬上昇腾，且不想把上游源码 fork 进仓再手改（fork 会让上游更新变成痛苦的 rebase）时，用**运行时 monkey-patch 层**做零侵入适配。

## 何时不适用

- 上游改动小且稳定、直接 fork 更简单；
- 需要改的是上游数据流结构（非仅算子替换），monkeypatch 难以覆盖。

## 做什么：统一 monkey-patch 入口

用一个统一 `apply_all(quant_type)` 入口，在运行时把上游模块的层/算子替换成昇腾版，对上游源码**零侵入**，无需维护上游文件改动，但上游升级仍须重新核对补丁绑定、接口、权重同步与输出；当前README约定的Sana上游版本须保持，不能由补丁存在推定兼容任意新上游。要成立必须满足**三条前置约束**：

当前入口先安装Triton导入stub与本地文本权重适配，再导入上游；解析quant_type后调用apply_all。apply_all不再负责提前安装stub，不能把旧无参调用直接移植。_npu_available现在使用packaging.version比较版本；Conv快路径另由enable_quant门控，量化模块在权重加载后替换。

1. **按补丁类型确定注入时机**——导入兼容 stub 要早于依赖导入；方法替换可以在模块导入后进行，但须早于相关实例构造或调用，并检查已缓存的旧绑定；
2. **核对来源版本的导入兼容层**——Sana PR341 使用 Triton stub 绕过未执行的 CUDA 依赖导入；这不表示 NPU 没有 Triton。只有确认相关内核不会被调用时才可采用 stub，否则应接入受支持的实现；
3. **新增的 zeros-init 补丁层必须在 `load_state_dict` 后手工同步真实权重**——否则补丁层保持零权重、输出错。

## 融合算子替换的通用做法

把上游原生小算子换成 torch_npu 融合算子时：

- 来源中的 RMSNorm、Attention、RoPE 部分计算分支有 `_npu_available` 门控；Conv1x1-as-Matmul、temporal conv 等方法替换不都受其守卫，须分别检查；
- 其中「全量非因果注意力（如 cross-attention）→ `npu_fusion_attention`」有一套**可跨模型复用的 BNSD 调用约定**（哨兵 token 数 + mask 布尔化链）。注意：这里全量非因果场景用训练向 `npu_fusion_attention`（BNSD），与因果 decode 用推理 FIA 相反（见相关经验）。

## correctness 验证 / 风险 / rollback

- 仅实际受 `_npu_available` 控制的分支可回退；其他补丁须显式禁用注入或恢复保存的原方法，并核对重新构造实例后的行为。
- zeros-init 补丁层若漏同步权重 → 输出全错但不报错，须在 `load_state_dict` 后校验。
- 逐项核对导入兼容补丁和方法替换的时机，以及实例或调用方是否已保存旧绑定；不能仅凭模块已 import 判定补丁失效。

## 相关经验
- [aclgraph 图捕获前 monkeypatch upstream graph_captu](../../runbooks/runtime/aclgraph_capture_patch_module_base_vs_mro.md)

- CUDA 原生 DiT/视频模型的注意力后端改路由 + 绕过 SP 库 CUDA 硬检查见 [cuda-native-dit-video-attention-sp-npu-adaptation](../../optimizations/rules/cuda_native_dit_video_attention_sp_npu_adaptation.md)。
- DiT 算子级代数改写（conv/LN 折叠）见 [dit-cnn-operator-algebraic-rewrite-npu](../../optimizations/rules/dit_cnn_operator_algebraic_rewrite_npu.md)；DiT 融合算子/autocast 精度对齐见 [precision-dit-fusion-autocast-cossin-dtype](../../optimizations/rules/precision_dit_fusion_autocast_cossin_dtype.md)。
- 因果 decode 用推理 FIA（与此处全量非因果用 FA 相对）见 [attention-to-fia-sparse-mode-sink-window](../../optimizations/rules/attention_to_fia_sparse_mode_sink_window.md)。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md)（primary）
- [__init__.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/__init__.py)（implementation）
- [npu_patches.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py)（implementation）
- [inference_sana_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/inference_video_scripts/inference_sana_video.py)（implementation）

## bringup 验收与停止条件

记录上游与 patch 版本，先确认替换点是否实际命中、权重是否同步到新增层，再按固定输入逐项比较原实现与 NPU 输出。逐个开启融合替换并记录精度和耗时；上游符号变更、stub 路径被实际调用、权重未同步或输出不对齐时停止，撤回对应 patch。
