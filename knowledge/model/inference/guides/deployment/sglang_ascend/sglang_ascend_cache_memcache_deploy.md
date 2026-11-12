---
type: Guide
title: SGLang Ascend MemCache作为L3缓存的部署与配置边界
description: 说明HiCache接入npu_memcache所需的Meta与Local服务、Ascend IO布局组合、容量与world_size约束，以及配置解析失败的区分。
tags:
- task.implementation
- topic.model_serving
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/storage/npu_memcache/README.md
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/storage/npu_memcache/start_meta_service.py
  role: implementation
created_at: '2026-11-08T12:04:34Z'
updated_at: '2026-11-09T04:31:21Z'
platforms: []
aliases:
- npu_memcache
- MetaService
---

# SGLang Ascend MemCache作为L3缓存的部署与配置边界

## 接入合同

固定源码说明将Ascend MemCache作为HiCache L3后端，其下层依赖MemFabric。它不是启用层次缓存即可自动具备的远端存储：先准备memcache_hybrid与MetaService，再给SGLang匹配的meta_service_url/config_store_url。本文不将链接到的外部MemCache版本或传输能力当作已独立验证事实。

示例的组合是enable_hierarchical_cache、attention_backend=ascend、hicache_io_backend=kernel_ascend、hicache_storage_backend=npu_memcache，以及MLA的page_first_kv_split；不应把MLA布局直接套到MHA。Local配置经hicache_storage_backend_extra_config传JSON，Meta配置经start_meta_service的config_path传文件。

README列出device_sdma/device_rdma与host_rdma/host_urma/host_tcp/host_shm等协议。host_shm要求dram_size>0、hbm_size=0且无hcom；world_size为最大rank数，rank连接后不能修改，变更需重启Meta。文档称dram_size对host_rdma/host_tcp/host_shm按2MB、device_sdma/device_rdma按1GB自动对齐；host_urma虽在协议列表中，其对齐规则本段未声明，须另行核对，部署应同时核对实际依赖版本的行为；默认示例1GB并不表示每个模型足够。

## 启动失败定位

Meta配置文件必须是真正JSON对象，README展示的注释不能原样放入严格JSON。已知MetaConfig属性直接赋值，未知字段只告警忽略，不能靠拼错字段后的“启动成功”证明配置生效。加载文件错误返回1；setup返回非零整数时原样返回；main异常返回2；KeyboardInterrupt返回0。只有setup完成并进入服务不等于Local存储数据链路通过。

验收顺序为核对配置解析与版本→Meta/Local端口和rank→注册Host池→小块put/exists/get→真实KV前缀恢复及精度。回退到不使用该L3后端的配置并重启，保留Host/HBM预算与模型启动参数，不把简单HTTP可达当数据完整性。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
