---
{
  "type": "Runbook",
  "title": "DSV4.1 D 侧 async spec decode Embedding aivec 334 崩溃：-1 采样占位符进入 draft 模型 input_ids 的根因定位",
  "description": "DSV4.1 PD 分离部署 D 侧开启 --async-scheduling + dspark 投机解码后，压测下 decode 报 Embedding 算子 aivec 334。根因是 vLLM 的 -1 采样占位符经 backup fallback 与 copy_and_expand 内核进入 draft 模型 input_ids，target 侧有专门的 sanitizer 而 draft 侧没有防护。",
  "tags": [
    "task.debugging",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# DSV4.1 D 侧 async spec decode Embedding aivec 334 崩溃：-1 采样占位符进入 draft 模型 input_ids 的根因定位


## 摘要

DSV4.1 PD 分离部署 D 侧开启 --async-scheduling + dspark 投机解码后，压测下 decode 报 Embedding 算子 aivec 334。根因是 vLLM 的 -1 采样占位符经 backup fallback 与 copy_and_expand 内核进入 draft 模型 input_ids，target 侧有专门的 sanitizer 而 draft 侧没有防护。

## 适用场景

DSV4.1 / vllm-ascend-dsnext PD 分离部署：D（decode）侧开启 `--async-scheduling` 并使用 dspark 投机解码（target 与 draft 均捕获进 ACL 图），压测或持续有新请求从 prefill 移入的场景。也适用于任何“vLLM 采样占位符 -1 可能进入 spec-decode drafter 的 input_ids”的 fork 环境。

## 触发与观测

触发：异步调度 + spec decode 下，新调度请求的 spec 槽位被 v1 调度器以 `-1` 占位（scheduler.py pad_spec_decode）；本步没有有效采样 token 的行（刚移入/被 discard 的请求）触发 backup fallback。
观测：decode 间歇性抛算子执行异常并最终在 get_output 的 `async_copy_ready_event.synchronize()` 暴露 AICORE 粘性错误。P 侧（同步调度）不触发，可作为不对称旁证。

## 探针与操作

1. 一行确认实验（改前先验）：在 `set_inputs_first_pass` 里 `n = next_token_ids.shape[0]` 之后打印 `logger.warning("seed neg=%d", int((next_token_ids < 0).sum()))`——新请求到达的步骤出现非 0 即坐实 -1 进入 drafter。
2. 代码链路静态核对：scheduler 的 -1 占位、get_token_id 的 return -1、prepare_next_token_ids_padded 的 fallback、copy_and_expand 内核 bonus 写入、target sanitizer 与 draft 侧缺失的不对称。

## 机制与判别

判别要点（为什么只有 draft 崩、且只在 async+压测下崩）：
- target forward 前有 `_sanitize_placeholder_input_ids_for_forward`（masked_fill_==PLACEHOLDER_TOKEN_ID→0），上游 v0.27.1 `_preprocess` 还有 `clamp_(min=0)`；draft 路径 grep 全 spec_decode/ 无任何等价消毒。
- dspark.py:252-253 自带的 `torch.where(input_ids==-1,0,input_ids)` 只喂 MoE 且在 embedding（:247）之后——作者知道 -1 会出现，但防护位置错了。

## 适用与失效边界


适用于来源 DSV4.1 async DSpark draft 输入链路的静态排查。-1 placeholder 到 embedding 的生产/消费路径是源码观察，不能据此排除其他路径，也不能断言非 async 配置永不触发。运行时确认探针、设备复现与修后精度/接受率未取得；补丁与静态检查见 [embedding 前消毒候选](dspark_draft_embedding_placeholder_sanitize_fix.md)。

## 验证信号

### 来源结论b

> -1 的生产链路（各环节均有 file:line 证据）：async 调度路径向 host token 表 append PLACEHOLDER_TOKEN_ID=-1（model_runner_v1.py:1029 prev_sampled_token_ids / :1043 output_token_ids.append）；CachedRequestState.get_token_id 对未知/未就绪索引显式 return -1；prepare_next_token_ids_padded 的 fallback 把该 -1 写进 next_token_ids（对刚调度的新请求/被 discard 的请求触发，压测下反复出现，故间歇）；copy_and_expand_dflash_and_dspark_inputs 内核把 bonus=next_token_ids[req_idx] 直写 draft 的 input_ids。防护不对称：target 侧 forward 前有 _sanitize_placeholder_input_ids_for_forward（model_runner_v1.py:2556，masked_fill_==PLACEHOLDER_TOKEN_ID→0），上游 v0.27.1 _preprocess 还有 clamp_(min=0)，draft 侧 grep 全 spec_decode/ 无任何等价物；dspark.py:252-253 自带的 torch.where(input_ids==-1,0,input_ids) 在 :247 embedding 之后、只喂 MoE 路径，够不到 embedding。仅 D 侧崩溃是因为 P 侧同步调度不经过 async 占位符路径。


## 补充机制片段

### 机制片段

```
2556	    def _sanitize_placeholder_input_ids_for_forward(
2557	        self,
2558	        scheduler_output: "SchedulerOutput",
2559	        num_forward_tokens: int,
2560	    ) -> None:
2561	        scheduled_spec_tokens = scheduler_output.scheduled_spec_decode_tokens
2562	        if not scheduled_spec_tokens:
2563	            return
2564	        if not any(
2565	            PLACEHOLDER_TOKEN_ID in token_ids
2566	            for token_ids in scheduled_spec_tokens.values()
2567	        ):
2568	            return
2569
2570	        input_ids = self.input_ids.gpu[:num_forward_tokens]
2571	        input_ids.masked_fill_(input_ids == PLACEHOLDER_TOKEN_ID, 0)
2572
```
