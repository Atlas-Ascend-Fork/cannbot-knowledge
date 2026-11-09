---
type: Guide
title: vLLM Ascend GLM-5.1：SFA C8、PCP 与量化分支验收
description: 区分GLM-5停止维护和GLM-5.1的当前路径，按A3 C8与950 MXFP4分别检查PCP、主缓存/Indexer和融合开关。 补单机、双机共置与分离的角色预算，明确TP/PCP、V1/V2连接器、P1/D3草稿和每host服务数量，保留135K/198K、seq8/20及融合限制的来源冲突。
  量化权重、main KV与Indexer缓存分别选型：950配方用FP8，A3 W8A8C8与PD配方用INT8。
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/models/GLM5.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/support_matrix/supported_models.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/models/GLM5.po
  role: supporting
created_at: '2026-10-29T10:03:49Z'
updated_at: '2026-10-31T01:42:51Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- GLM-5.1
- GLM-5.1-w4a8
- GLM-5.1-w8a8
- GLM-5.1-w8a8c8-MTP
- GLM-5.1-w4a4c8-mxfp4
- GLM5.md
- GLM5.po
---


# vLLM Ascend GLM-5.1：SFA C8、PCP 与量化分支验收

## 模型身份与环境

文件名GLM5.md同时含GLM-5停止维护声明和GLM-5.1部署，必须按实际checkpoint区分。教程要求transformers>=5.2.0；TokenizersBackend缺失先核版本/配置，不随意替换tokenizer class。

## 权重和并行参考

A2/A3 W4A8/W8A8、A3 W8A8C8-MTP与950 W4A4C8-MXFP4互不等同。A3长序列参考有PCP4高吞吐与PCP16低延迟，不是PCP越大总吞吐越好。PP+PCP+PD需按connector独立核对，不能从并列表的单项推全组合。

## 优化边界

主SFA C8与Indexer INT8是两开关；低延迟例子可能均关闭，不能仅由C8名称认定全部开启。MLAPO占额外HBM，PD来源只在D端建议；旧non-CP限制按实际版本代码判断。Fused MC2与shared-expert overlap存在自动禁用，参数合并后核对有效值。balance scheduling与PD/CPP/Dyntra的限制依现行配置，不复制教程旧顶层字段。

## 验收

先同权重原精度输出，再比较量化/图/PCP；对照真实prefix命中，0%与非零命中需分别测。MTP P1/D3是该非hybrid参考，不能套Qwen hybrid的P/D等K。既有CANN Executor的GLM5部署保持独立框架边界。

## 证据与验收边界

上述为固定提交的模型专属条件提取，不表示教程全部场景已穷尽或已在本仓复测。先按[模型支持裁决](vllm_ascend_model_support_resolution.md)核对维护状态和实际版本，再逐项执行加载、数值、混batch、状态推进与目标SLO验收。失败关闭新增功能、恢复完整已验证权重和配置；本次未下载权重或执行NPU/分布式测试。


## 教程全文与当前模型范围

补读GLM5.md全1562行与GLM5.po全159条。GLM-5自Ascend v0.30.0停止支持及后续修复，当前部署对象是GLM-5.1；历史0.23链接未在本批取回，不将同名文件当GLM-5重获支持。此停更声明不替代另一框架[固定CANN Executor部署](glm_5_deployment.md)的版本边界。transformers>=5.2.0、实际checkpoint与模型配置先匹配，TokenizersBackend错误不靠随意替换tokenizer class解决。

W4A8/W8A8、W8A8C8-MTP与950 W4A4C8-MXFP4分别保存。950权重名带MXFP4，命令仍是quantization=ascend，不能改成M3 MXFP8的量化参数；main KV与Indexer dtype又是两个选项。A3参考8块128GB物理NPU/16逻辑设备，950八块96GB、A2八块64GB，按真实可用容量预算，不把逻辑ID翻倍成HBM。权重表“两台A2”与32K单A2例并存，不外推单A2可跑200K。

以下都是参考配方；PD明确仅展示过程、不建议生产。容器版本宏、-a3/-a5后缀与shm1g请求不证明实际软件身份或可用共享内存；本批没有安装、下载或运行这些命令。

## 单机与双机共置：脚本和参考表分开

预算列按max-model-len / max-num-seqs / max-num-batched-tokens / gpu-memory-utilization排列。未显式值不补运行时默认。K为deepseek_mtp num_speculative_tokens，草稿enforce_eager=true与target图模式分开。

| 脚本场景 | 全局拓扑与本地身份 | 长度 / 序列 / 批token / 比例 | KV与执行条件 |
| --- | --- | --- | --- |
| 950单机W4A4C8-MXFP4 | DP1/TP1/PCP8 | 202752 / 128 / 8192 / .95 | main/Indexer FP8、K3、APC、target FULL_DECODE_ONLY |
| A3单机W4A8 | DP1/TP16 | 200000 / 16 / 4096 / .95 | K3、APC/chunk、target FULL_DECODE_ONLY |
| A2单机W4A8 | DP1/TP8 | 32768 / 8 / 4096 / .95 | K3、APC/chunk、target FULL_DECODE_ONLY |
| A3双机W8A8C8-MTP | globalDP8/TP1/PCP4，各local4，start0/4 | 未显式 / 未显式 / 未显式 / .92 | main/Indexer INT8、K3、async/APC/chunk，Node1 headless |
| A2双机W4A8 | globalDP2/TP8，各local1，start0/1 | 131072 / 2 / 4096 / .95 | K3、target FULL_DECODE_ONLY；APC未显式 |

单机与共置API8000、模型名glm-5.1；A3双机RPC12980，A2双机RPC13389。A3双机源码没有显式长度/序列/batch，不能把性能参考表的202752/6/4096当作命令已设置。该表另给低延迟globalDP2/TP1/PCP16、每host local1、202752/16/4096/K3；它不是完整专用脚本，也不能用不同拓扑的seq6与16直接比较容量或吞吐。

上述配方均给use_index_cache=true、index_topk_freq=4。950单机还有DYNAMIC_EPLB、heat collection50/algorithm interval5/policy2/redundant0及MLP prefetch；这些是来源参数，不当本仓优化收益。950 additional-config中的cpu binding/shared-expert overlap为字符串"True"，不是JSON bool，先核实际版本解析与有效配置，不静默替来源换类型。

## 950四host分离：两个独立P组与一个D组

两个P host各自DP1/TP1/PCP8，各API6700/RPC10521，rank均从0开始，是两个独立P服务组；两个D host组成globalDP16/TP1，各local8、start0/8，协调地址D0、RPC10523、API各6721–6728。proxy8000注册两个P和十六个D端点，不能将P擅改成globalDP2或每host只注册一个D API。

| PD脚本场景 | 实际并行组 | 长度 / 序列 / 批token / 比例 | 角色专用设置 |
| --- | --- | --- | --- |
| 950 Prefill，每个独立P组 | DP1/TP1/PCP8 | 135000 / 8 / 8192 / .95 | target eager、K1、APC、main/Indexer FP8、KV30100 |
| 950 Decode，跨两D host | globalDP16/TP1，各local8 | 135000 / 60 / 240 / .95 | target FULL_DECODE_ONLY、K3、APC、FP8、KV30300、LM-head TP8 |
| A3 Prefill，跨两P host | PP2/TP1/PCP16，78层41,37 | 202752 / 64 / 16384 / .92 | target eager、K1、APC、main/Indexer INT8、KV30000 |
| A3 Decode，跨两D host | globalDP8/TP4，各local4 | 202752 / 32 / 164 / .92 | target FULL_DECODE_ONLY、K3、async、INT8、KV30200；APC未显式 |

950用MooncakeConnectorV1，extra写P dp1/tp1、D dp16/tp1、hixlep静态路径；同时导出LOCAL_COMM_RES version1.3。该组合属于来源模板，按实际UB/RoCE/SDK路径核对，不能据导出字符串证明网络已可用。P HCCL buffer300、D1200，model timeout30000秒；P/D recompute均为字符串"True"，D另设LM-head TP8。

950八参launcher将每rank设备段按TP×PCP、API按local rank递增；local DP缺省全局、start0/API8000。RPC声明type=str但默认值写整数12345，并原样进入subprocess参数列表；默认分支的有效类型需核对。所列启动调用都显式传RPC，不能据此局部问题宣称整个参考已失败。子进程check=True，父只join不聚合退出码，所有join不证明所有engine健康。

## A3分离：PP、PCP、API与连接器维度

A3 P是一个PP2组跨两host，不是两个独立P组。P0为master/API8000，P1 node-rank1/headless无API，MP nnodes2/master7060、每stage PCP16。P直接bash启动，不用D侧TP×PP launcher来切P设备。D两个host各四个TP4 engine，global ranks0–3/4–7、RPC12321、API各8000–8003；proxy8000只注册P0一个P API及八个D API。

P/D用MooncakeConnectorV2，extra写P dp1/pp2/tp16/partition41,37与D dp8/tp4。extra中的16不能直接替CLI TP1/PCP16：所读[V2门面与初始化合同](../integration/vllm_ascend_mooncake_v2_facade_contract.md)从实际parallel config和PCP group读取维度并建端口，完整peer布局仍需握手/transfer证据，未证明所有legacy extra如何消费。不要盲改成同一数字，也不推断任意PP/CP组合都成功；教程明确V1不能同时PP+PCP。

A3 P recompute=false、D=true，D启MLAPO，P/D都写MC2与shared-expert-overlap=true；最终有效开关需核实自动禁用。D 32序列/K3的扩展token为128，预算164不是164序列；950 60×(1+3)=240。P K1/D K3是此配方，双端同method=deepseek_mtp且草稿eager，不套其他模型P/D等K规则。

proxy和若干engine都监听0.0.0.0:8000；若同host运行，要选空闲端口或独立host并更新映射。“任意机器”不保证无端口冲突。先等所有实际rank/API就绪、确认权重/版本/模型名与有效配置，再经真实proxy做短请求，核对KV匹配、取消、重算与失败恢复；本批没有打开任何端口。

## 参数冲突、实验项与验收

Fused MC2自动关闭shared-expert overlap，不能将两个配置true记录成两个收益叠加。来源又对dispatch_ffn_combine/mega_moe给非MTP/非dynamic-EPLB和格式/EP上界，同时参考脚本启MTP与MC2；在没有实际kernel选路前保留冲突，不凭flag证明具体融合算子生效，也不据表一句话判定全部部署必失败。

PCP取代旧PO的enable_dsa_cp字段；“128K需要PCP”与单机A3 200000/TP16无PCP例并存，不能作全模型硬拒绝。Sparse SFA C8表称0.23实验、参考高吞吐/PD开启，但命令没显式enable_sparse_sfa_c8，需有效配置证据；Sparse LI C8的Indexer INT8独立，低延迟表称两者关闭也不能据模型名自动推断。MLAPO的额外HBM、Flashcomm与o_proj layer_sharding冲突、balance scheduling的V1/非PD及TTFT代价分别验收，未显式Runner时不替脚本补V1/2默认。

参考表950 P seq20与脚本seq8不同；场景列表仍称950“198K”，当前表/脚本却135000，旧PO整表仍202752。参数调优表.92属于相应A3参考，不能覆盖单机/950脚本的.95。eager只控制图，不代替chunked prefill；APC 0%与非零prefix命中是两种测量设置，均需真实命中观测。

159双语条目149原串匹配、10人工差异、0仅历史上下文：旧DP8TP4/PP2TP16迁移为TP1×PCP，表头新增PCP，PO157旧活动表与159当前表按当前英文对照，不当两个并行有效配方。24来源限定随卡保留；匹配不等于事实真、全站HTML一致或本次NPU验证。文档只给AISBench入口、配置与输入/输出和prefix比例记法，没有本批精度/吞吐基线；更多seq/K或融合收益要做受控A/B，保存实际checkpoint、各rank限制、acceptance、TTFT/TPOT和HBM。失败恢复同一版本/权重/拓扑，不能混CANN Executor、GLM5历史或其他GLM模型参数。
