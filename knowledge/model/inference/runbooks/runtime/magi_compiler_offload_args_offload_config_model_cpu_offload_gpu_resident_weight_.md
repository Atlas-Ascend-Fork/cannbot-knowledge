---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman sr_1080p OOM 迁移修复未闭合：config_patch 双模型 offload 覆盖与 mm 启动器 PYTHONPATH/dit_cache 陷阱，直接 torchrun 方案三次停在配置打印",
  "description": "模型/框架：daVinci-MagiHuman（15B DiT 音频-视频生成，base + sr 双模型加载）sr_1080p（1920×1088）推理；magi_compiler 编译装饰器 + `config_patch` 钩子 + CPU offload（`gpu_resident_weight_ratio`）。",
  "tags": [
    "task.testing",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# daVinci-MagiHuman sr_1080p OOM 迁移修复未闭合：config_patch 双模型 offload 覆盖与 mm 启动器 PYTHONPATH/dit_cache 陷阱，直接 torchrun 方案三次停在配置打印

## 适用场景

- 模型/框架：daVinci-MagiHuman（15B DiT 音频-视频生成，base + sr 双模型加载）sr_1080p（1920×1088）推理；magi_compiler 编译装饰器 + `config_patch` 钩子 + CPU offload（`gpu_resident_weight_ratio`）。
- 硬件/环境：型号未确认的单卡 Ascend NPU（`ASCEND_RT_VISIBLE_DEVICES=5`，61-64 GB HBM），CANN 8.5.1 conda 环境 `davinci-magihuman`， cann-recipes-infer executor（mm_function.sh 启动器）。
- 本卡是失败迁移会话的负结果 + 源码级双根因判别：修复在本轨迹内未闭合，不应按"已解决"引用。

## 触发与观测

- 前一会话遗留的 OOM（本轨迹读到的修复文档与日志，source 0 seq 46）：`[E617 09:53:32.629080798 OpParamMaker.cpp:454] NPU out of memory.`，发生在 sr model forward 路径。
- 本轨迹自身三次运行修复脚本（10:17/10:20/10:25）均未进入模型加载：日志停在 MagiPipelineConfig 打印（188 行，无 Load model/ERROR 行、无 mp4 产出，source 0 seq 316/354）。
- 对照重跑"成功版本"参考脚本同样未在观察窗口产出 mp4 或成功行（source 0 seq 399/401）——会话末尾的"问题已解决"总结为 Agent 自述，无设备验证。

## 探针与操作

- 双根因之一：config_patch 无条件覆盖 offload（源码级，两侧目录代码完全一致）。原始 `inference/model/dit/dit_module.py:869`（source 0 seq 53，逐字）：

```python
869:         compile_config.offload_config.gpu_resident_weight_ratio = 0.0
870:     return compile_config
```

  修复版 `inference_patched/model/dit/dit_module.py:869-870`（source 0 seq 57，逐字）：

```python
869:         if not compile_config.offload_config.model_cpu_offload:
870:             compile_config.offload_config.gpu_resident_weight_ratio = 0.0
871:     return compile_config
```

- 双根因之二：成功版与失败版 offload 传参方式不同。成功版 `example/sr_1080p/run_T2V.sh` 把参数追加到 torchrun 命令行（source 0 seq 93/296，逐字）：

```text
MAGI_COMPILER_OFFLOAD_ARGS="--offload_config.model_cpu_offload --offload_config.gpu_resident_weight_ratio 0.35 --offload_config.offload_policy HEURISTIC"
  --output_path "output_example_sr_1080p_t2v_$(date '+%Y%m%d_%H%M%S')" $MAGI_COMPILER_OFFLOAD_ARGS \
```

  失败版 `infer_sr_1080p.sh` 只设环境变量（source 0 seq 95，逐字）：

```text
export MAGI_COMPILE_OFFLOAD_CONFIG='{"model_cpu_offload":true,"gpu_resident_weight_ratio":0.35,"offload_policy":"HEURISTIC"}'
```

  成功版 2026-06-16 历史日志显示双模型加载成功（source 0 seq 186，逐字）：

```text
[2026-06-16 20:03:15,275 - INFO] [Rank 0] (tp, cp, pp) rank (0, 0, 0):  Model size: 28.54 GB, parameter count: 15299419136
[2026-06-16 20:03:35,896 - INFO] [Rank 0] Load model successfully GPU 0 memory allocated: 28.54 GB, max_allocated: 28.54 GB, reserved: 28.56 GB, max_reserved: 28.56 GB
```

- 本轨迹修复尝试：去掉 YAML 中的 `dit_cache:` 空键（mm 启动器会据此注入 entry.py `parse_known_args` 静默忽略的 `--cache_config` 参数），新建 `infer_sr_1080p_direct.sh`（直接 torchrun + `inference_patched/pipeline/entry.py` + CLI offload 参数），运行三次均停在 188 行配置打印（source 0 seq 316）。

## 机制与判别

- OOM 根因（源码级）：`config_patch` 以模块级 `is_base_model` 标志区分两次模型构建，对第二个（sr）模型无条件将 `gpu_resident_weight_ratio` 置 0.0，覆盖用户的 CPU offload 配置，使全部权重上卡，61 GB 单卡在 1080p sr 阶段 OOM；带 `if not model_cpu_offload` 守卫的 patched 版本语义正确。
- 成功版本并非代码不同（两侧 dit_module.py 完全一致），而是靠 torchrun 命令行追加 `--offload_config.*` 参数的传参路径；仅设 `MAGI_COMPILE_OFFLOAD_CONFIG` 环境变量的路径没有生效证据。
- 迁移尝试未闭合的判别：直接 torchrun（绕过 mm_function/dit_cache/--cache_config）后仍停在配置打印且无错误行，说明失败条件未被任一已识别根因完全解释——仍存在未定位的配置加载/退出问题；本轨迹未进一步定位。
- 关联：mm 启动器 PYTHONPATH 前置 `RECIPES_ROOT` 使 `inference_patched` 失效的完整证据链在（会话标识已删除）中闭合，本卡不重复展开。

## 验证信号

- tool_observed（source 0 seq 53/57/97）：原始与 patched 两侧 dit_module.py:869 源码及 diff 逐字核对。
- tool_observed（source 0 seq 93/95/296）：成功版与失败版 offload 传参方式 grep 逐字输出。
- tool_observed（source 0 seq 186）：成功版 2026-06-16 历史日志（28.54 GB 双模型加载成功）——历史日志文件读取，非本轨迹实跑。
- tool_observed（source 0 seq 316/354/399/401）：本轨迹三次修复运行日志均 188 行、无 mp4；参照成功版重跑亦无 mp4/成功行。
- agent_narrative（source 0 seq 412）："问题已解决"总结与根因归因——未被上述客观信号支持，按未闭合处理。
- user_reported（source 0 seq 1）：sr_1080p OOM 任务描述。

## 适用与失效边界

- 适用：daVinci-MagiHuman 双模型（base+sr）加载在 61-64 GB 单卡的 OOM 排查——先核对 config_patch 守卫与 offload 传参路径（CLI vs 环境变量），再怀疑显存本身。
- 失效边界/不可采用：`infer_sr_1080p_direct.sh` 直接 torchrun 方案在本轨迹未跑通（三次停在配置打印），不能当作已验证修复；"问题已解决"结论不可引用。MM 启动器路径下仅靠 PYTHONPATH 前置 inference_patched 不可靠（见 w19-s2-c3）。
- 停止条件：运行停在 MagiPipelineConfig 打印且无错误行时，应先取完整 stdout/stderr 与退出码定位静默退出点，而不是继续换脚本重试。

## 附：断言存档

- daVinci-MagiHuman sr_1080p OOM 的源码级根因是 config_patch 以 is_base_model 区分双模型构建、对第二个（sr）模型无条件置 gpu_resident_weight_ratio=0.0 覆盖 CPU offload 配置使全量权重上卡；两侧目录 dit_module.py:869 代码完全一致，守卫版（if not model_cpu_offload）为正确语义，成功版并非代码不同而是靠 torchrun 命令行追加 --offload_config.model_cpu_offload --offload_config.gpu_resident_weight_ratio 0.35 --offload_policy HEURISTIC（2026-06-16 历史日志显示 28.54 GB 双模型加载成功），失败版仅设 MAGI_COMPILE_OFFLOAD_CONFIG 环境变量、无生效证据。
- 参照成功版迁移的直接 torchrun 修复（去掉 YAML dit_cache 空键以避免 mm 启动器注入 entry.py parse_known_args 静默忽略的 --cache_config、改用 inference_patched/pipeline/entry.py、CLI offload 参数）在本轨迹未闭合：10:17/10:20/10:25 三次运行日志均停在 MagiPipelineConfig 打印（188 行、无模型加载行、无 mp4），连参照的成功版脚本当日重跑也未在观察窗口产出 mp4 或成功行；会话末尾『问题已解决』为 Agent 自述，无设备验证，不可按已修复引用。

```text
188 ./log_example_sr_1080p_t2v_20260617_102009.log
```
