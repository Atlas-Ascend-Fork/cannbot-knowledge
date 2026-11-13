---
{
  "type": "Runbook",
  "title": "dsv41_fused_prefill_kernel cannsim host SIGABRT vs 同 kernel 真机运行完成（cannsim/真机差异判别）",
  "description": "dsv41_fused_prefill_kernel 在 cannsim（npusim, -s Ascend950DT）下使 host 进程 SIGABRT。用『从真实 kernel 向下裁剪』的 bisect 方法：每级精简 kernel 先真机跑通再进 cannsim 记录 SUCCESS/FAILED。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# dsv41_fused_prefill_kernel cannsim host SIGABRT vs 同 kernel 真机运行完成（cannsim/真机差异判别）

## 适用场景

dsv41_fused_prefill_kernel 在 cannsim（npusim, -s Ascend950DT）下使 host 进程 SIGABRT。用『从真实 kernel 向下裁剪』的 bisect 方法：每级精简 kernel 先真机跑通再进 cannsim 记录 SUCCESS/FAILED。对同一完整 kernel：真机运行正常完成（TG tile group 全部打印、launch_returned、synced、DONE），cannsim 运行 45.8s 后 Simulation FAILED signal 6，日志显示 munmap_chunk(): invalid pointer → Fatal Python error: Aborted。任务侧已单独验证排除的构造包括 torch 算子、纯 vector、纯 cube、mix、fp8 量化（vf.astype→FP8+PACK4_B32）、跨核同步 set(FIX,0)/wait(V,0)、60 参数 kernel、pl.getval/setval、3-D store、set_validshape、Acc→Vec DualModeSplitM 交接。本批轨迹在拿到最终最小复现单元前中断（diag 脚本又遇 libhccl.so/aclnn 符号缺失环境问题）。

kernel 在 cannsim（npusim）下 host 进程 SIGABRT 而真机正常的定位；裁剪式 bisect harness 搭建。

（知识形态：diagnostic_rule —— 触发 → 可执行探针 → 客观观测 → 可区分解释）


## 触发与观测

触发与观测对应的结论原文：

- 同一完整 kernel 真机运行正常完成（打印全部 [TG] tile group 定义后 MARK launch_returned、MARK synced、DONE），而 cannsim 运行 45.8s 后 Simulation FAILED signal 6，伴随 munmap_chunk(): invalid pointer 与 Fatal Python error: Aborted。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。


探针即裁剪 bisect harness：每级精简 kernel 先记录设备执行与数值检查结果；只运行完成而无数值对照不得称语义正确再进 cannsim（cannsim record -s Ascend950DT，脚本禁 os.chdir），记录 SUCCESS/FAILED 到 BISECT.md；对同一 kernel 的真机/cannsim 差异取崩溃栈判别。

## 机制与判别

机制判别：同一 kernel 的一次设备运行完成与仿真宿主崩溃构成环境差异线索，但不能排除 kernel 语义或未定义行为；cannsim 的 SIGABRT 伴随 munmap_chunk(): invalid pointer 与 Fatal Python error: Aborted（见来源结论），与真机结果构成可区分对照。旁证：任务侧已单测排除 torch 算子、纯 vector、纯 cube、mix、fp8 量化、跨核同步、60 参数 kernel、pl.getval/setval、3-D store、set_validshape、DualModeSplitM 交接等构造。

本条目引用的机制片段：原文：

```bash
cd ${SCRATCH_DIR}/opencode/sim && timeout 900 ./run_sim.sh tg ./probe_ours.py trace 2>&1 | tail -20
```


## 验证信号

验证信号（判别性，非闭环）：真机完整运行 DONE（TG 定义全打印、launch_returned、synced）；cannsim 45.8s Simulation FAILED signal 6 + munmap_chunk invalid pointer。最小复现单元与最终根因未在本轨迹内取得（会话中断于 diag 脚本环境问题：libhccl.so 缺失、aclnn metadata 符号缺失——后者属另一目录环境错误，与本 kernel 无关）。

## 适用与失效边界

适用：cannsim/npusim 宿主 SIGABRT 与设备行为异常的快速分流。边界：最小复现单元与根因未取得（会话截断），不可据此断言特定 tile group 形态必然崩溃；cannsim 运行必须 -s Ascend950DT 且脚本禁 os.chdir（否则 LPDDR 初始化 assert）；排除清单（torch 算子/纯 vector/纯 cube/mix/fp8/跨核同步/60 参数/getval/setval/3-D store/set_validshape/DualModeSplitM）为任务方已验证口径，这是来源报告在当时条件下的排查记录，不能免除新环境的复测。
