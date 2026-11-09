---
type: Guide
title: vLLM Ascend Engram 接入：历史哈希、门控与 Runner 事件
description: 接入Engram时核对配置和注册包装器、原始token历史与PCP哈希、PAD mask、rotation门控及FULL图多流事件，定位拒绝采样和退役时序错误。
aliases:
- AscendNgramHashState
- create_engram_hash_state
- engram_dead_mask
- prime_engram_v2_graph_inputs
- Engram接入
tags:
- task.implementation
- topic.model_adaptation
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/hash_state.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_engram_defaults.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_engram_multistream.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_engram_registered_v2_contract.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_engram_v2_model_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_engram_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_deepseek_v41_engram_state.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/v2/test_engram_state_hooks.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/common.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/layer.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/vl_model.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/engram_gate.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/engram_hash.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/engram_lookback.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_engram_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/engram/model_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/deepseek_v41/model.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_engram.py
  role: implementation
created_at: '2026-10-31T06:34:38Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T06:36:34Z'
---

# vLLM Ascend Engram 接入：历史哈希、门控与 Runner 事件

## 消费任务与版本边界

为新模型移植 Engram，或排查重复请求、拒绝采样、图重放后查询错误时，按配置→原始token历史→hash→表查询→mask/事件→gate→退役逐段保存证据。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取Engram的Host适配、Triton定义、注册VL包装器和所列UT；target model、platform、V1 Runner与配置仅明确选段。没有执行上游导入、测试、编译、服务或NPU。本卡整项硬件集合未知，保持draft/空平台。

Main配对Native为544f182d9f0c9bfe8bd7645525951d5e3692a542，不等于独立v0.32.0快照5df63a7203cdb9328d824a27b682e77c7b9928be。Native EngramConfig、NgramHashState与EngramLayout依赖本次未读，父类历史分配、use_slot_cache和配置完整校验不当已闭合。部署参考另见[V4.1平台与Runner边界](../models/vllm_ascend_deepseek_v41_platform_boundary.md)，表与UVA见[Engram表加载](vllm_ascend_engram_table_uva.md)。

## 配置生效与实际注册对象

engram_enabled只检查engram_layer_ids非空；模型最终has_engram还要求有效engram_config不是None。NPU platform对精确DeepseekV41ForCausalLM架构和非空层列表，可在没有CLI Engram配置时补Native EngramConfig并调用其resolver；缺CLI选项不能直接当关闭。先保存解析前后config身份、层列表、量化/存储与实际类名。

_validate_engram_config在当前model_config恰为spec.draft_model_config对象时，改核target配置；它接受的主架构仍为DeepseekV41ForCausalLM。禁止embedding_across_dp、elastic EP、TP不在1/2/4/8、PP或DCP不为1；加载格式限auto/safetensors/dummy。此处没有证明其他架构、任意CP/DP与全部CPU-offload组合可用。

patch_engram_config先find_spec，旧Native缺模块时安全不安装该覆盖；它替换模型约束及DP共享判定，DP>1或PCP>1且非elastic才会要求共享方向。它不是给旧Native补全Engram实现的shim，也不覆盖所有未来Native校验。不要删除guard来宣称适配。

models/__init__.py实际把文本架构注册到vl_model.py的AscendDeepseekV41ForCausalLM包装器，内部才是language_model。外层requires_raw_input_tokens=True，转发get_model_state_cls、prepare_engram_inputs、prepare_engram_graph_inputs、prime_engram_v2_graph_inputs、retire_engram_lookups、token_lookback_depth与supports_engram_graph_producer，并传cudagraph模式、force_dummy及token_indices。只给内部类补hook会漏真实Runner入口；注册UT用mock语言模型，不证明完整视觉预处理与多模态数值。

## 历史、slot与多模态死行

AscendNgramHashState继承Native状态，用AscendEngramSlotCache暴露SWA缓存。cache property只解包长度1的list/tuple；不存在或多平面结构返回空CPU int32，而非猜第一平面。block_size从实际绑定SWA层取得；模型构造绑定首个Engram层，另一个公开engram_cache_layer_name指向layer0，须核真实几何，不能用规划的logical block常量替代。

engram_dead_mask同时识别image_token_id和image_pad_token_id，覆盖当前token及lookback；合法历史位置判断还处理负token。lookback中的-1是未知历史哨兵，不是图像ID，不将所有负数或所有多模态编码都视为相同格式。valid_engram_token_mask在表查询前发布，不能等第一层gate时才发现PAD。

V2的_gather_lookback_kernel以persistent idx_mapping取请求槽，按corrected num_computed_tokens从新到旧读取位置cursor-1-j；未用行、负位置填-1。先clamp地址再masked读取，避免负GM地址。拒绝采样后下次执行重新取已校正device游标，不能复用上一轮乐观长度。PCP先构造全局连续请求历史和hash，再按local_token_indices选本地行，不能每rank独立拼断开的n-gram。

V1 _get_engram_device_inputs沿用父类prompt-only lookback路线，源码注释及UT以生成区-1说明可用边界；Native _prepare_lookback_token_ids/_init_model_kwargs未在本批读完。是否启用slot cache必须核对有效Native状态与实际缓存对象，不能仅由MRv1/MRv2名称判断。缺slotless历史会显式RuntimeError，不补零绕开。

## 哈希输入与PAD顺序

_engram_req_index_kernel与_hash_ids_kernel拆开请求搜索和哈希，源码解释为避开E3编译器“LLVM buffer memory released”问题；这是实现动机，未由本批复现编译故障或证明性能收益。rolling hash使用int64乘法/XOR，逐head prime取模再加vocab offset；乘法溢出语义、Native head参数必须与checkpoint匹配，不替换为Python任意精度golden后忽略宽度。

历史优先当前query chunk，其次已知lookback，再按use_slot_cache可选V1缓存，最后pad。DEAD_ID从Native导入，不假设普遍等于-1。slot-cache写kernel先于hash读取；不要删去写入或将padding请求当真实history。

target Engram入口要求query_start_loc至少有两个元素，slot-cache启用时还需block table；N=0可以返回空hash张量，但不等于跨EDP通信可直接跳过。先发布mask，再hash和table；静态图bucket使用设备valid_count屏蔽PAD，PCP选择mask与hash必须一致。idle DP的split-table路径仍构造dummy hash并参加collective；共享host模式与分片模式的通信不同，见表加载卡。

## 持久buffer、流与事件

模型以max-num-batched-tokens/最大capture容量分配长期BF16 lookup与mask buffer，清PAD尾部。SP场景先等mask ready再复制/分片，消费表分片前等table lookup；非SP可把mask等待延后到早期非Engram层之后。buffer地址稳定不证明内容属于本次请求。

multistream_engram_overlap默认工厂按FP8_OPTIMIZED能力策略开启，显式配置覆盖默认；默认策略UT不是全部SKU的性能结论。NONE/FULL路径可重叠，PIECEWISE或未知模式同步执行。只有实际FULL调用消费ExternalEvent wait/reset，不能看到配置FULL就假定当前forward在图内。

外部producer先wait主流，输入和输出record_stream，普通Event走wait_event，ExternalEvent走wait/reset。External事件按V1 batch descriptor或V2 padded token数登记；prime函数给捕获准备event与固定buffer，不能让Python临时tensor替换已捕获地址。

supports_engram_graph_producer还要求已启用Engram、overlap、slotless、无SP、PP1，且各表的dp_size=tp_size=1。该谓词不是全部物理DP/PCP、图模式、CANN和真实并发验证。图内producer使用独立aux流及普通事件，finally将主流join回来；不按外部producer逻辑预提交External等待。FULL状态保留max_num_reqs+1的query offsets及valid_count，不能把FIA padding长度当Engram有效token数。

producer抛错时join/reset，EngramModelState.finish_execution先清本步输入/退役查询，finally调用super。V1所读_model_forward的finally只释放device_metadata_executor，完整外围失败后Engram退役尚未闭合；这是待核路径，不凭局部缺调用报告已复现泄漏。一般捕获桶机制见[ACLGraph时序](../../concepts/frameworks/vllm_ascend_aclgraph_replay_lifecycle.md)，SP行轴见[SP原语](vllm_ascend_sp_primitive_contract.md)。

## gate数值与rotation加载

AscendEngram先以WKV投影将(n-1)×heads×head_dim的lookup变成(hc+1)×H；query/key归一化与BF16通道权重分开。输出gate计算归一化q·k/sqrt(H)，对绝对值至少clamp 1e-6，带符号开平方后sigmoid，再按valid mask和value形成残差并cast回目标dtype。投影仍在fused gate之外，不宣称整层融合。

load_engram_rotation_block要求完整旋转矩阵是重复的32×32 block diagonal；只读取一个block验证后按32通道块使用。缺rotation文件的辅助函数返回32维identity，但engram_rotated由get_rotation_path配置来源决定，不能因存在identity buffer就判已旋转。hidden按FP32乘旋转block的转置恢复原始basis，key转FP32但不重复逆旋转；value已经处于前向rotation空间，不再次旋转。

fused_engram_gate仅在rotation为None、设备NPU且profile有ENGRAM_UNROTATED_GATE能力时走Triton；其他情形保留Torch参考。kernel要求末维stride1，禁fp_fusion以保留计算顺序；signed sqrt含负零signbit语义。没有覆盖所有NaN/Inf、宽度、精度与硬件数值，不能以CPU reference相似代替实际NPU对照。

## Agent验收与退回条件

按同checkpoint eager无overlap保存基线，逐步加入Engram、split/shared表、PCP、拒绝采样、FULL与多流；每步核原始token/持久请求槽/corrected游标/lookback/hash/mask/有效行数、event类型/桶身份及buffer地址。测试包含请求槽重用、PAD、image、空本地rank、不同bucket和producer异常；先证明本步history与lookup一致，再比吞吐、HBM、host带宽、TTFT/TPOT。

相关UT499/308/104/636及worker228/308等包含fake NPU、临时文件、mock collectives、importorskip和AST约束，本批均未执行。它们仅提供验收设计，不证明实际注册模型、图捕获、设备kernel或分布式已通过。SWA回放生命周期继续按[回放合同](vllm_ascend_swa_bounded_replay_contract.md)检查，不能把本卡hash历史当全部prefix恢复。

历史/配置ABI不符、有效行数错位、External等待未配对或异常后未退役时，停止新增组合，恢复匹配版本和完整配置；先关闭overlap/新图路径核对基线，不吞缺历史错误或篡改DEAD_ID。确认数值和资源生命周期后才提出性能结论；本卡无NPU或Agent A/B结果。
