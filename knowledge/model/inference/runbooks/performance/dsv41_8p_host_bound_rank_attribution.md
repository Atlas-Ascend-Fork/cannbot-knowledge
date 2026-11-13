---
{
  "type": "Runbook",
  "title": "诊断规则 · DSV4.1 8P host-bound：用 kernel_details 算子计数归因 MLA/LI 角色分工（LI rank 计算量小、rank5/7 host 暴露）",
  "description": "对 1104_hostopt_v3 八卡 profiling 做 per-rank 分析：角色分工由 kernel_details 算子计数确认——MLA rank（0/2/4/6）mqsmla=645、QuantBatchMatmul=3930、Computing 9.7-10.1ms；LI rank（1/3/5/7）mqsmla=75、QuantBatchMatmul=1770、Computing 6.7-7.0ms；LI rank device 计算量小，其中 rank1/3 因 CommNO 8.2ms 恰好盖住 host，rank5/7 的 host 侧暴露。",
  "tags": [
    "task.debugging",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 诊断规则 · DSV4.1 8P host-bound：用 kernel_details 算子计数归因 MLA/LI 角色分工（LI rank 计算量小、rank5/7 host 暴露）

## 适用场景

对 1104_hostopt_v3 八卡 profiling 做 per-rank 分析：角色分工由 kernel_details 算子计数确认——MLA rank（0/2/4/6）mqsmla=645、QuantBatchMatmul=3930、Computing 9.7-10.1ms；LI rank（1/3/5/7）mqsmla=75、QuantBatchMatmul=1770、Computing 6.7-7.0ms；LI rank device 计算量小，其中 rank1/3 因 CommNO 8.2ms 恰好盖住 host，rank5/7 的 host 侧暴露。

vllm-cann（vllm_ascend worker）在 8P（八卡 TP）DSV4.1 部署上的 host-bound 判定与优化优先级排序：基于 torch_npu step_trace + python 树 profiling（1104_hostopt_v3，8 rank trace_view.json + kernel_details.csv）。

## 触发与观测

触发：host bound 优化事务推进到「结合实测 profiling 输出分析：host bound 的点、优化优先级、与 device 异步的情况」；此前基于 rank0 的分析给出「host 掩盖率 99.6%、残余 ~38µs 暴露」的结论。

## 探针与操作

per-rank 分析流程（工具化探针）：1) 对每个 rank 的 trace_view.json 定位 host pid（python_function 最多的 pid）与 device pid（Computing 事件的 pid），取 execute_model 外层窗口求 step 周期；2) 用 kernel_details.csv 的算子计数判定角色（mqsmla/flash_mla/KvCompress/QuantBatchMatmul，见工件）；3) 以 em 窗口内 device 活动覆盖 + >10µs 连续无 device 活动双口径算 host 暴露与掩盖率；4) 对异常 rank 定位暴露窗口位置及其 host 事件名。

## 机制与判别

判别结构：MLA/LI 角色分工由 kernel_details 算子计数确认——MLA rank（0/2/4/6）mqsmla=645、QuantBatchMatmul=3930、device Computing 9.7-10.1ms；LI rank（1/3/5/7）mqsmla=75、QuantBatchMatmul=1770、Computing 6.7-7.0ms；rank1/3 因 CommNO 8.2ms 恰好盖住 host，rank5/7 盖不住。

### 补充机制片段
```
import pandas as pd
# 用 kernel_details 确认 rank 角色：mqsmla 计数（MLA rank 高）、KvCompressEpilogV2 等
for rk in range(8):
    df=pd.read_csv(f'rank{rk}/kernel_details.csv')
    n_mq=(df['Type']=='MqsmlaKernel___call__').sum()
    n_fla=(df['Name'].str.contains('mixed_quant_sparse_flash_mla')).sum()
    n_comp=(df['Name'].str.contains('KvCompressEpilog')).sum()
    n_qbm=(df['Type']=='QuantBatchMatmulV3').sum()
    print(f"rank{rk}: mqsmla={n_mq} flash_mla={n_fla} KvCompress={n_comp} QuantBatchMatmul={n_qbm}")
```

## 验证信号

全部为实测 tool_result：kernel_details 角色计数（16648）、device Computing/CommNO 分布（16645）。

### 结论与证据边界

  角色分工由 kernel_details 算子计数确认：MLA rank（0/2/4/6）mqsmla=645、QuantBatchMatmul=3930、device Computing 9.7-10.1ms；LI rank（1/3/5/7）mqsmla=75、QuantBatchMatmul=1770、Computing 6.7-7.0ms——LI rank device 计算量小，其中 rank1/3 因 CommNO 8.2ms 恰好盖住 host，rank5/7 的 host 侧暴露。

## 适用与失效边界

适用：多 rank 异构分工（separate-MLA 类）部署的 host-bound 复核。失效/边界：(a) 结论基于 step5-13 中位，未覆盖抖动/异常 step（em14 有 1.1ms 异常窗口，用户已提出要查）；(b) 「掩盖率」用窗口覆盖近似，未按 Start/Duration 逐流精算 overlap_pct 与假并行排查；(c) 代码快照是 host_opt_hugo@50b7d6fc8（A1/A1b 提交前），最新代码的 submit 批提交/C2 直构未体现在该数据上。
