---
type: Runbook
title: 开启 NaN 探针后长 Prefill 内存上涨：分块扫描，避免整张量 FP32 副本
description: 保留普通浮点 dtype，沿第一维分块扫描，仅对当前块的 E4M3 activation 转换；原始 E8M0 scale 仍跳过检查并披露覆盖缺口，分块目标不是模型总峰值上限。
tags:
- task.debugging
- task.optimization
- topic.memory
- topic.precision
status: draft
sources: []
created_at: '2026-10-30T03:17:19Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      objective:
      - memory
      phase:
      - prefill
---

# 开启 NaN 探针后长 Prefill 内存上涨：分块扫描，避免整张量 FP32 副本

## 现象

Kimi K3 原路径能够运行，打开非有限值诊断后长 Prefill 的峰值内存明显上涨。启动日志显示持久计数 buffer 很小，仍不能据此排除探针开销：旧扫描对完整 activation 建立 FP32 副本，再生成全尺寸布尔 mask，临时副本、归约 workspace 和图内存池可能远大于统计状态。

该问题与模型本来就有的 MoE 长序列 OOM 要分开。先比较完全相同请求、权重和并行配置下的诊断关闭/开启行为，确认新增开销来自探针，再采用本卡的扫描实现。

## 适用场景与数据范围

- 目标是 950PR/DT 的 Kimi K3 `FinitePoint`，重点为 eager Prefill 的长 activation；相同检查模块也可进入 `npugraph_ex` Decode，但图内池与 replay 行为需要另外验收。
- 普通 FP16/BF16/FP32/FP64 直接保持原 dtype 检查。需要转换的 E4M3 activation 只转换当前块，不对整输入 `.float()`。
- raw E8M0 scale 在任何读取、view、cast、比较前返回，并显式记录未检查。这不是“所有 FP8 类型都可以分块转换”的通用规则。
- 具体 NPU 峰值、CANN/torch_npu 版本和性能收益没有本轮实测；该方案只承诺代码层面的分块组织，不保证不会 OOM。

## 内存机制与分块推导

设输入总元素数为 `E`。对完整 BF16 输入执行 `.float()` 会额外创建 `4 × E` 字节的 FP32 数据副本，原 BF16 数据仍然存在；每个全尺寸布尔 Tensor 还需要按元素规模分配，且不包含后端归约 workspace。仅计算计数 buffer 的逻辑字节，解释不了这些瞬时峰值。

扫描沿第一维切片。若第一维每行宽度为 `W = max(1, product(shape[1:]))`，每块目标为 `L = max_check_elements`，则 `chunk_rows = max(1, floor(L / W))`。默认 `L` 为 `2^20` 个元素。

- 当 `W <= L` 时，单块数据元素数不超过 `L`；E4M3 转 FP32 也只发生在这个块内。
- 当单行本来就比目标宽，即 `W > L`，最小单元仍是一整行，因此 `chunk_rows=1`，单块元素数为 `W`，**会超过目标 L**。不能把 `L` 写成硬性分配上限。
- 非连续输入用 `value[start:start + chunk_rows]` 切片，不先 flatten/reshape 整张量。整体 reshape 可能隐式复制全部输入，使分块失去意义。
- 有效行比较使用 `local_row + row_offset < valid_rows`。`row_offset` 必须带上当前块起点，否则后面的无效尾部可能被当成有效行扫描。

## 完整扫描实现

下列为已有 `FinitePoint` 完整类，依赖同模块的 `math`、`torch`、`torch.nn as nn`。state 在初始化时分配，forward 只累加当前访问的计数并原地写回；`mx_scale=True` 在最前返回。它可作为核对部署实现的完整机制单元，不是单独包含模型上下文的推理脚本。

```python
class FinitePoint(nn.Module):
    def __init__(self, device, max_check_elements=1 << 20):
        super().__init__()
        self.max_check_elements = max_check_elements
        # visits, first bad visit (1-based), NaN count, Inf count.
        self.register_buffer("state", torch.zeros(4, dtype=torch.int64, device=device), persistent=False)

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

    @staticmethod
    def _count_chunk(value, valid_rows, row_offset):
        if value.dtype not in (torch.float16, torch.bfloat16, torch.float32, torch.float64):
            # E4M3 needs conversion, but only for this chunk. Raw E8M0 scales
            # returned above before any tensor operation.
            value = value.float()
        if valid_rows is None:
            return torch.isnan(value).sum(), torch.isinf(value).sum()
        rows = torch.arange(value.shape[0], device=value.device) + row_offset < valid_rows
        rows = rows.reshape((-1,) + (1,) * (value.ndim - 1))
        return (torch.isnan(value) & rows).sum(), (torch.isinf(value) & rows).sum()
```

## 实际排查步骤

1. 记录当前输入 shape、dtype、stride、是否连续，计算 `W` 和实际 `chunk_rows`。不要只记录总元素数；单行特别宽时必须单独评估。
2. 检查实际扫描实现是否在切片前调用 `value.float()`、`flatten()`、`reshape()` 或生成完整 mask；这些操作会把主要临时开销提前发生。
3. 区分持久统计、当前块转换、布尔 mask、归约 workspace、多 stream 同时存活的临时量和图池保留。`state_payload_bytes` 只统计逻辑 buffer，排除了分配器对齐和 graph pool。
4. 验证有效行掩码横跨块边界仍正确，尤其是非连续输入和 `valid_rows` 落在块中间的情况。
5. 确认 raw scale 仍被跳过，启动/异常报告仍披露覆盖缺口；不能为了减少内存而顺手删除其他 activation 检查点。

## 验证信号

本次核对了分块实现、非连续多块计数和临时分配守卫的测试定义，没有运行这些测试或 NPU 峰值测量。以下完整 fixture 分别约束跨块计数/无效尾部，以及普通 BF16 不产生 FP32 提升、E4M3 转换和布尔结果只在测试块范围内产生；它们依赖已有测试模块的 `torch`、`pytest` 和 `FinitePoint`。

```python
def test_chunked_noncontiguous_check_preserves_counts_and_padding():
    point = FinitePoint("cpu", max_check_elements=12)
    compiled = torch.compile(point, backend="aot_eager", fullgraph=True)
    x = torch.ones(6, 8, dtype=torch.bfloat16).t()
    x[0, 0] = float("nan")
    x[4, 2] = float("inf")
    x[6, 3] = float("nan")  # Outside the valid prefix, in a later chunk.
    assert not x.is_contiguous()
    compiled(x, torch.tensor(5))
    assert point.state.tolist() == [1, 1, 1, 1]
```

```python
@pytest.mark.parametrize("dtype", [torch.bfloat16, torch.float8_e4m3fn])
def test_temporary_masks_and_conversions_are_chunk_bounded(dtype):
    from torch.utils._python_dispatch import TorchDispatchMode

    class AllocationGuard(TorchDispatchMode):
        def __torch_dispatch__(self, func, types, args=(), kwargs=None):
            output = func(*args, **(kwargs or {}))
            if isinstance(output, torch.Tensor):
                if output.dtype == torch.bool:
                    assert output.numel() <= 12
                if output.dtype == torch.float32:
                    # Ordinary BF16 must never be promoted; FP8 casts must
                    # stay chunk-sized instead of copying the whole input.
                    assert dtype == torch.float8_e4m3fn
                    assert output.numel() <= 12
            return output

    point = FinitePoint("cpu", max_check_elements=12)
    x = torch.ones(8, 6).to(dtype)
    with AllocationGuard():
        point(x, torch.tensor(7))
    assert point.state.tolist() == [1, 0, 0, 0]
```

这里的小形状和块目标是测试 fixture，用来强制触发多个块，不是模型部署推荐值。分配守卫只证明被检查的 Tensor 输出尺寸约束；不能代替后端 workspace 或真实分配器峰值记录。

## 部署验收与预期结果

保持请求、权重、并行配置和 Prefill 分块不变，依次记录诊断关闭、旧扫描、新扫描的峰值与输出；分开记录分配与保留内存，区分 eager 首次前向、capture 和后续 replay。比较诊断方案时还要保留相同检查覆盖，不能拿少检查点的结果宣称扫描优化。

在受支持的 activation 中分别注入首块、跨块和有效前缀内异常，再仅在无效尾部放异常。预期为有效异常均被检出、尾部不误报、首次异常计数保持正确；raw E8M0 scale 仍无访问，JSON 继续列出未检查点。

真实 NPU 上还要使用动态量化产生的 E4M3/E8M0 数据验证 dtype 路径。CPU 的 fullgraph 或 AllocationGuard 不能证明 NPU kernel 数学、峰值或 graph pool 保留已达标。

## 设计取舍、坏实践与回退

- 保留原 dtype、按第一维切片是为了限制单次扫描工作量，同时保留非连续张量布局；不为诊断强迫模型 activation 整体连续化。
- 块越小可能产生更多检查/归约节点与调用开销；没有目标设备数据，不给出固定性能改善或最佳块大小。
- 不把每点 4 个 int64 的小状态写成“探针只有这些显存开销”；不把布尔/转换块大小当作整个模型新增显存上限。
- 不通过跳过有效数据、清理 NaN、改变容差或把 FP8 编码当普通整数比较来得到通过结果。
- 回退时关闭探针，恢复匹配的未插桩路径与缓存，保留模型原计算。若关闭探针仍 OOM，应转入 [MoE 长序列 OOM 排查](moe_prefill_oom_peak_memory.md)，而不是继续认定探针为根因。
- 未决项：单行超宽、多流临时量重叠、后端归约 workspace 和 capture 后图池保留的实际峰值尚未测量。本卡保持草稿，不承诺零开销或不会 OOM。

E8M0 的独立兼容边界见 [E8M0 诊断类型限制](../precision/nan_probe_e8m0_unsupported_comparison.md)。
