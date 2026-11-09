---
type: Guide
title: vLLM Ascend 旧版大规模EP模板：DP组、端口与迁移验收
description: 审查仍面向v0.9.1的A3大规模EP中文模板，分别核对P端独立DP组、D端全局rank与端口，固定模型/connector/参数版本后再做当前部署验收。
tags:
- task.implementation
- task.optimization
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/large_scale_ep.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/large_scale_ep.po
  role: supporting
created_at: '2026-10-30T07:18:05Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T07:18:05Z'
---

# vLLM Ascend 旧版大规模EP模板：DP组、端口与迁移验收


## 适用范围与版本

固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的large_scale_ep.md仍建议v0.9.1官方版本，并链接v0.9.1-dev代理示例。本卡按其八台Atlas800T A3、4P/4D的历史部署解释迁移审查；平台a3是此示例范围，不表示已在本次v0.32.0或目标机器运行。配套large_scale_ep.po有62条有效译文，msgid均匹配，但匹配不刷新模板版本或保证英文正确。

先固定目标两仓commit、CANN/驱动、模型checkpoint/量化scale、网络与实际生效参数。旧fork、外部DP环境变量、deepseek_mtp、enable_weight_nz_layout和prefill优化键需要逐项检查当前读取路径，见[配置生效链](../integration/vllm_ascend_configuration_resolution.md)。不要整段复制旧部署来宣布当前新模型适配完成。

## 分开审计两种DP组

| 项目 | P端模板 | D端模板 | 不能推导 |
|---|---|---|---|
| master | 四台P各自独立master/IP | 四台D共享192.0.0.5 | 一个全局统一DP master |
| DP组 | 每P节点dp_size=2、dp_size_local=2、rank从0开始 | dp_size=64、local=16；各节点rank_start为0/16/32/48 | 把P端聚合8个engine当单一DP8组 |
| TP/EP | TP8、enable_expert_parallel；每组EP16 | TP1、enable_expert_parallel；组EP64 | 再额外乘EP得到worker总数 |
| HTTP端口 | engine_port=9000，local序号产生9000/9001 | local16产生9000到9015 | 与kv_port或DP master port相同 |

run_dp_template.sh接收参数顺序为DP size、master IP、master port、local rank、global rank、engine HTTP port、local size。dp_rank_start是该节点global rank的起点，与从0计数的local rank分开。VLLM_DP_RANK_LOCAL与VLLM_DP_RANK职责不同；记录每个实际进程的rank/设备/组/监听端口，而不是只保存启动命令。模板的os.system和process.join没有收集检查shell命令的业务成功结果；启动器返回、进程存在或join结束都不等于服务就绪。

代理命令的host列表、重复数及ports-inc意图分别对应P每host2、D每host16个入口。要用目标版本实际代理解析后的endpoint列表核对，不仅凭名字中的inc推定扩展算法。该文链接的是另一历史ref代理，本批未读取该外部版本，未启动代理或监听端口。

## 通信探针与服务成功是不同层

指南A2分支说明节点内HCCS、节点间RDMA，A3分支节点内外HCCS；A2通信探针不是整套A3 EP部署的A2支持承诺。A3示例枚举0到15、用vnic/hccs_ping并查superpodid/SDID；A2枚举0到7、用ip/ping。所有编号先按实际逻辑设备与拓扑核对，不能当物理卡数通则。

依次保留链路UP/net_health/netdetect/gateway、NPU IP、跨节点可达与实际collective证据。宿主LAN连通、一个NPU ping成功、单机服务ready都不能替代全rank通信、P→D KV传输或真实请求完成。网络/线程/内存环境变量、共享端口和旧fork方法的生效范围应单独审查，本批未运行hccn_tool/npu-smi、改网络或启动服务。

## 旧配置只作带条件候选

来源P端HCCL_BUFFSIZE=256、eager、16384 batched tokens、max seq4；D端buffer1024、batched tokens256、max seq28，两端max_model_len17000/gpu_memory_utilization0.9/seed1024。P为kv_producer、D为kv_consumer，使用MooncakeConnectorV1、kv_port20001；这些与DP master13395、HTTP9000族分开。是否有效要按实际当前connector/schema检查，不将旧字符串数值或方法名当当前合同。

表格条件是平均输入3.5k、输出1.1k、context16k、输入最大7k以及4P/4D；开头说“优化配置”，末尾又要求按实际场景调整。它没有给出所有模型的最优参数或本次收益。warm-up应在同模型、相同请求/模式下记录，不能把删去冷启动时段变成完整端到端时延改善。

AISBench例另设model=dsr1，而服务--served-model-name为deepseek_r1；需确认代理是否映射，不能假定别名自动等价。request_rate28、batch_size1536、max_out_len10与上述1.1k输出负载不是同一已证明条件，不能直接共享吞吐结论。取消http_proxy/https_proxy只是此样例环境动作，实际实验记录有效client网络和代理，避免改用户全局环境。准确率与压力测试按[四工具验收](../bringup/vllm_ascend_accuracy_evaluation_contract.md)留数据/模板、失败、重试及原始产物。

## 当前版本验收顺序

1. 先完成真实权重共置smoke与任务精度，固定当前worker/Runner、量化和草稿路径。
2. 核对P/D组、设备映射、网络/端口与实际connector配置，先最小拓扑验证KV身份和传输完成。
3. 扩展目标DP/TP/EP并覆盖失败、部分启动、暂停/退出、资源清理和请求完成；每项保存实际证据。
4. 正确性通过后，以同负载、采样、数据集、冷暖和SLO比较P/D容量与性能。未验证项保持未知，保留回退到最近通过拓扑的配置。

本批仅完整阅读冻结英文/中文与审查模板，不执行其中shell/Python、安装AISBench、下载权重或进行NPU/Agent评估。
