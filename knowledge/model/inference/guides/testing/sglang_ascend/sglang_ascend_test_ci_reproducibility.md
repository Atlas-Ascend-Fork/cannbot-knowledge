---
type: Guide
title: SGLang NPU测试环境重现与CI覆盖证据边界
description: 说明CI依赖版本、源码与镜像包混用、可见设备转换、AST注册和enabled/nightly过滤，区分套件选择、运行记录和硬件通过。
tags:
- task.testing
- topic.compilation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/scripts/ci/npu/npu_ci_install_dependency.sh
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ascend/e2e/run_npu_testcase.sh
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/scripts/ci/npu/precise-test/list_tests.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/test/ci/ci_register.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/run_suite.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/.github/workflows/_npu-pr-test-stage.yml
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/.github/workflows/_npu-single-node-test-stage.yml
  role: supporting
created_at: '2026-11-08T12:20:23Z'
updated_at: '2026-11-09T04:36:38Z'
platforms: []
---

# SGLang NPU测试环境重现与CI覆盖证据边界

CI安装脚本默认CANN9.1.0、Torch2.10.0/PTA2.10.0.post6、内核2026.11.0.post1、Triton-Ascend3.2.2、MemFabric/MemCache1.3.0，ZBAL按950与其他分1.2.21004.post1/1.1.3。脚本使用py312制品并替换NPU pyproject，dev_npu不是系统驱动安装。用户override CANN/Torch/内核版本需同时匹配整个制品集合，脚本默认不能证明任意组合兼容。

run_npu_testcase可用源码PYTHONPATH，也可用镜像中SGLang但把当前checkout测试helper复制进去；因此“测试来源commit”和“运行包commit”可能不同。还可为SGLang和评测工具分别安装Transformers，需记录两个环境。它把ASCEND_VISIBLE_DEVICES排序转ASCEND_RT_VISIBLE_DEVICES再清原变量，并设置CPU affinity/性能环境；这些会影响可见rank和可比性，不能只保存启动命令。

register_npu_ci是runtime no-op，由AST收集est_time/suite/nightly/disabled。list_tests只选择NPU、目标suite、非nightly、disabled为None的文件，再LPT分区；注册和列出不表示执行过，更不表示通过。nightly/full另有套件，精度和性能分开；est_time用于调度，不是模型测得时延。

重现报告至少绑定运行镜像digest、实际导入sglang路径/版本、测试commit、依赖、设备/rank/网络、所选文件及skip/disabled、退出码和原始结果。覆盖率推荐子集不是全功能验收，测试helper被复制也不等于已加载当前实现。

本次没有执行安装脚本、CI、设备可见性修改或系统调优，仅静态提取可复用约束。

## Workflow分支仍需记录

可复用PR stage对非nightly重新安装依赖，nightly则可只复制当前测试helper到镜像安装目录；single-node stage也按install_sglang_deps开关选择。两者支持覆盖率runner或普通run_suite路径；only_tests 过滤仅在 use_coverage_runner=false 的普通 run_suite 路径生效。覆盖率分支虽先构造 ONLY_FILE_ARGS，却没有传给 list_tests.py/覆盖率runner，随后直接退出；NIGHTLY_FLAG 也只传普通路径，因此覆盖率路径仍按 list_tests 的非nightly注册条件选集。PR/单节点/job成功不代表全套nightly与多节点测试都执行。
