---
type: Guide
title: Host Runtime 故障排查的证据纪律与错误码分流
description: Host Runtime 排查从同一轮运行中最早失败的 Host 调用开始：返回码只决定检查方向不证明根因；先保存不会重现的证据（首个非零返回值/先核对 err_msg_mode 收集范围再读取保存 aclGetRecentErrMsg/匹配进程线程时间窗的 plog）；连续失败不能只保留最后一个错误（清理成功不能覆盖最早失败）；161 系参数错、561 系 Kernel 包溯源（561003 查找失败/561107 路径缺失/561112 库未加载）各自取证不混淆。
tags: [task.debugging, topic.implementation.error_handling, topic.implementation.resource_lifecycle]
status: stable
sources:
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/749c3c88283397b28472e91c36a402e598121622/skills/tool-runtime-debug/references/error-evidence-and-routing.md
    role: primary
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/749c3c88283397b28472e91c36a402e598121622/skills/tool-runtime-debug/references/kernel-package-provenance.md
    role: supporting
  - resource: https://gitcode.com/yeswecann/all_in_one/blob/35fffec73cf110d097f1a8a6624b60fd20357bbe/skills/tool-runtime-debug/SKILL.md
    role: primary
created_at: "2026-11-05T05:50:00Z"
updated_at: "2026-11-10T03:25:00Z"
platforms: [a2, "950"]
aliases: ["161001", "161002", "561003", "561107", "561112", aclGetRecentErrMsg]
---

# Host Runtime 故障排查的证据纪律与错误码分流

排查 Ascend C Host Runtime 故障（ACL/ACLNN 返回码异常、输出参数错误、Context/Stream/Event 时序可疑、Memcpy 容量或方向不符、异步完成读取异常、资源重复或提前释放、Kernel 包来源可疑）。**从同一轮运行中最早失败的 Host 调用或数据检查开始**；若证据表明最早失败属编译、AI Core、Tiling、纯精度或多卡通信问题，则停止本专项并交接。

## 排查原则

返回码用于缩小检查范围，**不能单独证明根本原因**。先确认初始化配置中的错误收集范围（`err_msg_mode` 线程级/进程级），再固定最早失败调用、原始返回值、按收集范围关联的错误文本和对应日志位置，结合参数、对象关系与时间线决定下一步。同步接口暴露的设备错误必须追溯到更早的异步任务。

## 先保存不会重现的证据

1. 记录第一个非零返回值、API 名、线程、设备、Context、Stream、输入摘要和复现命令；
2. **在失败线程调用其他 ACL 接口之前**读取、复制并保存 `aclGetRecentErrMsg()`——后续调用可能改变最近错误信息，重复读取不能替代保存。**先记录并核对 `err_msg_mode` 初始化配置**：其错误收集范围可配置为进程级，多线程场景下即使从失败线程读取，也不能仅凭读取线程断定错误文本属于该线程——按线程级/进程级范围关联错误文本与日志，避免首错归因错误；
3. 只截取与本次进程、线程、设备、Stream 和时间窗匹配的 plog，保留原始时间戳；
4. 同步点观察到的错误要追溯到队列中最早异常任务，同时保留同步点作为 Host 观察位置；
5. 错误文本、错误码和日志互相矛盾时，不任选其一作为结论——记录冲突并保持 UNRESOLVED。

**连续失败不能只保留最后一个错误**：Event wait 先失败、随后复制成功不能补偿失败的 wait；恢复 Context 先失败、调用者同步又失败是两个独立错误；Host 工作失败后清理成功不能把函数返回改成成功；一处修改后首错消失、出现新数据错误时保存前后证据、针对新失败重新提假设。

## 返回码分流（检查方向）

| 返回码 | 可确认的范围 | 下一步 |
| --- | --- | --- |
| `0` | 本次 API 按接口约定返回成功 | 继续检查输出参数、完成边界和实际数据——成功返回不等于任务完成 |
| `161001` | 必需的指针参数为空 | 对照目标版本算子页检查全部必填参数（描述对象/executor/workspace） |
| `161002` | 参数不满足接口约定 | 检查 dtype、shape、format、属性范围及输入间推导关系 |
| `561003` | Kernel 查找失败 | 先确认进程看到的算子包根目录、vendor 配置、算子名、dtype/format 与目标 SoC；证据明确落在 SEL/TilingKey/Kernel 变体/编译产物时才转 Compile/Tiling，Host Runtime 不猜测应生成哪个变体 |
| `561107` | 算子包路径缺失 | 记录进程实际环境与初始化脚本来源；不为消除错误临时拼接未经确认的路径 |
| `561112` | 二进制 Kernel 库未加载 | 区分「文件不存在」「配置未指向」「依赖无法解析」「进程命中另一份包」；保留加载失败文本和候选路径，**不把重新安装当第一步** |

**修改后输出不变**：依次比较源码编译产物、部署产物和运行时命中证据——内容哈希能证明两个文件相同，不能证明哪个文件被进程加载；没有实际命中证据时结论保持 UNRESOLVED。

## 修复与验证纪律

- 提出一个可被推翻的假设，做最小修改（只替换有误的表达式），按原命令检查数据和完成条件；一次通过后停止扩大修改；**同一补丁至少独立运行三次**才能报告 PASS；
- 不得删除、反转、短路或硬编码验证器、Golden、失败分支，不缩小传输量或比较范围，不用 sleep 替代同步；
- 新证据指向编译、AI Core、Tiling、纯精度或多卡通信时，立即停止 Runtime 修改并重新分诊。

## 与存量知识的分工

Runtime API 的语义与约束见 `runtime/apis/`（515 张）；单点运行时错误的实战处置见 `runbooks/runtime/`（127 张）；本卡是排查流程与证据纪律总纲。Event/MemcpyAsync/资源生命周期等专题知识见[Host Runtime 专题卡](runtime_topics_event_memcpy_lifecycle.md)。
