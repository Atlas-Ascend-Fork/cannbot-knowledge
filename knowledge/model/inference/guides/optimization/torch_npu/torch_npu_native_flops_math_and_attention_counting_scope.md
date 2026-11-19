---
type: Guide
title: TorchNPU原生FLOPs公式与Attention计数口径
description: 限定原生GEMM/卷积/Attention计数的数学实现、TND平均长度与Python/MSTX口径差异。
tags:
- task.optimization
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/flopcount/FlopCounter.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/flopcount/FlopCount.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCounter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCount.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-11T08:00:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU原生FLOPs公式与Attention计数口径

## 公式层与公共状态层分开

依据PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的FlopCounter.cpp，两份381行原始字节完全相同，主线全部数学定义已逐段读取，发布按完整字节复用。另仅核宏和OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`/发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的指定Host调用片段；两个main不自动构成兼容栈。

本文新增数学/计数诊断，不重复[FlopsCounter公共状态API](../../../../training/apis/torch_npu/flops_counter.md)的start/pause/返回顺序，也不扩大其产品表。与[Python/MSTX FLOPs公式](torch_npu_profiler_attention_gemm_flops_estimates_and_throughput.md)为不同实现路径，不能只因名字接近就合并数值。平台未知，未编译、导入、执行公式、操作Tensor或做训练/吞吐实验。

## GEMM与通信乘积

mm_flop只先检查两输入rank>0，将各自rank>2的batch前缀交at::infer_size广播；左rank>=2追加M，右rank>=2追加N，以左末维K乘2再乘输出各维。因此向量点积为2K，一侧向量不额外补该侧M/N；这里没有另核两侧收缩维相等或所有dtype/设备条件。addmm复用mm，不加bias或alpha/beta算术。

bmm显式取[B,M,K]与[B2,K2,N]，要求B==B2且K==K2，返回2BMNK；baddbmm直接复用，不另外计相加项。all_gather_mm先求mm值，只有gather_index==0才乘world_size，其余返回原值，未核world_size与真实通信组；这不是通信字节、等待或全部归约开销。

这些GEMM乘法与累乘没有通用溢出保护，不能因为返回int64_t就认证任意大shape计数安全。它们依赖已满足原算子合同的输入，调用数学函数给数不证明算子可运行。

## 卷积实现按代码乘积，不按注释补全

conv_flop_count取batch=x_shape[0]、Cout=w_shape[0]、Cin=w_shape[1]、filter=prod(w_shape[2:])，再乘2。非转置时conv_shape为out_shape[2:]；转置分支实际用**整个out_shape**，并非注释提到的输入空间维。这里只记录该固定实现，不将其替换成通用卷积理论公式。

filter和conv_shape的accumulate初值为1、运算器为std::multiplies<int>，不能用最终int64_t变量宣传全程64位保护。bias未独立计入；注释称只算multiplication而代码又乘2，比较统计时应保留实际函数版本和约定，不凭注释任意改单位。

conv_backward仅按output_mask[0]/[1]分别加输入梯度和权重梯度项，不计算第3项bias梯度。转置与否控制传给conv_flop_count的布尔和交换顺序；辅助t只构造{shape[1],shape[0],shape[2],shape[3]}，没有把任意rank都自动泛化为同一交换方案。公共支持和完整shape检查仍属于调用者/底层算子。

## Attention布局重建与TND的平均长度

_unpack_flash_attention_nested_shapes先要求head_num!=0，再读取Q/K/V的第1/2维；不是完整rank、正head数或整除验证。BSH/SBH按head_num整数除隐藏维重建BNSD；BSND重排四维；BNSD沿原shape。用于GQA/MQA的调整条件实际是Q对应维同时不等于K且不等于V时才一起替换两个KV维，不能将注释扩写成任意不一致都被正确归一化。BNSD分支最终直接放入原始query/key/value shape，前述k_1/v_1局部替换未写回这些shape；该layout的Q/K/V head数不等仍会进入sdpa中H相等的TORCH_CHECK，计数宏没有catch。这里只描述静态调用路径，不作运行复现结论。

TND只要求两份累计序列数组非空、条目数相同，并用条目数作B。它没有逐项按累计端点做差，而是把Q/K/V各自总token数除B，拼成一份等长的[B,N,total/B,D]；只发射一个shape元组，未检查总token是否整除。数组的具体端点数值没有用于这个重建。因此不同变长序列分布即使总token和条目数相同，也会得到同样这层估算，不能当作逐序列精确QK/PV面积。

不在已列layout分支时result可以为空，外层累加初值0；0并不证明实际算子无计算。代码并无sparse_mode、padding/attention mask、dropout窗口参数，不能从函数名推成这些真实有效元素均已排除。

## SDPA前反向的实际返回式

归一化为Q=[B,H,Sq,Dq]、K=[B,H,Sk,Dq]、V=[B,H,Sk,Dv]后，sdpa_flop_count检查B/H一致、K/V序列长相等、Q/K头维相等，返回两个乘积之和：

```text
B*H*Sq*Dq*Sk + B*H*Sq*Sk*Dv
```

这里没有像本文件GEMM一样额外乘2。原生宏也只是累加这个返回值，所以不能把全部计数都假定已统一成同一种“乘加计2”口径。Python/MSTX的普通Attention公式显式有2，亦不应拿它直接替换这个C++函数的结果。

反向helper再检查grad的B/H/Sq及末维等于Dv，累加gradScores、gradV、gradQ、gradK四个矩阵乘积，不另外计softmax、bias或mask算法。外层flash_attention_backward_flop虽接收dy，构造dy_shape却来自query；布局重建时只看这个向量是否非空，再用重建后的query形状作grad_out_shape。不能因参数名dy就认为真实dy形状已被这层校验。

safe_multiply遇0返回0，否则以INT64_MAX/dim限制每步乘法；safe_sum逐项检查上界。它们不是所有GEMM/卷积或全局计数累加共享的保护，且只约束所走的乘积/求和，不证明所有维度、动态值和调用者均合法。

## 宏和Host调用说明数字怎样进入计数器

主线TORCH_NPU_FLOP_COUNT在Context启用时调用数学函数，将返回int64_t直接加traversed，未暂停时也加recorded；FLOP_COUNT是带弃用编译提示的转发宏。发布使用旧名直接实现同一累加路径。宏不重新乘2、不作公式异常捕获，也没有全局累加的独立溢出检查。

所读FlashAttention前向Host块在EXEC_NPU_CMD之后调用flash_attention_forward_flop，所读AllGatherMatmul块调用all_gather_mm_flop再返回两输出。这只覆盖这些具体计数调用，不是对整个Host文件、全部版本、后端Kernel完成或数值正确性的资格。计数函数本身可能TORCH_CHECK；若计数阶段抛错，宏没有在本地把它吞掉或替换成0，不能一律把启用统计视为对Host错误路径无影响。

## 对比吞吐时保留两个实现的口径

本地原生Counter的GEMM、卷积、Attention不同函数具有上述不同乘积约定，TND又采用平均长度；Python/MSTX按另一组形状/累计序列和mask公式求值。它们都不是设备实测指令计数，也不自动识别全部重计算/通信/激活。

保存原算子路径、公式提交、layout、各rank局部shape、变长端点、计数开关区间及实际测时窗，再比较FLOPs/时间或MFU/HFU。不要无条件将整个模型数乘2修正，也不要把两个机制结果简单相加或拿一套峰值分母套另一套算术口径；硬件峰值与设备性能本卡均未测量。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/flopcount/FlopCounter.cpp)（1–381行；完整数学模块）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/flopcount/FlopCount.h)（6–20行；仅有界宏/调用块）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCounter.cpp)（1–381行；完整数学模块）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/flopcount/FlopCount.h)（6–16行；仅有界宏/调用块）
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（938–952行；仅有界宏/调用块）
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp)（155–165行；仅有界宏/调用块）
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（734–748行；仅有界宏/调用块）
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllGatherBaseMatmulKernelNpuOpApi.cpp)（75–83行；仅有界宏/调用块）
