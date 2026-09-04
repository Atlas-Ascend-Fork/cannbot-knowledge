---
type: Concept
title: Hunyuan3D 2.0 — 图生 3D 资产生成（NPU 推理适配）
description: Hunyuan3D 是腾讯混元系列在 2025 年推出的图生 3D 资产创作模型，生成带高分辨率纹理贴图的高保真 3D mesh。cann-recipes-spatial-intelligence 提供其昇腾 Atlas A2 单机单卡推理适配版，依赖上游开源仓 Tencent-Hunyuan/Hunyuan3D-2 的网络结构代码，通过非覆盖方式叠加优化模块（替换文件 + module/dit_cache）；实现与测量证据限于该昇腾适配版本，不覆盖上游完整实现。环境为 CANN 8.2.RC1 + torch/torch_npu 2.6。推理通过 python minimal_demo_npu.py 入口启动（source set_env.sh 后），优化后 texgen 在 2 万平面 mesh 输入下推理时间降至约 26 秒。
tags:
- task.design
- topic.three_dimensional_reconstruction
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/models/Hunyuan3D/Hunyuan3D_optimization.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a2
---

# Hunyuan3D 2.0 — 图生 3D 资产生成（NPU 推理适配）

## Summary

Hunyuan3D 是腾讯混元系列在 2025 年推出的图生 3D 资产创作模型，生成带高分辨率纹理贴图的高保真 3D mesh。昇腾 Atlas A2 单机单卡推理适配版依赖上游开源仓 [Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) 的网络结构代码，通过非覆盖方式将优化模块（替换文件 + `module/dit_cache`）叠加进去。环境为 CANN 8.2.RC1 + torch/torch_npu 2.6。推理通过 `python minimal_demo_npu.py` 入口启动（`source set_env.sh` 后），优化后 texgen 在 2 万平面 mesh 输入下推理时间降至约 26 秒。

整条流水线参考 `diffusers` API，分两段：
- **shapegen（Hunyuan3D-DiT，1.1B）**：图像 → 3D 形状（DiT 扩散 + VAE 几何解码），支持单视角与多视角（`Hunyuan3D-2mv`）。
- **texgen（Hunyuan3D-Paint，1.3B）**：mesh + 图像 → 纹理贴图（多视角光栅化 + delight + bake）。

## shapegen 性能优化（Hunyuan3D-DiT）

优化集中在 `hy3dgen/shapegen/models/denoisers/hunyuan3ddit.py` 与顶层 `minimal_demo_npu.py`。

### 融合算子 / 高性能算子替换
- **RmsNorm**：torch 侧无 RmsNorm 接口，原实现以自定义类多算子拼出 `x * rsqrt(mean(x^2)+eps)`；替换为单算子 `torch_npu.npu_rms_norm(x, self.scale, epsilon=self.eps)[0]`。
- **FasterGelu**：用 `torch_npu.npu_fast_gelu` 替换 `nn.functional.gelu`（FastGelu 的泰勒展开化简版，大幅提升 GELU 计算性能）。

### FIA 算子适配（关键，入图前置条件）
官方用的 `scaled_dot_product_attention` 对应 NPU 算子 `npu_fusion_attention`，**不支持图模式**——静态图编译时会被拆成 `BatchMatMul + SoftmaxV2 + BatchMatMul` 三个核心算子，带来性能劣化。改用 `torch_npu.npu_fused_infer_attention_score`（FIA），同时适配增量&全量推理的 FlashAttention，可图编译，并解决 Softmax 溢出与内存连续问题：

```python
def npu_fia(q, k, v, scale):
    batch_size, num_head, seq_len, head_dim = q.shape
    out = torch_npu.npu_fused_infer_attention_score(
        q, k, v, num_heads=num_head, input_layout="BNSD", scale=scale, atten_mask=None
    )[0]
    return out
```

> 在 3D DiT 注意力里，FIA 既是性能算子又是「让 DiT/VAE 能整图编译」的前置条件（`npu_fusion_attention` 不可入图），详见 [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md)。

### torchair 图模式适配
单算子模式有 host bound 与漏掉的融合机会；图模式经计算图优化、多流并行、内存复用、模型下沉加速。通过 `--full_graph` 用 torchair 后端 `torch.compile` 分别使能 **DiT model** 与 **VAE geo_decoder** 两个模块入图（避免标量入图导致编译失败），并开启 tiling 图下沉：

```python
config = torchair.CompilerConfig()
config.experimental_config.keep_inference_input_mutations = True
config.experimental_config.frozen_parameter = True
config.experimental_config.tiling_schedule_optimize = True   # tiling 图下沉
npu_backend = torchair.get_npu_backend(compiler_config=config)
pipeline.model = torch.compile(pipeline.model, dynamic=False, backend=npu_backend, fullgraph=True)
pipeline.vae.geo_decoder = torch.compile(pipeline.vae.geo_decoder, dynamic=False, backend=npu_backend, fullgraph=True)
```

### CPU-NPU 搬运优化
生成时间步时频繁 CPU→NPU 搬运劣化性能；改为在 `timestep_embedding` 中直接以 `device=t.device` 在 NPU 上生成 `freqs`，省去搬运。

### DiT-Cache step-level 适配（3D 差异，见下节）

### shapegen 性能指标
1 卡 Atlas 800I A2，输入 `assets/example_images/004.png`，`num_inference_steps=100`：

| 使能方法 | DIT 扩散耗时（s） | VAE 生成耗时（s） |
|:---:|:---:|:---:|
| baseline | 21.63 | 17.98 |
| 算子优化＋搬运优化 | 20.07 | 18.71 |
| 算子优化+图模式编译 | 19.00 | 16.68 |

## DiT-Cache 在 Hunyuan3D 的 3D 适配差异

DiT-Cache（FBCache / TeaCache / TaylorSeer 三范式）是扩散推理加速的通用缓存框架，概念定义见 [dit-cache](../../../inference/concepts/techniques/dit_cache.md)。Hunyuan3D 复用 `module/dit_cache/cache_method.py`（`CacheManager` + `BaseCache`/`FBCache`/`TeaCache`/`TaylorSeer`/`NoCache`）。

适配差异（相对 cann-infer 视频/图像 DiT 场景）：
- **非 CFG 串行**：Hunyuan3D 为非 CFG 串行项目，`cache_config.json` 中 `enable_separate_cfg=false`（双分支 TeaCache/FBCache 用于 wan2.2 等 CFG 串行场景，且不支持 TaylorSeer）。
- **配置入口**：通过 `models/Hunyuan3D/hy3dgen/cache/cache_config.json` 选择 `cache_forward`（FBCache/TeaCache/TaylorSeer/NoCache）与各范式参数；可 `--cache_config <path>` 自定义路径。插桩点在 `hy3dgen/cache/cache_block.py` 与 `denoisers/hunyuan3ddit`，模型层数（`double_stream_layers`/`single_stream_layers`）由顶层传入 `cache_params`。

实测（63 张图像生成任务，UNI3D/ULIP 指标；TaylorSeer 为 100 步、预热 3、截断 0 的多轮均值）：

| 范式 | 推荐阈值/配置 | 跳过率 | 加速比 | 备注 |
|:---:|:---:|:---:|:---:|:---|
| FBCache | rel_l1=0.05 | 63% | 2.08× | First-Block L1 误差判据 |
| FBCache | rel_l1=0.06 | 66% | 2.47× | 精度损失略增 |
| TeaCache | rel_l1=0.1 | 48% | 1.86× | 推荐；0.2 时跳过 75% 但精度损失 >1% |
| TaylorSeer | O1N3（导数阶数1/跳过间隔3） | 72% | 3.17× | Uni3d-I 0.372 / ULIP-I 0.220 |
| TaylorSeer | O1N5 | 78% | 4.15× | Uni3d-I 0.371 / ULIP-I 0.217 |

TaylorSeer 实现支持 `offload`（多流：`copy_stream`/`cal_stream` + event 串接，预测特征 CPU↔NPU 搬运与计算重叠以降显存）。

DiT-Cache 三范式的概念定义见 [dit-cache](../../../inference/concepts/techniques/dit_cache.md)（FBCache=First-Block L1、TeaCache=Timestep-Embedding 多项式拟合差异、TaylorSeer=高阶导数 Taylor 级数预测）。`cache_config.json` 的完整字段语义与三套 benchmark 全量数据如下。

### cache_config.json 字段语义

`cache_forward` 选择 Cache 方案（`FBCache`/`TeaCache`/`Taylorseer`，否则 `NoCache`）；`enable_separate_cfg` 为 CFG 串行开关（适配 wan2.2 等双分支 TeaCache/FBCache，不支持 Taylorseer；Hunyuan3D 非 CFG 串行，置 `false`）。各范式字段：

```python
"FBCache":{
        "cache_name": "FBCache",
        "rel_l1_thresh": 0.05,   # FBCache 阈值，越大跳过越多、精度损失越大，需平衡性能与精度
        "latent": "latent",
        "judge_input": "cache_latent"
},
"TeaCache":{
        "cache_name" : "TeaCache",
        "rel_l1_thresh": 0.1,    # TeaCache 阈值，越大跳过越多、精度损失越大
        "coefficients": [733.226126,-401.131952,67.5869174,-3.149879,0.0961237896],  # 多项式拟合系数（由输入输出拟合）
        "warmup": 2,             # 预热步数，强制前几步计算
        "latent": "latent",
        "judge_input": "modulated_inp"
},
"Taylorseer":{
        "cache_name" : "Taylorseer",
        "n_derivatives": 3,      # 导数阶数，越大理论上拟合越优，过大可能过拟合且占显存更多
        "skip_interval_steps": 4,# 计算间隔（= 跳过步数+1），越大性能提升越明显、精度越低
        "warmup": 1,             # 预热步数，强制前几步计算
        "cutoff_steps": 1,       # 截断步数，强制最后几步计算
        "offload": false         # offload 开关，开启降低显存占用
}
```

> 注：缓存方法的 JSON key 为 `TaylorSeer`（文档行文写作 `Taylorseer`），FBCache 配置文件内 `rel_l1_thresh` 默认 `0.025`（上例沿用文档示例值 `0.05`）。

### FBCache 阈值扫描（63 张图像生成任务，UNI3D 指标）

|阈值|跳过率|采样耗时（s）|Uni3d-I|加速比|
|:---:|:---:|:---:|:---:|:---:|
|baseline|0|19.28|0.3748|x1.00|
|0.04|50%|10.19|0.3704|x1.89|
|0.05|63%|9.62|0.3687|x2.08|
|0.06|66%|7.80|0.3690|x2.47|

### TeaCache 阈值扫描（63 张图像生成任务，UNI3D/ULIP 指标）

在跳过率为 75% 时精度损失大于 1%，因此推荐使用阈值 0.1：

|阈值|跳过率|采样耗时（s）|Uni3d-I|ULIP-I|加速比|
|:---:|:---:|:---:|:---:|:---:|:---:|
|baseline|0|19.28|0.3179|0.2157|x1.00|
|0.1|48%|10.32|0.3090|0.2050|x1.86|
|0.2|75%|5.83|0.23908|0.1879|x3.30|

### TaylorSeer 导数阶数 × 跳过间隔 benchmark 网格

推理步数 100、预热步数 3、截断步数 0，多轮生成取每次生成时间均值。表头横轴为跳过间隔（0~6），三组（导数阶数 0/1/2）各列总时间/加速比/性能提升：

|导数阶数 |跳过间隔|0|1|2|3|4|5|6|
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
||attention次数|4800|2496|1728|1344|1104|960|864|
||MLP次数|6400|3328|2304|1792|1472|1280|1152|
||预测步数|0|48|64|72|77|80|83|
|0|总时间|19.9s|10.24s|7.66s|6.17s|5.14s|4.58s|3.98s|
|0|加速比|1.00|1.85|2.60|3.23|3.87|4.35|5.00|
|0|性能提升|0%|46.0%|61.5%|69.0%|74.2%|77.0%|79.9%|
|1|总时间|20.44s|11.14s|8.02s|6.44s|5.51s|4.92s|4.35s|
|1|加速比|1.00|1.84|2.55|3.17|3.71|4.15|4.70|
|1|性能提升|0%|45.5%|60.8%|68.8%|72.9%|75.9%|78.7%|
|2|总时间|20.72s|11.47s|8.30s|6.67s|5.82s|5,23s|4.64s|
|2|加速比|1.00|1.81|2.50|3.11|3.56|3.96|4.47|
|2|性能提升|0%|44.7%|60.0%|67.9%|71.9%|74.8%|77.6%|

TaylorSeer 精度对照（O=导数阶数，N=跳过间隔，UNI3D/ULIP 指标）：

|导数/阶数|跳过率|加速比|Dit耗时|性能提升|Uni3d-I|ULIP-I|
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
|baseline|0|1.00|19.26s|0%|0.374|0.221|
|O1N1|48|1.84|11.14s|45.5%|0.374|0.222|
|O1N3|72|3.17|6.4s|68.6%|0.372|0.220|
|O1N5|78|4.15|4.92s|75.9%|0.371|0.217|
|O2N1|48|1.81|11.47s|44.7%|0.374|0.222|
|O2N3|72|3.11|6.67s|67.9%|0.373|0.221|
|O2N5|78|3.96|5.23s|74.8%|0.368|0.217|

> 数据来源：上游 [`docs/models/Hunyuan3D/Hunyuan3D_optimization.md` § DIT-Cache step-level 适配](https://gitcode.com/cann/cann-recipes-spatial-intelligence/blob/92747ee512faebff6068704f893d19d622f7282a/docs/models/Hunyuan3D/Hunyuan3D_optimization.md)。

## texgen 性能优化（Hunyuan3D-Paint）

### 多线程并行光栅化
texgen 在 6 个视角分别投影法向/位姿/纹理信息，共 18 次光栅化。CPU 侧串行光栅化时延巨大；法向计算、位姿计算与 delighting 来自不同数据通路、无数据依赖，可并行隐藏时延。改造 `hy3dgen/texgen/pipelines.py`：用 `ThreadPoolExecutor`（`max_workers=min(20, total_tasks)`）并发提交 `render_normal`/`render_position`（`_delighting_render_multiview`）与 `back_project`（`_bake_from_multiview`），用 `as_completed` 收集。

### aicpu 算子迁移
FP32 数据会使 `torch.mean`/`torch.std` 落到 aicpu 上、性能下降。手动把相关张量转为 `torch.float16` 使其回到 aicore：`pipelines.py` 的 `texture`、`dehighlight_utils.py` 的 `src_mean/src_stddev`、`target_mean/target_stddev` 及 `image_tensor` 均改用 fp16。

### Inpaint 计算优化
生成的 3D mesh 纹理存在未上色点，需平滑补全。源码默认走 Python 版 `meshVerticeInpaint`；手动改为 `import mesh_processor` 的 C++ 版（`mesh_processor.meshVerticeInpaint(...)`），性能更优。

### 光栅化结果复用
18 次光栅化只有 6 种不同相机输入，其余 12 次冗余。以 `(elev, azim, camera_distance)` 为 key 把首次 `rast_out` 缓存进 `self.render_result`，相同位姿直接命中（`--save_render`）。

### 光栅化过程 NPU 迁移（render_npu）
源码光栅化无 NPU 版本、被迫迁 CPU 串行。`cann-recipes-spatial-intelligence` 引入 `render_npu`：把「遍历 mesh 顶点」改为「二维平面分块，每块内三角网格合并成矩阵计算深度/重心坐标，再判定每像素对应三角面片」（`--use_render_npu`）。NPU 侧为小算子计算，**不能与多线程并行光栅化共用**（`--multi_thread` 与 `--use_render_npu` 互斥）。

### texgen 性能指标
1 卡 Atlas 800I A2，输入 `assets/example_images/004.png`，mesh 面数 20000，开启 `--face_reduce`：

| 使能方法 | texgen 运行时长（s） |
|:---:|:---:|
| baseline | 59.83 |
| 光栅化并行 | 35.43 |
| 光栅化并行+算子优化 | 30.46 |
| NPU光栅化+算子优化+Inpaint优化+结果复用 | 32.86 |
| 光栅化并行+算子优化+Inpaint优化+结果复用 | 26.52 |

## 推理启动

```bash
source set_env.sh   # 把 module 优化模块（含 dit_cache）加入环境变量
python minimal_demo_npu.py --model_path tencent/Hunyuan3D-2 \
  --multiview --face_reduce --full_graph --multi_thread --save_render
```
开关：`--multiview` 多视角；`--face_reduce` 减面；`--full_graph` 图模式；`--multi_thread` 多线程并行光栅化；`--use_render_npu` NPU 光栅化（与 `--multi_thread` 互斥）；`--save_render` 复用光栅化结果。

权重支持 Hunyuan3D-DiT-v2-0（单视角）、Hunyuan3D-DiT-v2-mv（多视角）、Hunyuan3D-Paint-v2-0（纹理）、Hunyuan3D-Delight-v2-0（去高光），默认 `base_dir=~/.cache/hy3dgen/`。

## Links

Hunyuan3D 的计算模块与优化机制：
- [dit](../../../inference/concepts/modules/dit.md) — DiT 是 shapegen 形状生成主干；Hunyuan3D 是其 3D 图生场景部署。
- [dit-cache](../../../inference/concepts/techniques/dit_cache.md) — Hunyuan3D 在非 CFG 串行场景中使用 FBCache、TeaCache 与 TaylorSeer，缓存阈值和跳过间隔影响生成精度与加速比。
- [vae](../../../inference/concepts/modules/vae.md) — VAE geo_decoder 负责几何解码，与 DiT 一同入图编译。
- [torchair](../../../inference/concepts/frameworks/torchair.md) — `--full_graph` 经 torchair 后端 `torch.compile` 入图。
- [npu-graph-mode](../../../inference/concepts/techniques/npu_graph_mode.md) — 图模式优化（计算图优化/多流/内存复用/模型下沉/tiling 下沉）。
- [fused-infer-attention-score](../../../inference/concepts/kernels/fused_infer_attention_score.md) — FIA 替换 `npu_fusion_attention`，是 DiT/VAE 整图编译的前置条件。
- [multi-stream](../../../inference/concepts/techniques/multi_stream.md) — TaylorSeer offload 用 copy/cal 双流 + event 重叠搬运与计算。
- [ascendc](../../../inference/concepts/frameworks/ascendc.md) — render_npu / 自研光栅化小算子的实现底座。
- [atlas-a2](../platforms/atlas_a2.md) — 目标平台。

源：[cann-recipes-spatial-intelligence](https://gitcode.com/cann/cann-recipes-spatial-intelligence/tree/92747ee512faebff6068704f893d19d622f7282a)
