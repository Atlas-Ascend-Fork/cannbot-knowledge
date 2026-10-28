---
type: Runbook
title: asc_dump 数据不可信诊断：四项核对与最小验证
description: asc_dump 数据不可信时，先核对地址空间、模板类型、元素数和起始地址；区分有效数据的 32B 对齐估算与每核、单次及 VF 容量约束，再用已知长度的小数组复验。
tags:
- task.debugging
- topic.implementation.debugging
- topic.data_movement.memory_access
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/asc_dump.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/diagnosis_workflow.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/debug_api_quickref.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/platform_matrix.md
  role: constraint
created_at: '2026-10-23T01:40:00Z'
updated_at: '2026-10-23T01:40:00Z'
platforms:
- '950'
- a3
- a2
---

# asc_dump 数据不可信诊断：四项核对与最小验证

`asc_dump` 的输出**首先是观测工具的输出，其次才是被观测数据的证据**。当打印结果与预期不符时，
先要把"观测通道自身错了"排除掉，再谈算子数据通路。错值、截断、来源对不上这三类
"dump 数据不可信"应先排除调用形式问题：地址空间与指针限定符不匹配、模板 `T` 与内存里
实际存储的类型不一致、`dump_size` 超出实际元素数、起始地址取错位置；剩下的一部分才是
容量超限导致的少打印，以及 L1/L0C 等特殊 Buffer 的平台差异。

## 触发条件

- `asc_dump` 打印出的数值与同位置的预期值不符，但同一份数据在别处观测是对的；
- 打印条数少于 `dump_size`、尾部截断，或两次调用之间输出互相污染；
- 多核场景下输出顺序不可读，无法判断某条记录来自哪个 Block、哪个阶段；
- 换用 L1 Buffer / L0C Buffer / 寄存器等非 GM/UB 地址空间后，结果格式与 GM/UB 明显不同。

## 第 1 步：四项核对

对每一条"不可信"的 dump，逐项核对下列四项事实，不要跳过任何一项：

1. **实际地址空间**：确认待打印数据当前真实所在的内存，与调用的接口一一对应。
   `__gm__` 对应 `asc_dump_gm`（或 GM 重载的 `asc_dump`）、`__ubuf__` 对应 `asc_dump_ubuf`、
   `__cbuf__` 对应 `asc_dump_l1buf`（L1）、`__cc__` 对应 `asc_dump_cbuf`（L0C）。
   容易搞反的是 L1 用 `__cbuf__`、L0C 用 `__cc__` 这一对；SIMD VF 寄存器则用 `asc_dump_reg`
   或寄存器参数的 `asc_dump` 重载。用错地址空间的重载，拿到的是另一段内存的内容，看起来
   就像"数据错了"。
2. **模板数据类型**：模板参数 `T` 必须与内存里实际存储的类型一致。类型不匹配时，
   同一段字节会被按错误的宽度和语义解释，表现为量级离谱或规律性的乱码。
3. **元素数量**：`dump_size` 是要打印的**元素个数**（不是字节数）。当 `dump_size` 超过
   `input` 的实际元素个数时会出现未定义问题——这是"不能用 `dump_size` 试探未知长度"的原因。
   先确认地址与长度，再决定打印多少个。
4. **起始地址**：确认 `input` 指向的是你想看的那段数据的开头，而不是偏移后的中间位置、
   上一轮的残留地址或已复用的 buffer。

## 第 2 步：区分对齐估算与各层容量约束

- 非 32 字节对齐的 dump，系统会在末尾自动补齐 padding 以满足对齐；**padding 本身不一定会打印**。
  `ceil(实际元素字节数 / 32) * 32` 只是有效数据经 32B 补齐后的估算，不是含记录管理信息的完整占用。
- 容量约束是多层的：文档分别给出每核 dump 总量默认 30 KB，以及 SIMD 单次调用默认 30 KB；
  单次超限时该次不打印，不能据此推断所有输出都消失。相关配置须按目标 CANN 文档和工程 `acl.json` 确认。
- SIMD VF 中 `asc_dump`、`printf` 与断言共享同一块预留 UB 空间：单条记录必须能完整放进该空间，
  文档列出单条 2 KB 预留空间及每条 72 B 管理信息；不能拿上述 32B 数据估算直接判定是否放得下。
  单条过大时该条不会打印；关闭 reserved UBUF 的配置下接口可能直接不可用。具体口径以[镜像 API 卡](../../../../ops/ascendc/apis/utils_api/tuning_interface/asc_dump.md)与目标版本文档为准。
- 多核同时 dump 时用 `desc` 区分阶段，并对线程 / Block 做适当过滤，否则输出既不可读也容易触顶。

## 第 3 步：平台差异分流（L1 / L0C / BiasTable / Fixpipe）

- `asc_dump` 在公开 tuning 文档中的支持面是 **Ascend 950 SIMD（另有受限的 VF / Buffer 变体）、
  A3 SIMD、A2 SIMD**；310P/310B 与 910/Kirin 在当前文档中不支持。
- **L1 / L0C / BiasTable / Fixpipe 的支持情况与结果格式具有平台差异**，不能按 GM/UB 的经验类推，
  优先查当前 API 文档与示例。
- BiasTable Buffer 与 Fixpipe Buffer 的变体目前只在 Ascend 950 的公开文档中描述；只有在
  **当前产品文档与编译头文件同时确认支持**时才使用这些变体，不要因为编译头文件里存在就当作可用契约。
- Fixpipe Buffer 保存的可能**本身就是硬件参数位域**，打印结果不一定等于上游 L1 中的原始数据。
  因此不能用 Fixpipe 的 dump 结果反推"上游数据被写坏了"。

## 第 4 步：来源归属核对

输出可信与否，一半取决于能不能确认"这条记录是谁打的"。用 `desc`、Block / 线程 ID 与地址空间标签
建立来源关系；多核输出**不要假设全局顺序**，需要顺序时写回带索引的 GM 缓冲区再读回。
单核现象也要确认没有被线程条件过滤掉——漏掉的分支和错误的地址一样，都表现为"值不对"。

## 第 5 步：最小验证顺序（先构造已知值小数组，再扩大）

1. 用**长度明确、值已知、且不跨越边界**的 GM / UB 小数组作为 dump 目标；
2. 先 dump 1 个元素；只有数组实际至少有 32 个元素时才尝试 32 个，确认模板类型与存储类型一致；
3. 先验证 `asc_dump_gm` / `asc_dump_ubuf` 这条主通路，确认无误后再扩展到 L1 / L0C / VF 等特殊 Buffer；
4. 对照 `desc`、Block 和地址空间标签检查输出来源是否与预期一致；
5. 以上链路成立后，才逐步换成真实数据与真实 `dump_size`，一次只放大一个变量。

若只是想查看 `LocalTensor` / `GlobalTensor` 的常规内容，评估公开的 `DumpTensor` 是否更合适；
它不构成 `asc_dump` 的内部实现协议，不要按这个假设去解读 `asc_dump` 的输出格式。

## 验证方式

按"接口能编译 → 语句确实执行 → 输出内容符合预期 → 扩大到真实数据与多核 → 关闭或删除调试代码"
逐级验证。每一步只增加一个变量，出现回归就退回上一级。**不要为了让输出出现而修改算子算法，
或放宽真实的边界检查**——那样得到的"输出正常"没有证据价值。

## 失效边界

- 本卡结论来自 asc-devkit 内核调试 Skill 的参考资料（固定到 40 位 commit）；平台支持面最终以目标
  CANN 版本的公开 API 文档、公开头文件与实际编译验证为准，公开文档与内部资料不一致时以公开文档为准。
- A2/A3 在公开 tuning 文档中"主要为 SIMD"，表示**没有为它们承诺 SIMT 或 VF 变体**，
  不能由产品名称推断所有调用形式都可用；本卡只覆盖上述 SIMD 支持面。
- 本卡只解决"**观测通道不可信**"。若 dump 读数本身可信、而张量内容确实是垃圾值，
  那是算子数据通路问题，走分层探针路线而不是继续调 dump 参数。
- `asc_dump` 只用于调试，不应保留在生产性能路径上；`ASCENDC_DUMP=0` 可关闭 dump（同时也会关闭
  `printf` 与断言）。dump 只提供局部观测，**不能替代功能校验**。
- Super Tensor、type 11/12 或 FIFO 传输实现不是公开调用契约：除非对应能力已进入当前版本公开 API
  文档，不要生成这些宏、TLV 字段或内部 transport 的使用代码。
- `dump_size` 超出实际元素数是未定义问题，本卡不提供"先试探性放大再收敛"的做法。
- 不覆盖 CPU 侧调试手段与算子入图框架自身的日志通道。

## 与相邻卡的分工

- [asc_dump（镜像 API 卡）](../../../../ops/ascendc/apis/utils_api/tuning_interface/asc_dump.md)：
  函数原型、参数语义（`desc` / `dump_size`）、数据类型清单与约束原文归它；本卡不重复签名，
  只回答"输出不可信时按什么顺序判定"。
- [kernel 垃圾值分层探针链](../../../../ops/ascendc/runbooks/runtime/kernel_output_garbage_layered_probe_chain.md)：
  适用于**dump 读数可信但张量内容确实是垃圾值**的场景，用常量写入 / 参数回显 / 回读 / 向量拷贝分层
  定位污染层。与本卡是上下游关系：先用本卡确认观测通道可信，再用探针链定位真正的数据通路故障。
- [Kernel printf 无输出诊断](kernel_printf_no_output_diagnosis.md)：处理"printf 完全没有输出 / 输出不全"，
  重点在平台模式支持、`ASCENDC_DUMP` 开关、FIFO 容量与执行路径；本卡的症状是"**有**输出但数值
  不可信或来源对不上"，两者共享容量核算口径但判定入口不同。
