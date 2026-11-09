---
type: Guide
title: vLLM Ascend 非连续 KV 接入：物理页 stride 与混合状态视图
description: 按MRv1中英文设计核对物理页stride、K/V与Mamba backing和状态gather/scatter，分开判断逻辑块、注册传输与测试证据，避免把非连续视图当全路径零拷贝。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/non_contiguous_kv_cache.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/non_contiguous_kv_cache.po
  role: supporting
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-10-30T06:01:20Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 非连续 KV 接入：物理页 stride 与混合状态视图

## 适用范围与产物

固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的设计说明覆盖标准 Model Runner V1 的 hybrid Attention+Mamba 和受支持的纯 GQA 缓存构造。本卡限定标准 Worker/Runner 路径；310P 的独立缓存实现不由此推导支持。交付各缓存的 shape、stride、storage_offset、backing 分配及读写验证记录。

## 保持逻辑编号，核对物理步长

逻辑 block 是 scheduler 寻址单位，物理 page 是 allocator 实际预留的字节范围。page 对齐可能留下 padding，因此 block stride 应从物理页字节数和元素大小推导，不能只用逻辑 tensor 的 numel。若逻辑负载是96字节而 page为128字节，两个块之间的步长仍是128字节。

K、V、conv state、SSM state 可以是不同 backing 上的独立视图。不能从连续兼容路径的拼接图推断非连续路径也按 K→SSM→V 邻接。是否共享 backing 由 allocator 和层映射决定，block table 的逻辑编号保持原语义。

## 接入步骤

1. 读取实际 KVCacheSpec、kernel block size 和 raw allocation 形态，区分独立 K/V、合并两 lane 和 Mamba 状态。
2. 沿 `_reshape_kv_cache_tensors`、`_adjust_kv_layout` 核对 typed view；`as_strided` 的步长和 storage_offset 必须落在实际存储内。
3. 对 Mamba 状态按索引 gather 到算子友好张量，算后 scatter 回原始 strided allocation；保留请求索引、has_initial_state 和未选中行。
4. 检查 padding 不被误写、原地更新可见、K/V 层映射未变化，并核对临时 `[non-contiguous-kv-cache]` 调试日志的真实布局。

## 组合限制与验收

sparse、compressed、offload 和 connector 可能要求独立物理布局，不能因为模型是 hybrid/GQA 就启用该路径。图捕获和 PD 传输须分别验证同一视图是否可被消费。来源列出了相关 UT、状态索引和 FLA 测试定义，但每个图/connector/分布式组合仍需要模型级验收。

回退使用目标版本已有的连续兼容路径，保持模型、输入和逻辑块编号一致后比较输出、显存和复制量。路径未启用、布局超界、状态错位或输出不一致时停止收益结论。本次未运行 NPU 模型或上述测试。

## Evidence

固定非连续 KV 设计文档提供目标、构造流程、观测点和非目标；硬件 profile 用于区分标准与 compatibility Worker，不把设计说明扩大为所有平台、所有缓存后端支持。


## 平台证据待补

主设计仅限定MRv1、hybrid/GQA及物理布局，没有整项功能的A2/A3/950范围；标准Worker路径和设计中的测试计划不能替代硬件范围证据。据此撤回原平台枚举，保持draft/空平台；这是证据不足，不能解读为这些平台不支持。


## 中文非连续布局与注册/测试边界

non_contiguous_kv_cache.po的66条有效译文均匹配当前英文。逻辑块号不变并不表示实际物理stride不变；48个float16元素是96字节payload，对齐128字节后block stride为64个元素，间隔16个元素不属于逻辑view。该数字仅为示例，不能把128字节、64元素或双lane示意推广成所有模型缓存格式。

combined K/V的两lane stride和每block stride都从实际allocation推导；独立Attention与Mamba原始分配、层共享backing和连续兼容拼接图分开判断。纯GQA不需要凭空增加Mamba层；hybrid采用use_hybrid_blocks的公共分配合同，不能因为两者最终shape相同就忽略storage_offset与物理页padding。

_allocate_kv_cache_tensors负责raw backing，_reshape_kv_cache_tensors/_adjust_kv_layout构造view；gather_ssm_states与scatter_ssm_states_另完成状态搬入算子友好tensor及写回。避免整页dense staging的设计目标不等于全路径零数据搬运：Mamba gather/scatter仍有自己的读写和临时tensor。按原始backing核对has_initial_state、未选行与padding，而非只比较返回tensor数值。

FLA AscendC接口causal_conv1d_fn、causal_conv1d_update、recurrent_gated_delta_rule的测试隔离，与本地Triton状态索引、mock GDN connector、Runner布局UT各自提供不同证据。独立PyTorch golden、放在其他conftest树之外或临时debug日志，仅是设计说明/测试安排，不是本仓已经运行，更不代表所有图/PD/connector组合通过。

同一视图交给connector时，其注册地址范围、传输长度和owner还应沿[Sleep/GlobalTE生命周期](vllm_ascend_sleep_wakeup_lifecycle.md)及具体connector合同核对，不能按逻辑nbytes或storage key直接注册。该入口也不自动覆盖全部SDK、offload、压缩/稀疏缓存或310P独立实现。本卡继续draft/空平台，未执行文档中的pytest/NPU命令或读取外部FLA实现。
