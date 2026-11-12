---
type: Guide
title: Ascend C 编译失败诊断流程：首错固定、签名判读与原配方验证
description: 已有算子工程编译失败时先固定首错与失败现场（工程/完整日志/目标/SKU），按诊断输出定位首错与根因证据；修复沿原构建配方在独占副本验证并读结构化证据字段（transition/built_target/compile_failure_fixed），不只看退出码；同一首错 ≥2 轮修复失败即停滞交接；只接管编译期失败，版本域判定（match/ahead/conflict/mismatch/unknown 五态）按目标 CANN 声明核对。
tags: [task.debugging, topic.compilation, topic.implementation.error_handling]
status: stable
sources:
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/35fffec73cf110d097f1a8a6624b60fd20357bbe/skills/tool-compile-debug/SKILL.md
    role: primary
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/35fffec73cf110d097f1a8a6624b60fd20357bbe/skills/tool-compile-debug/scripts/engine/configs/static_rules.yaml
    role: constraint
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/35fffec73cf110d097f1a8a6624b60fd20357bbe/skills/tool-compile-debug/scripts/engine/configs/error_signatures.yaml
    role: supporting
created_at: "2026-11-05T05:20:00Z"
updated_at: "2026-11-05T05:20:00Z"
platforms: [a2, a3, "950"]
aliases: [编译错误, compile error, 首错, CMake, 链接错误]
---

# Ascend C 编译失败诊断流程：首错固定、签名判读与原配方验证

诊断并修复**已有** Ascend C 自定义算子的编译失败：定位首错、提供修复依据，并沿原构建配方验证修复结果。适用 Linux、CANN ≥9.0.0；纯运行时、精度或性能问题由对应专项处理。

## 诊断流程四步

### 1. 固定失败现场并诊断

先取得工程、完整构建日志、用户目标（接口/功能/目标平台）、构建命令和相关环境。诊断定位**首错**（first error）与已有声明线索：

- 从同一轮构建的日志取首错——后续错误多为首错的级联；
- 保留用户要求的接口、功能和目标，不擅自替换；`--soc` 传准确 SKU（如 `Ascend910B1`、`Ascend950`），不能传 `2201`/`3510` 架构号；
- 诊断与验证报告写到工程外的独立输出目录，安装目录只读。

### 2. 按错误类别分流判读

按症状读必要的错误类别（不默认加载全部）：配置/依赖（CMake `find_package(ASC)` 缺失、`enable_language(ASC)` 未启用、无 `kernel_operator.h` include）、头文件缺失、链接错误（`undefined reference` / `cannot find -l`）、模板/API 不匹配、Tiling/Schema 字段错位、打包（tar 文件名过长：缩短 OpType/Comment/vendor_name；json 未生成：上游构建步骤先修）、编译器内部限制（模板递归深度）。

**版本敏感条目示例**：报错文本含 `include/driver` 路径段时先核对 toolkit 版本——`include/driver/*` 头文件 CANN 9.1.0 起迁移到 `pkg_inc/driver/*`（旧路径 2027-06-30 下线）：≥9.1.0 工具链上报此错是改 include 路径而非缺依赖；9.0 域旧路径仍合法（另有原因）。

### 3. 沿原构建配方验证

修改后在独占副本验证：先读原构建入口（工作目录、全部目标、CMake 选项、build.sh 参数、环境），保留原参数。验证结论读结构化证据字段，**不只看包装脚本退出码**：

- `transition` / `compile_passed` 只说明本次编译通过；`compile_failure_fixed` 还要求适用失败前态、构建目标一致和相关源码覆盖证据；
- 没有适用失败前态时只报告本次结果，变化保持未知；dry-run、超时、缺日志或工具链不可用不算编译成功；
- `contract_check.status=ok` 或 `tolerated` 不能证明语义等价——结合实际声明、调用关系与源码差异核对接口、dtype、shape 与功能；
- 每轮分别保存日志与结果，不覆盖原始失败证据；出现新首错时回喂诊断。

### 4. 停滞时交接并带回证据

同一首错经历 **≥2 轮**「修改→真实编译验证」仍失败且无新证据时，停止同路径重试：先查修改是否进入实际编译单元、是否有影子定义或生成链；工具/构建配方故障先处理（不计为源码修复失败轮次）。交接报告保存已验证事实、尝试及反证、未决假设、缺失证据与下一技能的具体问题——协同处理不是把修复责任转给用户。

## 版本域五态判定

支持范围按 CANN ≥9.0.0 版本域管理（随包登记表核实到 9.1，知识基线覆盖 9.0/9.1）。更高或无法识别的版本只使用有证据支持的建议：

| 状态 | 处置 |
| --- | --- |
| `match` + `supported` | 使用已核版本域内建议，按条目 since/until 过滤 |
| `match` + `ahead` | 版本相关建议仅作参考，逐项核对目标版本声明与真实构建证据；不擅自降级工具链 |
| `match` + `conflict_in_domain` | 披露日志与环境的版本差异，按失败日志版本核对知识 |
| `mismatch` | 查 resolution 区分低于支持下限或保守未核实；保留通用诊断 |
| `unknown` | 保留未知，版本敏感修法先补工具链版本证据 |

## 行为边界

- 只接管编译期失败；编译通过不代表运行时、精度、性能问题已解决；
- 不删除报错功能、不造 stub、不修改 golden、不擅换 target 制造通过；
- 修复涉及 API 语义、参数取值域或版本差异时，核对目标版本官方声明（如 `ascendc-docs-search` 消费流程），不以引擎内置知识库缺项推断「不存在」。

## 与存量知识的分工

单条编译错误的实战处置已有大量存量 runbook（`runbooks/compilation/`，973 张：161001/161002 系列、增量编译旧二进制、AddConfig 变体名等）；本卡是**流程总纲**（首错纪律/验证证据字段/版本域五态/停滞交接），具体错误按 knowledge-query 检索对应存量卡。
