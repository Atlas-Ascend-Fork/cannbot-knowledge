---
{
  "type": "Runbook",
  "title": "hc_pre 返回契约不一致：单 Tensor 不能替代调用点要求的三元组",
  "description": "调用点需要 hidden_states、post、comb，而封装函数只返回 y。保留返回结构诊断与待验证修正，删除 eager 更宽松的错误解释。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": [
    "agnostic"
  ]
}
---
# hc_pre 返回契约不一致：单 Tensor 不能替代调用点要求的三元组

## 适用场景

vllm-ascend 的 hc_pre 自定义算子迁移；调用点与 wrapper 的返回结构需要同步。该 Python 返回契约判断与硬件无关。

## 触发与观测

图编译报告不能将 32 行 Tensor 解包为三个元素；源码读取显示 forward 两处执行 hidden_states, post, comb = self.hc_pre(...)。

## 探针与操作

沿报错读取真实调用点、wrapper、算子 schema 和 Meta。下面展示记录中提出的完整 wrapper 修正；应在对应类中核对各配置字段后验证。

轨迹中提出、尚未设备复跑的 wrapper 修正：

```python
def hc_pre(self, x, hc_fn, hc_scale, hc_base):
    y, post, comb = torch.ops.custom.npu_hc_pre(
        x, hc_fn, hc_scale, hc_base,
        hc_mult=self.hc_mult,
        hc_sinkhorn_iters=self.hc_sinkhorn_iters,
        norm_eps=self.norm_eps,
        hc_eps=self.hc_eps,
    )
    return y, post, comb
```

## 机制与判别

修正方向是让 wrapper 透传调用点需要的三个返回值。普通赋值 y = op(...) 保留整个返回对象，不会自动取 tuple 的首元素；单个 32 行 Tensor 在 eager 下也不能解包为三个变量。不能把该错误归因为 torch.compile 比 eager 更严格。

## 验证信号

原始工具输出显示三目标解包调用点，以及 npu_hc_pre_meta 返回三元组；轨迹结束于修正建议，没有应用和设备复跑闭环。修订时的 CPU 反例同样在 eager 下抛出 too many values to unpack。

## 适用与失效边界

真实算子与 Meta 的形状、dtype 和返回顺序仍须同版本核对。所示代码为待验证修正，不宣称 eager/compile 两条执行路径已通过。
