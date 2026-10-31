---
type: Runbook
title: Prefill CP 下 DSpark 草稿状态行序错位或越界
description: DSpark 整批 proposal 保持集合通信形状一致，结束后按 output_request_indices 选状态行，写回按 output_idx 索引。
tags:
- task.debugging
- topic.speculative_decoding
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/dspark_worker.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/forward_data_info/forward_data_info.py
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/1164
  role: evidence
created_at: '2026-10-29T04:09:05Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- agnostic
---

# Prefill CP 下 DSpark 草稿状态行序错位或越界

## 症状与快速检查

开启 Prefill CP 后在草稿状态写回阶段越界，或后续请求读到其他请求的投机状态。核对 cp_metadata.output_request_indices、返回 token 行数及 draft_info 各张量的第 0 维。

## 根因与诊断路径

MTP 与 DSpark 曾使用不同的状态行序：前者已经选择本 rank 的输出请求，后者仍保留整批状态。将全局 request_idx 用于已筛选状态会越界或读错行。CP 选择不是简单的前 B 行截断。

## 修复

DSpark proposal 仍对整批请求计算，保证各 rank 进入草稿集合通信时形状一致。proposal 结束后以 state.select_rows(output_request_indices) 选取本 rank 状态；Batch.update_requests_from_batch 对筛选后的 draft_info 使用 output_idx 读取，再写回对应的原始 request。两处改动需配套。

## 验证与回退

用非连续输出请求索引、多请求和不同 rank 归属验证：返回 token、状态张量和目标 Request 一一对应；检查各 rank 的 proposal 通信 shape 与调用次序。补测关闭 CP 与 MTP 路径。

不要把筛选提前到集合通信之前。无法确认两处实现版本一致时回退成套变更或暂用已验证的非 CP 配置，并重新核对资源容量。PR 未提供完整硬件回归报告，本批未执行多卡推理。

## Evidence

- [dspark_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/dspark_worker.py)（primary）
- [forward_data_info.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/forward_data_info/forward_data_info.py)（supporting）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/1164)（evidence）
