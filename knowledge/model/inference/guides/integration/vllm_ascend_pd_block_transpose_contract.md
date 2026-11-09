---
type: Guide
title: vLLM Ascend异TP缓存接入：block原位重排与传输完成门禁
description: 核对TransposeKvCacheByBlock将分片优先恢复为token优先的原位变换、K/V独立block stride和相邻层分组，沿Mooncake普通/Hybrid调用区分拉取完成、拼接和NZ转换；明确block ID去重/范围、非幂等重排、空输入、UB分块及图mutation待验边界。
aliases:
- transpose_kv_cache_by_block
- MooncakeConnectorWorker.reformat_kv_cache_with_fused_op
- TransposeKvCacheByBlockTilingFunc
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.data_movement
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_host/transpose_kv_cache_by_block_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_host/transpose_kv_cache_by_block_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_host/transpose_kv_cache_by_block_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_host/transpose_kv_cache_by_block_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_kernel/transpose_kv_cache_by_block.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_kernel/common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_kernel/full_load.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/transpose_kv_cache_by_block/op_kernel/general.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_transpose_kv_cache_by_block.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_connector.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_hybrid_connector.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
created_at: '2026-11-03T02:17:49Z'
updated_at: '2026-11-03T02:17:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend异TP缓存接入：block原位重排与传输完成门禁

## 任务与固定范围

P/D使用不同TP时，多份P端KV分片可能已传到D端正确的backing，却仍按分片优先排列；Attention需要token优先布局。TransposeKvCacheByBlock解决这个块内重排，不负责传输、TP拓扑协商、NZ转换或cache分配。总体Pull/Push、ACK和释放见[PD传输生命周期](vllm_ascend_pd_transfer_lifecycle.md)，物理页视图见[非连续KV接入](vllm_ascend_non_contiguous_kv_cache.md)。

本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读该算子README、全部Host、Device源码、两份CMake及320行nightly定义，另读Torch/Meta、两个Mooncake调用点和配置默认值的明确片段。OpDef只登记ascend910b/ascend910_93和FP16/BF16；这不扩展为950、310P或所有PD组合支持。

外部AscendC库、生成ACLNN入口、动态TensorList ABI、完整connector状态机和图runtime没有闭包；本卡是集成Guide，不作为完整Operator/source_closed声明。未运行上游、pytest、编译、服务、NPU、图或性能实验，保持draft与空平台。

## 先确认数据处于哪一个阶段

令B为blockSize、H为当前cache的KV头数、D为headDim、S为splitNum。Tensor外形一直是[num_blocks,B,H,D]，但待处理块的字节顺序是[S,B,H/S,D]。重排把前两轴交换，再合并头维为[B,H,D]；不是对Tensor metadata做transpose，也不是交换block IDs。

该操作原位修改被选块，返回None，保持view的shape、stride、storage_offset和data_ptr。未选块和block间隙不属于有效写入范围。S=1时排列不变；一般S>1时变换不幂等，不能在重试、重复完成通知或重放回调中再次处理已经token优先的块。

接入时应记录每个请求/组/块是否已完成传输、是否仍是分片优先、是否已重排，以及哪个事件允许Attention消费。传输完成日志与重排完成是两个信号，P端可释放也不自动证明D端已具备正确布局。

## Torch入口校验与未代办的责任

C++先检查layerNum>=0且两个列表长度均等于layerNum；B/H/D/S为正且H可被S整除；blockIDs必须连续一维INT64。layerNum=0在这些基础检查后直接返回，不访问列表首项。

非零层逐个检查K/V为[blocks,B,H,D]、与blockIDs同设备、所有数据dtype等于首个K，block内size>1的轴必须连续；多block时stride(0)>=B×H×D。每层K/V的block数量须相同，但不同层的block数未在这里统一相等校验。每个ID都必须对所有参与层有效，不能只检查首层容量。

空blockIDs仍先经过各cache元数据校验，再不发射；零block的cache只允许空ID。单block的第0轴stride可任意，因为不推进该轴，binding会把其传给Host的stride归一为dense block大小。不要为让检查通过而改变原view的storage_offset或伪造capacity。

binding不读取设备ID值验证非负、上界或去重，也不检查跨层/K/V的有效区域重叠；这些是调用方责任。Device直接读取ID并转成64位block偏移，没有本地ID范围保护。负ID不能充当scatter式PAD；重复ID或跨Tensor别名会使原位重排互相干扰，不能通过“同一个storage”判断一定安全。

OpDef/README限定FP16/BF16，当前binding的上述检查主要保证dtype一致，不能由它未拒绝其他dtype推导设备支持。headDim×2必须按32字节对齐，即当前D为16倍数；Host会拒绝不对齐宽。

## K/V独立stride与相邻层分组

IgnoreContiguous允许block轴有间隔，未授权block内部任意转置或列间隔。K/V可由交错backing的不同lane得到，但各自访问的有效区域仍须互不重叠；不需要把整份cache先contiguous再写回。

binding从真实Tensor推导K/V各自的block stride，以**元素**为单位，并按相邻层的stride对分组提交。相同stride的非相邻层不被跨越合并；层间布局变化会增加launch数。单block归一化只用于分组/参数，不改变Tensor本身的stride。

Host属性kBlockStride/vBlockStride为0时使用B×H×D，小于dense大小时拒绝；直接调用ACLNN必须显式提供非连续view的真实值，缺省0不自动发现padding。新增stride属性与64位tiling字段要求binding、生成ACLNN接口和算子库来自同一版本，不能只替换Python文件。

## Host的UB分块与设备同步边界

Host按2字节数据计算整block占用。可放入UB时选key0的full-load路线；否则从可用AIV核数的因子中选blockSizeSplitNum，先尝试单tile<=UB/2的双buffer，失败再尝试单buffer。只沿B切分，不进一步拆H或D；仍不能容纳时返回失败。

| key | Host选择 |
| --- | --- |
| 0 | 整block加载，单buffer |
| 1 / 3 | 切B并双buffer；B能整除/不能整除切分数 |
| 2 / 4 | 切B并单buffer；B能整除/不能整除切分数 |

任务总数按layerNum×选中block数计算，核数再按切分与工作量缩减；tile字段多数为UINT32，block stride为UINT64。合法小Tensor通过检查不等于任意极大整数、零core或溢出配置可用。Host没有在所读函数中设置workspace大小，不能据此宣称执行器全过程零分配。

full-load路线把一个选定block完整搬到UB后写回；general路线按分片读入各token段，再写回token优先位置，尾部不整除时单独计算src/dst offset和copy长度。general在写出前使用CrossCoreSetFlag/CrossCoreWaitFlag，部分分核尾部另有补齐等待。Host CMake关闭cce-auto-sync，不能删除这些手工同步或仅凭单核结果推广多核/所有key正确。

这里只读到自定义Device源码及其库调用，未核验底层DataCopy约束、完整跨核barrier参与者和编译生成结果。原位读写需要所有相关读取先完成，不能将显式flag当成任意重叠输入或跨stream依赖的保证。

## Mooncake调用的门禁与参数来源

普通connector的选定流程在pending reformat中按请求/分片记录并取出ready组，非hybrid路线要求组的pull数一致。只有需要多分片拼接或NZ时才继续；开关enable_transpose_kv_cache_by_block与enable_custom_op同时为真时，拼接部分走融合算子，NZ仍单独走原Torch路径。is_hma_required分支使用独立hybrid-linear Torch重排，不能仅由开关True判断所有组都执行本算子。

普通helper从实际首层K/V Tensor推导KV头数和K headDim，从cache字典取layers，flatten块列表为INT64设备ID；实际binding再校验全部参与Tensor。它没有在此helper去重IDs，也未用V headDim构造另一套参数，故模型K/V宽不同、组内形状不统一或列表含别名时须提前判断适配。

Hybrid connector的所读调用点只在global_offset到达pull数×prefill PP数−1时触发需要的拼接/NZ阶段。其融合helper从model_config推导headDim、local KV头数和num_hidden_layers，再把实际cache列表传入；配置层数与实际列表不等会被binding拒绝，不能据此默认任意PP/local-layer划分已适配。两个helper的参数来源不同，不宜互相复制。

开关默认True，可置False保留connector已有的Torch重排路线；它不影响直接调用算子。关闭融合后仍应从同一份未重排数据开始比较，不能先原位变换后再执行参考路径当验收。整个传输完成事件、锁与请求释放没有在这两个有界片段完全复核，不能据方法名证明端到端时序已正确。

## 图与验收

Torch schema声明Tensor[]输入并返回空值，没有在所读schema中标注列表元素的mutation alias；实际C++/Device却原位改cache。Meta和GE proto函数均直接返回，不提供额外shape或副作用校验。应检查真实编译/捕获图是否保留该调用及读写依赖，不能因fake成功或返回None便认定图正确，也不能在本次静态阅读后宣称已复现图消除问题。

nightly定义以A2/A3 skip门、FP16/BF16、整块/切块/127尾块、独立K/V stride、交错/带gap和非零offset等比较；部分用gather→Torch transpose→scatter作参考，存储用例则比较整份backing并检查view metadata，另覆盖单block任意stride、空ID/空cache、overlap和非连续payload拒绝。本次只读取测试，未执行；未由用例定义证明每个key、barrier或PD端到端均已通过。

新模型先保存传输前后的逻辑layout、各层capacity/stride/alias和唯一有效ID，确认重排只执行一次；逐块比较有效区、未选块、K/V其他lane和guard padding，再分别验证真实key、图/eager、并发与传输→重排→Attention完成事件。正确后再比较launch分组、UB与省去的临时gather/scatter开销，不从融合名称承诺固定延迟或显存收益。
