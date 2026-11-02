---
type: Runbook
title: MoE NaN 探针误报：只扫描 Dispatch 与 GMM 的有效专家行
description: 仅按已确认的 packed 专家行裁剪探针，区分专家有效行与 Combine 有效请求行；复现按 shape 套用专家行数导致的漏报，并给出显式边界检查与 CPU 回归。
tags:
- task.debugging
- topic.precision
- topic.mixture_of_experts
status: stable
sources: []
created_at: '2026-10-30T03:17:18Z'
updated_at: '2026-11-02T02:47:27Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - moe
      phase:
      - decode
---

# MoE NaN 探针误报：只扫描 Dispatch 与 GMM 的有效专家行

## 现象

在 Kimi K3 的 eager Decode 中启用算子级 NaN/Inf 诊断后，`npu_moe_distribute_dispatch_v2` 或后面的 grouped matmul 被报告为异常；但直接参与专家计算的 token 可能仍是正常值。原因是 Dispatch 返回了按静态容量分配的专家 buffer：第一维是可容纳的行数，不等于这次实际收到的行数。未写入的尾部可能含 NaN、Inf 或上一次内容，通用全张量扫描会把这些尾行计入。

另一种容易误导的现场是 Combine 输出真的含 NaN，而输入 buffer 只有无效尾部含 NaN。若报告检查输入时仍扫描全容量，就会把这个现场归类成“输入已有异常”，遮住真正需要继续排查的有限输入到非有限输出边界。

还有相反的漏报：专家容量 `C=4`、有效专家行 `R=2`，Combine 恰好返回四行**全部有效**的请求输出 `[1, 1, 1, NaN]`。下文保留的历史 dispatcher 仅凭首维等于 C 就裁成前 R 行，会直接返回这个含真实 NaN 的结果。同样的误裁剪也会隐藏同形状权重或 shared 分支张量中的异常。

**历史代码存在已复现的漏报缺陷，不能直接作为修正后的通用探针使用。** 本卡保留它用于定位问题；可复用的是“先确认张量角色与布局，再确定检查范围”的诊断规则，以及后文的显式边界检查示例。文档修订不代表模型仓的 dispatcher 已被修复。

## 适用场景

- 工程路径：950PR/DT 上 Kimi K3 的 split MoE Decode，Dispatch → GMM1 → activation/quant → GMM2 → Combine；局部诊断入口为 `eager_nan_trace.py` 的 `EagerNanTrace` 和 `trace_valid_rows`。
- 数据前提：`expert_token_num` 是每个本地专家的实际 token **计数**，对应 `group_list_type=1`；专家行组成 packed 前缀，尾部仅是容量。必须先查真实算子接口，不能把累计 group-list 当计数求和。
- 角色前提：每个被裁剪的 Tensor 都必须由算子参数/返回项语义或明确的模型边界确认属于该 packed 专家行布局；`shape[0] == C` 只能检查容量是否一致，不能证明角色。Combine 输出按自己的有效请求范围检查，权重与 shared 分支不能继承专家 R。
- 本卡给出的是诊断口径；不修改 Dispatch、GMM、Combine 的真实数据，也不证明模型已经没有 NaN。具体 CANN/torch_npu 组合与真实模型精度尚需部署验收，不能由 CPU fixture 外推。
- 若部署使用融合 MegaMoE，只能检查融合输入/输出；本卡的中间检查点不代表能观察其内部专家缓冲。

## 根因与判别方法

设专家计数为 `c_e`，buffer 第一维容量为 `C`，则实际专家行数为 `R = sum(c_e)`。只有在 count 模式和 packed-prefix 契约同时成立时，`buffer[:R]` 才是这次算子有效输入/输出；`buffer[R:C]` 不应参与精度判断。

此处的“输入/输出”仅指已确认采用上述布局的**专家张量**，不包括作用域内任意同形状张量。Combine 从专家行还原请求行，二者不是同一个行空间：它的专家输入可以使用 R，请求输出则必须使用独立确认的有效请求数 N；没有请求 padding 契约时，默认扫描全部请求输出。

| 已确认的张量角色 | 检查范围 | 不能采用的推断 |
|---|---|---|
| Dispatch 的 packed 专家输出、保持同一行布局的 GMM/activation 中间结果 | 专家有效前缀 `[:R]`；先校验容量与布局 | 不能把同一个返回元组中的其他张量一并裁成 R |
| Combine 的 packed 专家输入 | 专家有效前缀 `[:R]` | 不能只因该输入首维等于 C 就认定它是 packed 布局 |
| Combine 的请求输出 | 独立的有效请求范围；全部有效时扫描整个输出 | 即使输出首维也等于 C，仍不能使用 R |
| 权重、shared 分支及其他输入/输出 | 按各自契约检查；无明确 padding 说明时扫描全范围 | 不能继承外层专家有效行上下文 |

1. 在 Dispatch 返回处保留 `expert_token_num`、`R`、`C` 和异常行位置。先检查所有专家计数非负，且 `R <= C`。计数非法是独立的路由/metadata 问题，不能通过截断 `R` 掩盖。
2. 分别检查有效前缀与尾部。如果只在 `R:C` 发现异常，先修探针范围，不把现象归因为 GMM 算错。
3. 逐个核对已确认的 packed GMM1、activation/quant、GMM2 和 Combine 专家输入采用的 `R` 是否一致，并独立核对 Combine 请求输出的 N。只修 Dispatch 输出扫描而忘记 Combine 输入，会污染归因；反过来把 R 套到请求输出，又会漏掉真实异常。
4. 比较报告中的 `checked_inputs`、`bad_outputs`、`valid_rows` 和 `unchecked_float_inputs`，不能只看最外层的 `input_is_nan` 布尔值。

`EagerNanTrace` 对 Dispatch 特殊处理时会读取返回元组第 4 项 `result[3]` 作为计数，检查最小值和总和；这依赖该版本的返回签名。普通 `trace_valid_rows` helper 只检查聚合后的行数范围，**不会单独验证每个专家计数非负**。绕过 Dispatch wrapper 直接调用 helper 时，调用方还须做逐专家合法性检查。

## 机制代码与作用域

下面是历史实现的完整上下文管理器。它依赖同模块的 `_ACTIVE_TRACE`、`_ACTIVE_ROWS` 与 `_disable_current_modes`；未启用诊断时只透传，不增加读取。启用时把 `(R, C)` 放入上下文，并在离开作用域时恢复旧值。恢复上下文能避免跨模块泄漏，**不能解决作用域内部不同张量角色被误裁剪的问题**。

```python
@contextlib.contextmanager
def trace_valid_rows(counts, capacity):
    """Restrict checks to packed MoE rows consumed by grouped matmul."""
    if _ACTIVE_TRACE.get() is None:
        yield
        return
    with _disable_current_modes():
        rows = int(counts.sum().item())
    if rows < 0 or rows > capacity:
        raise RuntimeError(f"Invalid MoE valid rows: {rows}, capacity: {capacity}")
    token = _ACTIVE_ROWS.set((rows, capacity))
    try:
        yield
    finally:
        _ACTIVE_ROWS.reset(token)
```

### 有效行的实际消费者

`trace_valid_rows` 只把 `(R, C)` 放进 `ContextVar`；历史 `EagerNanTrace.__torch_dispatch__` 读取它并按 shape 裁剪，缺少张量角色绑定。只复制上下文管理器、不安装消费者，并不会让普通 `torch.isnan` 自动忽略 padding；成套安装这版消费者也不能保证正确，仍会触发本文的同形状漏报。

先看完整的 `_bad_counts`。它依赖同模块的 `_CHECK_DTYPES`、`_disable_current_modes`、`_count_value`、`_as_nd`、`_WARNED_UNCHECKED`、`_rank`、`sys` 和 `torch`。`_count_value` 返回 NaN/Inf 整数计数，`_as_nd` 只为诊断创建临时 ND 视图/转换；二者沿用部署版本实现，不在这里改模型数据。`valid_rows` 非空时，先裁 `value[:valid_rows]`，再计数；`_disable_current_modes` 避免诊断自己的 Tensor 操作递归触发诊断。未支持的 dtype、空张量或无法完成检查的兼容分支返回 `None`，它不是有限值结论。

```python
def _bad_counts(tensor, valid_rows=None):
    if tensor.dtype not in _CHECK_DTYPES or tensor.numel() == 0:
        return None
    with _disable_current_modes():
        value = tensor.detach()
        if valid_rows is not None:
            value = value[:valid_rows]
        try:
            return _count_value(value)
        except RuntimeError as error:
            if value.device.type != "npu" or "internal format" not in str(error).lower():
                raise
        # Some NPU tensors use an internal/NZ format that aclnnIsNan cannot
        # compare directly. Reformat a temporary; never change the model data.
        try:
            return _count_value(_as_nd(value))
        except RuntimeError as nd_error:
            try:
                return _count_value(value.cpu())
            except RuntimeError as host_error:
                key = (str(tensor.dtype), str(nd_error), str(host_error))
                if key not in _WARNED_UNCHECKED:
                    _WARNED_UNCHECKED.add(key)
                    print("[KIMI_EAGER_NAN_UNCHECKED] "
                          f"rank={_rank()} dtype={tensor.dtype} shape={list(tensor.shape)} "
                          f"ND check failed: {nd_error}; CPU check failed: {host_error}",
                          file=sys.stderr, flush=True)
                return None
```

下面保留 `EagerNanTrace` 类的完整历史 `__torch_dispatch__` 方法，供复现和定位，**不是可直接复制的修正版**。该类继承 `TorchDispatchMode`，其 `__init__` 保存 `phase` 与 `step`；此方法还依赖同模块的 `_tensors`、`_ACTIVE_ROWS`、`_MAX_MUTABLE_PRECHECK_ELEMENTS`、`_OUTPUT_DTYPES`、`_bad_counts` 和 `_report_bad`。`_tensors` 遍历参数及容器里的 Tensor，`_report_bad` 生成下文的 JSON 分类并终止本轮 eager 诊断。

```python
def __torch_dispatch__(self, func, types, args=(), kwargs=None):
    kwargs = kwargs or {}
    inputs = list(_tensors(args, "args")) + list(_tensors(kwargs, "kwargs"))
    name = str(func)
    # Stream lifetime bookkeeping does not compute tensor values. In
    # particular, its mutable schema must not trigger a full tensor scan.
    if "record_stream" in name:
        return func(*args, **kwargs)
    # Allocators return uninitialized storage. Views cannot introduce new
    # values either, and may expose storage while it is still being filled.
    if name.startswith(("aten.empty.", "aten.empty_strided.",
                        "aten.empty_like.", "aten.new_empty.")):
        return func(*args, **kwargs)
    # For in-place/out= operations, input values must be checked before
    # invocation; otherwise the mutated input hides the first bad output.
    before_mutated = {}
    written = []
    if func._schema.is_mutable:
        for index, argument in enumerate(func._schema.arguments):
            if argument.alias_info is None or not argument.alias_info.is_write:
                continue
            value = args[index] if index < len(args) else kwargs.get(argument.name)
            written.extend(_tensors(value, f"mutated.{argument.name}"))
        for _, tensor in written:
            before_mutated[id(tensor)] = (
                _bad_counts(tensor)
                if tensor.numel() <= _MAX_MUTABLE_PRECHECK_ELEMENTS else None
            )
    result = func(*args, **kwargs)
    active_rows = _ACTIVE_ROWS.get()
    if name.startswith("npu.npu_moe_distribute_dispatch_v2."):
        with _disable_current_modes():
            counts = result[3]
            rows = int(counts.sum().item())
            minimum = int(counts.min().item())
        capacity = result[0].shape[0]
        if minimum < 0 or rows > capacity:
            raise RuntimeError(
                f"Invalid MoE dispatch counts: min={minimum}, "
                f"sum={rows}, capacity={capacity}"
            )
        active_rows = (rows, capacity)
    output_tensors = list(_tensors(result, "output"))
    output_ids = {id(tensor) for _, tensor in output_tensors}
    output_tensors.extend((name, tensor) for name, tensor in written
                          if id(tensor) not in output_ids)
    if not func._schema.is_mutable and inputs and output_tensors:
        input_storage = {tensor.untyped_storage().data_ptr()
                         for _, tensor in inputs}
        if all(tensor.untyped_storage().data_ptr() in input_storage
               for _, tensor in output_tensors):
            return result
    def row_limit(tensor):
        if active_rows is not None and tensor.ndim and tensor.shape[0] == active_rows[1]:
            return active_rows[0]
        return None

    outputs = [(output_name, tensor, _bad_counts(tensor, row_limit(tensor)))
               for output_name, tensor in output_tensors
               if tensor.dtype in _OUTPUT_DTYPES]
    if not any(counts is not None and any(counts) for _, _, counts in outputs):
        return result
    before = [(name, tensor,
               before_mutated[id(tensor)] if id(tensor) in before_mutated
               else _bad_counts(tensor, row_limit(tensor)))
              for name, tensor in inputs]
    _report_bad(self, str(func), before, outputs,
                None if active_rows is None else active_rows[0])
    return result
```

按该方法的执行顺序理解范围：

1. 执行真实算子前，先识别 schema 中可写的参数。小于预检查阈值的可写输入提前计数，超大可写输入记为 `None`；这些计数保存在 `before_mutated`，避免算子原地写坏数据后再把“坏输出”误当“原输入就坏”。
2. 执行 `result = func(...)` 后，从 `_ACTIVE_ROWS.get()` 取得已发布的 `(R, C)`。Dispatch 特例又从 `result[3]` 读取专家计数，检查最小值非负及总和不超容量，并为**这一次 Dispatch 输出检查**设置局部 `active_rows`。这个局部赋值并不会替模型把上下文持续发布给后续 GMM，所以前面的模型 `with trace_valid_rows(...)` 仍不可省略。
3. `row_limit` 对“有第一维，且第一维等于容量 C”的所有 Tensor 返回 R。**这是缺陷所在**：它不区分专家行、请求行或权重行。当 Combine 请求输出也有 C 行时，真实异常可能落在未扫描的 `R:C`，使后面的早返回跳过报告；同形状权重/metadata 也没有受到语义保护。
4. 输出检查只覆盖 `_OUTPUT_DTYPES` 允许的 dtype；可写参数若没有作为显式返回值出现，也会作为输出补进检查列表。纯分配器、`record_stream` 和未引入新值的共享存储 view 有明确透传路径，避免扫描未初始化分配或把生命周期管理当模型计算。
5. 只有被扫描的输出范围发现异常时，才检查普通非可写输入；这里同样调用有缺陷的 `row_limit(tensor)`。真正的 packed buffer 会被裁成前缀，但同形状的其他输入也可能被误裁剪，造成“输入正常”的错误归因。可写输入复用运算前保存的计数，不能在被改写之后重新假装获取旧输入。

**历史实现的可写输入预检查还有独立问题：调用 `_bad_counts(tensor)` 时没有传 `row_limit`。** 普通输入/输出路径只是对碰巧匹配容量的张量做了前缀扫描，并不保证扫描范围正确；可写输入路径则没有沿用这个前缀，可能再次把 packed 专家尾部计入。两者都需要按真实参数角色核对，不能推广为对任意原地或 `out=` 写入的 padding 保护；超大可写输入仍必须保留 `unchecked`。

历史实现的完整启用上下文如下。它同时设置 `_ACTIVE_TRACE` 和进入 `with trace` 安装 `TorchDispatchMode`，退出时恢复原上下文。这说明诊断如何接线，不表示 shape 裁剪缺陷已被解决。

```python
@contextlib.contextmanager
def trace_eager_decode(enabled, phase, step):
    if enabled:
        trace = EagerNanTrace(phase, step)
        token = _ACTIVE_TRACE.set(trace)
        try:
            with trace:
                yield
        finally:
            _ACTIVE_TRACE.reset(token)
    else:
        yield
```

下列是历史模型在 Dispatch 返回之后的完整 routed 计算作用域，变量由原有路由、通信和 shared-expert 逻辑准备；它展示上下文的实际覆盖范围，不是推荐接法。**该范围不仅覆盖 Combine 专家输入，也覆盖其请求输出和 shared 分支；没有角色绑定的 shape 裁剪不能在这里统一套用。** 把 Combine 放进或移出作用域，都不能单独解决“输入需要 R、输出需要 N”的区别。

```python
with trace_valid_rows(expert_token_num, expand_x.shape[0]):
    if self.shared_experts is not None:
        wait_event(switch, events, 2, self.exe_mode)

    routed_gate_up = self.experts.gmm1(
        expand_x, expert_token_num, pertoken_scale=dynamic_scale
    )

    # Shared down/reduce-scatter overlaps routed activation and GMM2.
    if self.shared_experts is not None:
        record_event(switch, events, 3, self.exe_mode)
        with npu_stream_switch(switch, shared_stream, exe_mode=self.exe_mode):
            wait_event(switch, events, 3, self.exe_mode)
            shared_states = self.shared_experts.project_down(shared_states)
            shared_output = self.shared_experts.reduce_scatter(shared_states)
            record_event(switch, events, 4, self.exe_mode)

    routed_activated, routed_scale = self.experts.activate_and_quant(
        routed_gate_up, expert_token_num
    )
    expert_output = self.experts.gmm2(
        routed_activated, expert_token_num, pertoken_scale=routed_scale
    )

    if shared_output is not None:
        wait_event(switch, events, 4, self.exe_mode)
    routed_output = self._combine_split_moe_decode(
        expert_output,
        ids,
        expand_idx,
        ep_recv_counts,
        tp_recv_counts,
        topk_weight,
    )
```

此处模型作用域提供计数，历史 dispatcher 仅按容量匹配决定切片，因此会发生本文的漏报。算子的执行结果仍按原样返回；“不清零原数据”只能保留现场，不能证明检查范围正确。修正时应删除通用 shape 推断，按已核对的算子参数/返回项或模型边界传递各自范围；别名、view、原地写入的角色传播若尚未实现，就不能声称任意算子均受保护。

### 显式区分 Combine 输入与输出的边界示例

下面是用于说明修正方向和执行 CPU 回归的补充示例，**没有替换上面的历史 dispatcher，也未接入模型仓**。调用方必须已经确认 `expert_input` 是 packed 专家输入，且 Combine 不会原地改写它；`request_rows` 只能来自请求布局自己的有效前缀契约，不能直接复用专家 R。未提供该请求契约时，扫描请求输出的全部行。容量匹配只是对已确认角色做一致性检查。

`other_float_inputs` 显式列出要参与这个局部检查的权重、shared 等张量，按全范围扫描，不因 shape 碰巧等于 C 而裁剪。没有列出的输入仍未检查；返回有限计数不构成所有模型输入正常的结论。此示例仅检查已取得的输入/输出边界，不是通用 `TorchDispatchMode`，也不替代原报告器、dtype 兼容处理与原地算子预检查。

```python
def check_combine_boundary(expert_input, request_output, *, expert_rows,
                           expert_capacity, request_rows=None,
                           other_float_inputs=()):
    if expert_input.ndim == 0 or expert_input.shape[0] != expert_capacity:
        raise ValueError("expert input capacity mismatch")
    if not 0 <= expert_rows <= expert_capacity:
        raise ValueError("invalid expert row range")
    if request_output.ndim == 0:
        raise ValueError("request output must have a row dimension")
    if request_rows is None:
        request_rows = request_output.shape[0]
    if not 0 <= request_rows <= request_output.shape[0]:
        raise ValueError("invalid request row range")

    # These roles are explicit at the model boundary; shape does not assign them.
    inputs = {"expert_input": _bad_counts(expert_input, expert_rows)}
    for name, tensor in other_float_inputs:
        if name in inputs:
            raise ValueError("duplicate input role")
        inputs[name] = _bad_counts(tensor)
    output = _bad_counts(request_output, request_rows)
    if output is None or any(counts is None for counts in inputs.values()):
        raise RuntimeError("KIMI_COMBINE_UNCHECKED")
    if any(output) or any(any(counts) for counts in inputs.values()):
        raise RuntimeError(
            f"KIMI_COMBINE_NONFINITE inputs={inputs} request_output={output}"
        )
    return inputs, output
```

## 报告字段与归因

| 字段 | 阅读方式 |
|---|---|
| `valid_rows` | 历史上下文的专家有效行数 R；应与 Dispatch 的实际 count 总和一致，不表示 Combine 的有效请求行数 N |
| `checked_inputs` | 已扫描输入范围的名称、shape、dtype 和非有限值计数；须再确认该范围与张量角色相符，不能把错误裁剪后的零计数当作完整输入正常 |
| `bad_outputs` | 被扫描范围内含 NaN/Inf 的输出，不代表未扫描 buffer 的状态 |
| `unchecked_float_inputs` | 无法检查的浮点或 uint8 输入；非空时不能声称所有输入正常 |
| `classification` | 历史代码在扫描输入无异常且无未检查输入时写入 `input_ok_output_nan` / `input_ok_output_inf`；使用该归因前还须确认范围正确，否则同形状输入的误裁剪会造成假“input_ok” |

原地算子的可写输入需要在运算前检查；很大的常驻可变 cache 若因代价未预扫，仍应保留 `unchecked`。输出异常且已检查 activation 正常，也不能排除未检查的 scale、权重、历史状态或融合内部问题。

对于历史版本，“未报警”和空的 `unchecked_float_inputs` 都不能排除本卡已复现的漏报。上面的边界示例使用独立的异常摘要，没有改变历史 JSON 报告格式。

## 验证信号

本轮在 CPU 上提取并执行了本卡保留的 `trace_valid_rows`、`_bad_counts` 和完整 dispatcher 方法，辅以 Tensor 遍历和报告捕获 fixture，确认了两个缺陷：四行全有效的 Combine 输出 `[1, 1, 1, NaN]` 在 `R=2、C=4` 时无报警；同形状权重第四行的 NaN 在异常输出归因中被裁掉。执行设备为 CPU，报告器使用捕获桩，不运行真实 Combine、MC2 或专家 kernel。

没有运行原上游测试文件，也没有进行 NPU 推理。“Combine 包含在上下文内”和“诊断不清零 buffer”只说明接线与数据未改写，不能证明范围正确或部署通过。下面先保留历史单行输出 fixture，随后给出本轮已执行的八个显式边界回归。

下面的历史 CPU fixture 防止把 padding 异常错归到 Combine 输入。它依赖测试文件中的 `torch`、`pytest`、`SimpleNamespace`、`trace_eager_decode`、`trace_valid_rows`、`eager_nan_trace` 和解析 JSON 的 `_report`；返回的报告结构对应上表。它的输出只有一行，首维不等于 C，**没有覆盖请求输出恰好等于专家容量的漏报**；此原始 fixture 在本轮仍只是已阅读的断言定义。

```python
def test_combine_ignores_padded_input_when_output_is_nan():
    class Combine:
        _schema = SimpleNamespace(is_mutable=False)

        def __str__(self):
            return "npu.npu_moe_distribute_combine_v2.default"

        def __call__(self, value):
            return torch.tensor([[float("nan")]], dtype=torch.bfloat16)

    expert_output = torch.tensor([[1.0], [1.0], [float("nan")], [float("nan")]],
                                 dtype=torch.bfloat16)
    with pytest.raises(RuntimeError, match="KIMI_EAGER_NAN") as error:
        with trace_eager_decode(True, "target.decode", 0):
            with trace_valid_rows(torch.tensor([1, 1]), capacity=4):
                eager_nan_trace._ACTIVE_TRACE.get().__torch_dispatch__(
                    Combine(), (), (expert_output,)
                )
    report = _report(error)
    assert report["operator"] == "npu.npu_moe_distribute_combine_v2.default"
    assert report["valid_rows"] == 2
    assert report["classification"] == "input_ok_output_nan"
    assert report["checked_inputs"][0]["nan"] == 0
```

以下回归依赖前文的 `_bad_counts`、`check_combine_boundary` 和 CPU PyTorch/pytest，不需要真实 NPU 算子。参数化展开共八项，本轮全部通过。它们验证的是显式边界示例；没有把历史 dispatcher 的漏报变成通过，不能据此声称历史实现已修复。移植到模型探针时，必须让真实 Combine 的调用路径也通过同样断言。

```python
import pytest
import torch


@pytest.mark.parametrize("tail", [float("nan"), float("inf")])
def test_boundary_ignores_only_expert_tail(tail):
    expert = torch.tensor([[1.], [1.], [tail], [tail]], dtype=torch.bfloat16)
    output = torch.ones((4, 1), dtype=torch.bfloat16)
    before = expert.clone()
    inputs, counts = check_combine_boundary(
        expert, output, expert_rows=2, expert_capacity=4
    )
    assert inputs["expert_input"] == (0, 0) and counts == (0, 0)
    torch.testing.assert_close(expert, before, equal_nan=True)


@pytest.mark.parametrize("bad, expected", [
    (float("nan"), "request_output=(1, 0)"),
    (float("inf"), "request_output=(0, 1)"),
])
def test_boundary_reports_valid_output_even_when_rows_equal_capacity(bad, expected):
    expert = torch.tensor([[1.], [1.], [float("nan")], [float("nan")]],
                          dtype=torch.bfloat16)
    # All four request rows are valid; R=2 must not hide row four.
    output = torch.tensor([[1.], [1.], [1.], [bad]], dtype=torch.bfloat16)
    with pytest.raises(RuntimeError, match="KIMI_COMBINE_NONFINITE") as error:
        check_combine_boundary(expert, output, expert_rows=2, expert_capacity=4)
    assert "'expert_input': (0, 0)" in str(error.value)
    assert expected in str(error.value)


@pytest.mark.parametrize("role", ["weight", "shared"])
def test_boundary_same_shape_other_input_is_not_cropped(role):
    expert = torch.ones((4, 1), dtype=torch.bfloat16)
    output = torch.ones((4, 1), dtype=torch.bfloat16)
    other = torch.tensor([[1.], [1.], [1.], [float("nan")]], dtype=torch.bfloat16)
    with pytest.raises(RuntimeError, match="KIMI_COMBINE_NONFINITE") as error:
        check_combine_boundary(
            expert, output, expert_rows=2, expert_capacity=4,
            other_float_inputs=((role, other),),
        )
    assert f"'{role}': (1, 0)" in str(error.value)


def test_boundary_request_padding_uses_its_own_valid_prefix():
    expert = torch.ones((4, 1), dtype=torch.bfloat16)
    output = torch.tensor([[1.], [1.], [1.], [1.], [float("nan")], [float("nan")]],
                          dtype=torch.bfloat16)
    # This fixture separately guarantees N=4 request rows, independent of R=2.
    _, counts = check_combine_boundary(
        expert, output, expert_rows=2, expert_capacity=4, request_rows=4
    )
    assert counts == (0, 0)
    output[3, 0] = float("nan")
    with pytest.raises(RuntimeError, match="KIMI_COMBINE_NONFINITE"):
        check_combine_boundary(
            expert, output, expert_rows=2, expert_capacity=4, request_rows=4
        )


def test_boundary_zero_expert_rows_does_not_skip_request_output():
    expert = torch.full((4, 1), float("nan"), dtype=torch.bfloat16)
    output = torch.tensor([[1.], [1.], [1.], [float("nan")]], dtype=torch.bfloat16)
    with pytest.raises(RuntimeError, match="KIMI_COMBINE_NONFINITE"):
        check_combine_boundary(expert, output, expert_rows=0, expert_capacity=4)
```

## 部署验收与预期结果

应在角色绑定已修正的实际探针中覆盖以下输入，固定模型配置并保存报告；历史 shape 裁剪版无法满足第 4、5 项，不能作为验收通过版本：

1. 有效行全有限、仅尾部放 NaN/Inf：Dispatch、GMM 与 activation 的探针不应报警；真实尾部保持原值，不能通过清零获得“通过”。
2. 把异常移到有效前缀：必须报告有效行异常，`nan`/`inf` 数量与注入位置一致，不能因屏蔽尾部漏检。
3. 有效 Combine 输入有限、尾部非有限、Combine 输出非有限：报告中有效输入计数仍为零；无其他未检查输入时应保留 `input_ok_output_nan` 分类。
4. `R=2、C=4`，Combine 的四行请求输出全部有效，第四行注入 NaN/Inf：必须报警，不能裁成前两行；R 为零时也不能跳过有效请求输出。
5. 同形状的权重、shared 分支张量在专家 R 之外、其自身有效范围内含 NaN：必须检出，不能被误标为输入正常。请求本身有 padding 时，须另行验证其有效范围 N，不能沿用专家计数。

随后用真实路由、权重和原精度标准回归。CPU mock 不运行 MC2/专家 kernel，只能验证 wrapper 的范围和归因；真实 NPU 还要确认该算子版本仍使用相同返回签名与 packed-prefix 约定。

## 坏实践、回退与失效边界

- 不把“buffer 中有 NaN”直接等同“有效专家 token 有 NaN”，不把未写入尾部当作模型计算结果。
- 不为消除报警把整个 buffer 清零、放宽容差或跳过有效行；这些动作改变问题现场。
- 不对累计计数、带洞布局、非 packed buffer 使用 `sum(counts)` 前缀口径。若计数合法而实际有效行并非前缀，优先重查 Dispatch/GMM 接口与布局约定。
- 不以 `shape[0] == C` 代替 packed 专家行语义，不把同一 `_ACTIVE_ROWS` 作用域解释成所有输入/输出共享 R。历史实现的同形状漏报已经复现；部署前须修正消费者的角色绑定并跑实际调用链回归。
- 回退可以关闭诊断并恢复原推理路径；这只移除诊断开销，不能视为 NaN 已修复。
- 未决项：目标 NPU 的实际路由签名、有效行映射与整网非有限问题仍待核实。scale 或 cache 未检查时，根因范围必须继续保留这些输入。
