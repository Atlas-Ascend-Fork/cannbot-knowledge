---
type: Guide
title: GE集合通信实现：计数、写回与版本边界
description: 保留GE计数与通信记录边界，补充发布量化Eager的world_size/H/BS门槛、RS扁平输出及FP4与Meta差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allgather.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allgather.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allreduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allreduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_alltoall.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_alltoall.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_broadcast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_broadcast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_reducescatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_reducescatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/c10d_functional.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/c10d_functional.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/hcom_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/hcom_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_all_reduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_reduce_scatter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge_concrete_graph/ge_converter/experimental/hcom_allgather.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge_concrete_graph/ge_converter/experimental/hcom_allgather.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge_concrete_graph/ge_converter/experimental/patch_for_hcom_allreduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge_concrete_graph/ge_converter/experimental/patch_for_hcom_allreduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantAllReduceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantReduceScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T09:40:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE集合通信实现：计数、写回与版本边界

## 固定版本与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013，审阅六个experimental通信模块、c10d_functional、两版hcom_utils全文及限定辅助函数。主线15份分页、发布完整383行AST/注释差异均已核对；一组成对Converter AST相同，六组有差异，其中AllToAll计数/shape和Broadcast签名/返回行为是实质变化。

本文限定源码静态合同，整卡平台矩阵未知，保持draft与空平台；未导入或运行上游、初始化进程组、开启端口、发送数据或做多卡实验。文档层入图清单和产品范围另见[集合通信指南](collective_communication_graph_contract.md)，不能把那个层次的支持列表用来覆盖本卡每个重载、参数和版本。

## 跟踪补丁、写回和异步分支

npu_*_patch_dist在_are_we_tracing()为False时回调原distributed_c10d或保存的uneven接口；跟踪分支的all_reduce、all_gather、all_gather_into_tensor、all_to_all、all_to_all_single、broadcast和uneven包装均明确拒绝async_op=True。它们创建功能化结果后copy_回调用方输出或原tensor，这与Converter里的out形参是否被写回是不同层次；不能按构图返回值认证公开原地语义。

patch_for_deepspeed_allreduce捕获导入异常后只记日志；导入成功时替换deepspeed.comm的all_reduce与inference_all_reduce。这里涉及进程内全局函数替换，模块含定义/Meta/PrivateUse1注册，源码阅读没有执行任何安装或通信。

## 归约枚举存在两套不同处理

convert_reduce_op接受字符串原样返回；枚举SUM/AVG/PRODUCT/MIN/MAX分别变为sum/avg/product/min/max，**BAND分支却返回bor，BXOR返回bxor，没有对应BOR枚举分支**。这是可定位的静态映射疑点，未做运行复现，不能宣传所有位归约都正确。

normalize_reduceop_type先upper并检查Torch RedOpType成员，但GE映射只接受SUM/MIN/MAX/PRODUCT，最后一个改为prod；其他已知成员也抛ValueError。因此convert_reduce_op能给出的avg/bor/bxor不表示所有下游GE入口都接受。反向的convert_reduce_type还接受band/bor/bxor及avg并转Torch枚举，不能假定两套转换互为逆函数。

## AllGather的形状恢复、拆分和非等长计数

| 入口/分支 | 静态处理 |
| --- | --- |
| torch.ops.npu_define.allgather_in_tensor.default | HcomAllGather(input,rank_size=group_size,group,fusion=0)，再Reshape至Shape(output_tensor,INT64)；output_tensor在此Converter提供尺寸，不作为接收结果的直接数据写回对象。 |
| torch.ops.npu_define._allgather_in_tensor_shape.default | 同样HcomAllGather，但按显式output_shape恢复；公开patch从output_tensor.shape取该参数，之后copy_回输出。 |
| npu_define.allgather列表分解且输出等size | 将input按group_size次复制引用并cat作输出规格，调用allgather_in_tensor，按input.shape[0]重复分段，再恢复各输出shape。最终patch逐项copy_。 |
| 列表分解且输出不同size | 按输出列表逐项broadcast；用torch.distributed.get_rank()与枚举i比较来选择本rank输入。子组rank映射需继续核对，不能据此认证任意非连续rank_list。 |
| torch.ops.npu_define.allgather_in_tensor_uneven.default | send_count/recv_counts/recv_displacements转INT64，HcomAllGatherV后dont_prune_me标记；patch默认按output.size(0)//group_size分配并检查和等于output.size(0)，send_count=input.size(0)，位移传空列表，最后reshape/copy_。 |

uneven的Meta/Eager helper按sum(recv_counts)决定第0轴；Eager调用保存的ALL_GATHER_INTO_TENSOR_UNEVEN，缺接口抛AttributeError。这里保存的是第0轴分段，不能未经核对就套用下述AllToAll的元素计数换算。列表patch检查输出列表长度等于rank数，但不能替代所有shape/分段值域校验。

## AllToAll的计数单位和主线对齐分支

准确Converter入口为torch.ops.npu_define.all_to_all_single_npu.default。_all_to_all_single根据输入除第0轴外的元素数，将input_split_sizes/output_split_sizes乘成send_counts/recv_counts；缺分段时按input.numel()//group_size均分，并构造前缀和displacements。这里只检查两个counts列表长度相同，没有完整分段总和、组大小和整除校验。

两版Eager bridge不同：主线将元素counts除以尾部维度乘积，还原第0轴split_sizes再调用c10d.all_to_all_single；发布版直接把counts当split_sizes并用sum(recv_counts)作第0轴。这个差异对多维输入重要，不能把相同Schema当作相同计数语义。两版Meta helper仍会按尾部维度乘积处理recv_counts；Eager/Meta/GE应分别核对，displacements在这些Eager调用中没有被消费。

Converter先尝试_is_gte_cann_version('8.2.RC1',module='CANN')，导入或RuntimeError视False。当版本条件为True、send/recv_counts均为Python List且合并后所有值相同时，提前返回HcomAllToAll；其他路径将四组计数和位移转INT64，再HcomAllToAllV并标记dont_prune_me。快路径没有后面V分支的同样标记或Meta Reshape；不能任意将两条分支合并。

主线V分支有meta_outputs时，尝试读取其静态size并INT64 Reshape；size访问AssertionError则警告并返回原未知shape结果。发布版没有这段对齐。主线公开single patch还在input.numel()==0时直接返回output_tensor，发布版没有；这一快捷分支的跨rank一致性需按真实通信协议确认，不能作为可随意跳过集体通信的通用优化。

列表AllToAll先flatten/cat输入，按每个tensor.numel()生成counts，输出按recv_counts拆分并恢复原shape；存在0接收项时只split非零项，零项用相应shape的empty占位，再copy_回用户列表。这些处理不认证所有空输入、异构shape和复数路径；来源保留暂不支持复数入图的TODO，未在本次验证。

## ReduceScatter非等长路径

torch.ops.npu_define.reduce_scatter_tensor_uneven.default把send_counts、send_displacements、recv_count转INT64，以normalize_reduceop_type处理归约，再HcomReduceScatterV并标记保留。patch默认按input.size(0)//group_size生成input_split_sizes，检查其和，recv_count取output.size(0)，位移为空，返回结果reshape/copy_；Eager和Meta helper按recv_count设置输出第0轴。保存的REDUCE_SCATTER_TENSOR_UNEVEN接口缺失时AttributeError，不能把GE节点构造成功当外部依赖可用。

## Broadcast、Send/Recv的rank与返回差异

主线npu_define.broadcast Schema接受可选src及group_src；Converter创建/查找组，经_canonicalize_group_rank(group,src,group_src)后HcomBroadcast。发布版src为必需int且没有group_src，规范化时传None。主线跟踪patch最后返回tensor，发布版最后返回None；Eager分支仍回调原函数，不能混淆两条返回路径。c10d v2的broadcast映射则把src直接作root_rank，没有复制这个规范化步骤。

_send/_recv Schema携带显式int[] shape，patch从tensor.shape取得；Converter分别HcomSend和HcomReceive，后者用tensor.dtype及该shape并标记保留。两者使用pg_tag/ranks和_canonicalize_group_rank处理dst/group_dst或src/group_src；_send的Meta返回None并在FX注册side effect，_recv的Meta返回新empty并在patch copy_回原tensor。

这些是静态shape和构图依赖处理，不等于任意动态通信shape、收发匹配、rank顺序或无死锁保证。Recv跟踪patch没有显式return，完成copy_后返回None；不能只按函数名假设跟踪与Eager分支完全同一返回合同。

## c10d功能化入口与wait

旧torch.ops.c10d_functional.all_reduce.default、torch.ops.c10d_functional.reduce_scatter_tensor.default、torch.ops.c10d_functional.all_gather_into_tensor.default分别构造HcomAllReduce/HcomReduceScatter/HcomAllGather；out形参在这些Converter中未被使用。wait_tensor仅Identity(self)，不独立证明整图没有通信等待，实际执行和依赖语义需核对后端。

文件在torch.__version__ >= '2.3.1'条件下注册_c10d_functional版本：由group_name解析ProcessGroup，再取得ranks/tag并记录HCCL group；包含all_reduce、all_gather_into_tensor、reduce_scatter_tensor、broadcast和wait_tensor。不能只因比较右边是字符串就断言纯字符串排序，实际取决于版本对象的比较实现。decomp_c10d_functional_all_to_all_single在本文件仅定义函数，是否注册须看加载模块，不能把定义当作生效证明。

## Group缓存、导出记录与保留标记

get_group_name_and_record先_find_or_create_pg_by_ranks_and_tag；CPU用tag/rank_list编码名称，NPU以当前rank调用get_hccl_comm_name(init_comm=True)，然后在当前GeGraph记录group_name到(rank_list,tag)。CPU名称路径不是CPU产品执行保证，记录元数据也不是完整rank校验。

record_pg_to_graph只扫描已初始化的hccl组，取init_comm=False的现存comm name，再为图上匹配group属性补记录。rename_cached_pgname将已记录名称改成tag/rank_list编码；codegen_refresh_cache_pgname生成加载时代码，要求_find_pg_by_ranks_and_tag已能找到组，否则AssertionError，然后init_comm=True取得新名称并改写图属性。它不是跨任意进程组配置可复用缓存的证明，本次没有执行生成代码。

GeGraph.record_process_group只保存字典映射，dont_prune_me只把op追加到保留列表；后续Pass怎样消费仍需继续审阅，不能把这两个辅助方法当作通信完成或内存屏障。FX side-effect登记和GE保留意图应与真实运行同步分别核对。

## 优化验证

先确认Eager通信、软件配套和各rank一致调用，再检查准确FX入口、counts单位、分段和shape、公开copy_写回、归约转换、group/rank规范化及缓存重命名；核对最终图和多rank数值后再测重叠与吞吐。本次仅静态审阅，未执行上述实验。

## 发布快照专有路径的量化集合通信

额外完整审阅发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的quant_all_reduce.py与quant_reduce_scatter.py，各76行；所选主线无同路径，仅记录文件差异，不作全局能力否定。准确入口分别torch.ops.npu.npu_quant_all_reduce.default、torch.ops.npu.npu_quant_reduce_scatter.default。

两函数在x_dtype/scales_dtype非None时，分别Bitcast输入至数值翻译后的GE类型并设置Proto描述符，随后check_dtype；output_dtype非None时做数值类型翻译，否则默认BF16。它们不是普通数值Cast，也不根据Meta默认推导输出精度。

check_dtype的实际允许集合：x为INT8/HIFLOAT8/FLOAT8_E5M2/FLOAT8_E4M3FN；scales为FLOAT或FLOAT8_E8M0。**源码错误消息把scale范围写成float32/hifloat8，但实际集合是float32/float8_e8m0**，不能照报错文字扩展支持。x为INT8或HIFLOAT8且scales为E8M0时额外拒绝；其他集合内组合只表示本地检查未拒绝，不是产品/kernel全矩阵。

最终分别QuantAllReduce/QuantReduceScatter，传group=hcom、world_size、reduce_op和output_dtype。reduce_op默认sum但原样传递，没有调用前文normalize_reduceop_type；hcom也是直接字符串，没有调用get_group_name_and_record，导出/缓存组记录需要按调用方继续核对。不能将普通通信的归约限制、组名编码或uneven分段规则机械套用。

## 发布量化集合通信的Eager/Meta限制

另核对OpPlugin发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的QuantAllReduce/QuantReduceScatter包装、Schema及Meta。两份C++在主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`同路径均不存在，仅记录精确路径差异，不推断主线全局缺少量化通信能力。发布Schema登记op_api的[v2.6,newest]范围，也不是CANN最小版本、设备或完整模型支持证明。

### world_size和shape不能按普通AllReduce概括

两个Eager包装都要求x是非空二维[B,H]或三维[B,S,H]、world_size仅2/4/8，H按输入Tensor实际尾维检查为1024..8192且128对齐。令BS=B或B*S，两者都要求BS可被world_size整除，**包括不切分结果的QuantAllReduce**。不能从数学AllReduce无需切batch推导此包装接受任意BS。

scales只在本地检查非空、rank为2/3/4；错误文字说TG需同rank、MX需多一维，但代码没有逐项实现x/scales对应轴、分组尺寸或scale值检查。不能把这一宽松rank集合当成完整TG/MX广播合同。

| 入口 | Eager输出与Meta形状 |
| --- | --- |
| npu_quant_all_reduce | 与x的物理shape相同；二维仍二维，三维仍三维 |
| npu_quant_reduce_scatter | 总是二维[BS/world_size,H]；三维输入也将B*S合并，不保留原batch/sequence分界 |

两者输出缺省BF16，显式output_dtype通过枚举转换用于分配，C++没有完整输出类型白名单。Meta只做x/scales非None和world_size集合检查，再推导shape/dtype，不重复H范围、非空、BS整除或全部dtype组合；非法尺寸的整除截断或Meta成功不能作为Eager可用证明。

### FP4检查与GE并不相同

Eager显式x_dtype集合实际含INT8、HiF8、FP8 E4M3/E5M2以及FP4 E1M2/E2M1，虽然报错文字漏写FP4；scales_dtype显式允许FP32/E8M0。未提供覆盖参数时，本包装没有执行相同集合的实际Tensor dtype检查；不据缺检查扩展任意FP16/FP32激活支持。

前面的发布GE局部check_dtype却不接受FP4，并且拒绝INT8/HiF8配E8M0尺度。Eager没有同样的配对拒绝，不能将Eager局部未拒绝解释成kernel已支持，也不能因提供相同覆盖参数便认为Eager与GE可互换。make_wrapper只指定后端逻辑解释，不执行数值量化或位打包。

尤其FP4时，这两份Eager包装按原Tensor物理尾维检查H并分配输出，没有在本文件把打包H显式恢复两倍逻辑H。不能用FP4枚举存在认证打包输入的完整shape、尺度和浮点输出协议；需要对照真实ACLNN及逻辑解码另证，本次未运行这一分支。

### 通信域与性能验收

Eager将hcom和reduce_op字符串（缺省sum）直接传aclnnQuantAllReduce/QuantReduceScatter；**world_size只参与本地检查/输出分配，没有作为这个ACLNN调用的单独实参**。本包装不创建进程组，也不查询hcom实际成员数来核对world_size。GE则把world_size放入节点属性，不能把两个层次混为一体。

实际调用前应由调用方核对通信组、world_size和各rank一致调用、目标逻辑dtype与真实位编码，再按对应反量化尺度对比完整归约参考；ReduceScatter还检查扁平化后的rank分片。性能对比要包括上游量化、尺度传输、通信、反量化及模型消费，不能仅以输入位宽计算收益，也不对未知reduce_op或软件组合给出运行保证。本次没有初始化通信域、运行上游或多卡测试，无新增verified。

## 旧命名空间导入也有进程全局副作用

两快照的python/torchair/ge_concrete_graph/ge_converter/experimental/hcom_allgather.py（即torchair.ge_concrete_graph.ge_converter.experimental.hcom_allgather，注意没有前导下划线）在模块顶层导入新命名空间patch函数，并直接替换torch.distributed.all_gather/all_gather_into_tensor，还发出未来不再支持旧路径的warning。__all__=[]不代表显式导入这个模块无副作用；不能为了检查是否可用就随意导入。

旧路径patch_for_hcom_allreduce.py（torchair.ge_concrete_graph.ge_converter.experimental.patch_for_hcom_allreduce）同样在顶层替换torch.distributed.all_reduce并调用patch_for_deepspeed_allreduce。两版计算副作用相同，差异仅warning字符串写法；这不是被动的兼容别名，也不是只改一张图。本文仅静态读取，未导入模块或安装补丁。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allgather.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allgather.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allreduce.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_allreduce.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_alltoall.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_alltoall.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_broadcast.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_broadcast.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_reducescatter.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_reducescatter.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/c10d_functional.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/c10d_functional.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/hcom_utils.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/hcom_utils.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_all_reduce.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_reduce_scatter.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge_concrete_graph/ge_converter/experimental/hcom_allgather.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge_concrete_graph/ge_converter/experimental/hcom_allgather.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge_concrete_graph/ge_converter/experimental/patch_for_hcom_allreduce.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge_concrete_graph/ge_converter/experimental/patch_for_hcom_allreduce.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）

## 补充实现证据

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantAllReduceKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantReduceScatterKernelNpuOpApi.cpp)（implementation）

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定实现来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_all_reduce.py)（implementation）

- [固定实现来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_reduce_scatter.py)（implementation）
