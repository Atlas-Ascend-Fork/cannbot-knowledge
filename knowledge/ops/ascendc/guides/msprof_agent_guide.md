---
type: Guide
title: "msprof Agent 使用指南"
description: "让 Agent 用 msprof 做性能分析而不撑爆 context 的指南：先用系统级 msprof 定位瓶颈，落到单算子再用算子级 msopprof（等同 msprof op）展开；核心是分层读取——优先只读 op_statistic 聚合 csv，再按需 grep op_summary 取关键指标，避免读二进制 trace。"
tags: [task.optimization, topic.performance.analysis]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/reference/porter/toolchain/msprof_agent_guide.md
    role: primary
created_at: "2026-08-05T14:23:52Z"
updated_at: "2026-10-21T04:09:57Z"
platforms: ["950"]
---
# msprof Agent 使用指南

> 如何让 AI Agent 高效使用 msprof 进行性能分析，避免撑爆 context。
> 本文档持续更新。

---

## 0. msprof vs msopprof：选哪个工具（系统级 vs 算子级）

> Owner 2026-06-24 澄清；main 对照官方 CANN/MindStudio/Huawei 文档核实（msprof=系统级 / msopprof=算子级）。两者对象不同、功能略有重叠：

- **`msprof` = 系统级 profiling（最常用）** —— 查看整个执行的系统级时间线/瓶颈（host-device 调度、算子间隙、内存搬运、AI Core 全局利用率）。**默认先用它**找系统级瓶颈。
- **`msopprof` = 算子（operator）级 profiling** —— 对单个算子内部展开指令/pipe 级细节。`msopprof` 是 CANN 包里的可执行文件、接口用法与 **`msprof op`** 一致（同一算子级能力的两种调用名）。
- **工作流**：先 `msprof` 找系统级瓶颈 → **若瓶颈定位到某个算子**、再用 `msopprof` 对那个单算子展开看内部。
- 本指南下文的 context-安全分层读取策略主要针对 `msprof` 系统级输出；`msopprof` 单算子展开同理（只读聚合 csv、不读二进制 trace）。

---

## 1. 核心问题

msprof 原始输出可达 **数 GB**（二进制 trace 数据），但 agent context 窗口有限（~200K tokens 有效空间）。
直接读取原始数据不可行，必须有过滤策略。

## 2. msprof 输出结构

```
/tmp/msprof_out/
└── PROF_000001_xxxxxx/
    ├── device_0/data/          # 二进制 trace（数十 MB~数 GB）← NEVER READ
    │   ├── stars_soc_profile.data.0.slice_*
    │   └── ffts_profile.data.0.slice_*
    ├── device_0/sample.json    # 小 JSON，设备信息
    └── mindstudio_profiler_output/  # ← AGENT 只读这个目录
        ├── op_statistic_*.csv  # 聚合统计（2-5 行）← 首选
        ├── op_summary_*.csv    # 逐 task 详情（可达数千行）← grep 过滤
        ├── task_time_*.csv     # timeline（数千行）← 通常不需要
        └── api_statistic_*.csv # ACL API 统计（十几行）
```

## 3. Agent 分层读取策略

### Level 1: `op_statistic_*.csv`（首选，< 10 行）

**格式**: `OP Type, Core Type, Count, Total Time(us), Min/Avg/Max Time(us), Ratio(%)`

**用途**: 快速判断哪个 kernel 是瓶颈（按 Ratio% 排序）。

```bash
# Agent 命令：只读聚合统计
cat PROF_*/mindstudio_profiler_output/op_statistic_*.csv
```

**示例输出（2 行）**:
```
pooling_backward_kernel,AI_VECTOR_CORE,793,1291324us,5.8us,1628us,65302us,86.9%
pooling_forward_kernel,AI_VECTOR_CORE,793,194107us,7.5us,244us,10309us,13.1%
```
→ 一眼看出 backward 占 87% 时间。

### Level 2: `op_summary_*.csv` + grep/awk（按需，< 50 行）

**格式**: 逐 task，包含 `aiv_vec_ratio`, `aiv_scalar_ratio`, `aiv_mte2_ratio` 等关键指标。

**关键列**（按列号，从 0 开始）:
| 列 | 字段 | 含义 |
|----|------|------|
| 4 | Op Name | kernel 名 |
| 9 | Task Duration(us) | 执行时间 |
| 37 | aiv_vec_ratio | vector pipe 利用率（0~1.0） |
| 39 | aiv_scalar_ratio | scalar pipe 利用率 |
| 41 | aiv_mte2_ratio | DMA pipe 利用率 |

```bash
# Agent 命令：只提取特定 kernel 的关键指标
# 取 backward kernel 的 top-5 最慢 task
grep "backward" PROF_*/mindstudio_profiler_output/op_summary_*.csv | \
  awk -F',' '{print $10, $38, $40, $42}' | sort -rn | head -5
```

```bash
# Agent 命令：取所有 kernel 的平均 vec_ratio 和 scalar_ratio
grep -v "^Device" PROF_*/mindstudio_profiler_output/op_summary_*.csv | \
  awk -F',' '{
    name=$5; dur=$10; vec=$38; scl=$40; mte=$42;
    sum[name]+=dur; cnt[name]++; svec[name]+=vec; sscl[name]+=scl; smte[name]+=mte
  } END {
    for(n in sum) printf "%s: avg_dur=%.1fus vec=%.3f scl=%.3f mte=%.3f (n=%d)\n",
      n, sum[n]/cnt[n], svec[n]/cnt[n], sscl[n]/cnt[n], smte[n]/cnt[n], cnt[n]
  }'
```

### Level 3: `task_time_*.csv`（按需，需要 `--task-time=l2`）

Timeline 数据。文件可达数千行但单个 CSV（非二进制，可用 grep/awk 处理）。

**用途**: 分析 kernel 间 gap、stream 并发、逐 task 精确 timing。
**大小**: 通常 50K-100K（数百~千行 CSV），agent 可安全读取 header + wc -l。

```bash
# 只看行数和 header（不读全部内容）
head -1 PROF_*/mindstudio_profiler_output/task_time_*.csv
wc -l PROF_*/mindstudio_profiler_output/task_time_*.csv
```

**注意**: 需要 `--task-time=l2` 参数才会生成详细数据。默认 `--task-time=on` 只有 l0/l1 粒度。

### Level 4: `device_0/data/*`

二进制 trace 文件，数十 MB~数 GB。只能用 MindStudio GUI 或 msprof CLI 解析。**Agent 绝不直接读取。**

## 4. 不同 metrics group 的使用

msprof 的 `--aiv-metrics` 参数控制采集内容，不同 group 不能同时采集：

| Group | 关键指标 | 用途 |
|-------|---------|------|
| **PipeUtilization**（默认） | `aiv_vec_ratio`, `aiv_scalar_ratio`, `aiv_mte2_ratio`, `aiv_mte3_ratio` | **首选**：判断瓶颈在计算、标量、DMA 读还是 DMA 写 |
| Memory | HBM 带宽利用率 | 判断是否带宽瓶颈 |
| **L2Cache** | L2 读/写命中率、miss 率、eviction 计数 | **判断 L2 缓存效果**（Batch 14 验证有效） |
| **MemoryUB** | UB 读写带宽 | 判断 UB 利用率 |
| ArithmeticUtilization | MAC 利用率 | 矩阵运算密集型 kernel |
| ResourceConflictRatio | 资源冲突 | 排查 bank conflict |

**推荐流程**:
1. 先用默认 PipeUtilization 跑一次
2. 如果 vec_ratio ≈ 1.0 且性能仍差 → 将 Vector 相关工作列为候选；按问题选择 Memory 或指令级证据，不能由该 ratio 宣称已无优化空间
3. 如果 scalar_ratio 高 → 检查控制路径、寻址与相关等待；不能仅由 ratio 归因 GetValue 或某条指令
4. 如果 mte3_ratio 高 → 检查实际写路径及重叠；只有另有源码/指令或对照证据时才归因 atomicAdd，不能直接迁移历史案例结论
5. **如果需要区分"读缓存 vs 写缓存"** → 跑 L2Cache（Batch 14-6 关键手段）

**L2Cache metrics 提取**（Batch 14-6 验证的方法）:
```bash
# 找 L2 相关列名
head -1 op_summary_*.csv | tr ',' '\n' | cat -n | grep -i 'l2\|cache'

# 提取每个 kernel 的 L2 命中率（列号需根据实际 header 调整）
grep -v '^Device' op_summary_*.csv | awk -F',' '{
  name=$5; l2_rd_hit=$XX; l2_wr_hit=$YY; l2_wr_miss=$ZZ;
  ...
}'
```

**op_summary 列号对照（PipeUtilization metrics）**:
| 列号（1-based） | 字段 | 说明 |
|----------------|------|------|
| 5 | Op Name | kernel 名 |
| 10 | Task Duration(us) | 执行时间 |
| 37 | aiv_time(us) | AIV 总时间 |
| 39 | aiv_vec_time(us) | VEC 时间 |
| **40** | **aiv_vec_ratio** | VEC 利用率 |
| 41 | aiv_scalar_time(us) | 标量时间 |
| **42** | **aiv_scalar_ratio** | 标量利用率 |
| 43 | aiv_mte2_time(us) | MTE2 读时间 |
| **44** | **aiv_mte2_ratio** | MTE2 读利用率 |
| 45 | aiv_mte3_time(us) | MTE3 写时间 |
| **46** | **aiv_mte3_ratio** | MTE3 写利用率 |

## 5. Agent 完整 workflow

```
Step 1: 采集
  msprof --output=/tmp/msprof_X -- ./benchmark_command

Step 2: 快速定位瓶颈（< 10 行输出）
  cat PROF_*/mindstudio_profiler_output/op_statistic_*.csv

Step 3: 深入分析（grep 过滤后 < 50 行）
  grep "kernel_name" op_summary_*.csv | awk 提取 vec/scalar/mte ratio

Step 4: 判断 → 实施优化 → 重新 profile
```

## 6. msprof 运行命令模板

```bash
# 基础采集（默认 PipeUtilization）
MSPROF=/usr/local/Ascend/cann-9.0.T501/tools/profiler/bin/msprof
export LD_LIBRARY_PATH=/usr/local/Ascend/cann-9.0.T501/x86_64-linux/lib64:$LD_LIBRARY_PATH
$MSPROF --output=/tmp/msprof_out -- ./benchmark_command

# 指定 metrics group
$MSPROF --output=/tmp/msprof_mem --aiv-metrics=Memory -- ./benchmark_command

# 导出为 CSV（如果默认未生成）
$MSPROF --export=on --output=/tmp/msprof_out --type=text --summary-format=csv
```

## 7. 已知限制（A5 容器环境）

- msprof 在 `can_torch_cann_device_1` 容器内可能报 "Running profiling failed. Please check the driver package"
  - 原因：容器权限不足或 driver 版本不匹配
  - Workaround：之前的 session 成功跑过（可能需要重启容器或检查 driver 挂载）
- msprof 的 `--analyze` 和 `--parse` 模式需要 Python 3.7.5+

## 8. 使用 aog-researcher agent 做深度分析

**推荐对复杂优化问题使用 aog-researcher agent**:

当需要跑多轮 msprof（不同 metrics group）并交叉分析时，交给 researcher agent 可以：
1. 保护主 agent 的 context 不被 profiling 数据污染
2. Researcher agent 可以连续跑 3-4 轮 msprof 并综合分析
3. 返回结构化的诊断报告和假设建议

**Batch 14-6 验证的深度分析 workflow**:
```
Step 1: PipeUtilization 跑基线 kernel + 待优化 kernel
Step 2: L2Cache 跑待优化 kernel（看缓存命中）
Step 3: 对比两个 kernel 的 4 管线利用率差异
Step 4: 提取 L2 读/写 hit/miss 数据
Step 5: 综合诊断 → 输出结构化假设

关键发现模板:
  "Kernel X 的 mte3_ratio=0.88，先检查当前源码是否真的使用原子写。
   结合 L2 写 miss 与 Kernel Y 的指标提出可证伪假设；
   若没有指令/受控对照，不把相关性写成 thrashing 或唯一根因。
   速度差另由相同未插桩 consumer 测量，不由 ratio 推算。"
```

## 9. msprof 运行命令模板（更新 2026-04-02）

```bash
# 基础采集（PipeUtilization — 首选）
MSPROF=/usr/local/Ascend/cann-9.0.0/tools/profiler/bin/msprof
export LD_LIBRARY_PATH=/root/a5_ops/build/lib:/usr/local/Ascend/cann-9.0.0/x86_64-linux/lib64:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64/common:$LD_LIBRARY_PATH
$MSPROF --output=/tmp/msprof_out --application='./benchmark' --aic-metrics=PipeUtilization

# L2 Cache 分析
$MSPROF --output=/tmp/msprof_l2 --application='./benchmark' --aic-metrics=L2Cache

# Memory 带宽分析
$MSPROF --output=/tmp/msprof_mem --application='./benchmark' --aic-metrics=Memory

# UB 利用率
$MSPROF --output=/tmp/msprof_ub --application='./benchmark' --aic-metrics=MemoryUB

# 详细 task timing（L2 级）
$MSPROF --output=/tmp/msprof_detail --application='./benchmark' --aic-metrics=PipeUtilization --task-time=l2
```

**注意**: 使用 `--application=` 而不是 `-- command`（后者在某些 CANN 版本不工作）。LD_LIBRARY_PATH 必须包含 kernel .so 路径。
3. 真正大的是二进制 trace（永远不读），CSV 最多几千行（grep 后很小）

**如果未来需要**（比如 profiling 上千个 kernel 的大模型训练）：
- 可用 haiku sub-agent 做 CSV 过滤 + 聚合
- 输入：op_summary CSV + 查询条件（"找最慢的 5 个 kernel 的 vec_ratio"）
- 输出：< 20 行摘要
- 但对当前项目（2 个算子，< 10 个 kernel），主 agent 直接 grep 足够

## 9. 瓶颈判断速查表

| 现象 | 指标 | 含义 | 优化方向 |
|------|------|------|---------|
| vec_ratio ≈ 1.0, 性能差 | PipeUtilization | Vector 相关活动候选，尚非优化极限证明 | 核对工作域、重叠和指令；再验证改动 |
| scalar_ratio > 0.2 | PipeUtilization | 控制/寻址相关候选，阈值非通用定因规则 | 结合当前源码与对照定位 |
| mte2_ratio > 0.5 | PipeUtilization | 搬运/等待相关候选，可能与其他 pipe 重叠 | 核对字节账与时间域后再评价复用 |
| HBM bandwidth < 10% | Memory | 先校准聚合口径、核数与窗口 | 不能单独排除局部带宽或延迟限制 |
| HBM bandwidth > 80% | Memory | 带宽饱和 | 减少数据量、提高计算密度 |

## 10. 项目中的实际使用记录

| 场景 | 采集命令 | 关键发现 | 指导的优化 |
|------|---------|---------|-----------|
| Pooling A baseline | `--aiv-metrics=PipeUtilization` | bwd vec_ratio=1.0, atomicAdd 15.9 cycles | sorted-edge 寄存器累加 (-81%) |
| Pooling D BRE=dim | 同上 | 历史 fwd vec_ratio=1.0 | 旧记录曾据此判定极限；该推断撤回，单个 ratio 不能证明无优化空间 |
| Pooling nblk sweep | nblk=56 vs 448 | bwd -28%, fwd +14% | 排序后不需要超订 |
| SG forward xlarge | 同上 | vec_ratio=0.69, scalar_ratio=0.31 | 常驻核心分发 (E8-2, 1.86x) |
| SG backward xlarge | 同上 | vec_ratio=0.989 | compute-bound, persistent 无效 |

## 更新 (2026-09-19)

私有沉淀仓（不公开，pinned commit cb9c78c85ead3088398f3455051355349298b3cb）`okf/runbooks/operator-optimization/` 下 MSPROF_AGENT_GUIDE.md 的 9 张节选卡经逐张核读为本文对应小节的忠实摘录（同 lesson、无内容增量），不单独建卡，锚点对照：tool_selection_system_vs_operator → §0；layered_reading_context_safe → §1-§3 分层读取；metrics_group_selection → §4；op_summary_metric_extraction → §4 / Level 2（op_summary 列号与动态表头）；optimization_workflow_loop → §5；run_command_template → §6 与 §9（2026-04-02 更新）；a5_container_limitations → §7 已知限制（A5 容器）；researcher_agent_deep_analysis → §8 aog-researcher 深度分析；bottleneck_lookup_table → §9 瓶颈判断速查表。


## 11. 从调用身份关联任务，再解释时间

### 适用范围与关联步骤

本节处理 arch35 上框架 Node 与公开 ACL 直接启动两种路径。先固定源码、主/辅助 DSO 的实际映射与 hash、PID、输入/布局、warm/目标调用和输出摘要。工具主程序与 `op` 子工具的版本分别记录；主程序只打印 Usage 时，其语义版本仍未知，不能用子工具版本替代。

1. 用同一线程内的主机调用边界定位实际 `aclrtLaunchKernelWithHostArgs`，同时检查外层 Node。分别保留 Node 与嵌套 ACL 的 `connection_id`；二者可能不同，不能预设某个键总是正确。
2. 沿当前原始 JSON 中实际存在的连接关系查设备任务：有 Node 时验证 Node/ACL 哪个键对应设备任务；无 Node 时，只有直接 ACL 键能唯一关联当前任务，才接受该路径。flow 起点缺失应记录，但不自动否定另一个已核实的直接关联；也不能推广成忽略 flow 的规则。
3. 在同一 collection/device/rank 或进程语境内，用具名 Stream ID、Task ID、任务开始与时长交叉核对导出 CSV，保留重复/未关联项，不靠 kernel 名相近或最近时间猜配。单次调用可能产生多个任务，必须先核实任务集合的基数，不能强制“一次 forward 一个 kernel”。必要字段缺失或关系歧义时报告 UNKNOWN。
4. 若采用 flow ID，则核对 Host flow 起点、Device flow 终点与实际任务的 ID/stream/start。没有 MSTX 时，可在源码明确串行且每次 end Event 已同步的条件下，用成对的设备 Event-record 顺序关联多任务集合；说明这是顺序配对，不冒称已完成 Event handle→Task ID 的直接关联。
5. 主机区间仅用于选择主机 API；时钟偏移未校准时，不用其绝对值裁剪设备任务。设备区间用十进制定点/精确十进制计算并集、跨度与间隙，避免 epoch 时间转低精度浮点后丢失微秒。任务并集、host span、Event 和 PMU 各自报告，不相加替代整算子 wall time。

### 输出与因果边界

PMU 的 VEC/MAC/MTE/scalar 活动可重叠；ratio 是待检验假设的线索，不是唯一指令根因、MFU、独占 wall share 或硬件极限。前面的速查表只用于选择下一项观测。单例 profile 不替代正式固定分母 P/Q；profiled Event 与历史未插桩 Event 的差异也不是同窗口开销对照。

公开归档中的直接 ACL 反例有 8 次返回、8 个任务关联，但仅发出 2 份目标输出摘要；不能写成 8 份输出校验。另一个多任务反例每次候选调用有三个工作任务：首 warmup 摘要与历史不同，其余三次候选和四次参考分别与各自历史摘要相同（候选与参考摘要不同），且未做新鲜 CPU64；不能赋予本次 profile 精度 PASS，原因仍未知。商业原生二进制与所读 CANN 源码分支的对应、跨窗口收益和冷黑盒结果均须单独验证。

归档还保留了两项过期 freeze 描述：实际 app 有独立 pre-GO hash 绑定，另一个 claim-control 文件的 pre-GO hash 未绑定。载荷运输 hash 全对不等于所有描述一致；应区分当前实际映射/调用证据与描述缺口。原 guard launcher 的真实返回值也不能补造当时未记录的 guard PID/startticks。具名 WHITE_BOX 源码研究按 caller authority 与复用来源记录；灰盒/冷验证 recipe 的源码访问约束继续按其原契约执行。

资料：直接 ACL 归档与多任务／勘误归档（内部归档，社区不可访问）。这些是范围明确的实验来源，非全部工具版本的行为保证。
