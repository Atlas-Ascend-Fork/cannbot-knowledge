---
{
  "type": "Runbook",
  "title": "融合主开关 use_fused_ops=0 被逐点 fuse_* 配置覆盖失效：改为硬主闸 AND 语义的修复",
  "description": "Runner 初版把 use_fused_ops 仅作为逐点开关的默认值（custom.get(f\"fuse_{name}\", use_fused_ops)），YAML 显式 fuse_*: true 时 HYV4_USE_FUSED_OPS=0 无法全关、A/B 回退失真；改为 fusion_flags[name] = master and enabled 的硬主闸 AND 语义后，主闸关闭即全关并逐位复现阶段 2 paged 基线 token，算子计数插桩证实 all_off 时融合算子调用计数全为 0。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# 融合主开关 use_fused_ops=0 被逐点 fuse_* 配置覆盖失效：改为硬主闸 AND 语义的修复

## 适用场景

- 模型/框架：HYV4 独立部署 Runner（`runner_hy_v4.py`）的阶段 3 融合开关体系；也适用于任何「yaml 主开关 + 逐点开关 + env 覆盖」三层配置的推理 A/B 场景。
- 平台/版本：Ascend950PR_9589 单卡、CANN 9.1.0、torch_npu 2.12.0；开关面：`use_fused_ops` / `fuse_moe_experts|moe_router|rms_norm|mlp_swiglu|rope` / `HYV4_USE_FUSED_OPS` / `HYV4_FUSE_<NAME>`。
- 目标：A/B 与回退方法论——主开关必须能「一键全关」干净回退基线，逐点开关独立可观测，否则回退验证与性能 A/B 结论全部失真。

## 触发与观测

实施后首次回退验证（来源记录 事件 180 命令 `HYV4_USE_FUSED_OPS=0 bash infer.sh`）产出（事件 181，原文）：

```
2026-10-13 17:05:23,179 INFO building model (layers=4, seed=1234, paged_fa=True, fusion={'moe_experts': True, 'moe_router': True, 'rms_norm': True, 'mlp_swiglu': True, 'rope': True}) ...
```

env 主开关已设 0，构建日志仍显示五点全 True——`HYV4_USE_FUSED_OPS=0` 未生效，回退路径不可用（若据此做「融合前」计时或精度对照，会得到假 A/B）。

## 探针与操作

失败前的语义（来源记录 事件 124，初版 edit 原文；`use_fused_ops` 仅作逐点默认值）：

```
        # Stage-3 fusion switches. ``use_fused_ops`` is the master default for
        # every fusion point; each point can still be overridden individually via
        # ``custom_params.fuse_<name>`` or ``HYV4_FUSE_<NAME>`` for precision A/B.
        self.use_fused_ops = bool(custom.get("use_fused_ops", True))
        env_fused = os.environ.get("HYV4_USE_FUSED_OPS")
        if env_fused is not None:
            self.use_fused_ops = env_fused.lower() not in ("0", "false", "no", "off")
        fusion_flags = {}
        for name in ("moe_experts", "moe_router", "rms_norm", "mlp_swiglu", "rope"):
            enabled = bool(custom.get(f"fuse_{name}", self.use_fused_ops))
```

缺陷：yaml 中显式 `fuse_*: true`（事件 130 写入）永远压过主开关默认值，env 只改默认值不改显式配置。

修复后语义（来源记录 事件 184 修改、最终状态见 来源记录 事件 71 原文）：

```
63:         # Stage-3 fusion switches. ``use_fused_ops`` is a hard master gate: when
64:         # false every point is off. When true each point defaults on and can be
65:         # disabled individually via ``custom_params.fuse_<name>`` /
66:         # ``HYV4_FUSE_<NAME>=0`` for precision & performance A/B.
67:         master = bool(custom.get("use_fused_ops", True))
68:         env_fused = os.environ.get("HYV4_USE_FUSED_OPS")
69:         if env_fused is not None:
70:             master = env_fused.lower() not in ("0", "false", "no", "off")
71:         fusion_flags = {}
72:         for name in ("moe_experts", "moe_router", "rms_norm", "mlp_swiglu", "rope"):
73:             enabled = bool(custom.get(f"fuse_{name}", True))
74:             env_point = os.environ.get(f"HYV4_FUSE_{name.upper()}")
75:             if env_point is not None:
76:                 enabled = env_point.lower() not in ("0", "false", "no", "off")
77:             fusion_flags[name] = master and enabled
78:         set_fusion_flags(**fusion_flags)
79:         self.fusion_flags = get_fusion_flags()
```

## 机制与判别

- 结论一（失效机理）：初版语义下 HYV4_USE_FUSED_OPS=0 bash infer.sh 仍构建 fusion={'moe_experts': True, 'moe_router': True, 'rms_norm': True, 'mlp_swiglu': True, 'rope': True}——use_fused_ops 只作逐点默认值，被 yaml 显式 fuse_*: true 覆盖，主开关回退失效。锚点：来源记录 事件 124（初版语义）；信号：事件 181（构建日志 fusion 全 True）。
- 结论二（修复有效）：改为硬主闸 AND 逐点语义（fusion_flags[name] = master and enabled）后，HYV4_USE_FUSED_OPS=0 全关并逐位复现阶段 2 paged 基线 token；算子计数插桩证实 all_off 时 8 个融合算子调用计数全为 0。锚点：来源记录 事件 184（修复 edit）、来源记录 事件 71（最终代码）；信号：来源记录 事件 189（全关后 token 逐位复现 [101453, 76480, 13901, 65000, 40554, 58506, 105246, 58506]）、事件 277（逐点 env 覆盖生效：`HYV4_FUSE_MLP_SWIGLU=0 HYV4_FUSE_MOE_ROUTER=0` 后构建日志对应 False）、来源记录 事件 184（all_off 计数全 0）、事件 188（infer.sh 默认 vs master-off 两条 env 路径 token 均复现）。
- 可区分解释：开关是否「真实生效」不能只看构建日志（它只反映 flag 字典），reviewer 用算子计数插桩（对 8 个 torch_npu 融合算子包一层计数 wrapper）证明 flag→算子调用的真实路由：all_off 时 8 个算子计数全 0，单开 moe_experts 时 init_routing_v2=3/grouped_matmul=6/clipped_swiglu=3/finalize=3 且其余为 0，互斥成立（来源记录 事件 184）。
- 未验证推断：无。

## 验证信号

本组来源观测轨迹内客观观测（Ascend950PR_9589 单卡、seed=1234）：

- 失效证据：来源记录 事件 181——`HYV4_USE_FUSED_OPS=0 bash infer.sh` 构建日志 `fusion={'moe_experts': True, ...}`（全 True）。
- 修复验证：来源记录 事件 189——`HYV4_USE_FUSED_OPS=0` 构建日志 `fusion={'moe_experts': False, ...}`（全 False），输出 token `[101453, 76480, 13901, 65000, 40554, 58506, 105246, 58506]` 与阶段 2 paged 基线逐位一致（prefill 220.33 ms / decode ~53 ms，回到未融合量级）。
- 逐点覆盖：来源记录 事件 277——`HYV4_FUSE_MLP_SWIGLU=0 HYV4_FUSE_MOE_ROUTER=0 bash infer.sh` 构建日志 `fusion={'moe_experts': True, 'moe_router': False, 'rms_norm': True, 'mlp_swiglu': False, 'rope': True}`，token 不变。
- 算子级验证：来源记录 事件 184——op-count 插桩：all_off 8 算子全 0；moe_experts→{init_routing_v2: 3, grouped_matmul: 6, clipped_swiglu: 3, finalize: 3}；moe_router→{gating_top_k: 3}；rms_norm→{rms_norm: 17}；mlp_swiglu→{swiglu: 4}；rope→{rotary_mul: 12}；all_on 为各单点之和。
- 端到端：来源记录 事件 188——RUN A 默认（全开）token `[101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480]`、RUN B（`HYV4_USE_FUSED_OPS=0`）token `[101453, 76480, 13901, 65000, 40554, 58506, 105246, 58506]`，两条 env 路径均按预期复现对应基线。

## 适用与失效边界

- 通用边界：只要配置层存在「显式逐点配置」，把主开关实现成逐点默认值就会失效；主开关必须是 AND（硬闸）而非 OR（默认值）。
- env 优先级：本实现 env `HYV4_FUSE_<NAME>` > yaml `fuse_<name>` > 默认 True；`HYV4_USE_FUSED_OPS` > yaml `use_fused_ops`；主闸 AND 逐点。若需求是「env 逐点不得越过主闸开启」，本语义已满足；若需求是「yaml 显式 true 必须无视 env 关闭」，则为本语义的反例，不适用。
- 开关生效性验证必须包含算子级证据（计数插桩/trace），仅日志 flag 或退出码 0 不足以证明路由（退出码 0 不自动代表行为正确）。
- 该修复只影响 Runner 配置解析，不改模型数值路径；修复后「关闭全部融合」与「阶段 2 基线」逐位一致是回退可用的判据，换模型/开关面需重建对应基线 token。
