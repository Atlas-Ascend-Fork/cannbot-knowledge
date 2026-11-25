---
{
  "type": "Runbook",
  "title": "HunyuanVideo eval_l0_perf.py 传 --cache-config 报 unrecognized arguments：hv_parse_args 走 sys.argv 重定向，需在 argparser 与注入列表两头补参",
  "description": "HunyuanVideo（hyvideo 管线）自写 L0 计时脚本 eval_l0_perf.py 需要启用 DiT cache（TeaCache/FBCache/TaylorSeer）配置 JSON 时。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-20T14:17:04Z",
  "platforms": []
}
---

# HunyuanVideo eval_l0_perf.py 传 --cache-config 报 unrecognized arguments：hv_parse_args 走 sys.argv 重定向，需在 argparser 与注入列表两头补参

## 适用场景

HunyuanVideo（hyvideo 管线）自写 L0 计时脚本 eval_l0_perf.py 需要启用 DiT cache（TeaCache/FBCache/TaylorSeer）配置 JSON 时。该脚本的模型参数不是自己解析的——hyvideo 的 `hv_parse_args()` 从 `sys.argv` 读取，脚本通过重定向 `sys.argv` 把参数传进去（cache_manager.from_config(hv_args.cache_config, ...) 消费）。

## 触发与观测

autotune 命令模板把 `{config_file}` 替换为 `--cache-config autotune_test/trial_configs/trial_001_config.json` 直接追加到 eval_l0_perf.py 命令行（source 0 seq 28），首跑失败（source 0 seq 29，逐字）：

```
eval_l0_perf.py: error: unrecognized arguments: --cache-config autotune_test/trial_configs/trial_001_config.json
```

Exit code 2（argparse 拒绝）。模型与 NPU 环境本身加载正常（torch_npu transfer 补丁日志已出现，失败点纯在参数解析）。

## 探针与操作

`head -80`/`grep -n "cache"` 定位（source 0 seq 32-34）：脚本 `from module.dit_cache.cache_method import cache_manager`，init 处 `cache_manager.from_config(hv_args.cache_config, cache_params=cache_params)`——cache_config 是 hv_args 的字段而非本脚本参数；脚本 argparser（seq 39）只有 --prompt/--seed/--video-size/--video-length/--infer-steps/--device/--model-base/--embedded-cfg-scale/--flow-shift。

## 机制与判别

根因：两套解析器——脚本自己的 argparse 与 hyvideo 的 hv_parse_args()；命令行参数先被脚本 argparse 消费，未声明的 --cache-config 直接报错；hv_args 需要的字段必须出现在重定向后的 sys.argv 里。修复 = 两头补参（source 0 seq 41 编辑 diff 逐字）：

```python
    parser.add_argument("--embedded-cfg-scale", type=float, default=6.0)
    parser.add_argument("--flow-shift", type=float, default=7.0)
    parser.add_argument("--cache-config", type=str, default=None,
                        help="Path to cache config JSON (passed to hyvideo parse_args)")
    eval_args = parser.parse_args()

    # --- Redirect sys.argv so hyvideo parse_args picks up our params ---
    tmp_save_path = "./results/tmp_eval_l0"
    sys.argv = [
        "eval_l0_perf.py",
        "--prompt", eval_args.prompt,
        "--seed", str(eval_args.seed),
        "--seed-type", "fixed",
        "--video-size", str(eval_args.video_size[0]), str(eval_args.video_size[1]),
        "--video-length", str(eval_args.video_length),
        "--infer-steps", str(eval_args.infer_steps),
        "--device", str(eval_args.device),
        "--model-base", eval_args.model_base,
        "--embedded-cfg-scale", str(eval_args.embedded_cfg_scale),
        "--flow-shift", str(eval_args.flow_shift),
        "--flow-reverse",
        "--use-cpu-offload",
        "--save-path", tmp_save_path,
        "--sparse-method", "no_sparse",
    ]
    if eval_args.cache_config is not None:
        sys.argv += ["--cache-config", eval_args.cache_config]
```

判别：默认 None + 条件追加，不带 cache 配置的原有 L0 用法不受影响；只加 argparse 不加 sys.argv 注入（或反之）都不能闭环——前者 hv_args.cache_config 仍为空，后者依旧 exit 2。

## 验证信号

- tool_observed（失败）：source 0 seq 29（exit 2 + unrecognized arguments 原文）。
- tool_observed（修复生效）：seq 45 重跑 L0 完整跑通（加载 text encoder/DiT、推理出片日志）；seq 48 sanity check `[PASS]`；seq 50 aggregate_l0 输出 `feasible=True speedup=1.9057 sanity_passed=True`——cache 确实生效（加速 1.9 倍且 per_step 出现 ~7ms 跳步），不是仅仅不再报错。
- trial_002（另一会话）同命令直接成功，佐观修复 persist 在脚本里。

## 适用与失效边界

- 已证边界：hyvideo 管线「宿主脚本 + hv_parse_args(sys.argv 重定向)」双解析器结构下，新增透传参数必须 argparser 声明与 sys.argv 注入两处同步。
- 失效边界：hyvideo 侧 hv_parse_args 未声明 --cache-config 时本修不适用（本轨迹中 hv_parse_args 已支持，仅宿主脚本缺）；该脚本属 autotune 评测工具链，非模型本体。

## 附：断言存档

- HunyuanVideo 评测脚本 eval_l0_perf.py 的 cache 配置经 hv_parse_args 从 sys.argv 解析：直接向脚本传 --cache-config 报 exit 2 'unrecognized arguments'；修复 = 自身 argparser 增加 --cache-config 并在重定向 sys.argv 时条件追加该参数，重跑 L0 成功出片、sanity PASS、聚合出 speedup
