---
{
  "type": "Runbook",
  "title": "DeepSeek-V3.2-Exp W4A8C8 16cp CI 样例 warmup prefill MoE dispatch OOM：max_prefill_tokens 65536→16384 修复",
  "description": "DeepSeek-V3.2-Exp W4A8C8 在单机 16 die Atlas A3（64GB/die）执行 CI 样例 rank_16_16ep_16cp_w4a8c8_mtp3_minibatch4 时，warmup prefill 的 MoE dispatch（aclnnCat 算子）处稳定 OOM（EL0004，16 rank 全部 core dumped）。根因是 YAML 默认 max_prefill_tokens=65536 与 input_truncated_len=16384 组合使每 rank 单次 prefill 并发 4 条 16K 序列（prefill_batch_size = 65536 // 16384 = 4）。仅将 max_prefill_tokens 下调为 16384 后，4 天 4 次独立运行全部通过（MTP3 等效时延 38.49/18.80/19.08/18.96 ms/token，单次观测）。该 CI 样例历史 5 次中 4 次 OOM，唯一成功日恰为生效值 16384。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.memory",
    "topic.speculative_decoding"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# DeepSeek-V3.2-Exp W4A8C8 16cp CI 样例 warmup prefill MoE dispatch OOM：max_prefill_tokens 65536→16384 修复

## 适用场景

- 模型/框架：DeepSeek-V3.2-Exp（W4A8C8 量化权重，${LOCAL_PATH_1}，146GB、71 个 safetensors 分片与 index 一致），cann-recipes-infer 仓（https://gitcode.com/cann/cann-recipes-infer.git，master 分支），统一推理入口 `bash executor/scripts/infer.sh --model deepseek_v3_2_exp --yaml ci/<yaml>`。
- 平台/版本：Atlas A3（Ascend 910_9362），单机 16 die（8 物理卡，A3 双 die，YAML 注释 `world_size = 2 * chip_num in A3`），单 die 64GB HBM；Docker 镜像 `cann9.0_pt2.8.0_dsv3.2_aarch_image:v0.1`（容器内 CANN 9.0.0、PyTorch 2.8.0+cpu、torch_npu、transformers 4.53.3、Python 3.11.12）；宿主机 CANN 9.2.0、驱动 HDK 26.0.rc1（README 要求 25.2.0，实测兼容）。
- 负载：CI 样例 `config/ci/deepseek_v3.2_exp_rank_16_16ep_16cp_w4a8c8_mtp3_minibatch4.yaml`：world_size=16、cp_size=16（仅 prefill 生效）、moe_ep_size=16、lmhead_tp_size=16、o_proj_tp_size=8、dense_tp_size=4、embed_tp_size=16、next_n=3（MTP3）、exe_mode="ge_graph"、enable_multi_streams=True、input_truncated_len=16384、batch_size=64、batch_size_per_dp_rank=4、max_prefill_tokens=65536、mem_fraction_static=0.85、cp_mini_batch=-1、block_size=128、max_new_tokens=256；数据集 InfiniteBench longbook_qa_eng.jsonl（351 条，拷贝至仓库根 `dataset/InfiniteBench/`）。
- 多来源：2026-10-14 至 2026-10-17 四天四次独立执行，结论一致。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

CI 样例原样执行时，权重加载完成（约 50s~4min）后进入 warmup/正式 prefill 的 MoE dispatch 阶段即 OOM，16 rank 全部 `Aborted (core dumped)`。2026-10-14 首次失败的设备侧报错（事件 144）：

```
[rank0]: [PID: 96738] 2026-10-14-00:58:54.392.377 Memory_Allocation_Failure(EL0004): Failed to allocate memory requested by APP module.
[rank0]:         Possible Cause: Available memory is insufficient.
[rank0]:         Solution: Close applications not in use.
```

同次日志还含 `torch.OutOfMemoryError: ... the current working operator name is aclnnCat.` 与 `ERR00006 PTA memory error / NPUWorkspaceAllocator.cpp:465`，异步栈指向 `modeling_deepseek.py:645 dispatch_double_routing → combine_tokens_cpu = combine_tokens.cpu().tolist()`（MoE 双路由 dispatch 路径）。2026-10-17 运行给出分配器视角（事件 155）：

```
[rank0]:[E1017 07:30:38.587516765 OpParamMaker.cpp:454] NPU out of memory. NPUWorkspaceAllocator tried to allocate 512.00 MiB(NPU 0; 61.27 GiB total capacity; 577.31 MiB free). If you want to reduce memory usage, take a try to set the environment variable TASK_QUEUE_ENABLE=1.
```

即 OOM 时单 die 61.27 GiB 可管理显存仅剩 577.31 MiB，512 MiB 的 aclnnCat 分配失败。设备端 plog 检查（2026-10-17 时段 252 个文件、2771 条 ERROR）无 ECC/硬件故障/device reset 类错误，全部 ERROR 可归因于 OOM 与异常退出的次生影响（HCCL 清理噪音、集合通信等待超时等）。

历史统计（2026-10-14 事件 148）：该用例 20261005/07/08/09 四次运行日志中 `OutOfMemoryError|Memory_Allocation_Failure` 计数均为 2（OOM），仅 20261006 成功（MTP3 41.76 ms）；对比成功/失败日志的 InferenceConfig（事件 170），唯一差异为 `max_prefill_tokens=16384`（20261006 成功）vs `65536`（失败），其余参数（input_truncated_len=16384、batch_size=64、batch_size_per_dp_rank=4、mem_fraction_static=0.85、num_reserved_decode_tokens=64、cp_mini_batch=-1、world_size=16、cp_size=16）完全一致。

## 探针与操作

1. 定位 OOM 阶段：日志显示 OOM 均发生在 `Warm-up [Main]: executing model prefill step...`（execution_engine.py:761）之后的 MoE dispatch，首个 65536-token prefill wave。
2. 配置对比探针（2026-10-14 事件 169/170）：`grep -m1 "InferenceConfig" <成功日志/失败日志> | tr ',' '\n' | grep -E "batch_size|mem_fraction|cp_mini|input_truncated|max_prefill|num_reserved|world_size|cp_size"`，锁定唯一差异 max_prefill_tokens。
3. 机制确认（2026-10-14 事件 180/181，`sed -n '725,745p' executor/core/engine/execution_engine.py`）：

```
        if self.infer_config.parallel_config.cp_size > 1 and self.infer_config.scheduler_config.cp_mini_batch >= 1:
            prefill_batch_size = self.infer_config.scheduler_config.cp_mini_batch
        else:
            prefill_batch_size = self.infer_config.scheduler_config.batch_size_per_dp_rank
        decode_batch_size = self.infer_config.scheduler_config.batch_size_per_dp_rank
        seq_len = self.input_truncated_len

        max_prefill_tokens = self.infer_config.scheduler_config.max_prefill_tokens
        if max_prefill_tokens > 0:
            seq_len = min(seq_len, max_prefill_tokens)
            prefill_batch_size = max(1, max_prefill_tokens // seq_len)
            if (
                self.infer_config.parallel_config.cp_size > 1
                and self.infer_config.scheduler_config.cp_mini_batch >= 1
            ):
                prefill_batch_size = min(
                    prefill_batch_size,
                    self.infer_config.scheduler_config.cp_mini_batch,
                )

        return prefill_batch_size, decode_batch_size, seq_len
```

4. 修复（临时副本 YAML，仅改一行，2026-10-15 事件 309/310 的 diff 逐字）：

```
33c33
<   max_prefill_tokens: 65536
---
>   max_prefill_tokens: 16384
```

   执行命令（2026-10-14 事件 213 参数原文）：`cd models/deepseek_v3_2_exp/config/ci && sed 's/max_prefill_tokens: 65536/max_prefill_tokens: 16384/' deepseek_v3.2_exp_rank_16_16ep_16cp_w4a8c8_mtp3_minibatch4.yaml > neg_tmp_oom_mitigation.yaml`（10-15/16/17 为同型 sed，副本命名 tmp_oom_mitigation_16cp_mtp3.yaml / tmp_oom_mftp16k.yaml，跑通后均删除，原始 CI YAML 未改动）。
5. 失败路线（不可采用）：同日先按 OOM 缓解顺序试"减 batch_size"（64→32），仍 OOM——详见[减 batch_size（64→32）不能缓解 DeepSeek-V3.2-Exp 16cp CI 样例的 warmup prefill OOM](batch_size_deepseek_v32_exp_warmup.md)，此处明确标注该路线对本 OOM 无效。

## 机制与判别

- 结论 1：CI 样例 deepseek_v3.2_exp_rank_16_16ep_16cp_w4a8c8_mtp3_minibatch4.yaml 自创建起默认 max_prefill_tokens=65536，与 input_truncated_len=16384 组合使每 rank 单次 warmup prefill 并发 4 条 16K 序列（prefill_batch_size = 65536 // 16384 = 4），在单机 16 die Atlas A3 64GB HBM、W4A8C8 权重、CP16+EP16+MTP3 配置下于 MoE dispatch（aclnnCat 算子内存分配失败，EL0004）处稳定 OOM，16 rank 全部 core dumped。
- 结论 2：仅将 max_prefill_tokens 由 65536 下调为 16384（其余参数不变），同一用例在 4 天 4 次独立运行中全部通过：MTP3 等效时延分别为 38.49（2026-10-14）、18.80（2026-10-15）、19.08（2026-10-16）、18.96（2026-10-17）ms/token，均无 Aborted、全 rank 无 ERROR，每请求 257 有效 token（各为单次运行观测值，跨日波动未做多轮统计）。
- 结论 3：该 16cp CI 样例在本机历史执行 5 次中 OOM 复现 4 次（20261005/07/08/09），唯一成功的 20261006 当时生效的 max_prefill_tokens=16384（prefill 单批降为 1 条序列），YAML 本身自创建（commit db40505）以来一直是 65536。
- 机制：上引 execution_engine.py 代码中 prefill 批大小 `prefill_batch_size = max(1, max_prefill_tokens // seq_len)`（seq_len 为 input_truncated_len 被 max_prefill_tokens 截断后的值），不依赖 batch_size；仅当 cp_size>1 且 cp_mini_batch>=1 时才被 cp_mini_batch 钳制（本例 cp_mini_batch=-1 不钳制）。65536//16384=4 → 单 wave 4 条 16K 序列的 MoE dispatch 激活；16384 时为 1×16K，wave 缩小 4 倍后可跑通。
- 可区分解释与未验证点：20261006 的生效值 16384 来源（代码层 clamp 或当时环境差异）未进一步追查；OOM 报错本身不指向 max_prefill_tokens（仅提示"Close applications not in use"），需靠配置对比定位。下发 YAML 原文（自创建未变，事件 174）：

```
+scheduler_config:
+  block_size: 128
+  max_new_tokens: 256
+  batch_size: 64
+  max_prefill_tokens: 65536
```

## 验证信号

- 2026-10-14 缓解运行（事件 216/217）：EXIT_CODE=0、Aborted 计数 0、16 rank 无 ERROR，日志逐字：

```
[INFO][2026-10-14 01:54:34.965][infer.py:129] deepseek_v3_2_exp model average equivalent latency of MTP3 is 38.49 ms
[INFO][2026-10-14 01:54:34.965][infer.py:133] The speculation accept rate: 1.0000
```

- 2026-10-15（事件 312/313）：4 请求 × 257 有效 token（共 1028），MTP3 等效 18.80 ms/token；2026-10-16（事件 162/163）：19.08 ms/token；2026-10-17（事件 169/170）：18.96 ms/token，prefill 正式阶段 64 个 multi-cycle、平均 2701.43 ms/cycle（2026-10-15 观测）。
- 对照组：1cp+MTP1 样例（rank_16_16ep_1cp_w4a8c8.yaml，max_prefill_tokens=4096、input_truncated_len=4096）四天均直接通过（MTP1 等效 40.84/22.66/23.41/22.93 ms/token），说明显存问题特定于 16cp 样例的 65536-token wave 而非环境。
- 证据等级：同会话（同机、同镜像、同权重、同数据集）可比观测；性能数字均为单次运行，未做多轮统计与置信区间；缓解后与 1cp 样例的时延对比混杂了并行策略/MTP/输入长度差异，不作通用加速结论。缓解后运行的空输出问题见[DeepSeek-V3.2-Exp W4A8C8 空输出诊断：生成 token 全为特殊 token，输入侧与 tokenizer 已排除（根因未闭合）](../precision/deepseek_v32_exp_w4a8c8_token.md)（不影响本条 OOM 修复结论）。

## 适用与失效边界

- 适用：DeepSeek-V3.2-Exp W4A8C8、单机 16 die（64GB/die）A3、ge_graph、CP16+EP16+MTP3、input_truncated_len=16384 的 warmup prefill MoE dispatch OOM（aclnnCat/EL0004）。
- 失效/未知：更大显存或多机环境（≥32 die）下 65536 是否可行未验证；cp_mini_batch>=1 的配置会另行钳制 prefill 批大小；mem_fraction_static、num_reserved_decode_tokens、enable_prefill_multi_cycle、moe_chunk_max_len、kvp_size 未做单独扫描；下调 max_prefill_tokens 将 prefill 拆为多个 cycle（观测到 64 cycles），对端到端吞吐的影响未量化。
- 停止/回退条件：若 16384 仍 OOM，按缓解顺序继续尝试 enable_prefill_multi_cycle、moe_chunk_max_len、kvp_size 或更高压缩量化；修复验证通过后建议向仓库反馈 CI 样例默认值与 16 die 环境显存不匹配（四份报告均建议下调默认值或在 README/YAML 注释标注显存前提）。
