---
type: Guide
title: SGLang NPU缓存与PD回归的命中和时延断言
description: 区分Radix/HiCache命中、Mamba L3回读、PD主机池解析与TTFT相对门槛，避免把测试存在当成验证结果。
tags:
- task.testing
- topic.model_serving
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hicache_mamba.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hicache_mha.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_mla.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_mutually_exclusive.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_ttft_mha.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_radix_cache.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/pd_disaggregation/test_npu_pd_decode_retraction_backup.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/pd_disaggregation/test_npu_pd_disaggregation.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_mla_fia_hicache_bf16.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/hicache/test_npu_kimi_k3_hicache.py
  role: supporting
created_at: '2026-11-08T12:28:23Z'
updated_at: '2026-11-09T04:35:29Z'
platforms:
- a3
---

# SGLang NPU缓存与PD回归的命中和时延断言

## 命中正确性与缓存层次

来源注册面向A3；以下是测试条件和期待信号，本次未运行。通用GSM8K的PR替换见[共同契约](sglang_ascend_test_gsm8k_contract.md)，多节点启动和transfer的生命周期见[PD harness](sglang_ascend_test_multinode_pd_harness.md)。

| 用例 | 固定条件 | 实际断言 |
|---|---|---|
| Radix / hierarchical cache | Qwen3-8B、TP1、禁图；长/短及不同文本 | 重复长文本cached_tokens>0；短文本因page不足为0；不同长文本为0；Radix用例方法间flush |
| MHA HiCache | Qwen2.5-7B，pinned allocator，PR cache1GB/其他10GB | 非PR GSM8K1319题、5shot、max512、parallel128，目标0.85；PR仅smoke |
| MLA FIA HiCache | Moonlight16B-A3B BF16、TP2、FIA，PR cache2GB/其他10GB | GSM8K目标0.83；PR额外禁图，评测backend evalscope |
| HiCache与disable-radix互斥 | 同时启动两个冲突选项 | 期待明确的启动错误；不是性能比较 |

## Mamba L3文件回读专门测试

Qwen3.5-0.8B，TP1/static0.2，SSM BF16、chunk1024、page64，HiCache1GB，storage=file、prefetch wait_complete、write_through、IO backend=`kernel`、layout=page_first_direct。输入3200个重复token id1000，输出16、ignore_eos、temperature0。

首次cached=0；热设备缓存时device>0、host=0、storage=0；等待最多30秒出现新的Mamba文件，flush后重新请求要求storage>0且生成文本相同。这个active nightly-A3定义与文档支持表“Mamba HiCache不支持”存在版本内差异：测试描述的是这条文件后端路径及其预期，不能单凭文件存在宣称功能已通过，也不能把page64移植到所有模型。

## TTFT对照门槛

MLA场景使用DeepSeek-R1 W8A8 TP16、禁图、chunk512；GSP input3584（共享1792+独有1792）、output1、N128/C16，对比disable-Radix基线与HiCache write_back/ratio5，要求TTFT≤基线80%。MHA场景是Qwen3-32B TP2、chunk=-1，同类负载要求≤60%。这是20%/40%降幅的**验收要求**，不是本次测到的改善；output1还不能计算普通逐token TPOT。复测必须保留相同warmup、cache状态与客户端口径。

## PD主机备份与回读

decode-retraction-backup用Llama3.2-1B的P/D TP1，static0.6、禁图、reserved-decode-tokens128。可见设备默认P=1/D=8，各自进程内部base GPU为0；检查server_info解析到host_pool、kernel_ascend、page_first_direct及非空补全，**没有强制造成真实retraction或验证其释放生命周期**。

PD HiCache用Qwen3-32B P/D TP2、bootstrap8996/store24667、file wait_complete/kernel_ascend/page_first_direct，reserved128/poll2，PR cache2GB/其他10GB。800-token prompt在flush/offload后重复要求cached>700；多轮初始提示由300个随机token解码构造，此后逐轮追加生成文本并发送不断增长的完整上下文，每轮最多生成200个token，turn2–4要求cached单调增加。这些断言针对指定PD配置，不证明所有transfer backend或故障回收情形。

Kimi-K3另有手工mixed非PD的HiCache L2质量定义：W4A8 ModelSlim、BF16、TP64/attention-DP4、DeepEP auto、static0.75、max-Mamba240、kernel_ascend、ratio4、cache-report。旧GSM8KAscendMixin的accuracy目标0.9，没有在该子类单独断言命中率或性能，也未声明芯片产品。

## Evidence

- [test/registered/npu/basic_function/HiCache/test_npu_hicache_mamba.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hicache_mamba.py)（primary）
- [test/registered/npu/basic_function/HiCache/test_npu_hicache_mha.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hicache_mha.py)（supporting）
- [test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache.py)（supporting）
- [test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_mla.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_mla.py)（supporting）
- [test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_mutually_exclusive.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_mutually_exclusive.py)（supporting）
- [test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_ttft_mha.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_hierarchical_cache_ttft_mha.py)（supporting）
- [test/registered/npu/basic_function/HiCache/test_npu_radix_cache.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/HiCache/test_npu_radix_cache.py)（supporting）
- [test/registered/npu/basic_function/pd_disaggregation/test_npu_pd_decode_retraction_backup.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/pd_disaggregation/test_npu_pd_decode_retraction_backup.py)（supporting）
- [test/registered/npu/basic_function/pd_disaggregation/test_npu_pd_disaggregation.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/pd_disaggregation/test_npu_pd_disaggregation.py)（supporting）
- [test/registered/npu/basic_function/runtime_opts/test_npu_mla_fia_hicache_bf16.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/registered/npu/basic_function/runtime_opts/test_npu_mla_fia_hicache_bf16.py)（supporting）
- [test/manual/hicache/test_npu_kimi_k3_hicache.py](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/hicache/test_npu_kimi_k3_hicache.py)（supporting）
