---
type: Guide
title: vLLM Ascend GLM KDA RecoverSSM：实验开关、并行限制与回退
description: 在A3/A5的GLM-5.3-Flash MRv2中核对--use-replayssm、APC、Mamba缓存和PD约束，区分上游ReplaySSM与Ascend
  RecoverSSM并验证质量和净时延。
tags:
- task.optimization
- topic.speculative_decoding
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/5fa10c3799e249627112ead02c8414988d85ddcc/docs/source/user_guide/feature_guide/speculative_decoding.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/glm5next/recoverssm_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_replayssm_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/models/test_glm5next_recoverssm_config.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/cache.py
  role: constraint
created_at: '2026-10-29T14:19:58Z'
platforms:
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:05:17Z'
---

# vLLM Ascend GLM KDA RecoverSSM：实验开关、并行限制与回退

以下所列旧版本限制继续保留；7d9e新增有条件的PCP producer路径，见[7d9e运行时差异](../integration/vllm_ascend_7d9e_runtime_delta_contract.md)的RecoverSSM节。先核target版本、TP/PP/DCP、connector角色及metadata回传，再判断PCP能否启用。

## 适用范围和版本

Ascend文档提交`5fa10c3799e249627112ead02c8414988d85ddcc`明确列出GLM-5.3-Flash、A3/A5、Model Runner V2的实验路径；本卡950仅指该A5范围，不扩为全部950变体，也不因GLM模型本身支持A2而扩为A2 RecoverSSM支持。源码探针固定在已有`ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，上游CacheConfig参照vLLM v0.32.0的`5df63a7203cdb9328d824a27b682e77c7b9928be`。三者各有身份，不能把网站latest、Ascend main和任意PyPI安装视为同一运行环境。

RecoverSSM在投机验证后恢复被接受的递归状态，减少为每个草稿token保存完整recurrent checkpoint的需要。默认仍是native AscendC KDA；不预设显存或速度必然改善。`stable`表示知识卡生命周期，功能仍为实验性，本仓未执行真机验证。

## 启用前先检查的完整交集

| 条件 | 固定来源约束 | 不满足时的动作 |
| --- | --- | --- |
| 模型与Runner | 文档限定GLM-5.3-Flash MRv2；实现识别hf_text_config.model_type为glm5_next或glm5_next_text | 实现谓词命中不扩为其他GLM模型的部署支持 |
| 投机 | speculative_config必须存在，目标配置还需正的有效草稿窗口 | 沿实际schema核对方法/K，不能只留开关 |
| 缓存 | 关闭prefix caching，mamba_cache_mode=none | 关闭APC后重新核算容量与TTFT；不能套上游align模式 |
| 并行 | PP=1、PCP=1、DCP=1 | 改回受支持布局或关闭该功能，不删启动校验 |
| 状态精度 | 禁stochastic rounding；源码另注明FP16 KV cache未验证 | 未验证不是已支持，也不是现有代码已硬拒绝FP16 |
| PD | connector字段直接为MooncakeConnectorV2或MooncakePullConnector | 不从MultiConnector内嵌上述名称推导允许 |

参考是在已经适配的GLM服务配置上增加`--use-replayssm`、`--no-enable-prefix-caching`、`--mamba-cache-mode none`和`--compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}'`，配合文档MTP K5示例。K5及图模式是该示例，不是由config validator证明所有图模式都禁止或所有K都可用。权重量化、KV dtype、TP与内存预算继续按[GLM-5.3-Flash模型指南](../models/vllm_ascend_glm53_flash_hybrid.md)独立选择。

## 开关解析和配置错误定位

上游CacheConfig.use_replayssm默认false，描述主要围绕Mamba2 ReplaySSM；use_kda_recoverssm为内部派生字段。Ascend的validate_mamba_cached_kernel补丁在启用开关且模型谓词命中时先运行validate_glm_recoverssm，再置use_kda_recoverssm=True；其他情况调用原校验。不能把上游Mamba2的FlashInfer/Triton、buffer或align限制原样套到这个Ascend分支，也不能手填内部字段绕开校验。

遇到“requires speculative decoding”“Mamba cache mode none and prefix caching disabled”“PP=1 and PCP=1”“DCP=1”或“requires Mooncake”时，先保存实际解析后的config及模型类型，核对对应字段。补丁修改了pydantic validator并rebuild dataclass；只看CLI字符串或只import单个helper不足以确认实际启动路径。

## 验收、收益和回退

PD两侧必须对齐模型权重、TP、speculative window和RecoverSSM开关，保持相同状态协议；不把单端启用写成可互通。先建立同权重、同采样和同负载的native KDA基线，再核对零/部分/全接受、无草稿轮次、混batch、图填充、EOS及抢占后的状态推进。图相关排查见[RecoverSSM元数据诊断](../../runbooks/precision/vllm_ascend_glm_recoverssm_graph_metadata.md)。

浮点差异可能改变生成token，不能承诺bitwise一致或仅凭接受率证明质量。分别评估任务质量、接受长度、verify/commit耗时、HBM、TPOT/吞吐及关闭APC的TTFT代价，按目标SLO作决定。失败时移除--use-replayssm并重启完整服务/PD组以选择native KDA；还需按原基线恢复缓存和内存配置，不复用不兼容的状态缓存。本次未运行NPU、PD或性能实验。
