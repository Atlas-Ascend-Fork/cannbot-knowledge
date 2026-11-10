---
{
  "type": "Runbook",
  "title": "DeepSeek-V4.1 私有环 SWA 前缀命中时 bounded-replay 热身行窗口截断导致环形 KV 系统性偏差",
  "description": "vllm-ascend releases/v0.27.1rc 的 DeepSeek-V4.1 适配中，私有环 SWA 平面不做前缀缓存；前缀命中后调度侧回退一个窗口重放 [H−W, H)，但 dsa_v41.py:243 对 bounded replay 行置 history_len=0，重放段除最后一行外真实 SWA 窗口被截断，写入 ring 的 KV 系统性偏差并被后续约 W 个 decode 步读取。触发条件是 P 节点/standalone/抢占恢复的任何本地前缀命中，与是否命中缓存相关，表现为间歇性精度波动；PD 的 D 节点导入路径不受影响。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "agnostic"
  ]
}
---

# DeepSeek-V4.1 私有环 SWA 前缀命中时 bounded-replay 热身行窗口截断导致环形 KV 系统性偏差

## 适用场景

- 模型/框架：DeepSeek V4.1（DSA 注意力 + 私有环 SWA KV），vllm-ascend 硬件插件，分支 releases/v0.27.1rc，审查区间 `git log 09220f435~1..HEAD`（HEAD=6746201ec）。
- 平台：Ascend NPU；生产配置为 PD 分离（MooncakeHybridConnector）、enable_fused_mc2=1、expert parallel、dspark 投机解码、fp8。
- 工作负载：用户报告"精度波动"（间歇性）与"长稳测试随时间退化"。
- 缺失信息：生产是否开启 prefix caching 的比例、窗口 W 与块大小在生产中的具体取值（审查推断 W=128、B∈{32,64,128}）未在轨迹内给出运行时日志。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发 = 生产症状"精度波动"（用户叙述，事件 2）+ 代码路径"任何本地前缀命中后的 bounded replay"。审查（只读，未修改文件）观测到的客观代码事实（事件 352，grep 输出，仓库 ${LOCAL_PATH_1}）：

```
243:        history_len = 0 if row in bounded_replay_rows else min(window_size - 1, confirmed)
428:            max_recv_token_num = get_ascend_config().mega_moe_max_tokens
112:        renorm=0,
347:                renorm=0,
1739:                        self._private_circle_receiving_requests[
163:    def refresh_moe_hccl_groups() -> None:
164:        from vllm_ascend.ops.fused_moe.moe_comm_method import _MoECommMethods
166:        for comm_method in _MoECommMethods.values():
185:            self.refresh_moe_hccl_groups()
```

调度侧把命中 H 回退一个窗口（事件 45，private_circle_pool.py 全文读取）：

```
37: def compute_prefix_bounded_replay_start(
38:     hit_length: int,
39:     bounded_replay_tokens: int,
40:     alignment: int = 1,
41: ) -> int:
42:     """Return the scheduler-visible recompute start after bounded replay.
43:
44:     The hit length is rolled back by one warm-up window and floored to
45:     ``alignment`` (the scheduler block alignment) so the reported hit stays
46:     block-aligned for allocation.
47:     """
48:     if hit_length < 0 or bounded_replay_tokens < 0:
49:         raise ValueError("hit_length and bounded_replay_tokens must be non-negative")
50:     if alignment < 1:
51:         raise ValueError("alignment must be positive")
52:     start = max(0, hit_length - bounded_replay_tokens)
53:     return start // alignment * alignment
```

## 探针与操作

核查命令（审查会话实际执行，事件 350，workdir=${LOCAL_PATH_1}）：

```
grep -n "history_len = 0 if row in bounded_replay_rows" vllm_ascend/attention/dsa_v41.py; grep -n "max_recv_token_num = get_ascend_config().mega_moe_max_tokens" vllm_ascend/ops/fused_moe/moe_comm_method.py; grep -n "renorm=0" vllm_ascend/ops/fused_moe/router/fused_topk_router.py; grep -n "_private_circle_receiving_requests\[" vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_hybrid_connector.py; grep -n "refresh_moe_hccl_groups\|_MoECommMethods" vllm_ascend/device_allocator/sleep_mem_optimized.py
```

读取调度回退函数（事件 45 对应读取）：`vllm_ascend/core/private_circle_pool.py` 中 `compute_prefix_bounded_replay_start`（第 37-53 行）。配合 dsa_v41.py 第 1190-1196 行的窗口 clamp（事件 367 报告内引文）：

```
  # dsa_v41.py:243  bounded replay 行不恢复任何历史
  history_len = 0 if row in bounded_replay_rows else min(window_size - 1, confirmed)
  # dsa_v41.py:1190-1196  workspace 内窗口被 clamp 到本地坐标
  valid_len = torch.clamp(positions + 1, max=window_size)
  window_start = positions - valid_len + 1
```

注意：这是只读审查发现，轨迹内没有实施修复；修复建议（回退两个窗口 2W 或恢复 ring 中可复用窗口数据）未被验证，不能当作已验证修法采用。

## 机制与判别

结论 1：私有环 SWA 平面前缀命中后重放区间 [H−W, H) 的热身行 history_len=0，绝对位置 p 的真实窗口 [p−W+1, p] 中低于 H−W 的部分不在 workspace 中被截断，仅最后一行 (H−1) 窗口完整。
- 证据：dsa_v41.py:243（事件 352 逐字）+ compute_prefix_bounded_replay_start（事件 45 逐字）+ 报告引文（事件 367）。
- 机制：私有环 SWA 平面不做前缀缓存（新请求分配新的 ring）；重放 [H−W, H) 时 `history_len=0`，FA 只能看到重放段自身，workspace 内窗口被 clamp 到本地坐标。

结论 2：重放段第 1 层之后各层的 KV 写入 ring 并被后续约 W 个 decode 步读取，构成与是否命中缓存相关的间歇性精度劣化来源；触发条件是 P 节点/standalone/抢占恢复的任何本地前缀命中，PD 的 D 节点导入路径不受影响（P 侧传完整窗口）。
- 可区分解释分支：
  - 若精度劣化与"是否命中前缀缓存"相关、随负载波动（间歇性）→ 指向本机制（P1-1）。
  - 若劣化随运行时间单调加剧（长稳形态）→ 更指向 sleep/wake 后 HCCL 组失效或 Mooncake 接收字典泄漏等慢性机制（同一报告的 P1-6/P1-7/P2-8 排序更高）。
  - D 节点导入路径不受影响可作为判别实验：只在 P 节点/standalone 复现的劣化支持本机制。
- 未验证推断：影响幅度与"后续约 W 个 decode 步读取偏差 KV"的量化关系是代码级推理，轨迹内未运行数值验证。

## 验证信号

- 信号等级：代码事实（grep/read 工具结果），非运行验证。
- 本轨迹内观测到的客观信号：事件 352（grep 输出确认 dsa_v41.py:243 当前 HEAD 逐字内容）、事件 45（compute_prefix_bounded_replay_start 完整函数原文，含 "The hit length is rolled back by one warm-up window" 的自述）。
- 平台：Ascend NPU（vllm-ascend releases/v0.27.1rc，DeepSeek-V4.1 适配提交区间 09220f435~1..HEAD）。
- 无性能/精度数值结论（本轨迹为只读审查，未运行基准）。

## 适用与失效边界

- 适用：DeepSeek-V4.1 私有环池（private circle pool）开启 + 本地前缀命中/抢占恢复场景；P 节点与 standalone。
- 不适用/不受影响：PD 部署中 D 节点的 KV 导入路径（P 侧传完整窗口）。
- 版本边界：结论针对 releases/v0.27.1rc 的 09220f435~1..HEAD 区间；e4e6b0e97 声称修复的精度问题已被 7f8cab566 重构（device 侧 ring 表重建）替代，但该重构不改变本条的窗口截断几何。
- 停止/回退条件：若分层消融显示劣化与缓存命中率无关，或 D 节点也能复现，应转向长稳类根因（HCCL 生命周期、内存泄漏）。
- 修复方向（未验证）：前缀命中回退两个窗口（2W）或恢复 ring 中上一个请求可复用的窗口数据，保证重放行窗口完整。
