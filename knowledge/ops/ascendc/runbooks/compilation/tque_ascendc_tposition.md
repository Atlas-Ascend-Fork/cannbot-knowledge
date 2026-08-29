---
type: "Runbook"
title: "TQue 位置参数须用 AscendC::TPosition 枚举"
description: "dav-3510/CANN 9.1.0 上用 ASCEND_TPOSITION_VECIN/VECOUT 宏声明 TQue 模板位置参数，编译报 use of undeclared identifier；判别后改用 AscendC::TPosition::VECIN/VECOUT 作用域枚举可消除该组错误。"
tags: ["task.debugging", "topic.implementation.api_layer.basic_api"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# TQue 位置参数须用 AscendC::TPosition 枚举

## 现象

masked_scale 首版 kernel 在 `AscendC::TQue` 模板位置参数处使用了 `ASCEND_TPOSITION_VECIN` / `ASCEND_TPOSITION_VECOUT` 这类 C 风格宏名。`bash build.sh` 编译期在 `masked_scale_kernel.cpp:176-178` 报：

```
error: use of undeclared identifier 'ASCEND_TPOSITION_VECIN'   // :176, :177
error: use of undeclared identifier 'ASCEND_TPOSITION_VECOUT'  // :178
3 errors generated.
```

build 以非零退出码（Error 2）结束。

## 判别方法

- **触发（trigger）**：`bash build.sh` 退出码非零，编译报 `use of undeclared identifier 'ASCEND_TPOSITION_VECIN'/'ASCEND_TPOSITION_VECOUT'`，错误定位到声明 `TQue` 模板位置参数的行（`masked_scale_kernel.cpp:176-178`）。该症状是 tool_observed 的构建期失败。
- **探针（probe）**：在出错的 `TQue`/`TBuf` 声明行检查位置参数写法——是 `ASCEND_TPOSITION_*` 裸宏标识符，还是 `AscendC::TPosition::VECIN/VECOUT/VECCALC` 作用域枚举；并对照同仓已知可编译算子（如 `csrc/ops/exp/op_kernel/exp_kernel.cpp` 中 `AscendC::TQue<AscendC::TPosition::VECIN, ...>`）确认目标版本的合法写法。可用 `grep -n "TQue\|TPosition\|TPOSITION" <kernel>.cpp` 快速定位。
- **观测（observation）**：将位置参数改为 `AscendC::TPosition::VECIN` / `AscendC::TPosition::VECOUT` 后重编译（`rm -rf build && bash build.sh 2>&1 | grep -i error`），`ASCEND_TPOSITION_*` 的 undeclared identifier 错误组消失，编译推进到下一个与本根因无关的模板推导错误——证明本根因被消除。该观测是 tool_observed 的重建信号。
- **判别（interpretation）**：CANN 9.1.0（dav-3510 tikcfw）的 `AscendC::TQue`/`TBuf` 模板参数要求 `AscendC::TPosition` 作用域枚举值，并不提供 `ASCEND_TPOSITION_VECIN` 这类 C 风格宏别名。使用宏名等于引用一个未声明标识符，故编译器报 undeclared identifier。判别要点：错误信息中出现的标识符形如 `ASCEND_<TYPE>_<VALUE>` 全大写宏风格、且仅出现在 `TQue`/`TBuf` 模板位置参数处，即指向本根因。

## 适用场景

- **工程形态**：ops-direct-invoke-flash Reg kernel，`AscendC::TQue<Position, DEPTH>` / `TBuf<Position, ...>` 声明。
- **API 路径**：`AscendC::TPosition::VECIN/VECOUT/VECCALC` 作用域枚举。
- **验证平台与版本**：Ascend950PR_9579 / dav-3510，CANN 9.1.0。仅此平台实测。
- **适用粒度**：`operator_family`——任何在 dav-3510/CANN 9.1.0 上声明 TQue/TBuf 位置参数的 kernel。
- **路线优先级**：`recommended_fastpath`——直接使用 `AscendC::TPosition::*` 作用域枚举。
- **不适用/未验证场景**：旧版 CANN 若提供 `ASCEND_TPOSITION_*` 宏可能不受影响；a2/a3 未验证，推断可迁移（作用域枚举是 AscendC API 通用约束），迁移前以目标版本头文件为准。

## 验证信号

- 修复前 `bash build.sh` 返回非零退出码（Error 2），编译报 `error: use of undeclared identifier 'ASCEND_TPOSITION_VECIN'`（×2，:176/:177）与 `'ASCEND_TPOSITION_VECOUT'`（×1，:178），共 3 errors generated（来源平台：950；证据等级：tool_observed）
- 位置参数改为 `AscendC::TPosition::VECIN/VECOUT` 后重编译，该组 undeclared identifier 错误消失，编译推进到下一个不相关的模板推导错误，证明本根因被消除（来源平台：950；证据等级：tool_observed）

## 失效边界

- 仅 dav-3510 / CANN 9.1.0 实测；旧版 CANN 是否提供 `ASCEND_TPOSITION_*` 宏未在本 trace 验证，迁移到其他版本前以目标版本头文件为准。
- 本卡只覆盖 TQue 位置参数命名；`TBuf<AscendC::TPosition::VECCALC>` 的位置参数是否同属该枚举未在本 trace 独立运行期验证。
