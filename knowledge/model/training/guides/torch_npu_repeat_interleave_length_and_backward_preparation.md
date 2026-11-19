---
type: Guide
title: RepeatInterleave：输出长度、Host读数与反向准备
description: 区分RepeatInterleave重载的output_size哨兵、Host标量读取、整数版本路由及反向view/sum或SDK准备。并含反向两名 custom 算子（repeat_interleave_backward_int/tensor）的 yaml 注册归属与 symint 段重复登记。
tags:
- task.optimization
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RepeatInterLeaveKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RepeatInterleaveBackwardKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RepeatInterLeaveKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RepeatInterleaveBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-12T02:29:43Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# RepeatInterleave：输出长度、Host读数与反向准备

Tensor repeats是否需要Host读数，取决于**具体重载及output_size的值**。传了output_size并不代表所有路线都没有归约、同步或梯度准备，尤其0在self+Tensor helper中被当作“待推导”哨兵。

| 入口 | 输出准备与可见成本 |
| --- | --- |
| self+整数repeats | SymInt通过expect_int具体化；检查dim及repeats非负，形状直接按repeats×轴长或numel计算；申请结果。self非空且给出output_size时比较计算值，无Tensor sum/item |
| self+Tensor repeats，output_size非0 | 形状helper直接使用给定长度；没有在这个helper中重新sum验证Tensor repeats。申请后self非空时再次比较给定值与推导值 |
| self+Tensor repeats，output_size缺省或值为0 | 执行repeats.sum().item().toLong读取Host长度；repeats只有一个元素时再乘self选中轴长度，未给dim时乘self.numel；因此显式output_size=0也走该读数路线 |
| 主线新增、仅repeats的Tensor重载 | 要求一维且Int/Long；空repeats先返回empty_like，未检查给定output_size是否匹配。非空始终先cumsum；给output_size则直接expect_int作为total，未给才读取cumsum尾项并对`(repeats>=0).all().to(Bool).item()`作负数检查。按total申请后执行aclnnRepeatInterleaveTensor |

self+Tensor的本地形状检查允许0维repeats，或一维长度为1/选中轴长度（未给dim时为numel），不是完整数值验证器。apply_result_tensor对空self不比较output_size；Tensor helper没有统一负值/溢出防护。上表只是源码可见检查与Host标量提取，不把正确output_size外推为所有值都已被本地认证。

## 整数路线的真实版本差异

主线整数repeats在有无dim时都使用aclnnRepeatInterleaveIntWithDim；未给dim先将self.reshape为一维、SDK轴为0。发布有dim用IntWithDim，无dim则直接用aclnnRepeatInterleaveInt和原self，两条兼容探测也分开。Tensor repeats的有dim/无dim则分别使用aclnnRepeatInterleaveWithDim/RepeatInterleave。

V2R1的output_size为optional<int64_t>，V2R2及之后为optional<SymInt>并expect_int；主线仅repeats重载在V2R2之后守卫内，发布对应CPP和所读official Schema没有该定义。这里比较精确路径与配置，不宣称发布社区中所有其他实现都缺该公开功能。

## 反向的两个成本形态

整数repeats反向直接具体化并走本地view→sum→view：在选中轴将grad轴拆为`[长度/repeats,repeats]`，随后沿新增轴sum，再view为self形状；本地在该轴检查repeats非0，没有单独的整除检查或显式contiguous整理，不能声称所有stride布局均零拷贝。

Tensor repeats只有一个元素时先`repeats.item().toLong()`，再用同一view/sum路线；多个元素时把grad选中轴替换为repeats.size(0)，申请ND结果，调用aclnnRepeatInterleaveGrad后view为self形状。缺省dim在这段反向代码取grad最后一轴，与前向未给dim的flatten准备分开；两版反向活动代码相同。

## 固定证据

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`，只读完整包装与所列形状函数/Schema；未执行算子、Host读数或设备实验。外部view、SDK及旧ACL兼容实现不在这里补造支持结论。DTensor布局分发另见[Repeat布局](torch_npu_dtensor_loss_and_repeat_layouts.md)。

## Evidence

- [RepeatInterLeaveKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RepeatInterLeaveKernelNpuOpApi.cpp)（primary）：1–231。
- [RepeatInterleaveBackwardKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RepeatInterleaveBackwardKernelOpApi.cpp)（primary）：1–83。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1867–1927。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4275–4292、7107–7111。
- [RepeatInterLeaveKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RepeatInterLeaveKernelNpuOpApi.cpp)（implementation）：1–219。
- [RepeatInterleaveBackwardKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RepeatInterleaveBackwardKernelOpApi.cpp)（implementation）：1–77。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1678–1735。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：4160–4174、6897–6901。

## 反向两名 custom 算子的注册绑定

前文「反向的两个成本形态」所述实现文件（RepeatInterleaveBackwardKernelOpApi.cpp）对应 yaml `custom:` 段登记的两名：`repeat_interleave_backward_tensor`（op_api: all_version）与 `repeat_interleave_backward_int`（op_api: [v2.1, newest]；均无 acl_op 行）。`repeat_interleave_backward_int` 另在 `symint:` 段重复登记（op_api: [v2.1, newest]），实现侧的 `repeat_interleave_backward_int_symint` 以 SymInt 形参承接、`expect_int` 具体化后进入同一 `repeat_interleave_backward_one_repeat`。这两个不带 npu_ 前缀的 ATen 名义名实际是 OpPlugin 自定义算子；单元素 repeats 的 view→sum→view 本地组合与多元素的 aclnnRepeatInterleaveGrad 分流即前文两节内容，本节只补注册归属，不重复行为结论。symint 段同区域另登记 `repeat_interleave.self_int`（acl_op+op_api v2.1）与 zeros(SymInt[])（**仅 acl_op [v2.1,newest]**，与官方段 zeros 的双后端登记并存）。

### 注册绑定补充证据

- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：7107–7112、7687–7696；custom 段两名与 symint 段重复登记（该文件已列于 frontmatter 来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：6897–6902、7453–7458；同两组条目（该文件已列于 frontmatter 来源）。
