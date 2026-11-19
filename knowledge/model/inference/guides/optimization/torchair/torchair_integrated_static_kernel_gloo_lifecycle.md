---
type: Guide
title: 集成TorchAir静态编译：Gloo组与跨rank状态同步
description: 核对集成两版静态编译的节点内Gloo探测、安装状态广播、编译同步和清理边界，定位首轮等待及跳过原因。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/static_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/static_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_backend.py
  role: implementation
created_at: '2026-11-11T02:55:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成TorchAir静态编译：Gloo组与跨rank状态同步

## 固定版本与实际入口

本卡比较TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013中python/torchair/_acl_concrete_graph/static_kernel.py集成实现。整卡平台与部署配套未知，保持draft、空平台。命名空间、单卡dump和去重入口见[两条静态编译实现](torchair_integrated_and_standalone_static_kernel_consumers.md)。

两版先以_is_single_card判断分布式可用性、初始化及world_size；未初始化或取world_size异常时沿单卡选择。多卡且缺少LOCAL_WORLD_SIZE时，compile_static_kernel警告后返回。进入本卡多卡路径还要求launcher的rank布局与节点分块方式一致。

## 自动辅助组的拓扑和两阶段创建

_get_local_gloo_group把LOCAL_WORLD_SIZE转为整数，要求大于零，并要求world_size可整除。以global_rank // local_world_size选本节点，以每个连续rank块创建一组Gloo。每个rank依次对所有node_idx调用new_group，创建顺序需要全体参与者协调。

先创建超时3分钟的probe组，并在本节点probe组barrier。正常完成后逐组尝试销毁probe，再创建超时30分钟的正式组，保存到模块级_local_gloo_groups。这里的超时属于对应进程组，模型整体启动耗时还包含建组、采集和编译等阶段。

probe阶段异常会记录原因并返回None；probe_groups已有返回列表时调用销毁helper。_create_local_gloo_groups_for_nodes内部逐项填本地列表，只在全部创建完后返回。如果new_group在中途抛出，调用者的probe_groups尚未接收该列表，本层清理仅能处理已取得的引用。正式组创建位于probe的except之外，异常恢复需另行核对。

## 缓存安装分支广播的是状态枚举

use_cache_compile严格为字符串"1"时进入安装或编译路线。每个节点的local rank 0核对缓存参数与目录，其他本地rank通过broadcast_object_list取得结果，src按(rank // local_world_size) * local_world_size计算。

| rank 0产生的状态 | 组内后续路径 |
| --- | --- |
| NEED_COMPILE | 转入多卡编译，复用本次已创建的Gloo组。 |
| INSTALLED | 各rank调用reselect，再barrier并尝试销毁本地组。 |
| NEED_SKIP及其他非NEED_COMPILE值 | 走barrier与销毁分支，保留跳过状态。 |

缓存检查涉及CANN版本相等、全局确定性布尔值、目录存在和属主。检查失败时rank 0选择NEED_SKIP。该消费者只比较上述确定性布尔，完整缓存身份仍按精确来源核对。

_find_and_install_run_pkgs找到带run包的ts输出目录后调用_install_run_packages，随后返回INSTALLED。安装helper逐包执行，CalledProcessError在内部转为warning；因此验收时还需要保存每包安装结果。reselect helper也捕获异常并记录warning，不能只用状态枚举或到达barrier确认安装及重选结果。

## 编译分支的通信和清理顺序

每个rank执行dump，dump异常被捕获为warning，随后仍选择目录。各rank通过gather_object把目录送至节点根rank，根rank合并、编译并安装。其后依次是组内barrier、各rank reselect、再次barrier和销毁本地组。

_merge_and_compile_install在没有可用合并目录或static_compile返回False时直接返回；调用者仍按所读顺序进入后续同步。所选链没有额外广播编译成功布尔。数值与安装验收需要同时核对根rank日志、产物及各rank重选结果。

destroy_local_gloo_groups逐组调用destroy_process_group，单组销毁异常被捕获后继续，并在结束时清空模块级列表。上述清理位于正常控制流后段，整条编译流程没有一个包住所有异常的finally。广播、采集、合并或barrier之前抛出的异常如何收束，需要对应故障路径验证。

## 两版一致范围与采用验证

本卡独立比较了13个完整所选函数AST，包括Gloo建组/销毁、安装状态、缓存检查和两条多卡驱动，其语法相同。其它函数只作为所列范围内的消费者核对，完整模块仍有其它版本差异。独立npugraph_ex的显式辅助组与生命周期按[独立包设计合同](npugraph_ex_standalone_design_contracts.md)消费。

记录每节点实际rank成员、LOCAL_WORLD_SIZE、全体new_group顺序、probe/正式组阶段、广播状态及各rank到达的同步点。首次编译成本应分开保存dump、gather、根rank编译/安装和barrier等待。进程组销毁、安装失败、部分rank退出及通信正确性留待部署验收。本次没有构造进程组、读取真实dump或缓存、执行run包、编译、通信或访问设备，没有新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/static_kernel.py)（primary）：22–36, 39–73, 76–104, 132–183, 186–206, 234–288, 291–306, 438–469, 472–495, 515–522, 525–534, 538–558, 562–570, 573–582, 585–591, 606–655, 658–660, 663–670。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/static_kernel.py)（implementation）：19–32, 34–49, 52–60, 73–108, 111–117, 143–191, 194–207, 317–344, 347–367, 386–393, 396–405, 409–429, 433–440, 443–452, 455–461, 476–526, 529–531, 534–541。


## 安装成功登记卸载记录，退出清理由后端finalize触发

集成`_install_run_packages`按run包内容哈希对模块级`_installed_run_pkgs`去重，重复包跳过；单个包安装成功后调用save_uninstall_info，在ASCEND_HOME_PATH的兄弟目录按`*/opp/static_kernel/ai_core/<包名>/uninstall.sh`匹配出脚本路径记入模块级`_uninstall_paths`，并警告进程异常退出时必须手动执行该脚本卸载。安装失败只写warning：不登记卸载、不改状态枚举，INSTALLED仍照常广播。

uninstall_static_kernel遍历记录的脚本逐个执行，失败只写error日志后继续，最后清空列表；两版该函数仅差调试日志f-string与一个未使用赋值。触发方在集成core/_backend.py：finalize_graph_engine按顺序执行dynamo reset、FinalizeGraphEngine、uninstall_static_kernel三步，步骤之间没有try/finally，reset或FinalizeGraphEngine任一步抛错时uninstall_static_kernel在本次退出中不可达；两版该函数逐字节相同并都经atexit注册，atexit路径同样受这条顺序边界约束。差异在信号路径：主线额外注册SIGTERM/SIGINT处理，且注册只发生在主线程；handler先执行finalize_graph_engine，再把同信号处置置为SIG_IGN后向自身重发同信号，重发时该信号已被忽略，这一步既不是重新抛出异常，也不是恢复默认终止，不能据此推断进程必然退出或原始终止语义会被传播；handler内finalize抛错时SIG_IGN与重发同样不可达；发布没有信号注册。因此正常解释器退出（两版）与主线收到SIGTERM/SIGINT都只是尝试执行这条清理链，卸载是否实际落地以reset与FinalizeGraphEngine不抛错为前提；kill -9等其他异常退出不会进入该链，对应安装时的手动卸载警告。独立npugraph_ex的atexit _finalize是另一套实现，见[run包生命周期](npugraph_ex_static_kernel_run_package_lifecycle.md)，两者不互相推导。

## 广播的NEED_SKIP有两个来源

_find_and_install_run_pkgs除缓存检查失败外，还在输出目录存在但没有任何.run文件时返回NEED_SKIP，并警告静态编译可能已失败、建议删除编译缓存重编。两种原因共用同一状态值：收到NEED_SKIP的rank无法从广播值本身区分缓存不匹配还是上次编译失败，定位时结合rank 0日志。

## 版本比较方法

对集成static_kernel.py的15个具名函数做归一化AST比较：14个完全相同，uninstall_static_kernel仅差前述日志写法；finalize_graph_engine两版文本相同。前文13函数AST一致结论维持，重核其中的建组、销毁、安装、重选与两条多卡驱动，并新覆盖卸载登记、单卡/多卡环境判断与入口分发。

## 补充来源

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/core/_backend.py)（implementation）：135–212，finalize、atexit与主线程信号注册。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/core/_backend.py)（implementation）：76–111，finalize与atexit，无信号注册。
- 复核范围（既有来源）：主线static_kernel.py 39–73, 75–131, 132–183, 234–288, 438–496, 515–535, 538–570, 573–606, 606–670, 673–702；发布static_kernel.py 34–108, 347–367, 433–461, 476–541, 544–575。
