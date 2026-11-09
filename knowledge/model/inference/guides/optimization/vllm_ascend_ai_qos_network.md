---
type: Guide
title: vLLM Ascend AI QoS：A3 网络流量优先级和交换机联动
description: 结合AI QoS中文资料与两原图区分Strict Priority的SP、通道tag和UB交换机VL，核对A3/DSMI/驱动限制与实际策略，再测拥塞和服务尾延迟。 补充endpoint实际写入、mode未分派、DSMI返回值与baseline/unset部分失败和状态文件边界。
tags:
- task.optimization
- topic.data_movement
- topic.performance.analysis
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/Ai_QoS_introduction_en.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/Ai_QoS_introduction_en.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/ai_qos1.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/images/ai_qos2.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/ai_qos.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/ai_qos/ai_qos.cpp
  role: implementation
created_at: '2026-10-29T09:45:39Z'
updated_at: '2026-11-03T05:30:47Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- AiqosConfig
- run_unset
- _parse_and_validate_unset_state
---

# vLLM Ascend AI QoS：A3 网络流量优先级和交换机联动

## 适用范围与目的

来源限定 Atlas 800T A3、Atlas900 A3 SuperPoD，HDK>=25.5.2、LingQu network>=1.5.1，需可访问相关能力的容器。机制是 host通道priority→UB switch VL→strict-priority调度，隔离并区分 D2D、H2D/D2H 与算子下发流量。不是给任意 NIC 设置 DSCP，也不等于 KV Pool 的0–4 qos_priority。

## 准备和参数

从源码构建 tools/ai_qos 扩展，DSMI头和 libdrvdsmi_host.so 路径由环境确认，容器需可见。Auto 或 manual 为 AIV/SDMA/PCIEDMA 生成 tag 和交换机配置；manual取 high/middle/low，来源默认 AIV high、SDMA low、PCIEDMA high。

当前驱动 AIV QoS不生效，不能把生成了tag当成该通道已受控。工具打印配置不代表交换机已应用；实际策略会覆盖原有QoS，执行前保存环境现有配置并走运维流程。unset 同样仅打印交换机撤销命令，不会自动恢复所有外部配置。

## 验证与回退

先确认时间线/网络计数表明KV和集合通信竞争，再在同负载比较通道生效、拥塞、HCCL、offload尾部和服务SLO；高优先级收益可能以低优先级等待增加为代价。无拥塞时不可由机制推断收益。回退应用保留的交换机策略及host配置，重新核对流量。本次未构建模块或改交换机。


## 中文AI QoS与原图的SP含义

Ai_QoS_introduction_en.po的31条有效译文均匹配当前英文，两张原图按原始分辨率阅读。ai_qos1.png用不同颜色展示节点内D2D、节点内H2D与跨节点D2D在UB switch的冲突，并另标UB/RDMA平面；图中CPU/NPU、switch board数量只是示意，不是实际部署卡数、路由或带宽要求。

ai_qos2.png以VL1/VL2/VL3展示high/middle/low队列，SP调度先发四个高优先报文。这里SP是Strict Priority（严格优先级），与Sequence Parallelism（序列并行）的SP不同。Schedule Capability: 4是图示参数，不是实测吞吐、必需队列编号或低优先级等待上界；CLI的high/middle/low也不能直接替换成图中数字1/2/3。

## 通道、VL与生效证据

文档给AIV/SDMA/PCIEDMA默认high/low/high：AIV覆盖相关dispatch/combine及算子下发，SDMA覆盖相关collective与H2D/D2H KV搬运，PCIEDMA覆盖PCIe DMA下发。当前固定指南明确AIV配置受驱动限制不生效；生成tag、打印VL建议、驱动实际生效与交换机策略应用是不同状态，未来驱动/模块升级仍需独立证据。

该指南要求Atlas 800T A3或Atlas900 A3 SuperPoD、对应HDK/LingQu版本与特权容器；DSMI头文件/libdrvdsmi_host.so实际路径、挂载、扩展构建和运行时加载分别核对，不从CMake找到文件推导ABI/硬件已就绪。此要求只在该功能范围，不扩成所有推理/基准容器的默认权限。

Auto/manual输出的交换机配置会覆盖已有策略，unset打印的交换机撤销命令也需要实际在目标交换机应用；不能据工具输出认定外部配置已经改变或完整恢复。先保留实际通道/VL映射和当前策略，再在相同流量负载下核拥塞、低优先KV等待、HCCL与服务SLO。严格优先级机制不直接保证所有流量同时加速。本批未构建模块、调用tools.ai_qos、安装驱动或改交换机。


## 实际工具会写endpoint，交换机命令仍仅打印

补读同提交tools/ai_qos.py全部AST程序投影、ai_qos.cpp136行全文，未构建或执行。AiqosConfig虽保存mode=auto/manual，set_qos没有按mode分出不同自动优化算法；两者实际使用传入AIV/SDMA/PCIEDMA优先级和固定映射。CLI默认apply与high/low/high，不能当只读查看命令。

工具在所选设备真实调用DSMI set_fuse_gbl_config、set_qos、SDMA set_bw，交换机hccs remap/SP命令则去重排序后打印system-view/commit。端点已修改与交换机已应用必须分开验收；失败返回部分只打印/继续，没有跨设备事务回滚。ASCEND_RT_VISIBLE_DEVICES非空时按逗号非负整数列表使用，空时才用torch.npu.device_count生成0..N-1，逻辑/物理device映射须在目标环境核对。

## baseline快照与unset的完整性条件

状态默认写tools/ai_qos_state.json，保存原master QoS五元组、SDMA四元组、fuse三元组与打印过的命令。重apply优先复用已有baseline，新增设备再补采集；但某设备三类信息有任一缺项时会重新采集该设备并覆盖已有子项，不能保证失败后仍保留所有首次原值。读取失败会缺保存条目，且HW修改之后才write_text，写文件不是覆盖所有已改端点的原子事务。

unset先验证JSON结构/tuple长度并转int，按BW→QoS→fuse恢复保存值，再打印每条交换机命令前加undo并删除文件；部分恢复错误仅warning/忽略，不确认交换机状态。状态不存在退出1；JSON/结构失败会打印恢复说明并尝试删除坏状态文件，本次不执行其重启或外部设备操作建议。保留原始有效快照和实际设备状态后再按运维流程回退，不能把文件删除当成功恢复。

C++ getter除DSMI ret还核结构size，size错返回-1；set_qos对PCIEDMA设置bitmap0=1、SDMA为全1，master/core索引按固定DSMI子命令位域编码。这些是当前头/驱动ABI，不是任意版本可复用的裸数字。保存每设备get/set ret、实际tag/VL、状态完整性与交换机提交证据，再测拥塞和SLO；原A3/驱动限制仍保持，未新增运行验证。
