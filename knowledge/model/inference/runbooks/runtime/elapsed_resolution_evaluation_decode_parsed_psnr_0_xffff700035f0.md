---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman DiT 残差流重构 + npu_add_rms_norm 融合：denoise 小幅提速且画质保持",
  "description": "单卡 Atlas A3（Ascend 910_9382）上运行 daVinci-MagiHuman 15B 单流 DiT（40 层，hidden 5120，GQA 40/8，post_norm_layers 为空）推理，已使用 npu_rms_norm。；目标：消除每层「残差加法 + 下一子层 pre_norm」的独立 Add kernel，进一步压 denoise 阶段耗时。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# daVinci-MagiHuman DiT 残差流重构 + npu_add_rms_norm 融合：denoise 小幅提速且画质保持

## 适用场景

- 平台范围依据：source 0 seq 194的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 单卡 Atlas A3（Ascend 910_9382）上运行 daVinci-MagiHuman 15B 单流 DiT（40 层，hidden 5120，GQA 40/8，post_norm_layers 为空）推理，已使用 npu_rms_norm。
- 目标：消除每层「残差加法 + 下一子层 pre_norm」的独立 Add kernel，进一步压 denoise 阶段耗时。

## 触发与观测

- 现状（source 0 seq 183，agent 对代码结构的阅读）：`DiTBlock.forward` 为 `hidden_states = hidden_states + attn_out` 后由下一子层 `pre_norm` 独立做 `npu_rms_norm`，Add 与 Norm 各自成核。
- 基线实测（source 0 seq 199，tool_observed，2026-07-13 14:39 同机同 prompt 同 seed 1234）：

```text
Time Elapsed: [0:00:05.363239] From [Step3: Basic Resolution Evaluation ...] To [Step6: Decode Video ...]
```

## 探针与操作

- 重构（source 0 seq 217-303 多次 edit）：`MultiModalityRMSNorm.forward*` 增加 `residual` 参数——residual 非空时改用 `npu_add_rms_norm(residual, x, gamma_i, eps)` 返回 `(normed, new_residual)`；`Attention.forward`/`MLP.forward` 返回 `(out, residual)` 元组；`DiTBlock` 在非 post_norm 路径把 attn 后的 residual 传入 MLP 的 pre_norm 融合；`TransformerBlock` 跨层串联 residual。首层/末尾 final_norm 走原 `npu_rms_norm`。
- 实施中先修复两处：residual 被 `normed.to(bf16)` 覆盖的变量遮蔽 bug（source 0 seq 312-314）；dtype 不一致触发 aclnnAddRmsNorm 161002（见 w32-s3-c2）。

## 机制与判别

- 机制：把「显式 Add（f32 residual）+ npu_rms_norm」合并为单个 `npu_add_rms_norm` 核，40 层 × (attn pre_norm + mlp pre_norm) 每步省去独立 Add；denoise 8 步合计收益 ~1.4%-2%。
- 判别：同一脚本、同一 prompt/seed/分辨率/步数、同日同卡 A/B，唯一变量为 residual 融合开关；修复 dtype 后三次运行（5.287/5.207/5.201s，后两次为 agent 转述运行日志）均低于基线 5.363s，方向一致。

## 验证信号

- 基线与首次优化运行均为设备日志逐字（source 0 seq 199/366，tool_observed）：Step3→Step6 5.363239s → 5.286873s（-1.4%，单次对比）。
- 输出质量（source 0 seq 392，tool_observed，ffmpeg psnr 基线 vs 优化视频）：

```text
PSNR y:33.389936 u:50.757419 v:49.683256 average:35.105687 min:34.043495 max:36.211037
```

## 适用与失效边界

- 适用：post_norm 关闭、pre_norm 紧跟残差加法的 DiT 结构；对 ~5s 级 denoise 的小幅 kernel 级收益预期（百分级，非倍级）。
- 失效/停止：收益小（5.36→5.29s），若系统噪声大于 ~1% 需多次重复测量；residual 流精度因 dtype 统一而变化，画质结论以 PSNR≈35.1 dB（平均）为界，低于 30 dB 应停用；仅验证 distill 8 步 448x256 工况，base 32 步/1080p 未在本轨迹验证。

## 附：断言存档

- daVinci-MagiHuman DiT 把残差加法并入 pre_norm（MultiModalityRMSNorm 增 residual 参数走 npu_add_rms_norm，Attention/MLP 返回 (out, residual)，跨层串联）后，distill 8 步 denoise 阶段 5.363s→5.287s（-1.4%，同机同 prompt 同 seed 单次 A/B）
- 输出视频与基线 ffmpeg psnr 对比 average 35.11 dB（y:33.39 u:50.76 v:49.68，min 34.04 max 36.21），画面基本一致；后续两次复跑 5.207/5.201s（agent 转述运行日志）方向一致

```text
Time Elapsed: [0:00:05.363239] From [Step3: Basic Resolution Evaluation (2026-07-13 14:39:11.728496)] To [Step6: Decode Video (2026-07-13 14:39:17.091735)]
```

```text
Time Elapsed: [0:00:05.286873] From [Step3: Basic Resolution Evaluation (2026-07-13 14:53:44.723316)] To [Step6: Decode Video (2026-07-13 14:53:50.010189)]
```

```text
[Parsed_psnr_0 @ 0xffff700035f0] PSNR y:33.389936 u:50.757419 v:49.683256 average:35.105687 min:34.043495 max:36.211037
```
