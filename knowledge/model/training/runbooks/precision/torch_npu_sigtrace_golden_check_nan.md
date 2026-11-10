---
{
  "type": "Runbook",
  "title": "torch_npu sigtrace golden/check 双跑定界引入 NaN 的 kernel（aten_lowering 白名单单变量）",
  "description": "CANN 0923 的 torchtitan-npu 双跑中，摘掉 aten.sigmoid 白名单的 golden 梯度有限，原白名单 check 的 mul_934 出现 NaN；可按 FX 名找到其 producer。sum_30 两侧签名均有限，sigmoid_1 仅 check 侧有限、golden 签名缺失，不能称为双侧通过。需使用新缓存并核对 logger、FX 名和采集覆盖，缺失签名不得按 nan=0 处理。",
  "tags": [
    "task.implementation",
    "topic.precision",
    "task.testing"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "910"
  ]
}
---

# torch_npu sigtrace golden/check 双跑定界引入 NaN 的 kernel（aten_lowering 白名单单变量）

## 适用场景

- 框架/平台：torch_npu 2.14.0+gita916959（commit a9169594）+ torch 2.14.0+cpu（git 08187d9e）+ Python 3.11.16（conda torch-npu-build-2.14-py311）；CANN 9.3.0~weekly.20260923.01（0923，innerversion V100R001C12B126）；SoC Ascend910_9362（1 板 2 chip），npu-smi 25.5.5，aarch64。
- 工作负载：torchtitan-npu deepseek_v4 flash 8p 训练（`examples/deepseek_v4/debug/deepseek_v4_flash_8p_cpt_4k_a3_graphtrainer.sh`，worktree HEAD f11db1e，`--compile.inductor_compilation full`），整网 step 1 `grad_norm=nan` 的精度定界。
- 目标：当两次 run 的融合配置不同（kernel 划分/md5 不同）、无法逐 kernel 对比时，用 torch_npu 内置 sigtrace 按 **FX 节点名**（fusion-invariant）对齐两次 run 的 kernel I/O 张量签名（shape/dtype/nan/inf/absmax/sum/sumsq，几十字节指纹、每张量一次 `.cpu()`），定界引入 NaN 的 kernel。
- 缺失信息：每次 run 约 34 分钟（单次运行）；签名条数实测 569/566，未达 GUIDE 所说"几千量级"，但足够完成本例定界。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_4}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_5}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_6}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_7}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${TORCHTITAN_ROOT}` 为torchtitan-npu 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 触发：CANN 0923 整网训练 step 1 即 `grad_norm=nan`，需要独立复现"NaN 引入点在哪个 kernel"的定界结论。
- 客观输出（单次双跑）：
  - golden：`[titan] ... step:  1  loss: 12.34433  grad_norm: 31.3270`，rc=0；`aten_lowering.py` md5 变为 `d1e1fe62...`，`grep -n '# [sigtrace-golden] '` 命中 `100:# [sigtrace-golden] _LoweringGuard.support(aten.sigmoid, float_dtypes())`。
  - check：`[titan] ... step:  1  loss: 12.14439  grad_norm:     nan`，rc=0；`aten_lowering.py` 已还原 md5 `80aed59ab7b149703436d038d3ac7701`。
  - 签名对比（离线读 `golden.json` / `golden.check.json`，事件 246）：`mul_934` golden 侧 `nan: 0, absmax: 1.565102714096156e-08`，check 侧 `nan: 22030162, inf: 0`；`sum_30` 两侧均 nan=0、inf=0；`sigmoid_1` 的 golden 为 `None`，只有 check 侧观测到 nan=0、inf=0。

在同一套 CANN 0923 上两次只差 `aten_lowering.py:100` 一行注释（`_LoweringGuard.support(aten.sigmoid, float_dtypes())`）的 torchtitan 训练：golden grad_norm=31.3270 有限，check grad_norm=nan。

`mul_934`（shape (1,4096,4,4096) fp32）在 golden 侧 nan=0，在 check 侧 nan=22,030,162 / 67,108,864（32.83%）；check 同 kernel 的 `sum_30`/`sigmoid_1` 均有限。check producer 为 `autofused__to_copy_add_expand_matmul_mean_mul_pow_rsqrt_sigmoid_sum_unsqueeze_view_d2a3593a787c14c7dcd5b4a928674723`，golden 同名 `mul_934` 由 `..._bea037b00...` 产出。`sigmoid_1` 没有 golden 签名，不能把它列为跨运行比较通过的节点。

## 探针与操作

两次 run 串行、各占一张卡（chip 0）；脚本全自动备份/打补丁/还原 `aten_lowering.py`（原始 md5 `80aed59ab7b149703436d038d3ac7701`）。RUNG 阶梯（golden 不合格时逐级加摘）：

```
38: LADDER = [
39:     ["_LoweringGuard.support(aten.sigmoid, float_dtypes())"],
40:     ["_LoweringGuard.support(aten.sigmoid, float_dtypes())",
41:      "_LoweringGuard.support(aten.rsqrt, float_dtypes())"],
42:     ["_LoweringGuard.support(aten.sigmoid, float_dtypes())",
43:      "_LoweringGuard.support(aten.rsqrt, float_dtypes())",
44:      "_LoweringGuard.support(aten.mean, float_dtypes())"],
45: ]
```

golden 侧实验变量（check 侧只差白名单与缓存目录，`TORCHINDUCTOR_ASCENDC_SIGTRACE="check:$GOLDEN"` 读同一份 golden.json）：

```
106: # ---- 4. 实验变量 ----
107: export ASCEND_SET_ENV_PATH=${LOCAL_PATH_1}   # 两次 run 都是 0923
108: export TORCHINDUCTOR_CACHE_DIR=${LOCAL_PATH_2}                     # 必须全新，见 GUIDE 前置条件 1
109: export TORCH_EXTENSIONS_DIR=${LOCAL_PATH_3}
110: export TORCHINDUCTOR_ASCENDC_DEBUG=noloadtrans
111: export TORCHINDUCTOR_ASCENDC_SIGTRACE="golden:$WORK/golden.json"
```

```
73: # ---- 3. 实验变量：与 golden 只差 aten_lowering.py 和缓存目录 ----
74: export ASCEND_SET_ENV_PATH=${LOCAL_PATH_1}   # 与 golden 同一套 CANN
75: export TORCHINDUCTOR_CACHE_DIR=${LOCAL_PATH_4}                      # 必须全新，见 GUIDE 前置条件 1
76: export TORCH_EXTENSIONS_DIR=${LOCAL_PATH_5}
77: export TORCHINDUCTOR_ASCENDC_DEBUG=noloadtrans                        # 必须与 golden 一致
78: export TORCHINDUCTOR_ASCENDC_SIGTRACE="check:$GOLDEN"
```

启动（后台、脱离进程组）：

```bash
cd ${TORCHTITAN_ROOT}/benchmark_check
setsid nohup bash sigtrace_golden_0923.sh > ${LOCAL_PATH_6} 2>&1 < /dev/null & disown
# golden 合格后再跑：
setsid nohup bash sigtrace_check_0923.sh  > ${LOCAL_PATH_7} 2>&1 < /dev/null & disown
```

golden 合格三条判定（本例全过，未加码 RUNG）：(a) grad_norm 有限且 31.4 量级（偏差 0.23%）；(b) 签名条数非 0（实测 569，全新缓存里生成 245 个 `eager_override.json`）；(c) `mul_934 in_golden=True`、`sigmoid_1` 缺失符合 RUNG≥1 预期。

check 判读纪律：nan/inf 计数精确比较，absmax/sum/sumsq 用 rtol 2e-2/atol 1e-3（可用 `TORCHINDUCTOR_ASCENDC_SIGTRACE_RTOL/ATOL` 覆盖）；`_cur_input_compared` 本例实际是 2（`arg143_1`/`arg144_1`，3 个 `buf*` 因重编号不在 golden）。离线核对：`golden.check.json` 与 `golden.json` 做 key 交集 + 分层 diff（本例 449 交集中 33 个 shape/dtype 伪影、55 个 nan 0→N、233 个仅软字段发散）。

缺失项单独标记为未采集/不可比较，不用 0 填充 nan/inf 计数。事件 270 中 golden 的 `sigmoid_1 -> []` 表示扫描的融合 meta 中没有该 producer 映射，不表示所有执行路径都已验证该值有限；这与 golden 摘掉 sigmoid lowering 后的采集范围有关。

sigtrace 的 warning 级输出默认被 `inductor_asc` logger 的 ERROR 级别吞掉（`ascendc/common/__init__.py:14`），日志一条 `[sigtrace]` 都没有但 golden.json 照常写出 569 条；设 `TORCH_COMPILE_DEBUG=1` 重跑后 114,076 条 sigtrace 行全部可见。

logger 门控源码（sigtrace 的 14 处输出里 8 处是 warning，包括 summary、total diverged、wrote N signatures、PROPAGATED 链）：

```
13:     rank = os.getenv("RANK", "0")
14:     level = logging.DEBUG if os.getenv("TORCH_COMPILE_DEBUG", "0") == "1" else logging.ERROR
```

运行前置与坑：`TORCHINDUCTOR_CACHE_DIR` 必须全新（复用旧缓存时 `eager_override.json` 不生成、一条签名都没有且不报错）；首次 nohup 后台任务被 shell 超时连带杀掉，改用 `setsid` 脱离进程组后正常；`tee`/torchelastic 日志均被块缓冲，判活要用进程 CPU 时间增量 + `npu-smi`。

## 机制与判别

- FX 名对齐是本方法核心：golden 与 check 的 kernel md5/划分不同（`..._bea037b00...` vs `..._d2a3593a78...`），但 `mul_934`/`sum_30` 等 aten FX 名稳定，因此能对齐；`buf*` 名随融合结构重编号，449 个交集 key 中 33 个出现 shape/dtype 伪影，属已知噪声而非真发散。
- 仅当两侧都有对应且 shape/dtype 可比的签名时，才能做双侧比较；check 侧单独有限与 golden 缺失是不同状态。本例不能用 `sigmoid_1` 的缺失补出一条“golden/check 均通过”的证据链。
- 引入 NaN 的结构由白名单决定：`aten.sigmoid` 摘掉后 sigmoid 落成 extern fallback，结果必须落 GM，两个消费者都只能读它，整条 `mean→truediv→add→rsqrt→mul→…→sigmoid` 链只算一次；原始白名单下同一份计算在一个 kernel 里出现两次，触发 CANN 0923 图融合 pass 的事务缺陷（拒绝后移且不回滚 → 图半改写 → tiling 错配 → 读到从未被写的片上内存 → NaN，位模式 `0x7fffffff`；该层缺陷 1009 已修，不在本方法范围内）。
- 与 `benchmark.py --check` 的区别：--check 把 eager_fn 片段重交给 torch.compile，图输出身份变化导致重编 kernel 与整网不同构（见[inductor 图输出身份决定 realize 时机：`sigmoid_1` 不在 return 里时 RMSNorm 链算两份（--check 结构性假阴性根因）](../compilation/inductor_realize_sigmoid_1_return_rmsnorm.md)）；sigtrace 双跑保持整网上下文不变，只改白名单这一个变量。
- 未验证/未穷尽：golden 签名只覆盖 569 个 FX 名（wrapper 6 入而 meta 只列 5 个，`in_ptr5` 未被签）；本次仅 RUNG=1，阶梯加码未执行。

## 验证信号

（单次双跑 + 离线 json diff；CANN 0923 / Ascend910_9362 单机单卡，证据等级：原始日志与 json 产物）
- golden：`grad_norm: 31.3270`、`elapsed_time_per_step: 2029.037s`、rc=0；`golden.json` 569 条、`mul_934 in_golden=True`。
- check：`grad_norm: nan`、rc=0；`mul_934` nan=22,030,162（32.83%）、`sum_30`/`sigmoid_1` nan=0。事件 246 中 golden 的 `sum_30` nan=0，但 `sigmoid_1` 为 `None`，后者没有双侧有限的验证结论。
- kernel 对齐：扫 245/243 个 `eager_override.json` 得 check 侧 `mul_934` producer = `autofused__to_copy_add_expand_matmul_mean_mul_pow_rsqrt_sigmoid_sum_unsqueeze_view_d2a3593a787c14c7dcd5b4a928674723`，golden 侧 = `autofused__to_copy_add_expand_mul_sum_unsqueeze_view_bea037b00ef6d5dac103a64619f3f6cf`；与既有独立定界（kernel 名 + 输出 FX 名 `mul_934`）逐项一致。
- logger 门控：默认级别下日志 0 条 `[sigtrace]`（json 照常写出）→ `TORCH_COMPILE_DEBUG=1` 复跑后 114,076 条全部可见。
- 收尾：`aten_lowering.py` 还原 md5=`80aed59ab7b149703436d038d3ac7701`、补丁标记 0 处、无残留进程、worktree 保持既有 3 个文件改动未碰。
- 单次观测说明：NaN 比例本身非确定（本例 32.83%；同日观测过 23.15%/31.28%/8.91%），定界结论应表述为"kernel 名 + FX 名"，不写固定百分比。

## 适用与失效边界

- 适用：改融合相关配置（aten_lowering 白名单、graph-autofusion 参数）导致两次 run kernel 划分不同、且怀疑特定配置引入 NaN/Inf 的整网训练定界。
- 失效/边界：
  - golden 缺失的 FX 名不参与双侧通过判定；若定位结论依赖该节点，须补齐对应执行路径的采集证据。
  - 只定位不解释：kernel 内部为何产生 NaN 属另一层（本例 CANN 图融合 pass 缺陷，1009 已修）。
  - CULPRIT 自动判读不可靠（见[sigtrace CULPRIT 误报判读：首条 nan_count 行、同配置噪声底与 logger 门控](../validations/sigtrace_culprit_nan_count_logger.md)），必须人工看首条 nan_count 行 + 离线 diff。
  - 旧缓存会让签名静默缺失（不生成 `eager_override.json`、不报错）；污染后必须删除缓存目录重跑。
  - 不开 `TORCH_COMPILE_DEBUG=1` 时 sigtrace warning 全部不可见，只有 3 条 ERROR；但 DEBUG=1 会顺带把 `INDUCTOR_PROVENANCE` 提到 1，需显式 `INDUCTOR_PROVENANCE=0` 把复跑的唯一变量收敛为日志可见性（本例复跑即如此处理）。
  - 不要显式设 `TORCHINDUCTOR_ASCENDC_TRACED_GRAPH=0`（显式 0 优先，会退回启发式片段抽取）；设了 `SIGTRACE` 会自动隐含 `traced_graph=True`。
  - 训练脚本带 `--debug.deterministic` 时不可比，跑前须确认未开。
