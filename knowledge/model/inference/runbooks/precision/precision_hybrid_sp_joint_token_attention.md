---
type: Runbook
title: 混合序列并行 (Ulysses + Ring) 下 joint / 文本 token 的 attention 精度
description: 混合序列并行 (Ulysses + Ring) 下 joint / 文本 token 的 attention 精度。给 DiT 视频/图像生成上混合序列并行（Ulysses 沿 head 做 all_to_all + Ring all_gather）时，模型把文本/全局 token 作为 joint tensor 传入、需被所有序列分片共同 attend。若序列并行实现对 joint token 处理不当，会在不报错的前提下破坏 joint attention、造成精度损失。长序列视频 DiT 接 Ulysses SP 的拓扑/pad 校验见 video-dit-ulysses-sequence-parallel。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/287
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/266
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 混合序列并行 (Ulysses + Ring) 下 joint / 文本 token 的 attention 精度

## 适用场景

给 [DiT](../../concepts/modules/dit.md) 视频/图像生成上混合序列并行（[Ulysses](../../concepts/parallelism/ulysses.md) 沿 head 做 all_to_all + [Ring](../../concepts/parallelism/ring_attention.md) all_gather）时，模型把文本/全局 token 作为 joint tensor 传入、需被所有序列分片共同 attend。若序列并行实现对 joint token 处理不当，会在**不报错的前提下**破坏 joint attention、造成精度损失。长序列视频 DiT 接 Ulysses SP 的拓扑/pad 校验见 [video-dit-ulysses-sequence-parallel](../../optimizations/experience/rules/video_dit_ulysses_sequence_parallel.md)。

## 失败签名：joint K/V 在 SP 集合通信之前拼进序列 K/V

根因：若在 Ulysses all_to_all（head→seq）与 Ring gather **之前**就把 joint K/V 拼进普通序列 K/V，joint token 会被后续 all_to_all 与 ring gather 当**普通序列 token 重分布**——joint attention 结果被破坏。

修法要点：**joint token 的 K/V 延后拼接、并按 ulysses rank 沿 head 维切分**（与 head 分片对齐），而不是一开始就当序列 token 混进去。

```python
# 旧（错）：joint_strategy 分支开头就把 joint K/V 当序列 token 拼进去
# k = torch.cat([k, joint_tensor_key], dim=1)   # 被 all_to_all/ring 按序列 token 重分布 → 破坏

# 修：all_to_all 之后，按 ulysses rank 沿 head 维切 joint K/V
if params.joint_tensor_key is not None:
    per_rank = joint_tensor_key.shape[-2] // self.ulysses_world_size
    s = per_rank * dist.get_rank(self.ulysses_pg)
    joint_tensor_key = joint_tensor_key[..., s:s+per_rank, :]
    joint_tensor_value = joint_tensor_value[..., s:s+per_rank, :]
# 无 ring 维直接拼；有 ring 维时把 gather 回的 K/V permute+reshape 成 (b,-1,n,d) 再 cat joint
```

可迁移原则：任何「普通序列 token 走 SP 集合通信重分布、而 joint/全局 token 要被所有分片共同看到」的混合 SP，joint token 不能与序列 token 同路径重分布——要**延后到通信之后、按并行维度对齐切分后再拼**。Query 侧的 joint 拼接可保留在前，破坏的是被 all_to_all/ring 重分布的 K/V 侧。

## 边界 / 反模式：自研公共 SP 实现可能仍有精度损失，成熟第三方 NPU 库是可选回退

> ⚠️ 同一模型上，joint-tensor 修复与「整体弃用自研 SP」两条决策并存——修复解决了 joint K/V 重分布这一具体 bug，但维护者后来仍以「自研公共 SP 在该模型上有精度损失」为由，把该模型的序列并行整体回退到第三方 `xfuser`+`yunchang`（`xFuserLongContextAttention`）。

因此，在自研混合 SP 上追精度时：joint-token 延后拼接是必要修复，但**不要默认自研 SP 一定能追平**；成熟第三方长上下文注意力库（新版已原生适配 NPU，无需再手动去 cuda 检查 / 打 `try: import torch_npu` 补丁）是一个可迁移的回退选项。这条边界仅就该模型成立（未断言自研 SP 在所有模型上都掉精度），迁移时按模型实测判断。

## 参考实现及其约束

- 失败签名参考实现：cann-recipes-infer 的 `module/unified_sp/core.py::UnifiedSPAttention`（[HunyuanVideo](../../concepts/models/hunyuan_video.md) 的 `double_blocks + single_blocks`），`joint_strategy` 为 `rear`/`front`；修复新增 `AttentionParams.joint_tensor_key/value` + `_kv_post_process` 静态方法。
- 回退参考实现：同模型上把 `parallelize_transformer` 的 `UnifiedSPAttention` 换成 `xFuserLongContextAttention()`，`requirements` 钉 `xfuser==0.4.5` / `yunchang==0.6.4`（旧版 `xfuser<=0.4.4`/`yunchang<=0.6.3.post1` 才需侵入式补丁）。
- 边界：具体字段名 / 库版本是参考实现形态；joint-token 重分布原则与「自研 SP 精度不保证」的判断限定到证据覆盖的 HunyuanVideo 混合 SP，不外推。

## 相关经验
- [序列并行(FlashComm V1)分支用只查环境变量的窄谓词门控：漏掉 shared_ex](sp_gate_narrow_env_predicate_misses_shared_expert_dp.md)

## Evidence

- diff 事实（@2c45117，merged patch）：joint K/V 顶部拼接删除、按 ulysses rank 沿 head 切分、`ring_world_size==1` 直接拼、新增 `_kv_post_process`；ulysses seq-len 补齐块删除的**理由**为推断、不并入事实面；精度 before→after 数值源未给。溯源下探 [cann-recipes-infer-pr-287-fix-fix-hunyuanvideo-sequence-parallel-and-vae-parallel-debug](https://gitcode.com/cann/cann-recipes-infer/merge_requests/287)
- diff 事实（回退动作，@366a74296cb5）：`UnifiedSPAttention`→`xFuserLongContextAttention`、requirements 加 xfuser/yunchang、README 删侵入式补丁附录；「自研 SP 精度损失」这一**回退原因**仅见 PR 描述、非维护者展开、无 benchmark，已降级标注。溯源下探 [cann-recipes-infer-pr-266-feat-hunyuanvideo-support-taylorseer-offload-prefetch-vae-parallel-rolli](https://gitcode.com/cann/cann-recipes-infer/merge_requests/266)

<!-- cannbot:related:start -->
## 相关

- [Ring Attention Sequence Parallelism](../../concepts/parallelism/ring_attention.md)（`related`）：joint-token 故障机制为“若在 Ulysses all_to_all（head→seq）与 Ring gather **之前**就把 joint K/V 拼进普通序列 K/V，joint token 会被后续 all_to_all 与 ring gather 当**普通序列 token 重分布**——joint attention 结果被破坏。”；Ring Attention 机制为“Ring Attention 是另一种长序列 SP 方案：与 Ulysses 不同，**attention 内部也保持序列切分**，每张卡仅维护自己那 1/SP 的 Q。”，并明确 KV 会跨 rank 汇集，因此能限定延后拼接发生在 Ring KV 汇集之后。
- [Ulysses Sequence Parallelism](../../concepts/parallelism/ulysses.md)（`related`）：joint-token 故障链是“若在 Ulysses all_to_all（head→seq）与 Ring gather **之前**就把 joint K/V 拼进普通序列 K/V，joint token 会被后续 all_to_all 与 ring gather 当**普通序列 token 重分布**——joint attention 结果被破坏。”；Ulysses 机制为“Ulysses 是面向**长序列多头注意力**的序列并行策略：在 attention 以外的部分沿 S（sequence）维度切分，在 attention 处通过一次 all-to-all 把切分维度从 S 换到 N（num_heads），attention 内部按 head 并行、attention 输出再 all-to-all 换回 S。”，可据此定位 joint K/V 应在换维之后按 head 对齐。
<!-- cannbot:related:end -->
