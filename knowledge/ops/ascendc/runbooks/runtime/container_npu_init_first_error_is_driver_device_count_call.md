---
type: "Runbook"
title: 容器内 NPU 初始化失败：首错应读驱动设备计数调用，而非下游 aclInit 返回
description: 非特权容器里上板初始化失败时，日志最醒目的 aclInit 返回往往不是首错；按时间戳向上找到的是 drvGetDevNum ret=87/num=0（设备计数调用失败，不是"枚举出 0 张卡"），其后 have device=0 → soc version 为空 → InitSocVersion 507008 → aclInit 500000。同一进程里 DrvGetApiVersion/DrvGetHostFreq 成功，故"驱动可达"与"设备可计数"是两件事；87 名为 RESOURCE_OCCUPIED、88 才是权限码，但 87 不指名资源或进程。附两臂对照（设备供给路径、注入驱动库来源、libc_sec/libmmpa 来源同时改变后首错不变——这不构成单项排除）、ascend runtime 实际注入的 11 项清单与其与宿主 /usr/lib64 副本的字节差异，以及一条范围仅限无设备环境（对照项 drvErr=4）的单变量身份 A/B。
tags: [task.debugging, topic.implementation.debugging]
status: draft
sources: []
created_at: '2026-10-20T09:47:11Z'
updated_at: '2026-10-20T09:47:11Z'
platforms: ["950"]
aliases:
  - "drvGetDevNum"
  - "get platform info failed drvErr=87"
  - "halGetDeviceInfo drvRet=87"
  - "have device=0"
  - "InitSocVersion 507008"
  - "aclInit 500000"
  - "RESOURCE_OCCUPIED"
---

# 容器内 NPU 初始化失败：首错应读驱动设备计数调用，而非下游 aclInit 返回

> **审查范围说明（2026-10-31）**：本卡所列 `tool_observed` 观测属原作者的私有轨迹，本轮内容审查**未重放**这些观测，只核对了正文内部的推断是否被所述证据支持。这不要求新实验，也不把未重放读成不成立。

## 现象

Ascend950DT 开发机，CANN 9.2.0，npu-smi `26.2.0.b020`。非特权容器（uid 1000、
`cap-drop ALL`、`no-new-privileges`、只读 rootfs），容器内用 ctypes 直调
`libascendcl.so` 做最小初始化探针，`aclInit` 返回非零。日志里最醒目的通常是
`aclInit` 的返回或一条 `Resource_Busy` 文案；照它去查"卡被占用 / 设备正在复位 /
软件未就绪"，再更换物理卡重试，会把同形失败重复若干次。**`aclInit` 的返回不是
首错。**

按时间戳把同一进程的日志向上读，真实顺序是（同一次运行，微秒级时间戳）：

```text
.208.761  [ERROR] ATRACE   trace_driver_api.c  get platform info failed, drvErr=87
.2xx.xxx  [INFO]  ASCENDCL acl.cpp             aclInitImpl: start to execute aclInit   <- aclInit 到这里才开始
.2xx.xxx  [INFO]  PROFILING platform.cpp       Succeeded to DrvGetApiVersion version: 0x7241a
.2xx.xxx  [INFO]  PROFILING ai_drv_dev_api.cpp Succeeded to DrvGetHostFreq frequency=100000 kHz
.218.797  [ERROR] PROFILING ai_drv_dev_api.cpp Failed to drvGetDevNum, ret=87, num=0
.2xx.xxx  [WARN]  PROFILING config_manager.cpp Get device num -1.
.218.863  [ERROR] PROFILING ai_drv_dev_api.cpp Failed to get device 0 status.
.2xx.xxx  [ERROR] RUNTIME   runtime_keeper.cc  GetDeviceType: Call halGetDeviceInfo failed: drvRet=87
.2xx.xxx  [INFO]  RUNTIME   runtime_keeper.cc  hardwareVersion=0xffffffffffffffff
.2xx.xxx  [INFO]  RUNTIME   runtime.cc         InitChipTypeAndSocVersion: device type=0, soc version=, have device=0
.2xx.xxx  [WARN]  RUNTIME   api_c_soc.cc       GetSocVersionStr: The soc version obtained by traverse device is empty
.2xx.xxx  [INFO]  ASCENDCL  acl_rt_impl_base   InitSocVersion: Cannot get soc version, runtime errorCode is 507008
.2xx.xxx  [ERROR] ASCENDCL  acl.cpp            aclInitImpl:[Init][Version]init SoC version failed
          aclInit 返回 500000
```

两个要点：**第一条 `drvErr=87` 出现在 `aclInit` 开始之前**，是库初始化期间
ATRACE 自己的驱动 API 调用；而 `aclInit` 的返回值是**下游后果**——设备计数拿不到
⇒ `have device=0` ⇒ SoC version 为空 ⇒ `InitSocVersion` 报 `507008` ⇒ `aclInit`
失败。本例 `aclInit` 返回 **`500000`**。

## 适用场景

- 工程形态：容器内上板运行自有候选件、算子 ST/UT、任何先调 `aclInit` 的路径。
- API 路径：`aclInit`、`aclrtSetDevice`、`aclrtGetDeviceCount`（`libascendcl.so`）、
  `halGetDeviceInfo`、`drvGetDevNum`、`npu-smi`、`/dev/davinci*`。
- 验证过的平台与版本：Ascend950DT，CANN 9.2.0，容器内 CPython 3.11。
- 适用粒度：platform_wide（判别方法与具体算子、具体消费者无关）。
- 路线优先级：recommended_fastpath（读日志顺序是标准做法）。
- 明确不适用：`aclInit` 返回 0 而 `aclrtSetDevice` 失败的情形——那属于
  [绕过 ascend docker runtime 导致驱动库未注入](507033_container_ascend_runtime_device_injection.md)
  与 [is_available=True 仍 507033](../validations/is_available_true_507033_probe.md)
  的判别范围，**首错点不在同一层**，不要混用它们的观测矩阵。

## 判别方法

**第一步：按时间戳找最早的 `drvErr`，不要从最醒目的那行开始。**
先确保日志可见（`ASCEND_GLOBAL_LOG_LEVEL=1` 配合 `ASCEND_SLOG_PRINT_TO_STDOUT=1`
把链路取到可归档的输出里），再在全部 `[ERROR]` 行里按时间排序取第一条，并与
`aclInitImpl: start to execute aclInit` 的时间戳比较先后。若最早的 `drvErr` 早于
该行，`aclInit` 的返回码就不是首错，不要据它选排查方向。

**第二步：区分"驱动可达"与"设备可计数"。** 在同一进程里查这三条：

| 观测 | 含义 |
|---|---|
| `Succeeded to DrvGetApiVersion` / `Succeeded to DrvGetHostFreq` | 驱动接口对**宿主级查询**是通的，不能据此说设备可用 |
| `Failed to drvGetDevNum, ret=<n>, num=0` | **设备计数调用失败** |
| `have device=0` + `soc version=` 为空 | runtime 据上一条得出的结论，不是独立观测 |

⛔ `ret=87, num=0` 读作**调用失败**，不是"成功枚举并返回 0 张卡"。
`ret` 非零时 **`num` 的有效性未建立**——本卡没有该实现的源码或契约，而失败实现**完全可以**在返回错误前把出参清零或部分写入。所以只能说：**不能把 `num` 当成一次成功枚举的卡数**；至于它到底有没有被写，本卡**不作断言**。把它读成"0 张卡"会把排查引向"卡被占用"。

**第三步：把错误码当名字用，不当结论用。** 本机驱动头文件里 `87` 名为
`RESOURCE_OCCUPIED`，`88` 才是权限码。因此收到 `87` 时，权限类猜测是**弱解释**——但**不能排除**：实现完全可能把权限类失败折叠到同一个码上，而本卡没有该实现的源码可据以排除这种折叠；
但 `87` **既不指名哪个资源也不指名哪个进程**，公共实现里 `open` 与 `ioctl` 的
`EBUSY` 都可能呈现为 `87`，所以实际失败的 syscall 与被选中的实现分支**未确定**。
不要把"occupied"直接读成"另一个进程占着这张卡"——本例同期该卡的 `npu-smi`
进程表为空、`fuser` 对该节点返回 1。

**第四步：同一调用点的错误码会随是否有设备而变。** 同一镜像、同一探针：

| 容器形态 | 同一 `trace_driver_api` 调用点 |
|---|---|
| 有设备（手工 `--device` 或运行时注入） | `get platform info failed, drvErr=87` |
| 完全不传任何设备（容器内逐一断言节点不存在） | `get platform info failed, drvErr=4` |

⇒ **错误码本身不能用来判断节点是否传入**；要判断就直接在容器内 `stat` 节点。

**第五步：让容器自己说话。** 把宿主上真实的 `npu-smi` 可执行文件只读挂进容器
（镜像里可能只有桩），它会打印自己的候选原因：

```text
Failed to obtain the console log level. The possible causes are as follows:
 1. Different containers share the same device;
 2. Failed to open the character device when interacting with the OS kernel;
 3. Failed to obtain the number of devices.
dcmi model initialized failed, because the device is used. ret is -8020
```

三条里只有第 3 条被 runtime 的 `drvGetDevNum ... num=0` 印证；第 1、2 条在上述
观测中**没有证据**，不要替它选一条。⚠️ 第 1 条在多租户宿主上往往是**常态**：
本例宿主每张卡都被不少于 5 个他方特权容器映射，该条件天天成立，并不区分失败与
成功的那一天，所以它不构成可执行的归因，也不应据此派生换卡或停他方容器的动作。
这一步只恢复**可观测性**，本身不改变初始化结果。

## 两臂对照：同码，但这不构成单项排除

两臂，同一宿主、同一镜像、同一 ctypes 探针，**映射的是同一批 23 个对象**，差异
恰好两组；两臂**失败完全一致**（同调用点、同码、`aclInit=500000`）：

| 维度 | 臂 A（手工 `--device`） | 臂 B（运行时注入） |
|---|---|---|
| 设备供给 | 显式 `--device /dev/davinci<N>` 别名到 0，外加 11 个 uburma/ummu **leaf 节点** | `--runtime ascend` + `ASCEND_VISIBLE_DEVICES=<n>`，`Devices=[]`；注入真 `/dev/davinci<N>` 与 **`/dev/ummu`、`/dev/uburma` 目录** |
| urma/ummu 库来源 | 手绑宿主 `/usr/lib64` 副本到自有目录 | 运行时注入到容器 `/usr/lib64` |
| `libc_sec.so`/`libmmpa.so` | driver 前置 ⇒ 来自 `driver/lib64/common` | 原序 ⇒ 来自 `cann-9.2.0/lib64` |
| 结果 | `drvErr=87` → `drvGetDevNum ret=87,num=0` → `aclInit=500000` | **同上，一字不差** |

⛔ **不要把这张表读成"这三项都被排除了"。** 两臂**同时**改了设备供给路径、urma/ummu
库来源、`libc_sec`/`libmmpa` 来源、节点粒度，而且换了物理卡。两臂同码只说明**这两套
尝试都没有消除症状**；多项同时改变而结果不变，**不能排除其中任何单项的因果**——某一项
仍可能是必要条件而被另一项的变化掩盖，或几项共同作用。能写的只有："这两套具体配置
下，首错不变"。根因 **UNDETERMINED**。
要排除单项，必须在**其他一切不变**的条件下只改那一项，并且 A/B 做在该错误所在的环境里
（本卡末尾那条身份 A/B 就是这种形状，它因此可以下结论；两臂对照不是）。

另有一条独立成立的事实（与修不修通无关）：**运行时注入的驱动库不是宿主
`/usr/lib64` 的那几份字节。** 容器内从注入集读出的完整摘要与宿主同名文件逐一比对，
四个里**只有 `libummu.so.1` 相同**，`liburma.so.0`、`liburma_common.so.0`、
`urma/liburma-udma.so` **全不同**；尺寸也对得上：注入的 `liburma.so.0.0.3` 为
**264,648 字节**而宿主 `/usr/lib64/liburma.so.0.0.3` 为 **264,576 字节**，是不同
构建。⇒ **手绑宿主 `/usr/lib64` 副本从来不与运行时注入路径字节等价**，两者不可
互相代替地用于复现或对照。

### 运行时实际注入了什么（本机实测清单）

`--runtime ascend` + `ASCEND_VISIBLE_DEVICES=<n>` 下，容器 `/usr/lib64` 里出现
**11 项**：`libnl-3.so.200`、`libnl-genl-3.so.200`、`libummu.so`、`libummu.so.1`、
`libummu.so.1.0.4`（目录）、`liburma.so.0`、`liburma.so.0.0.1`（目录）、
`liburma.so.0.0.3`、`liburma_common.so.0`、`liburma_common.so.0.0.1`、`urma/`（目录）。
这证实了相邻卡关于"约 11 项驱动用户态库被注入"的说法，并给出确切清单。

两条观测，都**不**升级成结论：

- **`libnl-3.so.200` / `libnl-genl-3.so.200` 确实在注入清单里，但在上述两臂失败后
  取的 `/proc/self/maps` 快照里都不出现。** ⚠️ 末尾快照的缺席**不证明**它们从未被
  需要或从未被加载——失败的 `dlopen`、先载后卸都会表现为同样的缺席。记为
  UNDETERMINED。
- **运行时的注入集里没有 `/dev/hisi_soc_cache_mgmt`**（容器内 ABSENT）。该节点在
  宿主上存在但是 `crw------- root:root`。这是关于**注入集内容**的事实；它不等于
  "该节点与失败无关"，也不等于"该候选不成立"。`/dev/devmm_svm` 同样 ABSENT，且在
  本机宿主上根本不存在——后者是节点存在性的直接测量。

## 另一条真实但无关的缺件：镜像缺 uid 身份条目

镜像里可能完全没有所用 uid 的 passwd/group 条目（实测：某镜像 `/etc/passwd` 25 行、
`/etc/group` 47 行，uid/gid 1000 条目数均为 0；容器内 `stat` 设备节点的 owner 显示
为 `UNKNOWN:UNKNOWN`）。它在 CANN 日志里的形态是一组**看起来像成功**的 ERROR：

```text
[ERROR] ATRACE trace_attr.c  get uid and gid failed, uid=1000, strerr=Success.
[ERROR] ATRACE trace_attr.c  init attr id failed.
[ERROR] ATRACE trace_core.c  init attr failed, ret=-1.
```

`strerr=Success` 表示 errno 仍为 0——"查不到条目所以返回空"的形态，不是"调用
出错"。**只追加、可回退、不改宿主、不改实际 UID/GID、不加组成员或凭据**的修法：
把镜像自身的 `/etc/passwd` 与 `/etc/group` 复制到暂存目录，各追加**恰好一行**，
账号用**不可登录** shell（按镜像自身约定选择：实测该镜像 25 个账号里 22 个用
`/usr/sbin/nologin`），再以只读方式分别挂到 `/etc/passwd` 与 `/etc/group`；撤掉
这两个挂载即回退。

**A/B 实测（同一探针、同一**无设备**外壳，对照项是 `drvErr=4`）**：ATRACE 的 ERROR
行数 **4 → 1**，消失的正是上面那三条，`id` 由纯数字变为带名字；而
`get platform info failed, drvErr=4` **一字未变**。

⇒ 可以写的结论只有这一句，范围很窄：**在这个无设备、对照项为 `drvErr=4` 的环境里，
补齐身份清掉了 attr 那三条错误，而没有改变 `drvErr=4`。**
⛔ **不要把它写成"身份缺件不是 `drvErr` 的因"这种普遍说法**，它尤其**不覆盖带卡时的
`drvErr=87`**——那个环境里没有做过这条 A/B。身份缺件本身是真实的、修法是可逆的，
这两点成立；因果范围就只到上面那一句为止。
⛔ 另外**不要用日志行的先后顺序来排因果**——消息顺序只说明谁先打印，不能排除同一
身份状态影响其他调用路径；分离要靠单变量 A/B，而且 A/B 必须做在**你关心的那个错误
所在的环境里**。

## 设计决策

- 判别放在"读日志顺序"而不是"换卡重试"：换卡只能区分这张卡的瞬时状态，无法区分
  首错在哪一层；本例换卡会把同形失败重复若干次而不增加信息。
- 最小探针用 ctypes 直调 `libascendcl.so`，只调 `aclInit` 与 `aclrtSetDevice(0)`，
  **不遍历其他设备号、不调 reset**：目的是取首错，不是扫描设备空间；遍历会在失败
  路径上制造噪声，reset 会改变他人可见的设备状态。
- `aclInit` 非零即停，使日志末尾就是首错链，不被后续级联错误淹没。
- **`/proc/self/maps` 要在失败路径上也打印**：否则"装了哪份字节"无从回答，而容器
  一旦删除就不可恢复。记录每个对象的路径、`maps` 的 dev/inode 与该路径文件的完整
  sha256。⚠️ 这是**路径文件摘要**，用于标识装机对象的内容身份；它既不是映射进内存
  那些字节的凭证，也不构成与任何公共源码的绑定——除非额外 `fstat` 核对同一对象，
  否则不要声称更强的结论。
- 真实 `npu-smi` 只读挂载定位为**可观测性**措施：已有观测表明把桩换成真 ELF 并不
  消除 DCMI 侧报错，所以不把它当修法。
- `ldconfig` 这条路在只读 rootfs 下不可用（它要写 `/etc/ld.so.cache`）。⚠️ 但这
  **不**等于 `LD_LIBRARY_PATH` 是唯一解：通用 loader 在 cache 之后还会搜默认目录，
  本镜像是否搜某个目录要看实际解析。若确要补 `/usr/lib64`，**追加在末尾、不要
  前置**：前置会改变该进程里所有库的解析，不只目标那几个。

## 验证信号

来源说明：以下信号来自同一开发机上几条具体的容器臂与其对照臂的实际运行记录；
容器均为运行者自有、运行后已删除。

- 首错链（"现象"节的时间戳序列）与 `aclInit=500000`（来源平台：950；证据等级：tool_observed）。
- 同一进程内 `DrvGetApiVersion`/`DrvGetHostFreq` 成功而 `drvGetDevNum ret=87, num=0`（来源平台：950；证据等级：tool_observed）。
- 同一调用点在无设备容器为 `drvErr=4`、在有设备时为 `drvErr=87`（来源平台：950；证据等级：tool_observed）。
- 两臂映射同一批 23 个对象、差异恰为两组、失败一致（来源平台：950；证据等级：tool_observed）。
- 运行时注入 11 项清单；四个承载库中三个与宿主 `/usr/lib64` 同名文件字节不同；注入的 `liburma.so.0.0.3` 264,648 B 对宿主 264,576 B（来源平台：950；证据等级：tool_observed）。
- 容器内真实 `npu-smi` 返回码 172，正文含三条候选原因与 `ret is -8020`（来源平台：950；证据等级：tool_observed）。
- 身份 A/B：ATRACE ERROR 行 4 → 1，`drvErr=4` 不变（来源平台：950；证据等级：tool_observed）。
- 同一时期**宿主级** `npu-smi info` 正常返回全表（来源平台：950；证据等级：tool_observed）。
- 同一宿主上**某一张卡**的 `npu-smi info -t board -i <n>` 返回 `get npu info failed!` / `Failed to query "board" info.`，而同一次读里其他三张卡的同一查询成功、该卡的进程表与整机健康表均正常（来源平台：950；证据等级：tool_observed）。

## 失效边界

- **根因 UNDETERMINED。** 本卡只给判别与已排除项，不给驱动层根因；失败的 syscall
  （`open` 还是 `ioctl`）与被选中的实现分支都未确定。
- 现有证据是**几条具体的臂**，不是供给路径 × 栈 × 卡 × 消费者的完整交叉验证；不要
  据此宣称某条供给路径或某种容器形态被普遍否定。
- ⛔ **本卡不提供任何"某项已被排除为因"的结论**，只有"某套具体配置下症状不变"。
  多项同时改变的两臂对照不是单项排除。末尾那条**单变量**身份 A/B 是本卡唯一的因果
  陈述，而它的范围仅限**无设备、对照项为 `drvErr=4`** 的那一个环境；它**不覆盖带卡
  时的 `drvErr=87`**，那里没有做过该 A/B。
- 另有若干条臂由 `torch_npu` 侧报 `aclInit 507899` 与
  `Get device cnt failed / drv devId is invalid`。⚠️ 那是**另一条调用链**：消费者
  不同、返回码不同、入口不同，**不与本卡的链并称同根**，也不构成对本卡结论的复现。
- 某次失败运行的 `plog` 叶文件为空（观测：该目录下 `find -type f` 零条），因此
  `Dev open failed` / `Get dev list failed` / `Ioctl failed` 这一层的**原始行不在
  证据内**；该目录为空的原因未确定，"因为同时开了 stdout 重定向"只是一种说法，
  既不能证明每个 UDA 模块都走该流，也不能证明去掉该开关就能取回缺失的行。
- 调整 driver 与 CANN 在 `LD_LIBRARY_PATH` 中的先后：**该配置下实测不消除症状**，
  但顺序确实决定装载哪份 `libc_sec.so`/`libmmpa.so`（已由 maps 证实），所以这是
  "变量真实但对本失败无效"，不等于库序普遍无意义。
- 设备无关环境下成立的那些结论（候选件 `CDLL` 加载、符号绑定、实际映射）只属于
  **那一个无设备环境**，不是对后续所有环境的永久保证。
- 单张卡 board 查询失败一项：**原因未确定**，不与容器内的 `87` 并称，也不作为占用
  信号；它的用途只是"这样的卡不是可靠目标"。
- 未验证、推断可迁移：错误码语义（`87`/`88`/`500000`/`507008`）在其他 CANN 版本与
  芯片上应一致，但未实测。
- 恢复手段（驱动重载、root 复位、宿主侧变更）全部未验证，本卡不提供。

## 坏实践

- 把日志里最醒目的 `aclInit` 返回或 `Resource_Busy` 文案当首错，然后照它的三因去查
  "卡被占用"：本例里更早的 `drvErr=87` 才是首错，且同期该卡进程表为空。
- 把 `ret=87, num=0` 读成"枚举出 0 张卡"：`ret` 非零时 `num` 的**有效性未建立**，不能据此认定"成功枚举 0 卡"（也不能反过来断言它未被写入——本卡无源码/契约可据）。
- 在首错机制未变的情况下更换物理卡重试：每次都得到同形失败，不增加信息，还占用
  他人可用的卡。
- 用"哪条日志先打印"来排除因果：顺序只说明打印先后。
- 把容器配置记录当成可行性证据：某容器的 `--device` 列表是它**创建时**的记录，既
  不证明该节点此刻存在，也不证明那套形态曾经成功过；同理 `Devices=[]` 不等于运行
  中的容器没有设备。
- 把"非特权且带设备的容器有很多"当成该外壳已被验证：那是**配置行**计数，其中可能
  就包含同期失败的臂，配置计数不是成功计数。
- 手绑宿主 `/usr/lib64` 的 urma/ummu 副本去"等价替代"运行时注入：实测**四个里三个
  字节不同**，不等价。（这只说明两者不可互换地用于复现或对照，不说明哪一套"对"。）
- 改了好几项之后看到同一个错误码，就宣布这几项都被排除：那只说明这两套尝试都没消除
  症状。单项排除需要单变量 A/B。
- 为前置某个目录而改全局 `LD_LIBRARY_PATH` 顺序：会改变该进程里所有库的解析。

## 误诊

- 初判怀疑容器少传了内存管理类设备节点：实测该节点在本机**根本不存在**，候选作废；
  另一个被运行时清单提到的路径同样不存在。相邻卡在**另一台**机器上观测到该节点缺失
  并与失败同现，但它自己也写明充分必要未追到机制层——**节点清单是逐机事实，不能
  跨机沿用**。
- 初判怀疑非特权安全外壳不足以访问设备：按容器配置清点出大量"非特权且带设备"的
  历史条目后一度认为该外壳已被排除，**这是错的**，见上节。该外壳既未被证明足够、
  也未被证明不足。
- 初判怀疑镜像缺 uid 身份条目导致驱动调用失败：无设备环境下的 A/B 显示补齐身份后三条
  ATRACE ERROR 消失而该环境的 `drvErr=4` 不变。⚠️ 这只否掉了"它是那个环境那条错误的
  因"，**没有**否掉它与带卡 `drvErr=87` 的关系——后者未做该 A/B。
- 初判怀疑 urma 插件集不全（宿主 `urma/` 目录里有一个未被手绑的 `liburma_ubagg.so`）：
  它不在失败后那次 `maps` 快照里，但**末尾快照的缺席不能排除失败的 `dlopen` 或先载
  后卸**，所以这条是 UNDETERMINED，不是已排除；也不据此去补插件。
- 一度把"两臂同码"写成"三项作为因已被排除"：这是把"没消除症状"误当成"已排除因果"。
  多项同时改变的对照只能否掉"这两套配置可用"，不能否掉任何单项的必要性。
