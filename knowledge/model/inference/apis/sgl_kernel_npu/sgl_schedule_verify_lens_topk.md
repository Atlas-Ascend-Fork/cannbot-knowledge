---
type: API
title: SGLang DSpark生存概率预算与验证长度调度
description: 说明schedule_verify_lens_topk_triton的FP32累乘、稳定排序、预算分配、验证长度上下界与三Kernel二次排名边界。
tags:
- task.implementation
- topic.speculative_decoding
- topic.compute.ordering
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/schedule_verify_lens_topk_triton.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/schedule_verify_lens_topk.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/schedule_verify_lens_topk.py
  role: implementation
created_at: '2026-11-08T11:03:55Z'
updated_at: '2026-11-09T04:38:44Z'
platforms:
- a2
- a3
- '950'
---

# SGLang DSpark生存概率预算与验证长度调度

```python
from sgl_kernel_npu.operators.sample import schedule_verify_lens_topk_triton
schedule_verify_lens_topk_triton(*, confidence, budget, cfg, impl="auto")
```

auto选Triton，另有独立Torch reference；文档声明arch22/arch35支持，分别列出Ascend910_9362及950已验证，不能把上游这条报告写成本次真机验证。

confidence为NPU `[B,gamma]` FP16/BF16/FP32，值须在[0,1]；支持非连续输入，Triton会先复制连续。cfg提供min_verify_len、survival_eps及resolved_max_verify_len()，调用者须保证 `0<=min_verify_len<=max_len<=gamma+1` 和survival_eps>=0，公开层不预先校验。

对每请求位置计算FP32生存概率 `S[r,p]=prod(confidence[r,0:p+1].float())`，仅考虑前min(gamma,max_len)位置，并从不低于survival_eps的候选中选至多budget个。排序键依次为概率降序、位置升序、请求编号升序。budget<=0不选择候选；某请求选中数count转换为 `clamp(min_verify_len+count,max(min_verify_len,1),max_len)`，当max_len>=1时至少验证一次，故不能只看零budget就推断零验证；合法max_len=min_verify_len=0时输出为0。输出同设备新建int32 `[B]`，不改输入。

Triton实现由三个Kernel组成，候选两两比较排名计算量随候选数二次增长；不要以TopK名字推断次线性排名。Torch reference用累乘、稳定排序、scatter-add。不同实现累乘的舍入可能改变极近概率的排序，验收需覆盖相同概率稳定性及近阈值情形。

上游入口 `tests/python/operators/sample/test_schedule_verify_lens_topk_triton.py`；以合法cfg验证预算<=0、候选过滤、全1平局、非连续输入与输出范围。本次未执行真机、数值或性能测试。
