---
{
  "type": "Runbook",
  "title": "minimax_h3 VAE 解码 attention/RoPE 融合算子在 TP+SP 模式下的启用：decode 计算 42s→35s（PSNR 42.50 dB）",
  "description": "模型：minimax_h3（TP2+SP2 4 卡推理，见 w32-s1-c6），VAE ViT 视频解码阶段 decode.video→decode.audio ≈ 54.15s。；平台：Atlas NPU，torch_npu 融合算子 `npu_rotary_mul` + `npu_fused_infer_attention_score`。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# minimax_h3 VAE 解码 attention/RoPE 融合算子在 TP+SP 模式下的启用：decode 计算 42s→35s（PSNR 42.50 dB）

## 适用场景

- 模型：minimax_h3（TP2+SP2 4 卡推理，见 w32-s1-c6），VAE ViT 视频解码阶段 decode.video→decode.audio ≈ 54.15s。
- 平台：Atlas NPU，torch_npu 融合算子 `npu_rotary_mul` + `npu_fused_infer_attention_score`。
- 问题：原实现用 `_PARALLEL_ENABLED` 守卫在多卡模式下禁用 VAE attention/RoPE 融合补丁，退回逐算子路径。

## 触发与观测

- 基线：VAE decode 计算耗时 ~42s（日志时间戳拆解）；decode 总 ~54.2s。
- 去掉守卫使 TP+SP 模式下 VAE ViT 解码器也走融合算子后（`infer_minimax_h3.py:738-819` `_patch_vae_fusion_ops`）：decode 计算 ~35s（-7s，17%），PSNR 42.50 dB、输出文件大小 1.54 MB 与基线一致（source 0 seq 267/354，agent 汇总运行输出）。

## 探针与操作

- 修改：移除 `_PARALLEL_ENABLED` 分支守卫，使 `_patch_vae_fusion_ops` 在多卡模式同样生效。
- 质量对照流程：先存基线输出，再跑优化版，ffmpeg/PSNR 对比；发现回归时用"回退融合只留 tile 变更 / 只留融合"两次单变量运行隔离归因。

## 机制与判别

- VAE ViT 解码器在 tile 内做全自注意力 + RoPE，`npu_fused_infer_attention_score` 替换逐算子 SDPA 路径减少 kernel 拼接开销；融合不改变数学语义，故 PSNR 保持（42.50 dB）。
- 与 tile size 变更的可区分性：tile 512 与 tile512+融合两次 PSNR 同为 25.63 dB，融合单独运行 42.50 dB——质量回归归因于 tile 语义变化而非融合（见 w32-s2-c5）。

## 验证信号

- VAE decode 计算 ~42s → ~35s（-7s，17%，单次运行，日志时间戳口径）；decode 阶段总耗时 ~54.2s→~54.9s 持平（transformer→CPU 搬移 12-22s 波动掩盖计算收益）；PSNR 42.50 dB、文件大小 1.54 MB 不变（source 0 seq 267/354，agent_narrative 汇总工具输出）。

## 适用与失效边界

- 适用：torch_npu 上 VAE ViT 解码器（tile-local 全自注意力结构）的融合算子补丁在多卡 TP+SP 模式下启用。
- 失效/停止：端到端收益被显存编排开销掩盖时，需先解决 transformer 驻留/搬移问题（见 w32-s2-c6 的 barrier OOM 边界）；融合算子语义随 torch_npu 版本变化需回归 PSNR。
- 数值为单次运行观测。

## 附：断言存档

- 去掉 _PARALLEL_ENABLED 守卫使 VAE ViT 解码器在 TP+SP 模式使用 npu_rotary_mul+npu_fused_infer_attention_score 融合，VAE decode 计算耗时 ~42s→~35s（-17%），PSNR 42.50 dB、输出文件大小不变

```text
**优化①：VAE Attention/RoPE 融合算子** — 去掉 `_PARALLEL_ENABLED` 守卫，使 VAE ViT 解码器在 TP+SP 模式下也能使用 `npu_rotary_mul` + `npu_fused_infer_attention_score` 融合算子。
```
