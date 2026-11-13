---
{
  "type": "Runbook",
  "title": "RUNTIME_GetInputData 调用语义错位：4 实参不触发尾随逗号错误但 dtype 拿到 offset 值，修复方向删 devSlot 并加 ##__VA_ARGS__ 兜底",
  "description": "PyPTO 设备侧代码生成报 aikernel_runtime.h:122 expected primary-expression before ')' token。结论原文（c2-3）：4 实参调用不触发尾随逗号错误但语义仍是错的（dtype 拿到 offset 值）；devSlot 疑为未完工的 host/device slot 分流特性，若不需要分流可删掉 devSlot、宏改为 (hostSlot, dtype, ...) 并加 ##__VA_ARGS__ 兜底空参。",
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
# RUNTIME_GetInputData 调用语义错位：4 实参不触发尾随逗号错误但 dtype 拿到 offset 值，修复方向删 devSlot 并加 ##__VA_ARGS__ 兜底


## 适用场景

PyPTO 设备侧代码生成报 aikernel_runtime.h:122 expected primary-expression before ')' token。来源结论：4 实参调用不触发尾随逗号错误但语义仍是错的（dtype 拿到 offset 值）；devSlot 疑为未完工的 host/device slot 分流特性，若不需要分流可删掉 devSlot、宏改为 (hostSlot, dtype, ...) 并加 ##__VA_ARGS__ 兜底空参。

## 触发与观测


源码核对发现 RUNTIME_GetInputData 的调用方实参约定与带 devSlot 的宏定义不一致。三实参/四实参展开表现可能不同，不能以某个四参调用没有尾逗号编译错误证明其 dtype/offset 语义正确。

## 探针与操作


机制片段：原文：

```
#define RUNTIME_GetInputData(hostSlot, dtype, ...) \
       RuntimeGetInputData<dtype>(&(RuntimeGetStartArgs())->devTensorList[(hostSlot)], ##__VA_ARGS__)
```

## 机制与判别


来源结论：

4 实参调用（如 RUNTIME_GetInputData(ARG_block_table, RUNTIME_int32_t, VALUE_loop_idx_b_idx, VALUE_loop_idx_bn_idx_3)）不触发尾随逗号错误但语义仍是错的（dtype 拿到 offset 值）；devSlot 疑为未完工的 host/device slot 分流特性，若不需要分流可删掉 devSlot、宏改为 (hostSlot, dtype, ...) 并加 ##__VA_ARGS__ 兜底空参。

## 验证信号

本卡验证信号并入『机制与判别』节：来源结论：的判别与登记机制片段：（修复后宏定义，客观观测）。

## 适用与失效边界

适用：PyPTO 设备侧代码生成报 aikernel_runtime.h:122 expected primary-expression before ')' token、且调用 RUNTIME_GetInputData 的场景。失效边界：结论为静态读码范围（source_read），未在源码仓实际应用修复并重跑单测；4 实参调用不报错但语义错位的问题同样存在。validation_scope: source_read。
