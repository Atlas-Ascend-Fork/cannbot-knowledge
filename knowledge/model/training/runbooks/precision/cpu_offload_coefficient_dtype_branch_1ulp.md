---
{
  "type": "Runbook",
  "title": "CPU offload 缩放分支：系数先转 bf16 可能改变舍入",
  "description": "四象限探针显示该输入下 bf16 两条缩放路径有差异；不能据单个最大差值宣称所有输入最多一 ulp，分支条件也须与注释区分。",
  "tags": [
    "task.debugging",
    "topic.precision"
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
# CPU offload 缩放分支：系数先转 bf16 可能改变舍入

## 适用场景

torchtitan-npu cpu_offload/HostSparse 的两段式缩放分支。需要分别核对梯度 dtype、coefficient dtype 和 correction 是否触发。

## 触发与观测

运行时 bool(state.corrections) 与“按容器类型区分”的注释不是同一个条件。

## 探针与操作

固定同一输入，对梯度 fp32/bf16 和 correction True/False 做四象限对照；再用边界数值、裁剪系数小于 1 的输入扩展验证。

原始源码差分或测试输出（用于核对）：

```text
################ PROBE ################
coefficient fp32 = 0.1234567, bf16 rounding of it = 0.12353515625
  grad dtype   correction fired   matches eager    max|diff|
torch.float32               True            True    0.000e+00
torch.float32              False            True    0.000e+00
torch.bfloat16               True            True    0.000e+00
torch.bfloat16              False           False    9.766e-04

=> for bf16 gradients the two branches of runtime.py:153 disagree,
   and which one runs is decided per step by whether correction != 1.0.
```

## 机制与判别

系数先降为 bf16 再参与乘法，可能比保留 fp32 系数多一次舍入；具体误差依赖数值。单次探针只能证明该输入下分支不等价，不能给出所有输入的 ulp 上界。

## 验证信号

coefficient=0.1234567 的记录中，两条 fp32 分支和 bf16 correction=True 与参考一致，bf16 correction=False 的 max|diff| 为 9.766e-04；相关单测 18 passed。

## 适用与失效边界

不要把显示精度、单例相等或差值的绝对量级当作普遍 ulp 证明。实际训练是否触发还依赖梯度 dtype 和分支条件；修改判据后需重做数值对照。
