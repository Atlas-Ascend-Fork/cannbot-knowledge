---
type: Guide
title: SGLang MemCache的KV分量键、前缀命中与混合状态完整性
description: 从NpuMemcacheStore提取配置覆盖、rank映射、缓冲区注册、KV/Indexer/scale分量键及v1/v2前缀和辅助池命中规则。
tags:
- task.implementation
- topic.memory
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/storage/npu_memcache/npu_memcache_store.py
  role: primary
created_at: '2026-11-08T12:04:34Z'
updated_at: '2026-11-09T04:33:52Z'
platforms: []
aliases:
- NpuMemcacheStore
- batch_exists_v2
---

# SGLang MemCache的KV分量键、前缀命中与混合状态完整性

## 配置和注册

配置文件由环境变量提供，加载失败告警；extra_config覆盖文件同名键。控制键不传入LocalConfig，未知LocalConfig字段告警。device_id缺省先取当前NPU，失败回退tp_rank再0；可用dict或JSON按TP rank指定，scalar在多rank下有告警。该逻辑使用进程可见设备，不能据此证明全局物理卡编号映射正确。

setup/init非零失败。init_bm=False是纯客户端，缺少本地buffer manager时无法完成要求注册的IO；warmup探针在注册阶段按env控制执行，并非构造即完成。check_server轮询metrics HTTP200只证明该服务端点就绪；4KB唯一键的put/exists/get才验证一条小数据路径，仍需真实KV验收。

支持的注册布局包括page_first、page_first_direct、page_head、page_first_kv_split。register_buffer错误会抛异常，不能套用PD transfer engine仅debug的行为。MLA在page_first_kv_split布局中分别注册K/V及存在的Indexer/scale，V注册不因packed DSA而跳过；packed判断只在生成存储分量键时省略V分量持久化/传输。混合池按buffer accessor注册，v2避免把KV anchor重复当辅助池。

## 键与分量必须共同命中

MHA命名空间含TP、PP、CP；复制式MLA含PP、CP而不含TP rank。head切分使用tp_lcm/tp_size，键后缀、分量顺序和实际pointer列表必须一致。MLA仅在page_first_kv_split布局中以packed的1或普通的2为基础分量数，再按Indexer K/scale增加；非split MLA布局每页只有一个K分量键，不在此扩展Indexer/scale键。混合池的Indexer、Mamba temporal与conv、draft K/V分别参与自己的分量合同。不能把单个K键命中解释成逻辑页已完整恢复。

v1 get/set返回逐逻辑页bool：get把底层成功码0转换成请求正字节数，失败转负绝对值，页内所有分量均成功才True；set要求各分量返回0，已有键可跳过put。batch_exists返回连续前缀页数，不是散落命中总数。

v2同时检查KV连续前缀和辅助池。ALL_PAGES要求相关全部页，TRAILING_PAGES要求边界尾页；算法分别在KV最长连续前缀范围内求各辅助池的最大boundary，再与KV边界取最小值，不会在缩短后的最终边界重新验证TRAILING_PAGES尾页。混合尾页状态有空洞时不能保证返回边界可恢复：例如KV命中5页、Mamba仅第5页有状态且trailing=1、draft连续命中4页，可能返回4而第4页Mamba状态缺失；调用方仍需核验最终边界。get/set按pool名返回结果，检查池已注册、键非空、索引非None及键数与页数关系，随后直接使用get_page_buffer_meta返回的指针/尺寸列表，没有检查它们与分量键数量相等；调用方须验证分量数量和顺序一致。混合Mamba/conv状态丢失不能用KV存在掩盖。

## 观测与验收

通用batch_get的前缀字节/分量换算与v1/v2结构化返回不同，调用者必须使用对应API合同。metrics中的v1大小/耗时按Host墙钟和gb_per_page计算，不是NPU task计时，也不能据此声称含所有V/scale的完整Fabric带宽或模型TPOT。

针对相同前缀逐项验证K/V、scale、Indexer、Mamba与draft恢复；覆盖稀疏缺键、部分分量失败、不同TP/PP/CP和配置拼写错误。运行时版本变更需重新核对外部MemCache返回码语义，本文只审阅SGLang侧处理。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
