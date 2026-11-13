---
{
  "type": "Runbook",
  "title": "Kimi K3 DSpark MegaKDA 输出行数不守恒的静态诊断与补零候选",
  "description": "源码审阅发现 MegaKDA 输出 plan.batch×spec_len 与层输入 token 数 T 可能分叉；来源加入 _restore_token_rows 补零。只核对了源码和提交，设备 capture/replay、精度以及连续两次压测仍待验证。",
  "tags": [
    "task.debugging",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Kimi K3 DSpark MegaKDA 输出行数不守恒的静态诊断与补零候选

## 适用场景
- Kimi K3（vllm-ascend + cann_ops_transformer）开 enable_mega_kda + DSpark 投机推理、ACL graph（FULL_DECODE_ONLY）部署，TP=16 + EP。
- 现象模式：批量 curl 压测第一次成功、第二次必崩（或第二次明显更快进入纯 spec-decode 后必崩），delta 与 partial_block 行数分叉即崩。
- 排查手段以静态代码 + git 提交链 + 崩溃日志为主（本机无 NPU 时同样适用）。

## 触发与观测
- 关键结论：


> MegaKDA 分支不是形状守恒的：`partial_block` 由 `torch.zeros_like(hidden_states)` 分配，行数 = 模型输入 token 数 T；attn 输出（delta）在 mega 路径下由 `_forward_mega_kda` 返回，行数 = plan.batch * spec_len，不是 T。而 `_plan_mega_kda` 当时的校验只拒绝『行数更少』，放过了图 padding 造成的『行数更多』，于是只要 `T != plan.batch * plan.spec_len`，delta 与 partial_block 行数就分叉。


> 在 `vllm_ascend/ops/kimi_kda.py` 加形状守恒 `_restore_token_rows` 并在 `_forward_mega_kda` 末尾 `return _restore_token_rows(output, hidden_states.size(0))`：只在 `T > batch*spec_len`（图 padding）时才补，相等时不进入补零分支；未测量实际开销；纯宿主形状判断 + `new_zeros/copy_`，图模式安全性待设备验证；只动 padding 行，逐 token 的 AttnRes 不会串到真实行，尚无精度复测结果。此后 `kda_new` 分支（`20974ca27` 等）进一步改成从运行时元数据反推 `spec_len = hidden_states.shape[0] // batch`，用适配 batch 的方式保证形状一致。

## 探针与操作
1. 隔离复跑：enable_mega_kda=false 连续压测两次，若恢复即锁定 mega 段；再叠加 VLLM_ASCEND_KIMI_K3_ATTNRES_FUSED_ENABLED=0 判断与融合算子 ABI 的关系。
2. 日志检查：MegaKDA enabled、mega_kda on: batch=16、AttnRes mode: fused、Replaying aclgraph、VLLM_USE_BREAKABLE_CUDAGRAPH 实际取值。

## 机制与判别
- 静态风险：MegaKDA 输出行数 = plan.batch×spec_len，非形状守恒；_plan_mega_kda 旧校验用 `<` 只拒绝"行数更少"，放过图 padding 的"行数更多"。
- 修复 _restore_token_rows：尾部零填充补齐到 T 行——只影响图 padding 行、纯宿主形状判断 + new_zeros/copy_ 图模式安全性待设备验证、尚无精度复测结果。
- 后续演化（kda_new 分支 20974ca27 等）：从运行时元数据反推 spec_len = hidden_states.shape[0] // batch，用"适配 batch"替代"补零对齐"。

### 补充机制片段


```text
def _restore_token_rows(output, num_tokens):
    """把输出补齐到 num_tokens 行，尾部零填充（只影响图 padding 行）。"""
    if output.shape[0] == num_tokens:
        return output
    restored = output.new_zeros((num_tokens, output.shape[-1]))
    restored[: output.shape[0]].copy_(output)
    return restored
```


```text
  if int(hidden_states.shape[0]) < int(attn_metadata.num_actual_tokens):  # 用的是 <
      return None
```

## 验证信号
- 本轨迹为静态分析+git 历史验证：修复提交 ba3d6622e 已 push 至 origin/27.0_kda；kda_new 分支的 20974ca27/f5248ecdf/f0cf521e7/de5fd1f2b 的 diff 逐一读取核对（4201/4209/4212）。
- 局限：本机无 NPU，修复效果需真机连续两次压测验证（handoff 文档 4165 明确要求）。

- 验证范围（validation_scope）：source_read

## 适用与失效边界
- 仅适用于 DP padding/图 padding 造成 T > batch×spec_len 的场景；T < batch×spec_len（校验已拒绝）不会走到 mega 路径。
- _restore_token_rows 只保证形状契约，只有在缺失行确为 padding、消费者不把它们作为真实 token 时，才有保留真实行的设计依据；若未来 mega 路径改为形状守恒实现（kda_new 方案），该补零函数成为冗余保险。
- 诊断依赖"第一次成功、第二次失败"的时序（scheduler/prefix-cache 使第二次更快进入纯 spec-decode 命中 mega 路径），若部署关闭 prefix cache，现象时序可能变化，应重新核对输出行数及调用元数据。
