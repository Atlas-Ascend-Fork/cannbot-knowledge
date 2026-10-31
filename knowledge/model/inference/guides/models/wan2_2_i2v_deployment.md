---
type: Guide
title: Wan2.2-I2V 当前部署与验收
description: 当前A2/A3/950部署、统一三类YAML、CFG2默认与CFG1性能表差异、单卡缓存和多卡强制NoCache。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/config/14b_single.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md
  role: supporting
created_at: '2026-10-21T09:56:21Z'
updated_at: '2026-10-29T14:15:06Z'
platforms:
- a2
- a3
- '950'
---

# Wan2.2-I2V 当前部署与验收

## 环境与输入

当前README覆盖A2/A3/950：A2/A3要求CANN≥8.5.0、PyTorch2.7.1与torch_npu发布v7.3.0；950要求CANN≥9.0.0、PyTorch2.7.1与扩展发布v26.0.0。按架构、Python和驱动匹配实际wheel，不把不同平台组合混用。

上游Wan2.2代码非覆盖合入模型目录，安装requirements；准备I2V-A14B BF16的high_noise_model、low_noise_model、T5与Wan2.1_VAE。YAML的model_args.ckpt_dir指向完整权重，image/prompt/base_seed/size/frame_num/sample_steps确定任务。实际权重与依赖版本另记入运行记录。

## 当前统一入口

在models/wan2.2-i2v运行infer.sh，以YAML_FILE_NAME选择配置：

- 14b_single.yaml：单卡640×360、61帧、40步，convert_model_dtype=true；dit_cache.method可选NoCache/FB/Tea。
- 14b_cfg2_ulysses4.yaml：8卡、CFG2×Ulysses4、Ring1，1280×720×81、40步，DiT/T5 FSDP和VAE并行开启。
- 14b_single_platform.yaml：由infer_platform.sh读取的平台模板，实际路径先按本机填写。

普通入口调用mm_function.sh并torchrun generate.py；项目PYTHONPATH仅给子进程注入，日志在res/<日期>/<模型>/。布尔false被省略，不能假设可关闭argparse中默认为true的键；需显式字面量时核对解析器。

## 并行、融合与缓存

world_size=cfg_size×ulysses_size×ring_size；帧数按模型4n+1约束。CFG并行分别处理条件/负向分支并聚合；VAE使用共享H/W空间patch，卷积边界、插值与进程组按[VAE专题](../../concepts/parallelism/vae_patch_parallel.md)核对。Ring默认可用AllGather与本地FA重叠，再LSE合并。

单卡缓存配置已归统一YAML的dit_cache.method/params，实际公共实现是module/dit_cache/cache_method.py。Tea内置阈值0.15，单卡YAML注释仍示例0.1，取消注释即覆盖默认，两者不混同。串行CFG保留enable_separate_cfg并验证分槽。多卡world_size>1入口会记录日志且强制替换NoCache，不会获得缓存跳步加速。

当前优化文档的LayerNorm调制片段已将入参修正为scale，旧“未定义scale”的结论撤销；片段仍需核对实际gamma/beta和布局后使用，来源文档不是任意形状保证。

## 来源性能与验收

README的8卡性能表使用CFG1×Ulysses8、Ring1，区别于默认CFG2×Ulysses4：832×480×61的A2/950 E2E为102.54/52.24s，1280×720×81为418.01/303.17s。来源未给完整build、逐轮样本与方差，不将该表直接归给默认配置，本次未复测。

先NoCache固定seed验收参考图一致性和时间连贯性，再逐项比较并行/缓存，记录Host/NPU峰值、输出质量、重复E2E及日志中的最终缓存方法。异常恢复相同规格的NoCache和合法并行；不要用旧JSON片段或旧run.sh参数拼接当前YAML。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/README.md)（primary）
- [14b_cfg2_ulysses4.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/config/14b_cfg2_ulysses4.yaml)（example）
- [14b_single.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/config/14b_single.yaml)（example）
- [generate.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py)（implementation）
- [wan2.2-i2v_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/wan2.2-i2v/wan2.2-i2v_optimization.md)（supporting）
