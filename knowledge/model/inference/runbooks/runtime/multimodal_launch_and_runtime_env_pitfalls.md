---
type: Runbook
title: 一站式平台/未激活环境拉起多模推理的环境与运行期坑（torchrun PATH / cv2 static-TLS / TBE 首调缺依赖 / 退出双重释放）
description: 一站式平台/未激活环境拉起多模推理的环境与运行期坑（torchrun PATH / cv2 static-TLS / TBE 首调缺依赖 / 退出双重释放）。在 CANNLab 一站式平台默认环境（未 conda activate）或 aarch64 上拉起多模态推理（mm 推理启动链：infer.sh → executor/scripts/mm_function.sh）时，几类报错发生在意外阶段、易误读为算子/CANN 问题，实为环境未就绪。对号入座即可。
tags:
- task.debugging
- topic.multimodal
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/246
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/250
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/369
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/372
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 一站式平台/未激活环境拉起多模推理的环境与运行期坑（torchrun PATH / cv2 static-TLS / TBE 首调缺依赖 / 退出双重释放）

## 适用场景

在 CANNLab 一站式平台默认环境（未 `conda activate`）或 aarch64 上拉起多模态推理（[mm 推理启动链](../../concepts/frameworks/mm_inference_launch.md)：`infer.sh → executor/scripts/mm_function.sh`）时，几类**报错发生在意外阶段、易误读为算子/CANN 问题**，实为环境未就绪。对号入座即可。

## 症状 → 根因 → 修法

### A. 裸调 torchrun 报 command not found

- 信号：`mm_launch_task` 裸调 `torchrun` 报 `torchrun: command not found`（python 本身可用、PyTorch 已装）。
- 根因：`torchrun` 是 PyTorch 的 console_script，只在该 Python 环境的 `bin/` 目录，一站式平台默认环境未把该目录加入 PATH。
- 修法：用 `command -v torchrun` 判存在、缺失则回退等价且不依赖 PATH 的 `python -m torch.distributed.run`（经解释器自身解析）；或先 `conda activate` / 前插环境 `bin` 到 PATH。

### B. source CANN 后 import cv2 报 static TLS block

- 信号（尤 aarch64）：`ImportError: libGLdispatch.so.0: cannot allocate memory in static TLS block`。
- 根因：先 source CANN 环境后，CANN 的共享库在 cv2 dlopen 其原生绑定前已**耗尽 glibc 的 static-TLS 池**。
- 修法：用 `LD_PRELOAD` 预加载 `libGLdispatch.so.0`，让它进入 loader 的**初始 TLS 配额**而非 static 池。

### C. 首次 NPU 调用才报「缺 Python 模块」

- 信号：python import 期一切正常，**首次 NPU op** 时报 `Environment_Error_Import_Python_Module_Failed: No module named '<mod>'`（scipy / attrs / decorator / cloudpickle / ml-dtypes 等）。
- 根因：CANN TBE 在首次 NPU 调用时才 import 一批宿主 Python 模块，缺哪个不在 import 期暴露、而在首次 NPU op 时报——易被误读为 CANN/算子问题，实为**缺宿主 pip 依赖**。
- 修法：按报错模块名补装宿主 pip 依赖。

### D. 推理正常结束后退出期 SIGABRT

- 信号：所有输出已落盘、推理正常结束后，仍在 Python 解释器退出（atexit / C 扩展析构）阶段触发 torch_npu C 扩展**双重释放 SIGABRT** 崩溃 + 噪音告警。
- 根因：torch_npu C 扩展在解释器 shutdown 阶段重复释放。
- 修法（参考实现在 SANA-Video 入口）：用 `os._exit(0)` 绕过解释器 shutdown、并先对直接子进程发 SIGKILL，规避崩溃与噪声。注意 `os._exit` 会跳过正常清理，仅在确认输出已全部落盘后使用。

## 风险 / 边界

- `python -m torch.distributed.run` 与 `torchrun` 等效但要确认 torch 版本一致。
- `os._exit(0)` 是绕过式规避，跳过 atexit/flush，务必放在所有落盘之后；不适用于需正常析构资源的长驻服务。

## 相关经验
- [昇腾多模态模型 bringup 的结构失配：框架侧 config 扫描盲区与 OOT 算子秩](mm_bringup_config_scan_and_oot_op_rank_contract.md)

- 初始化/HCCL 报错根因在驱动/设备层见 [bringup-error-root-cause-env-driver-platform](bringup_error_root_cause_env_driver_platform.md)。
- 多模 yaml 参数透传与 tokenizer 侧车坑见 [config-tokenizer-sidecar-and-attr-alias](config_tokenizer_sidecar_and_attr_alias.md)。

## Evidence

- `diff 事实 / 维护者确认`（@621be70）：`mm_launch_task` 裸调 torchrun，改 `python -m torch.distributed.run` 回退。
- `diff 事实`（@c919cb7）：`LD_PRELOAD libGLdispatch.so.0` 规避 static-TLS；TBE 首调 import 宿主模块；入口 `os._exit(0)` + 子进程 SIGKILL 规避退出期双重释放。
- 溯源下探：[cann-recipes-infer-issue-246-question-hunyuan-video-torchrun-command-not-found](https://gitcode.com/cann/cann-recipes-infer/issues/246)、[cann-recipes-infer-issue-250-question-wan2-2-i2v-torchrun-command-not-found](https://gitcode.com/cann/cann-recipes-infer/issues/250)、[cann-recipes-infer-pr-369-fix-add-hyvideo-sparse-parameters-update-readme-and-fix-sana-video-weigh](https://gitcode.com/cann/cann-recipes-infer/merge_requests/369)、[cann-recipes-infer-pr-372-add-sana-video-one-stop-platform-quickstart](https://gitcode.com/cann/cann-recipes-infer/merge_requests/372)

<!-- cannbot:related:start -->
## 相关

- [MM Inference Launch（多模态生成模型统一推理拉起架构）](../../concepts/frameworks/mm_inference_launch.md)（`related`）：MM Inference Launch 是 cann-recipes-infer 中 4 个多模态生成模型（Wan2.2-I2V / HunyuanVideo / SANA-Video / HunyuanImage-3.0）的统一推理拉起架构：每个模型以 `infer.sh` 为入口，切换 YAML 选择推理场景；YAML 集中管理公共字段、启动器、环境变量、Dit-Cache、块稀疏 Attention 与模型透传参数；统一函数库 `executor/scripts/mm_function.sh` 负责校验、解析、环境设置与启动。；在 CANNLab 一站式平台默认环境（未 `conda activate`）或 aarch64 上拉起多模态推理（［mm 推理启动链］(../../concepts/frameworks/mm_inference_launch.md)：`infer.sh → executor/scripts/mm_function.sh`）时，几类**报错发生在意外阶段、易误读为算子/CANN 问题**，实为环境未就绪。对号入座即可。；启动架构定义 infer.sh 到 mm_function.sh 的配置与执行链，运行手册针对同一链路的环境未就绪故障给出定位方式。
- [NPU 推理脚本 os._exit 快退残留 CANN TBE 孙进程的 shutdown 噪声（RouteServer.finalize 消除）](os_exit_tbe_routeserver_shutdown_noise.md)（`related`）：“在 `os._exit(0)` 之前显式调用 TBE `RouteServer` 的 finalize 清理这层孙进程”承接“用 `os._exit(0)` 绕过解释器 shutdown、并先对直接子进程发 SIGKILL”，补上直接子进程清理触达不到 RouteServer 孙进程时的收尾步骤。
<!-- cannbot:related:end -->
