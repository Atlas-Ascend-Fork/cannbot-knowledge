---
{
  "type": "Runbook",
  "title": "Ascend950 CANN 缺 ops_nn 算子包的判别与 env.sh 双条件自动探测修复",
  "description": "Ascend950PR 上 torch_npu 导入成功、elementwise 算子正常但 mm/linear/softmax 报 aclnnMatmul 561103（Parse dynamic kernel config fail）/ Op SoftmaxV2 does not has any binary 时，根因是 CANN 安装的 ascend950 kernel 目录缺 ops_nn 子包（950 ops 组合包按 cv/legacy/math/nn/transformer 分子包）。用同时检查 lib64/libhccl.so 与 opp/.../kernel/ascend950/ops_nn 的 env.sh 自动选择完整 CANN 安装后全部算子恢复，全模型推理跑通并采到基线。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.model_serving",
    "topic.attention"
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

# Ascend950 CANN 缺 ops_nn 算子包的判别与 env.sh 双条件自动探测修复

## 适用场景

- 模型/框架：任意通过 torch_npu 2.12.0 跑在 Ascend950PR_9589 上的独立部署推理（本例 Hunyuan-A13B-Instruct-FP8，W8A8 FP8）；CANN 9.x。
- 平台：Ascend950PR_9589 单卡（HBM 123.25 GiB）；机器上多套 CANN 并存（`/usr/local/Ascend/cann-9.0.0`、`/usr/local/Ascend/cann-9.1.0`，另有 `${LOCAL_PATH_1}` 完整安装）。
- 目标：NPU 基础算子（MatMul/Softmax）报"无 kernel 二进制"类错误时，快速判别是环境/安装问题而非代码问题，并落到可复现的环境选择脚本。
- 缺失信息说明：未在其他 SoC（如 910B）或其他 CANN 版本上复测；子包目录名以 ascend950 布局为准。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：source 系统 `/usr/local/Ascend` 的 set_env（默认指向 cann-9.1.0）后执行任意含 MatMul/Softmax 的 NPU 计算。三种可区分的客观观测（本轨迹逐字日志）：

1. 默认环境（未配 `ASCEND_OPP_PATH`，走 cann-9.1.0）：
```
[PID: 3121358] ... Config_Error_Invalid_Environment_Variable(EZ1002): Get opp kernel path failed. Environment variable ASCEND_OPP_PATH is not configured.
        Solution: Reset the environment variable by referring to the Environment Variable Reference.
        TraceBack (most recent call last):
        Load static bin json failed. Environment variable ASCEND_OPP_PATH is not configured.
        LoadStaticBinJson failed.
        AclOpKernelInit failed opType.
```

2. `ASCEND_OPP_PATH=/usr/local/Ascend/cann-9.0.0/opp`（有 ascend950 kernel 但缺 ops_nn）：
```
RuntimeError: matmul_implement_npu:../third_party/op-plugin/op_plugin/ops/opapi/MatmulKernelNpuOpApi.cpp:92 NPU function error: call aclnnMatmul failed, error code is 561103
[ERROR] ... ERR00100 PTA call acl api failed.
EZ9999: Inner Error!
EZ9999[PID: 3177480] ... AclNN_Inner_Error(EZ9999):  Parse dynamic kernel config fail.
        TraceBack (most recent call last):
        Failed to ParseDynamicKernels.
        AclOpKernelInit failed opType.
```

3. Softmax 同环境下：
```
EZ9999[PID: 3200276] ... AclNN_Inner_Error(EZ9999):  Op SoftmaxV2 does not has any binary.
        TraceBack (most recent call last):
        Kernel Run failed. opType: 9, SoftmaxV2
        launch failed for SoftmaxV2, errno:561000.
```

同时（关键判别信号）：`torch_npu` 本身导入成功，且 elementwise 类算子全部正常，只有 mm/linear/softmax 失败。

## 探针与操作

算子分域探针（逐字，事件 204）：

```
import torch, torch_npu
torch.npu.set_device(0)
def t(name, fn):
    try:
        r=fn(); torch.npu.synchronize(); print("OK  ", name)
    except Exception as e:
        print("FAIL", name, str(e).splitlines()[0][:120])
a=torch.randn(4,8,dtype=torch.bfloat16,device='npu'); b=torch.randn(8,16,dtype=torch.bfloat16,device='npu')
t("add", lambda: a+a)
t("mul", lambda: a*a)
t("mm", lambda: a@b)
t("linear", lambda: torch.nn.functional.linear(a, b.t()))
t("softmax", lambda: torch.softmax(a.float(),dim=-1))
t("view", lambda: a.view(4,8))
t("cast-fp8", lambda: a.to(torch.float8_e4m3fn))
t("fp8->bf16", lambda: a.to(torch.float8_e4m3fn).to(torch.bfloat16))
t("rmslike", lambda: a.float().pow(2).mean(-1))
```

系统 CANN 状态探针（客观输出摘要）：

- `ls /usr/local/Ascend/cann-9.0.0/opp/built-in/op_impl/ai_core/tbe/kernel/ascend950/` → 只有 `ops_cv ops_legacy ops_math ops_transformer`（无 `ops_nn`）；`ops_math` 下 286 个目录无 matmul/softmax 基础实现（事件 209）。
- `cat /usr/local/Ascend/cann-9.0.0/x86_64-linux/ascend_ops_install.info` → `package_name=Ascend-cann-950-ops version=9.0.0`（事件 166），即系统装的是 950 ops 包但不含 nn 子包。
- 950 ops 组合安装包 `--list`：`run_package` 下 `cann-950-ops-{cv,legacy,math,nn,transformer}_9.1.0_linux-x86_64.run` 各自独立（ops-nn 800305576 字节，事件 241）。
- 完整安装判别（事件 257）：`${LOCAL_PATH_1}` 的 ascend950 kernel 目录含 `ops_nn`，且 `lib64/libhccl.so` 存在。

修复：写入 `env.sh` 自动探测完整 CANN（逐字，事件 316；可用 `ASCEND_TOOLKIT_DIR` 覆盖候选）：

```
#!/bin/sh
# Ascend CANN environment setup for Hunyuan-A13B standalone inference.
#
# The system CANN under /usr/local/Ascend lacks the ascend950 ``ops_nn`` kernel
# package (no MatMul/Softmax binaries), so this script auto-detects a complete
# CANN install that provides both libhccl.so and the ascend950 ops_nn kernels.
# Override by exporting ASCEND_TOOLKIT_DIR before sourcing.
#
# Usage:  source env.sh

_cann_root=""
for _c in "${ASCEND_TOOLKIT_DIR}" "/usr/local/Ascend/cann-9.1.0" "${LOCAL_PATH_1}" "/usr/local/Ascend/cann-9.0.0"; do
    [ -z "${_c}" ] && continue
    if [ -e "${_c}/lib64/libhccl.so" ] && \
       [ -d "${_c}/opp/built-in/op_impl/ai_core/tbe/kernel/ascend950/ops_nn" ]; then
        _cann_root="${_c}"
        break
    fi
done

if [ -z "${_cann_root}" ]; then
    echo "[env.sh] ERROR: no complete CANN install (libhccl.so + ascend950 ops_nn) found" >&2
    echo "[env.sh] set ASCEND_TOOLKIT_DIR to a valid CANN toolkit dir" >&2
    return 1 2>/dev/null || exit 1
fi

export ASCEND_TOOLKIT_DIR="${_cann_root}"
export ASCEND_HOME_PATH="${_cann_root}"
export ASCEND_OPP_PATH="${_cann_root}/opp"
export ASCEND_AICPU_PATH="${_cann_root}"
export ASCEND_TOOLKIT_HOME="${_cann_root}"
export PATH="${_cann_root}/bin:${PATH}"
export LD_LIBRARY_PATH="${_cann_root}/lib64:${_cann_root}/lib64/plugin/opskernel:${_cann_root}/lib64/plugin/nnengine:/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:${LD_LIBRARY_PATH}"
export PYTHONPATH="${_cann_root}/python/site-packages:${_cann_root}/opp/built-in/op_impl/ai_core/tbe:${PYTHONPATH}"

echo "[env.sh] using CANN at ${_cann_root}"
```

## 机制与判别

- 结论 a1：系统 CANN（/usr/local/Ascend 下 cann-9.0.0 与 cann-9.1.0）的 ascend950 kernel 目录只含 ops_cv/ops_legacy/ops_math/ops_transformer 四个子包、缺 ops_nn，此时 aclnnMatmul 报 "call aclnnMatmul failed, error code is 561103"（EZ9999: Parse dynamic kernel config fail），softmax 报 "Op SoftmaxV2 does not has any binary"（error code 561000），而 torch_npu 导入与 add/mul/view/fp8 cast 等简单算子仍正常。（证据：事件 204/209 探针，144/181/205 错误日志）
- 结论 a2：缺 ops_nn 的来源是 950 系列 ops 组合安装包按算子域拆分子包（run_package 下 cann-950-ops-{cv,legacy,math,nn,transformer}_9.1.0_linux-x86_64.run 各自独立存在，ops-nn 约 800 MB）；系统 cann-9.0.0 的安装身份是 Ascend-cann-950-ops（ascend_ops_install.info）但其 ascend950 kernel 目录无 ops_nn，即系统安装的 ops 包不含 nn 子包。（证据：事件 166/209/241）
- 结论 a3：用 env.sh 同时检查 lib64/libhccl.so 与 opp/built-in/op_impl/ai_core/tbe/kernel/ascend950/ops_nn 自动选择完整 CANN 安装（可用 ASCEND_TOOLKIT_DIR 覆盖）后，mm/linear/softmax/fp8_cast 探针全部 OK，全模型 FP8 推理跑通并采到部署基线（单次验证）。（证据：事件 261/647/651）
- 可区分解释分支：
  1. `ASCEND_OPP_PATH` 未配置/指向的 CANN 无 ascend950 目录 → EZ1002 "Get opp kernel path failed"（环境变量问题）；
  2. 指向的 CANN 有 ascend950 但无 ops_nn → 561103 "Parse dynamic kernel config fail" / 561000 "SoftmaxV2 does not has any binary"（安装不完整问题）；
  3. 完整安装（libhccl + ops_nn 齐）→ 全部 OK。
- 判别要点：torch_npu 导入成功、elementwise/reshape/cast 成功都不能证明 mm/linear/softmax 可用；遇到 `AclOpKernelInit failed opType` 优先查 opp kernel 子包目录，而不是怀疑驱动或代码。
- 附带事实（后续轨迹复现）：该仓库 shell 为 `/bin/sh` 时 `source env.sh` 报 `source: not found`（事件见阶段 2 轨迹 infer.sh 首跑），需 `bash infer.sh` 或 `. ./env.sh` 方式执行；`sh` 下直接 `source` 会导致 libhccl.so 缺失、torch_npu 导入失败。

## 验证信号

- 事件 261（切换完整 CANN 后单次探针）：`OK mm (4, 16)`、`OK linear (4, 16)`、`OK softmax (4, 8)`、`OK fp8_cast (4, 8)`。
- 事件 320：小配置 NPU 冒烟 `NPU SMOKE OK`（prefill/decode logits 有限）。
- 事件 647：全模型 80GB FP8 权重加载后（used 79.12 GiB / total 123.25 GiB）完整推理跑通，`prefill is 1923.02 ms`，decode 7 步 1722–1792 ms。
- 事件 651：`agentic/baseline/baseline_metadata.json` 采集成功（`"all_ranks_success": true`）。
- 证据等级：单机单卡、单次运行验证；平台 Ascend950PR_9589 / CANN 9.0.0+9.1.0（系统）与 CANN 9.1.0（完整安装）/ torch_npu 2.12.0 / torch 2.12.0+cpu。

## 适用与失效边界

- 仅验证于 Ascend950PR_9589 与 CANN 9.0.0/9.1.0 目录布局；其他 SoC（如 910B）或 CANN 版本的 kernel 子包名/路径可能不同，套用前先 `ls $ASCEND_OPP_PATH/built-in/op_impl/ai_core/tbe/kernel/<soc>/` 确认。
- env.sh 的候选列表含机器特定路径（`${LOCAL_PATH_1}`），迁移环境需用 `ASCEND_TOOLKIT_DIR` 覆盖或修改候选。
- 正确做法的停止条件：探针 mm/linear/softmax 全 OK 即环境闭环；若仍失败则不是本问题（转 runtime-debug）。
- 不成立的情形：若错误来自单个自定义算子而非基础算子，或 elementwise 也失败，则不是缺 ops_nn 子包问题。
