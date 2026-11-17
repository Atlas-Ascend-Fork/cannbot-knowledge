---
{
  "type": "Runbook",
  "title": "FXRT warm guard 恢复失败：区分可重建对象与不可序列化占位",
  "description": "宽泛的 pybind 替换规则可能把 guard 需要的类型变成 _Missing；区分白名单重建、允许舍弃与拒绝，并把 CPU reducer 测试限定在实际覆盖范围。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# FXRT warm guard 恢复失败：区分可重建对象与不可序列化占位

## 适用场景

FXRT guard 序列化/恢复与 vLLM 多 worker；记录中的 guard 实现绑定 torch 2.10.0+cpu。

## 触发与观测

warm 加载在 load_guards_state/pickle.loads 报 _Missing 缺少 moe_forward_shared；原规则按 pybind11_builtins 前缀统一替换。

## 探针与操作

检查失败对象的真实类型、模块、guard 引用及 reducer 安装顺序。对允许重建的类验证身份恢复，对禁止的类型验证明确拒绝；不能仅测试 pickle 能否返回。

引发过宽替换的旧 reducer（诊断反例）：

```python
def _reducer_pickling_safe(self, obj):
    """Replace known-unpicklable C extension objects with _Missing."""
    obj_type = type(obj)

    # 1. Exact zmq.Socket (module is zmq.sugar.socket, not "zmq")
    if zmq_socket_type is not None and obj_type is zmq_socket_type:
        return (_Missing, (
            f"Unpicklable {obj_type.__module__}.{obj_type.__qualname__} "
            f"pruned by sitecustomize",))

    # 2. pybind11_builtins (function records, etc.)
    if _is_unpicklable_pybind(obj_type):
        return (_Missing, (
            f"Unpicklable {obj_type.__module__}.{obj_type.__qualname__} "
            f"pruned by sitecustomize",))

    if original_override is not None:
        return original_override(self, obj)
    return NotImplemented

pickler.reducer_override = _reducer_pickling_safe
```

## 机制与判别

将一整类 C 扩展对象无差别替换为 _Missing 会破坏 guard 所需的属性访问。记录提出按可重建性分类处理；是否可以舍弃必须依据对象在 guard 中的实际用途，不能把某个测试白名单当作所有版本的通用策略。

## 验证信号

CPU 链测试输出包含 ProcessGroup/DispatchKey/FunctionSchema/Tag 身份恢复、已配置拒绝样例及 ALL CHAIN CHECKS DONE。这只覆盖所测 reducer 链，不等于多 worker cold→warm 设备链已通过。

## 适用与失效边界

升级 torch 后需重新审计对象类型、源码版本和安装顺序。下面保留的是引发问题的旧 reducer，用于识别宽泛替换，不是建议直接安装的修复；完整策略部署及端到端复验仍需单独完成。
