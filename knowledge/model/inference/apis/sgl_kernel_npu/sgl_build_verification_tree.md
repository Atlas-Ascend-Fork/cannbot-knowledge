---
type: API
title: SGLang验证树构造的预分配输出与掩码模式
description: 蒸馏build_tree_kernel_efficient的父索引、tree_mask容量和retrive链表语义，保留bitpacking未实现与平台未定位边界。
tags:
- task.implementation
- topic.speculative_decoding
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/build_tree/README.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/build_tree/op_kernel/build_tree_kernel.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/build_tree/op_host/build_tree.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/build_tree/op_host/build_tree_tiling.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_build_tree.py
  role: evidence
created_at: '2026-11-08T11:03:55Z'
updated_at: '2026-11-09T13:21:21Z'
platforms: []
---

# SGLang验证树构造的预分配输出与掩码模式

## 接口身份

README将draft模型多步TopK候选组织为verification tree，入口为下述Torch绑定；固定材料未给独立整卡芯片支持范围，因此保持draft与空平台，不以仓库整体支持代替本接口证据。

```python
torch.ops.npu.build_tree_kernel_efficient(
    parent_list, selected_index, verified_seq_len, tree_mask, positions,
    retrive_index, retrive_next_token, retrive_next_sibling,
    topk, depth, draft_token_num, tree_mask_mode)
```

函数返回None，通过调用方预分配Tensor写结果。`parent_list`为int64 `[B,topk*(depth-1)+1]`，`selected_index`为int64 `[B,D-1]`，verified_seq_len为int64 `[B]`，D为draft_token_num。

## 容量、位置和链表

FULL_MASK的布尔存储元素数为 `sum(verified_seq_len)*D+B*D*D`；QLEN_ONLY示例分配 `B*D*D`。positions与retrive三组链表在语义上为 `[B,D]` int64；README的positions示例用等元素数的扁平存储，不能据此承诺任意stride或shape均合法。

retrive_index是节点到扁平索引，retrive_next_token为首个子节点，retrive_next_sibling为下个兄弟，缺失用-1。README示例先将三组链表填-1、mask填True，再调用构造；三组retrive输出不读取调用方原值，Kernel内部把next_token/next_sibling初始化为-1，写入全部retrive_index并完整写回，因此预填-1是示例写法，不是这三组输出的必要条件。FULL_MASK中每行历史前缀mask未被Kernel覆盖，仍须由调用方预先置True，不能与完全写回的链表输出混同。positions表示完整序列中的绝对位置。

实际头文件枚举为`FULL_MASK=0`、`QLEN_ONLY=1`、`QLEN_ONLY_BITPACKING=2`；README参数表中的“1=FULL_MASK”与头文件及测试枚举冲突，应以同版真实绑定为准，不能按该表把1当FULL_MASK。Host对2明确抛出Not implemented；示例存在bitpacking分配分支不代表支持。

固定Device的QLEN_ONLY还有独立静态写址边界：非FULL分支用`D*D*bs+D*bs`计算每次mask写出起点，没有使用当前tid。D>1时同一batch的D次Compute覆盖同一段，不能认为生成了完整`[B,D,D]`矩阵；b>0的额外D*bs偏移也不是预期逐行位置。对未知非0/2模式Host没有枚举拒绝，Device同样走该else，不构成额外公开模式支持。上述是实际源码寻址推导，没有本次真机复现。

Host只检查八Tensor dtype组合及bitpacking未实现，不检查完整shape/device/连续性/索引值域；batch和mask.size(0)先进入int32，Device又将D与mask_size窄化uint16。batch=0可令分核计算除零，大D或大mask声明范围也不能直接视为已支持。caller应提供连续、同NPU、足够容量且合法无环的树输入；父节点搜索最多比较到D项，而selected每行只有D-1项，父节点缺失等非法输入存在越行读取/未终止祖先追踪边界，不能依赖本Host过滤。

完整链表初始化与mask历史前缀保留仍按上文区分。本文补充接口与实际寻址限制，不将这些静态事实写成完整工程编译或运行验收。

## 验证入口和未知项

`tests/python/sgl_kernel_npu/test_build_tree.py`的实际main只调用默认FULL_MASK，B2、topk4、depth4、D8，断言positions、三组链表和预处理得到的draft token；tree_mask只打印，没有数值断言，也没有QLEN_ONLY验证。预处理的Torch topk/sort/gather属于测试输入构造，不是上述原生构树入口本体。不能用该测试定义为QLEN_ONLY或mask矩阵背书。

消费前应核对同版本绑定的模式值、输入合法性、Tensor布局及平台，并构造父子/兄弟/绝对位置和mask的独立树reference。README引用的CUDA分支链接不作为本卡额外技术证据。本次未编译、运行真机或数值/性能测试。
