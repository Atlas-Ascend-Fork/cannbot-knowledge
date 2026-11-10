---
{
  "type": "Runbook",
  "title": "gpt_oss PD 在线分离启动失败诊断：驱动不支持 memfabric 传输引擎，worker 静默秒死且真实崩溃日志在仓库根 res/ 目录",
  "description": "在 16 卡 Atlas A3（Ascend 910_9362）+ CANN 9.2.0 上启动 cann-recipes-infer gpt_oss 在线 PD 分离推理时，prefill/decode worker 子进程在向父进程报告 ready 之前即崩溃，父进程 pipe.recv() 只抛 EOFError，nohup 日志与 log_server.log 均无 worker 崩溃栈。真实崩溃日志位于仓库根 res/<日期>/<角色>/<角色>_node0/log_0.log，内容显示权重加载、warmup、create_config_store 均成功后，HYBM 层报 \"the current version of ascend driver does not support mf!\"，最终 transfer_engine.initialize() 抛 \"Ascend transfer engine init returned -1\"，根因是昇腾驱动版本不支持 memfabric（mf）传输引擎，属环境硬阻塞；mooncake 备选后端因 /etc/hixlep 无端点文件同样不可用。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# gpt_oss PD 在线分离启动失败诊断：驱动不支持 memfabric 传输引擎，worker 静默秒死且真实崩溃日志在仓库根 res/ 目录

## 适用场景

- 框架：cann-recipes-infer（gitcode.com/cann/cann-recipes-infer，master），`executor/scripts/infer.sh --mode online --pd-role prefill/decode` 在线 PD 分离推理，gpt_oss（GPT-OSS 20B/120B，bf16，PD YAML 为 `models/gpt_oss/config/gpt_oss_pd/prefill.yaml` + `decode.yaml`，两侧 world_size=1）。
- 平台：单机 16 卡 Atlas A3（Ascend 910_9362），CANN 9.2.0，Python 3.11.15，torch 2.10.0+cpu，transformers 5.0.0（轨迹内升级）。
- 默认 KV 传输后端为 memfabric（`disagg_config.engine_backend='memfabric'`，store 为首个 prefill leader 的 10002 端口）。
- 缺失信息：昇腾驱动（HDK）具体版本号未采集（轨迹内未读取 driver version.info），memfabric 所需最低驱动版本未知。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${RECIPES_ROOT}` 为cann-recipes-infer 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

在 repo 根目录启动 PD 在线分离（prefill 占 NPU0、decode 占 NPU1）：

```
rm -rf models/gpt_oss/res/*; ASCEND_RT_VISIBLE_DEVICES=0 nohup bash executor/scripts/infer.sh --model gpt_oss --mode online --pd-role prefill > ${LOCAL_PATH_1} 2>&1 &
echo "prefill PID: $!"; sleep 15; ASCEND_RT_VISIBLE_DEVICES=1 nohup bash executor/scripts/infer.sh --model gpt_oss --mode online --pd-role decode > ${LOCAL_PATH_2} 2>&1 &
echo "decode PID: $!"
```

客观观测（单次）：
- router 健康：`GET /health` 返回 `{"status":"ok", "prefill_addrs":["http://192.168.0.x:8001"], "decode_addrs":["http://192.168.0.x:8100"], ...}`；但 `curl http://localhost:8001/health` 与 `:8100/health` 均 not ready，`ps` 只剩 router 进程——prefill/decode worker 均已死亡。
- nohup 日志（pd_prefill.log / pd_decode.log）中父进程栈：`server.py:275 spawn_workers → pipe.recv() → EOFError`，即 worker 在向父进程回送 `"ready"` 之前就退出了。
- `models/gpt_oss/res/20261013/gpt_oss_prefill/prefill_node0/` 下 `log_server.log` 为 0 字节、`log_0.log` 不存在，表面看"两个 worker 均秒死且无日志"。

gpt_oss PD 在线分离启动后 router 健康（/health 返回 prefill:8001/decode:8100 地址），但 prefill/decode worker 子进程在向父进程发送 ready 之前即崩溃，父进程 spawn_workers 在 pipe.recv() 处只抛 EOFError，nohup 日志里没有 worker 自身的崩溃栈。

## 探针与操作

1. 最小化复现 fork 问题（排除 multiprocessing/fork 本身）：

```bash
source /usr/local/Ascend/cann-9.2.0/bin/setenv.bash; python3 - <<'EOF' 2>&1 | tail -8
import multiprocessing as mp
import sys

def child(pipe):
    try:
        import torch
        import torch_npu
        print("child: imports OK", flush=True)
        pipe.send("ready")
    except Exception as e:
        print(f"child failed: {e}", file=sys.stderr, flush=True)
        pipe.send(f"fail: {e}")

if __name__ == "__main__":
    parent, childp = mp.Pipe(duplex=False)
    p = mp.Process(target=child, args=(childp,), daemon=True)
    p.start()
    childp.close()
    try:
        msg = parent.recv()
        print("parent got:", msg)
    except EOFError:
        print("parent got EOFError - child died")
    p.join(5)
    print("exitcode:", p.exitcode)
EOF
```

结果：`child: imports OK / parent got: ready / exitcode: 0`——fork + torch/torch_npu 导入不是死因。

2. 前台直跑 worker 入口（捕获真实崩溃点）：用 `FakePipe` 直接调用 `executor/online/server.py` 的 `worker_main(0, 0, 1, 1, "models/gpt_oss/config/gpt_oss_pd/prefill.yaml", "192.168.0.x", FakePipe(), None, None)`。结果：权重加载、KV cache 初始化、warm-up 全部成功并发送 ready，随后在连续循环处报 `AttributeError: 'Scheduler' object has no attribute 'advance_queues_consensus'`——注意该复现传的 disagg_config=None（disaggregation_mode=NONE，跳过了 KV 传输管理器构建），此报错是复现方式造成的分支差异，不是真实 PD 失败点，勿据此定位。

3. 找真实 worker 日志（关键探针）：`grep -n "WORK_DIR=" executor/scripts/function.sh` + `find <repo根> -name "log_0.log" -newermt "<启动时间>"`：

```
225:    export WORK_DIR="${PARENT_PARENT_DIR}/models/${MODEL_DIR}"
${RECIPES_ROOT}/res/20261013/gpt_oss_decode/decode_node0/log_0.log
${RECIPES_ROOT}/res/20261013/gpt_oss_prefill/prefill_node0/log_0.log
```

真实崩溃日志位于仓库根 res/<日期>/<角色>/<角色>_node0/log_0.log（WorkerManager 的 log_dir 取 os.getcwd()+RES_PATH 相对路径），日志显示权重加载与 warmup 均成功、create_config_store ok 之后 hybm_init 报 "the current version of ascend driver does not support mf!"，最终 transfer_engine.initialize() 抛 "Ascend transfer engine init returned -1"——根因是当前昇腾驱动版本不支持 memfabric（mf）传输引擎，属环境限制而非模型/框架代码缺陷。

## 机制与判别

真实 worker 日志（`res/20261013/gpt_oss_prefill/prefill_node0/log_0.log`，`tail`）中的驱动层错误链：

```
2026-10-13 17:20:52.939399 ERROR [2285510-2285510][HYBM hybm_gva_version.cpp:211 HalGvaPrecheck] Failed to determine driver version
2026-10-13 17:20:52.939423 ERROR [2285510-2285510][HYBM hybm_entry.cpp:96 hybm_init] the current version of ascend driver does not support mf!
2026-10-13 17:20:52.939430 ERROR [2285510-2285510][SMEM smem_trans.cpp:47 smem_trans_init] hybm core init failed: -1
2026-10-13 17:20:52.939436 ERROR [2285510-2285510][ADAPTER pytransfer.cpp:71 Initialize] Failed to init smem_trans, ret=-1
```

随后 Python 层栈终止于：

```
  File "${RECIPES_ROOT}/executor/online/server.py", line 213, in worker_main
    llm = OnlineInference(config, leader_addr)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "${RECIPES_ROOT}/executor/online/online_inference.py", line 81, in __init__
    self.kv_transfer_manager.transfer_engine.initialize()
  File "${RECIPES_ROOT}/executor/online/kv_transfer/transfer_engine.py", line 264, in initialize
    raise RuntimeError(
RuntimeError: Ascend transfer engine init returned -1 (store_url=tcp://192.168.0.x:10002). Check DisaggConfig.store_url.
```

注意该日志前几行还有 `[INFO] ... create_config_store ok (store_url=tcp://192.168.0.x:10002)`——配置存储创建成功，死在传输引擎（HYBM/mf）初始化，而非 store_url 配置错误，报错文案里的 "Check DisaggConfig.store_url" 具有误导性。

mooncake 备选后端同样不可用：worker_main 要求 /etc/hixlep/ub_endpoint_npu_<device>.json 存在，本机 /etc/hixlep 目录为空（ls 无任何端点文件输出），改用 --engine-backend mooncake 也无法在该环境跑通 PD。对应前置条件代码（executor/online/server.py worker_main，经 `sed -n '180,240p'` 摘取）：

```
    if disagg_config is not None and disagg_config.engine_backend == "mooncake":
        # Load the per-device HIXL endpoint configuration for Mooncake.
        raw = os.environ.get("ASCEND_RT_VISIBLE_DEVICES", "")
        devices = [int(x) for x in raw.replace(" ", "").split(",") if x != ""]
        # Fall back to the logical device index when visibility is not set.
        physical_device = devices[local_rank] if devices else local_rank
        local_comm_res_file = os.path.join("/etc/hixlep", f"ub_endpoint_npu_{physical_device}.json")
        try:
            with open(local_comm_res_file) as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Endpoint config file not found: {local_comm_res_file}. "
                "Ensure that the HIXL endpoint configuration is available under /etc/hixlep."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse endpoint config file: {local_comm_res_file}") from e

        os.environ["ASCEND_LOCAL_COMM_RES"] = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
```

日志为什么"消失"：worker 的 `log_0.log` 由 `_redirect_worker_stdio`（os.dup2）写入 `WorkerManager` 的 `log_dir = os.getcwd() + RES_PATH`，RES_PATH 是相对路径（如 `res/20261013/gpt_oss_prefill/prefill_node0`），而 server 进程 cwd 是仓库根，因此落在仓库根 res/ 而不是 `models/gpt_oss/res/`；同时 function.sh 对 server/router 用 `2>&1 > "${WORK_DIR}/${RES_PATH}/log_server.log"` 的重定向顺序（stderr 先指向旧 stdout，再重定向 stdout 到文件），导致 uvicorn/server 的 stderr（含大部分日志）进了 nohup 父日志，`log_server.log` 为空。

fork+import 最小复现正常（子进程 exitcode 0 并回送 ready）、前台直跑 worker（disagg_config=None）可完成权重加载、warmup 并发出 ready，且同时段 NPU 设备端日志除 hybm 外 0 ERROR，说明 NPU 与模型路径本身正常，失败被隔离在 KV 传输引擎初始化一层；在此驱动环境上应快速判定 PD 不可测，不要继续做代码级调试。

## 验证信号

（均为本轨迹单次观测，平台：16 卡 Atlas A3 910_9362 + CANN 9.2.0）

| 信号 | 事件序号 | 说明 |
|---|---|---|
| worker 静默秒死、仅 router 存活 | T 372 | prefill:8001 / decode:8100 not ready |
| 父进程 EOFError（pipe.recv 等 ready 失败） | T 379 | nohup 日志中的父进程栈 |
| 真实 worker 日志定位到仓库根 res/ | T 452 | find 结果给出 log_0.log 实际路径 |
| HYBM hybm_init 不支持 mf 错误链 | T 456 | 驱动层 4 条 ERROR |
| transfer_engine 抛 RuntimeError -1 | T 459 | Python 层终止点 |
| /etc/hixlep 为空（mooncake 无端点） | T 463 | ls 无输出 |
| fork+import 最小复现通过 | T 408 | 排除 fork/导入崩溃 |
| 前台直跑（disagg=None）加载+ready 成功 | T 429 | 排除权重/NPU/模型路径问题 |
| NPU 设备端日志（除 hybm）0 ERROR | T 468 | 失败隔离在传输引擎层 |

## 适用与失效边界

- 适用：cann-recipes-infer 在线 PD 分离 + memfabric 后端 + 驱动不支持 mf 的环境（症状：router 活、worker 秒死、父进程 EOFError、log_server.log 空）。
- 失效/不适用：
  - 若驱动支持 mf，本诊断不适用；此时 EOFError 应优先看仓库根 res/ 的 log_0.log 找其他崩溃栈。
  - 若 /etc/hixlep 下存在 ub_endpoint_npu_*.json，可尝试 `--engine-backend mooncake` 绕过 memfabric（本轨迹未验证 mooncake 可用环境的成功率，属推断）。
  - "升级驱动可恢复"是基于 hybm 错误信息（"the current version of ascend driver does not support mf!"）的合理推断，本轨迹未实测升级后的行为，亦未采集驱动版本号与 memfabric 所需最低版本。
- 停止条件：看到 `hybm_init ... does not support mf!` / `Ascend transfer engine init returned -1` 且 /etc/hixlep 无端点文件，即可判定 PD 在线模式在本机环境硬阻塞，转离线模式或换环境；不要反复重试或改模型代码。
- 诊断顺序建议：先 `find <repo根> -name "log_0.log" -newermt <启动时间>` 找真实 worker 日志，再读驱动层 ERROR，最后才考虑前台直跑复现。
