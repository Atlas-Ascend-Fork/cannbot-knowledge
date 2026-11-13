---
{
  "type": "Runbook",
  "title": "cannbot-dsl 0.7.0 bulk DMA 与跨 item 槽位复用下的精度损坏及同步规避",
  "description": "WeLMv4 融合算子接入 sglang 后，在大 M prefill、bulk 多 burst DMA 和 depth=1 槽位复用的组合下观测到 K 的 RoPE 段偶发损坏。每 item 插入 vec_sync_all() 后所测 30 次 launch 无损坏，对照删除该行则 6/30 损坏，恢复后回归 28/28 通过。dump 中存在 get_buf/release_buf；release 完成语义或跨 item 同步不足为待验证假设，尚未唯一定位框架或硬件根因。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.data_movement"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# cannbot-dsl 0.7.0 bulk DMA 与跨 item 槽位复用下的精度损坏及同步规避

## 适用场景

- 模型/框架：WeLMv4（sglang 推理树 `linyuan/sglang`）自定义融合算子 `fused_qkv_proj_norm_rope_cache`（bf16）与 `fused_qkv_proj_norm_rope_cache_mx`（MXFP8），用 cannbot-dsl 编写，CUBE+MIX 结构；算子把 QKV 投影、K 的 RMSNorm、Q/K 的 RoPE 与 paged KV cache 散写融合为单 kernel。
- 编译链：cannbot-dsl 0.7.0（`CANNBOTDSL_HOST_ABI_VERSION=9`）。自动同步实现链为 `AutoBufferSync.cpp`（按执行流水 MTE2/V/MTE3/FIX 分类缓冲读写事件）→ `AllocateSyncIds.cpp`（生成 wait_free/signal_ready/wait_ready/signal_free 四角色计数锁协议）→ `Optimize/EliminateBufferSync`（删"冗余"锁）→ `ConvertCANNIRToAsc`（降成 AscendC 的 `asc_lock`/`asc_unlock`，即 MLIR 的 `get_buf`/`release_buf`）。
- 平台/硬件：Ascend 950DT（NPU，`__NPU_ARCH__ == 3510`），CANN 9.1.0-beta.3 环境。
- 工作负载：大 M prefill（连续 positions，bulk cos/sin 预载 DMA）。触发区间 mirror 层 M>768 / plain 层 M>1024。
- 缺失信息：其他 cannbot-dsl 版本、其他 NPU 型号、其他算子结构未验证；框架侧修复（`AllocateSyncIds`/`OptimizeBufferSync` 补强）在本轨迹内未发生（仅整理了报障要点）。

路径补充：`${SCRATCH_ROOT}` 为本地复现脚本工作目录。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

故障：算子接入 sglang 网络后功能测试偶发精度失败。压测（`${SCRATCH_ROOT}/stress_base.py`，M=2048 mirror prefill，逐 launch 校验 K 输出）抓到稳定复现，客观输出（事件 387）：

```
iter 1: CORRUPT  r3: 113 elems, rows[504,505], first-row cols[193,255], loc=[(1, 1, 120), (1, 1, 121)]
iter 3: CORRUPT  r1: 115 elems, rows[430,431], first-row cols[192,255], loc=[(1, 1, 46), (1, 1, 47)]
iter 7: CORRUPT  r1: 118 elems, rows[260,261], first-row cols[192,255], loc=[(1, 0, 4), (1, 0, 5)]
iter 9: CORRUPT  r2: 244 elems, rows[24,27], first-row cols[192,255], loc=[(0, 0, 24), (0, 0, 25), (0, 0, 26), (0, 0, 27)]
```

关键事实：arena 样例**原样代码**（base 入口）在 M=2048 下同样损坏（事件 398，3/10 launch 损坏）——说明故障并非只出现在最初修改版；是否来自框架同步、算子资源建模或其他实现问题尚未隔离；小 M（无槽位复用）10/10 干净。修复对照（事件 1093，仅删掉一行同步的对照版）：30 次 launch 中 6 次损坏（20%），损坏集中在 K 的 RoPE 段、err 达 8。

cannbot-dsl 0.7.0 自动 buffer-sync 降级出的 get_buf/release_buf（asc_lock/asc_unlock）产物在本例『bulk 多 burst GM→UB DMA + depth=1 UB 槽位跨 item 复用』组合下出现精度损坏：M=2048 压测下 ~20-30%/launch 出现仅 K 的 RoPE 段（192-255 列）2-4 个连续行（512B 粒度）的陈旧数据损坏，损坏随代码生成方式变化（CANNBOTDSL_BARALL=1 与 DEBUG_ASC_SYNC=pipe 在所测 launch 中未再出现损坏）；尚不能排除算子资源建模或地址问题。

## 探针与操作

1. **压测 harness**：迭代 launch + 逐次与 golden 对拍，打印损坏 (rank, pair, AIV 半区, 行范围) 与"损坏行匹配哪个 cs 表偏移"诊断（±300 全搜）。
2. **对照矩阵**：
   - `CANNBOTDSL_BARALL=1`（给毕昇编译器传 `-cce-aicore-sync-bar-all=true`，全局保守屏障）：base/rank_chunk/MX 全部干净（事件 473：10/10；显式 `BARALL=0` 可复现，构成同步干预的 A/B 对照）。
   - `CANNBOTDSL_DEBUG_ASC_SYNC=pipe`（框架自带 `cannir-insert-debug-asc-sync` pass，跨流水域每个 op 后插 `asc_sync()`）：10/10 干净（事件 941）；`=vf`（VF 体内 MemBar）仍损坏（事件 945）——支持优先排查 MTE↔V 跨流水时序；插屏障会改变整体时序，不能独立排除 VF 或缓冲建模等其他原因。`BUFFER_READ_SHARING=0` 在本次实验中未消除损坏（事件 938）。
   - `positions_contiguous=False`（逐行 cs gather，decode 产物）：M=2048 有复用时 10/10 干净（事件 433）——锁定 bulk DMA 路径。
3. **MLIR/AscendC dump**：`CANNBOTDSL_DUMP_MLIR=1 CANNBOTDSL_DUMP_ASCENDC=1 CANNBOTDSL_DUMP_DIR=...` 编译 racy 版本后检查 item 循环同步端点（证据见下节）。
4. **单屏障二分**（`CANNBOTDSL_REUSE_ASCENDC` 从 dump 文件回读手工编辑的 .asc 再编译）：在 AIV item 循环内 DMA 后 / VF 后 / drain 后**任意一个**位置插一条 `asc_sync()`，做三变体 × 12 launch（事件 993）：

```
[plain   ] insertions=  0 iters=12 -> CORRUPT x4
[afterDMA] insertions=  1 iters=12 -> CLEAN
[afterVF ] insertions=  4 iters=12 -> CLEAN
[afterDr ] insertions=  6 iters=12 -> CLEAN
```

单屏障对照支持跨 item 时序相关假设：在 item 循环内 DMA 后/VF 后/drain 后任意一个位置插一条 asc_sync() 均修复（3 变体 × 12 launch 全干净，plain 对照 4/12 损坏）。DEBUG_ASC_SYNC=pipe（跨流水域）10/10 干净而 vf 域（VF 体内 MemBar）仍损坏，也支持优先排查跨流水同步。以上实验未直接测量硬件完成语义，不能唯一证明 item 内锁依赖充分或 release 协议失效。

## 机制与判别

**dump 实证（MLIR，racy 版 MX 产物 compile_aot_mx(2560, 24576, 24692, return_v=True, positions_contiguous=True)）**：item 循环内 bulk cs 预载被 `get_buf`/`release_buf` 包夹，锁 token 在生成代码里齐全（事件 1202）：

```
          ascvec.get_buf mte2, %c2_i64, 0 {cannir.buffer.generated_sync}
          %46 = arith.muli %41, %c64_i64 : i64
          %47 = arith.index_cast %46 : i64 to index
          ascvec.copy_gm2ub %alloc_12[%c0], %alloc_1[%47], %c128_i32, %c256_i32, %c256_i64, %c256_i32, %c0_i32, %c0_i32 l2_cache_ctl %c0_i32 : memref<8256xf32, 1>, memref<1580288xf32>
          ascvec.release_buf mte2, %c2_i64, 0 {cannir.buffer.generated_sync}
```

同一段在 AscendC dump 中（事件 1195；128 burst × 256B 的 `copy_gm2ub_align` 在 `asc_lock/asc_unlock(PIPE_MTE2, 2)` 之间，随后 VF 消费同一 buf227）：

```
1374:                    asc_lock(PIPE_MTE2, 2);
1377:                    cannbotdsl_92::cannbotdsl_copy_gm2ub_align((__ubuf__ float*)buf227 + 0, (__gm__ float*)gm6 + t393, 128, 256, 0, 0, true, static_cast<uint8_t>(0), (uint64_t)256, 256);
1378:                    asc_unlock(PIPE_MTE2, 2);
...
1394:                asc_sync_intra_wait(PIPE_V, 0);
1395:                asc_lock(PIPE_V, 1);
1396:                asc_lock(PIPE_V, 2);
1397:                kernel_FusedQkvProjNormRopeCacheMxKernel___call___0_vf0((__ubuf__ float*)buf225, (__ubuf__ bfloat16_t*)buf226, (__ubuf__ float*)buf227, sel380);
1398:                asc_unlock(PIPE_V, 2);
1399:                asc_unlock(PIPE_V, 1);
1400:                asc_sync_intra_arrive(PIPE_V, 0);
1401:                asc_lock(PIPE_MTE3, 1);
```

**框架契约（框架仓原文）**：设计文档 `docs/design/channel_buffer_sync_unification.md`（事件 1216）写明协议成立前提：

```
资源仅因源码先后而复用是不充分的：跨 PIPE 交接依靠此前生成的阻塞锁和对应 PIPE 的完成语义。
```

使用文档 `docs/usage/RING_BUFFER.md`（事件 1230）承诺：

```
head/tail 不固定对应 Cube 或 Vector。用户控制流决定预取、计算及收尾的时机；
编译器根据 Tensor 的实际访问及资源身份生成同步。
```

即算子的 depth=1 RingBuffer 槽位循环复用 + mem_copy 是官方支持模式（框架 matmul 样例自身即循环内 head_next/tail_next）。

机制解释（推断，未经硬件级直接测量）：release_buf（asc_unlock）排在流水的指令队列里、按队列条目 retire 生效——单 burst 小搬运 retire≈数据落盘，但一条 128-burst 大 DMA 的 retire 点与最后一个 burst 真正读写完 UB 之间存在缝隙，锁已放行而数据还在路上；框架设计文档（channel_buffer_sync_unification.md）写明该协议的成立前提是『跨 PIPE 交接依靠此前生成的阻塞锁和对应 PIPE 的完成语义』，且 RING_BUFFER.md 承诺『编译器根据 Tensor 的实际访问及资源身份生成同步』，算子的 depth=1 槽位循环复用是官方支持模式。release 完成语义不足是待验证假设；仍需检查算子的资源别名建模、实际地址与框架同步覆盖，不能仅凭文档承诺判定责任归属。

**触发条件判别**：本次样本将损坏与下列组合关联，但尚未证明这些是普遍必要且充分条件：跨 item 槽位复用（m_pairs×n_units > 32 个 AIC block，即 mirror 层 M>768 / plain 层 M>1024；depth=1 的 cs_ch/out_ch 使下一个 item 的写与本 item 的读写落在同一块物理 UB）、bulk cos/sin 预载 DMA（positions_contiguous=True 的 prefill 产物专有，一条 128-burst/32KB 描述符；decode 逐行 gather 压测 10/10 干净）、以及读写指针时序重叠（概率性而非必现）。这解释了 decode/小 batch 一直"没事"、prefill 大 M 才是风险面：逐行 gather 与 bulk 形式的指令发射时序不同，可能改变竞争窗口；该时序解释未做硬件级测量，10/10 干净不保证其他负载均不触发。

**损坏签名判别**：损坏签名可判别根因方向：仅 K 的 RoPE 段（192-255 列）错而同位 norm 段（0-191 列）正确（削弱整行 cv/fixpipe 陈旧的解释，但不能排除部分元素或其他路径的问题）、总是 2-4 个连续行（512B-1KB，DMA burst 粒度）、位置随机（前缀/中段/后缀都出现过）、损坏值不匹配任何 cos/sin 表行偏移（轨迹曾做偏移搜索，所搜范围内未匹配；不能排除全部寻址问题），更像读到别的作业写进同一块 UB 的数据。

**可区分解释分支**：
- 读错 cs 表行（如 positions 寻址错）→ ±300 偏移搜索未找到匹配（事件 425），削弱所搜范围内简单错行解释，未排除所有寻址问题；
- cv（fixpipe 跨核数据）整行陈旧 → “norm 段正确”削弱该解释，不能排除局部数据或其他路径问题；
- VF 体内乱序 → DEBUG_ASC_SYNC=vf 未消除损坏（事件 945），该干预不足以排除所有 VF 或跨域依赖问题；
- 算子资源建模、地址或依赖表达问题 → 尚未完全排除；BARALL/pipe 和样例对照仅能说明同步及时序干预有效，不能证明源码符合所有前提；
- 框架锁协议覆盖不足（跨 item WAR 依赖未被 release 完成语义约束）→ 与全部观测吻合（单屏障对照支持跨 item 时序相关假设，未唯一定位）。

## 验证信号

（均为本轨迹内、Ascend 950DT、单次会话客观观测）

- 压测复现：rank_chunk ~40%/launch 损坏（事件 387）；arena base 样例原样代码 M=2048 损坏 3/10、M=512（无槽位复用）10/10 干净（事件 394/398）。
- cs 偏移搜索为空（事件 425）；逐行 gather 版 10/10 干净（事件 433）；bulk DMA 无条件提出 if 仍损坏（事件 440）。
- `CANNBOTDSL_BARALL=1` 在本次 10 次 launch 中无损坏（事件 473，10/10）；`DEBUG_ASC_SYNC=pipe` 10/10 干净、`=vf` 仍损坏（事件 941/945）。
- 单屏障二分（事件 993）：三位置任一单屏障均 CLEAN，plain 对照 CORRUPT x4。
- 修复对照（事件 1090/1093）：含 `vec_sync_all()` 30/30 干净 vs 仅删该行 6/30 损坏（20%）。
- MLIR/AscendC dump（事件 1195/1199/1202）：锁 token 齐全但硬件仍竞态——同步"看似存在"不等于"足够"。
- 回归用例双向验证（事件 1140/1147）：临时移除修复后 MX 第 1 次 launch 即失败（4 K 行，max err 5.15）、bf16 第 5 次 launch 失败（err 5.67）；恢复后全套件 28/28 通过（事件 1153）。

## 适用与失效边界

- 适用：cannbot-dsl 0.7.0、Ascend 3510 架构（950DT）、CUBE+MIX 算子中 AIV 侧 `depth=1 UB 槽位 + bulk 多 burst GM→UB 预载 + VF epilogue + UB→GM 回写 + 跨 item 复用`的组合；损坏概率 ~20-30%/launch（10~30 次小样本压测估计，非大规模统计）。
- 本次未复现：decode 逐行 gather 路径；小 M（每 block 1 个 item，无槽位复用）；Cube 侧 L1/L0 槽位复用（框架 matmul 样例模式，单流水消费）。
- 根因的 retire/落盘缝隙机制是推断（有二分实验与文档旁证，未硬件级直接测量）；向框架团队报障时以此作为待验证假设，复现材料：`${SCRATCH_ROOT}/stress_base.py`（M=2048）+ MLIR/AscendC dump。
- 算子侧规避：在 cs 预载之后、cube K-loop 之前每 item 插入一次 `vec_sync_all()`；源码改动、双向正确性回归和 msprof task-time A/B 见 [每 item 一次 vec_sync_all() 的修复与代价测量](../performance/item_vec_sync_all_cannbot_dsl_msprof.md)，其中 0~1.4% 的代价仅为该环境下的观测。框架侧补强（`AllocateSyncIds`/`OptimizeBufferSync` 对多 burst DMA + 槽位循环复用组合补 release 完成语义，或对跨 item 危害插显式回边屏障）在本轨迹内未发生。
- 停止/回退条件：若框架后续版本在 dump 中对跨 item 回边生成了显式屏障（或 release 语义补强），算子内的 workaround 可按注释中的移除条件删除并用 `slot_reuse_race` 回归用例验证。
