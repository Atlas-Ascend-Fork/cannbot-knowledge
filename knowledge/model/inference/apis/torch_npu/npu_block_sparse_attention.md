---
type: API
title: npu_block_sparse_attention：块掩码、精度与950差异
description: 说明稀疏块mask与GQA/TND形状，保留950块粒度和精度参数的文档Meta冲突。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_block_sparse_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BlockSparseAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_block_sparse_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_block_sparse_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BlockSparseAttentionBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_block_sparse_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_block_sparse_attention_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BlockSparseAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BlockSparseAttentionBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_block_sparse_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_block_sparse_attention_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
created_at: '2026-11-09T07:08:10Z'
updated_at: '2026-11-10T02:42:48Z'
platforms:
- a2
- a3
- '950'
---

# npu_block_sparse_attention：块掩码、精度与950差异

## 固定版本与范围

前面的主线契约依据OpPlugin d84e9b1d6a558e5f27973cd4329f62968e46fdda产品页及同提交实现；后续另补固定发布差异与前反向测试缺口。未执行上游实现、图编译或设备实验。

## 接口与块语义

```text
npu_block_sparse_attention(query, key, value, block_sparse_mask,
    block_shape, *, q_input_layout='TND', kv_input_layout='TND',
    num_key_value_heads=1, scale_value=0.0, inner_precise=1,
    actual_seq_lengths=None, actual_seq_lengths_kv=None,
    softmax_lse_flag=0) -> (attention_out, softmax_lse)
```

块mask为INT8(B,Nq,ceil(Sq/blockX),ceil(Skv/blockY))，1表示计算该KV块、0表示跳过，不是sparse_indices的块ID列表。block_shape至少两个正元素。Q/K/V同为FP16或BF16，布局同为TND或BNSD，Nq≥Nkv且Nq%Nkv=0。正向headDim仅64/128，反向只128，不从前向范围推断完整训练链。

TND时两份actual_seq_lengths必传，BNSD可不传；两者必须同时有或同时无。参数页称每batch实际长度；主线TND测试进一步区分传给算子的长度与仅用于CPU切片的累计offset，见后文。序列不需整除块大小，mask块数向上取整。scale_value默认0不代表已确认自动采用1/sqrt(D)，应按模型显式设置所需系数。

## 产品与Meta限制

A2/A3的blockY须128倍数，inner_precise为0/1，其中BF16只能0。950DT产品专节改为blockY为16倍数、inner_precise只4；但Meta仍无产品判断地要求blockY为128倍数、BF16仅0。因而950较小块在Meta会被拒绝，BF16/950的两处文档条件也存在冲突，不提供该组合的图替换保证。

950的基础产品支持只按明确FP16与合法精度分支使用，不能据总dtype名单宣称BF16+4已得到一致证据。Python默认inner_precise=1也不符合950专节，部署必须显式核对。

## 输出与验证

attention_out同query shape/dtype；文档与Meta允许尾维随value，但当前约束value与key shape相同，C++按query分配，不扩展为任意不同value headDim。LSE为FP32，TND形状(T,Nq,1)，BNSD为(B,Nq,Sq,1)，仅flag=1时有效。C++和Meta在flag=0仍分配该shape，不能据关闭结果消费或假定零分配。

以相同块mask、GQA映射、长度和scale计算参考，覆盖尾块和全跳过行的产品规定；分别评估稀疏计算减少与不规则访存开销。此卡是接口边界，不把注册的反向入口当作所有组合已支持训练的证据。

## 发布与主线的反向范围

本节另核对发布OpPlugin dedc316708372c9a8bfde4527abd2a94b74840f5；发布组合为ascend_26_0_pt28，主线d84e9b1d6a558e5f27973cd4329f62968e46fdda配套未知。发布产品页只有A2/A3，反向明确只BNSD、MHA和headDim128。主线反向文档扩为同为TND或同为BNSD、MHA/GQA、headDim128；它是文档范围变化，不回推发布的TND/GQA训练支持。

950主线这里只列DT，不能由注册平台950泛化为PR也支持。英文block_shape总参数行仍写Y必须128倍，中文已移除这句，产品专节共同区分A2/A3的128倍与950DT的16倍；950DT专节只inner_precise=4，而BF16通用条款仍要求0。没有来源一致的BF16+4保证，默认1也不能直接用于950DT。已有Meta冲突按前文保留。

## 长度、LSE与自动求导

主线TND/GQA测试将各batch的实际Q/KV长度列表传给算子，例如[1,64,129,17]，并只在CPU参考内生成带起始0的累计offset切片。这里应区分长度与CPU切片偏移，不向算子传别的Attention接口的前缀和。Q/KV可以有不同的每batch长度，mask按各batch最长Q/KV长度向上分块、在有效范围裁剪。

两版本derivatives只有attention_out可微，LSE和block mask不可微；自动反向消费保存的Q/K/V、同次attention_out、LSE、mask、block_shape和两份长度。公开backward依次返回dQ、dK、dV，参数中没有inner_precise；不能从前向某精度分支推导任意反向精度可选。

softmax_lse_flag默认0虽仍分配并返回同形FP32 LSE，但公开协议只在1时有效。当前derivatives没有把0自动改为1或重算有效LSE，因此需要反向的调用应显式设1并核验保存的值，不能把“返回了张量”当成有效统计量。两个版本的autograd测试都显式设1，无法证明省略flag也可安全反向。

## 包装代码与编译前检查

前向C++只额外检查Q/K/V同dtype、按query尺寸分配输出和按rank分配LSE，透传scale_value而没有把0改为1/sqrt(D)。底层atten_mask、block_table为空，mask_type和block_size为0，pre/next_tokens固定最大值；公开接口没有因此获得逐token mask、分页KV或任意滑窗参数。EXEC_NPU_NO_FORMAT_CHECK_CMD也不代表后端没有其他校验。

两版反向C++检查同dtype与headDim<=128；这是较宽的前置检查，不替代文档的headDim128支持范围。主线新增TND两份非空实际长度检查，发布没有；最终布局和组合仍由ACLNN验证。backward的block_shape缺失或长度不足2时都使用[128,128]，不会自动恢复前向用过的其它块形状，显式调用应传同一合法block_shape。

两版Meta相同：前向只查query rank3/4、blockY能被128整除与BF16时inner_precise=0，再按value尾维分配；没有完整检查QKV/mask dtype、GQA头数、正blockX、长度配对、scale或精度枚举。反向Meta只创建三个同形梯度，没有相同的TND长度检查。Meta成功和后端设备支持分开，固定TorchAir Python快照未见专用转换器也不作全部编译方式明确No。

## 测试覆盖和参考值缺口

两版本正向测试逐字节相同，各9方法，全部门控Ascend910B及CANN>=9.0.0；包含BNSD/TND输出与LSE、FP16/BF16、精度0/1、flag0形状、多块与部分稀疏。这个测试门控不是已测最低部署版本。没有950DT/inner_precise4/blockY16、A3运行、图或性能数据，本次未执行这些测试。

主线反向14方法中9个TND/GQA/变长/负例/autograd方法全被无条件skip，提示等待gate CANN支持；发布仅5个BNSD方法。新增TND参考把连续的G个Q heads映射到同一个KV head，即kv_head=n//G，梯度向共享KV累计。旧BNSD/正向参考却用n%Nkv，正向所谓GQA测试只选Nq=Nkv或Nkv=1，恰好不能区分两种映射；文件注释提到的其他G也没有实际全部枚举。不要把旧参考搬成一般GQA实现。

旧BNSD反向参考的dV在head循环里是赋值而不是累加，只在当前MHA测试没有共享head时合适；不能拿它证明多Q共享KV的梯度。新增TND参考使用+=累计dK/dV，长度只用于各batch有效切片，属于更合适的参考意图，但对应九个方法仍跳过。

旧softmax参考声称全mask行返回0，实际用-1e10填满时减最大值得到全0，Softmax变成均匀分布；若输入全-inf又会产生NaN。当前稀疏用例特意每行保留至少一个KV块，不能据注释写全跳过行已验证。主线TND参考也填-1e10，仍需单独核对全屏蔽行的产品语义。

名字为forward_backward_together的测试实际只把CPU前向参考生成的attention_out/LSE送入NPU backward，没有运行该用例名暗示的NPU前向串接。另一个autograd用例只比较NPU自动反向与同一NPU显式反向，能检查绑定一致性，不能独立证明完整前后向数值正确。训练验收应增加真实同次前向统计量与独立参考的比较、Nkv>1且G>1、尾块/非均匀长度和目标产品；性能收益另测，本次无新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_block_sparse_attention.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BlockSparseAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_block_sparse_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_block_sparse_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BlockSparseAttentionBackwardKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_block_sparse_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_block_sparse_attention_backward.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BlockSparseAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BlockSparseAttentionBackwardKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_block_sparse_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_block_sparse_attention_backward.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）
