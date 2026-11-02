---
type: Runbook
title: NaN 诊断先报 DT_FLOAT8_E8M0：记录 scale 未检查，避免误判模型异常
description: 区分 aclnnEqScalar 不支持 E8M0 的诊断失败与模型 NaN；固定实验跳过不支持的 scale 检查并披露覆盖缺口，不以
  eager 或数值 cast 假装解决。
tags:
- task.debugging
- topic.precision
- topic.graph_execution
status: draft
sources: []
created_at: '2026-10-30T03:17:19Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
---

# NaN 诊断先报 DT_FLOAT8_E8M0：记录 scale 未检查，避免误判模型异常

## 现象

在 Kimi K3 的 MXFP8 MoE 路线插入 NaN 探针后，前向捕获先报 `aclnnEqScalar ... Tensor self not implemented for DT_FLOAT8_E8M0`。这是诊断比较算子拒绝了 scale 的底层 dtype；这个报错并没有给出模型 activation 中 NaN 的计数，不能记录为“模型已经出现 NaN”。

曾尝试的 `scale.view(uint8) == 255` 在该部署环境仍会让底层比较收到不支持的 E8M0 类型。这里能确认的是旧字节比较没有规避报错，尚未确认内部 storage/后端传型的精确机制；不能把一个环境的行为概括为所有 torch_npu/CANN 版本的普遍规律。

## 适用场景与输入区分

- 范围：950PR/DT、包含 `dispatch.mx_scale` 和 `activation.mx_scale` 检查点的 Kimi K3 诊断实现；图模式使用 `npugraph_ex` Decode，Prefill 仍为 eager。
- `E4M3 activation` 是量化数据，当前块可先转换再执行普通 NaN/Inf 检查；`E8M0 scale` 是对应量化尺度的编码，两者不可因都叫 FP8 而使用同一个探针策略。
- 图诊断中的 raw scale 选择明确跳过。历史独立 eager 算子级探针可能采用“按字节复制到 CPU、恢复 dtype 后解释”的兼容路线；它与当前图探针跳过是不同实现，不表示 eager 一定解决后端限制。
- 具体 CANN/torch_npu 版本及真实 NPU dtype 行为尚未在本轮验收；不修改模型本来传给 GMM/量化算子的 scale dtype。

## 判别步骤

1. 从失败栈区分错误属于真实模型算术还是新加的诊断算术。如果栈指向 scale 的等值比较，先把该问题归入探针兼容性，不据此修改模型量化参数。
2. 确认失败对象是 `dispatch.mx_scale` 或 `activation.mx_scale`，核对其实际 dtype、编码来源和 checkpoint 标记。读取 dtype/元信息与执行 scale 的 Tensor view/cast/比较要区别对待。
3. 在 raw scale 标记进入 `FinitePoint.forward` 时立即返回。返回必须发生在 `.view()`、`.float()`、布尔比较和 NaN/Inf 计算之前；不能先转换到 uint8 再声称“未检查”。
4. 同时在启动日志输出 `[KIMI_NAN_TRACE_SKIPPED]`，异常 JSON 把两个点列入 `skipped_checkpoints`，reason 明确包含 `uninspected`。
5. 继续保留普通 activation、router、attention、GMM 输出检查和所有 rank 一致停止；跳过 raw scale 不能变成跳过整个 MoE 或对异常输出放行。

## 机制代码

下面是 `FinitePoint` 的完整前向方法；它依赖类内预分配的 `state`、`max_check_elements`、`_count_chunk`，以及同模块的 `math` 和 `torch`。raw scale 分支没有触碰 `value`，因此即使是原生 E8M0 Tensor，也不会产生读取它的 FX 图节点。其余分支仍正常更新 activation 统计。

```python
def forward(self, value, valid_rows=None, mx_scale=False):
    if mx_scale:
        # Do not touch the scale, including view/cast/compare. Deployment
        # showed view(uint8) was insufficient to make aclnnEqScalar accept
        # the E8M0 input. Eager can hit the same unsupported kernel as graph.
        # Keep this checkpoint unvisited and disclose the coverage gap.
        return
    # Keep ordinary floating inputs in their original dtype. Scan row
    # chunks so long prefill tensors do not require full-size FP32 copies
    # and masks. Slicing, rather than flatten/reshape, also avoids copying
    # a noncontiguous full input. A single row is the minimum chunk size.
    if value.ndim == 0 or value.shape[0] == 0:
        nan_count, inf_count = self._count_chunk(value, valid_rows, 0)
    else:
        row_width = max(1, math.prod(value.shape[1:]))
        chunk_rows = max(1, self.max_check_elements // row_width)
        nan_count, inf_count = 0, 0
        for start in range(0, value.shape[0], chunk_rows):
            chunk_nan, chunk_inf = self._count_chunk(
                value[start:start + chunk_rows], valid_rows, start,
            )
            nan_count = nan_count + chunk_nan
            inf_count = inf_count + chunk_inf
    visit = self.state[0] + 1
    first = (self.state[1] == 0) & ((nan_count + inf_count) > 0)
    self.state.copy_(torch.stack((
        visit,
        torch.where(first, visit, self.state[1]),
        torch.where(first, nan_count, self.state[2]),
        torch.where(first, inf_count, self.state[3]),
    )))
```

两个 raw scale 检查点返回后 `state` 保持全零，含义是**未访问/未检查**，不是“0 个 NaN，所以有限”。报告器按 stage 名显式生成缺口条目，以免消费者把这个零误读成精度保证。

## 失败路线与设计决策

| 路线 | 当前证据与处理 |
|---|---|
| raw scale 直接比较或 `isnan` | 已遇到诊断 dtype 不支持；不得将该异常当成模型 NaN |
| `view(uint8)` 再比较编码 | 某部署仍报 E8M0 不支持，不能假定 view 已改变后端可接受类型 |
| 数值 cast 到整数再比较 | 会转换数值，不能代替原始编码检查；不采用 |
| 独立 eager 的 Host 字节解释 | 另一路诊断方案，可能涉及临时 ND 格式和 CPU 读回；改变时序，仍须验证真实环境 |
| 当前 raw scale 完全跳过 | 保留其余探针，同时公开 coverage 缺口；这是局部兼容取舍，不是精度修复 |

历史 eager `_bad_counts` 若在内部/NZ 格式检查失败时尝试临时 ND，再尝试 CPU，全部失败会标 `[KIMI_EAGER_NAN_UNCHECKED]` 并返回 `None`。`None` 必须沿归因保留为 unknown，不能转成“输入有限”。这条兼容分支不更改模型 Tensor，也不能用它推导图内可执行相同 Host 操作。

## 验证信号

本次核对了 early-return 实现和以下已有 CPU 回归定义，没有执行上游测试或 NPU smoke。下面两个完整测试分别定义：raw scale 不被图消费，而 activation 仍能在后续调用检出异常；JSON 明确披露未检查点。依赖同一测试模块的 `torch`、`nn`、`pytest`、`FinitePoint`、`trace_tensor`、`NanTrace` 和 `json`。

```python
@pytest.mark.parametrize("encoded", [False, True])
def test_mx_scale_is_not_touched_while_activation_checks_still_replay(encoded):
    class CheckBoth(nn.Module):
        def __init__(self):
            super().__init__()
            self.activation = FinitePoint("cpu")
            self.scale = FinitePoint("cpu")

        def forward(self, x, scales):
            self.activation(x)
            self.scale(scales, mx_scale=True)
            return x * 2

    model = CheckBoth()
    graphs = []

    def backend(gm, _):
        graphs.append(gm)
        return gm.forward

    compiled = torch.compile(model, backend=backend, fullgraph=True)
    scale = torch.tensor([[0, 254], [255, 127]], dtype=torch.uint8)
    if encoded:
        dtype = getattr(torch, "float8_e8m0fnu", None)
        if dtype is None:
            pytest.skip("This PyTorch has no native E8M0 dtype")
        scale = scale.view(dtype)
    compiled(torch.ones(2), scale)
    compiled(torch.tensor([float("nan"), 1.0]), scale)
    assert model.activation.state.tolist() == [2, 2, 1, 0]
    assert model.scale.state.tolist() == [0, 0, 0, 0]
    assert len(graphs) == 1
    # No graph operation consumes the raw scale input at all, even view/cast.
    for node in graphs[0].graph.nodes:
        if node.op == "placeholder" and "scales" in str(node.target):
            assert not node.users
```

```python
def test_skipped_scales_are_reported_as_uninspected(tmp_path):
    class KimiSparseMoeBlock(nn.Module):
        def forward(self, x):
            trace_tensor(self, "gmm1", x)
            trace_tensor(self, "dispatch.mx_scale", object(), mx_scale=True)
            return x

    model = KimiSparseMoeBlock()
    trace = NanTrace((("target", model),), "cpu", tmp_path)
    trace.begin("target.decode")
    model(torch.tensor([float("nan")]))
    with pytest.raises(RuntimeError, match="KIMI_NAN_DETECTED"):
        trace.finish()
    report = json.loads((tmp_path / "nan_trace_rank0.jsonl").read_text())
    assert [row["stage"] for row in report["checkpoints"]] == ["gmm1"]
    assert {row["stage"] for row in report["skipped_checkpoints"]} == {
        "dispatch.mx_scale", "activation.mx_scale",
    }
    assert all("uninspected" in row["reason"] for row in report["skipped_checkpoints"])
```

第一个测试同时覆盖 uint8 编码与存在原生 E8M0 dtype 的情况；其关键断言是 scale 的统计始终未访问、FX placeholder 无 user、activation 仍被检查且图数量不增加。第二个测试用不可执行 Tensor 运算的对象作为 scale 参数，意在保证跳过确实发生在读取之前。上述均是待执行断言，不能记成 NPU 兼容性已通过。

## 部署验收与预期

先使用真实 `npu_dynamic_mx_quant` 的 E4M3/E8M0 输出运行现有单 NPU smoke，而不是手工 uint8 代用品。检查正常捕获、后续同 shape replay 注入 activation NaN、无效尾部屏蔽、raw scale 统计始终未访问，以及没有重新编译；必要时再验证 smoke 的 `--eager` 路线。只有这些记录实际获得，才可确认目标环境的探针兼容性。

然后回到原 YAML 做单轮及多卡长稳。若 `gmm1` 输出异常而 raw scale 未检查，报告仍只能给出“已检查 activation 到 GMM 输出之间”的边界，候选包括 scale、权重、GMM 内部和访存，不能将责任缩为 GMM kernel。

## 回退、坏实践与失效边界

- 不通过改模型 scale dtype、清洗数据、放宽容差或吞掉异常输出来消除诊断报错。
- 不把 `skipped_checkpoints` 的点、eager 返回 `None` 的输入或零访问计数当作已检查正常。
- 若切换 eager 作对照，应修改所有节点所用配置并重新启动全部 rank；不能在失败 capture 进程内临时混切。eager 时序改变，不复现不能排除图模式问题。
- 关闭诊断可恢复原模型路径，但只说明探针不再触发，不能说明精度根因消失。
- 优先未决项：在目标环境复现比较算子的 dtype 传递，核对实际后端和 storage，确定是否存在可正确检查 raw E8M0 的方法。在此之前，scale 保持未检查边界，本卡继续为草稿。

图内设备计数和全 rank 停止协议见 [图重放 NaN 边界探针](graph_replay_nonfinite_boundary_probe.md)。
