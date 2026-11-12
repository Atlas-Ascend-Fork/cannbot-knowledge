---
type: API
title: SGLang投机输出构造与有效前缀长度
description: 说明build_out_tokens_triton如何保留draft尾部、插入bonus、固定gamma+1输出，并将提交前缀交由接受长度控制。
tags:
- task.implementation
- topic.speculative_decoding
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/build_out_tokens_triton.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/build_out_tokens.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/operators/sample/test_build_out_tokens_triton.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/utils/accuracy.py
  role: evidence
created_at: '2026-11-08T11:03:54Z'
updated_at: '2026-11-09T04:38:56Z'
platforms:
- a2
- a3
- '950'
---

# SGLang投机输出构造与有效前缀长度

```python
from sgl_kernel_npu.operators.sample import build_out_tokens_triton
build_out_tokens_triton(*, draft_tokens, correct_len, bonus,
                        verify_num_draft_tokens, gamma, impl="auto")
```

Triton与独立Torch reference声明arch22/arch35（A2/A3、950）支持，auto选Triton。输入draft为同NPU `[B,gamma]`，correct_len/bonus为 `[B]`，均int32或int64；gamma>=0，`verify_num_draft_tokens==gamma+1`，每行0<=correct_len<=gamma由调用者保证。Triton支持有stride的输入。

输出同设备新建 `[B,gamma+1]` int64，不改输入：先复制整个draft、追加0，再在correct_len处写bonus。**bonus之后的draft仍保留**，输出shape或非零值不能表示已提交token；有效前缀长度只能用 `correct_len+1`。

例如draft `[10,11,12]`、correct_len=1、bonus=99，得到 `[10,99,12,0]`，只提交前两个元素。完全接受gamma个draft时bonus写最后一列；接受0时bonus写首列。Torch reference用拼接/scatter提供相同合同。

上游测试定义覆盖0/全接受等接受长度、gamma=0及奇数宽度等边界，使用默认 int64 的连续 arange 输入并比较两种实现返回值；没有 int32、非连续 stride 或输入不变断言。非连续输入、int32、输入保持不变及有效前缀提交应另补定向验证，不能当作已有覆盖。上游入口 `tests/python/operators/sample/test_build_out_tokens_triton.py`。本次未运行数值或性能测试。
