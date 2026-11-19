---
type: Guide
title: 独立npugraph_ex通信：不均匀归约、Broadcast与点对点桥接
description: 完整核对不均匀归约转换、Broadcast两版源和返回值、Send/Recv静态桥接与副作用。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_reducescatter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_broadcast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_send_recv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_reducescatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_broadcast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_send_recv.py
  role: implementation
created_at: '2026-11-11T06:49:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex通信：不均匀归约、Broadcast与点对点桥接

## 完整本地注册与版本

完整读取TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的_hcom_reducescatter.py、_hcom_broadcast.py、_hcom_send_recv.py。这些是独立npugraph_ex本地Python Schema/Meta/PrivateUse1与追踪patch，不是全部HCOM设备实现，也没有本次建组、通信或运行结果。产品未知，保持draft[]。

各op仅在名字尚不存在时注册；普通c10d patch未追踪时返回原API的结果，uneven ReduceScatter则调用包导出函数后裸return，返回None，丢弃其结果（包括若存在的Work）；追踪时构造自定义op并copy回原缓冲。后端按group tag及ranks找/建PG；单看候选op、Meta成功或Python函数存在不能认证真实组、流顺序、通信完成和调用方返回值合同。完整Gather/AllToAll见[计数与回写](npugraph_ex_hcom_gather_alltoall_counts_and_copyback.md)。

## 不均匀ReduceScatter的分配与未用位移

PrivateUse1把输入shape第一维改为recv_count并new_empty；再调用包导出的REDUCE_SCATTER_TENSOR_UNEVEN，缺符号抛AttributeError，调用明确async=False。Meta按同一第一维规则申请占位；send_displacements在这两个本地函数体都未消费，不能由Schema字段存在推成任意位移布局已实现。

patch追踪时拒绝async_op=True，取group/ranks/tag，缺input_split_sizes就以input.size(0)//group_size填各段，只检查sum等于input第一维；recv_count取output.size(0)，传空displacements，最后reshape为output.size并copy_，没有显式返回Tensor或Work。局部没有补全段长度、非负、所有组大小/shape一致性；未追踪路线也要导出函数存在。

## 归约枚举两方向并不完全对称

convert_reduce_type接ReduceOp对象就原样返回；字符串sum/avg/product/min/max/band/bor/bxor分别映射对应枚举，其他值ValueError。反方向convert_reduce_op对任何str原样返回；枚举SUM/AVG/PRODUCT/MIN/MAX/BXOR对应字符串，但源码实际把BAND映为'bor'，且没有单独BOR枚举分支。两版均保留这段实际不对称，不能将其默默整理成八项对称表。

因此给str并不等于已在patch层验证是合法归约名，直接传枚举BAND与传'band'也不能按该本地转换认为同一路径。这里只记录静态代码差异，不认证底层运行后会出现哪种结果，未执行错误复现。源码不用字典表驱动的说明与Torch2.1符号转换限制有关，不推广为所有Torch版本都不能处理ReduceOp映射。

## Broadcast的组内源和返回值有版本差异

PrivateUse1把原input交给同步c10d.broadcast并返回它，Meta只empty_like；追踪patch取得新op结果后tensor.copy_(out)。主线Schema的src为optional，并新增group_src，patch默认src=None且将group_src一直传到原API/后端；发布Schema的src为必需int，没有group_src。两者并未在本文件统一验证src/group_src互斥和所有组内外rank映射。

追踪成功的主线patch返回tensor，发布则裸return即None；未追踪时均返回原API的结果，不能把两个分支和两个固定版本的返回值概括为同一类型。两版追踪路线均拒绝async_op=True，不能由eager原API支持的异步选项推成图路线已接收Work。

## Send/Recv保留副作用，但返回值需要独立对齐

_send的Schema包括Tensor、optional dst、ranks、PG tag、消息tag、optional group_dst以及optional int[] shape，Meta返回None，PrivateUse1调用c10d.send且不返回其结果；发布显式return None，主线隐式None。patch追踪时取tensor.shape传op，未追踪时直接返回原send。这里没有单独的async参数、通用rank/tag或shape校验。

_recv的Schema同样包含source/组内source和shape，Meta申请同shape empty；后端c10d.recv后返回被写入的Tensor，丢弃原c10d.recv的返回值。追踪patch把结果copy回tensor后隐式None；未追踪却返回原recv结果。因此不要用该patch认证源rank返回行为仍与原API完全相同，特别是src缺省场景。

两个op均显式has_side_effect，shape虽按注释为静态形状入图而加，本地PrivateUse1并不使用该参数重新分配/验证通信内容。int[]声明与注释不构成完整动态shape支持或缺失的证明；外部代码生成、匹配的收发参与者和实际运行库仍需各自证据。

## 模型侧验证

分别记录是否正在追踪、准确PG/rank列表、全局与组内源、消息tag、split和归约原值/转换值、用户原缓冲及返回对象，再核对Meta、发射图与真实通信。显式copy_、临时缓冲、归约语义、未更新区域及流生命周期一起计入端到端成本。本卡没有运行上游、导入注册、设备实验或新增verified。

## 完整本地ops来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_reducescatter.py)（primary）：1–145；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_broadcast.py)（implementation）：1–58；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_send_recv.py)（implementation）：1–123；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_reducescatter.py)（implementation）：1–136；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_broadcast.py)（implementation）：1–52；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_send_recv.py)（implementation）：1–122；仅完整本地定义与注册，外部被调实现另计。
