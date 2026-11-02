---
type: "Runbook"
title: "kernel 配置放错一层致内置同名算子静默顶替候选"
description: "自定义 vendor 的 kernel 清单对（binary_info_config.json + <op_lower>.json）必须位于 op_impl/ai_core/tbe/kernel/config/<soc>/；放到 op_impl/ai_core/tbe/config/<soc>/（该目录只承载 aic-<soc>-ops-info.json）时 ParseDynamicKernelConfig 记 is invalid or does not exist, continue next priority，SelectBin 回落到 SDK 内置同名算子。内置实现正确时全程无错误码、rc=0、输出可信且可能与自建产物逐字节相同，判别的第一信号是 SelectBin 命名的 .o 路径；但 SelectBin 只证明选择阶段命名了哪个对象，要归属设备执行还需同次调用/tiling key 的加载与发射对应。"
tags: ["task.debugging", "topic.implementation.operator_registration", "topic.compilation"]
status: stable
sources: []
created_at: "2026-10-20T22:00:00Z"
updated_at: "2026-10-20T22:00:00Z"
platforms: ["950"]
aliases: ["select_bin_builtin_fallthrough"]
---

# kernel 配置放错一层致内置同名算子静默顶替候选

## 现象

Ascend950（CANN 9.2.0）上以自有 vendor 目录经 `ASCEND_CUSTOM_OPP_PATH` 提供一个与 SDK 内置同名的激活类算子（Heaviside），容器内以 uid 1000 执行 201 例固定分母的 aclnn 调用：

```text
rc=0；201/201 输出文件齐全（0 空文件，ids 0..200 完整）
后续非作者数值判读：PASS 201 / FAIL 0，max_abs_error = 0.0
```

表面全绿，但加载链记录显示**选择阶段命名的 `.o` 全部落在 SDK 内置路径，本 vendor 命中 0 次**。
⚠️ 严格说：这证明的是**选择命中**；「设备上执行的是内置」是由此得出的**强推断**，本卡并未给出同次调用的加载与发射关联证据。开日志可见 kernel 清单查找逐优先级失败：

```text
ParseDynamicKernelConfig ... is invalid or does not exist, continue next priority
```

把 kernel 清单对从 `op_impl/ai_core/tbe/config/<soc>/` 移到 `op_impl/ai_core/tbe/kernel/config/<soc>/` 后，同一入口重跑：`SelectBin` 命名本 vendor 的 `.o` **174 次**、内置 **0 次**，rc 与输出数量不变。

关键放大因素：该 SDK 为 ascend950 内置了同名 Heaviside，其 3 个 kernel 的 tiling-key 哈希与自建产物**相同**（仅多 `_high_performance` 后缀），且两者输出在全部 201 例上**逐字节一致**（IDENTICAL=201/DIFFERENT=0），而两个 `.o` 确属不同构建（7576 B vs 7584 B）。因此数值、返回码、输出数量、文件哈希分布全都不能区分"谁在算"。

## 适用场景

- 工程形态：自有 vendor 目录（非 `.run` 安装）经 `ASCEND_CUSTOM_OPP_PATH` 提供算子实现，容器内非 root 用户执行 aclnn 两段式接口。
- API 路径：vendor kernel 清单查找 → `ParseDynamicKernelConfig` → `SelectBin` 选择 kernel binary → `StreamLaunchKernelV2`。
- 目录语义：`op_impl/ai_core/tbe/config/<soc>/` 只承载算子信息库 `aic-<soc>-ops-info.json`；kernel 二进制清单对 `binary_info_config.json` 与 `<op_lower>.json` 属于 `op_impl/ai_core/tbe/kernel/config/<soc>/`。两者层级不同、互不替代。
- 验证过的平台与版本：950（ascend950，容器内 uid 1000 实机执行）+ CANN 9.2.0。
- 适用粒度：operator_family——任何与 SDK 内置同名、且以手铺 vendor 目录提供 kernel 的算子。
- 明确不适用/未验证场景：`.run` 标准安装路径（安装器自行铺设目录层级）未在本轨迹对照；内置不存在同名算子时本卡的"静默顶替"不成立（清单放错只会表现为找不到实现）；非 ai_core 后端未验证。

## 根因

单句归因：kernel 清单对放在 `tbe/config/<soc>/` 时，`ParseDynamicKernelConfig` 在本 vendor 的 `kernel/config/<soc>/` 下查不到清单，按"continue next priority"继续向下一优先级查找，最终由 SDK 内置同名算子的清单命中，`SelectBin` 据此选中内置 `.o`；vendor 目录与 `load_priority`/`ASCEND_CUSTOM_OPP_PATH` 均配置正确，故不产生任何注册类错误码。

与两张邻接卡的边界：

- [561103 — vendor 未注册 load_priority 不被加载](561103_vendor_load_priority_not_registered.md) 覆盖"vendor 整体未进注册表"；本卡是**已注册但清单层级错**，该卡 失效边界 里"config.ini 已含 vendor 仍 561103，需查 kernel json 与 SOC 匹配"所指的方向之一即本卡，但本卡的实际表现**不是 561103**，而是无错误码。
- [ACLNN 507035 — opType 与内置 ops_legacy 同名碰](aclnn_optype_collision_built_in_ops_legacy_507035.md) 覆盖同名时内置优先命中并因 TilingData 结构不匹配崩 507035；本卡的内置实现与候选**结构兼容且结果正确**，因此不崩、不报错，只是"算的人"换了。该卡的修复（opType 加 Custom 后缀）在本卡场景下非必需：把清单放回正确层级即可让 vendor 命中。

## 解决配方

把 kernel 清单对放到 `kernel/config/<soc>/`，并在铺设后断言与作者原件逐字节一致：

```bash
VENDOR=<vendor_root>                       # 自有 vendor 目录
SOC=ascend950
DST="$VENDOR/op_impl/ai_core/tbe/kernel/config/$SOC"
mkdir -p "$DST"
install -m 0444 <src>/binary_info_config.json "$DST/binary_info_config.json"
install -m 0444 <src>/<op_lower>.json        "$DST/<op_lower>.json"
# 断言：铺设件与原件同字节
sha256sum "$DST/binary_info_config.json" "$DST/<op_lower>.json"
# 对照：算子信息库仍在上一层，不要混放
ls "$VENDOR/op_impl/ai_core/tbe/config/$SOC/aic-$SOC-ops-info.json"
```

Before（清单在 `tbe/config/<soc>/`）：

```text
ParseDynamicKernelConfig ... is invalid or does not exist, continue next priority
SelectBin → <CANN>/opp/built-in/op_impl/ai_core/tbe//kernel/ascend950/.../<Op>_<hash>_high_performance.o
本 vendor .o 命中 0 次
```

After（清单在 `tbe/kernel/config/<soc>/`）：

```text
SelectBin → /<vendor挂载点>/op_impl/ai_core/tbe/kernel/<soc>/<op>/<Op>_<hash>.o   ×174
内置 .o 命中 0 次
```

## 设计决策

- 为什么不改 opType 名：邻接卡的重命名修复针对"同名必然撞内置"；本轨迹证明在清单层级正确时 vendor 可以在同名前提下被正常选中，重命名会同时改变对外接口与调用方，代价大于收益。
- 为什么用 `install -m 0444` 并断言 sha256：候选件的身份是后续判读的根；铺设动作本身若引入改写，整轮结论不可用。
- 为什么不以数值或输出数量作为"候选已执行"的判据：本轨迹里内置与候选的输出在 201 例上逐字节相同，数值无区分力；身份只能来自加载/发射链的记录。

## 判别方法

- 触发信号：rc=0、输出齐全、精度判读通过，但**无法指出设备上加载了哪个 `.o`**；或日志里出现 `continue next priority` 而 vendor 目录看起来文件齐全。
- 探针（按序）：

```bash
# 1) 清单对到底在哪一层
find "$VENDOR/op_impl/ai_core/tbe" -name 'binary_info_config.json' -o -name '<op_lower>.json'

# 2) 开日志抓取选择链（关键三行）
ASCEND_GLOBAL_LOG_LEVEL=1 ASCEND_SLOG_PRINT_TO_STDOUT=1 <entry> 2>&1 | \
  grep -E "ParseDynamicKernelConfig|continue next priority|SelectBin"

# 3) 统计归属：按路径前缀分别计数，而不是只看有没有命中
grep -c "SelectBin.*<vendor挂载点>"      run.log
grep -c "SelectBin.*opp/built-in"        run.log
```

- 判读：`SelectBin` 命中内置 >0 且命中 vendor =0 → **选择阶段命名的是内置**，此时返回码与数值都不能再被当作本 vendor 产物的证据。两者都 >0 需按 tiling-key 分别归属，不可合并计数。
- ⛔ **聚合计数不能逐例归属执行**：174 次选择记录**不覆盖** 201 个案例的全部执行，`StreamLaunchKernelV2` 的 223 次总数是**另一个独立聚合**，两者相乘或并列都不构成逐项关联。
- ⇒ **配方应记四件而不是一件**：①选择（SelectBin）②加载/实际二进制身份（sha256）③发射（同次调用/tiling key 的对应）④消费者。**缺关联的范围只报「选择命中」，不转授 P/F。**

## 验证信号

段首来源说明：以下信号来自同一算子的两次对照执行（清单错层 vs 正确层级），平台 950 / ascend950，CANN 9.2.0，容器内 uid 1000，固定分母 201 例。

- 错层执行：rc=0、201/201 输出、非作者判读 PASS 201/0/0 且 max_abs_error=0.0，但 `SelectBin` 命名内置 `.o` 174 次、vendor 0 次（来源平台：950 实机；证据等级：tool_observed）。
- 正确层级执行：同一入口、同一输入、同一分母，`SelectBin` 命名 vendor `.o` 174 次、内置 0 次；`ParseKernelMetaData` 67、`BuildNewKernel` 38、`StreamLaunchKernelV2` 223（来源平台：950 实机；证据等级：tool_observed）。
- 两次产出的 201 个输出文件**逐字节一致**（IDENTICAL=201 / DIFFERENT=0），而两个 `.o` 大小不同（7576 B / 7584 B）——即"结果相同"与"同一二进制"是两件事（来源平台：950；证据等级：tool_observed）。
- 铺设断言：清单对与作者原件 sha256 相同（`binary_info_config.json`、`<op_lower>.json` 各一枚），vendor 源树未被修改且仍不含 `kernel/config`（来源平台：950；证据等级：artifact_verified）。

## 失效边界

- 本卡只覆盖"kernel 清单对层级错 → `ParseDynamicKernelConfig` 继续下一优先级 → `SelectBin` 选中内置"这一条；清单层级正确仍选中内置时属邻接卡（opType 同名碰）或其他根因。
- "内置与候选输出逐字节一致"是本算子值域（Heaviside 输出仅 0/1 类离散值）下的观察，不可推广为"同名算子一般会给出相同结果"；一般情形下结果可能不同，那反而更容易发现。
- 不能由"出现 `continue next priority`"单独断定本卡：该行是逐优先级查找的常规记录，必须与"vendor 命中 0 次 + 清单实际层级"合看。
- 本轨迹未验证 `.run` 标准安装是否会把清单铺到正确层级（安装器分支未读），也未验证多 vendor 同名时的优先级顺序语义。
- 内置同名算子的存在与否随 CANN 版本变化；9.2.0/ascend950 内置 Heaviside 为本轨迹实测事实，不能外推到其他版本或 soc。

**未决项**：

- `SelectBin` 在"vendor 与内置清单同时可见"时的确切优先级来源（是否同样受 `load_priority` 顺序影响）未查证。
- tiling-key 哈希相同、仅后缀不同（`_high_performance`）的两份 kernel 在选择期是否被视作同一候选集未查证。

## 坏实践

- 以 rc=0 + 输出齐全 + 精度 PASS 作为"我的候选已执行"的证据——这四项在内置顶替时全部成立。
- 只检查"vendor 目录存在且文件齐全"，不检查清单对所在的**层级**。
- 把 `binary_info_config.json`/`<op_lower>.json` 与 `aic-<soc>-ops-info.json` 混放在 `tbe/config/<soc>/`。
- 用输出字节比对来证明是哪份二进制在算；逐字节相同时该比对零区分力。
- 在未取得 `SelectBin` 归属计数前就开始调精度或性能。

## 误诊

- 先按"自建产物有缺陷"的方向修改候选与 vendor 布局，耗掉多轮设备执行；实际应先让一个**已知良好的内置实例**走同一条路径，确认缺陷是否属于自己这一侧。
- 曾把 201/201 输出与 PASS 判读当作产品成功上报，直到核对"哪个二进制被加载"才发现执行者是内置；判据改为先绑定加载链归属、再谈数值。
- 曾尝试自建 opp overlay 让 vendor 被看见，反而把 GE 翻到旧版路径结构（另见 [opp scene.info 不可读致包路径渲染为空](opp_scene_info_unreadable_blocks_so_load.md) 的失效分支），与本卡根因无关。
