---
{
  "type": "Runbook",
  "title": "flash26b decode 卡住时用跨节点采样栈定位 all_gather",
  "description": "来源服务 warmup 无进展，本地及另一节点各采样一个 scheduler 进程，forward 线程均阻塞 all_gather。两份栈可定位阻塞层，不能证明 8 节点全部 rank 已到齐，也不能排除未采样进程故障。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# flash26b decode 卡住时用跨节点采样栈定位 all_gather

## 适用场景

多节点 NPU 推理服务无进展且缺乏明确错误日志，需要区分主线程队列等待与 forward 线程集合通信等待。

## 触发与观测

来源看到 16 个 scheduler 进程存活，主线程等待 batch result；本地一个 scheduler 的 forward 线程在 `all_gather_into_tensor`。随后 SSH 到另一节点，选择一个 scheduler_0 PID，得到相同阻塞调用链。未采样所有节点与所有 rank。

## 探针与操作

对已确认 PID 使用 `py-spy dump --pid <scheduler_pid> --nonblocking`。记录节点、rank、线程和采样时间，再核对 `forward_decode_3b → get_attn_ep_group().all_gather(shortcut_mlp_output)` 的通信组。若要判断全组一致性，还需全 rank 的 collective 序号、shape、group 成员和错误日志，不能把两份栈当全组证据。

## 机制与判别

````text
Thread 3499782 (idle): "Thread-5 (forward_thread_func)"
    all_gather_into_tensor (torch/distributed/distributed_c10d.py:4049)
    wrapper (torch/distributed/c10d_logger.py:81)
    all_gather (npu_communicator.py:44)
    all_gather (distributed/parallel_state.py:516)
    forward_decode_3b (npu_longcat_flash.py:318)
    forward (npu_longcat_flash.py:249)
    _call_impl (torch/nn/modules/module.py:1786)
    _wrapped_call_impl (torch/nn/modules/module.py:1775)
    forward (npu_longcat_flash.py:959)
    decorate_context (torch/utils/_contextlib.py:120)
    _call_impl (torch/nn/modules/module.py:1786)
    _wrapped_call_impl (torch/nn/modules/module.py:1775)
    forward (npu_longcat_flash.py:1193)
    runner_fn (npu_graph_runner.py:221)
    decorate_context (torch/utils/_contextlib.py:120)
    _forward_raw (model_runner.py:487)
    forward (model_runner.py:455)
    decorate_context (torch/utils/_contextlib.py:120)
    forward_target_verify (eagle_worker.py:107)
    forward_decode_spec (eagle_worker.py:269)
    forward_batch_speculative_generation (base_spec_worker.py:928)
    forward_thread_func_ (eagle_worker_overlap.py:242)
    decorate_context (torch/utils/_contextlib.py:120)
    forward_thread_func (eagle_worker_overlap.py:199)
    run (threading.py:982)
    _bootstrap_inner (threading.py:1045)
    _bootstrap (threading.py:1002)
````

````text
Thread 3485130 (idle): "MainThread"
    wait (threading.py:327)
    event_loop_overlap_disagg_multi_step_decode (decode.py:1140)
````

这两份采样说明阻塞出现在 MoE 分发前的 EP all_gather 路径，主线程 queue.get 是等待结果的表象。`hccl_wa`/wait 状态不证明根因是对端从未发送，也不能排除网络、某个未采样 rank 提前失败或调用顺序不一致。

## 验证信号

本地和另一节点各一份进程栈支持相同卡点；没有全 rank 到齐记录，也没有修复后运行结果。随后版本回退加 eager 切换引入 `npu_wait_tensor NotImplementedError`，因同时变化两个条件不能单点归因。

## 适用与失效边界

这是阻塞位置诊断，不是死锁根因或修复闭环。MTP draft/verify 调度差异与其他通信路径差异在来源中仍是待验证假设。
