---
type: Guide
title: vLLM Ascend Score Encoder Cache：频率时钟、晋升阈值与双层预算
description: 解释 ScoreEncoderCacheManager 的score、promote_percentile、watermark和请求引用，区分CPU
  slots、NPU驻留、临时copy与ECCPU FIFO，限定理论成本及V1/V2消费边界。
tags:
- task.implementation
- task.debugging
- topic.multimodal
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ec_manager/score_ec_manager.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/configuration/encoder_cache_manager.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/mrv2_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/core/encoder_cache_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/ec_manager_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/configuration/encoder_cache_manager.po
  role: supporting
created_at: '2026-10-29T20:09:01Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T03:04:52Z'
---

# vLLM Ascend Score Encoder Cache：频率时钟、晋升阈值与双层预算


## 任务与范围

缓存已命中但仍搬运、CPU/NPU容量看似够却不能分配、冷clock/晋升阈值调优无预期效果，或新多模态模型初始化缺vision字段。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的Score策略与已读MRv1消费者片段；对照原生v0.32.0所需manager接口。整项硬件范围未知，保持draft/空平台，没有进行收益或精度测试。

这是Host缓存决策与metadata合同，不是已验证的所有模型最优策略。Score策略与[ECCPU共享mmap块池](../integration/vllm_ascend_eccpu_transfer_pipeline.md)有不同的管理/搬运路径，不能把它们的pin、FIFO、score或容量混合解释。

## 配置、单位与初始化假设

ScoreEncoderCacheConfig默认cpu_cache_slots=100000、max_clock=15、clock_decay_every=64、watermark=0.2、promote_percentile=0.2。cpu slots和decay interval要求正整数，max_clock可为0，bool不充当整数；两比例为[0,1]数值且排除bool/NaN。未知manager_config键会被dataclass拒绝。选manager类即启用，没有另一个enabled字段。

cpu_cache_slots与cache_size按encoder embedding槽数计，不是字节、文本token或ECCPU的ec_cpu_bytes。模型宽度/dtype不同时，同样slots不代表相同RAM/NPU用量；metadata manager本身不存tensor。CPU默认接收新计算项，NPU驻留和临时device copy另由worker执行。

实现直接读取hf_config.vision_config的hidden_size、intermediate_size与attention heads，缺num_attention_heads才退num_heads；没有为所有audio-only或任意新结构提供通用cost适配。硬件吞吐固定4e14，层数qwen3_5取27、其他取32，alpha=4H+5heads，beta按qwen3_5/其他分支估计。不是按实际NPU型号或真实encoder层数自动标定，也不能据此宣称支持所有模型。

## 分数与clock的精确口径

cal_theory_cost_storage_cost以embedding数s近似序列长度，返回layers*(alpha*s+beta)/hardware_flops；score=(freq+clock)*cal_cost。CPU候选晋升时include_clock=False，NPU驻留比较包含clock。freq不会因clock衰减而自动衰减；成本只是理论重算/槽估计，未包含实际搬运、带宽、并发和cache命中分布。

on_request每clock_decay_every次将所有NPU项clock减1至0；req_cnt增加发生在miss检查以及首次把该request_id关联到命中项时，不是严格一条外部请求只加一次。命中后该请求尚未引用该hash才增加freq，并对NPU项重置max_clock；同请求重复引用不应按每次lookup一律计热度。

cached保存hash到request ID集合，request_cached_ids另跟踪input IDs；引用是请求级集合而非每个重复媒体位置的独立计数。新增调度器处理重复hash/input时需核对释放时点，不能由同shape或同hash直接省略引用协议。

## 晋升不是只看一条阈值

should_promote先检查候选num_embeds不超NPU freeable容量，已有free足够时直接True。否则按NPU freeable项score升序，idx=int(len*promote_percentile)再夹到合法范围；CPU候选分数低于该位置才拒绝，相等可通过。它不是统计插值分位数，也不保证只淘汰比候选更低的全部项。

实际回收目标至少满足本次required_slots，同时尽量达到cache_size*watermark的空槽目标，但受当前可回收项总量限制；逐个淘汰最低分项，因此可能跨过精确槽数。should_promote会实际改变NPU状态并排npu_freed，不是只读判断。晋升把同一CacheEntry也放入NPU，并不立即删除CPU备份；不能按两字典长度求互斥占用。

## CPU分配、free与临时命中

can_allocate先拒绝单项超cpu_cache_slots，再检查encoder_compute_budget和加上num_embeds_to_schedule后的可回收容量；必要时FIFO淘汰cpu_freeable项并排cpu_freed，然后才返回True。调用它可改变状态，但不分配tensor；allocate才扣预算并建立CPU CacheEntry，freq=1/clock=0、绑定请求。

free_encoder_input移除当前input引用，最后一个request引用释放后才把存在于CPU/NPU的项加入各自freeable集合。free slots与freeable slots不同：后者包含空闲和可回收占用。evict_from_npu释放驻留并clock归0，有CPU备份时不会删除整个hash身份。

CPU命中若晋升不了，仍可返回True并发cpu_get_encoder_mm_hashes，让worker做临时device copy；“命中”不等于零H2D或永久NPU驻留。get_cached_num_encoder_embeds从实际cache项读取，不能把一次暂存误算为新增持久预算。

## metadata消费与Runner边界

get_manager_metadata一次取走并清空promoting_mm_hashes、cpu_get_encoder_mm_hashes、npu_freed和cpu_freed；get_freed_mm_hashes返回空，因为释放通过分层metadata报告。只消费通用freed列表会漏掉实际搬运动作。

已读Ascend V1 _process_encoder_cache_scheduler_output按这四表删除/晋升/临时H2D；CPU源不足时可跳过，_get_encoder_output_from_cache还保留同步H2D防御回退。异步H2D持有(source,event)队列到event完成；新encoder输出另建pinned CPU staging做non_blocking D2H。manager元数据与worker实际tensor、流/event仍须对齐，不能只据策略字典判值有效。

is_score_encoder_cache_manager用类对象is判断，不是任意子类名字都自动进入同一worker分支。当前已读消费者在MRv1，Ascend默认Runner选择/V2黑名单没有仅因Score配置就自动退V1的分支；不能把配置类成功解析等同于MRv2已消费这些动作。新Runner、与只支持MRv2的ECCPU组合需闭合实际接线与质量证据，不在此宣称普遍兼容或必现故障。

## reset与验收

manager.reset清CPU/NPU字典、引用、动作和计数，不等于已经同步物理DMA。V1 reset_encoder_cache在有临时/CPU/待完成copy时先同步设备，再清真实缓存；同步失败不能据manager计数重置就宣称tensor安全退役。

_check_invariant扫描占用+free=总容量、freeable=free+可回收占用及无引用条件，属于调试检查，不应放调度热路径。本次未执行该方法或上游测试。验收记录真实slot/字节、引用、freq/clock、理论cost、晋升/淘汰/临时copy、Runner和实际命中/质量/时延；调整参数后仍按同负载独立验证收益，不用模型化score替代硬件测量。


## 中文配置入口与新管理器接入

encoder_cache_manager.md及encoder_cache_manager.po的12条有效业务译文均有当前msgid连续匹配。在线--ec-manager-config与离线LLM(ec_manager_config=...)选择完整类路径vllm_ascend.ec_manager.score_ec_manager.ScoreEncoderCacheManager，并将五个策略参数放在manager_config内；它们不放additional_config。仅选择这个Score类即启用，给Score的manager_config另加enabled并不是关闭方法，未知键会沿ScoreEncoderCacheConfig.from_dict转成ValueError。

上游EncoderCacheManagerConfig把manager_config作为自定义manager解释的opaque字典；未指定类却带非空字典会拒绝，空字典不能证明manager已启用。get_encoder_cache_manager_obj按完全限定类名解析对象；自定义类自己实现create_manager(cache_size=..., vllm_config=...)与参数合同。所读Score.create_manager把二者交给Score构造，原生基类create_manager只把cache_size交构造；新manager继承基类不自动获得Score的schema与Runner动作消费。

中文表将clock_decay_every概括成“请求数”，实际on_request计数仍按前文命中/引用路径理解；watermark是驱逐后空闲NPU slots的目标比例，不是可突破正在引用项的硬保证。promote_percentile只决定候选比较位置，不是媒体命中概率；CPU/NPU槽位也不等于字节。保存有效类、manager_config、真实Runner、动作metadata、引用与实际tensor/流的对应证据，再比较质量和时延；此入口译文未增加硬件范围、MRv2消费证明或收益结果。
