---
type: "Runbook"
title: "ld.lld cannot open _mix_aiv 报错判别"
description: "cube/vec 双段编译下 ld.lld 报 cannot open _mix_aiv_*.o 实为 AIV 编译阶段失败、.o 未生成，需过滤链接噪声定位真实 AIV 编译错误。"
tags: ["task.debugging", "topic.compilation"]
status: stable
sources: []
created_at: "2026-08-17T03:42:43Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# ld.lld cannot open _mix_aiv 报错判别

## 现象

在对 `flash_attn_gqa` arch35 的 cube/vec kernel 做重构（抽取 `FlashAttentionLoop` 公共循环、`FALoopState` 状态控制 struct 统一 cube/vec，不经继承）后，运行固定构建命令：

```
bash build.sh --pkg --ops="flash_attn,flash_attn_metadata" --soc=ascend950
```

构建不以"AIC 编译错误"收尾，而是以链接器 `ld.lld` 的一长串 `cannot open ... .o: No such file or directory` 报错收尾，且**全部缺失对象都是 `_mix_aiv_*.o`**（vec 侧产物），`_mix_aic_*.o` 不在缺失列表中。原始报错（verbatim，trace 内 tool_observed）：

```
[2026-06-16 10:00:14] ld.lld: error: cannot open /mnt/workspace/wangke/ops-transformer_cv/build/binary/ascend950/gen/kernel_meta_FlashAttn_7a9b290f0be5028cb35fc6d409953d1d/kernel_meta/FlashAttn_7a9b290f0be5028cb35fc6d409953d1d_mix_aiv_196864.o: No such file or directory
[2026-06-16 10:00:14] ld.lld: error: cannot open /mnt/workspace/wangke/ops-transformer_cv/build/binary/ascend950/gen/kernel_meta_FlashAttn_7a9b290f0be5028cb35fc6d1d/kernel_meta/FlashAttn_7a9b290f0be5028cb35fc6d409953d1d_mix_aiv_512.o: No such file or directory
[2026-06-16 10:00:14] ld.lld: error: cannot open /mnt/workspace/wangke/ops-transformer_cv/build/binary/ascend950/gen/kernel_meta_FlashAttn_7a9b290f0be5028cb35fc6d409953d1d/kernel_meta/FlashAttn_7a9b290f0be5028cb35fc6d409953d1d_mix_aiv_131584.o: No such file or directory
[2026-06-16 10:00:14] ld.lld: error: cannot open /mnt/workspace/wangke/ops-transformer_cv/build/binary/ascend950/gen/kernel_meta_FlashAttn_7a9b290f0be5028cb35fc6d409953d1d/kernel_meta/FlashAttn_7a9b290f0be5028cb35fc6d409953d1d_mix_aiv_66048.o: No such file or directory
[2026-06-16 10:00:14] ld.lld: error: cannot open /mnt/workspace/wangke/ops-transformer_cv/build/binary/ascend950/gen/kernel_meta_FlashAttn_7a9b290f0be5028cb35fc6d409953d1d/kernel_meta/FlashAttn_7a9b290f0be5028cb35fc6d409953d1d_mix_aiv_197120.o: No such file or directory
```

报错看起来像"链接器找不到文件"的环境/路径问题，但实际是上游 AIV 编译阶段失败、`.o` 根本没生成。

## 适用场景

- **工程形态**：构建/编译（`bash build.sh --pkg --soc=ascend950`），非 kernel 直调、非 aclnn、非评测。
- **API 路径**：CANN 算子仓 `build.sh` + `kernel_meta_FlashAttn_<hash>/` 产物布局；cube/vec 双段编译（AIC 产 `_mix_aic_*.o`、AIV 产 `_mix_aiv_*.o`，最终 ld.lld 链接为 FATBIN）。
- **验证过的平台与 CANN 版本**：ascend950（构建命令 `--soc=ascend950` 实跑，trace 内 tool_observed）；CANN 版本未在 trace 中显式记录。
- **适用粒度**：`platform_wide`（同一 build.sh + 双段编译模型下，所有 cube/vec 算子仓构建均适用，不限定 flash_attn）。
- **路线优先级**：`recommended_fastpath`（命中该报错时首选"过滤链接噪声、定位 AIV 编译错误"判别，而非排查路径/权限/重装工具链）。
- **不适用或未验证场景**：单段编译（无 AIV 阶段）的算子仓不适用；非 ascend950 的 SoC 未验证（见 `## 失效边界`）。

## 判别方法

### 触发特征

`bash build.sh ... --soc=<soc>` 末尾出现一长串 `ld.lld: error: cannot open .../kernel_meta_<Op>_<hash>/kernel_meta/<Op>_<hash>_mix_aiv_*.o: No such file or directory`，且缺失对象**仅 `_mix_aiv_*.o`**（vec 侧）。`_mix_aic_*.o` 不在缺失列表 = AIC（cube）段已编译通过。

### 可执行探针

重跑构建并过滤掉 ld.lld 链接噪声，只留真实编译错误行。trace 内实际使用的探针命令（verbatim，tool_observed）：

```
bash build.sh --pkg --ops="flash_attn,flash_attn_metadata" --soc=ascend950 2>&1 \
  | grep -E "error|Error|ERROR" \
  | grep -v "ld.lld" \
  | grep -v "Traceback" \
  | grep -v "opc_common" \
  | head -40
```

- `grep -v ld.lld` 是关键——它剥掉"cannot open _mix_aiv_*.o"链接噪声，暴露上游 AIV 编译错误（如 `use of undeclared identifier`、`narrowing`、`static_cast` 相关报错）。
- 若该探针无输出，说明真实 AIV 错误行被 build.sh 的 `tail`/`head` 截断或落在 `opc_common`/`Traceback` 过滤分支里；改用不截断的全量重定向 `2>&1 | tee /tmp/build.log` 后再 `grep -v ld.lld` 检索，或直接翻 `build/binary/ascend950/gen/kernel_meta_<Op>_<hash>/*.log`。

### 观测

构建末尾出现 `ld.lld: error: cannot open .../kernel_meta_FlashAttn_<hash>/kernel_meta/FlashAttn_<hash>_mix_aiv_*.o: No such file or directory`，缺失对象仅 `_mix_aiv_*.o`、`_mix_aic_*.o` 不在缺失列表。探针命令实跑（命令执行本身为 tool_observed；其 grep 输出因 trace redaction 未在事件流恢复）。

### 判读（interpretation）

`_mix_aiv_*.o` 缺失 = AIV（vec）编译阶段失败、未产出 `.o`；链接器在 FATBIN 阶段拿不到 vec 产物，于是报 `cannot open`。报错文本本身**不包含**真实 AIV 编译错误（如 undeclared identifier），真实错误在 ld.lld 行**之前**的编译日志里。`_mix_aic_*.o` 不缺失即说明 cube 段已过。

本判别方法在 trace 中两次命中：

- **命中 A**：把 vec.h 中 `maskInfo.maskValue = negativeIntScalar;`（成员标量）改成 `maskInfo.maskValue = *((uint32_t *)&static_cast<T>(-1000000000000.0));`（对标量取地址做 type-pun）后，构建以 `ld.lld cannot open _mix_aiv_*.o` 收尾。探针 grep 当时未滤出真实错误（截断/过滤所致），据相关性推断为取地址 type-pun 触发 AIV 失败（agent_reported 推断，非直接错误原文佐证），改回 `-3.4028235e38F` 浮点字面量与已有 `constexpr uint32_t NEGATIVE_MIN_VALUE_FP32 = 0xFF7FFFFF` 后构建通过。
- **命中 B**：抽取 `FlashAttentionLoop` 公共循环后，vec.h 使用 `sectionNum_`（Init 中 `sectionNum_ = ((__gm__ uint32_t *)fiaMetaData)[0];`、Process 中 `for (uint32_t sectionIdx = 0; sectionIdx < sectionNum_; sectionIdx++)`）但类成员块缺失该声明，构建以 `ld.lld cannot open _mix_aiv_*.o` 收尾。探针 grep 滤出 `sectionNum_` / `GetFDSectionInfo` undeclared（agent_reported 转述，原始 grep tool_result 被 redact），补 `uint32_t sectionNum_ = 0;` 成员声明后构建通过。

## 根因

AscendC 算子仓采用 **cube(AIC) / vec(AIV) 双段独立编译**：两段各自产出 `_mix_aic_*.o` 与 `_mix_aiv_*.o`，再由 `ld.lld` 链接为 FATBIN。当 AIV 段编译失败时，其 `.o` 不生成，链接阶段便以 `cannot open ... _mix_aiv_*.o` 收尾——这一链接报错**掩盖**了上游 AIV 段的真实编译错误（undeclared identifier / narrowing / 不支持的 type-pun 等）。`_mix_aic_*.o` 不缺失即说明 cube 段已过。

> 注：双段编译模型由 verbatim ld.lld 报错中的 `_mix_aiv_*.o` 命名 + "No such file" + agent reasoning 共同推断，非直接 spec 工具输出；AIC/AIV 错误原文在 trace 内被 redact，未逐字恢复。

## 验证信号

来源说明：本知识来自一次 flash_attn_gqa arch35 cube/vec 重构会话；构建命令 `bash build.sh --pkg --ops="flash_attn,flash_attn_metadata" --soc=ascend950` 实跑，ld.lld 链接报错为 verbatim tool_observed 输出，探针命令实跑但 grep 输出被 redact 未恢复。

- 构建末尾出现 `ld.lld: error: cannot open .../kernel_meta_FlashAttn_<hash>/kernel_meta/FlashAttn_<hash>_mix_aiv_*.o: No such file or directory`，且缺失对象仅 `_mix_aiv_*.o`、`_mix_aic_*.o` 不在缺失列表（来源平台:950；证据等级:tool_observed）
- 探针命令 `bash build.sh ... 2>&1 | grep -E "error|Error|ERROR" | grep -v ld.lld | grep -v Traceback | grep -v opc_common | head -40` 实跑（来源平台:950；证据等级:tool_observed）

> 两次命中的真实 AIV 编译错误原文与两次修后的"构建成功"工具输出在 trace 内被 redact，未落入事件流，故不进 `## 验证信号`；`## 判别方法` 中的转述均标注为 agent_reported。

## 坏实践

- 把 `ld.lld: cannot open _mix_aiv_*.o` 当成"路径/权限/工具链未装"去排查——命中 A 中 agent 连续跑了 8 条 grep（按 hash、按 `aiv_1189744_65536`、按 `narrowing|overflow` 等）都滤不出真实错误，因为没先 `grep -v ld.lld` 剥链接噪声。正确第一步是过滤 ld.lld 行、看上游编译日志。
- 对标量做 `*((uint32_t *)&static_cast<T>(-1e12))` 取地址 type-pun 来构造掩码常量——在 AscendC vec kernel 上既触发 scalar 寄存器→内存 spill，又可能直接被 AIV 段编译拒绝。应改用浮点字面量（`-3.4028235e38F`）或已有 `constexpr uint32_t NEGATIVE_MIN_VALUE_FP32 = 0xFF7FFFFF` 位模式常量。

## 误诊

- 命中 A 中 agent 一度把 `ld.lld cannot open _mix_aiv_*.o` 误判为"链接器/环境问题"，连跑 8 条 grep 找真实错误无果；后据"插入取地址 type-pun 前构建通过、插入后失败"的相关性，推断为该 type-pun 触发 AIV 失败（agent_reported，非直接错误原文佐证）。
- 命中 B 中 agent 一度推测 `sectionNum_` 缺失是"预存 bug、与本次重构无关"（agent_reported），但未做 git 历史核验，不能排除是 `FlashAttentionLoop` 抽取时遗漏声明。

## 失效边界

- **未验证，推断可迁移**：a2 / a3 等 SoC 同样使用 `build.sh` + cube/vec 双段编译模型，本判别方法（`grep -v ld.lld` 定位 AIV 编译错误）推断可迁移；但本 trace 仅在 ascend950 实跑构建，a2/a3 未验证，未写入 frontmatter `platforms`。
- 单段编译算子仓（无 AIV 阶段、不产 `_mix_aiv_*.o`）不适用本判别。
- 若构建系统未来改为 AIV 失败即整体 fail-fast、不再进入 ld.lld 链接阶段，本"链接报错掩盖编译错误"判别即失效。
