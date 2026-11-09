---
type: Guide
title: vLLM Ascend fused LightningIndexer Manage Host：MTP请求池与C8工作区
description: 核对普通/C8 fused LightningIndexer Manage的T/B路由、固定TopK与21-bit源容量，区分BF16/FP16与INT8尺度合同；串接七输出、cache_slots_pool原位别名、分核及workspace布局，保留Inner
  API、Device合并/驱逐和异步完成的待验边界。 补两族Device评分/两段INT8 MMA、17至21位Source与15位slot编码、首填union、稳态驱逐和计数发布/持久映射先行的失败边界。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/fused_lightning_indexer_manage_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_host/fused_lightning_indexer_manage_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_host/fused_lightning_indexer_manage_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_host/fused_lightning_indexer_manage_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_host/fused_lightning_indexer_manage_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/fused_lightning_indexer_manage_constants.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/fused_quant_lightning_indexer_manage_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_host/fused_quant_lightning_indexer_manage_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_host/fused_quant_lightning_indexer_manage_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_host/fused_quant_lightning_indexer_manage_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_host/fused_quant_lightning_indexer_manage_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_constants.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_host/op_api/aclnn_fused_lightning_indexer_manage.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_host/op_api/aclnn_fused_lightning_indexer_manage.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_workspace.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/fused_lightning_indexer_manage.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/fused_lightning_indexer_manage_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/fused_lightning_indexer_manage_union.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/fused_lightning_indexer_manage_workspace.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/lightning_indexer_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/lightning_indexer_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/lightning_indexer_service_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/lightning_indexer_service_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_lightning_indexer_manage/op_kernel/lightning_indexer_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_service_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_service_vector.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_union.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/fused_quant_lightning_indexer_manage/op_kernel/fused_quant_lightning_indexer_manage_vector.h
  role: implementation
created_at: '2026-11-03T02:22:11Z'
updated_at: '2026-11-03T02:22:11Z'
platforms: []
aliases:
- npu_fused_lightning_indexer_manage
- npu_fused_quant_lightning_indexer_manage
- FusedLightningIndexerManageTiling
- FusedQuantLightningIndexerManageTiling
- MtpC8Workspace
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend fused LightningIndexer Manage Host：MTP请求池与C8工作区

## 任务与边界

新稀疏模型接入MTP热缓存、迁移INT8 indexer或诊断LIM内存预算时，把选择、请求池映射和下游搬运作为同一调用协议核对。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取两族Torch、OpDef/推形、tiling、常量与C8共享workspace，另含CMake和普通public wrapper，共17来源2012行。源码只作数据，未运行上游、UT、编译、JIT或NPU；保持draft、空平台。

[既有Sparse KV offload卡](vllm_ascend_sparse_layerwise_offload.md)保留P/D部署、MemFabric注册内存、A3/950和CP/PP边界及Python owner。本卡补其所调用LIM的Host，不由两个SoC允许项解除部署限制。它也不同于[QLI V2](vllm_ascend_quant_lightning_indexer_v2_host_contract.md)的candidate模式和1024-word metadata，不应因都返回TopK2048而互换入口。

## 两条入口共享几何，dtype与scale分别核对

| 项目 | 普通LIM | C8 LIM |
|---|---|---|
| query/index_key_cache | 两者与index_weights同为FP16或BF16 | 两者INT8 |
| index_weights | 与Q/K相同dtype | BF16 |
| query_dequant_scale | FP32 `[T,H]` | FP16 `[T,H]` |
| index_key_dequant_scale | FP32 `[blocks,128,1]` | FP16 `[blocks,128,1]` |
| 元数据及全部输出 | INT32 | INT32 |

query固定`[T,H,128]`，H为32或64；K为`[blocks,128,1,128]`且blocks正，weights为`[T,H]`。block_table为非空`[B,max_blocks]`，max_blocks不超过16384。B为请求数，T为请求的query routes总数，必须`B<=T<=14B`；不能把T等同B，或仅看到这条总量检查便断定每请求前缀差都在1..14。

两组actual_seq_lengths、offload_seq_lengths_key、num_cache_tokens、request_state与req_pool_entries都为`[B]`。C8 adapter注释把query长度定义为routes前缀和，request_state常量为-3普通、-2首次decode、-1稳定态；所读Host只检查shape/dtype，没有读取这些值证明前缀单调、末值T、状态转移合法或长度不超过页容量。

Torch明确要求19个调用tensor都连续、在同一NPU，query设备为PrivateUse1；不能把registered CPU KV视图直接传入LIM。CPU main KV是下游Copy-SFA的另一输入，indexer K及LIM请求池仍在NPU。FP8/MXFP8、更一般H或D、任意page stride都没有由该入口开放；普通分支仍要求FP32尺度，不能因Q未量化就省略或换dtype。

## 七输出与原位池不是纯TopK函数

caller预分配并向void Torch入口传入输出：

| 输出 | shape | 核对单位 |
|---|---|---|
| topk_src_ids / topk_dst_slots | `[T,1,2048]` | 每route的源ID和目标热槽 |
| topk_miss_counts | `[T]` | 每route计数 |
| miss_src_ids / miss_dst_slots | `[B,32768]` | 请求级合并miss容量 |
| miss_counts | `[B]` | 请求级计数 |
| cache_slots_pool_out | 与pool相同 | 持久请求池映射 |

cache_slots_pool是`[POOL,max_blocks*128]`且POOL正；Host将该宽度与block_table容量对齐，限制源容量不超过`2^21` token，与注释的21-bit source格式一致。这是容量与编码预算，不证明输出ID可直接当byte offset、物理block ID或另一算子的token ID。Device的精确编码、排序、tie、去重和驱逐逻辑未读，不从名称推导它们已正确。

Torch向最终cache_slots_pool_out再次传入同一个cache_slots_pool，明确保留输入/输出别名并原位更新池；不能用另一个同shape临时输出替代后就继续消费旧池。topk/miss各计数与对应列表、request pool entry和当前batch属于一组身份，不能只compact query或只复制TopK而保留错请求的池索引。

常量中MAX_CACHE_TOKENS为32640、MATURE_UNION_MAX_ROUTES为4，而Torch/Host总routes允许14。它们是不同用途的声明，未读Device消费前不能把4当整个入口上限，也不能据声明推断num_cache_tokens的任意值会在Host被拒绝。shape检查不覆盖pool entry范围、页ID、计数溢出、padding源-1或每条状态数据的语义。

## GE推形与public API不能替代执行证据

两族infer只从query取T、block_table取B、pool取原shape，生成七个INT32输出。infer先检查三组rank，未运行全部Host门禁、TopK计算或请求池更新；动态shape/rank注册也不保证同一capture可以任意换shape、pool backing和长度数据。

普通public wrapper的阶段一原样转发20个tensor给aclnnInnerFusedLightningIndexerManageGetWorkspaceSize，阶段二把workspace/executor/stream转给Inner执行函数；该44行wrapper没有额外Contiguous、值校验、同步或错误恢复。Inner/generated实现未读，不能把const aclTensor指针签名解释成pool内容不会修改，也不能据wrapper返回推导跨stream依赖已经建立。

普通CMake注册aclnn_inner，C8注册aclnn；本卡没有展开生成工具、实际链接产物或外部executor。两路都在配置中关闭自动同步并保留手写pipe同步相关编译选项，C8注释特别要求禁用membar removal。不能任意删除这些选项后仍把Host源码相同当二进制行为等价；选项存在也不证明Device同步已验证。

## 当前Host平台与调度路径

两条tiling都拒绝非ASCEND910B/ASCEND910_93，要求AIC/AIV数量非0，workspace和raw tiling输出有效。OpDef对应注册910b/910_93。此版本没有950 Host允许分支，不从QLI V2的950支持推导LIM也支持，也不把允许项当实机通过。

正式TilingFor入口均以mtp=true构造tiler，因此读取七输出、分配MTP工作区；类里保留的非MTP四输出/不同预算分支不等于此导出已开放旧ABI。排障时先核当前Torch19个tensor、GE13输入/7输出和生成API的对应顺序，不能把旧四输出调用塞入同名新符号。

调度取决于B而非单独T：`B%AIC==0`选AUTO=2，否则BALANCED=1。前者预选min(B,AIC)个core，后者预选AIC；请求AIV不超过两倍预选core，再用CalcTschBlockDim取得最终blockDim。写入tiling的usedCoreNum是最终blockDim，不能把前一步预选core数或机器总AIC直接代入kernel workspace偏移。

## 普通与C8的workspace不能共用公式

令C为最终blockDim，H为query heads，S为pool源容量。普通MTP基础打分缓冲为`C*(8H)*512*4*2`字节，scoreStride将S向512对齐；C8先归约head，其打分缓冲为`C*8*2048*4*2`，另加`C*(8H)*16*2`字节的折叠weights/query-scale缓冲，scoreStride向2048对齐。两路输入输出shape相同不代表workspace一样，不能拿BF16遗留512常量覆盖C8共享header。

随后两路都计入每核head/tail的8行TopK value/index缓冲、16项INT64参数，以及每请求两块8192元素FP32 pair区；再接T行score、每T行8个FP32 threshold和8个INT32 route count，并加平台libapi workspace。内存随页表容量S和T增长，而非只随实际有效seq_len；延长max_blocks可能明显增大预算，即使实际请求短。

C8的MtpC8Workspace把S2_BASE_SIZE=2048与Pair0/Pair1/Score/Threshold/RouteCount偏移放在共享header，该头供两侧共享，已核Host直接include；本卡没有展开Device初始化调用。注释中的历史微秒/chunk对比是作者背景，不是本卡测量。使用这些offset时还要核对真实kernel采用的workspace基址及当前blockDim/H/B/T/S，不能未经确认把整个外部workspace或张量元素下标直接代入字节偏移。

所读Host先将多个维度转uint32，部分普通基础缓冲乘法也在该宽度完成，没有展示对所有超大geometry乘法的完整溢出防护。不要由API的int64 shape承诺任意大batch/page预算安全；先保存实际workspace、tiling与分配，量化较省K字节不代表所有中间FP32预算同比缩小。

## 新模型验收与剩余闭包

先确认请求pool和indexer K/scales的真实owner/地址、routes前缀及每请求状态，维持七输出和原位池的一致身份；再让下游Copy-SFA按miss计数搬运注册CPU主KV并消费目的热槽。LIM Host本身没有完成CPU main KV传输，pool规划成功不等于miss数据已就位；具体Python写回/step复用遵循既有offload卡，不在这里改其部署范围。

之后按普通与C8分别比较参考TopK/映射、不同MTP routes和首次/稳定/非offload状态，观测临时内存、选择、搬运和完整Attention延迟。真正的Device评分、union、命中/驱逐、手写同步、全空行和数值误差，以及真实graph地址/stream依赖仍未读取或运行；本卡不声称完整Operator闭包、性能改善或所有硬件/模型适配成功。

## Device补全：读取范围与共同阶段

上述“Device未读”是本卡最初Host批的边界；本节补完队列余21源（两族entry、完整union、cube/vector/kernel/workspace和README），以完整去注释程序投影及与已读QLI、普通/C8同族的全部程序差异覆盖实现，不把这种阅读称raw全文或实机验证。未变Host合同仍成立，下面收窄此前未知的编码/管理细节。普通与C8均在__CCE_AICORE__=310/200或__DAV_310R6__宏下不执行主体；不能由注册符号存在推定这些目标可用。

两族先PrepareNonOffloadRows，AIV全局同步后执行评分/TopK，再完成跨核LD归并，AIV再次同步，偶数AIV Reset pipe后按请求负责union/池更新。全为-3的owner分片可只发布零计数；混合分片仍逐请求处理。跨核事件与全局屏障是手写协议，不能仅以最终数值一样删除。独立cacheSlotsOut参数未被entry作为另一路目标消费，实际持续改输入池，保持原位别名。

- 非卸载-3：每轮把对应整个pool源容量恢复identity，评分按各route因果可见长度，输出score序TopK；短于2048的后缀填-1，目的slot等于source，request/route miss计数0。
- 首次卸载-2：在稳定prefix内选TopK，忽略旧驻留映射，合并所有route的有序source去重union，补最小未选source直到C个，再清整行INT32_MIN、重建source→[0,C)；请求miss=C、每route miss=2048。最多8路可局部合并，>8分两组并借GM列表合并；不是只支持4路。
- 稳态-1：评分基于稳定prefix；每route先按source序重排miss前缀/hit后缀，union只去重miss，回收未受任一路TopK保护的驻留slot，写入池映射并发布请求/route计数。identity→稳态转换会在特定probe检测到旧identity后清C以后的源映射，正常稳态不每次清整行。

有效请求必须独占pool行且生命周期内稳定，两个请求同row不会由内部按请求分核自动串行化。ValidateOffloadRequest还要求L/C按128对齐、L>=2048、C<=L、L不超过所有route共同可见的完整页prefix；L<=Q*2048时C=L，否则C>=Q*2048且<=32640。输入K页表物理页合法与分配容量、末项query前缀=T仍是caller合同，局部guard不组成完整内存安全证明。

## 两种评分流水和长ID编码

普通分支明确忽略两个必选FP32 dequant scale的值：Q/K的FP16/BF16 MMA输出FP32并ReLU，再以同dtype weights乘和跨head归约，按512 token块保留TopK。H按16分组，s1按8行、两AIV分route；长序列可跨核拆S2，先写部分TopK及16项参数，再由LD按实际分段归并。两路后续管理使用相同的完整FP32 score scratch和route阈值，不把局部TopK当全序列最终阈值。

C8先把FP16 query scale与BF16 weight转FP32相乘，再CAST_RINT为FP16并广播到weight workspace；INT8 QK得到INT32，经fixpipe DEQF16固定2^-10和ReLU落为FP16分数，第二次MMA用折叠weight聚合head得到FP32，最后乘按同一block table gather的FP16 key scale。其S2块2048，排序缓存深度跟S2而变，不能套普通512×四块的常量。每次首块前新增Vec0→Cube和Cube→Vec0双缓冲事件，尾部有相应等待；scale/weights地址与数据刷新属于图生命周期。

这些舍入点意味着C8不是“先精确FP32反量化再普通公式”。同分TopK顺序、长ID和阈值附近数值必须单独验；README的C8测试也按集合比较TopK，不能把未执行的该说明升级为数值或排序已验证。普通Scale占位与C8真实消费必须在调用层区分。

payload低17位存source、其上15位存slot，32767为无效slot；source>2^17时把高4位嵌入FP32 score低4位，扩至21位，出接口再还原完整INT32 source。slot与ID编码不是裸FP32数值cast，修改score低位会改变细小分数/tie的次序；不可在不了解标记阶段时重用score给其他算子。池非驻留标记是INT32_MIN，输出无效项为-1，两者不能混同。

## Union、驱逐与失败之后

四路且queryStart=batch*4走成熟MrgSort4；其余最多14路走广义分支，按miss数选择小排序/有序多路merge、紧凑occurrence或逐route查回。局部路由容量不足或union超过8192会转generic算法；这些fallback改变调度/开销，不是丢弃route。路由source排序分miss/hit两段，有序前提是RouteContains二分和union成立的基础。

驱逐按512-source chunk扫描，起点由length与pool row hash决定；候选必须驻留且低于所有route TopK阈值，按聚合分数构造回收候选。<=512 miss时可合并保留候选并提前结束；更大时分chunk回收；不足时专门找与阈值相等且不在任一路TopK中的驻留source。故不是精确全局LRU，也不应承诺每次选择全局最小score集合。长ID路径先校验一批候选再写池；短路径可能边校验边写。

PublishSafeFailure填TopK=-1并置相关计数0，但它不是整个调用的回滚。generic稳态若已更新部分victim后发现不足，或prepare阶段已做identity/后缀清理，旧pool可能已经变化；广义分支还会以实际updated数量发布而非无条件保证每个miss已获slot。因此README“非法值不破坏pool”不能解读成所有内部失败原子性。上层必须提前校验pool双射/容量/状态和页表，发现不足或-1时撤销本步消费并重建，而不是仅将计数0当作全命中。

池映射与计数发布只完成计划，DRAM主KV尚未保证已写HBM；下游[融合Copy-SFA](vllm_ascend_sfa_selection_execution_contract.md)或框架搬运还需完成真实数据更新。调优应分开量化评分、TopK/LD、union/驱逐、pool清理、实际传输与attention，用长ID边界、14路、全命中、阈值全同、部分失败及跨步身份验正确性后再度量。本次未执行README所列NPU测试或性能配置，A2“上板验证中”和A3来源声明均保留来源边界。
