---
{
  "type": "Runbook",
  "title": "容器内 NPU 访问不可用时 torch_npu 初始化失败的判别链（aclInit 507008 / 507899）",
  "description": "仅安装 CANN toolkit 的 Linux 容器内 torch.npu.set_device / aclInit 阶段失败（507008 chipType=0，或 507899 + /dev/davinci* 设备节点缺失 + drvGetDevNum rc=7）。设备探针加基础算子对照可判别为容器内 NPU 访问不可用而非用例问题；判别链覆盖两类错误码。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-10-29T16:09:06Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": []
}
---

# 容器内 NPU 访问不可用时 torch_npu 初始化失败的判别链（aclInit 507008 / 507899）

> 本卡合并两个实例：原卡的 aclInit 507008 + chipType=0 判别链（保留），以及 2026-10 轨迹实测的 hunyuan_a13b_fp8 基线阻塞实例（aclInit 507899 + `/dev/davinci*` 设备节点缺失 + drvGetDevNum rc=7）。两者同属「容器内 NPU 访问不可用」家族，错误码与探针互补。

## 适用场景


- 框架与工具链：torch 2.9.0+cpu、torch_npu 2.9.0.post6（site-packages 安装）、torchair（随 torch_npu 安装于 `torch_npu/dynamo/torchair`）；Python 3.11.4（/opt/buildtools）。
- 环境：Linux 容器，仅安装 CANN cann-9.0.0 toolkit（`ASCEND_TOOLKIT_HOME` 等环境变量齐全），容器内观测不到 NPU 设备文件、`npu-smi` 命令不可用；`LD_LIBRARY_PATH` 含 CANN toolkit 自带的单算子仿真库路径 `tools/simulator/Ascend910B1/lib`。本卡全部「无 NPU」表述均限定为「该容器内 NPU 访问不可用」，不据此断言宿主机硬件配置。
- 目标与工作负载：在 cann/ops-transformer 仓运行 torchair aclgraph 复现用例 `tests/aclgraph_test.py`（依赖 `reduce-overhead` 模式的 aclgraph 捕获/回放）。判别方法不限于该用例，适用于任何触发 torch_npu 设备初始化的脚本。
- 缺失信息：容器镜像/发行版与内核版本未记录；宿主机硬件配置、NPU 设备是否映射进容器、宿主机驱动安装状态均未知；无有卡环境对照输出。

轨迹补充（hunyuan_a13b_fp8 长序列 Prefill 基线场景）：


- 模型/框架：Hunyuan-A13B-Instruct-FP8（细粒度 MoE + GQA，FP8 W8A8，activation_scheme=static），独立部署自管 Runner（`bash infer.sh <yaml>`，不走 cann-recipes-infer executor 入口）。
- 场景：长序列 Prefill，input_len=2048、batch=1、max_new_tokens=8、单卡、exe_mode=npugraph_ex。
- 平台：容器内环境；CANN 9.1.0（`env.sh` 自动探测到 `${LOCAL_PATH_2}`，需含 ascend950 ops_nn 算子子包）；torch 2.12.0+cpu / torch_npu 2.12.0 / Python 3.12 venv。
- 历史参照：该 case 此前（10-10）在 Ascend950PR_9589 单卡上跑通过基线（baseline_metadata.json：prefill 1923 ms / decode 1740.7 ms，eager），说明模型与 Runner 本身可用；本次（10-17）环境驱动重装后 NPU 不可见。
- 缺失信息：宿主机/容器设备暴露策略未知（是否本应通过 mdev/vNPU 暴露）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_4}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_5}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${TORCH_NPU_ROOT}` 为torch-npu 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

### 原卡实例（aclInit 507008 / chipType=0）


在仓根（${LOCAL_PATH_3}）执行：

```bash
timeout 120 python tests/aclgraph_test.py 2>&1 | tail -40
```

用例在 `tests/aclgraph_test.py:32` 的 `torch.npu.set_device(0)` 处失败（导入 torch、torch_npu、torchair 本身成功）。逐字原始输出：

```text
Traceback (most recent call last):
  File "${LOCAL_PATH_1}", line 32, in <module>
    torch.npu.set_device(0)
  File "/opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/npu/utils.py", line 91, in set_device
    torch_npu._C._npu_setDevice(device_id)
  File "/opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/npu/__init__.py", line 273, in _lazy_init
    torch_npu._C._npu_init()
RuntimeError: Initialize:../torch_npu/csrc/core/npu/sys_ctrl/npu_sys_ctrl.cpp:165 NPU function error: aclInit, error code is 507008
[ERROR] 2026-10-22-11:15:31 (PID:2025471, Device:0, RankID:-1) ERR00100 PTA call acl api failed
[Error]: Failed to obtain the SOC version.
        Rectify the fault based on the error information in the ascend log.
[PID: 2025471] 2026-10-22-11:15:31.080.159 Invalid_Argument(EE1001): The argument is invalid.Reason: rtGetDevMsg execution failed, the feature is not supported.
        Solution: 1.Check the input parameter range of the function. 2.Check the function invocation relationship.
        TraceBack (most recent call last):
        [Init][Version]init soc version failed.[FUNC:ReportInnerError][FILE:log_inner.cpp][LINE:132]
        chipType=0 does not support get device msg feature.[FUNC:GetDevMsg][FILE:api_impl.cc][LINE:6181]
        The argument is invalid.Reason: rtGetDevMsg execution failed, the feature is not supported.
```

在仅安装 CANN cann-9.0.0 toolkit 的 Linux 容器内，torch_npu 2.9.0.post6 的 torch.npu.set_device(0) 在 aclInit 阶段失败，报 NPU function error: aclInit, error code is 507008，并伴随 Failed to obtain the SOC version、rtGetDevMsg execution failed, the feature is not supported、chipType=0 does not support get device msg feature。

### 轨迹实例（aclInit 507899 / /dev/davinci* 缺失 / drvGetDevNum rc=7）


按场景构造完成后执行基线（构造过程见 [长序列 Prefill 场景的确定性恰好 2048 token 输入构造：词边界裁剪保留 BOS + prompt 内嵌 YAML 单命令复现](../validations/prefill_token_bos_prompt_yaml.md)）：

```
cd ${LOCAL_PATH_4} && timeout 300 bash infer.sh config/hunyuan_a13b_fp8_prefill2048.yaml > optimization-analysis/hunyuan_a13b_fp8/baseline_run_attempt.log 2>&1; echo "exit=$?"; tail -40 optimization-analysis/hunyuan_a13b_fp8/baseline_run_attempt.log
```

结果 exit=1，`baseline_run_attempt.log` 尾部（逐字）：

```
RuntimeError: Initialize:../torch_npu/csrc/core/npu/sys_ctrl/npu_sys_ctrl.cpp:165 NPU function error: aclInit, error code is 507899
[ERROR] 2026-10-17-12:01:00 (PID:116764, Device:0, RankID:-1) ERR00100 PTA call acl api failed
[Error]: An internal error occurs in the Driver module.
        Rectify the fault based on the error information in the ascend log.
[PID: 116764] 2026-10-17-12:00:47.373.938 Invalid_Argument(EL0003): The argument is invalid.
        Solution: Try again with a valid argument.
TraceBack (most recent call last):
        Call driver api drvGetDevNum failed, drvRetCode=7.[FUNC:GetDeviceCount][FILE:driver.cc][LINE:78]
        rtGetDeviceCount execution failed, reason=driver error:internal error[FUNC:FuncErrorReason][FILE:error_message_manage.cc][LINE:69]
        Call driver api drvGetDevNum failed, drvRetCode=7.[FUNC:GetDeviceCount][FILE:npu_driver.cc][LINE:146]
        Get device cnt failed, retCode=0x7020010[FUNC:CheckDeviceIdIsValid][FILE:api_error.cc][LINE:5057]
        drv devId is invalid, drv devId=0, retCode=0x7020010[FUNC:SetDefaultDeviceId][FILE:api_error.cc][LINE:5745]
        rtSetDefaultDeviceId execution failed, reason=driver error:internal error[FUNC:FuncErrorReason][FILE:error_message_manage.cc][LINE:69]
        [Process][DefaultDevice]process HandleDefaultDevice failed[FUNC:ReportInnerError][FILE:log_inner.cpp][LINE:132]
        chipType=0 does not support get device msg feature.[FUNC:GetDevMsg][FILE:api_impl_standard_soc.cc][LINE:619]
        The argument is invalid. Reason: rtGetDevMsg execution failed, the feature is not supported.
```

崩溃点在 `runner_hunyuan_a13b_fp8.py` 构造函数的 `torch.npu.set_device(local_rank)` → `aclInit`。

hunyuan_a13b_fp8 基线推理报 `RuntimeError: ... NPU function error: aclInit, error code is 507899`，伴随 `Call driver api drvGetDevNum failed, drvRetCode=7` 与 `torch.npu.device_count()==0`；若 /dev 下仅有 davinci_manager 与 hisi_hdc、没有 /dev/davinci0..N 设备节点，则根因是 NPU 设备节点未注册/未暴露给当前容器，而不是 CANN 安装或 torch_npu 版本问题。

## 探针与操作

### 原卡（保留）


1) 容器内设备与工具可用性探针：

```bash
ls /dev/davinci* 2>&1; env | grep -i -E "ascend|cann|npu" ; ls /usr/local/Ascend 2>&1
lspci 2>/dev/null | grep -i -E "huawei|d100|d80|davinci" ; ls /dev/davinci_manager /dev/devmm_svm /dev/hisi_hdc 2>&1
npu-smi info 2>&1 | head -20
```

逐字观测结果：`ls: cannot access '/dev/davinci*': No such file or directory`；`ls: cannot access '/dev/davinci_manager': No such file or directory`、`ls: cannot access '/dev/devmm_svm': No such file or directory`、`ls: cannot access '/dev/hisi_hdc': No such file or directory`；lspci 无任何 Ascend 匹配；`/usr/bin/bash: npu-smi: command not found`；`/usr/local/Ascend` 下仅有一个 driver 目录，CANN 环境变量（ASCEND_TOOLKIT_HOME、ASCEND_OPP_PATH 等）齐全。

观测容器内 /dev/davinci*、/dev/davinci_manager、/dev/devmm_svm、/dev/hisi_hdc 均不存在，npu-smi 命令不可用，lspci 过滤 Ascend 关键词无匹配，而 CANN cann-9.0.0 toolkit 已安装且环境变量齐全；这些观测证明容器内 NPU 访问不可用，但不能证明宿主机没有 NPU——设备未映射进容器、宿主机驱动未安装或命令在容器内不可用都是未被排除的替代解释。

2) 基础算子对照探针（在源码目录外 ${LOCAL_PATH_5} 执行，排除导入层干扰）：

```bash
timeout 60 python -c "
import torch, torch_npu
x = torch.ones(2,2).npu()
print((x*2).sum().item())
" 2>&1 | tail -5
```

逐字观测结果：

```text
        TraceBack (most recent call last):
        [Init][Version]init soc version failed.[FUNC:ReportInnerError][FILE:log_inner.cpp][LINE:132]
        chipType=0 does not support get device msg feature.[FUNC:GetDevMsg][FILE:api_impl.cc][LINE:6181]
        The argument is invalid.Reason: rtGetDevMsg execution failed, the feature is not supported.
```

同一解释器与包环境下，最基础的 .npu() 算子（torch.ones(2,2).npu()）以相同错误签名失败，说明失败发生在环境层的设备初始化，而非 aclgraph_test 用例自身的图捕获/回放逻辑。

3) CPU/仿真路径探针（检查默认安装是否存在 CPU/仿真运行模式）：

```bash
grep -rn -E "run_mode|RunMode" /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/npu/__init__.py | head -10
python -c "import torch_npu; print([m for m in dir(torch_npu.npu) if 'mode' in m.lower() or 'run' in m.lower() or 'cpu' in m.lower()])" 2>&1 | tail -2
strings /opt/buildtools/Python-3.11.4/lib/python3.11/site-packages/torch_npu/lib/libtorch_npu.so 2>/dev/null | grep -i -E "^(cpu|npu)_mode|set_run_mode|RunMode|simulation" | sort -u | head -20
```

逐字观测结果：第一个 grep 无输出；`dir(torch_npu.npu)` 中 mode/run/cpu 相关成员仅有 `['get_sync_debug_mode', 'set_compile_mode', 'set_sync_debug_mode']`；libtorch_npu.so 中唯一命中的仿真相关字符串为：

```text
The environment variable GE_INIT_DISABLE has been enabled, this switch is only used for single operator simulation
```

另在 torch_npu 源码树 grep `KERNEL_EXE_SIMULATION|SIMULATION_MODE|set_run_mode` 无命中；CANN toolkit 的 `tools/simulator/` 下存在 Ascend910B1 等多系列 simulator 目录（Ascend910B1 下仅 conf、lib），且 Ascend910B1/lib 已在本机 `LD_LIBRARY_PATH` 中。

在观测到的默认配置下，torch_npu 2.9.0.post6 无 set_run_mode 类 CPU 运行模式 API（dir(torch_npu.npu) 中 mode/run/cpu 相关成员仅 get_sync_debug_mode、set_compile_mode、set_sync_debug_mode），libtorch_npu.so 中唯一命中的仿真相关字符串为 GE_INIT_DISABLE 的单算子仿真提示；本轨迹未在 GE_INIT_DISABLE 或 simulator 模式下实际运行 aclgraph 用例，仿真模式能否承载 aclgraph 捕获/回放未经验证，不能据符号与字符串缺失断言所有 CPU/仿真替代路径不可行。

### 轨迹补充（2026-10）


按顺序执行下列只读探针（均不需要 NPU 权限）：

1. torch_npu 可用性（需 `bash -c 'source env.sh && ...'`，`/bin/sh` 无 source）：
   `bash -c 'source <model-dir>/env.sh && <venv>/bin/python -c "import torch, torch_npu; print(torch.__version__); print(torch.npu.is_available()); print(torch.npu.device_count())"'`
2. 设备节点：`ls -la /dev/davinci*`；`ls /dev/ | grep -i -E 'dav|ascend|hisi'`
3. 驱动安装：`ls -la /usr/local/Ascend/driver/`（关注目录时间戳）、`cat /usr/local/Ascend/driver/version.info`
4. 权限与恢复能力：`id`；`ls -la /usr/local/Ascend/driver/device/`；`sudo -n true && echo SUDO_OK || echo SUDO_NEEDS_PASSWORD`
5. 驱动模块与字符设备：`lsmod | grep -i -E 'davinci|ascend|drv'`；`cat /proc/devices | grep -i -E 'davinci|ascend|devdrv|vascend|hisi'`；`ls -la /sys/class/devdrv-class/ /sys/bus/mdev/devices/`

设备节点探针输出（逐字）：

```
/bin/sh: 1: npu-smi: not found
=== ls /dev/davinci* ===
crw------- 1 root root 511, 0 Oct 17 10:22 /dev/davinci_manager
=== ls /dev/ | grep -i -E 'dav|ascend|hisi' ===
davinci_manager
hisi_hdc
```

source env.sh 后的 torch_npu 探针输出（逐字，节选尾部）：

```
${TORCH_NPU_ROOT}/npu/__init__.py:402: UserWarning: Can't get ascend_hal device count
  warnings.warn("Can't get ascend_hal device count")
torch 2.12.0+cpu
torch_npu 2.12.0
npu available False
device count 0
DrvMngGetConsoleLogLevel failed. (ret=4)
```

## 机制与判别

### 原卡（保留）


- 判别一（环境级 vs 用例级）：基础 `.npu()` 算子探针与用例在 `set_device(0)` 处的失败同签名（init soc version failed、chipType=0、rtGetDevMsg 不支持），而基础算子不涉及 torchair/aclgraph 的任何图逻辑；最基础算子同样失败，可把问题归到环境层设备初始化，不必先怀疑用例逻辑。导入层若先报 `ImportError: cannot import name '_C'`，属源码目录遮蔽安装版的另一根因，判别与规避见 [torch_npu 源码目录下 import 触发 _C circular import 的判别与规避](torch_npu_source_dir_circular_import.md)。
- 判别二（容器内 NPU 访问不可用 vs CANN 未安装）：CANN cann-9.0.0 toolkit 已安装且环境变量齐全，但容器内设备文件全部缺失、npu-smi 不可用，属于「toolkit 有、容器内设备访问无」的形态；错误码 507008 出现在 aclInit 的 SOC 版本获取路径（rtGetDevMsg → chipType=0），与容器内无可用设备侧的形态一致。
- 判别三（宿主机硬件状态不可判定）：设备探针均在容器内执行，宿主机是否有 NPU、设备是否未映射进容器、宿主机驱动是否安装、npu-smi/lspci 是否因容器环境缺失而不可用，都无法从本轨迹观测区分；「宿主机无 NPU 硬件」保持未证实，不应作为已确立结论使用。
- 仿真替代的边界：符号/字符串探针只覆盖默认安装的 API 表面（无 set_run_mode 类 API、GE_INIT_DISABLE 自述 only used for single operator simulation），不构成对仿真模式的运行验证；本轨迹的 aclgraph 失败发生在默认配置下，GE_INIT_DISABLE/仿真模式下的 aclgraph 行为没有对照数据。
- 本卡不涉及 aclgraph_test 用例自身的多图共享输入污染机制结论（该机制链在本轨迹内无任何设备观测，仅为用例文件文档串记载）。

### 轨迹补充（2026-10）


判别链（每一环都有客观观测支撑）：

1. 不是 torch_npu 安装问题：venv 内 torch/torch_npu 版本正常（2.12.0+cpu / 2.12.0），source env.sh 后可导入。
2. 不是 CANN 库路径问题：不 source env.sh 时 `ImportError: libhccl.so: cannot open shared object file`（另一类故障），source 后消失——CANN 库路径与设备节点缺失是两类独立故障。
3. 是设备节点缺失：`/dev` 全量列表中 davinci 相关只有 `davinci_manager`（字符设备 511,0）与 `hisi_hdc`（509,0），没有 `/dev/davinci0..N`，也没有 devmm/devdrv 类节点；`/sys/class/devdrv-class/` 为空、`/sys/bus/mdev/devices/` 为空。
4. 驱动本身已加载：lsmod 列出 asdrv_buff/asdrv_vnic/asdrv_trs/asdrv_svm/asdrv_esched/drv_pcie_hdc_host/drv_vascend/asdrv_dms/asdrv_fms/asdrv_vmng/asdrv_dpa/drv_pcie_host/ascend_adapter/asdrv_vpc/asdrv_pbl/drv_seclib_host/asdrv_vascend_adapt/ascend_kernel_open_adapt/mdev/vfio 等模块；`/proc/devices` 已注册 `509 hisi_hdc`、`510 devdrv-cdev`、`511 hisi_davinci_intf`。
5. 时间线佐证：`/usr/local/Ascend/driver/` 及 `host_sys_init.sh`/`host_servers_setup.sh` 等目录时间戳为 10-17 10:13（驱动重装），`/dev/davinci_manager` 为 10-17 10:22，此后设备节点始终未注册；10-10 的历史基线在同一 case 上成功，说明是环境状态变化而非代码变化。

该环境驱动模块实际已加载（lsmod 可见 asdrv_*、drv_pcie_host、ascend_adapter 等模块，/proc/devices 已注册 509 hisi_hdc、510 devdrv-cdev、511 hisi_davinci_intf），/usr/local/Ascend/driver 于当日（10-17 10:13）重装后 /dev 设备节点始终未生成，故障定位在设备节点注册/暴露环节。

不 source env.sh 时 torch_npu 因找不到 libhccl.so 导入失败，source 后 torch 2.12.0+cpu / torch_npu 2.12.0 可正常导入但仍 npu available False、device count 0——CANN 库路径问题与设备节点缺失是两类独立故障，只有后者在本环境无解。

普通用户无法自助恢复：sudo 需要密码（SUDO_NEEDS_PASSWORD），host_sys_init.sh/host_servers_setup.sh 等设备初始化脚本属 root 且 /usr/local/Ascend/driver/device 无权限访问，需运维把物理/vNPU 设备暴露给容器并生成 /dev/davinci* 后重跑基线。

## 验证信号

### 原卡（保留）


以下均为本轨迹内的单次观测（tool 输出，证据等级 tool_observed；无设备验证，无有卡对照）：

- 从仓根运行 `tests/aclgraph_test.py`：`torch.npu.set_device(0)` → `aclInit, error code is 507008`，`Failed to obtain the SOC version`，`rtGetDevMsg execution failed, the feature is not supported`，`chipType=0 does not support get device msg feature`（容器环境，2026-10-22 观测）。
- 基础 `.npu()` 算子对照（${LOCAL_PATH_5} 下执行）：同签名失败。
- 容器内设备探针：`/dev/davinci*`、`/dev/davinci_manager`、`/dev/devmm_svm`、`/dev/hisi_hdc` 均不存在；`npu-smi: command not found`；lspci 过滤无 Ascend 匹配。宿主机硬件与驱动状态未观测。
- 仿真路径探针：`dir(torch_npu.npu)` 仅 `get_sync_debug_mode`、`set_compile_mode`、`set_sync_debug_mode`；libtorch_npu.so 仅 GE_INIT_DISABLE 单算子仿真开关字符串；torch_npu 源码树 grep 仿真模式开关无命中。仿真模式下的 aclgraph 运行无观测。

### 轨迹补充（2026-10）


（均为本轨迹单次观测，平台：容器 + CANN 9.1.0 + torch_npu 2.12.0，目标 Ascend950PR）

| 信号 | 事件序号 | 说明 |
|---|---|---|
| 基线 exit=1 + aclInit 507899 错误链 | T 187 | baseline_run_attempt.log |
| source env.sh 后 device count 0 | T 80 | npu available False |
| /dev 仅有 davinci_manager + hisi_hdc | T 84 | 无 /dev/davinci0..N |
| 不 source env.sh 时 libhccl.so 导入失败 | T 69 | 独立的 CANN 路径故障 |
| 驱动目录 10-17 10:13 重装 | T 90 | host_sys_init.sh 等同批时间戳 |
| driver/device 目录 Permission denied | T 94 | 普通用户不可访问 |
| lsmod 驱动模块已加载 | T 99 | asdrv_*/drv_pcie_host 等 |
| SUDO_NEEDS_PASSWORD | T 100 | 无免密 sudo |
| /proc/devices 注册 509/510/511 | T 108 | 字符设备主号在，节点缺失 |
| 历史基线（10-10）可跑 | T 48 | Ascend950PR_9589 prefill 1923 ms（旁证） |

## 适用与失效边界

### 原卡（保留）


- 适用：torch 2.9.0+cpu + torch_npu 2.9.0.post6 + CANN cann-9.0.0 toolkit、容器内无 NPU 设备访问的 Linux 容器；对其他 torch_npu/CANN 版本组合的签名一致性未验证。
- 失效/边界：缺少有卡环境中同命令的成功对照，不能断言 507008 + chipType=0 仅出现在容器内无 NPU 访问的场景；「宿主机有 NPU 但设备未映射或驱动异常」是否呈现相同签名未知。若设备文件存在仍报此错，应转向驱动/固件版本排查而不是套用本结论。本判别链只覆盖导入成功之后的设备初始化失败；若在 torch_npu 源码树内先遇到 `ImportError: cannot import name '_C'`（circular import），属源码目录遮蔽安装版的另一根因，判别与规避见 [torch_npu 源码目录下 import 触发 _C circular import 的判别与规避](torch_npu_source_dir_circular_import.md)，不适用本卡。同类 bringup 阶段环境/驱动层错误的泛化经验（如 docker 未透传设备的 aclInit 107001）见 [昇腾 bringup 初始化/HCCL 报错的根因常在环境/驱动/平台层](bringup_error_root_cause_env_driver_platform.md)。
- 停止/回退条件：确认容器内设备文件与 npu-smi 均缺失后，应停止在该容器内继续尝试任何 NPU 初始化路径（包括用例的各种参数组合）。后续路线按证据选择：先核实宿主机硬件、容器设备映射与驱动状态（本轨迹未做）；若确认宿主机确无 NPU，再转移到装有驱动+固件的真实 Ascend 910 设备 source CANN `set_env.sh` 后运行（助手会话建议，本轨迹未验证）。GE_INIT_DISABLE + simulator 仿真路径对 aclgraph 捕获/回放的可行性未经验证，如需评估须另行实测，不应默认可用或不可用。

### 轨迹补充（2026-10）


- 适用：torch_npu 推理在容器/虚拟化环境报 aclInit 507899 + drvGetDevNum rc=7 + device_count==0，且 /dev 无 davinci0..N 的情形。
- 不适用：/dev/davinci* 存在时的 aclInit 失败（可能是权限、驱动-固件/CANN 版本不匹配等其他原因，本轨迹未覆盖）；libhccl.so 导入失败属 CANN 环境变量/LD_LIBRARY_PATH 问题，source 正确的 env 即可解决。
- 停止/回退条件：探针确认"无 /dev/davinci* + 驱动已加载 + 无免密 sudo"三要素后，应立即判定基线 BLOCKED，只回报阻塞原因与所需运维操作（生成 /dev/davinci* 或提供可达 NPU 节点+卡号），不要伪造基线或强行绕过。
- 恢复后动作：按场景记录中保存的单命令（`bash infer.sh config/hunyuan_a13b_fp8_prefill2048.yaml` 及 golden 采集脚本）重跑即可产出基线。
- 未知项：设备节点未生成的精确根因（驱动重装未完成 vs 容器设备暴露配置缺失）无法从容器内判定，需运维侧确认。
