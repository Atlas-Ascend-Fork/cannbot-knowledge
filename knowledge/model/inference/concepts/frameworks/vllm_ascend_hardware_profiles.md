---
type: Concept
title: vLLM Ascend 硬件能力契约：HardwareProfile、950DT 与 950PR 产品边界
description: '说明A2、A3、310P、950的身份、实现族与策略，区分安装表950DT产品声明和950PR待核对边界，沿构建目标、SoC与实际消费者验证能力。 补充孤儿 310p.po 的 DUO、Atlas 200I Pro、event-id 图数量与显式 mask 二次方内存边界。 说明 310P 的 max_model_len、FP16 mask
  到 FRACTAL_NZ 的 OOM，2×L² 元素存储与 NZ 转换、512MiB、2GiB、8GiB 原始预算；Eco-Tech W8A8SC 的 8B、14B、32B，DUO 的 triton、triton-ascend 旧卸载，Atlas200IPro 的 root/host page cache 与 HBM，以及 #7394 的 Qwen3.5、Qwen3.6
  预览边界。'
tags:
- task.design
- topic.architecture
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device/test_hardware_profile.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device/test_device_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/getting_started/installation/supported_hardware.inc.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/getting_started/installation/supported_hardware.inc.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/hardwares/310p.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/__init__.py
  role: supporting
created_at: '2026-10-29T08:26:22Z'
updated_at: '2026-11-03T05:09:40Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 硬件能力契约：HardwareProfile、950DT 与 950PR 产品边界

## 适用范围

本文描述 vLLM Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的设备抽象。上游枚举 `A5` 在本知识仓归入 `950`；它是该实现的命名，不表示任意后续 950 产品都已运行验证。本文只解释软件选路契约，不提供各模型在四个平台上的功能或性能保证。

## 身份、能力和行为分开判断

设备包先把构建目标或运行时 SoC 映射为内部 `AscendDeviceType`，再选择不可变的 `HardwareProfile`。业务代码通过 `get_current_hardware_profile()` 读取三个不同层次的信息：

| 层次 | 代表字段 | 含义 |
| --- | --- | --- |
| 能力 | `supports(HardwareCapability.X)` | 某个明确的软件栈、算子 ABI 或运行时契约可供使用；调用方仍须检查模型、shape、dtype、配置和运行条件 |
| 策略/模式 | `weight_layout_policy`、`moe_comm_policy`、`cpu_binding_mode` | 选择默认行为或选路规则；不是性能结论 |
| 实现族 | `attention_backend_family`、`quantization_backend_family`、`device_adaptor_family` | 选择接口背后的实现系列；不证明该系列支持所有模型 |

能力位的缺失只说明该契约不可直接使用，消费者应按自己的实现回退或拒绝；不能由一个能力位推导整个硬件不支持相关技术。部分历史能力成员实际表示默认行为或实现选择，阅读时须保留其注释限定。

## 四个平台的选路差异

以下是固定源码中的策略，不是推荐的部署参数：

| 项目 | A2 | A3 | 310P | 950 / 上游 A5 |
| --- | --- | --- | --- | --- |
| Attention 与量化实现族 | STANDARD | STANDARD | COMPATIBILITY | STANDARD |
| 默认 Worker | `NPUWorker` | `NPUWorker` | `NPUWorker310` | `NPUWorker` |
| 设备适配族 | STANDARD | STANDARD | COMPATIBILITY | FP8_OPTIMIZED |
| CPU 绑定模式 | TOPO_AFFINITY | GLOBAL_SLICE | TOPO_AFFINITY | TOPO_AFFINITY |
| 设备寻址模式 | DIRECT | DUAL_CHIP_CARD | DIRECT | DIRECT |
| 权重布局策略 | CONFIGURABLE | CONFIGURABLE | FORCE_NZ | CONFIGURABLE |
| MoE 通信策略 | CAPACITY_AND_EXPERT_DENSITY | FUSED_OR_CAPACITY | ALLGATHER | CAPACITY_AND_WORLD_SIZE |

例如，A2/A3/310P 含有 `RUNTIME_CUSTOM_OPS`，该版本的 A5 profile 不含此能力；A5 却含有 `AUTO_ENABLE_CUSTOM_OPS`，310P 则没有后者。前者描述导入并注册编译扩展的契约，后者是平台配置时把 custom-op 列表设为 `all` 的默认策略，二者不能互相替代。不能由 A5 的默认列表设置推导编译扩展已可用，也不能由 310P 没有默认全开推导它不能注册扩展。

`NPUGRAPH_EX` 在 A2/A3/A5 profile 中存在、在 310P 中缺失；这只限定该图优化契约，不等于所有图执行方式的通用支持声明。类似地，A5 的 `FP8_ATTENTION` 只覆盖相应 Attention KV ABI，不能外推所有 FP8 算子。

## 选路消费者与前置条件

`NPUPlatform._select_attn_backend_cls` 先检查 FA3/FlashAttn 的专属条件，再区分 compatibility、PCP 和普通映射。310P compatibility map 目前只明确列出普通非 MLA、非稀疏分支，并有默认回落；返回了某个后端类不证明未登记的 MLA/SFA 模型语义正确。

`_setup_worker_and_scheduler` 仅在 `worker_cls="auto"` 时使用 profile 的默认 Worker；Xlite 启用且具备对应标准 patch 契约时有单独 Worker。用户显式 Worker 和其他模型/配置检查仍需另外核对，不能只从上表推断最终执行类。

新增适配时先确定需要的是能力、策略还是实现族，再查实际消费者。先检查能力，再保留 shape/dtype/模型和组合限制；不要把一个平台名判断改成过宽的“新一代硬件”判断。

## 构建目标与运行时校验

`get_device_config()` 从 `_build_info.__device_type__` 读取构建身份；旧包回退到 `__soc_version__`，缺少旧字段时存在 A2 默认值。这条路径有缓存且 import 时不探测 torch-npu。它反映安装包目标，不能当作独立的物理设备探测。

Worker 初始化时的 `check_ascend_device_type()` 再读取 `torch_npu.npu.get_soc_version()`，把运行时身份与构建身份比较，不一致抛错。未知 SoC 会被拒绝，不能仅改构建标签绕过校验。

## 验证和失效边界

源码中的 UT 对四个平台的策略、完整能力集合、当前 profile 身份以及未知身份拒绝行为作了断言；另有 CPU Tensor 上 `torch.compile(..., backend="eager", fullgraph=True)` 的 tracing 用例。设备配置 UT 使用 mock 覆盖不在 import 期探测运行时，以及构建/运行时不匹配。

这些是测试定义证据，本次没有执行上游 UT、NPU 推理或性能测试。实际适配还需验证所选类、有效配置、正确性和回退。升级来源后应重新核对能力集合与消费者，不从历史表推导新版本支持范围。

## Evidence

- `hardware_profile.py`：`HardwareCapability`、各策略枚举、`HardwareProfile` 和四套 profile 定义。
- `hardware.py`、`device_config.py`：SoC 映射、构建身份、缓存和运行时比较。
- `platform.py`：`_select_attn_backend_cls`、`_setup_worker_and_scheduler` 的实际选路。
- 两份设备 UT：核对断言范围，未把测试定义等同于运行结果。


## 安装产品表与运行时能力的对应边界

同一提交的supported_hardware.inc.md及中文supported_hardware.inc.po列出以下常见产品。中文5条有效译文的msgid均对应当前英文，产品名保持一致；该安装入口表描述产品家族，不提供驱动/CANN/TorchNPU版本、模型、量化、图模式或并行组合的保证。

| 安装文档分类 | 明确列出的常见产品 |
| --- | --- |
| Atlas A2 | Atlas 800T A2、Atlas 900 A2 PoD、Atlas 200T A2 Box16、Atlas 300T A2、Atlas 800I A2等 |
| Atlas A3 | Atlas 800T A3、Atlas 900 A3 SuperPoD、Atlas 9000 A3 SuperPoD、Atlas 800I A3等 |
| Atlas推理系列 | Atlas 300I DUO、Atlas 200I Pro |
| 950DT | 950DT |

只从此表可确认950DT这一行；表中没有950PR行，不能扩写成“所有950 SKU均支持”。反过来，未列出不等于已证明950PR无法运行；需要查看目标版本的其他明确文档、SoC映射、实际构建目标和消费者。其他知识卡或模型支持矩阵若声明950DT/950PR，仍保留各自精确范围，不能用某一张表覆盖全部来源。

从产品名进入新模型适配时，先记录完整SKU与SoC，再核对get_device_config的包目标、Worker运行时检查和HardwareProfile；随后查模型支持矩阵与实际Attention/量化/图/通信消费者，最后用目标配置验证。不要只因产品同属A2/A3，或都映射到一个实现族，就宣称所有模型、精度和性能结果可以互用。本卡平台列表仍仅限定这套硬件识别/能力裁决流程。


## 孤儿310P教程与产品形态

旧tutorials/hardwares/310p.po共44条业务译文完整读取，当前没有同名英文页。它描述Atlas300I DUO与Atlas200I Pro都使用310P，但产品形态、OS和容器挂载分别解释；不能把共同芯片身份当作相同驱动、库路径、内存容量或模型组合。Ubuntu24.04/openEuler24.03页签只证明有这两个历史入口，PO缺失的挂载代码不靠记忆补造。

旧200I Pro段说明容器内npu-smi还需额外驱动库/配置挂载，/dev/davinci0按实际分配设备调整；npu-smi可见、包版本、插件选路与模型推理是独立阶段。旧文的host page cache清理是主机内存紧张时的可选root操作，内存足够可跳过，本次未执行。它针对可回收主机页缓存，不等于释放NPU HBM、清除进程泄漏或保证权重加载成功，也不纳入Agent默认部署前置动作。

### 旧图数量与Triton声明

旧PO把Atlas300I DUO的FULL_DECODE_ONLY描述为受event-id资源限制：多TP时可捕获图数随模型深度变化，例Qwen3-32B只捕获/重放2个；TP1不受该特定限制。不把“TP1无此限制”解释成无限图/stream/HBM，也不将2个设成所有模型固定上限。旧“软件修复可行/仍需时间”的说明不是当前修复已合入或可用证明；此PO不替代当前profile里的NPUGRAPH_EX能力或具体图后端核验。

同页旧文称DUO不支持triton/triton-ascend，提醒源码安装可能间接拉入并建议卸载。此处只记录该历史环境条件，没有卸载包，也不作为当前全部310P软件栈的通用修复。先固定版本、产品和实际attention路径，核对依赖消费者后再制定环境变更。

### 旧显式mask与OOM归因

旧资料描述AscendAttentionMetadataBuilder310把model_config.max_model_len交给AttentionMaskBuilder310，创建float16[max_model_len,max_model_len]完整causal mask后转FRACTAL_NZ；attention_v1的_npu_flash_attention/_npu_paged_attention_splitfuse直接消费显式mask，并称当时无压缩mask路径。本节证据是该PO的历史说明，未新读这些类/函数实现，不以它证明当前全部310P后端仍同样分配。

在该分配假设下，原始FP16方阵仅元素存储为2×L² bytes：L=16384约512MiB，32768约2GiB，65536约8GiB。这是静态算术推算，NZ转换的对齐、临时双份与allocator开销另算，不是NPU实测峰值。自动模型长度若很大可导致启动OOM，所以旧文给显式max-model-len16384作为保守候选；它不是所有模型支持上限、必定可装下或能解决所有OOM的值。先区分host加载、mask、KV、权重、工作区和图，再单变量核验。

### W8A8SC checkpoint 与预览支持

旧表三项产物分别为Eco-Tech/Qwen3-8B-w8a8sc-310-vllm、Eco-Tech/Qwen3-14B-w8a8sc-310-vllm、Eco-Tech/Qwen3-32B-w8a8sc-310-vllm。W8A8SC/310后缀是来源身份，不与W4A4/W4A8或其他W8A8目录互换；本次未下载外部权重或验证模型描述/质量。旧在线和example.py离线入口没有保留完整命令和实际输出，不补造结果。

结尾让读者关注#7394获取Qwen3-MoE/VL及Qwen3.5/3.6加速预览，这只是当时的预览/更新指向。本次未访问工作项，不据此宣布这些模型当前全部310P功能、精度或性能已支持。平台列表仍只限定本卡的硬件识别/资料裁决流程，不扩大该旧教程的运行承诺。


### 与既有310P报错卡按版本交叉阅读

检索还会召回[旧图捕获Runbook](../../runbooks/runtime/ascend_310p_graph_mode_unsupported_enforce_eager.md)。其卡内复现环境写明vllm-ascend:v0.9.2rc1-310p、Seed-X-PPO-7B、float16、TP1，并记录enforce-eager绕过捕获。该旧版本记录不能单独证明所有后续310P软件栈都永久不可用图；本节固定PO又描述FULL_DECODE_ONLY和event-id条件，两者须按版本、具体模式、模型和运行栈分别核对。也不能由当前PO反推那个旧触发组合已修复，或认定某个精确修复release。

[既有Triton回退卡](../../runbooks/runtime/ascend_310p_no_triton_kernel_eager_fallback.md)讨论算子可执行路径、dtype与host等价实现，和图捕获不是同一能力。此处只读既有卡文本，没有重新获取其Issue/PR、执行UT或变更这些旧卡；Agent应保留版本冲突与实际消费者，不能把一个能力缺口替代另一个。


本节Atlas 200I Pro也可写作紧凑检索标识Atlas200IPro，产品身份仍按完整SKU核对。Eco-Tech旧表的W8A8SC候选规模分别为8B、14B、32B；max_model_len的FP16 mask原始2×L²元素预算与NZ转换的临时开销分开，不能把host page cache释放等同于HBM释放。

## 包根导出与实际能力消费者

同提交 device/__init__.py 全文只重新导出 DeviceConfig、HardwareProfile、能力/策略枚举及 get_device_config/get_current_hardware_profile/get_hardware_profile 等符号，__all__列出公共入口。导入这些名称不额外执行本文件中的NPU探测/能力测试，也不将所有枚举值变成已启用支持。新增消费者应沿真实profile与自己的dtype/shape/模型门禁，而非用包根可导入作为设备或算子验收。这里仅补公共导出合同，没有改变原平台范围或验证状态。
