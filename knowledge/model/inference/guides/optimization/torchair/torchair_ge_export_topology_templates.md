---
type: Guide
title: GE导出拓扑模板：rank映射与部署占位值
description: 核对两版关系与NUMA配置生成条件，保留全局rank零写入、通信组字符串及需要用户调整的节点设备网络占位值。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/export_config_generete.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/export_config_generete.py
  role: implementation
created_at: '2026-11-10T10:43:14Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE导出拓扑模板：rank映射与部署占位值

## 固定快照与用途

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的export_config_generete.py，保留源码generete拼写；两版AST相同。本卡限定导出部署JSON模板的生成条件和字段，不证明ATC、集群、设备或通信实际可用。产品范围未知，保持draft与空平台，未初始化进程组、写部署配置或启动通信。

## 只在已初始化且图使用通信组时生成

generate_config在torch.distributed未初始化或used_process_group为空时直接返回；否则取得默认进程组和其rank列表，依次调用关系与NUMA配置生成器。_generate_model_relation_config与_generate_numa_config均只让全局rank 0写文件，不是每个子组各自产生一份，也没有在此建立进程组或执行跨rank同步。

model_relation_config.json按默认组rank列表生成deploy_config、model_name_to_instance_id和rank_table。submodel_name委托get_export_rank_file_name，model_instance_id使用rankid；本文件没有另外建立真实物理设备拓扑映射。

## 关系配置含占位部署位置

deploy_device_id_list直接写为字符串0:0:rankid。源码说明Torch不能取得cluster/node信息，用户需要调整；不能把默认rankid无条件当作实际节点或设备号。

comm_group按groups_in_graph遍历，group_name原样写入，group_rank_list取rank_info[0]后用str(rank_list)，不是在此写原生JSON数值数组。调用方结构、下游配置格式和rank顺序仍须分别核对；其他rank_info字段在此不参与输出。

## NUMA模板不是硬件探测

numa_config.json固定item_type为Ascend910、node_type为ATLAS800；所有rank放入node_id=0，ipaddr为127.0.0.1、port为29500，nodes_toplogy保留源码拼写和空对象。以上是模板默认值，不是对当前服务器、网络、端口和产品的探测结果，也不能据这些字符串给整卡填写平台能力。

实际跨节点部署须按真实cluster/node/device和网络配置调整模板，再验证默认组与子组rank映射及子模型文件。本文不提供真实集群值，也未进行端口、进程或设备实验。

## 写入与验收边界

两文件写入前调用PathManager.check_path_writeable_and_safety，随后用w模式写JSON；本模块没有提供事务式双文件提交、失败回滚或完整部署格式验证。路径检查的完整实现不在本卡范围，调用了检查不代表部署内容已被认证。

核对是否实际进入生成分支、哪个rank写入、两个文件字段、占位拓扑是否已改、submodel_name是否对应真实导出件，再分别验证ATC编译和目标环境通信；本次只有两版静态全文审阅。

- [Dynamo离线导出部署](dynamo_export_offline_deployment.md)
- [集合通信的组元数据](torchair_ge_collective_lowering.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/export_config_generete.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/export_config_generete.py)（implementation）
