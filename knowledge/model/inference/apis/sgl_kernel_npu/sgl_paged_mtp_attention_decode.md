---
type: API
title: SGLang分页MTP注意力的固定draft宽度与graph契约
description: 说明DSpArk分页GQA的固定gamma、FIA ND缓存、右对齐因果和不截断有效KV的max_kv_len。
tags:
- task.implementation
- topic.attention
- topic.speculative_decoding
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/paged_mtp_attention_decode.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T04:38:51Z'
platforms:
- a3
- '950'
---

# SGLang分页MTP注意力的固定draft宽度与graph契约

## 接口原型

```python
from sgl_kernel_npu.operators.attention import paged_mtp_attention_decode

def paged_mtp_attention_decode(
    *,
    query,
    k_cache,
    v_cache,
    seq_lens,
    cu_q_lens,
    block_tables,
    page_size,
    num_q_heads,
    num_kv_heads,
    head_dim,
    gamma,
    softmax_scale,
    max_kv_len,
    causal=False,
    impl="auto",
):
    ...
```

## 固定宽度分页注意力

接口所有参数仅限关键字，auto选Triton、不自动回退。文档明确支持A3与A5/950。所有输入张量须在同一设备；auto/triton要求NPU，torch_native接受CPU或NPU（导入框架仍需原生NPU运行环境）。Q仅支持FP16/BF16，K/V须与Q相同dtype。每请求G=gamma个query，Q用TND `[B*G,Hq,D]`，K/V用FIA ND `[pages,page_size,Hkv*D]`，Hq是Hkv的整数倍、D=16..256，page_size是不小于16的2次幂；cache末维stride=1，外层与Q/page表可非连续。

seq_lens为连续int32 `[B]`、包含当前query块的有效KV末端，0表示padding请求；cu_q_lens为连续int32 `[B+1]`，内容必须等于arange(B+1)*G，不能传变长query分段。block_tables为int32/int64 `[B,max_pages]`，有效KV范围必须映射真实页，范围外和空请求整行可无效。

非causal读取所有0<=j<Lb；causal还要求 `j<=Lb-G+i`，即draft block向有效KV末端右对齐。max_kv_len只是任务划分提示，既不截断也不屏蔽超它的有效KV。没有滑窗或变长query block能力。有效Q/KV需有限、长度/页号由调用方保证，不为检查设备值而复制到CPU。

## 返回与graph边界

返回同Q shape/dtype/device的新tensor，输入不改；可见集合为空输出严格0，B=0返回空tensor。Triton支持NPU Graph捕获，重放从设备长度、页表和Q/K/V缓冲重新读取，无需host提取长度。torch_native使用FP32独立计算但会host读取边界，不支持捕获，且导入公共框架仍依赖可用原生NPU运行环境。

验证时覆盖gamma>1的右对齐、零KVpadding、尾页、无效但不可见页表和非连续stride；graph验收还应改变设备长度/页表重放，不能用一次eager对比代替。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 相关知识

- [MTP投机解码概念与其他集成路径](/model/inference/concepts/techniques/mtp_speculative_decoding.md)
