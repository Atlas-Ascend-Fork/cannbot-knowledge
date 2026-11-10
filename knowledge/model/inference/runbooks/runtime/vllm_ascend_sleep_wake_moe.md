---
{
  "type": "Runbook",
  "title": "vllm-ascend sleep/wake 后 MoE HCCL 组引用失效（draft MC2 dispatcher 不刷新 + MegaMoE 对称缓冲区持旧句柄）",
  "description": "vllm-ascend DeepSeek-V4.1 PD 生产中，HcclSleepWakeupManager.wakeup() 重建全部 HCCL PG 后仅 refresh_moe_hccl_groups 遍历扁平 _MoECommMethods 表；dspark draft 拓扑实例只存在于 _MoECommMethodsByTopology 分桶，唤醒后 draft 的 TokenDispatcherWithMC2 仍指向已销毁的 HCCL 通信名（野句柄 → 挂死或数据错乱）。A5 MegaMoE 对称缓冲区缓存于 mega_moe_group 属性进程级复用，restore_hccl 原地重建 device_group 后缓存 buffer 内部仍持旧通信句柄且无重建逻辑。触发条件为 Level-2 sleep/wake + dspark draft 拓扑异于 target 或 FUSED_MC2，是\"长稳测试随时间劣化\"的候选根因。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "agnostic"
  ]
}
---

# vllm-ascend sleep/wake 后 MoE HCCL 组引用失效（draft MC2 dispatcher 不刷新 + MegaMoE 对称缓冲区持旧句柄）

## 适用场景

- 模型/框架：DeepSeek V4.1 适配（MoE 通信 + dspark 投机解码 + MegaMoE），vllm-ascend 硬件插件，分支 releases/v0.27.1rc，审查区间 `git log 09220f435~1..HEAD`。
- 平台：Ascend NPU；生产为 PD 分离（MooncakeHybridConnector）、enable_fused_mc2=1、expert parallel、dspark、fp8。
- 工作负载：用户报告"长稳测试随时间退化"（Long-duration stability tests show degradation over time）。
- 缺失信息：生产长稳流程是否包含 Level-2 sleep/wake 周期未确认（这是本条触发的前提假设）；HCCL 野句柄的具体故障形态（挂死 vs 数据错乱）未实测。

## 触发与观测

触发 = Level-2 sleep/wake（HcclSleepWakeupManager.sleep 销毁全部 HCCL PG，wakeup 重建）+ dspark draft 拓扑异于 target（如 (128,3,ep)）或 FUSED_MC2 的 MegaMoE 组。

审查观测到的客观代码事实：

1. sleep/wake 生命周期（事件 132，sleep_mem_optimized.py 120-186 行读取，逐字）：

```
162:     @staticmethod
163:     def refresh_moe_hccl_groups() -> None:
164:         from vllm_ascend.ops.fused_moe.moe_comm_method import _MoECommMethods
165:
166:         for comm_method in _MoECommMethods.values():
167:             dispatcher = getattr(comm_method, "token_dispatcher", None)
168:             refresh_fn = getattr(dispatcher, "refresh_hccl_group", None)
169:             if callable(refresh_fn):
170:                 refresh_fn()
171:
172:     def sleep(self) -> None:
173:         if torch.distributed.is_available() and torch.distributed.is_initialized():
174:             for handle in getattr(self.worker, "_pp_send_work", []):
175:                 handle.wait()
176:             self.worker._pp_send_work = []
177:             torch.npu.synchronize()
178:             num_destroyed = self.destroy_hccl()
179:             if num_destroyed > 0:
180:                 logger.info("Destroyed %d HCCL process groups for sleep mode.", num_destroyed)
181:
182:     def wakeup(self) -> None:
183:         with set_current_vllm_config(self.vllm_config):
184:             num_restored = self.restore_hccl()
185:             self.refresh_moe_hccl_groups()
186:         logger.info("Restored %d HCCL process groups after sleep mode.", num_restored)
```

2. 拓扑分桶注册表（事件 28，moe_comm_method.py 读取头部，逐字）：

```
58: # instances via get_moe_comm_method(..., topology_key=...), otherwise it
59: # would run with comm methods sized for the other topology.
60: _MoECommMethodsByTopology: dict[tuple[int, int, int], dict[MoECommType, MoECommMethod]] = {}
61:
62:
63: def make_moe_topology_key(num_experts: int, experts_per_token: int, ep_size: int) -> tuple[int, int, int]:
64:     return (int(num_experts), int(experts_per_token), int(ep_size))
65:
66:
67: def _moe_topology_key(moe_config) -> tuple[int, int, int]:
68:     return make_moe_topology_key(moe_config.num_experts, moe_config.experts_per_token, moe_config.ep_size)
69:
70:
71: def get_moe_comm_method(
72:     moe_comm_type: MoECommType | None,
73:     topology_key: tuple[int, int, int] | None = None,
74: ) -> MoECommMethod | None:
75:     if topology_key is None:
76:         return _MoECommMethods.get(moe_comm_type)
```

baebb4dda（"dspark change to mc2 with new hccl group"）引入的 draft 拓扑实例只存在于 `_MoECommMethodsByTopology[(128,3,ep)][MC2]` 分桶，扁平表 `_MoECommMethods` 保留的是首个注册（target）的实例。

3. MegaMoE 对称缓冲区进程级缓存（事件 17，mega_moe.py 读取，_get_sym_buffer 逐字）：

```
307:     def _get_sym_buffer(self, fused_experts_input: MoEFusedExpertsInput, intermediate_hidden: int):
308:         vllm_config = get_current_vllm_config()
309:         if vllm_config is None:
310:             raise RuntimeError("A5 MegaMoE requires a current vLLM configuration.")
311:         buffer_tokens_per_rank = get_a5_mega_moe_buffer_tokens_per_rank(vllm_config)
312:         key = self._make_buffer_key(
313:             fused_experts_input,
314:             intermediate_hidden,
315:             buffer_tokens_per_rank=buffer_tokens_per_rank,
316:         )
317:         mega_moe_group = get_mega_moe_group()
318:         state: _MegaMoESymmetricBufferState | None = getattr(
319:             mega_moe_group,
320:             _MEGA_MOE_BUFFER_STATE_ATTR,
321:             None,
322:         )
323:         if state is not None:
324:             if state.key != key:
325:                 raise RuntimeError(
326:                     "A5 MegaMoE symmetric buffer is process-wide and cannot be replaced during inference: "
327:                     f"initialized={state.key}, requested={key}."
328:                 )
329:             return state.buffer
330:
331:         get_symm_buffer_for_mega_moe, _ = _get_mega_moe_ops()
332:         buffer = get_symm_buffer_for_mega_moe(
333:             mega_moe_group.device_group,
334:             num_experts=key.num_experts,
335:             num_max_tokens_per_rank=key.buffer_tokens_per_rank,
336:             num_topk=key.top_k,
337:             hidden=key.hidden_size,
338:             intermediate_hidden=key.intermediate_hidden,
339:             dispatch_quant_mode=key.dispatch_quant_mode,
340:             dispatch_quant_out_dtype=key.dispatch_quant_out_dtype,
341:         )
342:         setattr(
343:             mega_moe_group,
344:             _MEGA_MOE_BUFFER_STATE_ATTR,
345:             _MegaMoESymmetricBufferState(key=key, buffer=buffer),
346:         )
347:         return buffer
```

## 探针与操作

核查命令（审查会话实际执行，事件 350）：

```
grep -n "refresh_moe_hccl_groups\|_MoECommMethods" vllm_ascend/device_allocator/sleep_mem_optimized.py
```

以及读取 `vllm_ascend/device_allocator/sleep_mem_optimized.py`（120-186 行，事件 130/132）、`vllm_ascend/ops/fused_moe/moe_comm_method.py`（注册表与 MegaMoE buffer 分配段）、`vllm_ascend/ops/fused_moe/mega_moe.py`（_get_sym_buffer）。

本条为只读审查发现，未实施修复；"`refresh_moe_hccl_groups` 同时遍历 `_MoECommMethodsByTopology` 的所有 bucket"与"wake 时清除 `_MEGA_MOE_BUFFER_STATE_ATTR`/`mega_moe_symm_buffer` 缓存并重建"的修复建议未经验证，不能当作已验证修法采用。

## 机制与判别

结论 1：HcclSleepWakeupManager.wakeup() 重建全部 HCCL PG 后仅 refresh_moe_hccl_groups 遍历扁平 _MoECommMethods 表；dspark draft 拓扑实例只存在于 _MoECommMethodsByTopology 分桶，唤醒后 draft 的 TokenDispatcherWithMC2.moe_all_to_all_group_name 仍指向已销毁的 HCCL 通信名。
- 证据：事件 132（refresh 只遍历扁平表）+ 事件 28（分桶注册表逐字）。
- 机制：draft 的 `npu_moe_distribute_dispatch_v2/combine` 使用野通信句柄 → 挂死或数据错乱。

结论 2：A5 MegaMoE 对称缓冲区缓存在 mega_moe_group 的 _MEGA_MOE_BUFFER_STATE_ATTR 属性上进程级复用（state 非 None 直接 return state.buffer），restore_hccl 原地重建 device_group 后缓存 buffer 内部持有旧通信句柄且无任何重建/刷新逻辑。
- 证据：事件 17（_get_sym_buffer 逐字；323-329 行显示命中缓存即返回）。
- 机制：与 dispatcher 的 `refresh_hccl_group` 不对称——buffer 路径完全没有 wake 侧处理；触发条件 FUSED_MC2 + sleep/wake → MegaMoE 集合通信失败或静默错误。

结论 3：触发条件为 Level-2 sleep/wake + dspark draft 拓扑异于 target（或 FUSED_MC2 的 MegaMoE 组），是"长稳测试随时间劣化"的候选根因（若长稳流程含 sleep 周期）；私有池本身的分配/释放/ref 计数/deferred free 逐路径核对未发现双释放或永久泄漏。
- 可区分解释分支（同一报告的长稳根因排序）：
  - 劣化台阶状出现在每次 sleep/wake 之后 → 指向本条（P1-6/P1-7，排序第 1）。
  - 调度进程内存单调增长 → 指向 Mooncake `_private_circle_receiving_requests` 慢性泄漏（P2-8，排序第 2）。
  - 精度随负载波动而非资源退化 → 指向前缀命中 bounded-replay 截断（P1-1，排序第 3）。
  - 锁页内存碎片 → 每步新建 pinned 缓冲（P3-10，排序第 4）。
- 未验证推断：draft 野句柄的故障形态（挂死 vs 数据错乱）与长稳流程是否含 sleep 周期均未实测确认。

## 验证信号

- 信号等级：代码事实（read/grep 工具结果），非运行验证。
- 本轨迹内观测到的客观信号：事件 132（sleep_mem_optimized.py 完整生命周期代码：destroy_hccl/restore_hccl/refresh_moe_hccl_groups 只遍历扁平 _MoECommMethods）、事件 28（_MoECommMethodsByTopology 分桶注册表原文）、事件 17（MegaMoE _get_sym_buffer 进程级缓存原文）、事件 352（grep 确认 refresh 相关行号）。
- 平台：Ascend NPU（PD 分离 + dspark + enable_fused_mc2=1 生产配置）。
- 无性能/资源数值结论（只读审查；未运行长稳复现）。

## 适用与失效边界

- 适用：开启 Level-2 sleep/wake 的 vllm-ascend DeepSeek-V4.1 部署，且含 dspark draft（拓扑异于 target）或 FUSED_MC2/MegaMoE。
- 不适用：不含 sleep/wake 周期的长稳流程（此时应优先排查 Mooncake 接收字典泄漏与 pinned 内存 churn）。
- 版本边界：baebb4dda 引入 draft 拓扑分桶（mc2_draft 组）后本缺口成立；`_MoECommMethodsByTopology` 注册表本身无泄漏（仅刷新缺口）。
- 停止/回退条件：若 wake 后 draft 通信即挂死（响亮失败），可快速确认 P1-6；若仅数据错乱则表现为静默精度劣化，需用通信计数/日志定位。
- 修复方向（未验证）：`refresh_moe_hccl_groups` 同时遍历 `_MoECommMethodsByTopology` 的所有 bucket；wake 时清除 `_MEGA_MOE_BUFFER_STATE_ATTR`/`mega_moe_symm_buffer` 缓存并重建。
