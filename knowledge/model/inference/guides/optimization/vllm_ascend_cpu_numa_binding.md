---
type: Guide
title: vLLM Ascend CPU 绑定：NUMA、cpuset 与 950 特殊路径
description: 结合CPU绑定中文设计与用户指南，核对全局/隐藏NPU份额、ARM默认和950 cluster/UVB路径，分别验收线程、页面、IRQ及部分生效后的实际状态。
tags:
- task.optimization
- topic.performance.analysis
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/cpu_binding.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/cpu_binding.md
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/cpu_binding.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/cpu_binding.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/cpu_binding.po
  role: supporting
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-10-30T06:59:01Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend CPU 绑定：NUMA、cpuset 与 950 特殊路径

## 适用条件与默认行为

从来源声明的 v0.18.0rc1 起，ARM Ascend 服务器默认 enable_cpu_binding；固定版本可在 additional_config 显式关闭。x86_64 会跳过，不能把 NPU 型号单独作为 CPU 绑定生效证据。收益目标是主机调度局部性、隔离和尾延迟，需保留 cpuset/NUMA 拓扑与基线。

## 三种操作分别核对

taskset/util-linux、procps 与 numactl 支持进程线程绑定和内存迁移。缺 migratepages 只跳过迁移，CPU affinity 仍可成功；不能将远端页面未移动误报整个功能失败。容器不均衡 cpuset 会限制可选核心。IRQ 绑定另需读 /proc/interrupts 和写 smp_affinity，受 irqbalance 干扰；它与线程 affinity 不是一个验证项。

950 由 npu-smi topo 的 NPU→CPU affinity 选 NUMA，缺 affinity 则跳过 worker 绑定。每 worker 用一 CPU cluster，按 lscpu Thread(s) per core 为1/2对应8/16 CPU。UVB host polling 线程使用 NUMA0、排除CPU0且受 cpuset 限制；容器需具备 host PID 可见性。950 不单独绑定 ACL/release 线程，也不做 IRQ 绑定，日志的 skip 属预期。

## 验证、处置与回退

记录可见 NPU、lscpu、npu-smi topo、cpuset、worker/thread affinity 和页面 NUMA 分布；核对日志 worker 列表和 UVB tids。IRQ 路径每 logical NPU 至少5个可用 CPU，950 则需完整 cluster；这些不同规则不能相互替换。权限不足或资源不足先修复部署约束，不能靠日志静默跳过后宣称已优化。

对照保持模型与请求负载一致，比较 host context-switch、调度等待、TTFT/TPOT 尾部和吞吐。需要修改 host irqbalance 时遵守部署环境授权并在退出后恢复；此处仅记录操作条件，本次未修改主机策略。关闭 enable_cpu_binding 可阻止下一次执行该绑定入口；已有亲和性、页面与IRQ状态需分别核对和恢复，不能假定开关会自动回滚。


## 全局设备切片与拓扑分配的差别

配套设计明确 A3 默认 global_slice，950 与 A2 默认 topo_affinity。global_slice 在进程允许的排序 CPU 集合上按主机全局逻辑 NPU 总数切片，不按本服务可见 NPU 数重新平分；隐藏设备仍保留份额，使同一 cpuset 下独立服务不重叠。它不保证 NUMA 局部性，尤其设备与CPU编号跨NUMA时。

topo_affinity 将与 allowed CPUs 相交的隐藏设备也纳入分配；单NUMA池可向下一NUMA扩展，再对相同扩展池分片，不能只看当前visible列表推算份额。950 的 affinity 需恰好属于一个NUMA，缺失、多NUMA或不支持的threads/core布局均可跳过worker绑定；缺 migratepages 只跳过内存迁移。

上游 numa-bind 在该路径映射为 enable_cpu_binding，但 numa-bind-nodes/numa-bind-cpus 不作为该实现的选核来源。验收应读取进程 Cpus_allowed_list、全局逻辑NPU映射与实际worker亲和性，不能把CLI参数原样回显当作已按指定核绑定。


## Worker 接入时点与部分生效

固定 `worker.py` 在 warmup/capture 后检查 enable_cpu_binding，默认来自 AscendConfig 的 True。绑定使用 local_rank 对应的物理设备 ID；Engram `cpu_offload=True` 时仍设置 CPU/thread affinity，但传入 `migrate_memory=False`，避免对已经注册的 HOST_UVA backing 再做进程级迁移。未迁移页面在这个条件下属于明确设计，不是等价于整个绑核关闭。

Worker 用 try/except 捕获整个 bind_cpus 的异常，仅记录 warning 并继续；所以服务启动成功不证明绑定成功。run_all 顺序为建池→角色分配→打印→线程→可选页面迁移→IRQ，错误前可能已经改变部分亲和性。关闭 enable_cpu_binding 只阻止该入口再次执行，不会自动撤销当前进程已有 taskset、页面迁移或宿主机 IRQ/irqbalance 状态；恢复时逐项核对实际状态。

## 设备身份、全局份额与最小资源

DeviceInfo 使用 `npu-smi info -m` 的表头映射 NPU/Chip/Chip Logic ID，缺 Chip Logic ID 时回退 NPU ID；process 表含 Chip 时联合解析，无 Chip 且一块卡映射多个芯片会报错。运行设备来自进程表，并与模块导入时捕获的 ASCEND_RT_VISIBLE_DEVICES 求交；为空会报错，不能按服务参数猜正在使用的逻辑设备。

全局切片以全局逻辑 NPU 总数 G（优先映射，随后 topo/运行列表）和排序去重后的允许 CPU 数 C 计算：q=floor(C/G)，r=C mod G；设备 i 的起点 i*q+min(i,r)，长度 q+[i<r]。i 必须在 [0,G) 内，因此不能把有空洞的任意设备标签直接当作密集切片索引。当前 A3 profile 选 global_slice；隐藏 NPU 保留份额，拓扑编号不对齐 NUMA 时没有局部性保证。

topo 路径将有 cpuset 交集的隐藏设备一并建池。若基础池恰在一个 NUMA，extend_numa 按 `(node+1) % NUMA节点数` 尝试扩展到下一节点；这是编号假设，不是通用的距离最近节点选择。相同扩展 CPU 列表的设备平均分配，余数留给该组最后一个设备；没有通用的任意部分重叠集合消冲突算法，实际 cpuset 仍需检查。完全没有 topo 才回退 global_slice，某个候选与 cpuset 完全冲突则会抛异常。

普通角色分配有 IRQ_CPU_RESERVATION 时至少5 CPU：前2给 SQ/CQ IRQ，末2给 ACL/release，剩余给主进程；无 IRQ reservation 的普通分支至少3 CPU。950 走 cluster 分支，不套用这两个下限。线程级 taskset 失败会抛错，而 migratepages 的返回码未被该调用检查；迁移日志本身不能证明页面已全部移动。

## 950 UVB 与 worker 绑定是两个进度

cluster 路径先调用 bind_uvb_poll_window_threads，再检查 worker topo、cluster 数和有效 threads/core。UVB 池为 cpuset 内 NUMA0 的 CPU，排除CPU0；按 `ps -Te` 中包含 uvb_poll_window_thread 的行枚举线程，不仅限定当前 worker PID。权限/可见性失败按线程 warning 后继续；需核对实际影响的 TID，不能把这一操作理解为只改本 worker。

worker 池按 NUMA 内允许 CPU 排序分组，每组8或16项，由 `8 * threads_per_core` 得来；非完整尾组被舍弃，UVB 池先被排除。候选 NPU 包含与 cpuset 相交的隐藏设备，同 NUMA 内排序 NPU 依次领一个 cluster；列表分组不等于已经验证真实物理 core/SMT sibling 集合。topo 缺失、多NUMA、不支持 threads/core、cluster 不足或可见设备无池时跳过 worker 绑定，但先前 UVB 绑定可能已经发生。因此日志里的“skip worker”不能推出整个流程没有副作用。

## IRQ 与权限边界

有 IRQ reservation 才执行 IRQ 绑定，950 直接跳过。普通路径检查 /proc/irq 可写，并可能停止活动的 irqbalance 服务；按当前逻辑 NPU 查 PCI 信息，双芯卡用 card=i//2、chip=i%2。找到属于该 PCI 的 sq_send_trigger_irq 后，将 CQ IRQ 按 SQ 编号+1推导，再写两项 smp_affinity；不能把这个硬件布局假设推广到未核对的其他设备。

CPU mask 每32位一组，group=floor(cpu/32)，bit=cpu%32，写对应十六进制组。检查两项实际 IRQ、mask 和服务状态，不能只验证 taskset。实现没有对应的自动 irqbalance 重启/亲和性回滚，也可能在后续查 PCI/IRQ 失败前已经停掉服务。

上述增量来自完整阅读 cpu_binding.py 和 Worker/HardwareProfile/AscendConfig 的有关片段；未执行命令、绑核、内存迁移、IRQ 或性能测试。通用 torch_npu CPU_AFFINITY_CONF 和宿主机参数另见[系统调优合同](vllm_ascend_system_tuning_contract.md)，不混成同一个开关。


## 中文PO、工具输出与验收分层

cpu_binding.po的34条有效非空译文已全文与当前英文对照，0obsolete/fuzzy，msgid均精确匹配。它保留ARM默认行为、缺migratepages只跳迁移、950的worker/UVB/IRQ区别和排障信息；不增加310P、x86或其他拓扑的整项支持，也不把上游镜像工具声明当当前容器已安装的事实。

所读execute_command会为子进程设置LC_ALL/LANG/LC_MESSAGES=C，以便解析本地化系统的工具输出；它不是永久改变宿主机语言。helper捕获但不返回stderr，返回解码stdout和退出码，超时后kill再communicate。不同调用点是否检查退出码另行核对；中文文档不表示npu-smi/lscpu表头应按中文解析，也不能从没有stderr文本推断系统操作成功。

验证仍拆成线程亲和性、页面迁移、UVB、worker和IRQ各阶段。对照日志、实际TID/CPU集合及NUMA页面，不以服务ready、某条success或950预期IRQ skip代替整体验收。本文只增加中文与helper证据，没有调用工具、修改taskset/IRQ、迁移页面或改变irqbalance。


## 中文设计与用户指南的重复阅读边界

设计cpu_binding.po的81条有效译文均匹配当前英文，本次新增该来源；用户指南同名PO的34条此前已摄取，本次复读用于交叉核对，不重复计算中文资料覆盖。匹配不表示整段英文已覆盖所有设备边界：设计中通用topo失败回退global_slice的概述，仍要受950特殊cluster路径的跳过条件限制。

固定设计以640个允许CPU、16个全局逻辑NPU为例，每设备分40个CPU；worker0的IRQ为0–1、main为2–37、ACL为38、release为39，worker15对应600–639。它解释global_slice按全局ID保留隐藏设备份额，不是所有A3都有640 CPU/16 NPU或CPU编号天然NUMA对齐的保证。A2示例中两个服务仅见NPU0/NPU2、共享allowed_cpus=144–191，仍共同考虑隐藏同亲和设备而分别分得144–167/168–191；不能按本服务visible数重新均分所有CPU。

950的8/16是按Thread(s) per core推导的允许CPU列表项数，不能直接当8/16个已验证物理core。UVB host线程、worker cluster、内存页和IRQ各自有进度：缺worker topo可能在UVB绑定之后才跳过，缺migratepages只跳页面，950 IRQ skip是其路径预期。绑定日志、服务ready和进程退出都不能证明所有阶段成功或已回滚。

中文表格里的本地化术语不改变工具输出解析契约；实际Cpus_allowed_list、total_logic_npus、NPU/Chip映射和当前语言环境要与源码解析一致。宿主共享UVB线程的可见性及--pid=host不是只读观察开关，irqbalance/IRQ和页面迁移也会改变宿主状态；本卡仅沉淀证据与验收条件，没有执行这些操作。模型算法不由放置策略修改的设计目标，也不替代目标负载的输出和尾延迟对照。
