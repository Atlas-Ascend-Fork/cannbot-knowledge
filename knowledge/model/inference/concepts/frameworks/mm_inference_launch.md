---
type: Concept
title: MM Inference Launch（多模态生成模型统一推理拉起架构）
description: 'MM Inference Launch 是 cann-recipes-infer 为 Wan2.2-I2V、HunyuanVideo、SANA-Video 和 HunyuanImage-3.0 提供的统一多模态推理启动层。各模型以 infer.sh 和场景 YAML 为入口，mm_function.sh 负责字段校验、环境合并、cache/sparse 参数生成，并选择 torchrun 或 accelerate，日志统一写入模型 res 目录。YAML 对必填键、未知键、端口/卡数类型以及 Dit-Cache 和 sparse 方法枚举做校验；环境优先级为 NPU 默认→YAML→MODEL_BASE 派生→HCCL→用户 export。HunyuanVideo 的块稀疏 Attention 可配单卡或 Ulysses，但不支持 Ring，且与 cache 互斥。该体系独立于 LLM 的 CANN Executor。'
tags:
- task.implementation
- topic.architecture
- topic.attention
- topic.multimodal
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/design/mm_inference_design.md
  role: primary
created_at: '2026-05-31T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a3
- '950'
---

# MM Inference Launch（多模态生成模型统一推理拉起架构）

## Summary

MM Inference Launch 是 cann-recipes-infer 中 4 个多模态生成模型（Wan2.2-I2V / HunyuanVideo / SANA-Video / HunyuanImage-3.0）的统一推理拉起架构：每个模型以 `infer.sh` 为入口，切换 YAML 选择推理场景；YAML 集中管理公共字段、启动器、环境变量、Dit-Cache、块稀疏 Attention 与模型透传参数；统一函数库 `executor/scripts/mm_function.sh` 负责校验、解析、环境设置与启动。启动器支持 `torchrun` 与 `accelerate`；日志统一输出到 `models/{MODEL_DIR}/res/{YYYYMMDD}/{model_name}/`。这是一套**拉起与配置体系**——Dit-Cache、块稀疏 Attention、序列并行的方法细节各有专页（见下文链接），此处描述它们作为 YAML 段如何被框架检测与透传。

> 与 LLM 侧的 [cann-executor](cann_executor.md)（`OfflineInference` / `InferenceConfig` / `ge_graph`）是不同体系：多模态走 `infer.sh` + `mm_function.sh` + `torchrun`/`accelerate`，不经 CANN Executor 五组件，两者不混用。

## 目录与执行流程

```
models/{model_name}/
├── infer.sh                  # 统一入口，仅 source mm_function.sh + 导出 MODEL_DIR/YAML + mm_launch
├── config/{scenario}.yaml    # 各推理场景配置
└── {entry_script}            # YAML entry_script 指向的 Python 入口

executor/scripts/mm_function.sh   # 统一拉起函数库
```

`bash infer.sh` 内 `mm_launch()` 依次调用（函数名见 `mm_function.sh`）：

```
mm_launch()
  ├── mm_init_env()             # 计算 RECIPES_ROOT（脚本上溯两级）
  ├── mm_check_launch()         # 校验 YAML 环境变量已设置且文件存在
  ├── mm_validate_yaml()        # 必填键 / 顶层键白名单 / dit_cache.method·sparse.method 枚举校验
  ├── mm_parse_yaml()           # 公共字段解析到 shell 变量（MODEL_NAME/WORLD_SIZE/MASTER_PORT/ENTRY_SCRIPT/LAUNCHER）
  ├── mm_setup_env()            # NPU 默认 env → YAML env_vars → MODEL_BASE 派生 → HCCL → 日志目录
  ├── mm_generate_cache_config()  # 检测 dit_cache 段，拼 --cache-config / --cache_config
  ├── mm_generate_sparse_config() # 检测 sparse 段，拼 --sparse-method / --sparse-attention-config
  └── mm_launch_task()          # mm_build_args 透传 model_args + 按 launcher 调 torchrun 或 accelerate
```

`mm_validate_yaml` 在任何子进程拉起前快速失败：缺失 `model_name/world_size/entry_script`、出现未知顶层键、`world_size/master_port` 类型错误、或 `dit_cache.method ∉ {NoCache,FBCache,TeaCache,TaylorSeer}` / `sparse.method ∉ {no_sparse,TopK,SVG}` 都立即打印 `[ERROR]` 退出；`model_args` 子项不在此校验，由入口脚本 `argparse` 自行拒绝未识别 flag。

## YAML 配置体系

YAML 是推理配置的唯一来源，顶层键白名单（`ALLOWED_TOP`）共 10 个，分五类：

| 类别 | 字段 | 必填 | 说明 |
|------|------|------|------|
| 公共 | `model_name` / `world_size` / `entry_script` | 是 | 模型标识 / NPU 卡数 / 入口脚本（相对模型目录） |
| 公共 | `master_port` | 否 | 默认 29600 |
| 启动器 | `launcher` | 否 | `torchrun`（默认）或 `accelerate` |
| 启动器 | `launcher_args` | 否 | **仅 accelerate 生效**，每对 `k: v` → `--k=v` |
| 环境变量 | `env_vars` | 否 | 按原样 export，覆盖 NPU 默认值 |
| Dit-Cache | `dit_cache` | 否 | 缓存方法配置段，见下文 |
| 块稀疏 | `sparse` | 否 | 块稀疏 Attention 段（仅 HunyuanVideo），见下文 |
| 模型参数 | `model_args` | 否 | 透传给 `entry_script` 的命令行参数 |

- **`model_args` 透传规则**：字符串/数字 → `--key value`；列表 → `--key v1 v2`（`nargs="+"`）；布尔 `true` → `--key`（flag）；布尔 `false` → 忽略；加引号字符串 `"False"`/`"True"` → 按字面量透传（如 `sana-video` 的 `model.fp32_attention: "False"`）。`model_args` 非白名单，任意被 `argparse` 接收的参数（权重路径、量化开关、profiler 开关等）均可传入。
- **`world_size` 映射**：`torchrun` 下 `--nproc_per_node`，`accelerate` 下 `--num_processes`；`master_port` 同理映射 `--master_port` / `--main_process_port`。
- **env 优先级**（`mm_setup_env`，后者覆盖前者）：① NPU 默认值（`VAR:-default`，仅 shell 未设时生效：`PYTORCH_NPU_ALLOC_CONF`/`TASK_QUEUE_ENABLE=2`/`CPU_AFFINITY_CONF=1`/`TOKENIZERS_PARALLELISM=false`）→ ② YAML `env_vars`（无条件 export）→ ③ `MODEL_BASE` 从 `model_args.model-base` 自动派生（HunyuanVideo `hyvideo/constants.py` import 时把 `MODEL_BASE` freeze 进 VAE/Text-Encoder/Tokenizer 路径）→ ④ HCCL 硬编码（`HCCL_IF_IP`/`HCCL_IF_BASE_PORT=23456`/`HCCL_CONNECT_TIMEOUT=1200`/`HCCL_EXEC_TIMEOUT=1200`，覆盖 YAML 同名值）→ ⑤ `ASCEND_RT_VISIBLE_DEVICES` 等由用户手动 export。

### 关键实现细节

- **PYTHONPATH 注入**：拉起子进程时以命令行前缀 `eval PYTHONPATH=${RECIPES_ROOT}:$PYTHONPATH torchrun/accelerate ...` 注入，仅作用于推理子进程，不污染当前 shell 与 CANN TBE 编译器解释器。
- **Cache 参数名自动选择**（`mm_generate_cache_config`）：`model_name` 含 `hunyuan-video` → `--cache-config`（连字符），其他 → `--cache_config`（下划线）。
- **accelerate 解析**（`mm_resolve_accelerate_bin`）：优先用当前 `python` 所在环境的 `accelerate`，避免 `PATH` 命中其他环境的用户级脚本。

## 作为配置段被透传的方法（细节见专页）

- **Dit-Cache**：`dit_cache` 段是唯一配置源；`mm_generate_cache_config` 把 YAML 路径作为 `--cache-config`/`--cache_config` 传给入口脚本，由 `module/dit_cache/cache_method.py:load_cache_config()` 读取并与 `DEFAULT_CACHE_CONFIG` 合并构造 `CacheManager`。`method` 取 `NoCache`/`FBCache`/`TeaCache`/`TaylorSeer`，`params` 段只需写想覆盖的键。方法判据、默认值与 benchmark 见 [dit-cache](../techniques/dit_cache.md)。
- **块稀疏 Attention（仅 HunyuanVideo）**：顶层 `sparse` 段与 `dit_cache` 并列；`mm_generate_sparse_config` 检测后拼 `--sparse-method <method> --sparse-attention-config <yaml>`，由 `module/blockwise_sparse/sparse_method.py:load_sparse_config_from_file` 读取。`method` 取 `no_sparse`/`TopK`/`SVG`，启用后会覆盖所有 Dit-Cache 的 block forward（二者互斥）。并行支持详见下文「块稀疏 Attention `sparse` 段语义」。算法细节见 [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md)。
- **序列并行 / CFG 并行**：多卡场景由 `model_args` 的 `ulysses-degree`/`ulysses_size`、`cfg_size`、`ring-degree`/`ring_size` 等控制（约束 `world_size = cfg_size * ulysses_size * ring_size`）。Ulysses 见 [ulysses](../parallelism/ulysses.md)，CFG 并行见 [cfg-parallel](../parallelism/cfg_parallel.md)。

### Dit-Cache 各方法默认值（`module/dit_cache/cache_method.py:DEFAULT_CACHE_CONFIG`）

`dit_cache.params` 只需写想覆盖的键，未写的键沿用下表默认值（设计文档 §5.3）。`TaylorSeer` 的完整默认配置（`n_derivatives=3` / `skip_interval_steps=4` / `warmup=3` / `cutoff_steps=1` / `offload=true`）尤其需要注意——它与 `FBCache` / `TeaCache` 的参数集完全不同：

| 方法 | 参数 | 默认 | 说明 |
|------|------|------|------|
| `FBCache` | `rel_l1_thresh` | 0.05 | L1 差异阈值，越大越快、质量越低 |
| | `latent` | `"latent"` | 命中判定所用的张量 key |
| | `judge_input` | `"cache_latent"` | 用于缓存命中判定的输入 |
| `TeaCache` | `rel_l1_thresh` | 0.15 | 累积 L1 阈值 |
| | `coefficients` | `[733.23, -401.13, 67.59, -3.15, 0.096]` | 多项式重缩放系数 |
| | `warmup` | 2 | 前 N 步强制完整计算 |
| | `latent` | `"latent"` | 同上 |
| | `judge_input` | `"modulated_inp"` | 同上 |
| `TaylorSeer` | `n_derivatives` | 3 | Taylor 展开阶数 |
| | `skip_interval_steps` | 4 | 每 N 步做一次完整计算 |
| | `warmup` | 3 | 前 N 步强制完整计算 |
| | `cutoff_steps` | 1 | 最后 N 步强制完整计算 |
| | `offload` | `true` | 是否将导数缓存 offload 到 CPU |
| `NoCache` | — | — | 禁用缓存，按 DiT 原始前向执行 |

> 上表 `TeaCache.coefficients` 的 `[733.23, -401.13, 67.59, -3.15, 0.096]` 是设计文档表的四舍五入显示；代码默认值（`DEFAULT_CACHE_CONFIG` 字面量，`cache_method.py:41`）实为全精度 `[733.226126, -401.131952, 67.5869174, -3.149879, 0.0961237896]`，YAML 示例复用同一串。

### Cache-config 校验契约（`_validate_config_keys`，设计文档 §8.3）

合并后的缓存配置（YAML `dit_cache` 段 + `DEFAULT_CACHE_CONFIG`）必须包含以下 **6 个必备键**，缺任一键即立即退出并打印 `[ERROR]`（设计文档 §8.3）：

1. `cache_forward`
2. `enable_separate_cfg`
3. `FBCache`
4. `TeaCache`
5. `NoCache`
6. `TaylorSeer`

> 同节还有两条前置校验：`mm_check_launch` 校验 `YAML` 环境变量已设置且文件存在；`mm_setup_env` 校验 `entry_script` 解析后的绝对路径存在。三者任一失败均立即退出。

### 块稀疏 Attention `sparse` 段语义（设计文档 §5.5）

`sparse` 段内联在启动 YAML 顶层（与 `dit_cache` 并列），`mm_function.sh` 检测到后自动拼 `--sparse-method <method> --sparse-attention-config <yaml>` 透传给 `sample_video.py`；`module/blockwise_sparse/sparse_method.py:load_sparse_config_from_file` 读取顶层 `sparse` 段并扁平化成内部结构（向后兼容老的扁平 `sparse_config.yaml`）。完整字段示例（设计文档 §5.5）：

```yaml
sparse:
  method: "SVG"                      # [no_sparse, TopK, SVG]
  block_size_Q: 128
  block_size_K: 512
  model: "HunyuanVideo"
  params:
    TopK:                            # only used when method == TopK
      sparse_time_step: "10-49"
      sparsity_files_path: "./sparsity/320x480x65/v3"
      CAC_threshold: 0.66
    SVG:                             # only used when method == SVG
      sparse_time_step: "14-49"
      sparsity: 0.8
      sample_mse_max_row: 5000
      context_length: 256
```

字段语义：`block_size_Q=128` / `block_size_K=512` 为 `torch_bsa` 算子的块粒度；`method ∈ {no_sparse, TopK, SVG}`；`TopK.sparse_time_step`/`SVG.sparse_time_step` 为生效的去噪步区间（如 `"14-49"`）；`SVG.sparsity=0.8` 为稀疏率，`SVG.sample_mse_max_row=5000` 为采样 MSE 的最大行数、`SVG.context_length=256` 为上下文长度；`TopK.sparsity_files_path` 指向离线 profiling 生成的 sparsity 文件、`TopK.CAC_threshold=0.66`。

并行支持（更新自设计文档 §5.5）：

- **支持单卡、Ulysses 多卡和 Ring Attention 多卡**。Ulysses sparse forward 内置 all-to-all 通信路径，并在 `ulysses_degree > 1` 时调用 `apply_head_reorder_for_load_balance` 做 head 级负载均衡；Ring sparse forward 支持 TopK/SVG，**Ring + TopK 额外支持 overlap 路径**（`config/sp8_sparse_overlap.yaml`，默认 TopK 可切 SVG），Ring + SVG overlap 暂复用普通 Ring + SVG 路径。
- **与 Dit-Cache 互斥**：`sample_video.py` 先初始化 cache_manager 替换 block forward，再在 sparse 启用时把**所有** double/single block forward 替换为 sparse 版——sparse 会静默覆盖 FBCache/TeaCache/TaylorSeer 的 block forward。预置的 `single_sparse.yaml` / `sp8_sparse.yaml` / `sp8_sparse_overlap.yaml` 均固定 `dit_cache.method: NoCache`（§5.5 互斥说明列前两者，`sp8_sparse_overlap` 变体见 §6 配置表）。
- **TopK 前置**：`TopK` 策略需先跑 `module/blockwise_sparse/offline_profiling/offline_profiling_hyvideo.py` 生成 sparsity 文件（规格须与 `video-size / video-length` 一致——单卡默认 `320*480*65`，多卡默认 `720*1280*129`）；`SVG` 无需离线 profiling。
- **算子依赖**：运行前需依据 `blitz_sparse_attention` 算子文档编译对应算子库。

> ⚠️ 矛盾标记：早期设计文档（@2c45117）记载块稀疏 Attention「**不支持 Ring**」（`sample_video.py` 在 `ring_degree>1` 抛 `ValueError`，2026-05-31 ingest）；最新设计文档（@46485be，2026-06-23）改为「**支持 Ring**，Ring + TopK 额外支持 overlap」，并新增 `config/sp8_sparse_overlap.yaml`。以最新版本为准，旧版结论保留于此供追溯。

## 各模型 config 变体清单（对照 `models/*/config/` @2c45117，`sp8_sparse_overlap` 为 @46485be 新增）

| 模型 | config 变体 | 卡数 | 启动器 |
|------|-------------|------|--------|
| [wan2.2-i2v](../models/wan2_2_i2v.md) | `14b_single`（cache 注释切 NoCache/FBCache/TeaCache）/ `14b_cfg2_ulysses4`（CFG2×Ulysses4） | 1 / 8 | torchrun |
| [hunyuan-video](../models/hunyuan_video.md) | `single`·`sp8`（cache 注释切 NoCache/FBCache/TeaCache/TaylorSeer）/ `single_fp8`（FP8 FA + MXFP8 matmul）/ `single_sparse`·`sp8_sparse`（块稀疏 SVG/TopK）/ `sp8_sparse_overlap`（@46485be 新增；Ring + 块稀疏 overlap，默认 TopK） | 1 / 8 | torchrun |
| [sana-video](../models/sana_video.md) | `2b_480p_single` / `_a4w4` / `_a8w8`（量化）/ `_platform`（平台模板，经 `infer_platform.sh` 直拉） | 1 | accelerate（`_platform` 除外：直 `python -u`） |
| [hunyuan-image-3](../models/hunyuan_image_3.md) | `ep8_cfg`（Attn TP8 + MoE EP8 + CFG 并行 + VAE 并行） | 16 | torchrun |

> Cache 方法在 HunyuanVideo / Wan2.2-I2V 的基线 YAML 内通过 `dit_cache.method` 切换并在注释列出可选值，**没有** 为每种 cache 方法单独派生 YAML；`single_fp8` 的 950PR 平台要求为 README/设计文档级说明，YAML 仅含 `fa-perblock-fp8`/`mm-mxfp8` 开关，无平台字段。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/design/mm_inference_design.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/design/mm_inference_design.md)（统一推理拉起设计文档，MR!356）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/design/mm_inference_design.md` §5.3 / §5.5 / §8.3](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/design/mm_inference_design.md)（@46485be：Dit-Cache 各方法默认值、`sparse` 段字段语义、`_validate_config_keys` 6 必备键校验契约；块稀疏 Attention 改为支持 Ring + overlap）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`executor/scripts/mm_function.sh`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/scripts/mm_function.sh)（拉起函数库：函数名/校验/env/透传规则）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/{hunyuan-video,wan2.2-i2v,sana-video,hunyuan-image-3.0}/{infer.sh,config/}`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-video/infer.sh)（统一入口 + config 变体清单来源）

## Links

- [wan2.2-i2v](../models/wan2_2_i2v.md)
- [hunyuan-video](../models/hunyuan_video.md)
- [sana-video](../models/sana_video.md)
- [hunyuan-image-3](../models/hunyuan_image_3.md)
- [dit-cache](../techniques/dit_cache.md)
- [blockwise-sparse-attention](../modules/blockwise_sparse_attention.md)
- [ulysses](../parallelism/ulysses.md)
- [cfg-parallel](../parallelism/cfg_parallel.md)
- [cann-executor](cann_executor.md)

## Notes

- **doc/code nuance**：SANA-Video `2b_480p_single_platform` 的 YAML `launcher` 字段虽为 `accelerate`（与其余 sana 变体一致），但其入口 `infer_platform.sh` 只手动跑函数链子集（`mm_init_env`/`mm_check_launch`/`mm_parse_yaml`/`mm_setup_env`/`mm_generate_cache_config`/`mm_build_args`）后用 `python -u` 直拉（`infer_platform.sh:218`「python direct, no accelerate wrapper」、`:245`），**绕过 `mm_launch`/launcher 分发**——故该变体的 `launcher: accelerate` 字段惰性无效。设计文档 §6「python 直接拉起」为真实运行行为。
- **gap**：本架构无端到端 benchmark；各模型性能数据见各自模型页（如 HunyuanVideo Atlas A3 e2e 7.81×）。
- **scope**：覆盖范围为 4 个多模态生成模型的拉起与 YAML 配置；LLM 侧部署走 [cann-executor](cann_executor.md)，二者不共享拉起路径。

## 已知冲突

- 块稀疏 Attention Ring 支持：@2c45117 记载不支持 Ring；@46485be 改为支持 Ring（Ring+TopK 含 overlap）。以最新版本为准。