---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman FBCache（step 级 DiT Cache）导致视频画面异常并被全量回滚",
  "description": "模型/框架：daVinci-MagiHuman（DiT 音视频生成，15B/40 层，cfg_number=2）型号未确认的单卡 Ascend NPU（原记录65GB），torch_npu 推理；基线 denoise（32 步）约 43-52s。",
  "tags": [
    "task.testing",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# daVinci-MagiHuman FBCache（step 级 DiT Cache）导致视频画面异常并被全量回滚

## 适用场景

- 模型/框架：daVinci-MagiHuman（DiT 音视频生成，15B/40 层，cfg_number=2）型号未确认的单卡 Ascend NPU（原记录65GB），torch_npu 推理；基线 denoise（32 步）约 43-52s。
- 任务：为加速推理接入 step 级 DiT Cache（FBCache：以第一个 transformer 层输出的相对 L1 距离判定跳步，命中时复用上一步 noise_pred，rel_l1_thresh=0.05、warmup=2、cond/uncond 分离缓存、SP 组 all-reduce 同步判定）。
- 缺失信息：异常画面的具体形态（花屏/跳变/模糊）无图像级记录，仅有用户口头报告。

## 触发与观测

用户报告（source 0 seq 1，user_reported）：

```text
进行了DiT Cache优化，但是优化后输出的视频画面有有问题，撤销DiT Cache优化的所有改动
```

回滚时 git 状态显示该优化共改动 7 个文件（92 insertions），并衍生 6 份调参日志（cache_conservative/fixed/input_based/sync_cfg/thresh003/thresh005_log.txt），说明多组阈值/判定信号尝试均未消除异常（source 0 seq 7，tool_observed 文件清单）。

## 探针与操作

被回滚的实现机制（source 1 seq 79，实现轨迹写入文件逐字，FBCache 判定核心）：

```python
        rel_l1 = torch.abs(diff).mean() / (torch.abs(prev_judge_input).mean() + 1e-8)
        rel_l1_value = rel_l1.item()

        rel_l1_value = self._sync_scalar_for_sp(rel_l1_value)

        should_skip = rel_l1_value < self.config.rel_l1_thresh

        if should_skip:
            self.skip_count += 1

        return should_skip
```

配置默认：`rel_l1_thresh=0.05, warmup=2, enable_separate_cfg=True`，命中输出 `residual + ori_latent`。

回滚操作（source 0 seq 14/35，tool_observed）：`git restore` 7 个文件（dit_module.py/entry.py/pipeline.py/scheduler_unipc.py/video_generate.py/sr_540p 配置×2），删除 `cache_manager.py`、`base_single_cache*.yaml`、`infer_base_cache.sh` 及全部 cache_*.txt；`opt_by_dit_cache/` 因权限残留（仅输出目录）。

## 机制与判别

- 失败定位层次：症状为「输出视频画面有问题」——属生成质量回归，非运行时错误；缓存命中时直接以上一步 `residual + ori_latent` 顶替当前步完整 39 层前向，音频异常与否未单独报告。
- 根因未定位：相对 L1 阈值 0.05 对该模型 40 层单流结构（视频+音频+文本 token 同层）是否为有效跳步判据、以及多组调参（0.03/0.05/conservative/input_based/sync_cfg）后仍异常的具体机制，轨迹内无逐层消融或数值比对；不排除判定信号（首层输出）与全网络输出的相关性不足这一解释，但也未证实。
- 与既有经验的判别：HunyuanVideo_npu 采用同类 step 级 TeaCache/FBCache 可用（skill 参考文档，source 1 seq 12），说明失败更可能与该模型的判定信号/阈值适配有关，而非 step 级 cache 范式本身不可行（未验证推断）。

## 验证信号

- 回滚后基线复跑正常：denoise 32 步 51.92s，`output_base_5s_448x256.mp4`（1.1MB）正常生成（source 0 seq 81-90，tool_observed），确认异常由 DiT Cache 改动引入且可逆。
- 项目优化矩阵终态将 DiT Cache(FBCache) 记为 No-Go：「画面差异大，用户要求不启用有损优化」（source 0 seq 97/99，已记录结论）。
- 失败信号本身为 user_reported + 回滚行为佐证；无本轨迹内的画面截图/指标对比。

## 适用与失效边界

- 适用结论（负向）：在 daVinci-MagiHuman（15B/40 层单流 DiT、cfg=2）上，以首层输出相对 L1（阈值 0.03/0.05 等 6 组配置）为判据、缓存最终 noise_pred 的 step 级 FBCache 会导致画面质量异常，不可作为无损加速采用；后续同模型优化应默认排除该路线（todo 约束「不启用 cache 等有损优化」）。
- 边界：不外推到其他 DiT 模型（HunyuanVideo_npu 有成功先例）；不外推到 block 级 cache 或 TaylorSeer 等其他方法（本轨迹未试）；阈值再调低是否可消除异常未知（多组阈值已试但 conservative 下限未记录）。
- 回退路径：保留 git 回滚清单（7 文件 + cache_manager.py 等），任何重试应从 NoCache 基线起步并先做画面级 A/B（本轨迹缺失的验证环节）。

## 附：断言存档

- daVinci-MagiHuman 上以首层输出相对 L1 为判据、缓存最终 noise_pred 的 step 级 FBCache（rel_l1_thresh=0.05, warmup=2, cfg 分离）导致输出视频画面异常（用户报告），经 6 组阈值/判定变体调参未消除。
- 全量回滚（git restore 7 文件+删除 cache_manager.py 等）后基线 denoise 32 步 51.92s、output_base_5s_448x256.mp4 正常生成，确认异常由该改动引入且可逆；项目矩阵终态记 DiT Cache(FBCache)=No-Go（画面差异大）。

```text
rel_l1 = torch.abs(diff).mean() / (torch.abs(prev_judge_input).mean() + 1e-8)\n        rel_l1_value = rel_l1.item()\n        \n        rel_l1_value = self._sync_scalar_for_sp(rel_l1_value)\n        \n        should_skip = rel_l1_value < self.config.rel_l1_thresh\n        \n        if should_skip:\n            self.skip_count += 1\n        \n        return should_skip
```

```text
modified:   models/daVinci-MagiHuman/config/sr_540p_config.json
	modified:   models/daVinci-MagiHuman/config/sr_540p_ti2v.yaml
	modified:   models/daVinci-MagiHuman/inference/model/dit/dit_module.py
	modified:   models/daVinci-MagiHuman/inference/pipeline/entry.py
	modified:   models/daVinci-MagiHuman/inference/pipeline/pipeline.py
	modified:   models/daVinci-MagiHuman/inference/pipeline/scheduler_unipc.py
	modified:   models/daVinci-MagiHuman/inference/pipeline/video_generate.py
```
