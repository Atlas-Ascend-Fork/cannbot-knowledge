---
{
  "type": "Runbook",
  "title": "FSDP 初始化 HCCL error 4：原训练设备映射观测与独立绑卡测试的边界",
  "description": "Qwen9B 四卡初始化日志仅给出 RankID:3/Device:0；可见设备残留是待核实线索，独立 set_device 探针不能证明原训练绑定或根因已修复。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# FSDP 初始化 HCCL error 4：原训练设备映射观测与独立绑卡测试的边界

## 适用场景

- 平台范围依据：source 0 seq 325的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 框架/模型链路：torchtitan-npu Qwen9B SFT（qwen36_ascendc 训练接口），单机4进程、CP=2/FSDP=2的启动案例。
- 平台/版本：用户训练日志记录 Ascend950PR_9579，CANN 9.2.0-beta.2，HCCL；设备容量日志见 source 0 seq 12/325。
- 目标：在 HCCL/FSDP 初始化失败时，核对原进程的可见设备和实际绑定，而非由逻辑设备号或独立测试推定根因。

## 触发与观测

用户粘贴的实际日志（source 0 seq 325，user_reported）在 `init_weights` 的 FSDP/DTensor `all_gather` 路径报：

```text
HCCL function error:
hcclCommInitRootInfoConfig(...)
error code is 4
RankID:3
Device:0
```

这里只记录了该 rank 的逻辑设备号，不能推出所有 rank 都绑定逻辑0，更不能在没有各进程可见列表和宿主机映射时断言它们占用同一物理卡。来源没有读取到 `ASCEND_RT_VISIBLE_DEVICES` 的实际值。

## 探针与操作

### 原训练进程中的观测建议（本次未执行）

在原训练入口已有绑卡逻辑执行后、初始化 HCCL 之前插入日志。诊断日志不调用 `set_device` 替换原绑定，也不另启进程冒充原训练状态：

```python
import os
import socket
import torch
import torch_npu

print({
    "stage": "after_existing_binding_before_hccl",
    "host": socket.gethostname(),
    "rank": os.environ.get("RANK"),
    "local_rank": os.environ.get("LOCAL_RANK"),
    "world_size": os.environ.get("WORLD_SIZE"),
    "ASCEND_RT_VISIBLE_DEVICES": os.environ.get("ASCEND_RT_VISIBLE_DEVICES"),
    "ASCEND_VISIBLE_DEVICES": os.environ.get("ASCEND_VISIBLE_DEVICES"),
    "logical_device": torch.npu.current_device(),
}, flush=True)
```

将各 rank 的日志与部署侧的容器设备映射、宿主机 NPU/Chip ID、PCI Bus ID 或其他唯一物理标识对照记录。逻辑序号及设备型号名称本身都不能代替唯一物理标识；没有这份映射就不能由多个 `Device:0` 判断物理卡冲突。

### 独立映射测试（来源中的建议，未见执行结果）

source 0 seq 332 是助手建议，曾怀疑单卡调试的可见设备配置残留，并给出主动 `set_device(local_rank)` 的独立脚本。它测试指定 launcher/可见列表能否按逻辑序号绑卡，不观测原训练进程绑定前后的状态：

```bash
cat >/tmp/check_npu_rank.py <<'PY_PROBE'
import os
import torch
import torch_npu

local_rank = int(os.environ["LOCAL_RANK"])
torch.npu.set_device(local_rank)
print(
    "RANK=", os.environ.get("RANK"),
    "LOCAL_RANK=", local_rank,
    "WORLD_SIZE=", os.environ.get("WORLD_SIZE"),
    "DEVICE=", torch.npu.current_device(),
    flush=True,
)
PY_PROBE
ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
    torchrun --standalone --nproc_per_node=4 /tmp/check_npu_rank.py
```

只有共享相同可见列表、每进程一设备且按 `LOCAL_RANK` 显式绑定的这个测试，才预期 local rank n 对应逻辑设备 n。若部署给每个进程单独暴露一张不同物理卡，各进程均显示逻辑0也可能正确。独立测试结果不能证明原训练入口采用了相同绑定。

若原训练日志与部署映射确证配置残留，再按实际设备分配修正可见列表，并核对脚本内部 export 是否覆盖外部设置。来源中建议的 `0,1,2,3`/unset 是该案例的候选方案，不是已读取的原配置，也没有已完成的修复验证。

## 机制与判别

- `hcclCommInitRootInfoConfig error 4` 定位到通信器初始化失败；`RankID:3/Device:0` 只是一条设备映射排查线索，不能单独锁定可见设备变量。
- 判断物理卡冲突需要共同核对 rank/local rank、各自可见列表、已有绑卡逻辑和部署物理映射。进程内逻辑编号相同，不等于物理设备相同。
- 后续失败点变化也不能替代配置更改和因果验证。source 0 seq 332/344 都是助手分析，不作为工具观测或用户已完成修复的报告。

## 验证信号

- source 0 seq 325：用户日志报告初始化阶段 HCCL error 4。
- source 0 seq 339：下一轮用户日志在 `trunc_normal_`/`mask.any` 的 copy-stream 同步路径报 107020、1866s 超时，仍在训练开始前失败。
- 未见原训练进程的可见列表/物理设备映射记录，未见独立探针运行结果，也不能从后一轮日志确认采纳了哪项建议或 HCCL 根因已经修复。

## 适用与失效边界

- 仅本例单机、无其他并行维度的 CP2/FSDP2 配置对应4个进程。不能把 `NPROC_PER_NODE=CP×FSDP` 当作一般规则；多机或额外并行维度须按总进程拓扑及各组定义计算每节点进程数。
- `unset` 可能被脚本内部 export 覆盖，容器也可能为每个 rank 提供不同的可见列表；须核对实际启动实例。
- 本卡提供诊断顺序与未执行的探针建议，不声称可见设备残留已证实或训练已恢复。

## 附：断言存档

- 本例 HCCL 初始化 error4 与 RankID:3/Device:0 来自用户日志；单卡可见配置残留仅为助手提出的待核实假设。
- 独立 set_device 测试不能验证原训练绑定；后一轮参数初始化超时也不能证明前述根因或修复成功。
