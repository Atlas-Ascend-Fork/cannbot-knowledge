---
type: Runbook
title: 跳过 Prefill 的 Decode 能跑通：只能验证执行与性能，不能验收生成精度
description: 区分 Kimi K3 的 skip_prefill 和历史 PD prefill stub，检查 cache 是否真实填充；全零 cache、占位
  token 与强制均衡实验均需和真实请求验收分开。
tags:
- task.testing
- task.debugging
- topic.speculative_decoding
- topic.kv_cache
status: stable
sources: []
created_at: '2026-10-30T03:17:20Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      serving_mode:
      - offline
---

# 跳过 Prefill 的 Decode 能跑通：只能验证执行与性能，不能验收生成精度

## 现象

为了绕过长 Prefill 的计算或激活内存，给 Kimi K3 打开 `skip_prefill` 后，Decode 图可以捕获、内核可以执行，也可能打印正常的时延和生成文本。此时最容易误把“Decode 可运行”当成“模型精度已通过”，或把该结果描述成真实长上下文、真实 PD 分离的端到端结果。

本卡解释测试输入的真实性边界，不把异常文本当作已定位的 kernel 精度缺陷。没有经过 Prefill 的 cache 缺少真实上下文；输出 token 不是该 prompt 正常推理的结果。

## 适用场景

- 目标：昇腾 950PR/DT 的固定批次离线 Kimi K3，主模型可带 DSpark 草稿模型。
- 当前入口：`model_infer.py` 的 `KimiK3Infer._prepare_decode_input()`、`_stub_prefill()` 和 `_get_prefill_stub_tokens()`；配置读取 `model_config.skip_prefill`、`model_config.prefill_stub_token_id`。
- 另一个历史入口：调度器的 `simulate_pd_prefill_stub` 与 `_drain_waiting_queue_for_stub()`。这属于不同运行框架，不能假设两个开关可互换或同时存在。
- 允许用途：明确标记为打桩的 Decode 执行/局部性能实验。禁止用该路线验收上下文精度、cache 交接正确性、真实 KV 传输或线上 PD 功能。
- 本轮只核对实现与测试语义，没有运行模型或硬件 benchmark，具体 CANN/PyTorch 版本的通过情况未知。

## 根因与状态流

真实链路是 prompt → Prefill 写入 KDA/MLA state → 主模型给出首 token → 进入 Decode；启用 DSpark 时还要维护草稿 cache。打桩路线主动绕过了计算，但仍构造一个看起来合法的 Prefill→Decode 交接：

1. 清零主模型 cache；有草稿 cache 时也清零。
2. 选一个非 EOS token，追加到输出容器。
3. 调用正常的结果合并方法，把输入形态切换为 Decode；逻辑长度可以看起来像已有 prompt，但 cache 内容未由这些 prompt 计算产生。
4. 直接执行 Decode。因此 shape、容量、token id 都合法，仍不能推出上下文状态真实。

“cache 已分配”“长度已推进”“模型没有报错”是不同事实，均不能代替 Prefill 内容已经计算并写入的证据。

## 完整实现单元

下面三个方法保留在原 `KimiK3Infer` 类中使用，依赖 `torch`、`logging`、cache manager、EOS 集合与已有 `_append_tokens` / `merge_multi_cycle_res`，不是一份独立推理脚本。

占位 token 的选择方法保留 prompt 尾 token，并在需要时替换 EOS。若用户显式配置占位 token，构造阶段还会拒绝 EOS；不能随意选一个会立即终止的 token 后认为 Decode 没有问题：

```python
def _get_prefill_stub_tokens(self, input_dict):
    if self.prefill_stub_token_id is not None:
        return torch.full(
            (self.batch_size,),
            self.prefill_stub_token_id,
            dtype=torch.long,
            device=self.device,
        )

    stub_tokens = torch.stack(
        [token_row[-1] for token_row in input_dict["prompt_token_rows"]]
    ).to(dtype=torch.long, device=self.device)
    if not self.eos_ids:
        return stub_tokens

    eos_mask = torch.zeros_like(stub_tokens, dtype=torch.bool)
    for eos_id in self.eos_ids:
        eos_mask |= stub_tokens == eos_id
    if eos_mask.any():
        fallback_token_id = next(
            token_id
            for token_id in range(self.model.config.vocab_size)
            if token_id not in self.eos_ids
        )
        stub_tokens[eos_mask] = fallback_token_id
    return stub_tokens
```

打桩交接与实际分派如下，注意两组 cache 都被 reset，以及真实 Prefill 分支与打桩分支互斥：

```python
def _stub_prefill(self, input_dict):
    """Build the Prefill-to-Decode handoff without running Prefill."""
    self.cache_manager.reset_cache(input_dict["cache_data"])
    if input_dict.get("draft_cache_data") is not None:
        self.cache_manager.reset_cache(input_dict["draft_cache_data"])

    stub_tokens = self._get_prefill_stub_tokens(input_dict)
    self._append_tokens(input_dict, stub_tokens)
    self.merge_multi_cycle_res(input_dict, [stub_tokens])

    if not self._prefill_stub_logged and self.attn_tp_rank == 0:
        logging.warning(
            "Prefill is skipped: KDA/MLA caches are zero-filled and a synthetic "
            "Decode input token is used. Generated text is invalid; use this mode "
            "only for Decode execution and performance testing."
        )
        self._prefill_stub_logged = True
```

```python
def _prepare_decode_input(self, input_dict, warm_up=False):
    if self.skip_prefill:
        self._stub_prefill(input_dict)
        return []

    cycle_next_tokens = []
    prefill_times = []
    for cycle_idx in range(self.prefill_cycles):
        next_tokens, _, elapsed = self.prefill_infer_single_cycle(
            input_dict, cycle_idx, warm_up=warm_up
        )
        cycle_next_tokens.append(next_tokens)
        prefill_times.append(elapsed)
    self.merge_multi_cycle_res(input_dict, cycle_next_tokens)
    return prefill_times
```

历史调度器的实现则直接推进请求状态并分配槽位。以下完整方法没有远端 KV 接收步骤；“模拟已经传输”的注释不等于传输已发生：

```python
def _drain_waiting_queue_for_stub(self, engine: ExecutionEngine) -> None:
    """Move all waiting requests to running_requests for PD stub mode.

    In simulate PD mode, prefill is stubbed (no real prefill computation)
    to avoid the memory cost of prefill activation.  This method drains
    the waiting_queue by directly moving requests to running_requests,
    simulating "KV already transferred from Prefill instance".  KV cache
    blocks are allocated and computed_len is set so decode can proceed.
    """
    while self.waiting_queue:
        req = self.waiting_queue.popleft()
        req.is_prefill_done = True
        req.computed_len = max(req.prompt_tokens - 1, 0)
        self.prefilled_request_count += 1
        if engine.kvcache_manager:
            engine.kvcache_manager.allocate_slots(
                req.request_id,
                computed_tokens=req.computed_len,
                num_new_tokens=1 + engine.next_n,
                lookahead_tokens=max(engine.next_n - 1, 0),
            )
        self.running_requests[req.request_id] = req
```

## 判别步骤

1. 读取最终生效配置，区分 `skip_prefill`、`skip_warm_up` 和历史 PD stub。跳过 warmup 只影响启动过程，不能据此判断正式 Prefill 是否打桩。
2. 确认命中的函数。看到 `Prefill is skipped: KDA/MLA caches are zero-filled ... Generated text is invalid` 这条代码中定义的 warning，应把该次输出标为合成上下文；未看到 warning 也需检查 rank 和只打印一次的门控，不能反推真实 Prefill 已运行。
3. 检查主模型、草稿模型 cache 的 reset、写入和后续读取顺序。不能只检查 cache 大小或张量是否存在。
4. 若使用调度器 stub，检查 `computed_len`、block 分配和请求队列迁移；另行寻找实际 KV 传输及接收完成的证据。仅有 running_requests 中的请求不够。
5. 分别记录路由相关开关。`force_eplb` 等强制均衡设置会改变 MoE 路径；打桩、强制路由与原始真实请求的结果不能混作一组精度验收。

## 设计决策与实验口径

打桩的价值在于控制 Prefill 成本，让固定配置的 Decode 执行得到单独观察。它主动牺牲上下文真实性，故实验记录必须明确“Prefill 打桩、cache 未由真实上下文填充、是否改变路由”。局部耗时可用于标明条件的路线对照；本卡没有实测收益，也不能从一个打桩样本推导真实上下文下的请求时延或质量。

## 验证信号

本轮静态核对了开关分派、两组 cache reset、token 选择、warning 以及历史队列迁移。以上是实现行为，不是本轮成功执行的日志；尚未取得 NPU 实测结果。

## 恢复验收

需要验收生成精度时：关闭对应打桩开关，重新初始化进程和 cache，使用原权重、实际路由及真实 prompt 执行完整 Prefill。逐项核对主模型和草稿 cache 的内容写入、request/slot 对齐、Prefill→Decode 状态交接、输出 token、EOS 行为与任务指标。只有这一组真实输入结果可以用于模型精度结论。

## 坏实践、回退与失效边界

- 看到可打印文本就认为上下文有效，或用强制均衡路由掩盖真实路由问题，都会混淆测试目标。
- 不能只在已有进程内改一个开关就继续复用打桩 cache；恢复时重启完整推理，避免污染对照。
- 历史 PD stub 未证明远端 Prefill/KV 传输接通。真实 PD 的协议、同步和所有权应单独验收。
- 此卡只帮助划分测试证据；关闭打桩后仍有精度问题时，要沿真实 cache、路由和算子结果定位，不将“关闭开关”描述为通用精度修复。
