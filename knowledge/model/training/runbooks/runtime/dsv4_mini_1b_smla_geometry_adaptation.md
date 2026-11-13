---
{
  "type": "Runbook",
  "title": "torchtitan-npu DSV4 mini_1b 单卡启用 asc/SMLA 融合路径的注意力几何适配（head_dim=512 及三项配套约束）",
  "description": "torchtitan-npu DeepSeek V4 mini_1b 模型启用 asc/SMLA 融合注意力路径的几何适配，属真实模型配置与 AscendC kernel 硬约束（EZ0027/EZ0026/EZ0009）的适配验证。",
  "tags": [
    "task.implementation",
    "topic.tiling"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# torchtitan-npu DSV4 mini_1b 单卡启用 asc/SMLA 融合路径的注意力几何适配（head_dim=512 及三项配套约束）

torchtitan-npu DeepSeek V4 mini_1b 单卡启用 asc/SMLA 融合路径时，需按 AscendC kernel 硬约束适配注意力几何。本卡记录逐个暴露-适配循环与四项几何约束的报错判据。

## 适用场景

torchtitan-npu DeepSeek V4 mini_1b（A3 单卡/双卡调试）需要启用 asc/SMLA 融合路径（替代 golden 路径）时的模型几何适配；同类"AscendC kernel 对模型配置的硬约束"排查亦适用。

## 触发与观测

USE_GOLDEN=0 跑 asc 路径依次报错：EZ0027（ori_win_left/ori_win_right = 63,0 不合法，要求 127/0）；EZ0026（cmp_topk=128 不合法，要求 ∈[0,512,1024]）；EZ0009（LightningIndexerV2 query shape [2048,8,64] 不合法，query 末维 head_dim 仅支持 128）。

- ：

四项约束的客观报错判据：EZ0027（ori_win_left/ori_win_right 值 63,0 不合法）"When has_ori_kv is true, the value of ori_win_left must be 127 and the value of ori_win_right must be 0"→window_size=128；EZ0026（cmp_topk=128 不合法）"When has_cmp_kv is true, the value of cmp_topk must be in [0, 512, 1024]"→index_topk=512；EZ0009（query shape [2048, 8, 64] 不合法）"input query's last dim head_dim only support 128"→index_head_dim=128。

## 探针与操作

逐个暴露-适配循环：改 head_dim=512 → 跑 3 步 → 读报错 → 改下一项（window_size=128 → index_topk=512 → index_head_dim=128）→ 再跑；每步用 model_registry 打印确认配置生效（layers/ratios/window）；打通后把 wrapper 默认翻回 fused 路径并重生成 goldens。

## 机制与判别

四项约束分别来自不同 kernel：SparseFlashMLA 要求 head_dim=512；SMLA metadata（aclnnSparseFlashMlaMetadata）在 has_ori_kv=true 时要求 ori_win_left=127（即 window_size=128）、在 has_cmp_kv=true 时要求 cmp_topk∈{0,512,1024}；LightningIndexerV2 要求 index_head_dim=128。判据即报错文本本身，每项适配后对应报错消失。

- ：

DSV4 mini_1b 在 A3 单卡启用 asc/SMLA 融合路径的已验证几何适配：head_dim 64→512（SparseFlashMLA 要求）、window_size 64→128、index_topk 128→512、index_head_dim 64→128；适配后 1 rank 跑得下——显存 11.68GiB/64GiB（19%），asc 融合路径全通。

**工件 1**：

```
dim=1024,
        n_layers=24,
        vocab_size=129280,
        n_heads=16,
        # SMLA-compatible attention geometry (the AscendC kernels require
        # head_dim=512); 16 heads x 512 yields an 8192-wide attention.
        head_dim=512,
        rope_head_dim=64,
```

**工件 2**：

```
index_n_heads=8,
        # LightningIndexerV2 expects index_head_dim=128 (master mini_1b
        # uses 64); SMLA metadata kernel accepts cmp_topk in {0, 512, 1024}
        # (master mini_1b uses 128).
        index_head_dim=128,
        index_topk=512,
```

## 验证信号

适配后 1 rank 显存 11.68GiB/64GiB（19%），asc 融合路径全通（见来源结论 与触发报错消失判据）。

## 适用与失效边界

适用 torchtitan-npu pr_544 分支的 mini_1b 配置口径；适配后 head_dim=512 + window_size=128 + index_topk=512 + index_head_dim=128 是"本仓库 AscendC 可跑几何"，与 master mini_1b 原值不同。边界：8P/128P/多机脚本与 fused asc 的 EP2 场景未实测（需对应硬件）。
