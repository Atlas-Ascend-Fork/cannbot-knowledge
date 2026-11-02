---
type: Runbook
title: Flash MLA 加 NaN 探针后 FakeTensor 报 npu/meta 冲突：检查探针放置位置
description: 把 Flash MLA 输出探针移到模型既有设备归一之后、Value Projection 之前，避免 meta fake 输出与 NPU
  统计 buffer 混算；CPU FakeTensor 重现不替代 NPU 图验证。
tags:
- task.debugging
- topic.compilation
- topic.graph_execution
- topic.attention
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
      execution_mode:
      - npugraph_ex
      phase:
      - decode
---

# Flash MLA 加 NaN 探针后 FakeTensor 报 npu/meta 冲突：检查探针放置位置

## 现象

Kimi K3 的 MLA Decode 原本走 Flash MLA 图路径，添加 `flash.output` 非有限值检查后，Dynamo/FakeTensor 在 `aten.bitwise_and.Tensor` 一类布尔合并处报 `Unhandled FakeTensor Device Propagation ... npu:0, meta`。失败发生在图编译设备推导期间；这里没有已经执行成功的 NPU 扫描，也没有真实 NaN 计数，所以不能将它归类为模型精度异常。

旧检查点位于 `_flash_mla_attention` 刚拿到 Flash 返回值时。某些 Flash MLA fake 实现把输出标为 `meta`；而 `FinitePoint` 的统计状态预分配在 NPU。探针试图把 meta 输出导出的“是否异常”布尔值与 NPU 上的首次异常状态合并，导致设备推导冲突。

## 适用场景与相关入口

- 目标范围：950PR/DT 的 Kimi K3 `npugraph_ex` Decode，`KimiMLAAttention._forward_decode_flash` → `_flash_mla_attention` → Flash MLA → Value Projection；本轮未执行实际 NPU capture/replay。
- 前提：部署代码已经存在 `output.to(device=self.kv_b_proj_decode_w_v.device)` 的输出设备归一。修正只移动探针，不新增模型计算或换后端。
- 需要同时核对 Flash op 的 fake/schema、真实返回 dtype/device、统计 buffer 的 device，以及 Value Projection 的权重 device；不能只凭错误串添加任意 `.to()`。
- 如果部署版本没有这段已有归一，或错误出在另一个 custom op 的 fake/schema，本卡不能直接给出相同修复。具体 CANN、torch_npu 和 Flash 包组合仍需现场确认。

## 调用链与根因

1. `_forward_decode_flash` 根据 forward metadata 取得 block table、KV 长度和 query 前缀，调用 MLA Prolog 得到 query，并处理既有异步 metadata 事件。
2. `_flash_mla_attention` 调用 Flash MLA，返回尚未统一设备标记的输出。真实执行的输出语义与 tracing 时的 fake 输出设备是两件事。
3. 旧探针在此函数内部检查 `flash.output`，早于外层已有的设备归一。
4. 探针的首次异常判断含 `(self.state[1] == 0) & ((nan_count + inf_count) > 0)`。左侧状态属于加速器，右侧如果来自 meta fake Tensor，二元合并就不能推导成一致设备。
5. 修正把同一个 `flash.output` 检查放到已有归一之后、`npu_transpose_batchmatmul` 的 Value Projection 之前。观测边界仍是 Flash 输出，不变成投影后的另一个位置。

这条因果链解释的是**插桩引起的编译兼容性**。它不能证明 Flash 数值正确，也不能证明某个 meta 输出在运行时真的需要搬运。

## 完整处理方法

先删除 `_flash_mla_attention` 返回前的旧 `flash.output` 检查，保持该方法原有 Flash 调用及返回。外层 Decode 方法采用下面已有完整实现。它依赖 `KimiMLAAttention` 原属性、`ForwardMetaData`、`torch`、`torch_npu`、`wait_event` 和 `trace_tensor`；不是可脱离模型单独运行的脚本。

```python
def _forward_decode_flash(
    self,
    hidden_states: torch.Tensor,
    forward_metadata: ForwardMetaData,
    layer_cache: dict,
    metadata_events=None,
) -> torch.Tensor:
    """Run merged-cache MLA Prolog followed by Flash MLA attention."""
    tokens = hidden_states.shape[0]
    block_table = forward_metadata["block_table"][self.attn_type]
    cache_seqlens = forward_metadata["actual_seq_lengths_kv"]
    # Flash MLA expects the B+1 prefix-sum form with a leading zero.  The
    # legacy actual_seq_lengths_cu_q field stores only segment ends.
    cu_seqlens_q = forward_metadata["query_start_loc"]
    q_len = tokens // block_table.shape[0]
    q, *_ = self._mla_prolog(
        hidden_states,
        layer_cache["kv_cache"],
        forward_metadata["slot_mapping"][self.attn_type],
        decode=True,
        kr_cache=layer_cache["kr_cache"],
    )
    if forward_metadata.get("flash_mla_metadata_async", False):
        wait_event(
            self.enable_multi_streams,
            metadata_events,
            1,
            self.exe_mode,
        )
    output = self._flash_mla_attention(
        q,
        layer_cache["kv_cache"],
        block_table,
        cache_seqlens,
        cu_seqlens_q,
        q_len,
        forward_metadata.get("flash_attention_mask"),
        forward_metadata.get("flash_mla_metadata"),
    )
    output = output.to(device=self.kv_b_proj_decode_w_v.device)
    # Some Flash MLA fake implementations expose a meta-device output.
    # Use the existing device normalization before combining its finite
    # counts with the NPU-resident diagnostic state during graph tracing.
    trace_tensor(self, "flash.output", output)
    output = torch_npu.npu_transpose_batchmatmul(
        output,
        self.kv_b_proj_decode_w_v,
        bias=None,
        scale=None,
        perm_x1=(1, 0, 2),
        perm_x2=(0, 1, 2),
        perm_y=(1, 0, 2),
    )
    return output.reshape(tokens, self.total_num_heads * self.v_head_dim)
```

只调整检查点时应保持这四个不变量：Prolog 仍按原顺序写 cache；metadata wait 仍在使用 metadata 前；设备归一仍采用原有权重 device；检查仍在 Value Projection 前。若随手改动这些部分，即使编译错误消失，也无法把行为变化单独归因于探针位置。

## 判别与复核步骤

1. 在失败栈确认消费 meta 的确切算子；将 Flash fake 返回值、统计 buffer 和投影权重的 device 放在同一调用链上核对。
2. 搜索两个实际 MLA 方法，确认旧检查点已经移除，新的检查点只出现一次，且位于原归一后。只新增新检查但留下旧检查，会继续触发原错误。
3. 通过 meta-returning fake Flash 复现旧设备合并问题；新位置必须先对齐到权重 device，再调用诊断，最后执行投影。
4. 若归一后仍失败，重新检查部署版本的 fake/schema 和实际图，而不是继续插入转设备、切换 eager 或删除 mutation 声明。

## 验证信号

本次核对了上述实际方法和下列已有完整回归定义，没有执行此测试，也没有运行 NPU 图。回归从模型文件 AST 提取两个真实方法，使用 meta-returning Flash fake 和逻辑加速器 FakeTensor：它验证原位置的混合设备二元算子会失败、新位置的诊断在投影前观察到匹配 device。

测试中的 `cuda:0` 只是 FakeTensor 的逻辑设备，不申请 CUDA 硬件；不能把它记成 CUDA/NPU 实机通过。该完整 fixture 依赖同一测试模块中的 `ast`、`Path`、`torch`、`pytest` 和 monkeypatch fixture，实际方法还依赖配套调用约定。

```python
def test_flash_meta_output_is_aligned_before_diagnostic_state(monkeypatch):
    """Exercise the real MLA methods with a meta-returning fake Flash kernel.

    CUDA here is only a logical FakeTensor device; no CUDA runtime is used.
    It reproduces the same accelerator/meta propagation error as npu/meta.
    """
    from types import SimpleNamespace
    from torch._subclasses.fake_tensor import FakeTensorMode

    source = Path(__file__).parents[1] / "models/modeling_kimi_k3.py"
    tree = ast.parse(source.read_text())
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == "KimiMLAAttention")
    names = {"_flash_mla_attention", "_forward_decode_flash"}
    methods = [node for node in cls.body
               if isinstance(node, ast.FunctionDef) and node.name in names]
    fixture = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        ast.ClassDef(name="Attention", bases=[], keywords=[], body=methods, decorator_list=[]),
    ], type_ignores=[])
    ast.fix_missing_locations(fixture)
    observed = []

    def diagnostic(module, stage, value):
        # The failing binary op from FinitePoint, without indexing a simulated
        # accelerator buffer (that would require a compiled accelerator guard).
        first = torch.empty((), device=module.kv_b_proj_decode_w_v.device, dtype=torch.bool)
        bad = (torch.isnan(value).sum() + torch.isinf(value).sum()) > 0
        first & bad
        observed.append((stage, value.device))

    def flash(q, *args, **kwargs):
        return torch.empty((q.shape[0], q.shape[1], 512), device="meta"), None

    def projection(value, weight, **kwargs):
        assert observed[-1] == ("flash.output", weight.device)
        assert value.device == weight.device
        return value.new_empty((value.shape[0], 1, 2))

    monkeypatch.setattr(torch.ops.cann_ops_transformer, "flash_mla_with_kvcache", flash, raising=False)
    namespace = {"torch": torch, "trace_tensor": diagnostic,
                 "torch_npu": SimpleNamespace(npu_transpose_batchmatmul=projection)}
    exec(compile(fixture, str(source), "exec"), namespace)
    model = namespace["Attention"]()
    model.attn_type = "MLA"
    model.kv_lora_rank, model.qk_rope_head_dim = 512, 64
    model.scaling = 1.0
    model.total_num_heads, model.v_head_dim = 1, 2
    model._pa_nz_cache_view = lambda cache, width: cache
    model._mla_prolog = lambda hidden, *args, **kwargs: (hidden.new_empty((2, 1, 576)),)

    with FakeTensorMode():
        model.kv_b_proj_decode_w_v = torch.empty((1, 512, 2), device="cuda:0")
        hidden = torch.empty((2, 4), device="cuda:0")
        cache = hidden.new_empty((1, 128, 1, 576))
        # Prove the old placement fails on the same mixed-device binary op.
        with pytest.raises(RuntimeError, match="two different devices.*meta"):
            diagnostic(model, "flash.output", torch.empty((2, 1, 512), device="meta"))
        result = model._forward_decode_flash(hidden, {
            "block_table": {"MLA": hidden.new_empty((2, 1), dtype=torch.int32)},
            "slot_mapping": {"MLA": hidden.new_empty((2,), dtype=torch.int32)},
            "actual_seq_lengths_kv": hidden.new_empty((2,), dtype=torch.int32),
            "query_start_loc": hidden.new_empty((3,), dtype=torch.int32),
            "flash_mla_metadata": hidden.new_empty((2, 4), dtype=torch.int32),
        }, {"kv_cache": cache, "kr_cache": cache})
        assert result.device == hidden.device
        assert observed == [("prolog.query", hidden.device), ("flash.output", hidden.device)]
```

## 部署验收与预期结果

先在实际部署版本执行上面的回归，并确认它确实覆盖当前两个 MLA 方法；再使用原请求、权重与并行配置完成目标 NPU 的正常 capture 和后续多次 replay。应同时确认编译期设备冲突消失、输出及 cache 更新与未插桩基线一致、探针仍能检出受控异常，以及没有因额外搬运引入新的时序问题。

CPU/FakeTensor 只能证明设备传播与检查位置；真实 Flash kernel 的数学、PA_NZ cache 布局、NPU replay 稳定性和性能必须分别验收。当前缺这些修后实机记录，所以保留草稿。

## 设计决策、坏实践与回退

- 复用已有归一而移动观测点，是为了保留原模型数据路径和检查语义；不为探针随意增加 Host 读回、额外转换或新同步。
- 不把编译失败写成“检查到了 NaN”，不以关闭所有诊断、改为 eager 或放宽精度容差宣称问题已经修好。
- 不让检查点越过 Value Projection，否则“Flash 输出异常”与“投影后异常”的边界会混在一起。
- 回退可关闭诊断并恢复匹配图缓存，保留模型算子和状态更新；关闭探针后的成功只说明原路径能执行。
- 优先未决项：目标 Flash 包 fake/schema 与 NPU capture/replay 的真实行为仍需复现核实；若设备对齐后还失败，继续定位确切传播节点，不能套用通用 `.to()` 配方。

一般 custom op 的 converter/meta 一致性见 [converter 与 meta 正确性](../precision/custom_op_graph_lowering_converter_meta_correctness.md)。
