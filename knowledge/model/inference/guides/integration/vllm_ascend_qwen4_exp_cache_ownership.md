---
type: Guide
title: vLLM Ascend Qwen4Exp 缓存所有权：QSA/GDN 共享 slab 与私有 PLE
description: 按3164的Qwen4KVCacheLayout核对main/raw/compressed一对一映射、按物理block生命周期共享K/V与GDN state、128 kernel页、内存准入及精确CPU长度同步门禁。
aliases:
- Qwen4KVCacheLayout CacheOwner SlabRegion
- can_skip_qwen_cpu_length_sync
- QSA GDN PLE shared slab
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/cache_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/model_state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/cpu_length_sync.py
  role: implementation
created_at: '2026-11-03T06:32:28Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Qwen4Exp 缓存所有权：QSA/GDN 共享 slab 与私有 PLE

版本迁移时另读[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的Qwen节，核对7d9e对release/main的不同QSA长度同步类；本卡原有cache ownership边界不等于新父类ABI全部已核验。

固定 vLLM Ascend `3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 新增程序，完整 AST 程序投影已读，不执行 upstream import、JIT、NPU、真实模型或性能测试。Native私有类与CANN二进制仍须按安装版本成对验证；保持draft、空平台，不将实验类名当全硬件支持。

## 先分所有者和生命周期，再分配地址

cache role由spec和名称共同识别：QSA .attn全注意力、.raw_key_cache circular、.compressed_key_cache压缩MLA、GDN Mamba两state、PLE Mamba单state、HiddenStateCache。没有raw role返回None沿默认planner；存在raw却缺main/compressed/GDN/PLE或混入未知spec报错。每个QSA source layer必须main/raw/compressed一对一，按实际layers编号排序，不能按group枚举位置猜对应。

main与compressed同一allocation block ID生命周期，先合并成composite group；raw circular按请求寿命单独合并。若原group混入其他role、遗漏或重复owner会报错。兼容Mamba state按spec几何与target/eagle边界分桶，每组最多QSA slot_count个，独立scheduler table复用ordinal slot。这里不同group能alias同一pool依赖**物理block同一时刻只归一个group**，不支持任意group并发占同一ID。

## slab 几何和真实页距

共享slot有r0主K/V或state页；GDN conv在r1、SSM在r2，二者沿r0物理stride，r4 raw与r5 compressed另占slab后续区域。K/V-SSM页距取最大state/KV大小并按2×128×heads×width×dtype的lcm对齐。main manager block至少覆盖最大SSM，并为128倍数；main/compressed逻辑block按group关系与ratio整除，raw capacity也按ratio对齐。

PLE和hidden每owner独立backing，不参与共享slot的计费/alias。SlabRegion.size为 `(num_blocks-1)*block_stride+logical_page_bytes`，不能用逻辑页字节乘block数替代含gap的视图span。make_slab_view检查offset/dtype对齐、stride容纳item、所需bytes在uint8 backing内；内层dense，行间保留物理gap。

QSA main再按128 kernel page交错K/V对，每对两半等宽且manager block能整分。实际K/V返回两个stride=pair_bytes的view，物理kernel页count=manager_blocks*pages_per_manager；不能先flatten再丢失descriptor stride。descriptors只能发布anchor region及共有backing几何，Runner需由相同layout重建多个不相邻region，不是descriptor一行就完整表达state。

## 准入、容量与边界

每block计费为slot_count×完整slab+PLE/hidden私有页。候选num_blocks按available_memory估算，再用多block layout复算alignment并递减直到适配，然后允许Native override。override后的超预算和零候选会进入后续构造/错误，不应据初始除法宣称所有override都被budget二次限制。最大需求按各group max_memory/page折算所需块之和乘真实pool bytes，避免alias简单相加或完全漏算private。

## optimistic CPU 长度的严格门禁

AscendQwen4ExpModelState通过MRO保留Native PLE/ngram输入准备，prepare_attn落到AscendMambaHybrid，保存FULL replay所读metadata。CPU length sync能力在target/draft cache初始化后绑定一次，先synchronize现有num_computed_tokens_stream再置skip。

允许条件含精确state/speculator类型、限定Qwen4Exp architecture、PCP=DCP=1、关闭sparse offload；MM需明确非realtime encoder；target/draft所有backend-builder精确命中allowlist，双方都存在AscendQSA、draft QSA架构和实现类正确。任何import或检查异常返回False。不是仅模型名匹配就跳D2H，也不是每batch猜允许条件；producer和consumer必须共享稳定决定。device纠正后的position/seq_lens仍保留，Host上界不变成精确长度。

Agent应逐group记录owner/role/slot、物理block表、slab offset/stride、原始dtype及private bytes；测多shape、多个group、prefix回收、target/draft寿命、页距gap、state与KV切换、准入不足和override。graph需稳定地址且内容按device协议刷新，CPU skip需同时证明所有consumer允许上界。没有本次NPU内存/图/性能验证。
