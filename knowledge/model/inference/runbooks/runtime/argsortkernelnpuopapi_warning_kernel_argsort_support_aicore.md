---
{
  "type": "Runbook",
  "title": "daVinci-MagiHuman distill 模式 ArgSort/linalg.solve float32 化零收益负结果：AiCpu 回退警告消除不等于性能收益",
  "description": "模型/框架：daVinci-MagiHuman（15B 单流 DiT 音频-视频生成，distill 蒸馏模式，8 步 denoise），cann-recipes-infer-bot_cjz 仓，Ascend NPU（完整型号未记录，原报告65GB HBM）单卡（ASCEND_RT_VISIBLE_DEVICES=13），conda davinci-magihuman。",
  "tags": [
    "task.testing",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# daVinci-MagiHuman distill 模式 ArgSort/linalg.solve float32 化零收益负结果：AiCpu 回退警告消除不等于性能收益
## 适用场景

- 平台证据边界：旧进度中的泛称Ascend910不足以区分产品，不沿用其Atlas A2括注。

- 模型/框架：daVinci-MagiHuman（15B 单流 DiT 音频-视频生成，distill 蒸馏模式，8 步 denoise），cann-recipes-infer-bot_cjz 仓，Ascend NPU（完整型号未记录，原报告65GB HBM）单卡（ASCEND_RT_VISIBLE_DEVICES=13），conda davinci-magihuman。
- 场景：distill 模式基线日志出现 `kernel [ArgSort] can not support dtype int32 or int64 on AiCore ... running on AiCpu ... please cast dtype to float32` 警告，据警告提示实施 ArgSort 输入 float32 cast 与 scheduler 两处 `torch.linalg.solve` float32 化，期望缩短 denoise 耗时。


## 触发与观测

- 触发（source 0 seq 50，基线运行日志逐字）：`[W625 09:47:22.262733452 ArgSortKernelNpuOpApi.cpp:26] Warning: Warning: kernel [ArgSort] can not support dtype int32 or int64 on AiCore, Now this kernel is running on AiCpu.If you are more concerned about high-performance execution,please cast dtype to float32.` 同次运行 denoise（8 步，Step3 Basic Resolution Evaluation）计时 `Time Elapsed: [0:00:06.901266]`。
- after（source 0 seq 132，修改后完整运行）：denoise `Time Elapsed: [0:00:06.934376]`；`grep -i "argsort" distill_optimized.log` 无输出（source 0 seq 136/137），即 ArgSort AiCpu 警告消失。

## 探针与操作

- 基线运行：`bash infer_distill.sh 2>&1 | tee distill_inference.log`（source 0 seq 49/50）。
- 定位：grep `argsort` 命中 `dit_module.py:107-108`；grep `linalg.solve` 命中 `scheduler_unipc.py:440/579`（source 0 seq 74/76）；`git diff` 两文件确认未改（source 0 seq 94/96）。
- 修改（source 0 seq 100/102/104，逐字见机制节）；修后运行同命令 `tee distill_optimized.log`（source 0 seq 131/132）。
- 验证警告消失：`grep -i "argsort" distill_optimized.log`（source 0 seq 136/137，无输出）。

## 机制与判别

- 结论 1（尝试完整实施且警告消除，但无性能收益）：三处修改落地后端到端重跑，denoise 6.901s → 6.934s（+0.5%，同 workload 同 metric 单次对比），ArgSort AiCpu 警告确实消失——修改达到了消除回退的目的，但没有转化为 denoise 提速。
- 结论 2（ArgSort 不在每步主路径，警告具有误导性）：`_precompute_permute_mapping` 仅在模块 `__init__` 阶段调用一次（source 0 seq 83，dit_module.py:104-114），不在 8 步 denoise 循环内；即使消除该算子的 AiCpu 回退，对每步耗时无影响。
- 结论 3（linalg.solve float32 化引入额外 cast 开销）：scheduler_unipc.py 两处 solve 每步执行，修改把 `R`/`b` 先 `.to(torch.float32)` 再 solve 再 `.to(x.dtype)`；小张量线性求解本非瓶颈，新增两次类型转换使收益趋于零/微负（本轨迹为单次运行，+33ms 在噪声量级，不下强结论）。
- 结论 4（过程风险记录）：第一次运行因编辑破坏 `else` 块缩进报 `IndentationError: expected an indented block after 'else' statement on line 439`（source 0 seq 115）后修复重跑——多行 else 分支内插入代码需整体保持缩进。

before/after 机制单元（source 0 seq 83/85/87 → 100/102/104，逐字）：

```python
# === dit_module.py _precompute_permute_mapping BEFORE ===
    def _precompute_permute_mapping(self, modality_mapping):
        # 1. Compute forward and inverse permutation mappings.
        # argsort is an efficient O(N log N) operation.
        self.permute_mapping = torch.argsort(modality_mapping)
        self.inv_permute_mapping = torch.argsort(self.permute_mapping)
# === AFTER ===
    def _precompute_permute_mapping(self, modality_mapping):
        # 1. Compute forward and inverse permutation mappings.
        # argsort is an efficient O(N log N) operation.
        # NPU optimization: cast to float32 for AiCore support
        modality_mapping_float = modality_mapping.to(torch.float32)
        self.permute_mapping = torch.argsort(modality_mapping_float).to(torch.int64)
        self.inv_permute_mapping = torch.argsort(self.permute_mapping.to(torch.float32)).to(torch.int64)

# === scheduler_unipc.py:440 BEFORE ===
                rhos_p = torch.linalg.solve(R[:-1, :-1], b[:-1]).to(device).to(x.dtype)  # type: ignore
# === AFTER ===
                # NPU optimization: convert to float32 for better compatibility
                R_float = R[:-1, :-1].to(torch.float32)
                b_float = b[:-1].to(torch.float32)
                rhos_p = torch.linalg.solve(R_float, b_float).to(device).to(x.dtype)  # type: ignore

# === scheduler_unipc.py:579 BEFORE ===
            rhos_c = torch.linalg.solve(R, b).to(device).to(x.dtype)
# === AFTER ===
            # NPU optimization: convert to float32 for better compatibility
            R_float = R.to(torch.float32)
            b_float = b.to(torch.float32)
            rhos_c = torch.linalg.solve(R_float, b_float).to(device).to(x.dtype)
```

## 验证信号

- 工具观测（tool_observed）：基线与修后两次完整运行日志（source 0 seq 50/132，tee 落盘）；`grep -E "Time Elapsed|Denoise"` 提取（source 0 seq 64）；`grep -i argsort` 修后日志无输出（source 0 seq 136/137）；`git diff` 确认修改前代码原状（source 0 seq 94/96）。
- 统计口径：denoise_wall_time 秒，两次均为单次运行、同 5s/448x256 输入、同 8 步 denoise、同卡同环境；无重复测量，差异 +0.033s 视为无收益（非显著劣化声明）。
- 输出产物存在性：两次运行均产出视频/音频（日志走完 Step8 Post Process）；本候选为性能负结果，画面质量未对拍。

## 适用与失效边界

- 适用：NPU 上照官方警告提示做 dtype cast 优化前的收益预判——先确认该算子是否在每步热路径；仅初始化调用一次的算子回退警告不构成优化机会。
- 边界：denoise 步数少的蒸馏模式（8 步）下小算子 cast 收益被稀释；结论不外推到 base 模式（32 步）或 ArgSort 位于循环内的其他代码路径；单次运行不区分 +33ms 是噪声还是开销。
- 停止/回退条件：若目标仅是消除 AiCpu 回退告警，本修改有效；若目标是 denoise 提速，应先 profiling 定位每步热点（本轨迹未做），而非从告警文案直接推导优化点。

## 附：断言存档

- distill 模式（8 步 denoise）下实施 ArgSort 输入 float32 cast（dit_module.py _precompute_permute_mapping）与 scheduler_unipc.py 两处 linalg.solve float32 化，ArgSort AiCpu 回退警告消失（grep 修后日志无 argsort 命中），但 denoise 耗时 6.901s→6.934s 无收益

```text
[rank0]:[W625 09:47:22.262733452 ArgSortKernelNpuOpApi.cpp:26] Warning: Warning: kernel [ArgSort] can not support dtype int32 or int64 on AiCore, Now this kernel is running on AiCpu.If you are more concerned about high-performance execution,please cast dtype to float32.
```
