---
{
  "type": "Runbook",
  "title": "增量式梯度范数穿刺：单次 backward 的 dtype、归约与验收边界",
  "description": "对齐最终穿刺脚本的 float64 本地平方和与 fp32 HCCL 归约；仅保留单卡、单次 backward 的对拍结果，不宣称支持梯度累积或训练步加速。",
  "tags": [
    "task.implementation",
    "topic.optimizer"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# 增量式梯度范数穿刺：单次 backward 的 dtype、归约与验收边界

## 适用场景

单卡 FSDP2 CPUOffloadPolicy 穿刺，梯度位于 CPU pinned fp32；dist 进程组、dev 和模型由测试入口准备。每个参数在一次 finalize 前只参与一次 backward。

## 触发与观测

早期原型用 fp32 平方和并出现 norm=inf，随后改为 double().square()；最终实现还将归约张量转为 fp32 以适配该 HCCL 用例。

## 探针与操作

下方为按真实 Write/Edit 顺序重建的最终统计/缩放单元，须在测试入口定义 dev 并初始化进程组。对同 seed 的 oracle 比较范数、系数与梯度，同时真正触发系数小于 1 的裁剪分支。

按原始 Write/Edit 顺序重建的最终原型；dev 与进程组由穿刺入口提供：

```python
import torch
import torch.distributed as dist
from torch.distributed.tensor import DTensor

def local_of(t):
    return t.to_local() if isinstance(t, DTensor) else t


def replica_factor(g):
    rf = 1
    if isinstance(g, DTensor):
        for mesh_dim, placement in enumerate(g.placements):
            if placement.is_replicate():
                rf *= g.device_mesh.size(mesh_dim)
    return rf

class IncrementalClipper:
    def __init__(self, model, max_norm):
        self.max_norm = max_norm
        self.sq_sum = torch.zeros((), dtype=torch.float64)
        self._handles = []
        self.param_list = []
        for p in model.parameters():
            self.param_list.append(p)
            self._handles.append(p.register_post_accumulate_grad_hook(self._make_hook(p)))

    def _make_hook(self, p):
        def hook(_p):
            if p.grad is None:
                return
            local = local_of(p.grad)
            self.sq_sum += local.detach().double().square().sum() / replica_factor(p.grad)
        return hook

    def finalize(self):
        total = self.sq_sum.float().to(dev)
        dist.all_reduce(total, op=dist.ReduceOp.SUM)
        total_norm = total.sqrt().item()
        coef = min(self.max_norm / (total_norm + 1e-6), 1.0)
        locals_ = [local_of(p.grad) for p in self.param_list if p.grad is not None]
        torch._foreach_mul_(locals_, coef)
        self.sq_sum.zero_()
        return total_norm, coef
```

## 机制与判别

该原型以 float64 本地累计平方和，归约前转 fp32，再计算系数并 foreach 缩放。每次 post_accumulate hook 会读取当前累计梯度，因此重复 backward 的简单平方和相加不等价于最终梯度的范数；本模式仅限这里的单次 backward。

## 验证信号

最终单卡穿刺三项报告 PASS，其中异数据/小阈值一项 coef=0.873937，另外两项 coef=1。原型此前还有一次测试判定失败，不能把它的旧实现与最终 PASS 配对。该对拍不是完整训练步或多卡验证。

## 适用与失效边界

不支持直接外推到梯度累积、真实 EP 多卡或收益。float64 累计后转 fp32 仍有范围限制，溢出或非有限值必须停止采用该归约路径。性能穿刺排除了部分工作，不能据其残差时间宣称整体加速。
