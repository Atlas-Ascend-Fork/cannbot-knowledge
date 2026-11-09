---
type: Guide
title: "vLLM Ascend DSpark上下文接入：捕获边界、前缀身份与P端交接（DSparkPrefixKeys）"
description: "沿 get_dspark_aux_layer_ids、DSparkPrefixKeys 和 DSparkPrefixCache 核对checkpoint到capture boundary的转换、target/draft配对身份、独立草稿页、原子发布与读租约；区分共享配置helper、SFA纯P角色和恢复前缀后的投影/传输次序。"
aliases:
- DSparkPrefixKeys
- DSparkPrefixCache
- get_dspark_aux_layer_ids
- get_pd_dspark_aux_layer_ids
- find_dspark_prefix_connector
- uses_sfa_dspark_kv_transfer
tags:
- task.implementation
- task.debugging
- task.optimization
- topic.model_adaptation
- topic.speculative_decoding
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/dspark_prefix_cache.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/dspark_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/ascend_multi_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_dspark_aux_layer_ids.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ascend_store/test_dspark_prefix_cache.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_dspark_pd_context.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kv_offload/test_dspark_prefill_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/spec_decode/eagle/eagle3_utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/sfa_pd_rd2h/dspark_context.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/ascend_store_connector.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_scheduler.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T10:59:25Z'
updated_at: '2026-11-04T03:49:24Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend DSpark上下文接入：捕获边界、前缀身份与P端交接

## 接入任务与版本范围

接入新DSpark模型或外部前缀复用时，先建立checkpoint tap、target捕获边界、真实draft Context KV、持久对象身份及P端交接的对应关系。目标KV命中、辅助特征维度正确、对象存在或发送函数返回，都不能单独证明跳过的草稿上下文已可消费。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2；独立Native参考5df63a7203cdb9328d824a27b682e77c7b9928be。Main实际配对pin为544f182d9f0c9bfe8bd7645525951d5e3692a542，不能把独立5df当作该安装环境或ABI已验收。本卡保持draft、空平台及framework=vllm部分Scope，没有模型、NPU、图、数值、性能或Agent A/B结果。

14个选定范围为9份全文、5份有界：Main prefix cache284行、共享helper40行、MultiConnector284行及四份UT71/431/671/106行；Native辅助层helper137行与Main pin1行全文。有界部分仅为dspark_context1–306、Store connector145–205、Pool worker1182–1248、Pool scheduler373–432及Runner298–324/737–767。引用共享文件不表示整文件、接收/取消协议、SDK或全部硬件语义已闭合。

## 配置中的层号与实际capture boundary

get_dspark_aux_layer_ids在method精确为dspark时只调用checkpoint resolver；没有解析结果便返回空tuple，不回退读取connector的显式P选项。其他方法或target-only配置从kv_connector_extra_config.dspark_aux_hidden_state_layer_ids读取已经转换的边界，不再加1。返回空值只是该配置入口没有提供边界，不是模型已具备正确捕获协议。

独立Native的get_eagle3_aux_layers_from_config直接读取draft_model_config.hf_config，并按下表依次寻找非空值。它没有通用地解包所有复合text_config；实际传入对象和最终字段必须留证。

| 优先级与字段 | 解析动作 |
| --- | --- |
| eagle_aux_hidden_state_layer_ids | 已有边界，原样使用。 |
| dflash_config.target_layer_ids | 每项加1。 |
| dspark_target_layer_ids | model_type精确为deepseek_v41时原样；其他情况每项加1。 |
| target_layer_ids | 每项加1。 |
| dflash_config.layer_ids，再eagle_config.layer_ids | 作为已有边界使用。 |

共享helper校验实际解析出的序列为非空list/tuple、严格int（排除bool）、升序唯一且位于[0,num_hidden_layers]，再返回tuple。原始checkpoint字段被resolver忽略或缺失时可能先得到空结果，因此不能把后置校验描述成全部原始schema的完整验证；配置接受0和末边界也不证明每个target实现都能实际捕获它们。

V4.1的上述Native解析规则与[MRv1模型指南](vllm_ascend_v41_dspark_adapter.md)中的父类优先、fallback解包再加1属于不同调用路线，不能给全部V4.1字段再加一次1。Main UT定义用GLM raw层[1,21,37,57,73]和V4.1边界[2,22,38,58,74]表达相同捕获结果，本次未执行测试。

边界ID还不能决定materialized/raw特征格式。[Kimi](vllm_ascend_kimi_dspark_adaptation.md)、[GLM](vllm_ascend_glm_mla_dspark_adapter.md)、[V4](vllm_ascend_dsv4_dspark_adapter.md)各自保留训练tap与投影合同；适配Agent应逐项比对顺序、捕获时刻和特征格式，不能只比较拼接宽度。

## P角色限制由具体backend施加

共享helper本身不检查PD角色、CP、eager或APC。uses_sfa_dspark_kv_transfer另要求method=dspark、存在producer或consumer角色，并在connector树中找到精确名称SfaRemoteD2HConnector；MultiConnector按子配置递归查找。它不是对每个远端、子角色、网络或加载状态的完整验收。

get_pd_dspark_aux_layer_ids只对该backend的纯producer启用P端生成；consumer、kv_both或未选中的backend返回空tuple，不套用后续P限制。启用后要求PCP×DCP=1、enforce_eager=True、本地enable_prefix_caching=False，并从draft checkpoint解析到非空边界。这条P路径必须加载真实drafter，先在本地写draft KV；显式配置target-only捕获选项不能替代它。

本地APC关闭与paired AscendStore外部前缀复用是两个开关。不能把SFA P限制推广到[通用PD/D2RH](vllm_ascend_pd_transfer_lifecycle.md)或所有DSpark backend，也不能因共享helper返回了ID就认定P写入路径已启用。

AscendMultiConnector对纯SFA DSpark P尝试选择paired store；没有provider时，get_num_new_matched_tokens返回0，阻止target-only命中跳过缺失的draft上下文。最多允许一个provider，并把父配置传给它；只有该provider的联合命中参与此路由，不能随意采用另一个child的target命中。

Store的configure_dspark_prefix_cache方法自身要求use_layerwise、data plane为gva、角色为kv_producer及DSpark keys；它的局部guard与父MultiConnector的自动选择条件不同。配置时还给scheduler设置use_eagle=True，注释意图是保留最后prompt块用于target/aux重算；实际恢复范围仍以scheduler元数据为准。find_dspark_prefix_connector递归配对子connector及当步metadata，子数量不对齐或出现多个启用的store会失败。

## 持久前缀身份与全部rank的共同命中

DSparkPrefixKeys要求已加载的draft_model_config。identity以排序JSON求SHA256，包含target和draft各自的model路径、revision、code_revision、dtype、quantization、HF config，以及draft宽度、aux边界、TP/PP、block_size和prefix_match_unit。

它是配置身份，不是实际权重字节checksum或插件/Native版本兼容证明。相同路径和配置下原地换权重可能保持identity；升级、热加载及布局变化需要明确的隔离/失效策略，不能仅凭digest相同继续读取旧对象。

key形如dspark-prefix-v1@identity@pp最后stage@tp当前rank@block_hash。草稿companion对象只在最终PP stage，但命中检查枚举全部TP rank；普通target组还要合取target的stage/head keys，draft-only组则使用companion keys。共享block ID不等于共享物理缓存，也不能用某一个rank或target组的可读替代整体命中。

key不含DP独占ID，多个DP writer可能竞争同一前缀；碰撞处理必须保留其他writer的所有权。[通用KV Pool](../deployment/vllm_ascend_kv_pool_backends.md)的namespace/布局规则继续适用，这些对象也不是[ECCPU encoder输出缓存](vllm_ascend_eccpu_transfer_pipeline.md)。

## 注册独立draft页与地址生命周期

Pool worker把实际加载的draft层从target视图中分开，最终PP stage注册DSparkPrefixCache。register要求cache名字与layer-group映射集合一致、num_blocks为正、各组逻辑block size一致；每个实际draft层必须有非空页。每个tensor的内层kernel页连续，首轴能按逻辑块数整除，scale×kernel页token数覆盖一个逻辑块；scale>1时还要求kernel页相邻。

对象按排序后的层名及其组件拼接，page_bytes为各组件逻辑页字节和。注册region的跨度是(num_blocks-1)×stride+size，外层带间隔时不等于numel字节。不能把物理kernel页、逻辑token block和target scratch buffer当成同一分配单位。

初始化后要求backend.store提供callable batch_write_finish作为原子发布接口；方法存在不证明实际SDK、返回码或设备完成语义。缓存对象保存tensor引用和注册时的裸地址，真实storage更换或重新分配后要重新注册，引用仍活着也不代表它自动指向新缓冲。

## 保存：只发布自己拥有的完整页

save只保存prompt范围内已具hash的完整块，不发布部分尾块；readability探测必须返回等长的严格bool列表。已有readable对象直接跳过，即使探测后被逐出，本次save也不重新分配；这不证明随后restore仍会命中。

对缺失对象batch_alloc后，只有正整数且小于SSD命中sentinel的GVA属于本writer。非正碰撞地址需确认对象存在，可能仍由另一个writer处于WRITING；不得覆盖、发布或释放其租约。SSD sentinel也不是可写的本地memory GVA，混合结果只复制自己拥有的页。

当前顺序为copy_fn方向0→batch_write_finish(status=0)→释放自己的写lease。copy或发布异常时，仅对已分配给自己的keys提交status=-1，再在finally释放它们；没有获得所有权的对象保持不动。代码以copy_fn返回0决定是否继续发布，真实传输同步、原子可见性和故障持久性仍需所选SDK/NPU证据。

## 恢复：scheduler命中、读lease和地址刷新

非零restore offset必须为完整哈希块，且不超prompt范围，并要求load_spec.can_load及kvpool_cached_tokens>=offset；零offset可直接返回，不能据此证明实际读取命中。helper在num_prompt_tokens缺失时回退target_token_len，新框架需保证这些字段确实代表可用prompt上下文。

每批最多128个key，lease TTL为300000毫秒。先以for_load=True查询/rewarm元数据，再取得读lease；成功后重新查询GVA，按每组当前block表复制（方向1），finally只释放真正取得成功状态的租约。不能在lease后再触发可能移动对象的rewarm，也不能复用lease前的旧地址。

每对象需有匹配page_bytes和可读地址，每组block表要覆盖实际请求范围。相同字节数并不验证组件dtype、顺序、权重及训练tap语义。部分lease响应、失败或缺项会停止复制，只释放已成功取得的keys，不释放其他owner的租约。

## P端前缀恢复、后缀投影与发送

Runner只在已启用P边界且最终PP rank时进入该路径，并配对当步PD与prefix metadata。辅助特征拼接为BF16二维[tokens,aux_count×hidden_size]；只投影prompt范围，超出prompt的target verify行不作为context。数量/宽度guard仍不能代替实际有序tap ID与训练/远端schema逐项一致。

第一次带非零offset的suffix prefill，必须先restore完整draft prefix到精确offset，再投影后缀；只有target命中、没有prefix provider或恢复长度不足时，连续性检查在投影前失败。后续chunk校验allocation generation和offset连续性，按各draft组真实block size取当前已分配页，最多每64个token调用initialize_local_context。

每个chunk完成投影后先save draft prefix，再更新本地progress；仅到prompt终点才调用send_dspark_draft_kv并移除progress。prefix保存失败不能继续发布PD发送，finished请求也会清理旧progress。来源UT定义了restore→project→save→send和跨chunk只restore一次的顺序。

Store的save包装器在cache或请求metadata缺失时也可能直接返回而不调用cache.save；正常返回不能代替实际持久化证据。验收时同时核对完整层注册、当步请求metadata、写入/发布返回码及后续联合命中。

此处只闭合P端发出前的就绪条件，send调用不能替代D读取、ACK、取消或接收代际隔离证明。缓存组/slot与有效KV长度仍由[既有DSpark状态诊断](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)维护，块采样与Markov反馈见[模型接口合同](vllm_ascend_dspark_block_markov_contract.md)。

## Agent验收与性能归因

保存两个checkpoint及revision、实际resolver/Runner、原始字段与解析后边界、特征格式、真实draft层名/组、缓存地址、identity、rank keys、scheduler hit extent及allocation generation。先覆盖无前缀、完整/部分命中、chunked suffix、错误tap、独立组重映射、缺页、lease部分失败、并发writer和SSD rewarm，再验证真实设备数值及PD完成。

所引UT使用SimpleNamespace、mock和CPU字节backend表达配置、独立页、发布/lease与调用次序；本次没有执行它们。完整接收/取消、任意模型布局、图、外部Memcache和NPU并发仍待验收，不将测试定义或方法存在登记为verified。

性能分别记录target与draft共同命中、传输字节、lease/RPC、后缀Context KV投影、保留末块重算及端到端TTFT/TPOT。热命中仍可能搬页和投影，不按接受率或对象存在推导固定收益。身份、地址、tap或完成边界不符时停止消费该前缀，保留错误与返回码并恢复完整匹配配置；不要用扩大offset或静默跳过恢复来掩盖缺失context。
