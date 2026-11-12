---
type: API
title: SGLang row_argmax的NaN与并列索引语义
description: 记录row_argmax的FP32二维输入、列连续约束、最小并列索引与首个NaN规则，以及Triton/独立Torch入口。
tags:
- task.implementation
- topic.compute.ordering
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/row_argmax.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/row_argmax.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
created_at: '2026-11-08T11:03:53Z'
updated_at: '2026-11-08T11:03:53Z'
platforms:
- a2
- a3
- '950'
---

# SGLang row_argmax的NaN与并列索引语义

## 签名与分发

```python
from sgl_kernel_npu.operators.sample import row_argmax
row_argmax(x, *, impl="auto")
```

`auto`与`triton`指向同一入口，独立reference为`torch_native`；TileLang/Ascend C未实现。文档声明arch22/arch35支持，对应A2/A3、950；注册存在不证明全部芯片已真机验证。

## 输入输出合同

`x`为NPU FP32二维 `[B,V]`，`V>0`、列stride=1；B可为0，行允许额外stride。结果是输入设备上新建的 `[B]` int64索引，输入不变。

语义对齐 `torch.argmax(x,dim=-1)`：并列最大取最小列索引；有NaN的行取第一个NaN。不能以普通有限值最大归约替代这两条规则。Triton采用分块行归约，Torch后端直接argmax。

## 验证方式和边界

分别调用Triton与独立Torch reference，覆盖空batch、单列、非连续行、并列与多NaN，检查dtype/device及输入不变；列非连续不属于公开支持合同。上游验证入口为 `tests/python/operators/sample/test_row_argmax.py`。本次未运行数值、真机或性能测试。
