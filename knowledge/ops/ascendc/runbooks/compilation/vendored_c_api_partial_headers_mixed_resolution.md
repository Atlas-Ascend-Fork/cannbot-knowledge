---
type: Runbook
title: 外置 C API 头文件缺依赖导致新旧实现混用
description: 用实际 include trace 检查公共头、实现头与工具头的一致性，识别部分拷贝后的 SDK 回落。
tags: ["task.debugging", "topic.compilation"]
status: draft
sources: []
created_at: "2026-11-11T03:06:30Z"
updated_at: "2026-11-11T04:13:48Z"
platforms: ["950"]
---

# 外置 C API 头文件缺依赖导致新旧实现混用

## 适用场景

只拷贝较新的 C API 公共头，并不构成完整的头文件升级。其内部实现头与工具依赖若缺失，编译可能回落到安装目录中的另一版本，表现为模板、宏或类型不匹配。

## 症状与记录

CANN 9.3 相关工程试用中，外置 C API 的 public include、impl 与 utility 依赖不完整，引发混合解析。旧编译器还可能不认识新头使用的 `__int4x2`、`vector_bf16` 等内建类型。补齐依赖与编译器支持检查是两件事，不能用前者证明后者兼容。

## 定位与处理

1. 保存实际编译命令与 include trace，逐个确认入口公共头、实现头和工具头的实际路径。
2. 用同一受控版本恢复完整依赖与原有相对目录，排除同名文件被 SDK 中旧版本抢先命中。
3. 在受测 Bisheng 搜索规则下，引号 include 可检查 `-iquote` 与 `-I` 的顺序；`-iquote` 不处理所有尖括号 include，也不补齐缺失的编译器内建类型。
4. 依赖一致后，单独编译最小 dtype 探针。若仍缺内建类型，应选择兼容的头文件与编译器组合，不伪造类型定义压过诊断。

## 验证边界

用干净构建确认实际头来源，并重编译真实 kernel；增量构建成功不能证明依赖闭合。草稿：具体头文件快照与工具链组合尚待复核，不声明任意新头可被旧 CANN 使用。

相关：[头文件、宏与链接上下文](../../guides/environments/blaze_headers_macros_and_link_contexts.md)提供一般诊断边界；本卡聚焦 C API 部分依赖回落到另一副本的症状。
