---
{
  "type": "Runbook",
  "title": "torch_npu.profiler（Ascend PyTorch Profiler）同时采集 Python CPU 调用栈与 CANN 算子明细的标准模板及实测产物验证",
  "description": "按环境内 torch_npu 2.10.0.post4 的 profile() 签名与 _ExperimentalConfig 字段逐一核对后产出标准模板 prof_template.py：activities 同时含 CPU+NPU，with_stack/with_modules 记 Python 栈，experimental_config（profiler_level=Level1、aic_metrics=PipeUtilization、export_type=Text）出 CANN 明细，schedule + prof.step() 控窗，预热与首次 capture 放窗口外；落盘 ${LOCAL_PATH_1} 并在 sglang-npu-verify 容器（910B3）实测跑通：tensorboard_trace_handler 产物同时含 device_0（CANN 侧）与 FRAMEWORK/torch.python_tracer_func（Python 栈），并实测确认 op_attr 仅在 export_type=Db 下生效、warmup=0 的告警属预期。",
  "tags": [
    "task.implementation",
    "topic.model_serving",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "910"
  ]
}
---

# torch_npu.profiler（Ascend PyTorch Profiler）同时采集 Python CPU 调用栈与 CANN 算子明细的标准模板及实测产物验证

## 适用场景

- 框架/版本：torch_npu 2.10.0.post4 的 `torch_npu.profiler`（Ascend PyTorch Profiler），torch 2.10.0+cpu；在 `sglang-npu-verify` 容器（CANN 9.1.0 组件集）内实测。
- 平台：Ascend 910B3 单卡（NPU Id 7，`/dev/davinci7`）。
- 目标与工作负载：单卡模型推理/微基准的 profiling——同时拿到 Python CPU 调用栈（`torch.python_tracer_func`）与 CANN 侧算子/核明细（`device_0`），用于头开销定位、replay 路径分析等。模板文件落盘为 `${LOCAL_PATH_1}`（内置一个 Linear-ReLU-Sigmoid DemoModel，可替换为任意 nn.Module）。
- 缺失信息：多卡（每 rank 子目录）未实测；export_type=Db 的产物解析未做。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

路径补充：`${PROFILER_OUTPUT_ROOT}` 为本地 profiler 产物根，实际运行目录名由采集工具生成。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

触发（用户需求，事件 1071/1086）："我要个prof写法的标准模版"，且要求 prof 上同时有 python cpu 和 cann 堆栈；随后要求"落盘这个标准脚本放到${LOCAL_PATH_2}"。

观测（容器内实测，事件 1094/1098）：

- 首跑（`--steps 5 --warmup 3 --with-stack`）出现两条告警：`profiler.py: op_attr switch is invalid with export type set as text.` 与 `profiler.py: Profiler won't be using warmup, this can skew profiler results`。
- 产物目录结构（事件 1098）同时含 CANN 侧与 Python 栈两侧数据：

```
${PROFILER_OUTPUT_ROOT}/fca3ca372f6841a2a908f2a75196a20a_335480_20261016092255856_ascend_pt/PROF_000001_20261016092255898_00335480IHRLMPGL/device_0
${PROFILER_OUTPUT_ROOT}/fca3ca372f6841a2a908f2a75196a20a_335480_20261016092255856_ascend_pt/PROF_000001_20261016092255898_00335480IHRLMPGL/host
${PROFILER_OUTPUT_ROOT}/fca3ca372f6841a2a908f2a75196a20a_335480_20261016092255856_ascend_pt/FRAMEWORK/torch.python_tracer_func
```

## 探针与操作

探针（API 核对，事件 1074/1075/1078/1079）：容器内 `inspect.signature` 逐一核对——`profile(activities, schedule, on_trace_ready, record_shapes, profile_memory, with_stack, with_flops, with_modules, experimental_config, ...)`；`schedule(wait, active, warmup=0, repeat=0, skip_first=0)`；`_ExperimentalConfig(profiler_level, aic_metrics, l2_cache, msprof_tx, mstx, data_simplification, record_op_args, op_attr, gc_detect_threshold, export_type, host_sys, ...)`；`ProfilerActivity`=[CPU, NPU]、`AiCMetrics` 含 PipeUtilization/ArithmeticUtilization/Memory 等、`ProfilerLevel`=[Level0, Level1, Level2]、`ExportType`=[Db, Text]。

操作（模板核心代码，锚点事件 1085 逐字；文件落盘事件 1089/1090，`op_attr` 修正事件 1101/1102）：

```python
#!/usr/bin/env python3
"""torch_npu.profiler 标准模板：CPU(python 栈) + NPU(CANN 算子/核指标)。"""
import argparse, os
os.environ.setdefault("TASK_QUEUE_ENABLE", "1")   # 图模式/ACLGraph 必需
import torch
import torch_npu

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--warmup", type=int, default=5)     # 预热(含首次 capture)，放在 profiling 窗口外
    ap.add_argument("--steps",  type=int, default=10)    # profiling 的 active 步数
    ap.add_argument("--save-dir", default="./prof")
    ap.add_argument("--with-stack", action="store_true", help="记录 python 调用栈")
    args = ap.parse_args()

    torch.npu.set_device(0)
    model = ...            # 你的 nn.Module，.npu()
    inp   = (...)          # 输入张量(已在 npu 上)

    # 1) 预热 + 捕获：一定要在 profiling 窗口之前完成
    for _ in range(args.warmup):
        model(*inp)
    torch.npu.synchronize()

    # 2) CANN 侧明细：profiler_level + aic_metrics
    exp = torch_npu.profiler._ExperimentalConfig(
        profiler_level=torch_npu.profiler.ProfilerLevel.Level1,    # Level2 更细(含更全 CANN 算子/核)
        aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization, # 或 ArithmeticUtilization / Memory
        l2_cache=False,
        data_simplification=False,
        export_type=torch_npu.profiler.ExportType.Text,            # Text / Db
        op_attr=True,          # 可选：带算子属性
    )

    # 3) profiling 窗口 + 按轮次 step
    with torch_npu.profiler.profile(
        activities=[torch_npu.profiler.ProfilerActivity.CPU,
                    torch_npu.profiler.ProfilerActivity.NPU],
        schedule=torch_npu.profiler.schedule(
            wait=0, warmup=0, active=args.steps, repeat=1, skip_first=0),
        on_trace_ready=torch_npu.profiler.tensorboard_trace_handler(args.save_dir),
        record_shapes=True,
        profile_memory=False,
        with_stack=args.with_stack,    # ← python CPU 调用栈
        with_modules=True,             # ← python 模块栈
        with_flops=False,
        experimental_config=exp,
    ) as prof:
        for _ in range(args.steps):
            model(*inp)
            torch.npu.synchronize()
            prof.step()                # 每个迭代必须 step()

    print(f"done -> {args.save_dir}")

if __name__ == "__main__":
    main()
```

注：落盘版 `prof_template.py` 中 `op_attr` 已按实测修正为 `op_attr=False` 并注明"想带算子属性请改成 True 并把 export_type 换成 Db"（事件 1101）。

## 机制与判别

结论 c1（最小配置）：同时采集 Python CPU 调用栈与 CANN 算子明细的最小配置：activities=[ProfilerActivity.CPU, ProfilerActivity.NPU] + with_stack=True（可选 with_modules=True 记模块栈）+ experimental_config（profiler_level=Level1，aic_metrics=PipeUtilization，export_type=Text），预热与首次 capture 放在 profiling 窗口之外，窗口内每轮调用 prof.step()。对照关系：Python CPU 调用栈靠 `with_stack`（CPU activity 默认记录 aten/框架事件，`record_shapes=True` 附带 shape）；CANN 算子/核视图靠 NPU activity + `experimental_config(profiler_level, aic_metrics)`；更全 CANN 侧（含属性）用 `profiler_level=Level2` + `op_attr=True`（需 Db 导出）。

结论 c2（实测验证）：模板落盘为 ${LOCAL_PATH_1} 并在 sglang-npu-verify 容器（910B3）实测跑通：tensorboard_trace_handler 产物同时含 device_0（CANN 侧数据）与 FRAMEWORK/torch.python_tracer_func（Python 调用栈）。这直接满足"prof 上同时有 python cpu 和 cann 堆栈"的需求；`--with-stack` 与否两次运行都产出这两类目录。

结论 c3（告警语义）：实测确认两个警告语义：op_attr=True 仅在 export_type=Db 导出下生效，Text 导出下被忽略并告警；schedule warmup=0（预热放在窗口外）触发的 Profiler won't be using warmup 告警属预期行为。第一个告警对应模板修正（事件 1101）；第二个是模板设计使然（预热刻意放窗口外以免 capture/静态编译的头开销污染结果）。

## 验证信号

（平台：Ascend 910B3 单卡，sglang-npu-verify 容器 CANN 9.1.0；证据等级：真机实测，单次）

- 事件 1075/1079：容器内 `inspect` 核对 `profile()` 签名、`_ExperimentalConfig` 字段、`schedule` 参数——模板参数全部与安装版本一致（客观工具输出）。
- 事件 1090：`Write file successfully` → `${LOCAL_PATH_1}` 落盘。
- 事件 1094：容器内首跑（含 `--with-stack`）出现 `op_attr switch is invalid with export type set as text` 与 `Profiler won't be using warmup` 两条告警（模板缺陷暴露）。
- 事件 1098：复跑产物目录同时含 `device_0`（CANN）与 `FRAMEWORK/torch.python_tracer_func`（Python 栈）——模板有效性验证通过（单次）。
- 事件 1102/1109：`op_attr` 修正落盘成功（Edit applied successfully ×2）。

## 适用与失效边界

- 版本适用：torch_npu 2.10.0.post4 / torch 2.10.0（`_ExperimentalConfig` 为私有 API，跨版本字段可能变化，用前应重新 `inspect` 核对）。
- 关键约束（模板已内建，失效点）：
  - 预热与首次 capture 必须在 profiling 窗口外，否则 ACLGraph capture/静态编译的头开销污染结果；
  - 窗口内每轮必须 `prof.step()`，否则 schedule 不推进、`on_trace_ready` 不触发；
  - 图模式/ACLGraph 需在 `import torch_npu` 前设 `TASK_QUEUE_ENABLE=1`；
  - `experimental_config(record_op_args=True)` 且 `schedule(skip_first=0)` 时不能同时开静态 Kernel 编译（官方文档约束）；
  - `op_attr` 仅 Db 导出生效；`export_type=Text` 出人可读 trace、`Db` 出数据库。
- 未验证边界：多卡每 rank 子目录行为、Level2 + Db + op_attr 组合的实际产物内容、与 cache_compile replay 联用时的窗口划分，均未实测；DemoModel 仅 Linear/ReLU/Sigmoid，替换真实模型时输入需已在 npu 上。
- 停止/回退条件：若告警升级为报错（如 `_ExperimentalConfig` 字段不匹配），应先 `inspect.signature` 重新核对当前安装版本的 API 再调整模板；性能结论仍需同会话可比基线，本模板只负责采集。
