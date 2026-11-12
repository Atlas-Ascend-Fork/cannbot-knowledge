---
type: API
title: SGLang apply_token_bitmask 原地词表掩码接口
description: 说明 apply_token_bitmask 的位序、选行、原地别名、显式实现选择与子集 wheel 边界，区分 arch22/arch35
  声明和待完成的 NPU 验收。
tags:
- task.implementation
- topic.compute.indexing
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sampler/apply_token_bitmask.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sampler/apply_token_bitmask.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/operators/sampler/test_apply_token_bitmask.py
  role: evidence
created_at: '2026-11-08T10:55:13Z'
updated_at: '2026-11-08T10:55:13Z'
platforms:
- a2
- a3
- '950'
---

# SGLang apply_token_bitmask 原地词表掩码接口

## 接口与适用范围

```python
from sgl_kernel_npu.operators.sampler import apply_token_bitmask
apply_token_bitmask(logits, bitmask, indices=None, *, impl="auto")
```

固定版本声明 Ascend C 与 Torch reference 覆盖 arch22/arch35，即 A2、A3 与 950；这里记录实现契约，上游文档仍标记 NPU 验收待完成。`auto` 与 `ascendc` 均调用 `torch.ops.npu.apply_token_bitmask`，reference 必须显式指定 `impl="torch_native"`。缺失 CANN 注册会报错，没有自动回退。

## 参数与存储语义

| 参数 | 合同 |
| --- | --- |
| `logits` | 连续 NPU Tensor `[B,V]`，FP32、FP16 或 BF16，`B>=0`、`V>0`。 |
| `bitmask` | 同设备连续 int32 Tensor `[B,W]`；每个 word 从最低位开始对应 32 个词元。短缺的 word 视作零，超出词表的列忽略。 |
| `indices` | 可选一维 CPU 或同设备 Tensor；按既有行为转 int64 索引行，索引须有效。`None` 和空 Tensor 都选择所有行。 |

选中行中 bit=0 的词元写 `-inf`，bit=1 保留 logits；未选行不变。函数原地修改并返回与 `logits` 共享同一存储的 Tensor，`bitmask` 和 `indices` 不被修改。输入隔离应克隆 logits，不能让 reference 先改写被测输入。

适配层处理 Kernel 的 256 元素对齐与词表尾块，调用者不应为此擅改 `V`。底层索引与分块偏移受 uint32 范围限制，超限应报错；文档未声明新增 autograd、图捕获或编译模式已验收。

## 集成与验证入口

公共 Python 模块会进入每个 REFACTOR wheel，但原生算子由构建时 `--ops` 选择；能 import 接口不证明安装包包含 CANN 实现。子集 wheel 彼此替换，核对 `_build_manifest.json` 中的选择。

上游 `tests/python/operators/sampler/test_apply_token_bitmask.py` 覆盖三种浮点类型、词表 1/31/32/33、选行与空 indices、全零/全一/交替/随机位掩码，并检查返回存储身份、未屏蔽数值与掩码不变。验证时显式比较不同实现，并用各自克隆输入。性能路径只取 FP32 随机掩码的指定 shape，不能把边界用例存在当成性能测量。

本次知识提取未执行编译、真机、数值或性能测试；测试文件作为复核入口，不作为本次运行结果。

## 来源定位

- 主要合同：`docs/api/zh/operators/sampler/apply_token_bitmask.md`。
- 分发声明：`python/sgl_kernel_npu/sgl_kernel_npu/operators/sampler/apply_token_bitmask.py`。
- 架构与打包：`python/sgl_kernel_npu/README.md`。
- 验证设计：`tests/python/operators/sampler/test_apply_token_bitmask.py`。
