---
type: Runbook
title: "GM 标量表读取：256B 整拷 + 大分配 + 读前硬序"
description: "核内从 GM 读小标量表再 GetValue 需三件套：每单元垫到 256B 用 8 块整拷、表总量落常规大分配、读前加 PIPE_ALL 硬序；缺一即读回全零。"
tags: [task.migration, task.debugging, topic.data_movement.data_copy, topic.programming_model, topic.architecture]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetValue.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag_WaitFlag_ISASI.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/PipeBarrier_ISASI.md
    role: constraint
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-10-28T09:52:17Z"
platforms: ["310p"]
---

# GM 标量表读取：256B 整拷 + 大分配 + 读前硬序

## 现象

kernel 用一个 host 构建的 GM 侧整型表描述每个工作单元的参数（行偏移、batch、head、tile 序、基址等），核内先 `DataCopy` 到 UB，再 `GetValue` 取出标量。迁到 Ascend310P3 后：

- 核内读到的标量**恒为 0**（有效行数 = 0），于是整个"逐行存储"循环被跳过；
- e2e 表现为**输出全零或上一轮残留**，但 kernel 自身的计算段（探针可见）没有报错；
- 这个"全零"在进程之间时有时无（一次跑出 `0.0343`、下一次 `0.2092` 这类残留签名），很容易被误判成偶发竞态或计算错。

用"指针指纹"取证可以把"读没读到"和"算没算对"分开：host 在表的固定位置写一个只有 host 知道的值（例如 host 侧张量第 63 个元素 = 一个可识别的位模式），核内把它读出来回存到探针区，再把探针区 D2H 导出与 host 侧的 `.bin` 逐位比对。

- 坏形态：探针区**全零**、魔数不在、指纹读出 `0x0`，而 host 的 `.bin` 里字段齐全 —— 说明**拷贝根本没落到 UB**；
- 好形态：探针区前 8 个整型 = 期望的 8 个字段、魔数在位、指纹逐位等于 host 写入值 —— 说明**逐位一致**。

## 适用场景

- 工程形态：kernel 直调；host 侧用 `torch::zeros` / `torch::tensor` 构建小整型表并 H2D，kernel 侧 `DataCopy`（`DataCopyParams`）取到 UB 后用 `GetValue` 读标量。典型于"元数据驱动 grid-stride"的算子。
- API 路径：`GlobalTensor<int32_t>` + `DataCopy(UB, gm[u*64], DataCopyParams(8, 1, 0, 0))`、`LocalTensor::GetValue(idx)`、`SetFlag/WaitFlag<HardEvent::MTE2_V>`、`PipeBarrier<PIPE_ALL>()`。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / m200）+ CANN 9.1.0。
- 适用粒度：`operator_family` —— 所有"GM 小表 → UB → 标量"的 kernel 直调算子。
- 路线优先级：`recommended_fastpath`（该形态本身是正解，代价只有一次 256B 拷贝）。
- 明确不适用 / 未验证场景：aclnn/图模式（该表通常由框架物化为常量或 tiling 参数，不经过这条路）；其它代际未验证；32B 单块拷贝是否也需要同样的规避未单独验证。

## 根因

这条通路要同时满足三个条件，缺一个就回到"读值恒零"：

1. **拷贝粒度**：以**单块 32B**（`DataCopyParams(1, 1, 0, 0)` 且每单元只放 8 个 int32）搬运该表，在 310P 上多次实测**不落地**；改成**每单元垫齐 256B、用 8 块整拷**（`(8, 1, 0, 0)`）后落地。宿主要跟着改：表从 `[units, 8]` 变成 `[units, 64]`（`torch::zeros` 垫零），索引从 `u * 8` 变成 `u * 64`。
2. **分配归属**：表的**总量要落在常规大分配**上（本轨迹垫到 32KB 以上，与信标共用同一块缓冲），小分配会按进程地址彩票出现"写/读都到不了核"。
3. **读前硬序**：`MTE2` 到 `V` 的事件对**不保证标量管有序**，`GetValue` 可能在拷贝落地前就读 UB —— 读前必须 `PipeBarrier<PIPE_ALL>()`。标量读与 MTE3 写之间的同类序问题另有一张卡（见 `../precision/gm_setvalue_getvalue_reads_stale_within_kernel.md`），本卡不重复展开。

本轨迹里"256B 整拷"与"总量落大池"两项是**同一批落地的，贡献没有单独隔离**（见失效边界）。

## 判别方法

1. 在 host 侧表的**未使用位**写一个可识别指纹（例如第 63 个 int32 写一个特定位模式），并把**同一份** host `.bin` 落盘。
2. kernel 读完整表后，把**实际读到的 8 个字段**回写到 UB 的探针槽位（`metaUb.SetValue(9, lenQ)` 等），随探针区一起 D2H。
3. 比对三方：host `.bin` / 探针区字段 / 探针区指纹。
   - 三项全空 → 拷贝没落地（粒度或分配问题）；
   - 字段对、指纹对、但业务仍错 → 读没问题，往计算/存储查；
   - 字段是零而指纹在 → 读序问题（`GetValue` 读早）。
4. 用"把读到的值当输入影响输出"的方式做行为级验证：读对 → 存储循环进入次数、输出行数立刻正常；读错 → 存储循环一次都不进。

## 解决配方

host 侧把表按每单元 64 个 int32 构造（垫零）并落到大缓冲；kernel 侧 8 块整拷 + 全屏障 + `GetValue`。

## 设计决策

- **表按 64 个 int32 / 单元垫齐**：多占 224B/单元，换来"整块 256B 传输"这一已被实证的落地形态；标量数量（5 个）远小于垫齐后的槽位，字段布局保持可读。
- **表与信标共用一块 ≥32KB 缓冲**：两者都是"小、频繁读、要求可靠"的元数据，共用一次分配同时满足"落大池"和"信标在声明长度内"。
- **不使用"host 侧把标量拼成一次大拷贝再解析"**：那会把标量读取退化成每个字段一次 `GetValue` 的偏移计算，且同样要过 MTE2→标量的序问题，收益不明确。
- 该配方属 `recommended_fastpath`：一次 256B 拷贝 + 一次屏障，开销可忽略。

## 系统信息

- 目标平台 Ascend310P3（DAV_2002 / m200），CANN 9.1.0；`blockDim = GetBlockNum()`（本轨迹 host 侧取 `min(units, 8)`）。
- host：torch C++ 扩展；kernel：`<generic>_310p` 单文件，unit = (batch, head, q-tile)。
- 文件：`host/<generic>.cpp`（元数据构建与缓冲声明）、`kernel/<generic>.cpp`（unit 循环头部）。

## 完整代码

**host：表按每单元 64 个 int32 构造（垫零），并落到大缓冲**

```cpp
    // ---- 单元元数据 [units, 64]: {qRow,kRow,h,b,lenQ,lenB,t,vBase} + 垫零 ----
    // 垫齐 256B/unit: 核内 (8,1,0,0) 8 块拷贝——单块 32B 拷贝在 310P 上
    // 实测不落地（metaUb 终态恒零 → lenQ 恒 0 → 不存储）
    const int64_t vTile = H * ND * 4096;
    // 下面的 GlobalTensor 视图声明长度为 metaPad + 8，因此分配必须同长：
    // 原始轨迹把 meta 尾接在 >=32KB 的 scratch 大池里（总长度足够），
    // 这里按最小可复现改为独立分配 metaPad + 8 个 int32（尾部 32B 为信标区）。
    const int64_t metaPad =
        (static_cast<int64_t>(units) * 64 > 8192)
            ? static_cast<int64_t>(units) * 64 : 8192;
    auto metaBuf = torch::zeros({metaPad + 8}, torch::kInt32);
    {
        int32_t* mp = metaBuf.data_ptr<int32_t>();
        int64_t u = 0;
        int64_t jBase = 0;   // b 之前累计 tile 数
        for (int64_t b = 0; b < B; ++b) {
            const int64_t st = starts[static_cast<size_t>(b)];
            const int64_t len = cuP[b + 1] - cuP[b];
            const int64_t nb = nJt[static_cast<size_t>(b)];
            const int32_t vBase = static_cast<int32_t>(jBase * vTile);
            for (int64_t h = 0; h < H; ++h) {
                for (int64_t t = 0; t < nb; ++t) {
                    mp[u * 64 + 0] = static_cast<int32_t>(st + t * 64);
                    mp[u * 64 + 1] = static_cast<int32_t>(st);
                    mp[u * 64 + 2] = static_cast<int32_t>(h);
                    mp[u * 64 + 3] = static_cast<int32_t>(b);
                    mp[u * 64 + 4] = static_cast<int32_t>(
                        std::min<int64_t>(64, len - t * 64));
                    mp[u * 64 + 5] = static_cast<int32_t>(len);
                    mp[u * 64 + 6] = static_cast<int32_t>(t);
                    mp[u * 64 + 7] = vBase;
                    ++u;
                }
            }
            jBase += nb;
        }
    }
    auto meta = metaBuf.to(q.device());
```

配套的缓冲与两个视图（同一块 GM，长度 >= 32KB 并含信标区）：

```cpp
    // metaPad 已在上面定义（= max(units*64, 8192)）
    GlobalTensor<int32_t> gmMeta;
    gmMeta.SetGlobalBuffer(reinterpret_cast<__gm__ int32_t*>(meta),
                           metaPad + 8);
    GlobalTensor<float> gmBeacon;
    gmBeacon.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(meta),
                             metaPad + 8);
```

**kernel：8 块整拷 + 硬序 + 读标量**

```cpp
    for (int32_t u = core; u < units; u += blockDim) {
        // ---- unit meta ----
        // 8 块(256B)整拷: 单块 32B 的 (1,1,0,0) 在 310P 上实测不落地。
        // MTE2_V 对不保证标量管有序, GetValue 前须 PIPE_ALL 硬序。
        // unit 级 5 个标量, tile 循环内零标量。
        int32_t qRow, kRow, h, t, vBase;
        DataCopy(metaUb, gmMeta[static_cast<int64_t>(u) * 64],
                 DataCopyParams(8, 1, 0, 0));
        SetFlag<HardEvent::MTE2_V>(evM2);
        WaitFlag<HardEvent::MTE2_V>(evM2);
        PipeBarrier<PIPE_ALL>();
        qRow = metaUb.GetValue(0);
        kRow = metaUb.GetValue(1);
        h = metaUb.GetValue(2);
        t = metaUb.GetValue(6);      // 本 tile 序（对角）
        vBase = metaUb.GetValue(7);  // vT 块基址
        const int64_t qOff = (static_cast<int64_t>(qRow) * H + h) * D;
```

改前（单块 32B，且当时误以为屏障会让 kernel 异常终止）：

```cpp
            DataCopy(metaUb, gmMeta[static_cast<int64_t>(u) * 8],
                     DataCopyParams(1, 1, 0, 0));
            SetFlag<HardEvent::MTE2_V>(evM2);
            WaitFlag<HardEvent::MTE2_V>(evM2);
            // [已被推翻的注释] 此处禁加 PipeBarrier<PIPE_ALL>()——早期实测该屏障
            // 使 kernel 异常终止。真实原因是别处的越界写导致 fault，与屏障无关；
            // 读前硬序是必需的（见失效边界与误诊段）。
```

**探针：把读到的标量留证**（用于区分"拷贝没落地"和"读早"）

```cpp
            vBase = metaUb.GetValue(7);
            // [仪表] 把"实际读到的标量"留证到 metaUb[9..12], 随探针区带出
            metaUb.SetValue(9, lenQ);
            metaUb.SetValue(10, static_cast<int32_t>(u));
            metaUb.SetValue(11, h);
            metaUb.SetValue(12, vBase);
```

## 预防

- GM 元数据表按"≥256B / 8 块整拷 + 落到 ≥32KB 池 + 读前 `PIPE_ALL`"三件套实现，尺寸写成表达式（`8 * sizeof(int32_t)`）而不是字面量。
- 探针必须带指纹与魔数，随表一起读回留证，才能在"没落地"与"读太早"之间分流。
- 不要凭报错现象给屏障定罪；fault 要先用越界写排查（见同 area 的"零有效行重存末行"卡）。

## 验证信号

- 坏形态（改前）：连续三次调用读回 `B[0:12]` 全零、`A[0:8]` 全零、指纹 `0x0`；同时 e2e 在两次调用里是 `0.0343` 级、第三次跳到 `0.2092` 级残留签名（来源平台：310P；证据等级：tool_observed）。
- 好形态（改后）：读回 `B[0:8] = {0,0,0,0,64,64,0,0}`（期望的 8 个字段）、魔数 `0x5A5A` 在位、核内实测 `lenQ = 64`、`存储环进入 = 1`；同一批里核内读到的表与 host `.bin` **逐位一致**（含第 63 个元素的指纹）（来源平台：310P；证据等级：tool_observed）。
- 行为级：读值正确后"逐行存储"循环首次真正进入（探针计数从 0 变 1），输出不再呈全零（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- **未决项（优先）**：本轨迹里"8 块 256B 整拷"与"表总量落到 >=32KB 大池"是**同一批改动**，两者各自的贡献**没有隔离**。下一个 agent 若要写死其中一条，应先做二分实验（只改粒度 / 只改池大小），否则可能把不必要的约束写进规范。
- **不能用来推断"单块 32B 永远不落地"**：本轨迹只观测到该表这一形态；同一会话中 32B 的其它用途（例如小段信标写入）在换到专用大缓冲后是能落地的。判据是"实测 + 指纹"，不是"32B 一律不行"。
- 只适用于"kernel 直调 + host 侧自建表"；aclnn/图模式下该表由框架处理，不适用。
- 未验证平台：其它代际未验证；`PIPE_ALL` 的必要性在其它平台上是否成立未验证。
- "同代兄弟算子也用 8 块整拷读 GM 标量"这一点在本次会话里只是转述（未在本轨迹内独立核验），故不作为验证信号，只作旁证线索。
- 本卡不覆盖"表本身内容算错"的情形（那属于 host 侧索引构造问题）。

## 坏实践

- **每单元只搬 8 个 int32（32B）**：最自然的写法，也是本卡要禁的那一条。
- **把"表读回全零"当成"kernel 没跑到"**：两者的判别就靠起跑/收尾信标与指纹，不要凭感觉。
- **把 `MTE2_V` 事件对当成"标量读到的是新值"的保证**：它只管 V 管。
- **按报错现象给屏障定罪**：早期把 kernel 异常终止归给 `PipeBarrier<PIPE_ALL>()`，导致"读前硬序"这条被反向写进注释；屏障本身不是 fault 来源。

## 误诊

- 误诊（agent_reported）：曾把"表读值恒零"直接归因为"小块池 VA 对核不可达"，于是只把张量垫到 32KB —— 症状仍在；直到同时把拷贝粒度改成 8 块整拷才落地。
- 误诊（agent_reported）：也曾把"输出全零/残留"当成 kernel 计算错，反复改计算段的向量指令；判别成本其实很低（探针区指纹一比即知）。
- 误诊（agent_reported）：早期把某次 kernel 异常终止归因为"加了 `PipeBarrier<PIPE_ALL>`"，并在代码注释里禁用该屏障；后续定位到真正原因是别处的越界写触发 fault（见同 area 的"零有效行仍重存末行"卡），屏障本身无过。
