---
type: Guide
title: vLLM Ascend Engram 表加载：分片、量化与 UVA 所有权
description: 加载Engram表时核对head与vocab分片、checkpoint索引和scale格式、固定通信slot，以及私有或共享UVA注册、关闭和参数别名所有权。 区分Engram表的文档与实现接口核对、真实设备数值及跨rank退役验证，不把UVA地址或CPU/mock用例当真机结果。
aliases:
- AscendParallelEngramEmbedding
- HostUvaBuffer
- SharedUvaBuffer
- preflight_engram_checkpoint
- engram_gathered_num_tokens
- Engram表
- head_start
- pad_heads
- AscendParallelEngramEmbedding：表查询与UVA退役验收
tags:
- task.implementation
- task.debugging
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/embedding.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_engram.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_engram_fixed_slots.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/parallel.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/engram_lookup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/engram.md
  role: supporting
created_at: '2026-10-31T06:34:38Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-03T07:29:07Z'
---

# vLLM Ascend Engram 表加载：分片、量化与 UVA 所有权

## 消费任务与固定证据

适配Engram checkpoint、扩展并行表查询或定位host卸载后崩溃时，按head布局→checkpoint选择→存储量化→host/device地址→通信slot→退役所有权核对。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的embedding.py488、npu.py381、parallel.py99、engram_lookup.py123、UT499及fixed-slots118行全文；均只作数据读取，没有导入上游或执行UT/NPU。

Main配对Native为544f182d9f0c9bfe8bd7645525951d5e3692a542，Native布局、checkpoint/CPU-offload helpers与DeviceOperator CANN实现不在本批闭包；不以独立Native v0.32.0快照代替配对ABI。完整硬件集合未知，保持draft/空平台。[模型历史与事件接入](vllm_ascend_engram_model_adapter.md)处理另一个消费任务；本卡不是通用[UVA元数据脏行同步](vllm_ascend_uva_metadata_contract.md)协议。

## head切分、vocab行数与共享方式

AscendParallelEngramEmbedding按TP×EDP平均切head，head数必须可整除，但每head的head_sizes可以不同，vocab边界是这些正行数的prefix sum。总行数不得超过num_embeddings；不要将“均匀head桶”误读成均匀vocab行，或按num_embeddings/world_size切断head。

split模式把表分到TP×EDP，各peer查询同一owned-row区间。共享host模式把DP/PCP视为本地共享副本，表的dp_size=1，仍保留TP head分片；只有TP>1才继续head all-gather。所有TP和EDP×PCP peers必须同host/共享命名空间，本地组size>1才真正启用共享；跨节点不是POSIX共享表。resolve_dp_shared_memory是有效配置/组判定，不仅看用户bool。

真正的SharedUvaBuffer映射分配在cpu_offload分支；其他存储路径不能因dp_shared_memory=true就宣称共享了HBM或CPU backing。Native对cpu_offload、共享及其他配置组合的完整校验本批未读，不直接推荐孤立flag组合。模型部署教程的24 heads与主机内存预算见[V4.1部署](../models/vllm_ascend_deepseek_v41_platform_boundary.md)，不能自动套全部checkpoint。

## checkpoint索引与加载前检查

preflight_engram_checkpoint按每张表自己的header决定dense或quant，不把整个模型的quantization名字当所有Engram表相同。BF16 dense保留；量化表优先保留Native MXFP8/E8M0格式（profile有对应能力），旧profile先解码FP8再转INT8。dummy加载无真实header，不能当成功读取checkpoint。

_checkpoint_index优先含当前weight key的quant_model_weights.index.json，否则用model.safetensors.index.json。codes与weight_scale_inv必须在同一个选定索引里匹配，不能各选一个索引拼接。weight loader负责流式读取，scale callback为空操作；重复调用scale callback不代表重新加载scale。单文件/PT/无索引不是此路径自动支持的回退。

预检保存weight/scale key、分片路径与E8M0 header格式，在分配大buffer前失败；它没有完成全部shape、值域及存储dtype兼容校验。_load_into_storage只读本rank owned rows，按65536行分块，避免整表中间副本；FP8 uint8视图是位拷贝，E8M0 bytes不能按普通uint8数值scale解释。checkpoint跨张量加载并非完整事务，不能由预检成功推出后续所有分片均可用。

共享模式仅组内rank0加载写入，CPU all_gather传播错误并同步，防止其他rank使用半张表；这不保证进程死亡、collective异常或所有已写参数的回滚。先保存每rank实际head区间、索引选择与最终dtype再进入模型forward。草稿主模型量化继承另见[DSpark加载](../../runbooks/runtime/vllm_ascend_dspark_draft_quant_loading.md)，不能用该修复覆盖Engram独立表格式。

## INT8与E8M0数值合同

quantize_engram_rows按32列一组，FP32 absmax/127，再向上取power-of-two scale；全零组scale=1。使用ldexp缩放与ties-to-even舍入，codes夹到[-127,127]。这不是max/128，也没有证明任意非有限值/不整除宽度都受完整guard保护。dequantize_engram_rows以codes×scale恢复，输出BF16；weight_scale_inv虽带inv名称，实际存的是乘法scale，不能再次取倒数。

_decode_e8m0先取byte & 0xFF：0为2^-127的FP32 subnormal，255为NaN，不是Inf；正常码按指数bits左移23构造。普通FP32 scale与E8M0编码分开读取，E8M0的1.0编码是127。device分配和私有UVA在profile/dummy前清codes，scale填1或E8M0的127；清零不构成真实权重加载或内存一致性证明。

INT8/private/shared UVA lookup都按owned global int64行区间判断；不属于本rank的ID用安全row0读取并mask为零。输入IDs contiguous，kernel只写自己local heads，额外head padding不自动清；调用方需先清persistent output尾部。gather_dequantize_host_uva暴露host映射查询，不表示零总线流量、零延迟或全HBM性能。

## 固定token slot与collective顺序

engram_gathered_num_tokens对非同步路径按max(potential_tokens,min(max_num_batched_tokens,max_num_seqs×(1+K)))计算固定容量；profile或uniform warmup取本地EDP片的全局DP metadata，不拿另一节点峰值当本组实际长度。hash实际N超过slot时先显式抛错，不能截断或依赖后续all-to-all补齐。

gather_engram_hashes把短rank用DEAD_ID填到统一slot；零本地token的split模式仍参加通信。exchange_engram_rows先按目标EDP组织[EDP×slot,localHeads,D]，接收为source-major，再permute回checkpoint head顺序，trim到真实N；TP最后沿head维dim1 all-gather。TP/EDP/PCP次序或head-major/source-major混用会产生形状正确而语义错的结果。

shared host模式跳过EDP hash gather和row交换，因为每rank映射共享全表的本TP shard；不能把split的dummy与collective操作不加判断搬入共享模式，也不能以dp_size=1推断物理集群只有一个DP进程。fixed-slot UT使用3/0/1/0等不等长fixture和slot越界异常，只有CPU/mock定义，本批未运行真实collective。

## 私有UVA分配与释放

HostUvaBuffer通过aclrtMallocHost请求size+65535，向上对齐64KiB地址，只注册payload并取device pointer；释放必须保留原malloc指针，不能free对齐后的地址。源码以A3/CANN9.2解释对齐动机，本批未复现该组合，DeviceOperator注册flag及全部CANN ABI仍待单独验证。

codes与scale分别按自己的row bytes决定CHUNK_ROWS=2^22内的块布局；不假定两者地址连续或相同dtype。初始化register/get-device-pointer失败时尝试清理已有资源；正常close先同步NPU，再unregister和free，成功后可重复close。若unregister已成功而free失败，所有中间阶段的可重试事务性尚未由本批证明，不能笼统称所有异常都幂等。

## POSIX共享UVA与参数别名所有权

SharedUvaBuffer由组leader创建POSIX shared memory并广播全局rank/名称，各peer附着同一host backing，但各自注册NPU映射。附着端处理resource_tracker所有权，hugepage madvise仅best effort；创建/注册错误all_gather传播，清理前同步/barrier，leader负责unlink，不能每peer各自unlink。

共享backing归shared memory，close绝不能调用aclrtFreeHost。先同步设备、注销本peer映射，再关自己的shm引用；unregister失败保留所有权便于重试，不先丢掉storage导致悬空指针。embedding.close_host_offload在buffer close成功后才移除parameter alias；参数别名与映射生命周期必须一起检查，不能看到Python对象析构就认为device不再读。

单个close成功不证明进程崩溃、barrier失败、跨rank退出和资源tracker所有组合可回收。记录name、creator/attacher、host原指针/对齐指针、device view、registered状态与剩余参数别名，先停止读者再关闭；不要把通用pinned CPU tensor当已注册UVA，也不沿用元数据wrapper的dirty-row H2D协议。

## 验收、定位与退回

先验证每head行数/offset、TP×EDP head归属、所选索引和scale语义；以小型dense参考逐项比BF16/INT8/E8M0、owned/unowned/DEAD行、不等长rank及零本地token。再核host/shared/private路线、64KiB映射、失败传播、两次close及卸载后参数alias；本卡所列UT使用fake NPU/CANN、临时checkpoint与mock collectives，未被执行，不能当硬件验证。

表查询和关闭正确后，才比较host容量、峰值HBM、读带宽、通信、TTFT/TPOT及稳态吞吐，固定并发、输入长度、capture和checkpoint。错误先恢复匹配checkpoint与完整配置、停止消费者并按实际所有权释放；不得把codes/scale强行cast、跨索引拼接、忽略slot越界或跳过unregister当修复。Native存储校验、全部Device/Host API、真实多进程清理与Agent A/B继续独立验收。

## Triton独立输入/输出head坐标

ceac固定提交的ops/triton/docs/engram.md全文36行补充lookup的接口说明：输出为[tokens×pad_heads,width]，每token只写local_heads行，输出从head0开始；head_start选择的是输入hash ID的列，不能把它再用作输出head偏移。未写的额外head padding由调用方清零，注册存储须活到消费流结束，kernel本身不注册或释放host内存。

该文档把hash/lookback描述为A3也使用的模型路线，MXFP8与无旋转fused gate分别按ENGRAM_MXFP8、ENGRAM_UNROTATED_GATE能力选择，目前说明为A5能力。来源同时明确这些调用路线不构成A3 runtime validation或CI覆盖；保留draft/空平台，不因kernel移到ops/triton就扩大支持范围。模型持有表、请求状态和辅助流，移动文件不改变表布局、算术或所有权。上述为文档与已读实现的接口核对，没有新增NPU执行证据。
