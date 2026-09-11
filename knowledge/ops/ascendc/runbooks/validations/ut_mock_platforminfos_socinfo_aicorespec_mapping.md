---
type: "Runbook"
title: UT mock PlatFormInfos 控制 AIV 核数与 UB
description: "fe::PlatFormInfos::SetPlatformRes 写 SoCInfo/AICoreSpec/version 三组即可让 PlatformAscendC 的 GetCoreNumAiv/GetCoreMemSize(UB) 返回可控值；sysWs 恒 16MB。"
tags: [task.testing, topic.tiling, topic.architecture]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# UT mock PlatFormInfos 控制 AIV 核数与 UB


## 现象

自定义算子的 tiling 单元测试需要让被测 TilingFunc 在**指定的平台参数**下运行（不同 AIV 核数会改变多核切分/路由判定结果，UB 大小会改变 UB 因子推导），并且 oracle 也要用同一组参数手算期望值。做法是：UT 用 `gert::OpTilingContextBuilder` 组装 TilingContext 时挂一个自构造的 `fe::PlatFormInfos`，向其 `SetPlatformRes` 写 mock 资源，被测实现再经 `platform_ascendc::PlatformAscendC(platformInfo)` 查询。写 oracle 前需要实测确认三件事：**哪些查询受 mock 控制、mock 到哪个键、哪些查询根本不吃 mock**。

探针（`probe_plat.cpp`，链接配方见[host UT 链接 PlatformAscendC 需静态库+dlog](../compilation/platformascendc_host_ut_link_static_tiling_api.md)）以三组核数 48/64/7 运行，输出：

```
GetCoreNumAiv=48
UB size=262144
LibApiWorkSpaceSize=16777216
exit: 0
GetCoreNumAiv=64
UB size=262144
LibApiWorkSpaceSize=16777216
exit: 0
GetCoreNumAiv=7
UB size=262144
LibApiWorkSpaceSize=16777216
exit: 0
```

即 `GetCoreNumAiv` 精确跟随 mock 的核数（48/64/7），UB 固定等于 mock 的 `ub_size=262144`（三组未改它），`GetLibApiWorkSpaceSize` 恒 16777216（16MB，不随核数 mock 变化）。另有两个不经过 PlatFormInfos 的平台常量：`Ops::Base::GetUbBlockSize()` 固定返回 32、`GetCacheLineSize()` 固定返回 256（`pkg_inc/op_common/op_host/util/platform_util.h` 头文件源码，注释 "will using AscendC api later"，无视 context 参数）——oracle 可直接钉死这两个数。

## 适用场景

- 工程形态：算子仓自定义算子的 host 侧 tiling gtest（需要按用例控制 coreNum/ubSize 以覆盖多核切分、UB 容量钳制、少核平台等场景）；任何需要在本进程给 PlatformAscendC 喂平台参数的 host 程序。
- API 路径：`fe::PlatFormInfos::Init()` + `SetPlatformRes("SoCInfo"/"AICoreSpec"/"version", std::map<std::string,std::string>)` + `SetCoreNumByCoreType("AICore")`；查询侧 `platform_ascendc::PlatformAscendC::GetCoreNumAiv()/GetCoreMemSize(CoreMemType::UB, &out)/GetLibApiWorkSpaceSize()`。
- 验证过的平台与 CANN 版本：Ascend 950（mock `Short_SoC_version=Ascend950`、`NpuArch=3510`；编译目标 ascend950）+ CANN 9.0.0-beta.2（与 frontmatter `platforms` 一致）。
- 适用粒度：`platform_wide`（PlatFormInfos/PlatformAscendC 的 mock 语义绑定框架层，不绑定算子）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：真机环境（真实 platform info 由驱动/编译侧注入，不适用 mock 语义）；`GetLibApiWorkSpaceSize` 在其他 SoC version 下的取值未验证（按头文件注释随芯片类型变化）；`GetUbBlockSize/GetCacheLineSize` 若未来 CANN 改为真平台查询（注释预示 "will using AscendC api later"），钉死的 32/256 需重审。

## 根因

（本卡为已验证模式卡，核心是 mock 键 → 查询值的映射机制。）

`PlatformAscendC` 构造时持有 `fe::PlatFormInfos*`，其查询函数从 PlatFormInfos 的资源表取值：`GetCoreNumAiv()` 读 `SoCInfo` 表的 `vector_core_cnt`（`ai_core_cnt`/`cube_core_cnt` 同表其余键）；`GetCoreMemSize(CoreMemType::UB, out)` 读 `AICoreSpec` 表的 `ub_size`（同表还有 l0_a/l0_b/l0_c/l1 尺寸）；`version` 表（`Short_SoC_version`/`NpuArch`）决定按芯片类型查表的量（如 `GetLibApiWorkSpaceSize`）。`SetCoreNumByCoreType("AICore")` 配合 `core_type_list` 完成核类型映射。因此 UT 对三组 `SetPlatformRes` 的写入就是被测实现将读到的全部平台输入——mock 与实现读同一张表，oracle 用同一组数手算即可对齐。而 `GetUbBlockSize/GetCacheLineSize` 是 `op_common` 头文件内联模板、参数标记 `[[maybe_unused]]`、写死返回 32U/256U，与 PlatFormInfos 无关。

## 解决配方

UT 侧的 `InitPlatformInfo`（挂在 TilingContext 的 PlatFormInfos 上，逐字取自事件流——每用例可传不同 coreNum/ubSize）：

```cpp
static void InitPlatformInfo(gert::TilingContext *ctx, int64_t coreNum, int64_t ubSize)
{
    fe::PlatFormInfos *pi = ctx->GetPlatformInfo();
    if (pi == nullptr) {
        return;
    }

    std::map<std::string, std::string> socInfos;
    socInfos["ai_core_cnt"] = std::to_string(coreNum);
    socInfos["cube_core_cnt"] = std::to_string(coreNum / 2);
    socInfos["vector_core_cnt"] = std::to_string(coreNum);
    socInfos["core_type_list"] = "AICore";
    socInfos["l2_size"] = "33554432";
    pi->SetPlatformRes("SoCInfo", socInfos);

    std::map<std::string, std::string> aicoreSpec;
    aicoreSpec["ub_size"] = std::to_string(ubSize);
    aicoreSpec["l0_a_size"] = "65536";
    aicoreSpec["l0_b_size"] = "65536";
    aicoreSpec["l0_c_size"] = "131072";
    aicoreSpec["l1_size"] = "524288";
    pi->SetPlatformRes("AICoreSpec", aicoreSpec);
    pi->SetCoreNumByCoreType("AICore");

    std::map<std::string, std::string> socVersion;
    socVersion["Short_SoC_version"] = "Ascend950";
    socVersion["NpuArch"] = "3510";
    pi->SetPlatformRes("version", socVersion);
}
```

oracle 侧同源查询 sysWs（与被测实现读同一 mock 表，避免硬编码常量随平台漂移）：

```cpp
fe::PlatFormInfos *pi = ctx->GetPlatformInfo();
ASSERT_NE(pi, nullptr);
platform_ascendc::PlatformAscendC plat(pi);
sysWs_ = static_cast<int64_t>(plat.GetLibApiWorkSpaceSize());
```

## 设计决策

- 为何 mock 而非真平台：测试先行阶段需要**确定性**平台输入（少核 7 / 满核 48 / 超配 64、小 UB 触发容量钳制与 TILING_FAIL 路径），真机参数不可枚举；且 host UT 无真机。
- 为何 sysWs 走"UT 与实现各查同一 mock"而不是两边硬编码同一个数：`GetLibApiWorkSpaceSize` 按芯片类型取值（头文件注释），UT 查询保证 mock 的 `version` 表一旦改变，oracle 期望与实现行为同步漂移，比对的是**公式**（`ws[0] = sysWs + usrWs`）而非某个绝对常量。
- 为何 blockSize=32/cacheLineSize=256 直接钉死：头文件源码写死（`return 32U;` / `return 256U;`），无视 context；oracle 钉死并加注释引用出处（该 CANN 版本的平台固定值）。
- 备选与放弃原因：把 ub_size 也按用例变化——已支持（CaseIn 带 ubSize），本卡验证的是"控制通道本身"；mock 更少键（只写 vector_core_cnt/ub_size）——保留参考工程（scale_custom_package UT）的全键形态，避免 PlatformAscendC 内部对缺键的回退路径引入不确定性。
- 当前方案属哪档路线：recommended_fastpath。

## 系统信息

- CANN：`/home/<user>/Ascend/cann-9.0.0-beta.2`；头 `platform/platform_infos_def.h`（fe::PlatFormInfos）、`tiling/platform/platform_ascendc.h`（asc/include）；链接 `${CANN}/x86_64-linux/lib64/libtiling_api.a` + `-lunified_dlog`（详见[host UT 链接 PlatformAscendC 需静态库+dlog](../compilation/platformascendc_host_ut_link_static_tiling_api.md)）。
- 平台常量来源：`pkg_inc/op_common/op_host/util/platform_util.h`（GetUbBlockSize=32U/GetCacheLineSize=256U，源码实测）。
- 目标平台：ascend950（mock Short_SoC_version=Ascend950）。
- 相关文件：探针 `/tmp/opencode/probe_plat.cpp`（映射验证）；UT 源 `operators/<Op>_package/tests/tiling/test_tiling_gtest.cpp`（`InitPlatformInfo` 工程落点）。

## 完整代码

探针完整源码与编译运行命令见[host UT 链接 PlatformAscendC 需静态库+dlog](../compilation/platformascendc_host_ut_link_static_tiling_api.md)卡的「## 完整代码」（同一探针验证两件事：链接链与 mock 语义——本卡关注其输出映射）。UT 工程落点即上文「## 解决配方」的 `InitPlatformInfo` 与 sysWs 查询段，逐字内联完毕。

## 预防

- 写依赖平台参数的 tiling 用例前，先用本卡探针确认"你要控制的量确实受 mock 控制"（本 trace 实测：coreNum/ubSize 可控、sysWs 不可控但恒定、blockSize/cacheLineSize 与平台表无关）。
- mock 的 `version` 表要与你算子的目标 SoC 一致（`Short_SoC_version` 影响按芯片类型取值的查询），不要留空或随便填。
- oracle 与被测实现共享的平台量（sysWs）一律"各自查询同一 mock"，不复制粘贴数值。

## 验证信号

来源说明：以下信号来自本次自定义算子公共 TilingUT 开发会话的平台 mock 探针实测（三组参数独立运行），及 UT 全量运行对 mock 通道的间接验证。

- `GetCoreNumAiv` 受 mock 控制：三组运行分别输出 48/64/7，精确等于传入的 mock 核数（`vector_core_cnt` 与 `ai_core_cnt` 同值）（来源平台：950（host 侧探针，mock version=Ascend950）；证据等级：tool_observed）。
- UB 受 mock 控制：`GetCoreMemSize(CoreMemType::UB)` 输出 262144，等于 mock `AICoreSpec["ub_size"]="262144"`（来源平台：950；证据等级：tool_observed）。
- `GetLibApiWorkSpaceSize` 在三组核数 mock 下恒为 16777216（16MB，本 mock SoC 下的稳定值；不随 SoCInfo 变化）（来源平台：950；证据等级：tool_observed）。
- `GetUbBlockSize`=32、`GetCacheLineSize`=256 为头文件写死常量（`platform_util.h` 源码 `return 32U;`/`return 256U;`，参数 `[[maybe_unused]]`）（来源平台：950；证据等级：tool_observed）。
- 工程化验证：UT 用例以 `InitPlatformInfo` 设 coreNum=7/48 等不同值后，红基线阶段 oracle 期望按对应核数计算（如少核用例期望 usedCoreNum=7），33 用例全部按各自 mock 参数进入字段断言（来源平台：950（host 侧 gtest）；证据等级：tool_observed）。

## 失效边界

- 映射关系（`vector_core_cnt`→GetCoreNumAiv、`AICoreSpec.ub_size`→UB）在本 CANN 版本实测成立；其他版本键名或取值优先级可能变化（未验证，推断需以探针重验）。
- `LibApiWorkSpaceSize=16777216` 只在 mock `Short_SoC_version=Ascend950` 下验证；其他 SoC version 未验证（头文件注释表明该值按芯片类型取）。
- 本卡 mock 的是 host 侧 PlatFormInfos；kernel 侧（真上板）的平台参数注入不经此路径，未验证。

## 坏实践

- 在 oracle 里硬编码 sysWs=16777216：mock version 一旦换芯片即失配，且把"平台查询值"误当"设计常量"。
- 只写 `SoCInfo` 不写 `version` 表：`GetLibApiWorkSpaceSize` 等按芯片类型的查询走默认回退，值可能不是目标 SoC 的。
- 假设 `GetUbBlockSize/GetCacheLineSize` 会随平台变化而特意去 mock 它们：此版本它们无视 context，mock 无效；应直接按 32/256 钉死并注明出处。

## 误诊

- 无（探针三组对照直接给出映射，无误判环节）。


