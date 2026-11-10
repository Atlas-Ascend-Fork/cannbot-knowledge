---
{
  "type": "Runbook",
  "title": "npugraph_ex 仅 Decode 入图部署模式：静态输入原地更新 + list[int] replay + 一键回退与依赖门控降级",
  "description": "在独立部署 Runner 中以 exe_mode（yaml/HYV4_EXE_MODE）开关 Decode 图模式：图 cache 绑定为 model 常驻属性、input_ids/position_ids/graph_slot_mapping 预分配并原地更新、FA 长度以 list[int] 传入 replay 刷新；use_graph_decode 依赖 use_paged_fa 且全融合开启，条件不满足自动降级 eager 并告警；长 prompt overflow 步骤通过 actual_seq_* is not None 门控留在 eager。reviewer 独立验证：回退/降级/长 prompt 输出 token 与图模式逐位一致，无 crash、无错误静默。",
  "tags": [
    "task.implementation",
    "topic.compilation",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-09T09:37:53Z",
  "platforms": [
    "950"
  ]
}
---

# npugraph_ex 仅 Decode 入图部署模式：静态输入原地更新 + list[int] replay + 一键回退与依赖门控降级

## 适用场景

- 模型/框架：HYV4 独立部署（自管 Runner，`runner_hy_v4.py` + vendored `models/modeling_hy_v4.py`），阶段 3 全融合 + 阶段 2 Paged MLA + FA v2 之上叠加 Decode-only 图模式；无量化。
- 平台/版本：Ascend950PR_9589 单卡，CANN 9.1.0，torch 2.12.0+cpu，torch_npu 2.12.0；npugraph_ex（aclgraph 捕获/重放）后端，试验特性。
- 部署形态：batch=1、单请求逐 prompt 生成、decode 固定单 token shape；图 cache 与 eager prefill 共用同一 paged cache 的缓冲。
- 缺失信息说明：多 batch packed、长上下文（kv_len > 2048）、多卡/TP/EP 并行均未覆盖；回退/降级验证基于随机权重固定种子（seed=1234）。

## 触发与观测

部署目标：仅 Decode 入图（Prefill 保持 eager），且必须保留 enable 开关/回退方式，不得降低模型完整性。观测到的部署后稳态（reviewer 独立端到端运行，`bash infer.sh`）：

```
2026-10-13 20:03:08,642 INFO compiling decode graph (backend=npugraph_ex, fullgraph=True, dynamic=True) ...
2026-10-13 20:03:25,164 INFO hy_v4 inference time cost of prefill is 32.80 ms
2026-10-13 20:03:25,169 INFO hy_v4 inference time cost of decode is 4.67 ms
...
2026-10-13 20:03:25,197 INFO Request 0: generated_token_ids: [101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480]
```

## 探针与操作

完整实现单元（均在 `runner_hy_v4.py` / `config/hy_v4.yaml` / `models/modeling_hy_v4.py`）：

1. **配置开关（yaml 逐字，`config/hy_v4.yaml`）**：

```
  # Stage-5 execution mode. "npugraph_ex" enables the decode-only graph
  # (npugraph_ex/aclgraph) on top of the stage-3 fused path; prefill stays eager.
  # One-switch fallback to the stage-3 non-graph path: set "eager" here or
  # export HYV4_EXE_MODE=eager (no model/operator rollback needed).
  exe_mode: "npugraph_ex"
```

2. **依赖门控（runner edit 逐字）**：图模式要求 Paged FA + 全融合，否则自动降级：

```
        # Stage-5 decode graph mode (npugraph_ex, decode only; prefill stays
        # eager). Requires the Paged FA path and the full stage-3 fusion set:
        # without the fused MoE the eager expert loop uses ``torch.nonzero``,
        # which is not graph-traceable. ``exe_mode: eager`` (or
        # ``HYV4_EXE_MODE=eager``) is the one-switch fallback to the stage-3
        # non-graph path.
        requested_graph = self.exe_mode in ("npugraph_ex", "graph", "graph_mode")
        self.use_graph_decode = requested_graph and self.use_paged_fa and all(self.fusion_flags.values())
```

3. **图 cache 绑定 + 静态输入 + 编译（runner 最终代码逐字）**：cache 绑定为 model 常驻属性（使捕获的 in-place scatter 写向稳定地址），输入张量预分配、replay 前原地更新；FA 长度以 `list[int]` 传入（npugraph_ex 在 replay 期经 `updated_param_keys` 刷新，`kv_len` 增长不触发重编译）：

```
        self.graph_cache = self._new_paged_cache()
        self.graph_cache.graph_decode = True
        self.graph_cache.is_prefill = False
        self.model.graph_cache = self.graph_cache
        # Static input tensors updated in place before every replay.
        self._graph_input_ids = torch.zeros(1, 1, dtype=torch.long, device=self.device)
        self._graph_position_ids = torch.zeros(1, 1, dtype=torch.long, device=self.device)
        compile_options = {
            "inplace_pass": True,
            "input_inplace_pass": True,
            "pattern_fusion_pass": True,
            "reuse_graph_pool_in_same_fx": True,
            "clone_input": True,
            "clone_output": False,
            "remove_noop_ops": True,
        }
        logger.info("compiling decode graph (backend=npugraph_ex, fullgraph=True, dynamic=True) ...")
        self._compiled_decode = torch.compile(
            self.model.decode_graph,
            backend="npugraph_ex",
            fullgraph=True,
            dynamic=True,
            options=compile_options,
        )
```

4. **每步 replay（runner 最终代码逐字）**：

```
        self._graph_input_ids.copy_(next_token.to(torch.long))
        self._graph_position_ids.fill_(start)
        self.graph_cache.graph_slot_mapping.fill_(start)
        self.graph_cache.is_prefill = False
        out = self._compiled_decode(
            self._graph_input_ids, self._graph_position_ids, [1], [start + 1]
        )
        self.graph_cache.kv_len = start + 1
        return out.logits
```

5. **长 prompt overflow 门控**：`_forward_paged` 内 `graph_decode` 分支要求 `actual_seq_qlen is not None and actual_seq_kvlen is not None`，使 > prefill_chunk 的 eager q_len=1 余量步骤留在原 eager 路径（代码工件见[HYV4 Decode 29 处 Dynamo 图中断消除配方：npugraph_ex 整图捕获 + 0 重编译 + 同会话 decode 4×提速](hyv4_decode_dynamo_npugraph_ex.md)）。

## 机制与判别

- Runner 以 exe_mode（yaml 或 HYV4_EXE_MODE 环境变量）一键切换：npugraph_ex 开启 Decode 图模式、eager 一键回退到阶段 3 非图路径；reviewer 复核回退运行无图编译日志且生成 token [101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480] 逐位一致。
- 图模式依赖门控要求 use_paged_fa=true 且全部融合开关开启（use_graph_decode = requested_graph and self.use_paged_fa and all(self.fusion_flags.values())）；条件不满足时自动降级 eager decode 并输出 WARNING exe_mode=npugraph_ex requested but decode graph disabled (needs use_paged_fa=true and all fusion points on); falling back to eager decode，不 crash、无错误静默。
- 长 prompt（> prefill_chunk 的 eager q_len=1 overflow 步骤）与图模式共用同一 paged cache 时，通过在 _forward_paged 门控要求 actual_seq_qlen is not None 且 actual_seq_kvlen is not None 避免 overflow 步骤误入图分支；reviewer 复核图/eager 长 prompt 输出 token [4792, 114720, 60457, 97034, 44537, 44537, 4792, 114720] 逐位一致。
- npugraph_ex 编译期出现 npu_fused_infer_attention_score_v2.out 输出不得与输入 alias 的 deprecated UserWarning（.out static-workspace 替换机制所致），本会话内结果正确（cos 1.0 / argmax 7/7），但存在跨 torch_npu 版本可移植性风险。
- 未验证推断：`.out` aliasing 警告在未来版本（警告文本明示 "will become an error in PyTorch 2.12"）是否实际报错，未在本环境验证；`clone_output=False` 依赖调用方不改写输出张量的假设在本 Runner 成立，其他调用方未验证。

## 验证信号

仅列本组来源观测轨迹内实际观测到的信号（reviewer 独立复跑，Ascend950PR_9589 单卡，seed=1234）：

- **回退（一键 eager）**：`HYV4_EXE_MODE=eager bash infer.sh` EXIT=0、compile mentions 0、decode 17.85–18.23 ms、生成 token `[101453, 58721, 70389, 70389, 76480, 76480, 76480, 76480]` 与图模式逐位一致；yaml `exe_mode: "eager"` 路径同样无编译且 token 一致（单次观测）。
- **门控降级**：`HYV4_FUSE_RMS_NORM=0 bash infer.sh`（融合缺点）与 `HYV4_USE_PAGED_FA=0 bash infer.sh`（paged 关闭）均 EXIT=0、无编译、输出 WARNING 并自动 eager，decode ~20 ms，无 error/traceback；降级日志逐字（融合缺点场景）：

```
EXIT=0
compile mentions: 0
2026-10-13 20:14:30,940 WARNING exe_mode=npugraph_ex requested but decode graph disabled (needs use_paged_fa=true and all fusion points on); falling back to eager decode
```

- **长 prompt 门控**：图模式与 eager 模式跑同一 60+ token 长_prompt，输出 token 逐位一致；图模式侧日志逐字：

```
EXIT=0
2026-10-13 20:10:31,352 INFO compiling decode graph (backend=npugraph_ex, fullgraph=True, dynamic=True) ...
2026-10-13 20:10:48,645 INFO hy_v4 inference time cost of prefill is 556.46 ms
2026-10-13 20:10:48,678 INFO Request 0: generated_token_ids: [4792, 114720, 60457, 97034, 44537, 44537, 4792, 114720]
```

- **图模式真实生效**：reviewer 独立 verify（`tools/verify_graph_decode.py --reps 12`）prefill cos 1.000001、decode cos_min 1.0、argmax 7/7、capture 14900.848 ms、同会话 decode 16.479 → 4.449 ms（比值 0.27，单次观测）；独立 `explain` 复跑 1 graph / 0 break、recompile 计数 0。
- **deprecated aliasing 警告逐字**（编译期出现于 npugraph_ex 捕获时）：

```
UserWarning: npu::npu_fused_infer_attention_score_v2.out (with implementation in ???): The output of this custom operator (1) must not also be an input to this custom operator and (2) may not alias any inputs to this custom operator or other returns.
```

## 适用与失效边界

- 版本条件：结论限定 torch 2.12.0+cpu / torch_npu 2.12.0 / CANN 9.1.0；npugraph_ex 为试验特性、官方注明暂不支持商用。torch_npu 升级后 FA `.out` aliasing 可能由警告变错误，升级前需回归本模式（先跑 `verify_graph_decode.py`）。
- 门控条件：本模式硬依赖 Paged FA 路径与阶段 3 全融合（use_paged_fa=true 且全部 fuse_* 开启）；任一关闭即自动降级 eager decode——这是预期行为而非故障，排障时先看 WARNING 再查开关。
- shape/规模条件：仅 batch=1、decode 单 token 固定 shape、`graph_slot_mapping` 为 [1]；batch>1 不等长 packed、kv_len > 2048 的 DSA 长上下文均不适用（需 chunked prefill / sparse FA 另行设计）。
- 回退条件：yaml `exe_mode: "eager"` 或环境变量 `HYV4_EXE_MODE=eager` 一键回退且逐位复现；若观察到图模式输出异常（乱码/重复/全零/提前 EOS），应立即回退，再按 [HYV4 Decode 图中断与重编译排查配方](hyv4_decode_dynamo_npugraph_ex.md)中的 `torch._dynamo.explain(decode_graph)` 与 `torch._logging.set_logs(recompiles=True)` 探针复核图中断和重编译。
- 停止条件：图捕获开销（本会话 ~14 s，单次观测）对短生命进程不可摊销时，应关闭图模式；宿主重载导致绝对耗时漂移时，只以同会话 A/B 比值评估。
