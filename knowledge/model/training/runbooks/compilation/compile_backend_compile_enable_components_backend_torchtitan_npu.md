---
{
  "type": "Runbook",
  "title": "torchtitan-npu run_train.sh 中 COMPILE_BACKEND 环境变量隐式开启模型编译，导致 Engram EP 查表初始化被拒",
  "description": "框架：torchtitan-npu（私仓 torchtitan-npu-engram，DeepSeek-V4 Engram 训练），启动脚本 `scripts/run_train.sh`。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# torchtitan-npu run_train.sh 中 COMPILE_BACKEND 环境变量隐式开启模型编译，导致 Engram EP 查表初始化被拒

## 适用场景

- 平台范围依据：source 0 seq 249、source 1 seq 846的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 框架：torchtitan-npu（私仓 torchtitan-npu-engram，DeepSeek-V4 Engram 训练），启动脚本 `scripts/run_train.sh`。
- 平台：8 卡 Ascend 950PR，CANN 9.2.0 weekly（20260828），torch 2.14.0.dev20260719+cpu / torch_npu 2.14.0.dev20260808。
- 目标：Host Engram + Muon + EP4/FSDP4 4 卡训练验证。

## 触发与观测

4 卡 128 token / 1 step 启动在模型初始化阶段被拒绝。Agent 定位：环境变量 `COMPILE_BACKEND=aot_eager` 遗留在 shell 中，使脚本自动附加编译参数，而当前 Torch Engram EP 查表明确禁止被编译（source 0 seq 73、94）。

## 探针与操作

机制单元（`scripts/run_train.sh`，source 0 seq 76 逐字）：

```bash
if [ -n "${COMPILE_BACKEND:-}" ]; then
    ARGS+=(
        --compile.enable
        --compile.components model
        --compile.backend "${COMPILE_BACKEND}"
    )
fi
ARGS+=("$@")
```

修复（before → after）：

- before：shell 残留 `COMPILE_BACKEND=aot_eager` → 启动即被拒。
- after：清空该变量后重跑同一 4 卡 128/1-step；并将"启动前核对 CANN、`ASCEND_RT_VISIBLE_DEVICES`、`ASCEND_CUSTOM_OPP_PATH`、`NGPU`、compile 开关、override 列表"固化为流程（source 0 seq 94）。

相关变体（user_reported，source 1 seq 2587）：上游旗舰配置 `1024k_a5.sh` 通过 exec 链继承了 `4k_a3.sh:18` 的 `COMPILE_BACKEND=aot_eager`，使"CP + 编译"组合被误判为上游能力问题；同源教训是显式清空/审计该变量的继承链。

## 机制与判别

- 机制：脚本把"环境变量非空"直接翻译成 `--compile.enable --compile.components model`，用户未显式传编译参数时编译仍被打开；Engram host-offload 查表路径不支持被编译，故初始化即失败。
- 判别：失败发生在模型初始化而非训练 step，且清理变量后同一命令可进入训练（排除设备与算子包问题）。
- 未验证推断：aot_eager 下 Engram 表拿不到梯度的另一路 user_reported 实验（source 1 seq 2807）与本案同根于"编译被隐式打开"，但梯度缺失机制本轨迹未闭合。

## 验证信号

- tool_observed（source 0 seq 76）：run_train.sh 的 COMPILE_BACKEND 分支全文。
- agent_narrative（source 0 seq 73、94）：失败归因与修复动作。
- tool_observed（source 0 seq 467/468，修复后的同环境 4 卡运行日志）：`step: 1 loss: 12.52049 grad_norm: 45.6721 ... Training completed`。
- user_reported（source 1 seq 2587）：上游 exec 链继承 COMPILE_BACKEND 导致 CP+编译误判。

## 适用与失效边界

- 适用于所有通过环境变量驱动编译开关的 torchtitan-npu 启动链；排查任何"初始化即被拒/行为与预期不符"的 Engram 类不可编译组件前，先 `env | grep COMPILE`。
- 失效边界：若失败点在训练 step 或反向（而非初始化），本规则不适用；编译未被打开时清空变量无效果。
- 上游脚本通过 `source`/`exec` 继承变量时，需在最外层 wrapper 显式 `unset`，单点清空不彻底。

## 附：断言存档

- torchtitan-npu scripts/run_train.sh 在 COMPILE_BACKEND 非空时自动附加 --compile.enable --compile.components model --compile.backend，环境变量遗留会隐式打开模型编译
