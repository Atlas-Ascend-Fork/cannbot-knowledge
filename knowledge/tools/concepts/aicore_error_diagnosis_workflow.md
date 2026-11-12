---
type: Concept
title: AI Core Error 系统化诊断工作流（msaicerr/asys 管线六阶段）
description: 昇腾 NPU AI Core Error（含 aivec error）的诊断管线：Phase 0 环境与输入检查 → P1 收集准备 → P2 场景判定与报错行定位（info.txt/PC 修正/llvm-symbolizer 回退链）→ P3 错误类型识别（结论码 101-107）→ P4 单算子复现三态判读 → P5 四证据链汇聚与结论码优先级链（105→107→104→106→102→101→103→0）输出六段式报告。
tags: [task.debugging, topic.implementation.debugging, topic.precision]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-exception-dump/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-exception-dump/references/toolchain-orchestration.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-exception-dump/references/error-line-location.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-exception-dump/references/fix-suggestions.md
    role: supporting
created_at: "2026-11-05T02:40:00Z"
updated_at: "2026-11-05T02:40:00Z"
platforms: [a2, a3, "950"]
aliases: [AI Core Error, aicore error, aivec error, 结论码, EZ9999, 四证据链]
---

# AI Core Error 系统化诊断工作流（msaicerr/asys 管线六阶段）

昇腾 NPU 上发生 AI Core Error（含 aivec error，日志/屏幕出现 `there is an aicore error exception` / `there is an aivec error exception`）时的完整诊断管线。管线与 msaicerr 内置流程逐步对齐：工具自动完成的部分判读其产出，工具缺位的部分（手动回退、构造复现、证据汇聚）由工作流补位。

**执行纪律**：运行于故障发生环境本地（msaicerr 仅支持本地分析）；按 Phase 顺序推进不可跳步；全程只读分析，不修改产品代码；最终诊断报告落盘为 Markdown；执行测试用例前通过 `ASCEND_WORK_PATH` 预设独立运行目录，结束后立即留存日志防冲刷。

## 六阶段概览

| 阶段 | 内容 | 关键产出 |
| --- | --- | --- |
| P0 环境与输入检查 | 本地分析前提（python ≥3.7.5、非 RC 形态）、CANN 环境变量、msaicerr `-e` 环境自检（内置标杆算子） | 环境 PASS/FAIL |
| P1 收集准备 | 故障信息收集（`asys collect --tar="True"` 或直接复用已有收集目录），核对 dump/编译信息/日志三要素 | asys_output 目录 |
| P2 场景判定与报错行定位 | `msaicerr -p` 完整分析（退出码 0 或 101-107 为正常完成）、info.txt 判读、SK（SuperKernel 融合形态）场景判定、报错行定位（PC 修正两引擎、llvm-symbolizer 与 objdump 回退链）、多错误取第一个 | 错误行 + 报错原文 |
| P3 错误类型识别 | 芯片形态判定、高频错误位表、六模块子域分析、AI Core 数量核对 | 结论码候选 |
| P4 单算子复现 | 复现路径决策（有 dump 走解析重建 / 无 dump 手动构造）、tiling 三源重建、越界探测双模式（tail 与 magic）、三态判读（复现成功 / 未复现 / 未运行） | 复现结论 |
| P5 证据链汇聚与修复建议 | 四证据链填写、结论码优先级链、修复建议映射表、升级路径 | 六段式报告 |

## 关键判读点

**结论码 101-107 语义**：101 单算子运行错误、102 内存分配错误、103 硬件错误、104 算子输入数据错误、105 框架未执行 memset 清零、106 算子 args 被踩、107 atomic 算子溢出。

**结论码优先级链**（`get_return_code` 固定 elif 逻辑，先命中先返回）：**105→107→104→106→102→101→103→0**。四个细节：107 在返回码层面实际不可达（其求值前提与 105 互斥）；未运行（NOT_RUN）同样命中 101——用例没跑起来不能认为没有发现问题；flag_check、AI Core 数量不足、current_pc 为 0x0 没有专属返回码，只进结论文案；结论文案链与返回码链排序不同，人工读文案、脚本读返回码时预期差异。

**四证据链框架**：反编译→101（出错在算子源码哪一行）；寄存器解码→103（硬件报了哪一类异常，辅以标杆算子环境自检）；dump 校验→104（输入数据本身是否已脏——NaN/Inf 强证据、0.9 倍值域弱证据须人工确认业务值域后才关联）；单算子复现→105-107（脱离模型能否稳定复现、args 有没有被踩）。某条链数据缺失时明确写「本链失效（原因）」，不允许留空或臆造。

**dump 失败与多错误**：info.txt 出现 `Failed to get dump data of error op!` 即 dump 失败、结论码 102，P4 无 dump 输入可用；SK（融合形态）场景证据链退化，定位不清时建议关闭算子融合后重跑；故障信息含多个 AI Core Error 时工具按日志时间只解析第一个——修复首个错误后仍有报错则重新收集走一轮完整管线。

**越界判读**：以 magic_ret（1 为向前越界、2 为向后越界）与 tail 遍 sync_ret 为主；`Access Memory without OverBoundary` 关键字在当前 msaicerr 代码内没有产出方（属待接通钩子），运行时侧输出仍可作越界佐证，判读时如实注明口径。

## 工具分工与覆盖边界

- 工具用法层（msaicerr CLI 参数、asys collect 用法、退出码 0/1-11 状态码表）见[msaicerr 工具卡](msaicerr_aicore_error_analysis.md)与[asys 工具卡](asys_command_routing_and_constraints.md)；
- 覆盖范围仅 AI Core Error：GE/图编译层问题、算子精度不达标、AI CPU Error、HCCL 等其他错误类型不在本工作流内（说明后指路）；
- msaicerr 暂不支持的算子（MatmulAllReduce 系、AllGatherMatmul 等通信与 Matmul 融合类）的 AI Core Error 无法用本管线分析，转向按错误码走运行时调试或单独复现。
