---
{
  "type": "Runbook",
  "title": "GMM2 L1 供给环加深的负结果：单波通过不能替代多波验收",
  "description": "当前分支的 depth 3/4 在多波档出现误差，depth 2 配置通过记录中的 golden；保留负结果及配置，不把 FIFO 假设写成框架永久上限。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# GMM2 L1 供给环加深的负结果：单波通过不能替代多波验收

## 适用场景

CannBot-DSL GMM2 的 fp4 CrossCore 供给环，记录含单波和多波专家档。

## 触发与观测

尝试增大 b_l1 深度以增加前瞻供给；多波正确性检查失败，而单波通过不能排除该问题。

## 探针与操作

固定代码与输入，分别核对 L1 槽数、UB 槽数和 lookahead；先逐 rank 验证正确性，再比较性能。下面是该记录最终保留的配置常量。

所读版本最终保留的完整供给环配置：

```python
GMM2_B_L1_SLOTS = 2
GMM2_B_UB_SLOTS = 3
GMM2_B_LOOKAHEAD = 2
```

## 机制与判别

该分支的多波测试对 L1 depth 3/4 不成立，最终保留 L1 depth 2、UB depth 3、lookahead 2。失败随配置变化说明需要继续核对通道事务与跨波生命周期，但不能仅凭误差大小裁定具体 FIFO 根因。

## 验证信号

原始设备日志中有多波失败数值，最终配置的 golden 记录通过。显示为 0.0 的误差不能据此宣称数学零值；性能“中性”和通用深度上限不作为本卡的结论。

## 适用与失效边界

结论仅限该实现、配置与所测波数。若框架同步协议或循环展开改变，应重新验证；不使用“无框架变更不得重试”作为普遍规则。
