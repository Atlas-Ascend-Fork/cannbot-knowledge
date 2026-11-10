---
{
  "type": "Runbook",
  "title": "deepseek_v4 custom_params 纯配置约束校验发生在 275GB 权重加载之后（失败反馈慢）",
  "description": "deepseek_v4 的 custom_params 约束（limit_core×multi_streams、pypto×limit_core）校验挂在 model_worker.py:275-276 的 check_model_settings（模型构建/权重加载之后），每次违反都要先完整加载 275GB 权重才报错（冷启动约 5 分钟、热缓存约 19-60 秒实测）；对照 dataset 白名单校验挂在 infer.py:54（权重加载前）可秒级失败。纯配置类约束可前移至配置解析阶段（建议未实施）。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# deepseek_v4 custom_params 纯配置约束校验发生在 275GB 权重加载之后（失败反馈慢）

## 适用场景

- 模型/框架：cann-recipes-infer `models/deepseek_v4`（DeepSeek-V4 Flash，INT8 W8A8，`${LOCAL_PATH_1}` 275GB、46 个 safetensors 分片），统一推理入口；约束校验点为 `models/deepseek_v4/models/modeling_deepseek.py` 的 `check_model_settings`（README custom_params 表声明的 limit_core×multi_streams 依赖、pypto×limit_core 互斥等）。
- 平台/版本：Atlas A3（Ascend 910_9362 ×16），CANN 9.2.0（容器 `cann_recipes_infer` 系，镜像 `cann9.2.0.pt2.9.0_dsv4_aarch_a3_image_custom_20260827`），torch 2.9.0、transformers 5.0.0。
- 工作负载：快速迭代 YAML 配置（custom_params 类纯配置项）时的失败反馈延迟评估；冷/热权重加载两种情形。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${RECIPES_ROOT}` 为cann-recipes-infer 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：custom_params 纯配置约束违反——`enable_limit_core=True` 且 `enable_multi_streams=False`（V1/ct1）；`enable_pypto=True` 且 `enable_limit_core=True`（V2/ct2）。

逐字客观输出：

- 来源记录 T 170（V1，报错在权重加载后的 check_model_settings）：
```
T 170 | [rank0]:     self.model.check_model_settings()
[rank0]:   File "${RECIPES_ROOT}/models/deepseek_v4/models/modeling_deepseek.py", line 2469, in check_model_settings
[rank0]:     raise ValueError(f"{enable_limit_core=} only if enable_multi_streams!")
[rank0]: ValueError: enable_limit_core=True only if enable_multi_streams!
[ERROR] 2026-10-17-04:12:27 (PID:55724, Device:0, RankID:-1) ERR99999 UNKNOWN applicaiton exception
===RANKS===
2
```
- 来源记录 T 137（历史 verify 用例 rank0 日志，报错前先出现权重加载完成）：
```
[INFO][2026-10-13 04:23:38.881][patch_getenv.py:15] get env LOCAL_RANK = 0
[INFO][2026-10-13 04:23:43.131][comm_manager.py:442] CommManager: group 'cp_group' registered (my_subgroup=[0], reuse=True, rank_in_group=0)
[INFO][2026-10-13 04:24:12.390][default_loader.py:173] Loading weights took 18.72 seconds
---rank0 error context---
[INFO][2026-10-13 04:24:12.390][default_loader.py:173] Loading weights took 18.72 seconds
[rank0]: Traceback (most recent call last):
```
- 主样例冷启动权重加载时长（来源记录 T 122 进度条 + T 213 时间线）：`Loading safetensors checkpoint shards:  70% Completed | 32/46 [02:57<01:16,  5.45s/it]`；进程时间线 `03:50:23 ... get env PATH` → `03:55:33 [execution_engine.py:753] Starting warm-up...`（冷加载约 5 分钟）。

## 探针与操作

- 探针 YAML（来源记录 C 157，从 platform yaml 派生）：`sed 's/enable_multi_streams: True/enable_multi_streams: False/; s/enable_limit_core: False/enable_limit_core: True/' deepseek_v4_flash_rank_16_16ep_w8a8_platform.yaml > cv_v1_limit_core_no_streams.yaml`（V2 同型）；来源记录 C 242/C 245 与 来源记录 C 165-C 178 区用同型派生（ct1/ct2）。
- 运行：`timeout 720 bash executor/scripts/infer.sh --model deepseek_v4 --yaml ci_a3/cv_v1_limit_core_no_streams.yaml > ${LOCAL_PATH_2} 2>&1; echo EXIT=$?`（容器内执行，`$?` 为 infer.sh 退出码）。
- 时间点观测：用 `grep -m1 "get env LOCAL_RANK"` 取 rank 启动时刻、取日志末行 ERR99999 时刻做差。

## 机制与判别

机制（校验调用位置，来源记录 T 154 grep 原文）：

```
executor/core/model_worker/model_worker.py:218:        if hasattr(model_cls, "check_model_config_before_loading"):
executor/core/model_worker/model_worker.py:219:            model_cls.check_model_config_before_loading(self.hf_config, self.infer_config)
executor/core/model_worker/model_worker.py:275:        if hasattr(self.model, "check_model_settings"):
executor/core/model_worker/model_worker.py:276:            self.model.check_model_settings()
```

- 结论 1：deepseek_v4 的 custom_params 纯配置约束（limit_core×multi_streams、pypto×limit_core）校验挂在 `check_model_settings`（model_worker.py:275-276，模型构建之后），而权重加载先于模型构建完成，因此每次违反约束都要先完整加载权重才能看到报错。
  - 信号：来源记录 T 170（traceback 直接显示 `self.model.check_model_settings()` → modeling_deepseek.py:2469）；来源记录 T 137（rank 启动 04:23:38 → `Loading weights took 18.72 seconds` 04:24:12 → Traceback，同一日志内先后出现）；来源记录 T 255（ct1：`ValueError: enable_limit_core=True only if enable_multi_streams!` 紧跟 `Loading weights took 59.84 seconds`）、T 266（ct2：`Loading weights took 23.95 seconds` → pypto 互斥 ValueError）；来源记录 T 183（rank 启动 00:57:07.696 → ERR99999 00:57:51，约 44 秒，含权重加载）。
- 结论 2：对照校验点在权重加载之前的约束可秒级失败——dataset 白名单校验挂在 `executor/offline/infer.py:54` 的 `generate_prompt`（prompt 生成阶段，先于权重加载），V3 负向用例（dataset="InfiniteBenchX"）在配置打印（04:11:34.956）同一秒内即抛 `Exception: your dataset InfiniteBenchX is not supported, dataset supported: default, default_multimodal, LongBench, InfiniteBench, MMMU`，未做任何权重加载。
  - 信号：来源记录 T 162（配置打印与 Exception 同秒）；来源记录 T 167/179（ct4/ct5 亦在加载早期快速失败）。
  - 判别：同为"配置写错"，反馈延迟由校验挂载位置决定（加载前 vs 加载后），而不是报错文案差异。
- 结论 3：失败代价随缓存状态变化——冷启动加载 275GB/46 分片约 5 分钟（来源记录 T 122/T 213），热缓存（页缓存命中）下加载约 18.72-59.84 秒（来源记录 T 137/T 255/T 266），即冷环境下每次写错 custom_params 需等待约 5 分钟级反馈。
- 未验证推断（轨迹内未实施修复）：把 custom_params 纯配置校验前移至配置解析阶段（inference_config.py / infer 启动早期）可实现秒级失败；两条轨迹报告均如此建议，未验证。

## 验证信号

- 校验位置原文：来源记录 T 154（model_worker.py:218-219/275-276 grep 原文）。
- 加载后报错的直接证据：来源记录 T 170（V1 traceback + ERR99999 04:12:27）、T 173（V2 `ValueError: enable_pypto=True does not support enable_limit_core=True!` + EXIT=0）；来源记录 T 137/T 255/T 266（加载完成日志与 ValueError 同日志先后出现）；来源记录 T 183（00:57:07 → 00:57:51 约 44 秒）、T 187/T 190/T 194（ct2/ct3/ct6 同型）。
- 冷加载时长：来源记录 T 122（46 分片约 5.45-6.25 s/it）、T 213（03:50:23 → 03:55:33）。
- 对照组（加载前秒级失败）：来源记录 T 162；来源记录 T 281 区域（ct6 bad_dataset 在 infer.py:54 快速失败）；来源记录 T 167。
- 平台与证据等级：Atlas A3 容器内执行；以上均为工具结果原文；每类负向用例每条轨迹各 1 次，跨 3 条轨迹（2026-10-14/15/17）复现同一模式。

## 适用与失效边界

- 适用：cann-recipes-infer 统一入口 + 自定义 check_model_settings 的模型（deepseek_v4）；对反复试错 YAML 的用户，custom_params 约束违反的反馈成本 = 权重加载时长。
- 失效边界/未知：
  - 冷/热加载时长差异巨大（约 5 分钟 vs 20-60 秒），引用具体时长必须注明缓存状态；本组来源观测所有负向用例均在主样例刚加载过权重的热缓存环境测量；
  - `check_model_config_before_loading`（model_worker.py:218-219）目前承载 A4W4 MXFP4 平台约束（modeling_deepseek.py:2325 区域）等加载前校验，custom_params 前移属建议、未实施；
  - check_model_settings 中部分校验依赖模型结构（如 o_proj_tp_size ≤ o_groups、low_latency_tp 平台判断），并非全部都能前移到配置解析阶段——仅纯配置项（布尔组合互斥/依赖）适合前移，此边界为代码结构推断、未逐一实验；
  - 在线（PD）模式的校验时机未在轨迹内观测。
