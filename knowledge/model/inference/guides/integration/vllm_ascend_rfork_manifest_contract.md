---
type: Guide
title: vLLM Ascend RFork 新模型接入：兼容指纹、tensor发现与manifest验收
description: 按 RFork compatibility_fingerprint、structural_digest、sharded_dp_rank 与 manifest 接入新模型，核对共享tensor跳过、dense view、NPU format及指纹遗漏边界。 说明topk_indices_buffer作为scratch被排除，避免调度容量污染共享tensor结构身份。
tags:
- task.implementation
- task.debugging
- topic.checkpointing
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/identity.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/manifest.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/tensor_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/types.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/planner_client.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/session.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/transfer_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_lease_release.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_registration_cache_isolated.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/rfork.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/model_loader/rfork/identity.py
  role: primary
created_at: '2026-10-29T20:37:39Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:05:17Z'
aliases:
- RFork topk_indices_buffer scratch 排除
---

# vLLM Ascend RFork 新模型接入：兼容指纹、tensor发现与manifest验收

本卡的Manifest事实仍绑定其源码版本。7d9e新增主机Engram本地加载与tensor identity/data_ptr就绪账本，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的RFork节；Manifest或路径相同不能单独证明主机数据ready。


## 任务、版本与证据

为新模型/量化格式复用seed，排查同shape却不同内容、seed miss、manifest拒绝或传输后数值不符。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，原生接口对照vLLM v0.32.0 `5df63a7203cdb9328d824a27b682e77c7b9928be`；不是所有版本二进制兼容证明。整项硬件范围未知，保持draft/空平台；未导入上游模块、启动服务或执行NPU。

## 兼容身份分为配置、结构与分片

build_compatibility_fingerprint将RFORK_PROTOCOL_VERSION、model_url、model_deploy_strategy_name、revision、quantization_config digest、architecture、RoPE、kv_role与mix_placement规范化后做SHA256。当前协议版本为1。model_url是输入字符串，不等同于checkpoint内容hash；同路径换权重且缺可用revision时，指纹本身不能识别全部内容变化。

revision优先hf_config/hf_text_config的_commit_hash或commit_hash，再model_config.revision/model_revision，再HF revision；量化优先hf_quant_config，属性不可取时退HF quantization_config。architecture只取架构标识，不把整个HF配置全部纳入。RoPE显式收集theta、scaling、max_position_embeddings、rope_parameters、compress_rope_theta并把数值转float，等价整数/浮点数不必产生不同key。

_canonicalize_fingerprint_value对容器做确定性排序、转换dtype/Enum及非有限float；在其递归遍历中用active IDs拒绝环。对象优先稳定name/get_name，再公开非callable属性，最后可能只留下类型名。不是任意对象状态的完整序列化，也不是所有前置descriptor读取都由该环检测保护。字符串化dict key或不可见属性不能当作一一映射的通用承诺。

build_seed_key再加入配置指纹、structural_digest、TP/PP/EP、条件sharded_dp_rank及main/draft身份。_resolve_sharded_dp_rank在细粒度TP相关正整数配置存在，或DP>1且is_moe_model不明确为False时保守分区；未知MoE也可能分开。复制DP可共享，但不能把同shape的不同DP内容合并。空model_url/strategy/指纹/结构digest会拒绝，算法不读取每个tensor的数值。

新模型的内容决定因素若未进入上述descriptor或最终tensor结构，应调整兼容协议/strategy命名与seed更新流程。CANN/驱动/外部引擎版本、全部自定义配置并未由该函数自动完整指纹化；不能只以key相同允许任意运行环境混用。

## 发现的是live tensors，不是state_dict的等价副本

collect_transferable_tensors先收named_parameters、named_buffers，再按layout模式遍历模块公开属性。processed_layout=True扫描公开非Module属性；checkpoint模式只额外进入impl。容器递归与impl公开对象属性有访问环保护，执行函数/方法/类不作为对象内部状态扫描。

仅非meta、numel>0的NPU Tensor可传输；运行时scratch叶名topk_indices_buffer始终排除，避免scheduler容量不同改变seed结构。backend另拒绝named parameter/buffer中的非NPU实际状态；不能由这条检查推导任意隐藏对象里的CPU tensor都被统一拒绝。

_try_collect优先参数/buffer的规范名称，以(data_ptr,numel,shape,dtype,device,stride)签名去重完全相同的alias；不同view保留。相同逻辑名对应冲突tensor则报错。签名相同不构成数值校验，按data_ptr单独去重又会错误吞掉不同view。新模型的packed/derived tensors若只藏在未扫描私有字段，不能假定会自动出现在manifest中。

build_structural_digest按name排序，哈希name/shape/规范dtype/NPU format；不含tensor值、stride或物理storage容量。离设备read_npu_format可返回None，因此CPU检查可生成digest而不证明NPU注册/格式可用。log_tensor_layout_summary另有semantic/physical digests与最多3个样本，属于诊断，不是替代接收验收的另一协议。

## manifest必须先验收，再reshape和裸字节读取

validate_weight_manifest检查本地名无重复且非空；跳过的共享名必须存在远端、已从本地待传清单剔除。除这些已证实由target共享的名字外，双方名字集合必须一致，不能用任意skip列表消除缺权重。remote formats必须是覆盖整个远端名字集合的整数表，bool不充当format。

parse_weight_info只接收五字段(seed_ptr,numel,element_size,shape,dtype)，地址/numel/size为正整数且排除bool；shape为非负整数tuple/list且乘积等于numel，dtype按规范名比较。逐名核对numel、element_size、dtype与本地可读NPU format，再核对总条目/总逻辑字节。指针为正不证明远端地址所有权或可读范围；共享skip项不参与同样的逐tensorpayload验收，必须先由本地共享区域证明其归属。

shape不同但元素总数一致时，reshape_tensor_to_seed_shape通过tensor.data.view(seed_shape)尝试保持storage的metadata view，失败返回False；成功后更新本地manifest的shape/dtype。is_non_overlapping_dense_tensor按非单例维stride检查连续占用字节范围。dense是字节范围条件，不保证任意目标shape都可view；同shape也没有额外远端stride相等检查。

实际read按每name的numel*element_size，保持双方各自offset，不扩成allocator block、NZ物理padding或相邻storage，也不按地址简单合并名字。协议意图不等于所有新格式的真实byte order兼容；需要额外字节/不同解释时先改协议并在目标NPU比较输出。

## 结构漂移的两个检查不能混用

RForkPlannerClient.bind_structural_digest在已绑定值变化时抛RuntimeError；register_destination及部分发布前重新注册路径会用到它。verify_structural_digest不同：它记录漂移并返回False。当前Session._start_seed_service调用后未检查这个布尔返回，不能把注释或一条日志概括为“所有发布漂移都会被硬拒绝”。这是一条静态控制流观察，不是已复现的线上错seed。

测试定义中“拒绝发布漂移”覆盖重新绑定时的失败，不能替代上述所有分支证明。本次未运行该测试；新接线需分别覆盖REGISTERED、TRANSFERRED/READY及fallback后再发布的实际路径，并核对bound/current digest与peer session。

## 验收与相关任务

逐rank记录配置descriptor、key/结构digest、NPU format、发现/排除/alias名单、共享区域、manifest与view变更，再对同checkpoint比较冷加载和seed加载的实际值/输出。key/日志/CPU mock通过均不代替该质量证据；本卡不宣称全模型/全部存储格式已适配。

加载顺序见[处理后权重接线](vllm_ascend_rfork_processed_weight_loading.md)，失败时保留owner与注册状态见[注册内存及租约排障](../../runbooks/runtime/vllm_ascend_rfork_retained_memory_cleanup.md)，配置入口见[RFork热启动指南](../deployment/vllm_ascend_rfork_weight_warmstart.md)。


## 3164 版本补充：有效 fine-grained TP 才进入身份分片

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`，完整 unified diff 与上下文已读；不把增量阅读标为目标整文件FULL，没有执行上游、NPU、真实collective或性能验证。

rfork identity 的fine-grained TP判定由整数>0改为>1，仍排除bool。配置中某投影TP=1不再仅因显式设置就触发content-sharded DP rank身份；真正多于1的分片及原有MoE/DP条件仍需判定。不要把默认/显式1与实际跨rank切分等同，否则manifest身份或预热cache key可能分裂。该单点变化不修改其余checkpoint hash或manifest校验协议。
