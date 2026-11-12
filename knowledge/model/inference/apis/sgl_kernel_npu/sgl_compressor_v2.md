---
type: API
title: SGLang CompressorV2 的环形缓存与有效输出
description: 记录 CANN9.2/A3 实验接口的无APE分组压缩、必需状态块表、未定义padding与eager执行边界。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/compressor_v2.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-08T11:04:14Z'
platforms:
- a3
cann_versions:
- 9.2.0
---

# SGLang CompressorV2 的环形缓存与有效输出

## 接口原型

```python
from sgl_kernel_npu.operators.attention import compressor_v2

def compressor_v2(
    x, wkv, wgate, state_cache, cmp_ratio=4, *,
    state_block_table=None, cu_seqlens=None, seqused=None, start_pos=None,
    impl="auto",
): ...
```

## 入口与状态契约

该接口接入 CANN 9.2.0/A3 的 experimental CompressorV2。先以 FP32 计算 `K=XWkvᵀ`、`G=XWgateᵀ`，对每个已完成压缩组逐特征计算 `sum(softmax(G)*K)`，再转X.dtype。固定coff=1、cache_mode=2、无APE，也不包含 compressor 的RMSNorm/RoPE步骤。

X为FP16/BF16 `[B,S,H]` 或packed `[T,H]`，H=1024..10240且512对齐，权重 `[D,H]`、D=128/512。FP32状态 `[P,C,2D]` 原地写入，P>=B且P>0、C=1..1024，前D通道为K、后D为G。int32 `state_block_table[B]` 虽默认None，A3实际必需；块号须在0..P-1且全局唯一，0是有效块。仅cache第0轴可非连续，其他输入连续、同设备。

每次仅将新输入最后 `min(seqused[b],C)` 个token写入对应物理块的绝对位置模C处，其他cache不变。起始组不完整部分读取已有历史；续接必须更新start_pos并复用已写cache。cmp_ratio支持2/4/8/16/32/64/128。TH要求从0到T的非递减int32累计边界，BSH不传；seqused与start_pos可选，设备值合法性由调用方保证。

## 有效输出与依赖边界

仅返回cmp_kv：BSH容量 `[B,ceil(S/r),D]`，每请求有效槽数 `floor(((start_pos%r)+seqused)/r)`；TH按请求紧密拼接有效组，容量 `[min(T,T//r+B),D]`。padding未定义，不能比较或送入attention。

`auto`与包内 `cann_ops_transformers_cann920` 是同一后端，无回退。依赖独立experimental vendor/Python包、匹配编译环境，首次调用可能JIT编译绑定。torch_native是CPU FP32参考，要求C>=r。来源明确指出上游custom_op的 `mutates_args=()` 与实际cache写入不一致；当前仅记录eager契约，未确认functionalization、torch.compile、TorchAir捕获或autograd。

验证时用独立cache副本对比有效行及指定写入区域，覆盖多次续接、非零起点、块0与空输入；单次结果一致不能替代图模式验收。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。
