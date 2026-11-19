---
type: Guide
title: TorchNPU Profiler的任务依赖、IPC与失败状态
description: 区分任务依赖、三种执行模式、IPC输出和调度器失败收尾。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_task_manager.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_task_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-11T06:58:03Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler的任务依赖、IPC与失败状态

## 范围与执行模式

固定PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。两版_task_manager.py原始字节相同，本文完整读取本地定义，仅静态分析，没有启动线程、进程、管道或真实解析。具体parser内部的算子、通信和内存算法另计。

ConcurrentMode是可按位组合的常量：MAIN_PROCESS=0、SUB_PROCESS=1、PTHREAD=2、NON_BLOCKING=4。实际派发先检查SUB_PROCESS，再PTHREAD，否则当前进程同步执行。NON_BLOCKING只影响管理器何时停止等候，不代表该任务本身用了异步I/O，也不等于任务一定成功。

ConcurrentTask保存name/deps/mode，is_non_blocking按位检查；run抽象合同是返回(ret_code, output)，0成功，其余失败。TaskInfo保存原task、前后任务集合、Init状态、output/handler/管道/接收buffer及时间，未复制全部输入对象。

## 必须先加入依赖，失败不会释放后继

ConcurrentTasksManager默认max_concurrent_num=16。add_task只接受ConcurrentTask，每个依赖name必须已经在task_infos中，否则ValueError；不是等全图添加后再拓扑排序。没有本地重名拒绝：相同name覆盖字典项，不代表已存在的ready项或后继引用也被安全替换。构造并未完整校验并发数量。

初始无依赖任务进入ready队列。调度按max_concurrent_num减当前listening_infos数量计算可启动数，任务开始记Running与time.time。监听数量反映管道任务，当前进程同步任务不占监听槽；不能把16解读为任意运行对象或CPU线程的统一上限。

收到成功返回时记录结束时间和墙钟差，状态Succeed，保存非None输出，移除每个后继的这一前置；所有前置消失才进入ready。失败仅置Failed，不释放后继。一个前置的全部消费者都成功完成后，它的output被清空以节约内存；并非所有成功输出都永远保留。没有消费者的输出不会因这一规则自动清空。

## 三条执行路径的输出并不完全等价

| 模式 | 输入/输出传输 | 失败与清理边界 |
|---|---|---|
| 当前进程 | 从依赖name取output，直接调用run并交完成处理 | run抛Exception由外层manager.run捕获；正常0、False、空列表等非None输出可保留 |
| PTHREAD | 依赖output共享引用；ret_code=0直接写info.output，管道只发返回码 | wrapper没有统一try/finally；正常结束在线程内关写端；不能保证任意异常都发送返回码或执行关闭 |
| SUB_PROCESS | 创建multiprocessing.Process；子进程将stdout.write改为发PRINT消息，flush替为空函数 | 非0码先把output置None；正常通过管道发结果；没有统一捕获run异常并转成约定返回码 |

send_result_to_manager先发OUTPUT再RET_CODE，因为返回码使接收端认为任务完成。**OUTPUT只在if output为真时序列化**，所以子进程返回0、False、空容器会省掉输出消息；线程/当前进程并无同样的真值过滤。不要把缺少输出等同失败，或据成功码认定各模式都保留了相同返回对象。输出pickle序列化、返回码to_bytes及系统调用本身也可能失败，本地没有完整类型/范围规范化。

## 管道协议和退出识别

TLV用4字节大端type、4字节大端length，再接value；RET_CODE值为4字节，OUTPUT为pickle，PRINT为UTF-8。发送函数处理短写；结果函数明确拒绝负fd。接收一次最多os.read 64KiB，BlockingIOError直接返回，拼接旧buffer；不足8字节或value不完整时保留到下次，完整包循环处理，处理完清buffer。PRINT转发到父进程打印，未知type没有本地报错分支；这不是对任意外部文件的通用解码合同。

__add_listening创建pipe，将读端设O_NONBLOCK，并尝试两端0600；OSError/AttributeError后仅重设读端非阻塞，再向epoll注册IN/ET/ERR/HUP。不能说fallback必然设置了全部权限，也不能由注释“64K pipe buffer”宣称所有系统管道容量一致。ERR/HUP触发退出处理：尚未Succeed则Failed，取消监听并关管道；先前失败不转成功。

## 辅助任务不阻塞收尾，不等于全图完成

__listen发现没有监听任务或只剩NON_BLOCKING时，先等5×0.1秒，再检查当前监听任务是否全为non-blocking；成立即可结束调度，不要求所有Init/ready/阻塞于失败依赖的任务成功。其它情况下epoll.poll没有本地timeout。CANNTimelineParser被配置为PTHREAD|NON_BLOCKING的意义需结合这条退出规则，不能只看其内部无限轮询就认定整个解析必永久阻塞。

run捕获Exception打印错误，finally调用finalize并记执行摘要，没有返回汇总成功码。finalize对每个非Succeed任务打印失败并尝试停止：仅仍存活的子进程terminate；线程经ctypes请求注入InterruptedError，没有join或完整资源回滚证明。无handler/已不存活时不一定改成Stopped。clear停止监听任务后清字典/队列并关epoll，析构调用clear；finalize自身并不等价clear。

模块把self.finalize注册为SIGINT处理函数，但该定义只收self，没有显式信号参数适配；本文不通过运行信号实验推定具体结果。进度dot/cursor仅每秒打印，停止时把progress_bar设None，没有在此join进度线程。执行摘要只列已设置execution_time的任务，mode格式化按位测试；MAIN_PROCESS为0，因此该helper显示UNKNOWN，不能用这一字符串证明实际从未走主进程。日志里的耗时是管理墙钟差，不是设备Kernel耗时。

解析入口如何挑任务、何时写analyse.done，见[进程池、解析计划与完成标志](torch_npu_profiler_analysis_pool_parser_plan_and_done_marker.md)；单个任务状态、整体调用返回和输出文件必须分别验收。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_task_manager.py)（1–484行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_task_manager.py)（1–484行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（17–17行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)（16–16行；有界辅助）
