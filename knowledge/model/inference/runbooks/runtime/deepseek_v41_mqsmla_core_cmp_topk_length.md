---
{
  "type": "Runbook",
  "title": "DeepSeek-V4.1 Mqsmla 非法索引风险排查：预计算 cmp_topk_length 上界与有效索引数的缺口",
  "description": "静态审查发现 vllm-ascend 的预计算 cmp_topk_length 按位置推导，而 runtime 路径按有效索引计数；若前者大于实际有效数，且算子按长度消费 -1 填充槽，可能产生非法寻址。原始轨迹只有用户故障日志与源码观察，没有核对 checkpoint 候选池参数或运行时复现。建议记录同一token/channel的上界与实际数并验证假设，不能直接把其他同步、ABI或数据面问题排除。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "agnostic"
  ]
}
---
# DeepSeek-V4.1 Mqsmla 非法索引风险排查：预计算 cmp_topk_length 上界与有效索引数的缺口

## 适用场景

- 框架/版本：vllm-ascend，分支 `wzc` @ `c76608fea debug qli`（含 `81477c90f` qli/qsli 适配与 `5426d7eed` mooncake 修复）；文件 `vllm_ascend/attention/dsa_v41.py`（`_build_kernel_metadata`、`_sparse_mla_attention`、`pad_sparse_indices`）与 `vllm_ascend/ops/triton/prepare_indexer_indices.py`。
- 部署形态：DeepSeek V4.1 PD 分离（Mooncake）+ private circle pool 使能 + D 侧 decode ACL graph；故障集中在 decode 节点。
- 症状：`AI Core kernel execution failed`，fault kernel 为 `MqsmlaKernel`（即 `mixed_quant_sparse_flash_mla` FA 主算子）。
- 信息缺口声明：本卡为代码级风险假设（含落盘根因报告 decode_aicore_mqsmla_rootcause.html）；"候选池几何换算"依赖 checkpoint config 数值（candidate_topk_blocks / candidate_block_size / index_topk），轨迹内未取值核定；无运行时复现验证。

## 触发与观测

故障触发（用户提供报错日志，来源记录 事件 628，原文）：

```
[ERROR] RUNTIME(420294,):2026-09-27-16:02:31.593.687 [stream.cc:1834]420854 GetError:[DFX_INFO]AI Core kernel execution failed, device_id=6, stream_id=415, report_stream_id=59, task_id=32, flip_num=0, fault kernel_name=Z30kernel_MqsmlaKernel___call___029KernelArgTensor_bfloat16_t_2dS_24KernelArgTensor_float_2d26KernelArgTensor_uint8_t_4d26KernelArgTensor_int32_t_2d26KernelArgTensor_uint8_t_1dS2_S2_26KernelArgTensor_int32_t_1dS4_fiS3, fault kernel info ext=none, program id=150, hash=6402875724709821103.   decode节点报错
```

用户场景描述（事件 516）："deepseekV41 pd分离使能private pool 当前分支代码在decode aclgraph模式下attention算子执行报错"。

核心机制假设（静态审查，未运行验证）：

> 纯 decode 预计算路径使用位置上界作为 cmp_topk_length，而无效槽以 -1 填充。若同一 token/channel 的上界大于实际有效数，且算子未跳过这些槽位，存在读取 -1 后非法寻址的风险。是否正是本次生产故障的原因，尚无运行时证据。

> candidate-filtered 层、PD导入或前缀恢复可能形成实际数小于上界的条件；是否存在缺口，取决于真实索引与 checkpoint 几何。runtime 路径的计数方式提供对照，但不能据此判整个路径安全或排除私有环、ACL graph/ExternalEvent 等其他故障。

## 探针与操作

审查执行的探针链（事件 641-664）：
1. `sed` 定位 `_build_kernel_metadata`（事件 641/643）——确认 cmp 通道是位置上界。
2. `grep -rn "def pad_sparse_indices"` + `sed`（事件 646/647）——确认无效槽填充值。
3. `sed -n '1429,1505p' vllm_ascend/attention/dsa_v41.py`（事件 650/651）——确认算子消费的是哪条元数据路径。
4. `grep` 候选池几何与 `prepare_indexer_indices`（事件 654）。
5. 行号复核 `grep -n "def _sparse_mla_attention\|def _build_kernel_metadata\|... \|" vllm_ascend/attention/dsa_v41.py`（事件 663/664）：`649: def pad_sparse_indices`、`1756: def _build_kernel_metadata`、`1800: valid_length = (pos_i32 + 1) // r`。

根因报告已落盘：`decode_aicore_mqsmla_rootcause.html`（事件 667，write 工具，59KB 级 HTML，含 4 步根因链、触发条件表、安全路径对照、验证实验与修复方案）。

验证实验（审查建议，未执行）：
1. eager 对照（未执行）：D侧用相同输入、长度、并发与缓存状态分别复跑 eager/ACL graph，并记录实际元数据分支。eager仍失败可削弱纯图模式特有的解释，但不能独自锁定本假设；不复现也需考虑时序与调度差异。
2. 缺口探针（未执行）：在预计算消费点，对同一 token/channel 计算 `actual_valid_count = (cmp_indices >= 0).sum(-1)`。先确认它与 `cmp_topk_length` 的维度、token顺序和channel对应完全一致；必要时显式增加单例维度，禁止隐式广播。再检查 `(cmp_topk_length > actual_valid_count).any()`，这是上界多读的风险方向。记录原始shape及崩溃步两者分布，不把探针当成已验证修复。
3. 候选池几何核算：从 checkpoint config 取 candidate_topk_blocks / candidate_block_size / index_topk，代入换算判断导入请求的 gap 是否结构性必然。
4. 参考实现对拍：对照 cann-recipes deepseek_v4_1 的 `build_attn_metadata` 核对 cmp_topk_length 的参考算法——参考实现按实际有效数计算。

## 机制与判别

证据一：`_build_kernel_metadata` 中 win 通道用实际计数、cmp 通道只用位置上界（事件 643 逐字）：

```python
        win_topk_length = self._win_topk_length_buf[:num_tokens]
        win_topk_length.copy_((win_indices >= 0).sum(dim=-1).to(torch.int32))

        cmp_topk_lengths: dict[int, torch.Tensor] = {}
        for r in self._cmp_topk_length_bufs:
            buf = self._cmp_topk_length_bufs[r][:num_tokens]
            valid_length = (pos_i32 + 1) // r
            if index_topk > 0:
                valid_length = valid_length.clamp_max(index_topk)
            buf.copy_(valid_length.unsqueeze(1).to(torch.int32))
            cmp_topk_lengths[r] = buf
```

证据二：索引无效槽以 -1 填充并排在尾部（事件 647 逐字，dsa_v41.py:649-657；`prepare_indexer_indices` 把无效槽置 -1 并排序到行尾）：

```python
def pad_sparse_indices(indices: torch.Tensor, topk: int) -> torch.Tensor:
    """Convert V4.1's compact [T, K] selection into SMLA [T, 1, topk]."""
    if indices.ndim != 2:
        raise ValueError(f"V4.1 sparse indices must be rank 2, got {indices.shape}")
    if indices.shape[-1] > topk:
        raise ValueError(f"V4.1 sparse indices width {indices.shape[-1]} exceeds operator topk {topk}")
    if indices.shape[-1] < topk:
        indices = F.pad(indices, (0, topk - indices.shape[-1]), value=-1)
    return indices.unsqueeze(1).contiguous().int()
```

证据三：`_sparse_mla_attention` 的双路径（事件 651 逐字）——预计算分支读 builder 上界 buffer，runtime 分支按实际计数重建，构成该假设的判别依据：

```python
        if (
                precomputed_swa is not None
                and sub_batch == "full"
                and precomputed_swa.fa_metadata is not None
                and precomputed_swa.win_topk_length is not None
        ):
            n = q.shape[0]
            win_topk_length = precomputed_swa.win_topk_length[:n]
            ratio = self.role.compress_ratio
            if has_compressed and precomputed_swa.cmp_topk_lengths is not None:
                cmp_topk_length = precomputed_swa.cmp_topk_lengths[ratio][:n]
            else:
                cmp_topk_length = torch.zeros_like(win_topk_length)
            attention_type = "win" if ratio == 0 else f"c{ratio}a"
            op_metadata = precomputed_swa.fa_metadata[attention_type]
        else:
            win_topk_length = (win_indices >= 0).sum(dim=-1).to(torch.int32)
            cmp_topk_length = (
                torch.zeros_like(win_topk_length)
                if cmp_indices is None
                else (cmp_indices >= 0).sum(dim=-1).to(torch.int32)
            )
```

候选机制链（前3步有源码依据，第4步的故障因果待验证）：
1. 纯 decode 步没有 private circle plan（plan 仅在 `num_prefills > 0` 的混合步构建），`_native_attention` 调 `_sparse_mla_attention(sub_batch="full")` 命中预计算分支；A5 上 SWA builder 的 `_fa_precomputed` 为 True、positions 非空且 plan 为 None 时预计算激活——正是纯 decode 步。
2. 预计算的 cmp_topk_length 是 `(pos+1)//r` clamp 到 index_topk 的位置上界（dsa_v41.py:1800 一带）；win 通道则用 `(win_indices >= 0).sum()` 实际计数。预计算在 builder 阶段执行（索引此时尚未产生），是与实际内容脱钩的实现原因。
3. 索引无效槽是 -1 且排在尾部（prepare_indexer_indices.py:52-53 "invalid slots last"；pad_sparse_indices `F.pad(..., value=-1)`）。
4. 若 kernel 按长度消费且不跳过 -1：`actual < upper` 时被指示读取 `[actual, upper)` 区间的索引，读到 -1 并当作块表/平面索引用 → 负偏移/非法地址 → AI Core kernel execution failed。

判别（可区分的解释分支）：

| 路径 | 元数据来源 | cmp_topk_length | 结论 |
|---|---|---|---|
| 纯 decode 步（full batch） | builder 预计算 | 位置上界 | 待核对是否大于实际数 |
| 混合步 decode 子批（私有环） | runtime（sub_batch="decode"） | `(cmp_indices >= 0).sum()` 实际计数 | 避免该类计数缺口；不代表整体已验证安全 |
| 混合步 prefill 子批（workspace） | runtime | 同上 | 避免该类计数缺口；不代表整体已验证安全 |
| win 通道（所有路径） | 预计算或 runtime | 均为实际计数 | 避免该类计数缺口；不代表整体已验证安全 |

gap 的候选来源：candidate-filtered 消费层的有效数可能受候选池块数限制；PD导入/前缀恢复时位置上界与实际缓存内容也可能不一致。必须读取 candidate_topk_blocks、candidate_block_size、index_topk 并检查真实索引后，才能判断特定请求是否出现缺口；不能仅凭位置大就声称必现。

这些源码差异尚未排除私有环、ACL graph/ExternalEvent、ABI或数据时序问题。审查提出的修复方向均未实施验证：根据真实候选池几何限制预计算长度并区分不同消费层；或在消费点改用实际计数，同时重建匹配的FA调度元数据。是否可把 -1 定义为跳过哨兵，需核实算子契约；不能直接假设已支持。

## 验证信号

全部信号为代码读取类工具结果与落盘工件（客观事件），无运行时指标：

| 结论 | 信号（事件） | 证据等级 |
|---|---|---|
| cmp 通道位置上界 vs win 通道实际计数 | 来源记录:643（`_build_kernel_metadata` 段读取） | 工具结果（代码事实） |
| 无效槽 -1 填充 | 来源记录:647（pad_sparse_indices 全文 grep 输出） | 工具结果（代码事实） |
| 预计算/runtime 双路径消费 | 来源记录:651（_sparse_mla_attention 1429-1505 段读取） | 工具结果（代码事实） |
| 行号复核（649/1756/1800） | 来源记录:664（grep -n 输出） | 工具结果（代码事实） |
| 根因报告工件 | 来源记录:667（write decode_aicore_mqsmla_rootcause.html） | 工件事件（审查结论落盘） |

单次/条件说明：崩溃日志本身是用户提供的生产报错（非本轨迹复现）；是否出现gap的候选池几何换算依赖 checkpoint config 数值，报告标注为待确认项；performance_comparison 为空。

## 适用与失效边界

- 适用：vllm-ascend wzc 分支一带（qli/qsli 预计算元数据路径合入后）的 V4.1 PD 分离 + private pool + decode 压测；症状为 decode 节点 MqsmlaKernel AI Core 崩溃、与 prefix-cache/PD 导入强相关、qli/qsli 契约修复后仍复现。
- 失效边界：
  - 该风险假设只覆盖"预计算分支"；混合步 runtime 子批与 win 通道按实际计数，避免了此处上界与实际数脱钩；其他故障仍需检查。
  - 若部署未启用 qli/qsli 预计算（老算子接口），此路径不激活。
  - 报告同时列出残余嫌疑（若修复后仍复现）：`win_*`→`ori_*` ABI 改名与 ring 表寻址语义兼容性、SWA fa_metadata 预计算的旁路 stream/ExternalEvent 进图同步、折叠孪生数据面时序、int32 字节偏移 2GiB 类问题——排查时应保持这些分支开放。
  - checkpoint 的 candidate_topk_blocks / candidate_block_size / index_topk 数值未核对前，"gap 必现"是几何推断而非定论。
- 停止/回退条件：若崩溃步同一token/channel未发现上界大于实际数，则削弱本假设并继续核查同步、ABI与数据面。即使发现缺口，也需结合算子契约与控制变量对照确认因果，不能仅凭 eager 是否复现下结论。
