---
{
  "type": "Runbook",
  "title": "NPU 移植中 npu_fast_gelu 不支持 alpha：包装函数带 alpha 形参会静默丢弃非 1.702 值",
  "description": "Ascend NPU 上以 torch_npu 融合算子实现模型 FFN 激活（本例 daVinci-MagiHuman DiT 的 `gelu7_layers` 混合激活，dit_module.py）时适用。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# NPU 移植中 npu_fast_gelu 不支持 alpha：包装函数带 alpha 形参会静默丢弃非 1.702 值

## 适用场景

Ascend NPU 上以 torch_npu 融合算子实现模型 FFN 激活（本例 daVinci-MagiHuman DiT 的 `gelu7_layers` 混合激活，dit_module.py）时适用。当激活封装函数在签名里暴露 `alpha` 形参（如 `gelu7(x, alpha=1.702, ...)`）但底层调用 `torch_npu.npu_fast_gelu` 时，需要判断该参数是否真实生效。

## 触发与观测

- 触发（source 0 seq 134，用户检视意见）：`dit_module.py` 被检出 "gelu7 未使用 alpha 参数"，要求确认。
- 源码观测（source 0 seq 141/145，grep + 文件读取）：`gelu7`（dit_module.py:58）定义 `alpha: float = 1.702` 但函数体只做 `x.clamp_(max=limit)` 与 `torch_npu.npu_fast_gelu(x)`；同文件 `swiglu7`（dit_module.py:54）把 `alpha` 显式传给 `torch_npu.npu_clipped_swiglu(x_f32, alpha=alpha, limit=limit, bias=1.0, interleaved=True)`。
- 调用点观测（source 0 seq 172/197）：`create_activation_func` 返回函数引用，唯一调用点 dit_module.py:755 `self.activation_func(normed)` 只传位置参数 `x`，无任何调用方传自定义 alpha。

## 探针与操作

torch_npu 本地 docstring 查询（model-infer-fusion skill 的 `torch_npu_query.py`）：

```
python3 .agents/skills/model-infer-fusion/scripts/torch_npu_query.py show npu_fast_gelu
python3 .agents/skills/model-infer-fusion/scripts/torch_npu_query.py search gelu
python3 .agents/skills/model-infer-fusion/scripts/torch_npu_query.py search clipped
```

## 机制与判别

- 接口约束（source 0 seq 158，docstring 逐字）：`torch_npu.npu_fast_gelu(Tensor input) -> Tensor` 只接收 input；A2/A3 系列公式为 `x / (1+e^(-1.702*x))`，系数 1.702 硬编码在算子内部，无 alpha 入参。Atlas 训练/推理系列（公式1）同样是固定系数形式。
- 判别：`alpha` 在 `gelu7` 是死参数而非"遗漏使用"——API 根本不接受它；与 `swiglu7` 形成对照（后者 alpha 有效）。全仓搜索不存在 `npu_clipped_gelu`（只有 `npu_clipped_swiglu`），即没有可接收 alpha 的 clipped GELU 融合算子可替换。
- 风险：默认 1.702 恰好等于算子内部硬编码值，当前行为正确；但保留 `alpha` 形参会造成"传入即生效"的假象，传入非 1.702 值会被静默忽略，构成潜在精度陷阱。

## 验证信号

- 修复 = 从 `gelu7` 签名删除 `alpha`（source 0 seq 183，before/after 全文见「探针与操作」小节；函数体逐行不变）。
- 验证层次：调用点扫描（仅定义处无外部 `gelu7(` 调用，source 0 seq 197）+ `py_compile` 语法通过（source 0 seq 188）。无设备数值回归（调用点本就不传 alpha，行为零变化）。

## 适用与失效边界

- 结论限于 torch_npu `npu_fast_gelu` 当前 docstring 声明的签名与公式（A2/A3/训练推理系列）；若后续 CANN 版本提供带 alpha 的变体需复核。
- "删除死参数"是防误导性 API 的卫生修复；若确需可变 alpha 的 GELU，须退回非融合实现或自行组合算子，本轨迹未验证该路径的精度/性能。

## 附：断言存档

- torch_npu.npu_fast_gelu 接口签名只接收 input（torch_npu.npu_fast_gelu(Tensor input) -> Tensor），A2/A3 系列计算公式为 x/(1+e^(-1.702*x))，系数 1.702 硬编码在算子内部、无法经 API 定制；因此 daVinci-MagiHuman dit_module.py 的 gelu7(x, alpha=1.702, limit=7.0, ...) 中 alpha 是死参数——无法传给底层算子，与同文件 swiglu7（alpha 实际传给 npu_clipped_swiglu(alpha=alpha)）形成判别对照；默认值 1.702 恰与算子内硬编码一致故当前行为正确，但保留该形参会使传入的非 1.702 值被静默忽略，构成精度陷阱。修复为从签名删除 alpha（唯一调用点 dit_module.py:755 只传 x，行为零变化），py_compile 通过。

```text
def gelu7(x, alpha: float = 1.702, limit: float = 7.0, out_dtype: Optional[torch.dtype] = None):
    out_dtype = x.dtype if out_dtype is None else out_dtype
    x = x.to(torch.float32)
    x.clamp_(max=limit)
    x = torch_npu.npu_fast_gelu(x)
    return x.to(out_dtype)
```
