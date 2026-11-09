---
type: Guide
title: vLLM Ascend版本回归清单：发布声明、缓存恢复与适配重验
description: 按固定版本release fragments建立模型迁移回归检查点，区分版本限定的支持声明、真实实现约束与尚未执行的精度/性能证据；核对KV恢复、PP物理层、KDA状态、Mooncake失败及环境身份。
tags:
- task.testing
- task.debugging
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/18742.yaml
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/18857.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/18891.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19086.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19179.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19240.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19245.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19264.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19273.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19321.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19347.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19408.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19422.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19449.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19516.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19537.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19657.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19693.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19695.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19744.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19755.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19785.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/release_notes/fragments/19877.yaml
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-release/references/ref-past-release-notes-highlight.md
  role: evidence
created_at: '2026-11-03T04:45:55Z'
updated_at: '2026-11-03T04:45:55Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend版本回归清单：发布声明、缓存恢复与适配重验

## 证据强度与使用方法

本卡把固定ceac提交的23份release fragment与历史发布示例转成升级时的检查清单。fragment是维护者的变更声明，不等于已读全部实现、完整硬件支持或本次测试通过；按PR号定位对应代码/测试，再保留目标版本、配置、原始结果和失败边界。不能把“Fixed”翻译为任意安装已修复，也不能从性能类声明推导数值收益。

先按[测试证据选择](vllm_ascend_test_evidence_selection.md)区分CPU mock、真实权重、NPU与E2E，再按任务匹配下表。所有条目仍需目标环境复验。

## ceac快照中的具体升级检查点

| Fragment | 新模型适配或优化时核对的约束 |
| --- | --- |
| 18742 | MRv2的外部FlashMLA decode声明限符合条件的MLA、DCP及DSpark；prefill仍为FIA。 |
| 18857 | GLM-5.3-Flash的KDA递归状态显式BF16需同时核cache sizing与分层分配，auto仍FP32。 |
| 18891 | A5 DeepSeek-V4缺省KV dtype须与实际BF16布局一致；注意attention/indexer构造期拒绝不支持的dtype，不能等到capture才验。 |
| 19086 | Mooncake共享engine仅在初始化成功后发布；native构造/初始化失败后要求进程重启，避免重复积累传输资源。 |
| 19179 | MiniMax-M3在无dense attention的A5 PP stage混合FP8/BF16时仍需保留128-token block约束。 |
| 19240 | V4 Flash/V4.1 Flash声明TP上限8、V4 Pro上限16；MRv1 DSA-CP既有例外单独保留，不泛化成任意组合。 |
| 19245 | MRv2 static kernel启动需current-config上下文，覆盖missing-current-config启动回归。 |
| 19264 | Gemma4 MRv2 dense FP16/BF16 full与SWA兼容配置恢复共享KV容量；不能推广所有KV量化布局。 |
| 19273 | AscendStore segmented布局的partial bulk restore应核实际token范围。 |
| 19321 | V4.1 SWA bounded decoder replay新增PCP组合，包含关闭prefix cache时的cold prefill。 |
| 19347 | MRv1内部MoE SP而PP中间量采用full-token布局时，同时核buffer sizing与token截断。 |
| 19408 | GLM-5.3初始化复用metadata-owned convolution输出并移除冗余KDA清零；这是发布性能声明，未给本机收益。 |
| 19422 | layerwise KV在PP下物理注册层扩张时，需核实际完整传输与SSD pool路径。 |
| 19449 | 该fragment记录A2/A3/310P/A5镜像基座CANN 9.2.0_20261022115200；不据此推任何已安装机器版本。 |
| 19516 | vLLM兼容版本声明更新到0.32.0；实际安装SHA与paired接口仍逐次留证。 |
| 19537 | MiniMax-M3 DSpark draft FlashAttention声明限定A5与MRv2。 |
| 19657 | V4.1 Engram device/host表移除冗余结果buffer初始化，性能收益仍需真实同配置测量。 |
| 19693 | MRv2 preemption恢复后AscendStore block table需保持一致；修复说明恢复save而非依赖save-suppression workaround。 |
| 19695 | A3/CANN9.2小型private host-offloaded Engram有效payload按64KiB对齐，同时保留原allocation用于清理。 |
| 19744 | dense DP独立副本的Mooncake V1/V2 endpoint和AscendStore lookup IPC需隔离，防止命名碰撞。 |
| 19755 | 完整prefix已在local HBM时避免重复KV-pool查询/SSD rewarm，但仍保留layer-reuse probing。 |
| 19785 | KV-pool需拒绝陈旧load plan及超过worker已分配blocks的save范围。 |
| 19877 | PP stage的物理MTP cache层超出估算capacity时，memcache pool需核对象容量；升级需重建相关pool并同时更新所有读写端。 |

## 历史版本不能平移为当前默认

历史示例按版本写明：0.11.0的CANN8.3.rc2/TorchNPU2.7.1.post1、0.13.0rc2的CANN8.5.0/TorchNPU2.8.0.post1/Triton3.2.0，以及0.14.0rc1的TorchNPU2.9.0，属于不同依赖栈。post包不能假定由普通依赖解析自动装入。此处只记录版本迁移线索，不提供当前安装推荐。

0.11.0的Qwen3-Next EP/MTP、DeepSeek3.2图模式、Qwen2-audio和多实例CPU绑定限制，与0.13/0.14新增能力不能混成统一支持矩阵。0.13.0rc1将PCP/DCP标实验、Qwen3-Next长序列/部分长度性能和超短序列精度列已知问题；后续“更稳定”仍不是所有模型/拓扑/shape已验证。0.14.0rc1恢复的310P声明仅basic dense/VL eager，不能推当前全部模型或图模式。

配置迁移尤其核对：旧CPUOffloadingConnector、LLMdatadist、Torchair与Ascend scheduler的版本化弃用；EPLB字段移入eplb_config；Profiler环境变量转向--profiler-config；dump_config的dict改为dump_config_path字符串；chunked_prefill_for_mla与若干旧环境开关移除。MLAPO默认和内存成本也按版本核对，不照抄旧默认。历史EngineCore pickle问题的补丁建议仅对应其发布上下文，本卡没有执行cherry-pick、安装或任何代码。

## Agent应交付的重验材料

记录旧/新框架SHA、CANN/TorchNPU/算子库和真实权重身份，选择与变更直接相关的空批/边界/失败恢复及模型配置，再分别核对加载、prefill/decode、capture/replay、PP/DP/PCP/DCP、缓存清理和吞吐/时延。声明支持、用例存在、CI选中及实际通过是不同事实；没有原始设备结果时保持未验证。

本次只读取YAML和历史说明，没有执行测试、CI、模型、NPU或Agent A/B。完整Device数值/性能及跨版本行为仍需独立验证。
