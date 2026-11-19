---
type: Guide
title: 独立npugraph_ex通信：Gather与AllToAll的计数和回写
description: 完整记录Gather和AllToAll的组标记、元素计数、Meta/运行差异、临时缓冲与copy回写。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_alltoall.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_allgather.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_npu_define_lib.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_alltoall.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_allgather.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_npu_define_lib.py
  role: implementation
created_at: '2026-11-11T06:49:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex通信：Gather与AllToAll的计数和回写

## 完整固定来源与调用层级

完整绑定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的ops/_hcom_allgather.py、_hcom_alltoall.py及_npu_define_lib.py。两版后者均为npu_define FRAGMENT Library；各文件仅在对应op缺失时define/impl，已有dispatcher不会在此被强制替换。没有导入、分配Tensor、建组、追踪、通信或设备实验；产品与完整配套未知，保持draft与空平台。

patch函数按_functional_collectives._are_we_tracing选择：普通c10d patch未追踪时委托原distributed API并返回其结果；uneven Gather则在调用包导出函数后裸return，返回None，丢弃其结果（包括若存在的Work）。追踪时拒绝async_op=True，以默认组或指定组取rank列表/tag，通过自定义op得到结果再copy_回调用方缓冲。局部PrivateUse1则用ranks/tag/group_size找或建PG，调用原c10d且async_op=False；PG缓存、建组/调度与通信实现没有在这里闭合。patch函数存在也不证明安装补丁的入口已被调用，不能扩写成全部distributed API自动入图。

## Gather的Meta、分解及显式搬运

allgather(Tensor[] output,input,tag,ranks,size)在本文件只注册Meta，直接返回原output列表；真实运行应核对被选中的分解/后端，不把Meta视为已经通信。allgather_in_tensor的PrivateUse1把提供的output交原c10d，返回该对象；Meta则new_empty同shape。_allgather_in_tensor_shape用input.new_empty指定output_shape，Meta显式生成meta设备、input dtype的Tensor。into_tensor patch只使用原output.shape构图，最终output.copy_(out)，不是把原output内容当通信输入。

list patch要求输出列表长度等于组rank数，调用allgather op再逐项copy_，追踪路线没有显式Work返回。allgather_decomposition先比较各输出shape；全相同时，复制引用input共group_size份做cat(dim0)，将该临时Tensor作为gather输出，再按input第一维split、reshape回每个目标shape。这包含显式cat以及最终patch copy，不是完全无临时缓冲或零拷贝路径。

输出shape不同时，分解逐项broadcast；用torch.distributed.get_rank()的无组参数结果与枚举下标i比较，broadcast源也直接传i，未在本helper改成ranks[i]。不能由这段代码认证任意非连续子组rank映射，需按真实组、源rank含义及外层转换核对。check_same_size空列表返回True，不等于其余分解对空列表/零组已有完整支持。

uneven gather的本地后端以sum(recv_counts)改输出第一维，再调用包导出的ALL_GATHER_INTO_TENSOR_UNEVEN；缺符号抛AttributeError。send_count、recv_displacements虽在Schema中，在本地Meta/PrivateUse1没有消费；不要据此证明一般位移布局已支持。patch默认用output.size(0)//group_size填各段，只检查总和等于output第一维，没有另完整检查长度、非负和所有rank对应关系；调用后reshape为用户output.size再copy_。未追踪路线也显式要求导出符号存在。

## AllToAll计数先转元素单位

_all_to_all_single要求input至少一维，按尾部元素数把提供的0维split sizes乘成send/recv counts；缺省用input.numel()//group_size均分。第一维为0时尾部量计算走input.numel()，没有另用一般shape乘积恢复。只检查send/recv列表长度相同，再以前缀和构造displacements，交all_to_all_single_npu；不在此完整验证份数等于group_size、整除、非负或总量一致。

该op的Meta以尾维乘积（rank1取1）将sum(recv_counts)除回第一维；recv_counts空列表时先按numel/group补齐。局部PrivateUse1却直接以sum(recv_counts)作新输出第一维，并把同一send/recv counts直接传c10d.all_to_all_single的input/output_split_sizes；两项displacements没有在该本体消费。不能将上层元素计数、Meta尺寸与原c10d的0维split语义不加区分地写成已经相互验证，需要结合实际选中的编译降低/后端检查，尤其非一维和零维度数据。本卡记录静态差异，没有执行并复现故障。

single patch仅委托c10d单Tensor/同dtype检查，未按原生complex路线转换；然后调用上述helper并copy_输出。complex相关TODO不是完整产品能力矩阵，也不是本次实际异常。追踪成功没有独立Work或显式输出返回值。

## list AllToAll的flatten和零段恢复

list分解用每个Tensor.numel作为counts，计算位移，保存各输出shape；输入逐项flatten后cat，得到一维通信输入。返回按recv counts split并reshape原shape；出现零count时先只split非零段，再为零段创建指定shape/dtype/device的empty，而非给torch.split传所有零段。

list patch检查输入/输出列表长度相同，委托c10d列表及同dtype检查，解包数量匹配后逐项copy_；没有本地另检查两列表长度等于组大小。输入cat、分解输出、零段empty和回写都可能贡献临时显存/搬运，不能只按通信输出字节估算完整成本。

两版Gather/AllToAll完整差异主要为排版、不插值f-string改普通字符串、copy循环写法，以及发布局部work变量接收一个随后未消费的同步调用结果；这些不构成新的异步Work合同。按相同组、shape、split、输出别名和编译入口验证数值/顺序与峰值显存，再评估模型收益。[不均匀归约与点对点](npugraph_ex_hcom_reduce_broadcast_and_p2p_bridges.md)和[流事件](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)不自动为这里补全rank/同步检查。

## 完整本地ops来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_alltoall.py)（primary）：1–210；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_hcom_allgather.py)（implementation）：1–262；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/ops/_npu_define_lib.py)（implementation）：1–3；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_alltoall.py)（implementation）：1–199；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_hcom_allgather.py)（implementation）：1–238；仅完整本地定义与注册，外部被调实现另计。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/ops/_npu_define_lib.py)（implementation）：1–3；仅完整本地定义与注册，外部被调实现另计。
