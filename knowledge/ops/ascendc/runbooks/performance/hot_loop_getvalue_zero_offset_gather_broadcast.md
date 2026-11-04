---
type: Runbook
title: 热循环 GetValue 触发形态硬门 - 零偏移表 Gather 广播
description: 逐 token 用 GetValue 取门控标量做 Muls 命中形态硬门；改为全零偏移表 Gather 生成同值向量再 Mul，热循环零标量读，时延约为改造前的 0.93x。
tags: [task.optimization, topic.performance.analysis, topic.implementation.masking, topic.compute.elementwise.arithmetic]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/scatter_gather/Gather.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/GetValue.md
    role: supporting
created_at: "2026-10-28T10:00:08Z"
updated_at: "2026-10-28T10:00:08Z"
platforms: ["310p"]
---

# 热循环 GetValue 触发形态硬门 - 零偏移表 Gather 广播

## 现象

算子功能与精度都正确，性能数据也远超门限，但性能验收的**形态硬门**（主循环/tile 循环内 `GetValue`/`SetValue` 零容忍）判为失败：kernel 在每 token 的 tile 循环体内用 `LocalTensor::GetValue(tt)` 取一个门控标量，再拿它做整条向量的 `Muls`。每 token 一到两次标量读，总次数随 token 数线性增长——静态 `grep -n "GetValue\|SetValue"` 就能命中，命中行落在 tile 循环体内（本轨迹命中四行：一行是注释、两行是循环体内的 `egT.GetValue(tt)` / `beT.GetValue(tt)`、一行是与之配套的 `SetFlag/WaitFlag<MTE2_S>` fence）。

这类“逐元素标量读”和“per-launch 少量低频标量（例如只读张量尾的几项）”要严格区分：后者在门禁允许范围内（每 launch ≤7 次），前者是硬失败。

## 适用场景

- 工程形态：AscendC 单核/AIV 纯向量 kernel，tile 循环内需要对“整条向量乘同一个标量”的语义做广播（门控系数、β、缩放因子等按 token 变化的标量）。
- API 路径：`LocalTensor::GetValue` / `Muls` / 事件 `SetFlag<HardEvent::MTE2_S>`；替代路径 `Gather(dst, src, offsetTable, srcBaseOffset, count)` + `Mul`。
- 验证过的平台与 CANN 版本：310P（Ascend310P3，dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：单 kernel 的热循环体（tile 级）。
- 路线优先级：`recommended_fastpath`（既过形态硬门，又去掉标量可见性依赖）。
- 明确不适用 / 未验证场景：需要标量参与**分支控制**（if/while 条件）时不能换成向量广播——那类标量读无法用向量指令替代，只能靠 per-launch 低频设计规避；910B 等其它平台未在本轨迹验证。

## 判别方法

1. `grep -n "GetValue\|SetValue" <kernel>.cpp`，看命中是否落在 tile 循环体内（不是只出现在尾部/入口）。
2. 同时 `grep -n "Muls(" <kernel>.cpp`：与循环体内 `GetValue` 成对出现的 `Muls` 就是被广播的标量。
3. 若还有 `SetFlag/WaitFlag<HardEvent::MTE2_S>`，说明该标量读还依赖 scalar 可见性事件——这是同一问题的第二个症状。

## 根因

`GetValue` 是从 UB 里取标量到标量寄存器，属于 scalar 管道的逐元素读：它既被形态硬门直接禁止（热循环内零容忍），又需要显式的 MTE2→S 事件（`SetFlag/WaitFlag<HardEvent::MTE2_S>`）才能保证读到刚由 MTE2 搬进来的数据。也就是说，一个“把标量乘到整条向量”的语义，被迫拆成“逐元素标量读 + 依赖 scalar 可见性 fence”的脆弱形态，既过不了静态检查，又把每次循环卡在标量可见性上。

## 解决配方

把“逐 token 标量广播”改成“向量广播”：host 侧多下发一张**全零字节偏移表**，核内用 `Gather` 以 `srcBaseOffset = t*4`（字节）取整条同值向量，再用 `Mul` 取代 `Muls`。之后热循环里不再有标量读，配套的 MTE2→S fence 也随之删除（只剩下 `PipeBarrier<PIPE_ALL>` 保证 MTE2→V 可见性）。

核心改动只有三处：删 fence、`eg` 广播、`β` 广播；入参/缓冲/建表见“完整代码”。

## 完整代码

### 1) kernel 头部注释（说明形态契约）

修复前：

```cpp
//   E3  scalar 无隐式 auto_sync —— tile 装载后 PipeBarrier<PIPE_ALL> +
//       SetFlag/WaitFlag<MTE2_S> 再 GetValue(eg/β)
```

修复后：

```cpp
//   E3  scalar 无隐式 auto_sync —— 用 PipeBarrier<PIPE_ALL> 保证 MTE2→V；
//       ★ 热循环内零 GetValue/SetValue：eg/β 的逐 token 标量广播改为
//         Gather(全零偏移表 tabZ, srcBaseOffset=t*4) 生成"整条同值向量"，
//         再 Mul（而非 Muls）。既满足形态硬门，又避开 E3 标量可见性。
```

### 2) 删掉标量可见性 fence

修复前：

```cpp
            PipeBarrier<PIPE_ALL>();
            // E3: scalar(GetValue) 读 MTE2 结果必须显式 fence
            SetFlag<HardEvent::MTE2_S>(EV_M2S);
            WaitFlag<HardEvent::MTE2_S>(EV_M2S);
```

修复后：

```cpp
            PipeBarrier<PIPE_ALL>();   // MTE2→V 可见性（无标量读取, 不需 MTE2_S 事件）
```

（`constexpr int32_t EV_M2S = 0;` 随之删除。）

### 3) eg 的逐 token 广播

修复前：

```cpp
                float egv = egT.GetValue(tt);
                if (gm & 6) {
                    if (gm & 1) {
                        Muls(A, A, egv, VK);
                    }
                    Mul(state, state, A, VK);
                } else if (gm & 1) {
                    Muls(state, state, egv, VK);
                }
```

修复后：

```cpp
                // 逐 token 的 eg 广播：全零偏移表 + srcBaseOffset=t*4 →
                // dst[0..VK) 全为 egT[tt]（向量广播，热循环内零 GetValue）
                if (gm & 1) {
                    Gather(egV, egT, tabZ, static_cast<uint32_t>(tt * 4), VK);
                }
                if (gm & 6) {
                    if (gm & 1) {
                        Mul(A, A, egV, VK);
                    }
                    Mul(state, state, A, VK);
                } else if (gm & 1) {
                    Mul(state, state, egV, VK);
                }
```

### 4) β 的逐 token 广播

修复前：

```cpp
                const float bv = beT.GetValue(tt);
                Muls(rV, rV, bv, VS);
```

修复后：

```cpp
                Gather(beV, beT, tabZ, static_cast<uint32_t>(tt * 4), VS);
                Mul(rV, rV, beV, VS);
```

### 5) kernel 入参、UB 缓冲与装载

```cpp
// 入参：在既有的偏移表指针之后插入全零表
    GM_ADDR egG, GM_ADDR betaG, GM_ADDR tabCG, GM_ADDR tabRG, GM_ADDR tabIG,
    GM_ADDR tabZG, GM_ADDR sInitG, GM_ADDR sOutG, GM_ADDR wsG,

// GlobalTensor 声明
    GlobalTensor<uint32_t> gmTabC, gmTabR, gmTabI, gmTabZ;

// 绑定
    gmTabI.SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(tabIG), VSm);
    gmTabZ.SetGlobalBuffer(reinterpret_cast<__gm__ uint32_t*>(tabZG), VK);

// TBuf 声明（新增 tabZBuf / egVBuf / beVBuf）
    TBuf<TPosition::VECCALC> st16Buf, q32Buf, k32Buf, gk32Buf, v32Buf, gv32Buf,
        egBuf, betaBuf, stateBuf, aBuf, bBuf, outBuf, tabCBuf, tabRBuf, tabIBuf,
        tabZBuf, egVBuf, beVBuf, dotBuf, rBuf, tmp2Buf, oBuf;

// InitBuffer（表按 uint32 计，广播向量按 float 计）
    pipe.InitBuffer(tabIBuf, VSm * sizeof(uint32_t));
    pipe.InitBuffer(tabZBuf, VK * sizeof(uint32_t));
    pipe.InitBuffer(egVBuf, VK * sizeof(float));
    pipe.InitBuffer(beVBuf, VSm * sizeof(float));

// LocalTensor 取用
    LocalTensor<uint32_t> tabI = tabIBuf.Get<uint32_t>();
    LocalTensor<uint32_t> tabZ = tabZBuf.Get<uint32_t>();
    LocalTensor<float> egV = egVBuf.Get<float>();
    LocalTensor<float> beV = beVBuf.Get<float>();

// 装载（与其它偏移表同批 DataCopy 进 UB）
    DataCopy(tabI, gmTabI, VSm);
    DataCopy(tabZ, gmTabZ, VK);
```

### 6) host 侧建表与传参

```cpp
    std::vector<int32_t> tc(VKi), tr(VKi), ti(VSm, 0), tz(VKi, 0);
    for (int32_t i = 0; i < VKi; ++i) {
        tc[i] = (i % Ki) * 4;
        tr[i] = (i / Ki) * 4;
    }
    for (int32_t i = 0; i < VSm; ++i) ti[i] = i * 4;
    auto tabC = torch::from_blob(tc.data(), {VKi}, torch::kInt32).to(dev);
    auto tabR = torch::from_blob(tr.data(), {VKi}, torch::kInt32).to(dev);
    auto tabI = torch::from_blob(ti.data(), {VSm}, torch::kInt32).to(dev);
    // 全零偏移表：逐 token 标量广播用（Gather + srcBaseOffset=t*4 → 整条同值向量），
    // 使热循环内不出现 GetValue（形态硬门）
    auto tabZ = torch::from_blob(tz.data(), {VKi}, torch::kInt32).to(dev);
```

```cpp
// host 函数签名
    void* egG, void* betaG, void* tabCG, void* tabRG, void* tabIG, void* tabZG,
    void* sInitG, void* sOutG, void* wsG,

// launch 实参
        tabC.data_ptr(), tabR.data_ptr(), tabI.data_ptr(), tabZ.data_ptr(),
        sInitP.data_ptr(),
```

## 设计决策

- **用“全零偏移表 + `srcBaseOffset`”造同值向量**，而不是引入一个单独的 broadcast API 或改 stride：偏移逐 lane 为 0、基址按 token 步进，硬件 `Gather` 一次就得到“整条都是 src[t]”的向量；这个机制与 kernel 里已有的行/切片广播（常量字节偏移表）同源，UB 语义一致、无需额外同步。
- **`srcBaseOffset` 单位是字节**（`t*4`）：tile 内 token 索引上界 31，而门控表恒按 32 元素装载，越界不成立；这是选 `t*4` 而不是 `t` 的关键。
- **广播向量额外占 UB**：多出两张与 VS/VK 等长的 float 缓冲（本轨迹总量仍在 UB 预算内），换来热循环零标量读与去掉 scalar fence。
- **保留 `Muls` 的唯一位置**：缩放因子属于 launch 参数常量（不是逐元素读），不违反形态硬门，维持 `Muls(oV, oV, scaleF, VS)` 不改。
- 被放弃的候选：把标量塞进 event/同步后再 `GetValue`（形态硬门仍命中）；用 `Duplicate`/`Broadcast` 类接口（与已有埋点不一致、且需要额外的标量入参通道）。

## 系统信息

- 平台：Ascend310P3 / NpuArch 2002 / CANN 9.1.0；8 AIV、纯向量 kernel（无 cube）。
- 构建：工程根 `bash build.sh` → `build/lib<generic>_ops.so`；改 kernel 入参需同步 host 的 `aclrtlaunch_<op>` 实参顺序。
- 目录：`<op>/kernel/<generic>.cpp`（热循环）、`<op>/host/<generic>_host.cpp`（建表/传参）、`<op>/tests/`（精度门脚本 + 确定性探针）。
- 门禁口径：性能验收的形态硬门——热循环内 `GetValue`/`SetValue` 零容忍；per-launch ≤7 次低频标量（如张量尾）允许。

## 性能影响

同一算子内两条路线对比（来源平台：310p）——参照路线是**改造前的上一版 build**，两侧用同一 case 集、同一 `--quick` `Task_Duration` 口径分别跑，取几何平均后相除：改造后约为改造前的 **0.93×**。即“去掉逐 token 标量读”本身没有带来时延收益，甚至略慢——每 token 多出的一次 `Gather` 是纯向量开销。收益在于满足形态硬门并去掉 scalar 可见性依赖，不在时延。**不得**把该相对值外推为其它算子的预期收益。

## 预防

- 写 tile 循环前先定“整条向量乘同一标量”的表达方式：只要标量按 token/hv 变化，就用偏移表 + `Gather`，不要先写 `GetValue` 再回头改。
- 提交前跑静态检查：`grep -n "GetValue\|SetValue"` 的命中行必须全部在循环体外（或落在明确允许的低频尾段），`grep -n "HardEvent::MTE2_S"` 若还在，反问它服务于哪个标量读。
- 形态硬门是静态门，与性能数字无关：性能再好也过不了，所以要在写码阶段就规避而不是在验收阶段补救。

## 验证信号

本卡结论来自一次 310P 上逐 token 递推向量算子的性能验收会话；下列均为该会话工具实测。

- 静态检查（来源平台：310P；证据等级：tool_observed）：改造前 `grep -n "GetValue\|SetValue"` 命中循环体内两处逐 token 读（`egT.GetValue(tt)`、`beT.GetValue(tt)`）与一条 `SetFlag/WaitFlag<MTE2_S>`；改造后同一 grep 只剩注释行与一处 launch 参数常量的 `Muls`，实读为 0。
- 精度回归（来源平台：310P；证据等级：artifact_verified，绑定最终 `build/lib<generic>_ops.so`）：改造后抽检 8 例全部 PASS，且每一例的误差值与改造前**逐位相同**（如 0.000e+00 / 1.907e-06 / 1.526e-05 等成对一致）——说明向量广播与标量广播数值等价。
- 确定性（来源平台：310P；证据等级：artifact_verified）：同一输入双跑，输出位级一致（bit_exact=True，max_diff=0.000e+00）。
- 全量精度门（来源平台：310P；证据等级：artifact_verified）：50/50 通过、N_FAIL=0、NaN/Inf 为 0，其中 11 例位级一致。
- 性能门（来源平台：310P；证据等级：artifact_verified）：13/13 有效用例几何平均远超门限（≥1.0×），逐例最低仍 >1.9×；改造前后同一口径可成对比较（见“性能影响”）。

## 失效边界

- `Gather` 的偏移表必须是 host 侧常量且与 UB 装载长度一致；`srcBaseOffset` 上界必须落在已装载的 32 元素 tile 内，否则会读到相邻 tile 的数据（本轨迹靠“门控表恒按 32 装载”保证，换成动态装载长度即失效）。
- 需要标量参与控制流（条件分支/循环次数）的场景无解，只能按 per-launch 低频设计；本卡不适用。
- 平台范围只到 310P/CANN 9.1.0；其它平台 `Gather` 的 count/偏移语义未在本轨迹验证。
- 未决项：本次改造后几何平均略低于改造前基线（见“性能影响”），未进一步定位是 `Gather` 本身还是 UB 预算变化带来的次生影响；若后续要追回这部分，应优先看 VS 小档（向量做不满一个 repeat）的每 token 开销。
- 未决项：标量广播改为向量广播后，形态硬门的“≤7 次低频标量”上限未被本轨迹的压力用例触发验证（当前实现实读为 0）。

## 坏实践

- **先写 `GetValue` + `Muls`，指望“反正是向量算子”混过形态门**：静态门直接命中，功能再对也判失败。
- **为了过形态门去放宽/绕过检查**（改检查脚本、把标量读挪到看起来不在循环体的宏里）：测试侧放水，不构成解。
- **把 `Muls` 一律删掉**：launch 参数常量用 `Muls` 合法且更省一条 `Gather`；要区分“按 token 变化的标量”与“每 launch 恒定的标量”。
- **改 kernel 入参顺序却漏改 host 实参**：多算子共享 `lib<generic>_ops.so` 时表现为运行期读到错位指针（垃圾/崩溃），编译期不报错。

## 误诊

- 会话中最初认为“E3 标量可见性只要加 `SetFlag/WaitFlag<MTE2_S>` 就安全”，因此把 fence 写进了热循环（推断（非实测），来自该会话的自述）；该写法虽然数值正确，但正是形态硬门判定的对象，属于用错解的阶段。
