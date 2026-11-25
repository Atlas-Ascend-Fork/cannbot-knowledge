---
{
  "type": "Runbook",
  "title": "块稀疏注意力 NPU 适配：区分 BSND 长度与 TND 累计长度，互斥 key 区间用 LSE 合并",
  "description": "daVinci-MagiHuman SR 局部注意力适配：有效长度不能表达任意区间选择；LSE 合并要求同一 query 的 key 区间互斥，相交区间先去重，最终画质仍待验。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---


# 块稀疏注意力 NPU 适配：区分 BSND 长度与 TND 累计长度，互斥 key 区间用 LSE 合并

## 适用场景

- 模型/框架：daVinci-MagiHuman（SandAI Magi 系音视频生成模型，DiT 40 层 SR 分支）NPU 推理适配（cann-recipes-infer 适配副本）。
- 对象：`inference/model/dit/dit_module.py` 的 `flex_flash_attn_func` / `flex_flash_attn_with_cp`——SR2_1080 模式下 32/40 层走块稀疏 LOCAL attention（`use_local_attn = layer_idx in config.local_attn_layers`），q_ranges/k_ranges 描述「每帧 query 区间 ↔ 感受野内多段 key 区间」的局部模式（frame_receptive_field 默认 11）。
- 平台：Ascend NPU（完整型号与实际产品未确认），torch_npu 环境（`transfer_to_npu` 由入口 sample_video.py 导入）。

## 触发与观测

- 失败（user_reported，source 0 seq 1）：`inference/common/config.py` 恢复 GPU 原版（含 SR2_1080 块）后 `bash infer.sh sr_1080p` 输出视频画面错误；改回 NPU 适配版 config.py（SR2_1080 块被移除、全层 GLOBAL attention）画面正常。任务约束：保持 GPU 原版 config.py，让画面恢复正确。
- 对照基线分开记录：source 0 seq18/19比较的两个历史提交（babe5ae→c816cd2）只改了seed描述字符串，且两者都没有SR2_1080分支（seq34）。当前GPU原版工作区相对历史NPU配置则恢复了SR2_1080分支，使32层重新启用LOCAL attention（seq29/164）；当前两版配置确实存在行为差异。
- 依赖事实（source 0 seq 124）：NPU 环境无 `flash_attn` 包（`ModuleNotFoundError: No module named 'flash_attn'`），GPU 原版 `_custom_flex_flash_attn_func` 的 fallback 不可直接运行。

## 探针与操作

- before（错误 NPU 适配，source 0 seq 72，文件读取输出保留原行号）：把 q_ranges/k_ranges 折算成 `actual_seq_lengths` 变长参数一次调用，并返回**全零假 LSE**：

```text
546:     output, _ = torch_npu.npu_fused_infer_attention_score(
547:         query, key, value,
548:         actual_seq_lengths=q_seqlens,
549:         actual_seq_lengths_kv=k_seqlens,
550:         num_heads=N,
551:         num_key_value_heads=NK,  # Support GQA
552:         scale=scale,
553:         input_layout="BSND",
554:         sparse_mode=0
555:     )
556:
557:     # Remove batch dimension if input was 3D
558:     if B == 1 and query.shape[0] == 1:
559:         output = output.squeeze(0)
560:
561:     output_lse = torch.zeros((query.shape[0], query.shape[2]), dtype=torch.float32, device=query.device)
562:     return output.to(query.dtype), output_lse
```

- GPU 原版分段语义（source 0 seq 84，逐字）：对同一个 query 区间，逐段处理互不重叠的 key 区间，再用 LSE 校正合并。source 0 seq 114 的构造把视频窗口与音文 key 区域分开；不同 query 的窗口可以重叠，但同一个 query 的 key 集合不得重复计数：

```python
                qo_lse[qo_lse == torch.inf] = -torch.inf
                cur_qo_lse[cur_qo_lse == torch.inf] = -torch.inf
                max_lse = torch.max(qo_lse, cur_qo_lse)
                qo_se, cur_qo_se = torch.exp(qo_lse - max_lse), torch.exp(cur_qo_lse - max_lse)
                sum_se = qo_se + cur_qo_se
                qo_scale, cur_qo_scale = qo_se / sum_se, cur_qo_se / sum_se

                qo_out = qo_out * qo_scale.permute(1, 0).unsqueeze(-1) + cur_qo_out * cur_qo_scale.permute(1, 0).unsqueeze(-1)
                qo_lse = torch.log(sum_se) + max_lse
```

- after（修复，source 0 seq 158 git diff 逐字 + seq 141 委托）：`_flash_attn_with_correction` 内层替换为 `npu_fused_infer_attention_score(..., softmax_lse_flag=True)` 取得真实 LSE 供合并；`flex_flash_attn_func` 改为委托 `_custom_flex_flash_attn_func`：

```diff
+            q_sub = query[q_start:q_end].unsqueeze(0).to(torch.bfloat16).contiguous()
+            k_sub = key[k_start:k_end].unsqueeze(0).to(torch.bfloat16).contiguous()
+            v_sub = value[k_start:k_end].unsqueeze(0).to(torch.bfloat16).contiguous()
+            cur_qo_out, cur_lse = torch_npu.npu_fused_infer_attention_score(
+                q_sub, k_sub, v_sub,
+                num_heads=N,
+                num_key_value_heads=NK,
+                scale=scale,
+                input_layout="BSND",
+                sparse_mode=0,
+                softmax_lse_flag=True,
             )
-            cur_qo_out, cur_qo_lse = cur_qo_out.squeeze(0), cur_qo_lse.squeeze(0)
+            cur_qo_out = cur_qo_out.squeeze(0)
+            cur_qo_lse = cur_lse.squeeze(0).squeeze(-1)
```

```python
def flex_flash_attn_func(
    query: torch.Tensor, key: torch.Tensor, value: torch.Tensor, q_ranges: torch.Tensor, k_ranges: torch.Tensor
) -> Tuple[torch.Tensor, torch.Tensor]:
    return _custom_flex_flash_attn_func(query, key, value, q_ranges, k_ranges)
```

（委托行为以 seq 158 最终 diff 的 `+    return _custom_flex_flash_attn_func(query, key, value, q_ranges, k_ranges)` 逐字锚定）

## 机制与判别

- 长度语义须按布局区分（source 0 seq 119 的 API 帮助）：本次 `input_layout="BSND"` 使用逐 batch 的有效长度；`TND` 才使用累计长度。BSND 的长度参数不能指定任意区间起点，也不能把一个 query 对多个离散 key 区间的选择关系编码进去；把 range 端点直接当有效长度会改变选中的 key。全零假 LSE 还会使后续分段归一化失去依据。API 分支细节见[推理注意力接口](../../apis/torch_npu/npu_fused_infer_attention_score.md)。
- 判别链：先区分历史提交间的描述差异与当前工作区恢复SR2_1080分支的行为变化（seq18/19/29/34/164）→ 检查被重新启用的LOCAL路径与原先GLOBAL路径的注意力语义（seq72/84）→ flash_attn缺失排除直接调用GPU fallback（seq124）→ 核对BSND长度及softmax_lse_flag接口分支（seq119/122）。
- 修复后 `local_attn_layers` 真实生效：runtime 日志 sr_arch_config 段 `local_attn_layers: [0,1,2,4,5,6,8,...,39]`（32 层），base arch_config 段为 `[]`（source 0 seq 284/289，文件读取输出保留原行号）：

```text
157:         local_attn_layers: [
158:             0,
159:             1,
160:             2,
161:             4,
162:             5,
163:             6,
164:             8,
```

## 验证信号

- tool_observed（source 0 seq 262/268）：`bash infer.sh sr_1080p` 修复后完整跑通（模型加载无 Missing/Unexpected keys；SR 5 步去噪完成），产出 `output_sr_1080p_5s_448x256_1920x1088.mp4`（8,382,917 字节，17:35；此前错误输出为 33MB，16:48）。
- tool_observed（source 0 seq 284/289）：runtime 日志确认 local attention 路径激活（32 层清单逐字在案）。
- 边界（未闭合）：agent 用 ffmpeg 抽帧并以图像读取查看（seq 298-304），但轨迹在视觉判读结论落文字前截断（止于 seq 305）；「画面正常」的最终确认在本轨迹内未记录，此前正常/异常对照为 user_reported（seq 1）。

## 适用与失效边界

- 重复计数反例：等分数的三个 key，其 value 为 `[0,3,0]`；分别处理 key 集合 `{0,1}` 与 `{1,2}` 再按 LSE 合并得到 1.5，而去重并集 `{0,1,2}` 的均值为 1.0。原分段循环没有去重逻辑，不能直接处理这种相交区间。
- 适用：同一 query 对应的各 key 区间互斥时，可分别调用注意力并用真实 LSE 做在线合并。不同 query 之间的窗口重叠不影响这一前提；若同一 query 的多个 key 区间相交，必须先合并、去重区间，或使用另行验证的等价稀疏实现。
- 失效/边界：逐段调用引入循环与多次 kernel launch（性能未评估，本修复以正确性为先）；BF16 转换与 contiguous 沿用原路径；CP>1 时外层 `flex_flash_attn_with_cp` 的 all-to-all 分片逻辑未改动也未验证；「画面正确」的视觉验收依赖用户侧确认（轨迹内未落文字）。

## 附：断言存档

- BSND 有效长度与 TND 累计长度是不同语义；二者都不能直接替代本实现所需的 query/key 区间选择关系。
- 同一 query 的互斥 key 区间可用真实 LSE 合并；相交区间须先去重。原轨迹完成5步SR与出片，但最终视觉确认未落文字，不能据此宣称画质验收通过。
