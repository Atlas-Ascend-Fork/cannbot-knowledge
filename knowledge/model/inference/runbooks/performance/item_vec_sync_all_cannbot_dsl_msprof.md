---
{
  "type": "Runbook",
  "title": "源码级每 item 一次 vec_sync_all() 关闭 cannbot-dsl 0.7.0 跨流水同步缺口（msprof task-time 实测代价 0~1.4%、生产 prefill 热路径 0.0%）",
  "description": "针对 cannbot-dsl 0.7.0 自动 buffer-sync 在 bulk DMA + depth=1 槽位跨 item 复用下的概率性精度损坏，在算子源码 cs 预载之后每 item 插入一次框架公开 API vec_sync_all()（替代全局 CANNBOTDSL_BARALL=1 环境变量方案）：修复版 30 次压测 30/30 干净、仅删该行的对照版 6/30 损坏；msprof --task-time=on 的 A/B（逐字节相同模块仅差一条同步）实测生产 prefill 热路径 M=16500 代价 ±0.0%（bf16 493.1µs vs 493.1µs、MX 261.2µs vs 261.1µs），M=2048 +0.8%、decode M=56 +1.4%；随附 M=2048×20-launch 行级零容忍回归用例（双向验证）并已提交推送。",
  "tags": [
    "task.implementation",
    "topic.model_serving",
    "topic.data_movement"
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
# 源码级每 item 一次 vec_sync_all() 关闭 cannbot-dsl 0.7.0 跨流水同步缺口（msprof task-time 实测代价 0~1.4%、生产 prefill 热路径 0.0%）

## 适用场景

- 模型/框架：WeLMv4 融合算子 `fused_qkv_proj_norm_rope_cache`（bf16）/ `fused_qkv_proj_norm_rope_cache_mx`（MXFP8），cannbot-dsl 0.7.0 编写，接入 sglang（`linyuan/sglang`）与 cannbot-arena 样例仓（两个仓库共 4 份文件）。
- 平台：Ascend 950DT（NPU，3510 架构），CANN 9.1.0-beta.3；msprof 位于 `ascend/9.1.0-beta3/ascend/cann-9.1.0-beta.3/bin/msprof`。
- 目标：消除"bulk cs 预载 DMA + depth=1 槽位跨 item 复用"下 ~20-30%/launch 的 K RoPE 段陈旧数据损坏，同时量化该同步的 kernel 级代价；复现条件、跨流水同步定位实验及机制推断的边界见 [bulk DMA 与槽位复用下的自动 buffer-sync 缺口](../precision/cannbot_dsl_buffer_sync_bulk.md)。
- 缺失信息：其他 cannbot-dsl 版本/硬件未验证；性能数字为单次会话、共享设备上的观测。

## 触发与观测

不插同步时 M=2048 mirror prefill 压测 ~20-30%/launch 损坏（仅 K RoPE 段 2-4 行、512B 粒度，err 达 8）；该损坏在任何 M 下都被现有测试 0.1% 元素率容差稀释而漏检（损坏元素数与 M 无关、预算随 M 线性放大）。

修复有效性对照（arena MX 样例，30 次 launch @ M=2048 mirror prefill）：含 vec_sync_all() 的修复版 30/30 干净；同一文件仅删掉 vec_sync_all() 一行的对照版 6/30 损坏（20%）——若修复无效，30 次全干净的概率仅 0.8³⁰≈0.1%。

## 探针与操作

修复实现：在 fused_qkv_proj_norm_rope_cache（bf16/MX）算子源码的 cs 预载之后每 item 插入一次 vec_sync_all()（框架公开 API，from cannbotdsl.ops.sync import vec_sync_all），并在注释中写明触发条件与移除条件；替代此前 os.environ.setdefault("CANNBOTDSL_BARALL", "1") 全局屏障方案（本次会话交错 A/B 观测：barall 恒为最慢组，best 1.210-1.290ms vs plain 0.899-1.211ms；早前跨进程单次测量为 +1.2%，两种口径在共享设备上不一致）。

**实现工件**（git diff，4 文件同步应用；bf16 模块 2 个 device 入口共 2 处、MX 模块 1 处）：

```
 from cannbotdsl.ops.arch import get_block_idx, get_block_num, get_subblock_id
+from cannbotdsl.ops.sync import vec_sync_all
```

cs 预载（bulk/gather 两分支）之后、cube K-loop 之前插入：

```
            # WORKAROUND (cannbot-dsl 0.7.0 codegen race): the
            # bulk cs preload DMA and the VF epilogue share this
            # depth-1 cs_ch slot across loop items; the automatic
            # buffer-sync lowering leaves a cross-pipe (MTE<->V)
            # window when one AIV block processes >= 2 items
            # (m_pairs * n_units > 32 AIC blocks: mirror M > 768,
            # plain M > 1024) -- ~30% of launches read 2-4 stale
            # K RoPE rows (512B granularity). One full core barrier
            # per item closes it at noise-level cost; remove once
            # the framework lowers the missing barrier itself.
            vec_sync_all()
```

`vec_sync_all()` 即框架 Python 层公开的原语（`cannbotdsl/ops/sync.py`：`def vec_sync_all(): ascvec.sync_all()`，"Wait for all pending Vector Core pipeline operations"），与 debug pass 插入的 `asc_sync()` 同源，因此单屏障二分实验（任意位置一条 asc_sync() 即修复）直接支持该定点修复。

**代价测量方法**（msprof task-time，与仓内 `perf_compare_mx.py` 同款）：
- A/B 模块由正则从上船样例剥离 WORKAROUND 块生成：`ab/fused_{bf16,mx}_{fixed,nosync}.py`，逐字节相同、仅差一条 `vec_sync_all()`（C 1243）；
- msprof 逐 kernel 精确计时，避免把约 0.9ms host launch 耗时混入 kernel 时长；共享设备争用仍可能改变 kernel 时间，交替与中位数只能降低部分影响：

```
msprof --task-time=on --ai-core=on python perf_sync_msprof.py --runner --variant nosync --op mx --mode prefill --m 2048 --repeat 3
```

- 每组 = 3 轮 fixed/nosync 交替 × (1 预热 + 10 launch)，解析 op_summary 的融合 kernel Task Duration，取各轮中位数再取中位数（单轮偶发他人占用尖峰 981µs/312µs 被中位数自动剔除）。

msprof --task-time=on 实测代价（A/B 模块逐字节相同、仅差一条 vec_sync_all()，3 轮 fixed/nosync 交替 × (1 预热 + 10 launch)，取各轮中位数再取中位数，Ascend 950DT，单次会话）：bf16 prefill M=16500（生产热路径）nosync 493.1µs vs fixed 493.1µs（+0.0%）；MX prefill M=16500（生产热路径）261.2µs vs 261.1µs（-0.0%）；MX prefill M=2048（竞态触发区间）46.4µs vs 46.8µs（+0.8%）；MX decode M=56 9.2µs vs 9.3µs（+1.4%）。

原始输出（事件 1281）：

```
bf16 prefill M=16500: kernel-time nosync=   493.1us fixed=   493.1us  delta=   +0.0us ( +0.0%)  nosync-runs=[493 493 493] fixed-runs=[493 493 493]
mx prefill M=16500: kernel-time nosync=   261.2us fixed=   261.1us  delta=   -0.1us ( -0.0%)  nosync-runs=[261 261 261] fixed-runs=[261 261 261]
mx prefill M=2048: kernel-time nosync=    46.4us fixed=    46.8us  delta=   +0.4us ( +0.8%)  nosync-runs=[46 47 46] fixed-runs=[47 47 981]
mx decode M=56: kernel-time nosync=     9.2us fixed=     9.3us  delta=   +0.1us ( +1.4%)  nosync-runs=[9 9 9] fixed-runs=[9 312 9]
```

与端到端交错 A/B（同一进程内 fixed/nosync 交替计时，best-ratio 0.947~1.016，噪声内）互相印证。

**回归用例**（bf16/MX 测试文件各加一个，复用 AOT 用例编译常量命中进程内缓存，单用例仅 +21~32s）：

```
# ---- regression: bulk cs DMA + RingBuffer slot reuse race ------------------
# cannbot-dsl 0.7.0's automatic buffer-sync lowering leaves a cross-pipe
# (MTE<->V) window when one AIV block processes >= 2 work items (mirror
# M > 768 / plain M > 1024, i.e. m_pairs * n_units > 32 AIC blocks): on
# ~20-30% of launches the K epilogue reads 2-4 consecutive stale RoPE rows
# (512B granularity) from the depth-1 cs_ch slot.  The kernel inserts one
# vec_sync_all() per item to close it (see the sample source).
#
# M=2048 mirror prefill (80 items / 32 blocks + bulk cos/sin DMA) is the
# minimal production-shaped trigger.  The element-rate isclose budget of
# the network tests cannot see this corruption at ANY M (a fixed ~2-4
# corrupted rows always dilutes below 0.1%), so this test instead counts
# rows whose RoPE section deviates by more than 0.05 from the golden
# across repeated launches.  Threshold margin: clean launches stay under
# 0.05 everywhere (1-2 ulp on O(1) bf16 values), stale-cs corruption
# produces O(1..8) errors.  With the unfixed kernel at ~25%/launch, 20
# launches pass with probability < 1%.
_RACE_LAUNCHES = 20
_RACE_NUM_TOKENS = 2048  # 8 pairs x 10 units = 80 items > 32 AIC blocks
```

## 机制与判别

- 修复位点正确性：单屏障二分证明 `asc_sync()`（= `vec_sync_all()` 降级产物）是全核屏障、item 循环内任意位置都能关闭竞态窗口，故选在 cs 预载后、cube K-loop 前——此时屏障与 Cube 侧 8 轮 K-loop 的 MMAD 流水重叠，AIV epilogue 本就不是关键路径；这解释了大 M 反而零成本（M=16500 时每 AIV block ~20 个 item）而 M=2048（每 block 仅 2-3 个 item、尾部波次效应主导）也只有 0.4µs（+0.8%，接近 msprof 计时分辨率）。
- decode 路径本无槽位复用、不需要该屏障，+1.4%（0.1µs）属无害冗余。
- 对比修复路线：`CANNBOTDSL_BARALL=1` 是编译期全局保守屏障（毕昇 `-cce-aicore-sync-bar-all`），交错 A/B 中恒为最慢组（best 1.210-1.290ms vs plain 0.899-1.211ms；早期跨进程单次测量 +1.2%——共享设备上两种口径不一致，故以单进程交错与 msprof task-time 为准）。`vmem_bar`/`vec_sync_pipe/notify/wait` 等更细粒度原语未逐一验证定位效果，源码级 `vec_sync_all()` 是本次验证有效且观测成本较低的方案；未比较所有细粒度方案，不能认定成本最低。
- 未验证推断：屏障"被 Cube 侧 MMAD 完全掩盖"是结构性解释（单次会话观测的合理解释，未做波形级验证）。

## 验证信号

（本轨迹内、Ascend 950DT 客观观测）

- 正确性对照（事件 1090/1093）：修复版 30/30 干净；仅删 `vec_sync_all()` 一行的对照版 6/30 损坏（20%，均为 K RoPE 段、err 达 8）。
- 回归用例双向验证（事件 1134/1137/1140/1147/1150）：修复版两用例通过；临时移除修复后 MX 第 1 次 launch 失败（4 K 行，max err 5.1484）、bf16 第 5 次 launch 失败（err 5.6680）；恢复后全套件 28/28 通过（事件 1153）。
- 性能（事件 1281，msprof task-time，单次会话）：生产 prefill 热路径 M=16500 代价 ±0.0%（bf16 493.1 vs 493.1µs；MX 261.2 vs 261.1µs，三轮交替中位数完全稳定）；M=2048 +0.8%（0.4µs）；decode M=56 +1.4%（0.1µs）。
- 全套件复验（不带任何环境变量）：arena bf16 14 + MX 12 通过；网络集成 MX 5/5、bf16 5/5（bf16 套件一次偶发失败为共享设备抖动，单跑与复跑均过）。

回归用例（bf16/MX 各一）双向验证：M=2048 mirror prefill（80 items/32 blocks 槽位复用 + bulk cs DMA）× 20 次重复 launch，RoPE 段行级零容忍（|err|>0.05 计坏行，必须为 0）——修复版两用例通过；临时移除 vec_sync_all() 后 MX 在第 1 次 launch 即失败（4 K 行，max err 5.15）、bf16 在第 5 次 launch 失败（4 K 行，err 5.67）；恢复后全套件 28/28 通过。该修复与回归用例已提交（f28a960）并推送到 origin/fused_qkv（d862f65..2c68a16）。

## 适用与失效边界

- 适用：cannbot-dsl 0.7.0 + 3510 架构；CUBE+MIX 算子 AIV 侧存在跨 item 槽位复用 + bulk DMA 预载的场景。性能数字仅代表本会话硬件/版本口径，不构成通用加速或零成本承诺；共享设备上的绝对值有波动，复现时应采用同款 msprof task-time + 交替 A/B 协议。
- 失效/边界：若算子每 block 只处理 1 个 item（小 M），该屏障是纯冗余（但实测代价 ≤1.4%）；框架后续版本若自行补齐跨 item 屏障，按注释移除条件删除并用 `slot_reuse_race` 用例回归。
- BARALL 方案不推荐作为长期修复（全局恒定开销，且掩盖真实缺口）；`CANNBOTDSL_REUSE_ASCENDC` 与 `CANNBOTDSL_DUMP_ASCENDC` 互斥，勿同时开。
- 性能测量注意：msprof 计时分辨率约 1µs，0.1µs 级差异只做方向参考；共享设备上单轮尖峰（981µs/312µs）必须用中位数剔除，否则会得出错误结论。
