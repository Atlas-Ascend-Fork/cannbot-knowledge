---
type: Guide
title: SGLang NPU环境报告的版本发现与证据缺口
description: 说明check_env如何收集TorchNPU/内核/DeepEP、CANN与BiSheng、驱动和拓扑，区分报告缺失、路径选择与真正运行验证。
tags:
- task.debugging
- topic.compilation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/check_env.py
  role: primary
created_at: '2026-11-08T12:10:40Z'
updated_at: '2026-11-09T04:34:03Z'
platforms: []
aliases:
- NPUEnv
- check_env
---

# SGLang NPU环境报告的版本发现与证据缺口

NPUEnv扩展软件包列表torch_npu、sgl-kernel-npu、deep_ep，按torch.npu.device_count/name列可见卡。只有NPU available时进一步采集CANN信息；多rank需同时记录可见设备和local/TP映射，名称相同不代表同一物理卡。

CANN_HOME优先ASCEND_TOOLKIT_HOME、ASCEND_INSTALL_PATH中首个存在路径，再/usr/local/Ascend/ascend-toolkit/latest；该选择仅用 os.path.exists，不验证目录类型或安装完整性，存在的普通文件也会阻止继续检查后续变量/默认路径。本函数没有同样查询所有其他ASCEND_*变量，报告Not found不证明系统完全没装CANN。version.cfg按固定行格式解析，BiSheng先tools/bisheng_compiler再旧compiler/ccec_compiler路径，驱动用npu-smi board设备0解析Software Version，拓扑用npu-smi info -t topo。

部分命令失败只捕获subprocess.SubprocessError，缺可执行文件等其他异常不保证全部回退成Not Available。报告反映文件和命令发现口径，不能证明实际进程动态链接了同套库，更不能代替算子符号、数值、图和模型性能验证。

问题材料应附完整报告、实际启动参数/环境、固定模型与源码版本，并核对加载路径和custom vendor环境。本文仅只读审阅实现，没有执行环境报告命令或硬件探测。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
