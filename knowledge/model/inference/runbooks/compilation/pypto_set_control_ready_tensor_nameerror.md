---
{
  "type": "Runbook",
  "title": "PyPTO set_control_ready_tensor 形参名笔误（cpu_tensor 未定义）触发 DispatchError",
  "description": "运行 deepseekv32_lightning_indexer_quant 时，PIL dispatcher 在编译期执行 set_control_ready_tensor 函数体触发 NameError，被包装为 FeError: DispatchError: name 'cpu_tensor' is not defined。根因是 pypto/op/other.py:418 引用了不存在的 cpu_tensor（形参名为 host_tensor），源码仓与 site-packages 两份文件同样存在；修复时还需处理附带逻辑缺陷（tensor_none 创建后未使用）。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# PyPTO set_control_ready_tensor 形参名笔误（cpu_tensor 未定义）触发 DispatchError


## 适用场景

运行 deepseekv32_lightning_indexer_quant 时，PIL dispatcher 在编译期执行 set_control_ready_tensor 函数体触发 NameError，被包装为 FeError: DispatchError: name 'cpu_tensor' is not defined。根因是 pypto/op/other.py:418 引用了不存在的 cpu_tensor（形参名为 host_tensor），源码仓与 site-packages 两份文件同样存在；修复时还需处理附带逻辑缺陷（tensor_none 创建后未使用）。

## 触发与观测


源码与安装包的 `set_control_ready_tensor(host_tensor, npu_tensor)` 函数体引用了未定义的 `cpu_tensor`。来源读回显示形参为 host_tensor、条件却为 `if cpu_tensor is None:`。这是命名缺陷的源码证据；没有修后设备运行结果。

## 探针与操作


机制片段：原文：

```
416: @op_wrapper
417: def set_control_ready_tensor(host_tensor: Tensor, npu_tensor: Tensor) -> Tensor:
418:     if cpu_tensor is None:
419:         tensor_none = pypto.Tensor(npu_tensor.dtype, npu_tensor.shape, "tensor_none")
420:     if npu_tensor is None:
421:         raise PyptoError(0xF00001, TypeError("the second input must not be None"))
422:     return pypto_impl.SetControlReadyTensor(host_tensor, npu_tensor)

(End of file - total 422 lines)
```

## 机制与判别

来源结论：

pypto/op/other.py:417-422 的 set_control_ready_tensor 形参名为 host_tensor，但函数体第 418 行引用未定义名 cpu_tensor；源码仓（python/pypto/op/other.py）与已安装 site-packages 两份文件同样存在该笔误。


## 验证信号

本卡验证信号并入『探针与操作』『机制与判别』节：所示机制片段为 other.py:417-422 源码逐字读回（客观观测），来源结论：据此判别笔误在源码仓与 site-packages 两份文件同样存在。

## 适用与失效边界

适用：PyPTO 算子调用 set_control_ready_tensor 报 DispatchError: name 'cpu_tensor' is not defined 的场景。失效边界：仅覆盖 other.py:417-422 这一处笔误；若同类 DispatchError 出现在其他 op_wrapper 函数，需按本探针方法另行定位（读源码对照形参名）。validation_scope: source_read。
