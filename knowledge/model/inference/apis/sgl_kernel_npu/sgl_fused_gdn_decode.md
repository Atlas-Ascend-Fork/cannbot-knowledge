---
type: API
title: SGLang融合GDN decode的状态池和负索引语义
description: 说明单token递推、V×K连续FP32状态池原地写回、负槽零状态与Q/K归一化选项。
tags:
- task.implementation
- topic.attention
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/attention/gdn/fused_gdn_decode.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/gdn/fused_gdn_decode.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/attention/gdn/fused_gdn_decode.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/attention/gdn/fused_gdn_decode.py
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/fused_sigmoid_gating_recurrent_decode_optimized.py
  role: implementation
created_at: '2026-11-08T11:04:14Z'
updated_at: '2026-11-09T15:22:09Z'
platforms:
- a2
- a3
- '950'
---

# SGLang融合GDN decode的状态池和负索引语义

## 接口原型

```python
import torch
from sgl_kernel_npu.operators.attention.gdn import fused_gdn_decode

def fused_gdn_decode(A_log, a, dt_bias, softplus_beta, softplus_threshold, q, k, v, b, initial_state_source, initial_state_indices, scale=None, use_qk_l2norm_in_kernel=False, cu_seqlens=None, *, impl='auto'):
    ...
```

## 递推与形状

`fused_gdn_decode` 融合softplus衰减、sigmoid更新权重、可选Q/K L2归一化与GDN状态更新。先 `d=exp(-exp(A_log)*softplus(a+dt_bias))`、Sd=dS，再 `r=sigmoid(b)*(v-Sd*k)`、S=Sd+r*kᵀ，输出S*(q*scale)。softplus_beta须正，threshold控制线性分支，scale默认K^-0.5且应为正。

本快照可用契约为Q/K均为FP16/BF16 `[B,T,H,K]`，头数必须相同；V为 `[B,T,HV,V]`，HV仍可为H的整数倍。API说明表虽列出较小Hg，但公共wrapper注释与Triton实现都按同一H/i_h寻址Q和K，torch_native也按Q的heads重塑K，没有键头扩展；传较少K头会产生错误寻址或形状异常，不能按文档Hg分组直接调用。A_log/dt_bias为FP32 `[HV]`，a/b为Q dtype `[N,HV]`。固定长T=1；packed时B=1并且各序列恰好一个token，cu_seqlens为int32/int64 `[N+1]`。

## 可变状态池

initial_state_source为连续FP32 `[slots,HV,V,K]`，最后两维按V、K解释。initial_state_indices为同设备int32/int64 `[N]`，负槽按零初始状态计算且不写回；非负槽必须有效且调用方应避免有冲突的并发更新。

函数只返回与V同shape、Q dtype的新output，同时原地更新连续状态池的选中槽。非连续池会被复制，不能假设复制后的结果回写原tensor。Q/K归一化使用范数+1e-6，不要与其他epsilon定义混同。auto选Triton、无自动回退；内部状态递推FP32，torch_native仅独立精度参考并可能同步host元数据。

验证应克隆状态池分别运行参考/被测实现，比较输出及选中槽、未选槽保持，覆盖负索引、head分组和归一化开关。该入口是单tokendecode，不以packed参数存在推导多draft-token递推能力。

## 证据与复核范围

本卡依据固定提交的第一方API说明蒸馏；架构编号按同提交构建说明映射为A2/A3（arch22）及950（arch35），具体子功能仍受正文限制。本次知识提取未执行编译、真机、数值或性能测试，未记录verified事件。

## 旧decode优化入口的逐字复用与raw边界

固定fla.fused_sigmoid_gating_recurrent_decode_optimized.fused_sigmoid_gating_delta_rule_update_decode_npu整文件与新implementation/triton/attention/gdn/fused_gdn_decode.py逐字相同，含imports、_maybe_contiguous、JIT decorators/defaults、Host和body。因此可复用同一个decode后端算法，不为旧模块另建重复Operator；它与另一个旧fla.fused_sigmoid_gating_recurrent的BHV2、多token/KDA分支仍有不同入口和覆盖域。

这份优化Host将输入逐个_maybe_contiguous，并切到q.device context；initial_state_source/indices虽在JIT有USE_INITIAL_STATE heuristic，Host却无条件对两者调用is_contiguous，不能传None来触发JIT的零初态分支。已是连续的状态池原地写回；非连续池的复制不copyback。两个模块导入同一个旧utils.triton_utils.get_device_properties，复用该无参数cache对象，不能把此处写成两个独立device感知cache。

BHV=1、NHV=HV，grid=max(1,min(N*HV,vectorCores))，OVERSUB1，num_warps4、num_stages1、multibuffer=False。每program以pid+j*numPrograms处理(sequence,value-head)，内部遍历所有V片，BK=nextPower2(K)、BV=min(nextPower2(V),64)。本路线没有BHV2的奇数Hv漏头分发；每片状态按V×K解释并FP32加载/计算，单token按前文数学更新后转池dtype写回，output按Q options分配。

raw Host固定长只检查T==1；packed只检查q.shape[1]==N，没有逐项检查cu的差恰为1或B==1、头整除/正维度、所有shape/dtype/device及正向slot容量。公开合法合同仍要求每请求恰一token，不能用总T==N替代。若cu造出某段多token，body在该段token循环外只读首token门控，状态地址在循环内却按i*HV*K*V递进并逐次重载/写回；这不是携带同一状态的通用多token递推。负slot每步用零状态且不写池，超出合法单token域不因循环存在就得到正确多draft语义。

Q/K可选归一化为x/(sqrt(sum(x²))+1e-6)，在FP32局部进行；softplus、sigmoid门控也是FP32。源码do_not_specialize T/N/NHV，物理UB与最终pipeline仍由匹配Triton编译器决定，不把逻辑4*BV*BK状态payload误当全UB峰值。[A2/A3完整decode源码卡](../../operators/direct/transformer/attention/sgl_fused_gdn_decode.md)与[950源码卡](../../operators/direct/transformer/attention/sgl_fused_gdn_decode_950.md)展开当前公开域；本节不扩大旧raw Host的平台验收或多token支持，本次未执行任何运行测试。
