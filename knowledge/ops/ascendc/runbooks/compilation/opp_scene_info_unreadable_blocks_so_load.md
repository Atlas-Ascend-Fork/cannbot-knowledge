---
type: "Runbook"
title: "opp/scene.info 不可读致包路径渲染为空、零 SO 加载"
description: "共享 CANN 安装里 <opp>/scene.info 权限为 0440 root:root（root 只读）时，容器内非 root 消费者的 GetCurEnvPackageOsAndCpuType 失败，算子包路径渲染成 lib/// 并零 SO 加载；修复是在绝对包根路径上只读 bind 一份字节相同的 scene.info，而不是放进 ASCEND_OPP_PATH 指向的 overlay。自建 opp overlay 会把 GE 翻到旧版路径结构（plugin_manager.cc:644）产生重复层级，是已被证伪的修法。"
tags: ["task.debugging", "topic.implementation.operator_registration", "topic.compilation"]
status: stable
sources: []
created_at: "2026-10-20T22:00:00Z"
updated_at: "2026-10-20T22:00:00Z"
platforms: ["950"]
aliases: ["lib_triple_slash"]
---

# opp/scene.info 不可读致包路径渲染为空、零 SO 加载

## 现象

Ascend950（CANN 9.2.0）共享安装，容器内以 uid 1000 调用自定义算子：算子实现 SO 一个都没被加载，日志里算子包路径渲染成空段：

```text
lib///            # 期望形如 lib/<os>/<cpu>
dlopen liboptiling 次数 0；RegisterOpImplToRegistry 0
```

宿主上核对该安装的元数据文件权限：

```text
-r--r----- 1 root root  <CANN>/opp/scene.info
```

容器内消费者为 uid 1000，读不到这枚文件 ⇒ `GetCurEnvPackageOsAndCpuType` 失败 ⇒ 包路径的 os/cpu 两段为空 ⇒ 按该路径查找的 SO 全部落空。

在**绝对包根路径**上只读 bind 一份字节相同的 `scene.info` 后，os/cpu 段恢复、SO 正常加载。

## 适用场景

- 工程形态：多用户共享的 CANN 安装 + 容器内非 root（uid 1000）消费者；宿主安装目录对消费者只读甚至不可读。
- API 路径：算子包元数据读取 `GetCurEnvPackageOsAndCpuType` → 包路径模板渲染 `lib/<os>/<cpu>` → `dlopen` 实现 SO → `RegisterOpImplToRegistry`。
- 验证过的平台与版本：950（ascend950，容器内 uid 1000 实机执行）+ CANN 9.2.0。
- 适用粒度：platform_wide——与具体算子无关，凡该安装的元数据对消费者不可读即命中。
- 明确不适用/未验证场景：以 root 运行的消费者不命中（能读到原文件）；安装目录整体不可读（不止 `scene.info`）时本修法不足；未验证 `version.info` 单独不可读是否产生同一表现。

## 根因

单句归因：`scene.info` 是算子包路径模板的 os/cpu 两段的数据源，该文件对消费者 uid 不可读时读取函数失败，模板渲染出空段（`lib///`），此后所有按该路径查找的实现 SO 都找不到，表现为"零 SO 加载"而不是"权限错误"。

两条必须分清的事实：

1. **位置敏感**：读取发生在**绝对包根路径**上（`<CANN>/<ver>/opp/scene.info`），不是在 `ASCEND_OPP_PATH` 指向的目录上。把可读副本放进自建 overlay 并用 `ASCEND_OPP_PATH` 指过去**不生效**——加载器根本不从那里读这枚文件。
2. **自建 overlay 有副作用**：以自建 opp overlay 作为修法时，GE 会据此翻到**旧版路径结构**（`plugin_manager.cc:644` 分支），产生形如 `op_proto/built-in/op_proto/` 的重复层级，引入与本根因无关的第二个故障。该修法在本轨迹被证伪，正解是**删除 overlay 依赖**、只保留单枚文件的只读 bind。

## 解决配方

只读 bind 一份**字节相同**的 `scene.info` 到绝对包根路径，不动共享安装、不建 overlay：

```bash
# 1) 取宿主原件的身份（修复后必须仍然相同）
sudo sha256sum <CANN>/<ver>/opp/scene.info      # 记为 $SRC_SHA
# 2) 在自有目录放一份可读副本（内容逐字节相同，权限 0444）
install -m 0444 <可读副本> "$MY/scene.info"
sha256sum "$MY/scene.info"                      # 必须等于 $SRC_SHA
# 3) 容器创建时只读 bind 到【绝对包根路径】
docker create ... \
  --mount "type=bind,src=$MY/scene.info,dst=<CANN>/<ver>/opp/scene.info,readonly" \
  ...
# 4) 点火前在容器内以真实 uid 断言：宿主==容器 同字节
docker exec <cid> sha256sum <CANN>/<ver>/opp/scene.info
```

Before：

```text
lib///；dlopen liboptiling 0 次；RegisterOpImplToRegistry 0
```

After：

```text
os/cpu 段恢复；实现 SO 正常 dlopen 与注册；scene.info 宿主==容器 同哈希
```

## 设计决策

- 为什么只 bind 单枚文件而不是整个 `opp`：单文件只读 bind 是最小干预，既不改共享安装（他人仍在用），也不触发 overlay 的旧版路径分支。
- 为什么坚持字节相同并在容器内复核：替换元数据会改变环境语义；只有"同字节"才能主张"修的是可读性，不是内容"。
- 为什么不改宿主权限：共享安装属他方资产，改权限影响全机其他消费者，且本修法不需要。
- 为什么删掉 overlay 而不是继续修 overlay：overlay 引入的重复层级是**新**故障，排查成本高于其收益；验证表明单文件 bind 已足够。

## 判别方法

- 触发信号：日志里出现 `lib///` 这类空段路径，或"SO 一个都没加载"而没有任何权限/找不到文件的显式报错。
- 探针（按序）：

```bash
# 1) 元数据可读性（以消费者的真实 uid 判定，不要用 root 判定）
docker exec -u 1000 <cid> sh -c 'ls -l <CANN>/<ver>/opp/scene.info; cat <CANN>/<ver>/opp/scene.info >/dev/null && echo READABLE || echo UNREADABLE'
# 2) 渲染后的包路径里 os/cpu 段是否为空
grep -nE "lib/{2,}|lib///" run.log
# 3) 加载计数（0 与非 0 都要记）
grep -c "dlopen.*liboptiling" run.log; grep -c "RegisterOpImplToRegistry" run.log
```

- 判读：以消费者 uid 判定为 UNREADABLE + 路径出现空段 + 加载计数 0 → 即本卡；若以 root 判定为可读就下结论，会错过本根因。

## 验证信号

段首来源说明：以下信号来自同一容器配方的多次对照执行（无 bind / overlay 内放可读副本 / 绝对包根路径只读 bind），平台 950 / ascend950，CANN 9.2.0，容器内 uid 1000。

- 宿主原件权限实测为 `-r--r----- root:root`，消费者 uid 1000；无 bind 时路径渲染为 `lib///`、`dlopen liboptiling` 0 次、`RegisterOpImplToRegistry` 0（来源平台：950；证据等级：tool_observed）。
- 把字节相同的可读副本放进 overlay 并以 `ASCEND_OPP_PATH` 指过去：表现不变——加载器不从该目录读这枚文件，此修法被证伪（来源平台：950；证据等级：tool_observed）。
- 在绝对包根路径只读 bind 后：os/cpu 段恢复、实现 SO 正常加载；点火前以真实 uid 断言宿主与容器内 `scene.info` 同哈希（来源平台：950；证据等级：tool_observed + artifact_verified）。
- 自建 opp overlay 作为修法时出现 `op_proto/built-in/op_proto/` 这类重复层级，定位到 GE 的旧版路径结构分支（`plugin_manager.cc:644`）；删除 overlay 依赖后该故障消失（来源平台：950；证据等级：tool_observed）。
- 反例记录：把 `vendors/config.ini` 改为可读以"顺手修权限"，会把实现加载翻到 vendors 分支并跳过只含原型的 vendor，`dlopen liboptiling` 由 1 降到 0、`RegisterOpImplToRegistry` 由 4 降到 0——权限类改动不是无副作用的（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 本卡只覆盖"`<opp>/scene.info` 对消费者 uid 不可读 → os/cpu 段空 → 零 SO 加载"这一条；`lib///` 还可能由其他元数据缺失或模板层级不匹配造成，需按实际失败函数区分。
- 本轨迹曾把 `GetCurEnvPackageOsAndCpuType`、`GetVersionFromPathWithName`、`GetOppPluginVendors` 三个失败**并成同一个权限机制**处理并因此多跑一轮；三者的失败**模式**才是判别器，不可合并。
- 日志在某一采集级别下没有出现某函数的行，不能证明该函数没有读取相应元数据；"零行"只对该采集级别成立。
- 未验证：`version.info` 单独不可读的表现；root 消费者是否存在其他触发路径；非容器场景（直接以低权限用户在宿主运行）未对照。

**未决项**：

- 加载器读取 `scene.info` 的确切调用点与是否存在可配置的替代数据源未查证。
- `plugin_manager.cc:644` 旧版路径分支的完整触发条件（除自建 overlay 外还有哪些输入会命中）未查证。

## 坏实践

- 以 root 身份 `cat` 元数据文件就断定"可读"——判定必须用消费者的真实 uid。
- 为修这枚文件而自建整个 opp overlay：引入 GE 旧版路径结构与重复层级，制造第二个故障。
- 把可读副本放进 `ASCEND_OPP_PATH` 指向的目录就认为修好了：该位置不被读取。
- 顺手放宽共享安装里其他文件（如 `vendors/config.ini`）的权限：会改变加载分支，本轨迹实测使注册数由 4 降到 0。
- 把"一个 SO 都没加载"直接当作算子实现缺陷去改代码。

## 误诊

- 先按"算子包布局不匹配"方向改包结构；实际应先确认**以消费者 uid 能否读到元数据**。
- 曾以"日志里没有该函数的行"推断它不读元数据，被指出在该采集级别下的缺席不构成证据，结论降级。
- 曾把三个不同函数的失败归并为单一权限机制，据此做了一轮无效修正（overlay 内放可读副本）；真正的判别器是各自的失败模式。
