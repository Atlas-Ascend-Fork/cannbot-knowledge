---
type: Concept
title: 训练检查点 SHA-256 清单（完整性与未完成保存）
description: Checkpoint extension 的 pending marker、异步完成回调、逐文件 SHA-256 与真实拒绝行为；说明缺失清单、非递归覆盖和 rank0 未广播判定的边界。
tags:
- task.optimization
- topic.checkpointing
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/components/validation.py
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/components/checkpoint.py
  role: implementation
created_at: '2026-10-29T13:11:01Z'
updated_at: '2026-10-29T13:11:01Z'
platforms:
- agnostic
---

# 训练检查点 SHA-256 清单（完整性与未完成保存）

## Summary

TorchTitan NPU 的 checkpoint extension 可在 DCP/HF 保存目录记录逐文件 SHA-256，加载权重前重新计算并校验，区分文件损坏与保存未完成。它验证字节完整性，不验证模型语义、来源可信度、optimizer 兼容性或训练可恢复性。

## 启用与保存生命周期

设置 `--checkpoint.extensions.verify-hash-manifest`，默认 false。实际需要保存的 step 先创建 `_checkpoint_hash_manifest.pending`；同步/最后一步保存完成后计算清单，普通 async 则等待 save_future 成功再写清单，manager.save_future 被换成包含清单写入结果的 Future。取消或失败不应被解释为完整 checkpoint。

清单 `_checkpoint_hash_manifest.json` 包含 `granularity: file`、`algorithm: sha256` 和文件名→hash 映射。按文件名排序，1MiB 分块读取，排除自身和 pending；只扫描目录直属普通文件，不递归子目录。写清单后才删除 pending。底层使用 TorchTitan filesystem 抽象，支持其已接入的本地与远程文件系统。

## 当前加载行为以代码为准

- pending 存在：CheckpointManifestError，表示清单未完成。
- 清单不存在：FileNotFoundError；当前实现不会按 Config 注释所说的静默跳过。旧 checkpoint 未生成清单时，应明确选择关闭校验或用完整原文件重新生成可信清单，不能冒充已校验通过。
- payload 缺少 hash mapping 或 granularity 不是 file：ValueError。
- 清单列出的文件缺失：读取文件失败；hash 不一致：CheckpointManifestError。

校验只遍历清单列出的文件，新增未列文件不被拒绝；代码也未单独校验 algorithm 字段或清单文件名的路径安全性。清单应与 checkpoint 一并受控保存，不把修改后的清单当作独立可信证明。

## 分布式边界

未初始化分布式时本进程执行 I/O；初始化后只有 rank0 执行文件读取与判定。当前 verify_checkpoint_manifest **没有广播判定或同步异常**，与 Config 注释的广播承诺不一致。rank0 失败时其他 rank 可能继续进入后续加载，必须把所有 rank 的退出/错误与阻塞情况纳入验收，不能宣称当前已具备一致失败保障。

## 核验方法

在可丢弃的 checkpoint 副本中分别检查完整清单、修改单个 shard、删除已列文件、保留 pending、无清单和多 rank 场景；同时观察错误传播与 save_future 的最终结果。通过哈希检查后仍须执行模型/optimizer 恢复和后续 step 验证。本次只读复核实现，没有执行模型或 NPU 作业。

## Evidence

- [校验实现](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/components/validation.py)
- [Checkpoint extension](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/components/checkpoint.py)

## Links

- [DCP 与 HF 检查点](checkpoint_dcp_hf.md)
- [Virtual Optimizer](virtual_optimizer.md)
- [Swap Optimizer](swap_optimizer.md)
