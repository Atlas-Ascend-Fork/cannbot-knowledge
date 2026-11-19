---
type: API
title: MegaCache产物接口：保存、加载与命中条件
description: 记录save/load_cache_artifacts的返回值、兼容前提和CppWrapper打包限制。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/megacache/overview.md
  role: primary
created_at: '2026-11-09T15:23:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# MegaCache产物接口：保存、加载与命中条件

## 固定范围

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的MegaCache页，仅列950DT，不扩大其他产品或历史组合。本次未读取/反序列化缓存、导入上游或编译模型。

| 入口 | 文档合同 |
| --- | --- |
| torch.compiler.save_cache_artifacts() | 在代表性shape完成compile和预热后导出当前进程收集的缓存；有产物时返回(artifact_bytes, CacheInfo)，无可导出内容可能为None |
| torch.compiler.load_cache_artifacts(artifact_bytes) | 恢复序列化Artifact到对应缓存，返回CacheInfo；示例检查None为加载未成功。后续仍须torch.compile和运行，原缓存查询机制决定命中 |

缓存层包括PRECOMPILE、PGO、AOT_AUTOGRAD、INDUCTOR、AUTOTUNE，文档还列动态shape及Catlass Kernel缓存。PRECOMPILE实验功能默认关闭，需TORCH_CACHING_PRECOMPILE=1才扩大其层次；MegaCache不是自动把该实验开关打开。

跨进程或机器复用要求硬件型号及软件编译环境一致；并不意味着任何有相同函数名的模型、输入/状态或闭包均可复用。Artifact Key与数量依实际结果，文档示例hash不是固定格式/个数验收目标。不要把加载成功、非空CacheInfo或文件存在当命中和正确性的证明。

暂不支持CppWrapper：其独立二进制尚未纳入MegaCache打包。这与AOT/CppWrapper可运行或grouped autotune可落盘是不同层次。Guard放宽及预编译正确性另见[预编译缓存指南](../../guides/optimization/torch_npu/torch_npu_automatic_precompile_cache.md)；分别比较无缓存冷启动、加载命中和稳态，保留模型/输入/软件身份。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/megacache/overview.md)（primary）
