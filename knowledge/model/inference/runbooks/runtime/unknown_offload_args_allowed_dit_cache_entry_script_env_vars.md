---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman offload_args 被 mm_function.sh YAML 白名单拒绝：经 MAGI_COMPILE_OFFLOAD_CONFIG 环境变量传递（且必须绕开 runtime YAML env_vars 链路）",
  "description": "模型/任务：daVinci-MagiHuman（Magi 视频生成/SR，magi_compiler 编译栈）单卡推理，`bash infer_sr_540p.sh` 类 launcher（source mm_function.sh → mm_launch）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-20T14:17:05Z",
  "platforms": []
}
---

# daVinci-MagiHuman offload_args 被 mm_function.sh YAML 白名单拒绝：经 MAGI_COMPILE_OFFLOAD_CONFIG 环境变量传递（且必须绕开 runtime YAML env_vars 链路）

## 适用场景

- 模型/任务：daVinci-MagiHuman（Magi 视频生成/SR，magi_compiler 编译栈）单卡推理，`bash infer_sr_540p.sh` 类 launcher（source mm_function.sh → mm_launch）。
- 症状 A：启动即 `[ERROR] Unknown top-level YAML key(s): ['offload_args']`。
- 症状 B：offload 配置移入 env_vars 后运行期 `pydantic_settings.exceptions.SettingsError: error parsing value for field "offload_config" from source "EnvSettingsSource"`（内层 json.decoder.JSONDecodeError）。

## 触发与观测

- 症状 A（source 0 seq 6，tool_observed）：模型 sr 系列 YAML 自带顶级 `offload_args:` 块，而 `mm_validate_yaml` 的 ALLOWED_TOP 白名单只有 dit_cache/entry_script/env_vars/launcher/launcher_args/master_port/model_args/model_name/sparse/world_size；launcher 里 `export OFFLOAD_ARGS=...` 框架从不消费（seq 114 grep 证实仅脚本自设）。
- 症状 B（source 0 seq 211，tool_observed）：JSON 串放 YAML env_vars 首次跑通校验与 torchrun 拉起，但在 dit_module 导入期 `@magi_register_custom_op` → `get_compile_config()` → `CompileConfig()` 初始化即崩；runtime YAML（seq 217）中该值被 dump 折成两行单引号 scalar。

## 探针与操作

1. 能力探针（source 0 seq 165/166，tool_observed）：单卡 python 设 `MAGI_COMPILE_OFFLOAD_CONFIG` 为 JSON 串后 `CompileConfig().offload_config` 打印 `model_cpu_offload=True gpu_resident_weight_ratio=0.35 offload_policy=<OffloadPolicy.HEURISTIC: 'HEURISTIC'>`——确认 magi_compiler（pydantic-settings，env_prefix=MAGI_COMPILE_）支持嵌套字段的 JSON 环境变量覆盖。
2. 静态 YAML 解析探针（seq 218/219）：`yaml.safe_load` 静态文件得到的 JSON 串本身合法——损坏发生在 runtime 重生成/导出链路而非源文件。

## 机制与判别

- 传递契约：模型特有 offload 配置不能走 YAML 顶级键（白名单 fail-fast）；正确通道是 `MAGI_COMPILE_OFFLOAD_CONFIG`（CompileConfig 优先级 user config_patch > env > 默认）。
- 陷阱判别：同一 JSON 在静态 YAML 合法、经 runtime dump→reload→export 链路后损坏（折行/引号处理），pydantic EnvSettingsSource 拿到坏串即 SettingsError；确切损坏点（YAML 折叠语义 vs shell export 引号）未逐字定位，记 unknown。
- 闭合修复：JSON 环境变量改在 launcher 脚本内直接 export（紧凑无空格单引号包裹），同时删除死变量 OFFLOAD_ARGS。

## 验证信号

- 探针生效（seq 166）、崩溃错误链逐字（seq 211）、最终修复脚本逐字（seq 231）、复跑 `Launching with torchrun` + MagiPipelineConfig 正常加载（seq 271）——全部 tool_observed。
- 验证边界：观察到初始化段健康（无 JSON/Settings 错误、config 打印完整），端到端视频产物在轨迹结束前未产出。

## 适用与失效边界

- 适用：mm_function.sh 启动协议 + magi_compiler 编译栈的模型集成——一切"模型特有配置键"的传递设计（白名单外键 → 用 MAGI_COMPILE_ 前缀环境变量，且勿经 runtime YAML env_vars 传 JSON）。
- 失效/不覆盖：JSON 损坏的精确字符级机制未定位（避免断言"折行即损坏"的具体路径）；`mm_function.sh` 属 root 文件本轨迹未改白名单（框架侧补 offload_args 支持是另一条未验证路线）；多卡/torchrun>1 rank 场景未测试。

## 附：断言存档

- mm_function.sh mm_validate_yaml 的 ALLOWED_TOP 白名单（dit_cache/entry_script/env_vars/launcher/launcher_args/master_port/model_args/model_name/sparse/world_size）不含模型特有的 offload_args 顶级键——daVinci-MagiHuman sr 系列 YAML 带 offload_args 时启动即报 Unknown top-level YAML key(s)，且脚本内 export 的 OFFLOAD_ARGS 环境变量框架从不消费（死配置）。
- 正确传递路径=magi_compiler CompileConfig（pydantic-settings，env_prefix=MAGI_COMPILE_）：单卡探针验证设 MAGI_COMPILE_OFFLOAD_CONFIG 为 JSON 串后 CompileConfig().offload_config 生效（model_cpu_offload=True gpu_resident_weight_ratio=0.35 offload_policy=HEURISTIC）；但该 JSON 若写进 YAML env_vars，经 runtime YAML 重生成链路（dump 将长 JSON 折两行→reload→export）后损坏，dit_module 导入期 CompileConfig() 初始化抛 pydantic_settings SettingsError（json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)）。
- 闭合修复=从 YAML env_vars 移除该变量、在 launcher 脚本（infer_sr_540p/540p_ti2v/1080p/1080p_ti2v.sh）内直接 export 紧凑无空格 JSON：MAGI_COMPILE_OFFLOAD_CONFIG='{"model_cpu_offload":true,"gpu_resident_weight_ratio":0.35,"offload_policy":"HEURISTIC"}'，同时删除死变量 OFFLOAD_ARGS；复跑通过 YAML 校验、torchrun 启动、MagiPipelineConfig 正常加载（验证至初始化段，轨迹在端到端产物产出前结束）。

```text
[ERROR] Unknown top-level YAML key(s): ['offload_args']. Allowed: ['dit_cache', 'entry_script', 'env_vars', 'launcher', 'launcher_args', 'master_port', 'model_args', 'model_name', 'sparse', 'world_size']
```

```text
model_cpu_offload=True gpu_resident_weight_ratio=0.35 offload_policy=<OffloadPolicy.HEURISTIC: 'HEURISTIC'> bandwidth_safety_factor=0.9
```

```text
export CPU_OFFLOAD="${CPU_OFFLOAD:-true}"
export MAGI_COMPILE_COMPILE_MODE="NONE"
export TORCH_COMPILE_DISABLE="1"
export MAGI_COMPILE_OFFLOAD_CONFIG='{"model_cpu_offload":true,"gpu_resident_weight_ratio":0.35,"offload_policy":"HEURISTIC"}'
```

```text
[INFO] Launching with torchrun (nproc_per_node=1, master_port=29612)
==================================>
```
