---
type: "Runbook"
title: 容器内 aclrtSetDevice 507033：绕过 ascend docker runtime 导致驱动库未注入
description: 宿主 docker 的 Default Runtime 为 ascend 时，必须用 -e ASCEND_VISIBLE_DEVICES=<n> 让运行时注入设备；手工 --device 只拿到设备节点、拿不到 liburma/libummu 驱动库，TSD/HDC 起不来，aclrtSetDevice 报 507033（链路 Init UB context failed → drvHdcSessionConnect → InitTsdClient → TsdOpen failed → Start AI CPU executor failed → DeviceRetain）。--privileged 不能替代：缺的是库不是权限（实测同样失败）。伴随三个坑：镜像 ld.so.cache 构建期生成不认运行时注入的库需把 /usr/lib64 加入 LD_LIBRARY_PATH；整目录挂宿主 /usr/lib64 会换掉 glibc 连 head/grep 都崩；镜像 /etc/ascend_install.info 为 0 字节会让 set_env.sh 在调用方 pipefail 下静默杀 shell、零输出。
tags: [task.debugging, topic.implementation.debugging]
sources: []
status: draft
platforms: ["950"]
aliases:
  - "aclrtSetDevice 507033"
  - "Init UB context failed"
  - "TsdOpen failed"
  - "Start AI CPU executor failed"
  - "ASCEND_VISIBLE_DEVICES"
  - "ascend-docker-runtime"
  - "liburma.so.0 cannot open shared object file"
  - "Different containers share the same device"
  - "__tunable_is_initialized GLIBC_PRIVATE"
  - "Kill should be on/off"
created_at: '2026-10-10T09:55:00Z'
updated_at: '2026-10-29T22:55:14Z'
---

# 容器内 aclrtSetDevice 507033：绕过 ascend docker runtime 导致驱动库未注入

> **来源说明（2026-10-31）**：本卡结论来自车队私有实测/推理，暂无可公开复核的原始出处；按社区评审口径以 draft 收录，待补可复核来源后回升。
> 证据状态：历史 draft 待补工具记录。本文的成功配方与根因归纳沿用原卡自述，当前仅作待验证线索，不视为新验证知识；原失败日志片段与配方文字保留供追查。

## 现象

在一台 Ascend950DT 宿主上，用**手工 `--device`** 起的容器里执行算子，`aclInit` 成功但 `aclrtSetDevice` 失败。
标题里的 **507033 是错误码**——`aclrtSetDevice` 的返回值，runtime 侧记为 `rtSetDevice` 的 `ErrCode=507033`（`desc=[device retain error]`），不是本卡自编的编号：

```text
FAILED aclrtSetDevice(0) rc=507033
[ERROR] DRV  hdc_ub_drv.c:1287 [hdc_ub_connect] Init UB context failed.(ret=0; dev_id=0; session_id=109; service_type="service_TSD")
[ERROR] TDT  hdc_client.cpp:158 drvHdcSessionConnect failed, ret = -1
[ERROR] TDT  device_comm_agent.cpp:56 [TsdClient][deviceId=0] CreateSession for TSD failed
[ERROR] TDT  tsd_client.cpp:28  TsdOpen failed, deviceId[0]
[ERROR] RUNTIME runtime.cc:3164 DeviceRetain:Start AI CPU executor failed, retCode=0x7020009
[ERROR] RUNTIME api_c_device.cc:82 rtSetDevice:ErrCode=507033, desc=[device retain error]
```

容器内 `npu-smi info` 正常显示该卡、`/dev/davinci<N>` 存在、健康 OK —— **设备可见但不可初始化**。重启宿主后现象不变（非临时状态）。

## 适用场景

- **工程形态**：在宿主 docker 的 `Default Runtime` 为 `ascend` 的机器上，自建容器跑自定义算子（非框架镜像自带脚本）。
- **判别前提**：`docker info` 显示 `Runtimes: ascend runc` 且 `Default Runtime: ascend`。
- **已验证平台**：Ascend950DT，驱动 26.2.0.b020 / ascendhal 7.35.23，宿主 CANN 9.2.0（innerversion B213），镜像自带 CANN 9.2.0（B056）。
- **适用粒度**：`operator_family` —— 与具体算子无关，属容器接入方式。
- **路线优先级**：`recommended_fastpath`。
- ⚠️ **首错点不同的相邻情形**：若 `aclInit` 本身返回非零、且按时间戳更早出现 `drvGetDevNum`/`halGetDeviceInfo` 的 `drvErr`，那不是本卡这一层，见 [容器内 NPU 初始化失败：首错应读驱动设备计数调用](container_npu_init_first_error_is_driver_device_count_call.md)。该卡另有本卡注入清单的逐项实测（11 项）及一条补充事实：**运行时注入的 urma/ummu 库与宿主 `/usr/lib64` 同名文件字节不同**（四个里三个不同），故手绑宿主副本不等价于运行时注入路径。
- **不适用 / 未验证**：不解释 GID/权限类、驱动与 CANN 版本不匹配类、或其他成因的 507033（见失效边界）。

## 根因

`ascend` docker runtime 的接口是**环境变量**，不是 `--device`。用 `-e ASCEND_VISIBLE_DEVICES=<n>` 时，运行时不仅注入设备节点，**还把驱动用户态库注入容器 `/usr/lib64`**：实测注入 `liburma.so.0`、`liburma.so.0.0.1/0.0.3`、`libummu.so(.1)`、`libnl-3.so.200`、`libnl-genl-3.so.200` 共约 11 项。

手工 `--device /dev/davinci<N> --device /dev/davinci_manager --device /dev/hisi_hdc` **只给到设备节点，不给这组库**。TSD（Task Scheduler Daemon）要通过 HDC 在 UB（Unified Bus）上建会话才能把 AI CPU 包加载到设备，缺库则 `Init UB context` 直接失败 —— 于是设备"看得见、初始化不了"。

**`--privileged=true` 不能替代，实测同样失败**：它放开的是权限，而缺失的是库。这一点很容易误判，因为现象（设备节点齐全却起不来）看起来像权限问题。

## 解决配方

```bash
# 宿主实际的 CANN 安装目录与工作目录，按机器填一次；容器内保持同路径挂载
CANN_DIR=/usr/local/Ascend/cann-9.2.0
WORK_DIR=<工作目录绝对路径>

docker run -itd --name=<agent>-<task>-<hostLastOctet>-npu-<yyyymmdd> \
  -e ASCEND_VISIBLE_DEVICES=<调用者已获准的物理卡号，逐个列出> \
  --net=host --shm-size=10g \
  -v "$CANN_DIR:$CANN_DIR:ro" \
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
  -v "$WORK_DIR:$WORK_DIR" \
  <image> bash
# 容器内必须：
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}:/usr/lib64
```

非 privileged、不手工挂设备、只有自己的工作目录可写。

⛔ **`ASCEND_VISIBLE_DEVICES` 只列调用者已明确获准的物理卡，不要给全卡范围。** 原文曾以「给全卡可避免换卡时重建容器，运行时再用 `ASCEND_RT_VISIBLE_DEVICES` 选具体卡」为由推荐 `0-7`，**该建议已撤回**：`ASCEND_RT_VISIBLE_DEVICES` 是**应用层可见性开关**，它既不构成容器的设备权限边界，也不收回已经授予的权限；而枚举发生在该掩码生效之前。换卡就重建容器，这个成本应当付。（「可见不等于占用」这句仍然成立，但它说的是占用判断，不是授权判断。）

### 伴随的四个坑（都实测过）

1. **`ld.so.cache` 是镜像构建期生成的，不认识运行时后来注入的库。** `liburma.so.0` 明明在 `/usr/lib64` 仍报 `cannot open shared object file` ⇒ 必须把 `/usr/lib64` 加进 `LD_LIBRARY_PATH`（或 `ldconfig`）。
2. **不要整目录挂宿主 `/usr/lib64`。** 宿主 glibc 2.38（openEuler）vs 镜像 2.35（Ubuntu），覆盖后连 `head`/`grep` 都起不来：`symbol lookup error: /usr/lib64/libc.so.6: undefined symbol: __tunable_is_initialized, version GLIBC_PRIVATE`。⛔ **不要把「镜像 glibc 与宿主一致」当成可以整挂的条件——该例外已删除。** 同版 glibc 不保证其余用户态库与 loader 全都兼容，而且整目录覆盖本身不是正确修法。正确做法只有两条：让运行时注入它需要的驱动库，以及**按 SONAME 精确只读挂载**你确实需要的那几个文件。加 `LD_LIBRARY_PATH` 之所以安全，正因为运行时只往那注入了那约 11 个驱动库。
3. **镜像里 `/etc/ascend_install.info` 可能是 0 字节。** `set_env.sh` 内部 `set -e`，其中 `grep -iw driver_install_path_param /etc/ascend_install.info | cut -d= -f2-` 不命中返回 1；调用方若开了 `pipefail`，**source 会直接把调用方 shell 杀掉：退出码 1、零输出、日志一行不写**，看起来像"脚本没跑"。挂宿主那份 `:ro` 解决。
4. **本次历史同现与恢复记录（不是一般定律）**：当时同一宿主上自己另一个容器也映射了同一批设备，出现 `Failed to obtain the console log level… 1. Different containers share the same device`，停掉自己那个设备容器后同一条命令立即成功（`docker stop` 实测）。
   ⚠️ **不能据此断言「映射重叠必然冲突」。** 该报错文本是驱动列出的**候选原因之一**，不是归因；本记录也没有做解除重叠后的单变量复测。反例已实测：2026-10-31 有非特权容器在**五个容器同时声明 davinci0-7** 的情况下仍成功打开并计算某张卡。⇒ 映射重叠只记为冲突时的**同现事实**；卡能不能用，只能由**使用那一刻从自己的载体做一次真实设备打开**来判定。

另：镜像自带 CANN B056 的 `msprof` 不接受 `--kill=true`，报 `[ERROR] Kill should be on/off`；宿主 B213 接受。挂宿主 CANN 可同时解决这点并与构建工具链一致。

## 验证信号

当前未建立本卡成功配方的 `tool_observed` / `artifact_verified` 验证信号。本次只核对固定历史卡片字节，未执行设备、容器或算子实验；原卡自述不能补成工具证据。后续须先绑定实际命令、输出及其来源，才可将相应范围移入本节。

## 误诊

原卡固定提交 `fe8eb3e9` 的下列四项只保留为 `agent_reported` 历史线索。固定提交证明原卡曾如此陈述，不证明所述操作确已成功；不能据这些文字把当前环境或跨平台问题判为已修复。

- 来源平台（原卡自述）：Ascend950DT；证据等级：agent_reported（原始工具记录未绑定）。容器内 `ls /usr/lib64 | grep -E 'liburma|libummu'` 非空，仅证明同名文件存在；注入来源须结合 runtime 配置、实际挂载及文件身份核对，不能单凭文件名断言注入成功。
- 来源平台（原卡自述）：Ascend950DT；证据等级：agent_reported（原始工具记录未绑定）。`ldd <你的二进制> | grep 'not found'` 为空，只覆盖该二进制当时可解析的依赖，不能单独证明设备初始化成功。
- 来源平台（原卡自述）：Ascend950DT；证据等级：agent_reported（原始工具记录未绑定）。`docker info | grep -A2 Runtimes` 显示 `Default Runtime: ascend`；仍需核对本次容器实际使用的 runtime 和设备环境变量。
- 来源平台（原卡自述）：Ascend950DT；证据等级：agent_reported（原始工具记录未绑定）。原卡报告修复后同一二进制 `aclrtSetDevice` 成功、S=256 产出 `QFAG_SHAPE`/`QFAG_WS_SIZE` 且无 507033；这是该历史平台的一次结果自述，不是新测量或跨平台保证。

## 失效边界

- **只解释"运行时未注入驱动库"这一类 507033。** 不涵盖 GID/权限、驱动与 CANN 不匹配、设备被占用等其他成因。**反例**：同期另一实例在修正 GID 后仍为 `device_count=0` / `aclInit 507899`，原因 UNKNOWN —— 不能据本卡断言所有 507033 共用同一机制。
- 第 2 条的 glibc 冲突绑定具体镜像与宿主发行版，换镜像需重新核对。
- `/dev/devmm_svm` 在本卡验证的驱动版本（26.2.0.b020）上**不存在**；照抄含该设备的旧指引会失败。
- 本卡未验证严格 worker 沙箱（bwrap）内的可读性与注入行为。
