---
{
  "type": "Runbook",
  "title": "gauss-splat 复用输出 buffer 时 retain_grad 不刷新与 clone 规避",
  "description": "来源 A5 训练中观察到 means2d.grad 不随 step 刷新；增加输出 clone 后，300 步探针记录梯度刷新。30k 步指标与该补丁代码身份尚未绑定，不作为此修订的端到端质量证明。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# gauss-splat 复用输出 buffer 时 retain_grad 不刷新与 clone 规避

gauss-splat（3DGS）训练框架在 A5 上开启 densify 后 PSNR 崩塌。本卡记录 retain_grad 一次性失效的机制判别、探针序列与算子输出 clone 修复。

## 适用场景

A5（Ascend950PR/CANN 9.0.0）上 gauss-splat 训练开启 densify 后 bonsai PSNR 明显下降。所测 calc_render 梯度与 CPU autograd 参考接近（max abs err≈1e-6、allclose），但这不排除其他输入下的反向错误。本次发现的具体问题是 projection 算子把输出写进跨 step 复用的预分配 buffer 并把同一 Tensor 对象交给 autograd：densify 经 retain_grad() 读 .grad，从第 2 个 step 起钩子不再挂到新建图节点，.grad 冻结在第 0 步值。来源在 forward 返回前以 torch.no_grad() 下 clone means2d_culling 规避，并观察到短程梯度刷新；长程指标与本修订的对应关系尚未核对。

A5/Ascend NPU 上 3DGS 类训练框架（gauss-splat）开启 densify/clone-split 策略后 PSNR 反而下降的排查与修复；任何自定义 autograd.Function 跨 step 复用输出 buffer 并让下游经 retain_grad()/.grad 读梯度的场景。

## 触发与观测

触发与观测对应的结论原文：

- 在 projection forward 返回前对复用 buffer 加 with torch.no_grad(): means2d_culling = means2d_culling.clone() 后，info['means2d'].grad 每步刷新（4.673569e-03、3.835136e-03、4.331768e-03、4.517207e-03、4.020450e-03、5.023449e-03），300 步探针记录梯度刷新。另有 30k 步结果，但缺少代码修订绑定，不据此证明本补丁质量。

## 探针与操作

探针 1（冻结判别）：在训练循环内每步打印 info["means2d"].grad.abs().sum()，并同一步用 torch.autograd.grad(loss, info["means2d"]) 独立求真值；若 .grad 恒定而 autograd.grad 变化，即为 retain_grad 冻结。探针 2（方案判别）：分别实测 backward 前 m2d.grad=None+retain_grad、张量级 register_hook、节点级 grad_fn.register_hook、torch.autograd.grad 四种写法连续 3 步的取值。探针 3（开销）：micro-benchmark 纯 x.clone()（含 kernel launch）。

## 机制与判别

机制：projection 算子把 means2d_culling 写进 rast_ctx 预分配、跨 step 复用的 buffer（GaussianFilter.cpp 原地写 outputs[...]），并把同一 Tensor 对象作为自定义 Function 输出交给 autograd。retain_grad()/张量级 register_hook 是按张量对象一次性挂到当时的 grad_fn；第 2 步起对象上 retains_grad 已为 True、grad_fn 每步被新图替换，旧钩子不再触发，.grad 冻结在第 0 步（见下方工件注释）。densify 的 clone/split 判据（grads > grow_grad2d）一直用 SfM 初始化梯度，增长几乎不触发而 prune 照常。

本条目引用的机制片段：原文：

```
        ctx.width = width
        ctx.height = height
        ctx.rast_ctx = rast_ctx
        filter = filter_float if rast_ctx.proj_backward_culling else proj_filter
        # `means2d_culling` is a long-lived buffer cached in `rast_ctx` and rewritten in
        # place on every call. Returning that same tensor object from this
        # autograd.Function makes `retain_grad()`/hooks on it effectively one-shot:
        # PyTorch attaches the hook that fills `.grad` to the first step's graph node
        # only, so from the second step on `info["means2d"].grad` silently freezes at the
        # first step's value and the densify strategy keeps acting on a stale, step-0
        # gradient. Hand autograd a fresh tensor each call so the retained gradient
        # tracks the current step.
        with torch.no_grad():
            means2d_culling = means2d_culling.clone()
        return means2d_culling, depths_culling, conics_culling, opacities_culling,\
            radius_culling, covars2d_culling, colors_culling, cnt, filter, vi_culling
```


## 验证信号

修复验证（device_functional，本轨迹内）：grad 逐步刷新实测序列 4.673569e-03→3.835136e-03→4.331768e-03→4.517207e-03→4.020450e-03→5.023449e-03（300 步脚本）；30k 步指标不纳入本修订的验证闭环。clone 开销实测为 launch-bound（~4-10µs，<步长 31ms 的 0.05%）。回归：tests/test_rasterization.py、test_projection_3dgs_*.py 修复前后失败集相同（均为既有 507035 设备错误/旧签名问题），test_projection_3dgs_bwd.py::test_public_autograd_all_culled 由失败转通过。

## 适用与失效边界

适用：自定义 autograd.Function 每次返回同一复用 Tensor 且下游用 retain_grad()/.grad 读中间梯度的任何训练循环（这里只观察到来源 A5 运行，不外推 A2/A3 收益）。失效/边界：仅当 densify 消费 .grad 时才显性化，不开 densify 不触发；clone 开销 launch-bound（~4-10µs），性能敏感度低的场景优先选 clone（仍需逐调用方验证）。
