---
{
  "type": "Runbook",
  "title": "sigtrace CULPRIT 与 NaN 定位边界：日志顺序、运行间差异与 logger 门控",
  "description": "sigtrace 的 first_introducer 会先记录任意字段的首次发散，并不专门标记 NaN。本例 CULPRIT 为 absmax 发散，另一个 kernel 随后才记录 NaN；默认 logger 又隐藏 PROPAGATED warning。应分别核对采集覆盖、运行间差异和每次调用，首个已记录 NaN 输出只是定位候选，不能独立证明真实引入点。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# sigtrace CULPRIT 与 NaN 定位边界：日志顺序、运行间差异与 logger 门控

## 适用场景

- 框架/平台：torch_npu 2.14 sigtrace（`torch_npu/_inductor/ascendc/common/sigtrace.py`，343 行，check 模式输出判读）；CANN 9.3.0~weekly.20260923.01（0923）；Ascend910_9362。
- 工作负载：torchtitan-npu deepseek_v4 8p 训练的 sigtrace golden/check 双跑定界（[torch_npu sigtrace golden/check 双跑定界引入 NaN 的 kernel（aten_lowering 白名单单变量）](../precision/torch_npu_sigtrace_golden_check_nan.md)）中，check run 完成但 CULPRIT 与预期 kernel 不符、或日志里 sigtrace 行缺失的场景。
- 适用问题：sigtrace 报的 CULPRIT/FIRST divergence 可不可信、如何从被吞掉的 warning 里找到NaN 定位候选、如何区分噪声发散与真发散。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 触发：check run `grad_norm=nan` 复现，但 sigtrace 报的 CULPRIT 是另一个 kernel 且发散字段是 absmax 而非 nan_count（日志原文）：

```
[rank0]:[2026-10-16 13:47:44] [RANK0] [ERROR] [sigtrace] FIRST DIVERGENCE INTRODUCER: kernel autofused__to_copy_add_copy_t_7b790f234f1b6d09fe37b22a1752c5f0 output 'add_tensor_6' diverges from golden while all 1 compared input(s) still match -> THIS kernel introduces the error. absmax 4.25513e-07 -> 0.00420189 (rel 9.87e+03)
[rank0]:[2026-10-16 14:18:48] [RANK0] [ERROR] [sigtrace] CULPRIT (first introducer): kernel autofused__to_copy_add_copy_t_7b790f234f1b6d09fe37b22a1752c5f0 output 'add_tensor_6': absmax 4.25513e-07 -> 0.00420189 (rel 9.87e+03)
[rank0]:[2026-10-16 14:18:48] [RANK0] [ERROR] [sigtrace] FIRST divergence in execution order: kernel autofused__to_copy_9b03ef6fd235b4db1837b7069532d5f2 input 'arg0_1' <- graph input / producer not traced: sum 17738.9 -> -4906.86 (rel 1.28)
```

且默认级别下日志只有这 3 条 ERROR（`total diverged signatures`、`wrote N signatures`、全部 PROPAGATED warning 均被 logger 吞掉）。

sigtrace 的 CULPRIT（first_introducer）按时间先到先得：一个 absmax-only 发散 kernel 抢先 2 秒占位（line 68634 的 `add_tensor_6`），首个已记录 NaN 输出所在 kernel晚到落入 PROPAGATED 的 warning 分支。

同配置两次 check run 之间只有 51.9%（294/566）的 key 在 rtol 2e-2/atol 1e-3 内一致（185 个仅 absmax 超差、83 个仅 sum/sumsq），`arg143_1`/`arg144_1` 的 run 间抖动 77%/88% 与相对 golden 偏差同量级——把它们判发散即把真源降级为 PROPAGATED。

在已采集覆盖内优先检查日志中第一条 nan_count 发散行（line 68795，kernel `autofused_..._d2a3593a...` output `mul_934`，nan_count 0 -> 21908056）：它之前 68794 行里 nan/inf 出现 0 次（740 条发散全是 absmax 464 / sum 270 / sumsq 4 / shape 1），且该 kernel 64 次 launch 全部产 NaN。

`record()` 用 `setdefault`（sigtrace.py:144），同 FX 名多次 launch 折叠成首次写入：json 里 `add_tensor_6` 的 absmax 是 4.51e-07，而 CULPRIT 日志报 0.00420189，差 4 个数量级——两者可能对应不同 launch 的记录；必须先对齐调用再判断矛盾。

TORCH_COMPILE_DEBUG=1 复跑得到 114,076 条 sigtrace 行（114,073 WARNING + 3 ERROR），原因类型分布 absmax 48660 / sum 28050 / shape 20862 / nan_count 16219 / sumsq 250 / inf_count 32；introducer 判据触发 92 次（1 FIRST + 91 ANOTHER）去重后 3 个 kernel（63× add_tensor_6/absmax、26× cat_63/shape、2× mul_11/absmax），nan_count 0 次。

## 探针与操作

- 复跑（保住 run1 产物后）：

```bash
cp -p golden.check.json golden.check.run1.json && mv ${LOCAL_PATH_1} ${LOCAL_PATH_2}
TORCH_COMPILE_DEBUG=1 TORCH_COMPILE_DEBUG_DIR=${LOCAL_PATH_3} INDUCTOR_PROVENANCE=0 \
  setsid nohup bash sigtrace_check_0923.sh > wrapper_check_run2.log 2>&1 < /dev/null & disown
```

  混杂变量控制：DEBUG=1 只为抬日志级别，会顺带把 `INDUCTOR_PROVENANCE` 提到 1（provenance 会写进生成代码），故显式 `INDUCTOR_PROVENANCE=0`，把复跑唯一变量收敛为"日志可见性"。
- 过滤归类（10 万+ 条不能平铺）：抽取脚本分层输出——summary 段 / 仅 ERROR / 每 FX 名首次发散 / 按原因类型与类别计数 / 目标 kernel 相关行。
- 噪声底标定：run1 与 run2 同配置（原始白名单），两份 `golden.check.json` 的差即经验噪声底：`jitter = |run1−run2| / max(|run1|,|run2|)`；按 jitter 分层（本例 324 个发散 FX 名：jitter<5% 强信号 70、jitter≥20% 大概率噪声 203、需人工判读 22、SHAPE 伪影 29）。

introducer 判据源码（时间先到先得 + 输入全匹配才能当 introducer）：

```
186:         introducer = (not self._cur_input_diverged) and self._cur_input_compared > 0
187:         if introducer and self.first_introducer is None:
188:             self.first_introducer = (self._cur_kernel, fx, reason)
```

record 折叠源码：

```
143:     def record(self, fx, sig):
144:         self.recorded.setdefault(fx, sig)
```

logger 门控源码：

```
13:     rank = os.getenv("RANK", "0")
14:     level = logging.DEBUG if os.getenv("TORCH_COMPILE_DEBUG", "0") == "1" else logging.ERROR
```

## 机制与判别

- 可区分解释分支（本例逐条验证）：
  1. "CULPRIT 就是 NaN 引入点" → 应有 nan/inf 计数发散；实测 CULPRIT 两侧 nan=0 inf=0、纯 absmax → 不采信。
  2. "NaN 候选被标记 PROPAGATED" → 它仅有的 2 个可比输入 `arg143_1`/`arg144_1` 数值发散（shape 相同、非伪影），`sigtrace.py:186` 要求 `_cur_input_diverged` 为空才判 introducer → 降级为 PROPAGATED（warning 级，默认被吞），所以默认日志里一条 `mul_934`/`d2a3593a` 都没有。
  3. "输入发散是真信号还是噪声" → 同配置双跑 jitter 标定：`mul_934` 的 nan 计数 run 间只差 0.6%（22030162 vs 21908056），而 `arg143_1`/`arg144_1` 的 absmax/sum 抖动与相对 golden 偏差同量级 → 输入差异可能含运行间波动，但单对运行不能证明无害噪声，也不能据此把当前 kernel 确认为真实 introducer；须补齐所有相关输入和调用上下文。
  4. "FIRST divergence 行可信吗" → `arg0_1` absmax 三次稳定 5.677/5.678、sum 从 +17738.9 翻到 −4906.86 再 +7158.66（jitter 168%，N=5.3e8 近零均值、抵消主导）→ sum 字段在该类张量上不可当判据，FIRST divergence 行不可采信。
- 判读纪律（从本例归纳）：NaN 定位优先检查 nan_count/inf_count 发散；有限数值差异也可能在下游触发 NaN，不能一律忽略；absmax/sum/sumsq 发散需噪声底标定后才可解读；json 值与日志值不一致时以带时间戳、可定位行号的日志行为准，并检查 setdefault 折叠；introducer 触发但字段是 absmax/shape 时按候选源处理而非结论。

## 验证信号

（单次复跑 + 离线 diff；CANN 0923 / Ascend910_9362 单机单卡）
- 复跑环境变量已在真实 python 进程 `/proc/<pid>/environ` 确认（`TORCH_COMPILE_DEBUG=1`、`INDUCTOR_PROVENANCE=0`、`TORCHINDUCTOR_ASCENDC_SIGTRACE=check:...`）。
- run2：rc=0、`grad_norm: nan` 复现、`aten_lowering.py` md5 还原、日志 37 MB / 114,076 条 sigtrace 行。
- summary 原文（复跑后）：CULPRIT 仍是 `add_tensor_6`（absmax 4.25513e-07 -> 0.00403023，rel 9.47e+03）——另一 run 仍先标记该 absmax 发散，说明 CULPRIT 并不专门表示首个已记录的 NaN 输出；这不能证明所有上游有限数值差异都无害。
- 噪声底：run1/run2 交集 566、容差内一致 294（51.9%）、nan 计数不同的 4 个 key 中 `mul_934` 22030162 → 21908056（0.6% 抖动）；`arg143_1` jitter 0.770、`arg144_1` 0.883、`arg0_1` 1.685。
- 首 NaN：line 68795（15:24:32）`kernel ...d2a3593a... output 'mul_934' diverges (PROPAGATED ...): nan_count 0 -> 21908056`；line 68795 之前 0 条 nan/inf 发散；`inf_count` 首次出现要到 line 91384（15:30:48，下游传播）；d2a3593a 共 192 条 sigtrace 行 = 64 次 launch × 3 行。
- 证据等级：以上均为原始日志/json 的客观行；jitter 数值只代表本例单对同配置 run，不是通用阈值。

## 适用与失效边界

- 适用：sigtrace check 输出的可信度判读；同配置双跑噪声底标定法（check-vs-check 或 golden-vs-golden 均可）。
- 失效/边界：
  - 噪声底需一对同配置 run（本例约 34 分钟/次）；没有噪声底时只能按发散字段类型分层（计数类 nan/inf > 结构类 shape > 数值类 absmax/sum/sumsq）。
  - `record()` 的 setdefault 保留首次记录，是该输出的聚合限制（本轨迹未修改）：离线 diff json 时同 FX 名只反映首次 launch。
  - 首条 nan_count 行法只回答“当前日志已采集覆盖内哪个 kernel 首先被记录为输出 NaN”，不回答 kernel 内部缺陷根因（另案）。
  - 若整份日志一条 nan/inf 发散都没有而 grad_norm 仍 nan，说明 NaN 产生在 sigtrace 未覆盖的路径（extern kernel 内部 / 未映射输入槽），或采集/映射存在遗漏；应回退到 eager_override / kernel dump 级工具。
  - 停止条件：定位到首条 nan_count 行并与离线 json diff 交叉核对后，可暂停继续向下追 PROPAGATED 链；仍需回查该调用全部输入、未映射路径和执行顺序，才能报告真实 NaN 引入点。
