---
{
  "type": "Runbook",
  "title": "两份 decode profiling 的对比口径：round 活跃跨度 vs 轮周期",
  "description": "两份 decode profiling 的对比口径：端到端用 round 周期（相邻主流首算子间隔）、模型执行用 round 活跃跨度，两口径都量且中位数取 ≥5 轮才稳。",
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
# 两份 decode profiling 的对比口径：round 活跃跨度 vs 轮周期


## 适用场景
cann-recipes-infer 上对比两份 decode 阶段 ASCEND profiling（如 DSpark vs DFlash 草稿模型/kernel_details.csv）判断端到端谁更快、并解释差在哪的场景。

## 触发与观测
用户以 CSV 汇总对比得出矛盾结论（设备忙时 DSpark 低 ~7.8% 但端到端 DFlash 更短；两 step 间有大段空白不知是否该计入）。

## 探针与操作
操作：先用 compare_kernel_details.py 按 total/compact/attention/matmul/norm/comm 等桶给出 us/round 与 Delta；再用 FlashAttn 行数 ÷ 草稿层数等计数法校验 --steps；最终在 trace 上量两个口径：A. round 活跃跨度 = 本轮跨所有流首 kernel 到末 kernel；B. round 周期 = 相邻两次主流首算子（aclnnSubs_SubAiCore_Sub）间隔，各取 5 轮中位数。口径定义表：

```text
| 口径 | 定义 | 回答什么 |
|---|---|---|
| **A. round 活跃跨度** | 本轮**第一个 kernel** 到本轮**最后一个 kernel**（跨所有流） | 模型执行本身谁快（排除轮间空白） |
| **B. round 周期** | 本轮首算子到**下一轮**首算子（就是你量的 Sub→Sub） | 端到端谁快（包含轮间空白） |
```


## 机制与判别
判别：两个口径都量、结论一致才稳；若 A 稳、B 反向，需去 trace 空白区间定位轮间开销（有 D2H/.item()/aclrtSynchronize 为真实开销，完全无活动则可能是 profiler 空转）。

关键结论：

- 双口径定义：A. round 活跃跨度 = 本轮第一个 kernel 到本轮最后一个 kernel（跨所有流），回答模型执行本身谁快（排除轮间空白）；B. round 周期 = 本轮首算子到下一轮首算子（如相邻两次主流首算子 aclnnSubs_SubAiCore_Sub 的间隔），回答端到端谁快（包含轮间空白）；对 5 个 profiled 轮各取中位数，两个口径都量、结论一致才稳。

## 验证信号

来源有五轮分类汇总输出，例如 DSpark/DFlash 的聚合 kernel 时间为 2730/2696 us，compact 为 500/0 us。聚合 kernel 时间之和不是跨流活跃跨度，也不包含轮间空白；不能拿该表直接验证 round 周期，更不能把“减去 compact 的估计值”当作实测优化后的端到端时间。

## 适用与失效边界
适用：背靠背 decode 轮次的 profiling 对比（含 draft/主模型混合 trace）。失效边界：1) 大样本对比数据（DSpark 49,530.8 vs DFlash 53,704.8 us/round 等）来自用户粘贴，未在轨迹内以工具结果复核，仅作背景；2) 中位数要求 ≥5 个 profiled 轮，轮数不足时不可用；3) skip_prefill 下 accept≈1，吞吐换算 tokens/s ≈ batch×accept/round_wall 不适用于高拒收场景。
