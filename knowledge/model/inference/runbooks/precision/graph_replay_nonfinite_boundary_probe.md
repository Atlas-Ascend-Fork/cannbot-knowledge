---
type: Runbook
title: Kimi K3 长稳 NaN 定位：图内设备计数、图外汇总与全 rank 一致退出
description: 在 npugraph_ex Decode 中用持久设备计数记录非有限边界，图外统一汇总；Prefill 保持 eager，GE 不支持此图诊断开关，目标
  NPU 长稳仍待验收。
tags:
- task.debugging
- topic.precision
- topic.graph_execution
- topic.parallelism
status: draft
sources: []
created_at: '2026-10-30T03:17:19Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
---

# Kimi K3 长稳 NaN 定位：图内设备计数、图外汇总与全 rank 一致退出

## 现象

本卡处理 Kimi K3 多卡 Decode 在 `npugraph_ex` 图重放长稳中的疑似异常排查：首先需要确认是否真的出现 Tensor 非有限值，再在确认后定位它最早出现的已覆盖边界。既有 profiling、输出文本或某张卡的负载变化本身不能证明已经发生 NaN，也不能证明硬件故障；真实 NaN 是否发生仍须由实际探针记录确认。捕获函数里的 Python `print`、hook 或日志通常只在 tracing/capture 时运行，无法作为每次 replay 的观测；逐算子 `.cpu()` / `.item()` 又会引入 Host 同步、改变多流时序，甚至破坏图捕获。

这里的办法是在图内更新持久设备计数，在每个完整 Host 调用返回并同步后读取，再由所有 rank 在同一边界汇总和共同退出。它是定位“非有限值从哪个已覆盖边界开始出现”的诊断路线，不能单凭异常边界宣判坏卡或 kernel 根因。

## 适用场景与启动条件

- 目标范围：950PR/DT 的 Kimi K3 target/draft 模型；Decode 保留 `npugraph_ex`，Prefill 保留 eager。目标 NPU 长稳及具体 CANN/torch_npu 部署组合尚未在本轮验收。
- 入口：模型上的显式 `trace_tensor` / `trace_routes` / `trace_experts` 检查点，设备模块 `FinitePoint` / `Probe`，Host 协调器 `NanTrace`。必须在首次 eager/compiled forward 之前附加并分配探针。
- 开关 `KIMI_NAN_TRACE=1` 必须在全部参与 rank 一致。`enabled()` 只接受字符串 `0` 或 `1`；某些 rank 未开启会使全局异常通信参与关系不一致。
- 编译入口明确要求 `exe_mode=npugraph_ex`，否则报 `KIMI_NAN_TRACE graph diagnostics require npugraph_ex`；GE 不支持这套图诊断开关。纯 eager 的算子级诊断与这里的图重放协议分别验收。
- 调试时磁盘编译缓存被禁用，进程内仍会捕获与 replay；否则可能重用没有探针的旧磁盘图。所有节点应采用一致代码和配置后重新启动。

## 数据流与检查边界

| 部分 | 关键检查点 | 能定位到的粒度 |
|---|---|---|
| target 主干 | embedding、每层 attention/MLP 输入、归一化与输出、final norm、lm_head 前后 | 主干阶段和层级 |
| KDA / MLA | KDA core/gate、ReduceScatter 前；MLA Prolog query、Flash 输出、AllToAll 前后、ReduceScatter 前后 | 显式融合边界和通信生产者/接收者 |
| routed MoE | router logits、TopK weight、down projection、Dispatch、GMM1、activation/quant、GMM2、Combine、norm、up projection | split 路线中已插入的检查点 |
| shared experts | gate-up、activation、down、ReduceScatter | shared 路线边界 |
| draft | target hidden/context、embedding、attention/MLP、写入 cache 的 key/value、logits、Markov bias 后结果 | draft context 和每次 draft decode 访问 |

融合 MegaMoE 的内部计算没有逐步展开；历史 KV/recurrent cache、全部权重和原始 E8M0 scale 也未被完整扫描。看见输入 activation 正常、输出异常，只缩小了候选范围。

## 图内计数的含义

每个检查点有独立的 `int64[4]` buffer：`[visits, first_bad_visit, nan, inf]`。

- `visits` 是当前 Host 调用中该点被访问的次数。
- `first_bad_visit` 为第一次发现异常的 **1-based 访问序号**；0 表示没有发现异常。Prefill 分块、draft 循环、capture 内部 warmup 都可能增加访问次数，它不是全局 token 序号。
- `nan`、`inf` 保留首次异常访问的计数，而非跨全部访问累加，也不被后续异常覆盖。
- 每点的设备统计独立分配，避免主/辅助流共写同一统计状态。诊断只增加计数，不修改被检查模型 Tensor。

## 设备计数器的完整状态机

以下为 `FinitePoint` 完整类，依赖同模块的 `math`、`torch` 和 `torch.nn as nn`。它把计数状态注册成设备 buffer，forward 通过 `copy_` 更新同一块存储，既不依赖 replay 中不会重新执行的 Python 日志，也不在图内读回 Host。`persistent=False` 表示这些诊断 buffer 不进入模型 state_dict，不表示每次 forward 都重新创建。

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

`visit = state[0] + 1` 每次有效检查递增；`first` 仅在历史首次异常位置仍为零、且当前 NaN/Inf 总数大于零时成立。只有这一次会写入首次异常访问号及其 NaN/Inf 计数，以后的访问保留这三个字段。各块使用全局 `row_offset` 对齐有效行，raw E8M0 scale 则在任何读取前直接返回，连访问次数也不增加，必须按报告的跳过点解释。

## 预分配、模型接线与同一状态对象

下面的完整 `Probe` 为每个 stage 分配一个独立 `FinitePoint`，并预分配专家/路由计数；`trace_tensor` 使用模型实例上的 `_nan_trace` 和同一 stage 索引找到它。stage 名必须与模型显式调用及现有 `STAGES` 表一致，不能随意重命名后仍认为接线有效。

```python
class Probe(nn.Module):
    def __init__(self, stages, device, expert_count=0, ep_size=0):
        super().__init__()
        self.points = nn.ModuleList(FinitePoint(device) for _ in stages)
        self.stage_index = {stage: i for i, stage in enumerate(stages)}
        self.register_buffer("expert_counts", torch.zeros(expert_count, dtype=torch.int64, device=device), persistent=False)
        self.register_buffer("dest_counts", torch.zeros(ep_size, dtype=torch.int64, device=device), persistent=False)
        self.register_buffer("route_invalid", torch.zeros((), dtype=torch.int64, device=device), persistent=False)
        self.register_buffer("counts_invalid", torch.zeros((), dtype=torch.int64, device=device), persistent=False)
```

```python
def trace_tensor(module, stage, value, valid_rows=None, mx_scale=False):
    probe = getattr(module, "_nan_trace", None)
    if probe is not None and value is not None:
        probe.points[probe.stage_index[stage]](value, valid_rows, mx_scale)
```

完整的协调器初始化方法展示如何把同一个 probe 同时注册在模型上，并保留到 Host 协调器的 `self.probes` 列表。它属于 `NanTrace` 类，依赖同模块的 `dist`、`os`、`Path`、`logging`、`Probe`、`STAGES` 与 `MX_SCALE_SKIP_REASON`；`models` 提供 `(role, model)`，role 用来区分 target/draft。`list(model.named_modules())` 先固定遍历列表，避免一边挂子模块一边改变正在遍历的模块树。这里使用现有模型和检查点注册表，不是独立构造整网的脚本。

```python
def __init__(self, models, device, output_dir=None):
    self.device = device
    self.rank = dist.get_rank() if dist.is_initialized() else int(os.getenv("RANK_ID", "0"))
    self.output_dir = Path(output_dir or os.getenv("RES_PATH", "res"))
    self.probes = []
    self.call = 0
    self.context = {}
    for role, model in models:
        if model is None:
            continue
        # Materialize before attaching submodules to avoid mutating traversal.
        for name, module in list(model.named_modules()):
            stages = STAGES.get(type(module).__name__)
            if stages is None:
                continue
            probe = Probe(stages, device,
                          getattr(module, "local_expert_count", 0),
                          getattr(module, "moe_ep_size", 0))
            module.add_module("_nan_trace", probe)
            self.probes.append((role, name, stages, probe))
    state_bytes = sum(buffer.numel() * buffer.element_size()
                      for _, _, _, probe in self.probes for buffer in probe.buffers())
    logging.warning("[KIMI_NAN_TRACE] enabled rank=%s checkpoints=%s state_payload_bytes=%s "
                    "(excludes allocator alignment/graph pool); diagnostic timings are not a performance baseline",
                    self.rank, sum(len(stages) for _, _, stages, _ in self.probes), state_bytes)
    logging.warning("[KIMI_NAN_TRACE_SKIPPED] %s", MX_SCALE_SKIP_REASON)
```

这条对象关系必须一直保留：`module._nan_trace` 与 `self.probes` 中的 probe 是同一个模块对象；模型前向的 `trace_tensor` 调用 `probe.points[i].forward`，图内写入的 `state`，正是后文 `begin` 原地清零、`finish` 堆叠读取的 `point.state`。如果在 capture 后替换 probe、换掉 state buffer 或只向 Host 列表复制数值，这个“图写入、Host 读取”的关系就会断开。

专家 metadata 的设备更新使用下面两个完整 helper，与上述 `Probe` 中的 `route_invalid`、`dest_counts`、`expert_counts`、`counts_invalid` 接线。`trace_routes` 要求模型具备 `num_experts`、`local_expert_count` 和 `moe_ep_size`；`trace_experts` 的 counts 是 count 模式。非法 ID/计数与 Tensor 非有限是两种不同信号，但都会在后文 `finish` 的全局标志汇总中触发停止。

```python
def trace_routes(module, ids):
    probe = getattr(module, "_nan_trace", None)
    if probe is not None:
        invalid = ((ids < 0) | (ids >= module.num_experts)).sum()
        probe.route_invalid.add_(invalid)
        # Fixed-size scatter_add avoids bincount's data-dependent output shape.
        dest = (ids.flatten().long() // module.local_expert_count).clamp(0, module.moe_ep_size - 1)
        counts = torch.zeros_like(probe.dest_counts)
        counts.scatter_add_(0, dest, torch.ones_like(dest))
        probe.dest_counts.copy_(counts)
```

```python
def trace_experts(module, counts, capacity):
    probe = getattr(module, "_nan_trace", None)
    if probe is not None:
        # Both DispatchV2 and re-routing use count mode (group_list_type=1).
        probe.expert_counts.copy_(counts.reshape(-1))
        probe.counts_invalid.add_(((counts < 0).any() | (counts.sum() > capacity)).long())
```

图内仅用 Tensor 计算计数和原地更新；图外 `begin` 原地清零以保留 capture 绑定的地址，不能为每次调用重新创建 buffer 或替换 module。以下是已有完整方法，属于 `NanTrace` 类；`self.probes` 是初始化时收集的 `(role, name, stages, probe)`，每个 probe 由模型检查点定义提前建立。

```python
def begin(self, phase, warm_up=False):
    self.call += 1
    self.context = dict(call=self.call, phase=phase, warm_up=warm_up)
    # In-place reset preserves every graph-captured buffer address.
    for _, _, _, probe in self.probes:
        for point in probe.points:
            point.state.zero_()
        probe.expert_counts.zero_()
        probe.dest_counts.zero_()
        probe.route_invalid.zero_()
        probe.counts_invalid.zero_()
```

## 图外汇总与全 rank 退出

每次 target forward、draft context prefill 或 draft decode 开始前调用 `begin(phase, warm_up)`，在前向返回并完成设备同步后调用 `finish()`。`finish()` 必须处于 compiled/captured 函数之外，不能把下面的 `.item()`、CPU 读回、文件写入和 collective 放进图。

下面完整方法显示“某个 rank 有异常，所有 rank 均留档并停止”的协议。依赖同模块的 `torch`、`dist`、`logging`、`json`、`os`、`socket`、`MX_SCALE_STAGES` 和 `MX_SCALE_SKIP_REASON`，以及初始化的输出目录与 probe；它不是可以脱离模型同步边界随意调用的独立脚本。

```python
def finish(self):
    # Called only after synchronize, outside every compiled function.
    points = [(role, name, stages, probe) for role, name, stages, probe in self.probes]
    states = torch.stack([point.state for _, _, _, probe in points for point in probe.points])
    flags = [states[:, 1].amax()]
    flags.extend(probe.route_invalid + probe.counts_invalid for _, _, _, probe in points)
    any_bad = (torch.stack(flags).amax() > 0).to(torch.int32)
    if dist.is_initialized():
        dist.all_reduce(any_bad, op=dist.ReduceOp.MAX)
    if not any_bad.item():
        return
    rows = states.cpu().tolist()
    checkpoints, routes, skipped_checkpoints = [], [], []
    cursor = 0
    for role, name, stages, probe in points:
        for stage in stages:
            visits, first_bad, nan, inf = rows[cursor]
            cursor += 1
            if stage in MX_SCALE_STAGES:
                skipped_checkpoints.append(dict(
                    model=role, module=name, stage=stage, reason=MX_SCALE_SKIP_REASON,
                ))
            if visits:
                checkpoints.append(dict(model=role, module=name, stage=stage,
                                        visits=visits, first_bad_visit=first_bad,
                                        nan=nan, inf=inf))
        if probe.expert_counts.numel():
            routes.append(dict(model=role, module=name,
                               expert_counts=probe.expert_counts.cpu().tolist(),
                               destination_ep_counts=probe.dest_counts.cpu().tolist(),
                               invalid_expert_ids=probe.route_invalid.item(),
                               invalid_expert_counts=probe.counts_invalid.item()))
    report = dict(rank=self.rank, host=socket.gethostname(), pid=os.getpid(),
                  run=os.getenv("KIMI_INFER_RUN", "single"), **self.context,
                  checkpoints=checkpoints, routes=routes,
                  skipped_checkpoints=skipped_checkpoints)
    path = self.output_dir / f"nan_trace_rank{self.rank}.jsonl"
    bad = [row for row in checkpoints if row["first_bad_visit"]]
    # Every rank, including healthy ranks, emits this marker so multi_infer
    # stops on every host despite infer.sh not propagating worker exits.
    logging.error("[KIMI_NAN_DETECTED] rank=%s context=%s local_bad=%s report=%s",
                  self.rank, self.context, len(bad), path)
    for row in bad[:20]:
        logging.error("[KIMI_NAN_POINT] %s", json.dumps(row))
    try:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(report, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        # Still participate in the barrier; local disk errors must not
        # strand the other ranks. Retain the evidence in the worker log.
        logging.exception("Cannot write NaN report; report=%s", json.dumps(report))
    if dist.is_initialized():
        dist.barrier()
    raise RuntimeError("KIMI_NAN_DETECTED: all ranks stopped after saving finite checks")
```

全局异常标志使用 world-wide `MAX all_reduce`：即使本 rank 的所有 activation 正常，只要另一个 rank 异常，本 rank 也写自己的正常检查点并打印 `[KIMI_NAN_DETECTED]`。文件写入失败时仍尝试参加 barrier，避免单张卡因本地磁盘异常先退出、其余卡永远等待。这里的 barrier 不能挽救已经挂在图内通信、无法返回 Host 的进程。

## 如何读报告并继续定位

1. 保存所有节点的 `nan_trace_rank<global_rank>.jsonl` 和对应 worker 日志。正常调用不写 JSON；异常调用保存该 rank 已访问的正常点与异常点，控制台只展示有限数量，不能据此认为只有这些点异常。
2. 用 `run`、`call`、`phase` 区分长稳运行序号、当前进程 Host 调用和 target/draft 阶段。层号从 0 开始。
3. 沿真实依赖顺序比较生产者和接收者，找最靠前的“已检查输入有限、输出非有限”边界。模块注册顺序、JSON 行顺序和跨卡 wall-clock 都不是全局因果顺序。
4. `routes.expert_counts` 是本地专家 count，`destination_ep_counts` 是源 rank 路由到目标 EP 的分布；多个 Prefill chunk 时它们保留最后一次更新，**不一定是首次异常 chunk 的快照**。
5. `invalid_expert_ids` 或 `invalid_expert_counts` 也会触发共同停止，应先分辨路由 metadata 非法与 activation 非有限两类信号。
6. 将 `skipped_checkpoints` 当作明确盲区，不把未访问、被跳过或未注册检查点写成“正常”。例如 `dispatch.output` 正常而 `gmm1` 异常，仍需排查未检查的 MX scale、权重、GMM 内部及访存。

## 验证信号与部署验收

本次只核对了完整计数/汇总方法、编译入口限制与回归断言，没有执行上游 CPU/NPU 测试。以下已有完整 CPU 测试定义了正常捕获后再注入 NaN、同 shape 不重新编译的检查；它依赖测试文件的 `KimiMoEGate` 小模型、`torch`、`NanTrace`、`pytest` 和 `json`。看到测试定义不能记为测试已通过。

```python
def test_later_compiled_call_detects_nan_without_recompile(tmp_path):
    module = KimiMoEGate()
    trace = NanTrace((("target", module),), "cpu", tmp_path)
    graphs = []

    def backend(gm, _):
        graphs.append(gm)
        return gm.forward

    compiled = torch.compile(module, backend=backend, fullgraph=True)
    trace.begin("target.decode")
    torch.testing.assert_close(compiled(torch.ones(2, 3)), torch.full((2, 3), 2.0))
    trace.finish()
    trace.begin("target.decode")
    x = torch.ones(2, 3)
    x[1, 2] = float("nan")
    compiled(x)
    with pytest.raises(RuntimeError, match="KIMI_NAN_DETECTED"):
        trace.finish()
    assert len(graphs) == 1
    report = json.loads((tmp_path / "nan_trace_rank0.jsonl").read_text())
    assert report["call"] == 2
    assert report["checkpoints"][0]["nan"] == 1
    assert report["checkpoints"][0]["first_bad_visit"] == 1
    assert not (tmp_path / "nan_trace_rank1.jsonl").exists()
```

部署验收应按顺序完成：先运行现有 CPU fullgraph/AOT、首次异常保留/reset、有效行、双 rank 共同停止用例；再在空闲 NPU 上使用真实量化输出执行 capture/replay smoke；最后用原请求、权重与并行配置执行目标多卡长稳。NPU smoke 要先正常捕获，再保持 shape 不变地在后续 replay 注入异常，确认无重编译、padding 不误报和 scale 覆盖缺口仍被保留。Prefill 继续独立验证 eager 汇总，不为验收该探针而改成 Prefill 图。

## 设计决策、坏实践与回退

- 选择设备持久计数，是为了 replay 时仍执行诊断，同时把 Host 读取集中到现有调用边界；代价是扫描、归约、同步与图池开销，不能把调试耗时拿来比较快慢卡或优化收益。
- 不在图内打印，不通过逐层同步复制完整 activation 代替此低维记录，也不让单 rank 发现异常后立即抛错而其他 rank 继续集合通信。
- 不因为某点最先出现在 JSON 就归罪该点，不因为结果文字含 `nan` / `!!!` 就认定 Tensor 出现 NaN。
- 回退时关闭开关，全部 rank 重新启动并恢复匹配的未插桩图缓存；不要混用有/无探针进程。
- 未决项：实际 NPU capture/replay、真实 dtype 兼容和目标多卡长稳仍待验收。图未返回 Host 时无法保证留档；未覆盖的权重、cache 和融合内部仍需下一轮定向探针或 dump。

原始 E8M0 的覆盖限制见 [不支持的比较类型](nan_probe_e8m0_unsupported_comparison.md)；扫描开销见 [长 Prefill 扫描峰值](../performance/nan_probe_prefill_scan_peak_memory.md)。
