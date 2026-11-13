---
{
  "type": "Runbook",
  "title": "torchair AF concat 融合对转置+切片非连续输入：CPU 侧 stride 推导一致，转置被检测但无转置 kernel 生成证据（vector core retCode=0x31 场景）",
  "description": "DeepSeek V2 Lite inductor+auto fusion 场景报 vector core retCode=0x31（MTE_ERROR_T0_0=0x80000000）。CPU 侧 stride 推导验证与 buf45 实际 stride [86016,256,4096,1] 完全一致，AF 连续 stride 为 [0,2688,128,1]；LOAD_ROAD_DEBUG 显示转置被正确检测但没有任何转置 kernel 被生成的证据，最可能是转置 prologue 未被实际生成或 call_arg 未被正确改写。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# torchair AF concat 融合对转置+切片非连续输入：CPU 侧 stride 推导一致，转置被检测但无转置 kernel 生成证据（vector core retCode=0x31 场景）


## 适用场景

DeepSeek V2 Lite inductor+auto fusion 场景报 vector core retCode=0x31（MTE_ERROR_T0_0=0x80000000）。CPU 侧 stride 推导验证与 buf45 实际 stride [86016,256,4096,1] 完全一致，AF 连续 stride 为 [0,2688,128,1]；LOAD_ROAD_DEBUG 显示转置被正确检测但没有任何转置 kernel 被生成的证据，最可能是转置 prologue 未被实际生成或 call_arg 未被正确改写。

## 触发与观测


AF concat 路径收到来自 transpose+slice 的非连续输入 buf45，需要核对生成代码采用的 stride。CPU 构造 `torch.randn(1,21,16,256).transpose(1,2)[:,:,:,:128]` 得到 stride `(86016,256,4096,1)`；对应连续布局为 `(43008,2688,128,1)`。这证明布局不同，不单独证明未生成转置是唯一根因。

## 探针与操作


机制片段：原文：

```
# 模拟 DeepSeek-V2-Lite RoPE 的 key split 模式
x = torch.randn(1, 21, 16, 256, dtype=torch.bfloat16, device='npu')
x = x.transpose(1, 2)        # [1, 16, 21, 256], stride=[86016, 256, 4096, 1]
x = x[:, :, :, :128]         # [1, 16, 21, 128], stride=[86016, 256, 4096, 1] ← 非连续

y = torch.randn(1, 1, 21, 64, dtype=torch.bfloat16, device='npu')
y = y.expand(1, 16, 21, 64)  # [1, 16, 21, 64], stride=[1344, 0, 64, 1]

# 非连续 tensor 直接进 concat（不经过 .abs() 等 realize 操作）
out = torch.cat([x, y], dim=-1)
```

## 机制与判别


来源结论：

stride 推导经 CPU 侧验证：torch.randn(1,21,16,256).transpose(1,2)[:,:,:,:128] 的 stride 恰为 (86016, 256, 4096, 1)，与 buf45 完全一致（Match: True），AF 连续 stride 为 [0, 2688, 128, 1]、PyTorch 连续 stride 为 [43008, 2688, 128, 1]；LOAD_ROAD_DEBUG 显示 buf17/buf45 转置被正确检测（road_len=1, transpose，enable_load_transpose=True），但 debug_flag.log 中没有任何转置 kernel 被生成的证据，最可能是转置 prologue 未被实际生成或 call_arg 未被正确改写，concat kernel 直接收到了非连续原始数据。

## 验证信号

本卡验证信号并入『机制与判别』节：来源结论：的 CPU 侧 stride 推导（Match: True）与客观观测锚点。

## 适用与失效边界

适用：torchair inductor+AF 下 concat/cat 融合输入含 transpose+slice 非连续张量、NPU 报 vector core retCode=0x31 且 MTE_ERROR_T0_0=0x80000000 的场景。失效边界：根因判别依赖用户提供 error.log/debug_flag.log 与 asc_graph.py；“转置 prologue 未生成”为最可能解释（无生成证据），最终确认需在用户环境实际使用的 torch_npu npu.py 中加 TRANSPOSE_PROLOGUE/REWRITE_CALL_ARGS 日志整网复跑。validation_scope: source_read + cpu_reference。
