---
{
  "type": "Runbook",
  "title": "三重取证法判定 MindSpore 算子在 Ascend 上的实际执行路径：ResizeBilinearV2 走 AscendC 预编译向量核（非 TBE legacy、非 aclnn）",
  "description": "在 Ascend950PR + MindSpore 2.10.0 + CANN 9.2.0-beta.2 上，用『最小 E2E 脚本 + MindSpore DEBUG 日志 + CANN 设备侧 DEBUG 日志』三重取证，并以 ops-info 注册表、AscendC impl/预编译 bin、libopapi 符号交叉判别 aclnn/TBE-legacy/AscendC 三个解释分支。结论：ResizeBilinearV2 经 aclopCompileAndExecute 由 simpleKey 匹配到 AscendC 预编译核 ResizeBilinearV2_8d247302..._high_performance_30000（KERNEL_AIVEC 向量核，单次观测），未调用 aclnn 接口。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "task.testing"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# 三重取证法判定 MindSpore 算子在 Ascend 上的实际执行路径：ResizeBilinearV2 走 AscendC 预编译向量核（非 TBE legacy、非 aclnn）

## 适用场景

- 平台/版本：Ascend950PR（ascend950，npu-smi 25.7.rc1，device 0）+ CANN 9.2.0-beta.2（安装于 `/usr/local/Ascend/cann-9.2.0-beta.2`，`ascend-toolkit/latest` 解析到该目录）+ MindSpore 2.10.0（`${LOCAL_PATH_1}`，Python 3.10）。
- 目标：判定 mindspore.ops 算子端到端实际落到哪个底层实现（aclnn 接口 / TBE legacy Python 实现 / AscendC 预编译核 / CPU 回退），并留下日志级证据链。
- 本例工作负载：`mindspore.ops.operations.image_ops.ResizeBilinearV2`，GRAPH_MODE + device_target="Ascend" + device_id=0，float32 NCHW 输入 (1,3,8,8)、int32 size [16,16]，最小单算子 E2E（单次运行）。
- 缺失信息：其他 MindSpore/CANN 版本、其他芯片（如 910B）、其他 dtype/格式未在本轨迹验证。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_4}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_5}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_6}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_7}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：需要确认该算子在 ascend950 上到底走 TBE 的 `sync_resize_bilinear_v2.py`（SyncResizeBilinearV2）还是 AscendC/aclnn 路径（用户任务，事件 2）。

观测 1（E2E 成功，单次，事件 20）：

```
=== ResizeBilinearV2 E2E RESULT ===
input shape: (1, 3, 8, 8) dtype: Float32
size tensor: [16, 16]
output shape: (1, 3, 16, 16) dtype: Float32
```

观测 2（MindSpore DEBUG 日志，事件 45/51）：MindSpore 为 ResizeBilinearV2 创建的是 acl kernel module，并进入 aclopCompileAndExecute：

```
7161: [INFO] DEVICE(855267,7d4f54fe1740,python):2026-10-17-03:38:52.543.566 [mindspore/ccsrc/plugin/ascend/kernel_executor/ascend_kernel_executor.cc:175] GenerateKernelMod] kernel opname:ResizeBilinearV2, kernel type:acl_kernel
```

```
7274: [DEBUG] GE_ADPT(855267,7d4f54fe1740,python):2026-10-17-03:38:52.552.613 [mindspore/ops/kernel/ascend/acl_ir/acl_utils.cc:388] Run] Start aclopCompileAndExecute of op_type: ResizeBilinearV2
```

观测 3（CANN 设备侧 DEBUG 日志，事件 93/110/104）：opFile 解析、simpleKey 匹配、最终 launch：

```
140111:[DEBUG] FE(855813,python):2026-10-17-03:42:32.719.257 [op_kernel_info_constructor.cc:1377]855813 InitOpStrItem:The [opFile] for operation [ResizeBilinearV2] is [resize_bilinear_v2_apt].
```

```
206066:[DEBUG] TEFUSION(855813,python):2026-10-17-03:42:33.202.730 [fusion_binary_info.cc:118]856078 MatchSimpleKey Match opType[ResizeBilinearV2], simpleKey[ResizeBilinearV2/d=0,p=0/0,1/3,2/0,1] succeeded. binJsonPath is [ascend950/resize_bilinear_v2_apt/ResizeBilinearV2_8d247302e7438d1c4245c6a6bdcf024f_high_performance.json].
```

```
[INFO] RUNTIME(855813,python):2026-10-17-03:42:33.237.321 [aix_starsv2.cc:505] 855813 StreamLaunchKernelWithHandle: stream_id=122, kernel_name=ResizeBilinearV2_8d247302e7438d1c4245c6a6bdcf024f_high_performance_30000, kernelAttrType=KERNEL_ATTR_TYPE_VECTOR(2), funcType=3, arg_size=304, mixType=0, taskRation=2, kernelVfType=3, dynamicSmSize=0, addr1=0x12004101c758, addr2=0x0, kernelFlag=0x0, qos=0, partId=0, schemMode=0, infoAddr=(nil), atomicIndex=0.
[INFO] RUNTIME(855813,python):2026-10-17-03:42:33.237.331 [stream_david.cc:811] 855813 StarsAddTaskToStream: single-operator stream, stream_id=122, task_id=2, task_sn=7, type=66(KERNEL_AIVEC), sqe_num=1, device_id=0
[INFO] RUNTIME(855813,python):2026-10-17-03:42:33.237.334 [task_david.cc:629] 855813 DavidSendTask: device_id=0, ts_id=0, sq_id=49, stream_id=122, task_id=2, flip_num=0, task_sn=7, task_type=66(KERNEL_AIVEC), drvRet=0.
```

## 探针与操作

探针 1：最小 E2E 脚本 `${LOCAL_PATH_2}`（事件 14）：

```python
"""Minimal E2E test: MindSpore ResizeBilinearV2 on Ascend NPU (Ascend950PR)."""
import numpy as np
import mindspore as ms
from mindspore import Tensor, context
import mindspore.ops.operations.image_ops as image_ops

context.set_context(mode=ms.GRAPH_MODE, device_target="Ascend", device_id=0)

# float32 input (1, 3, 8, 8), size tensor int32 [16, 16]
np_x = np.random.randn(1, 3, 8, 8).astype(np.float32)
x = Tensor(np_x)
size = Tensor(np.array([16, 16], dtype=np.int32))

resize = image_ops.ResizeBilinearV2()
out = resize(x, size)

print("=== ResizeBilinearV2 E2E RESULT ===")
print("input shape:", x.shape, "dtype:", x.dtype)
print("size tensor:", size.asnumpy().tolist())
print("output shape:", out.shape, "dtype:", out.dtype)
out_np = out.asnumpy()
print("output[0,0,:2,:2]:\n", out_np[0, 0, :2, :2])
print("output[0,1,:2,:2]:\n", out_np[0, 1, :2, :2])
print("=== RUN OK ===")
```

探针 2：MindSpore DEBUG 日志重跑（事件 27；注意 `MS_LOG_FILE_PATH`/`MS_COMPILER_CACHE_PATH` 指定目录实际为空，DEBUG 日志靠 stdout 重定向捕获，事件 28/52）：

```
source /usr/local/Ascend/ascend-toolkit/set_env.sh && export GLOG_v=0 MS_LOG_LEVEL=DEBUG MS_LOG_FILE_PATH=${LOCAL_PATH_3} MS_COMPILER_CACHE_PATH=${LOCAL_PATH_4} && ${LOCAL_PATH_1} test_resize_e2e.py > ${LOCAL_PATH_5} 2>&1; echo "exit=$?"; ls -la ${LOCAL_PATH_5}; tail -8 ${LOCAL_PATH_5}
```

探针 3：CANN 设备侧 DEBUG 日志重跑（事件 83，产出 215023 行 cann_debug_run.log）：

```
source /usr/local/Ascend/ascend-toolkit/set_env.sh && export ASCEND_GLOBAL_LOG_LEVEL=0 ASCEND_SLOG_PRINT_TO_STDOUT=1 GLOG_v=2 MS_LOG_LEVEL=WARNING && ${LOCAL_PATH_1} test_resize_e2e.py > ${LOCAL_PATH_6} 2>&1; echo "exit=$?"; wc -l ${LOCAL_PATH_6}
```

探针 4：CANN 注册表/符号取证（事件 61/65/71/77/78，输出见"机制与判别"）：解析 `aic-ascend950-ops-info-cv.json` 的 ResizeBilinearV2 条目；`find` 定位 `*resize_bilinear*` 实现文件；读取 `resize_bilinear_v2_apt.cpp` 头部宏；解析 `kernel/config/ascend950/ops_cv/resize_bilinear_v2_apt.json` 的 binList；`nm -D` 查 libopapi.so 符号。

探针 5：分支排除计数（事件 107）：

```
grep -c "SyncResizeBilinearV2\|sync_resize_bilinear" ${LOCAL_PATH_6}; echo "---aclnn calls in log---"; grep -c "aclnnResize" ${LOCAL_PATH_6}; echo "---which ops-info registers SyncResizeBilinearV2---"; grep -rl "SyncResizeBilinearV2" /usr/local/Ascend/cann-9.2.0-beta.2/opp/built-in/op_impl/ai_core/tbe/config/ 2>/dev/null | head; echo "---ascend950 dir has sync_resize?---"; ls /usr/local/Ascend/cann-9.2.0-beta.2/opp/built-in/op_impl/ai_core/tbe/config/ascend950/ | head -20
```

输出（事件 109；注意"which ops-info registers SyncResizeBilinearV2"小节为空即无注册）：

```
92
---aclnn calls in log---
0
---which ops-info registers SyncResizeBilinearV2---
---ascend950 dir has sync_resize?---
aic-ascend950-ops-info-cv.json
aic-ascend950-ops-info-legacy.json
aic-ascend950-ops-info-math.json
aic-ascend950-ops-info-nn.json
aic-ascend950-ops-info-transformer.json
```

## 机制与判别

结论 1：MindSpore 2.10.0 在 Ascend950PR 上以 acl_kernel 路径执行 ResizeBilinearV2：MindSpore DEBUG 日志显示 kernel opname:ResizeBilinearV2, kernel type:acl_kernel，并进入 aclopCompileAndExecute(op_type=ResizeBilinearV2)；本次 CANN 日志中 aclnnResize 调用计数为 0，即未走 aclnn 接口。

结论 2：CANN 9.2.0-beta.2 在 ascend950 上把 ResizeBilinearV2 注册为 AscendC 实现 resize_bilinear_v2_apt（aic-ascend950-ops-info-cv.json 的 opFile，impl 位于 impl/ops_cv/ascendc/ 并带 arch35 头文件与预编译 .o）；TBE 的 sync_resize_bilinear_v2.py 位于 ops_legacy，且 ascend950 的 ops-info 配置中无 SyncResizeBilinearV2 注册。

结论 3：设备侧最终 launch 的 kernel 是预编译 AscendC 向量核 ResizeBilinearV2_8d247302e7438d1c4245c6a6bdcf024f_high_performance_30000：由 simpleKey 匹配选中该 bin，经 StreamLaunchKernelWithHandle 下发，task type 66(KERNEL_AIVEC)（单次观测）。

注册表证据（事件 62，`aic-ascend950-ops-info-cv.json` 中 ResizeBilinearV2 条目片段）：

```
 "opFile": {
  "value": "resize_bilinear_v2_apt"
 },
 "opInterface": {
  "value": "resize_bilinear_v2"
 },
```

实现文件布局（事件 67，find 输出中的两行关键行）：

```
/usr/local/Ascend/cann-9.2.0-beta.2/opp/built-in/op_impl/ai_core/tbe/impl/ops_legacy/dynamic/sync_resize_bilinear_v2.py
/usr/local/Ascend/cann-9.2.0-beta.2/opp/built-in/op_impl/ai_core/tbe/impl/ops_cv/ascendc/resize_bilinear_v2/resize_bilinear_v2_apt.cpp
```

AscendC 实现头部 tiling key 宏（事件 73，`resize_bilinear_v2_apt.cpp`）：

```
#define TILING_KEY_C_PARALLEL 10000
#define TILING_KEY_HW_CACHE 20000
#define TILING_KEY_SIMT_NHWC 30000
#define TILING_KEY_SIMT_NCHW 30001
#define TILING_KEY_SIMT_NHWC_IDX64 30002
#define TILING_KEY_SIMT_NCHW_IDX64 30003
#define TILING_KEY_SIMT_HW 30004
#define TILING_KEY_SIMT_HW_IDX64 30005
#define TILING_KEY_ALL_COPY 40000
#define TILING_KEY_POINT_COPY 40001
#define TILING_KEY_NCHW_BROADCAST 40002
#define TILING_KEY_NHWC_BROADCAST 40003
```

预编译 bin 注册（事件 79，`kernel/config/ascend950/ops_cv/resize_bilinear_v2_apt.json` binList 中 float32 的两条；NCHW bin 存在但本次未被选中）：

```
binList entries: 10
float32 entries: 2
 implMode: high_performance | inputs: [('x', 'float32', 'NCHW'), ('size', 'int32', 'ND')] | outputs: [('y', 'float32', 'NCHW')]
 binInfo: {"jsonFilePath": "ascend950/resize_bilinear_v2_apt/ResizeBilinearV2_e66a363bda230c55fa1a293c7befd9f0_high_performance.json"}
 implMode: high_performance | inputs: [('x', 'float32', 'NHWC'), ('size', 'int32', 'ND')] | outputs: [('y', 'float32', 'NHWC')]
 binInfo: {"jsonFilePath": "ascend950/resize_bilinear_v2_apt/ResizeBilinearV2_8d247302e7438d1c4245c6a6bdcf024f_high_performance.json"}
```

libopapi 符号（事件 80，`nm -D libopapi.so`，说明 aclnn 入口存在但本次未被调用）：

```
0000000002d77320 u _ZGVZN4l0op24ResizeBilinearV2OpTypeIdEvE24ResizeBilinearV2OpTypeId
0000000002d77540 u _ZGVZN4l0op28ResizeBilinearV2GradOpTypeIdEvE28ResizeBilinearV2GradOpTypeId
0000000000e103c0 T _ZN4l0op16ResizeBilinearV2EPK9aclTensorS2_bS2_P13aclOpExecutor
0000000000e1b6f0 T _ZN4l0op20ResizeBilinearV2GradEPK9aclTensorS2_bbPK13aclFloatArrayP13aclOpExecutor
0000000000e123a0 T _ZN4l0op22ResizeBilinearV2With4dEPK9aclTensorS2_bPK13aclFloatArrayS2_P13aclOpExecutor
0000000000e1dfb0 T _ZN4l0op23ResizeBilinearV2Grad5HdEPK9aclTensorS2_bbP13aclOpExecutor
```

同一预编译 bin 内注册多个 tilingKey 变体（事件 99；本轨迹另观测到 40001/40002/40003、30004、30005 的注册行）：

```
213788:[INFO] RUNTIME(855813,python):2026-10-17-03:42:33.230.800 [program.cc:1730] 855813 BuildNewKernel: new kernel success, size=1304, programId=1, original kernel_name=ResizeBilinearV2_8d247302e7438d1c4245c6a6bdcf024f_high_performance_40000, register kernel_name=ResizeBilinearV2_8d247302e7438d1c4245c6a6bdcf024f_high_performance_40000, tilingKey=40000, functionEntry=40000, funcType=3, kernelAttrType=KERNEL_ATTR_TYPE_VECTOR(2), mixType=0, taskRation=2, offset=0, dfxAddr=95813747504824, dfxSize=176
```

可区分解释分支：

| 分支 | 支持证据 | 反驳证据 | 判定 |
|---|---|---|---|
| aclnn（libopapi `l0op::ResizeBilinearV2`） | nm 符号存在（事件 80） | aclnnResize 计数 0（事件 109）；MindSpore 走 aclopCompileAndExecute（事件 51） | 排除 |
| TBE legacy `sync_resize_bilinear_v2.py` | 文件存在（事件 67/74，`def sync_resize_bilinear_v2` 位于该文件第 2566 行） | 位于 ops_legacy；ascend950 ops-info 无 SyncResizeBilinearV2 注册（事件 109）；opFile 指向 resize_bilinear_v2_apt（事件 62/93） | 排除 |
| AscendC 预编译核 resize_bilinear_v2_apt | ops-info opFile + AscendC impl + 预编译 bin（事件 62/67/73/79） | — | 成立（simpleKey 匹配 + KERNEL_AIVEC launch，事件 110/104） |

未验证推断：kernel 名后缀 `_30000` 对应 `resize_bilinear_v2_apt.cpp` 中的 `TILING_KEY_SIMT_NHWC 30000`（宏定义见上，事件 73）；"后缀=tilingKey"的对应关系由事件 99 的 `kernel_name=..._40000`/`tilingKey=40000` 行支持，属推断而非日志直印 `tilingKey=30000`。

另一细节：MindSpore 输入为 NCHW，CANN 侧 `generate_simple_key` 归一化为 `format[NHWC], dtype[float32]` 后匹配到 NHWC bin（8d247302），GE 图中同时出现 `trans_Transpose` launch 节点（`MakeSureTensorAtDevice_ResizeBilinearV21_in_*`，事件 100/104）；NCHW float32 bin（e66a36...）存在但本次未被选中，其决策链未深挖。

## 验证信号

（以下均为本轨迹内客观观测；平台 Ascend950PR + CANN 9.2.0-beta.2 + MindSpore 2.10.0；单次运行）

- 事件 20：E2E 脚本运行成功，输出 shape (1,3,16,16)，`=== RUN OK ===`（输出数值已打印，但未与参考实现比对精度）。
- 事件 28：MindSpore DEBUG 重跑 exit=0，ms_debug_run.log 1536698 字节。
- 事件 45：`kernel opname:ResizeBilinearV2, kernel type:acl_kernel`（日志行 7161）。
- 事件 51：`Start aclopCompileAndExecute of op_type: ResizeBilinearV2`（日志行 7274）。
- 事件 84：CANN DEBUG 重跑 exit=0，cann_debug_run.log 215023 行。
- 事件 93：`InitOpStrItem:The [opFile] for operation [ResizeBilinearV2] is [resize_bilinear_v2_apt]`。
- 事件 110：`MatchSimpleKey ... succeeded`，binJsonPath=ascend950/resize_bilinear_v2_apt/ResizeBilinearV2_8d247302e7438d1c4245c6a6bdcf024f_high_performance.json。
- 事件 104：`StreamLaunchKernelWithHandle ... kernel_name=..._30000`；`StarsAddTaskToStream ... type=66(KERNEL_AIVEC)`；`DavidSendTask ... task_type=66(KERNEL_AIVEC)`（设备侧最终证据，单次观测）。
- 事件 109：`grep -c "aclnnResize"` 为 0；`grep -rl "SyncResizeBilinearV2"` 于 tbe/config/ 无结果。
- 证据等级：日志 + 注册表 + 符号三方一致的取证级证据；非精度/性能验证。

## 适用与失效边界

- 适用：MindSpore 2.10.0 + CANN 9.2.0-beta.2 + ascend950 的 ResizeBilinearV2（float32；本例 NCHW 输入、size [16,16]、GRAPH_MODE 单算子）。
- MindSpore 2.10.0 对 CANN 9.2 报版本不匹配 WARNING（期望 8.2/8.3/8.5/9.0/9.1，事件 10/20）；任一侧升级/降级后路径可能改变，需重新取证。
- 方法依赖 CANN 日志模块名（`op_kernel_info_constructor.cc` / `fusion_binary_info.cc` / `aix_starsv2.cc` / `stream_david.cc` / `task_david.cc`）与注册表路径（`aic-ascend950-ops-info-*.json`、`kernel/config/ascend950/ops_cv/`、`impl/ops_cv/ascendc/`）；CANN 目录结构或日志模块变化时探针需相应调整。
- 取证时 grep 必须指向精确日志文件：本环境 `${LOCAL_PATH_7}` 下混有此前会话的自定义 SyncResizeBilinearV2 构建遗留（build_*.log、test_proj 等），目录级搜索会混入干扰（事件 40/46/88/90 已发生并纠正）。
- 未验证：float16/bfloat16、NHWC 直连输入、动态 shape、batch>1、多次运行稳定性；tilingKey 30000=SIMT_NHWC 为源码宏对应推断。
- 无性能结论（未测量耗时/吞吐）；输出数值仅打印未比对，不构成精度验证。
- 停止/回退条件：若日志缺失 `InitOpStrItem`/`MatchSimpleKey`/`StreamLaunchKernelWithHandle` 任一环节，三重证据链不闭合，只能给出降级结论（例如仅有 MindSpore 侧 acl_kernel 证据时，无法区分 AscendC 预编译核与其它 aclop 后端）。
