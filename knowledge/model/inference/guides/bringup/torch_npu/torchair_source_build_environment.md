---
type: Guide
title: TorchAir 源码构建：目标 Python、ABI 与运行环境分离
description: 区分只生成 wheel、CPU 调试及 NPU 执行的依赖，核对目标解释器、C++11 ABI、子模块和构建产物路径。
tags:
- task.optimization
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/installation_guide/building_from_source.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/README.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/infer_cases.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/README.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/Dockerfile
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/builder.sh
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/configure
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/build.sh
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/README.md
  role: constraint
created_at: '2026-11-09T04:39:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 源码构建：目标 Python、ABI 与运行环境分离

## 固定版本与用途

依据主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的安装指南，选择主线A2/A3与950的构建接口范围，设备执行仍另行核验；该快照举例 PyTorch/TorchNPU 2.13 与 CANN 9.1，不能与本知识仓 PyTorch 主线 2.14/CANN 9.2 自动拼成配套环境。版本兼容应看同一固定来源的 COMPATIBILITY 和明确基线。

## 三种环境不要混同

|任务|来源要求|
|--|--|
|只编译生成 TorchAir wheel|编译本身不依赖 CANN；需要匹配的目标 torch、工具链和依赖子模块，可在不含 CANN 的 builder 环境完成。|
|本地 CPU 调试 UT/简单用例|需要 Ascend SDK/Toolkit；按当前构建入口配置 SDK 路径，不能用“wheel 编译可跳过 CANN”推导测试也不需要 SDK。|
|NPU 上执行|需要配套 CANN 与 NPU 驱动；容器中还要按部署方式提供设备及驱动依赖，镜像构建成功不证明设备执行条件齐全。|

## 构建身份和 ABI

先固定主仓与递归子模块，再配置目标 Python。configure 读取该解释器已安装 torch 的编译选项；TARGET_PYTHON_PATH 要有效，无效路径仍会触发交互。仅构建可用 NO_ASCEND_SDK 跳过 SDK，CPU 调试通过 ASCEND_SDK_PATH 指定 SDK。物理机章节要求目标 torch 开启 C++11 ABI；不能只看 torch 版本号而忽略 ABI、架构和编译器。

该固定主线指南推荐 GCC 13.3.0；CMake 示例为 x86_64 3.18.4、AArch64 4.3.2。它们是此快照推荐值，不是所有 TorchAir 历史版本的通用最低版本。来源 builder/dev 多阶段镜像分别承担只编译和叠加 CANN 运行环境，选择架构、Python 与工具链后再检查实际配套。

## 产物与依赖冲突的检查顺序

当前安装指南的 CMake/make torchair 路线在 build/dist/dist 生成 wheel，可安装到 configure 选定的解释器；贡献文档的 CI build.sh 则在 output 产出 wheel，并区分仅编译和编译后自动安装。不要把两个入口的路径混用，或在另一个 Python 中检查导入后误判安装结果。

指南示例还列 numpy、pyyaml、setuptools、protobuf>=3.13,<4 及匹配 torch_npu；这是快照的依赖线索，不授权在当前机器安装或升级任意最新包。先确认实际包位置、解释器与 CANN，再按部署流程处理，已有下载与 TE 冲突参见下方卡片。

- [固定版本配套和来源身份](../../../concepts/frameworks/ascend_software_stack_baselines.md)
- [依赖下载失败与 TE 重复描述符](torchair_build_and_te_package_conflicts.md)

未执行上游构建脚本、安装包、容器构建或 NPU 测试。

## 主线README中的最小检查不等于设备验收

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` README将现有算子使用与源码构建分开：前者要求驱动、固件、CANN、PyTorch和TorchNPU配套，后者引导独立源码构建指南。README的安装检查脚本使用CPU Tensor/模型，另提无NPU环境可用SDK/stub做最小调试；这些示例不能证明NPU Kernel数值、GE设备执行或模型性能。本文只记录检查层次，没有设置LD_LIBRARY_PATH、加载stub动态库或执行构建。

ST页面建议按单例入口检查，整套UT/ST另有完整环境依赖；一次导入、backend构造或CPU最小调用不等价于通过ST。版本身份仍看固定COMPATIBILITY与基线卡，不跟随README链接中的master取任意最新包。

同一主线infer_cases导航仅称其DeepSeek-R1分布式推理示例当前支持A2，并链接外部Recipes模型；这既不证明整个TorchAir只支持A2，也不把外部模型内容视为三仓已全部摄取。模型场景、框架总览产品和具体API产品分别核对，不将教程示例当通用支持矩阵。

## Docker阶段和依赖的实际身份

固定主线Dockerfile的base→builder→dev三阶段中，builder默认Python3.10、torch2.13.0、GCC toolset13，不含CANN，但**实际已经执行pip install torch_npu，且没有固定该包版本**；README阶段图把torch_npu放在dev层，不能依图当builder只有CPU torch依赖。TORCH_VERSION固定一次安装参数也不等于最终torch/torch_npu配套已锁定，需保留实际解析后的包身份。

CPU torch使用--index-url按稳定/nightly分别安装，和其他仓Dockerfile的extra-index-url语义不同。NumPy分支3.9→1.22.4、3.10→1.23.2、3.11/12→1.26.2、3.13→2.1.2、3.14→2.3.4；仅X86分支pin CMake3.18.4.post1。解释器软链指向实际/opt/python/cpXY-cpXY，存在分支不保证所有TorchNPU/Python组合。

builder.sh默认--target builder，直接docker build不传target按末阶段得到dev；dev默认CANN9.1.0_beta.1/910b/NNAL0，release train固定CANN%209.1.T1。脚本更改CANN版本时检查train必填，直接Dockerfile并未实现同一前置校验，不能只改版本后认为路径自动适配。产品950等只是包选择，README旧“Atlas350”名称不扩展成逐功能支持表。

README的--torch-version表把dev nightly写成默认，实际脚本为稳定2.13.0；脚本帮助已含Python3.14、表仍止3.13。脚本会删除同名torchair-builder再启动，未知参数usage最终exit0，所以返回码0不能单独作构建成功证据。末尾提示bash ci/build.sh --python=...，但该固定主线没有ci/build.sh，应与真实根build.sh入口分别核对，不能照抄跨仓命令。

## configure缓存、SDK路径和实际测试入口

根configure仅在tools/TORCH_VERSION不存在时调用configure.py；该文件存在就打印Configuration finished并复用既有配置，不证明刚修改的目标解释器/torch/ABI已重新探测。根build.sh初始化子模块并按-c产出output/torchair-0.1-py3-none-any.whl；-i随后用当前PATH里的pip3先卸载再安装，不能自动假设它就是TARGET_PYTHON_PATH所指解释器。

build.sh运行UT/ST时优先从ASCEND_CUSTOM_PATH拼opensdk/opensdk，否则使用ASCEND_HOME_PATH；仅CI编译且未指定SDK才设NO_ASCEND_SDK。发布Contributing写ASCEND_CUSTOM_PATH、主线英文改写ASCEND_HOME_PATH，应按实际入口/快照核对。-g是拼接到g++前的工具链prefix，不是任意目录字符串。

-s后可传ST脚本名，实际去掉.py后以unittest执行；它会构建stubs、关闭TORCH_DEVICE_BACKEND_AUTOLOAD、设置GCOV环境，不能把一次ST/CPU最小加法当真实NPU模型性能。全量UT的Inductor扩展额外测试先用distutils.LooseVersion探测torch>=2.8，探测导入/版本失败也跳过，跳过不记通过。

容器npu-smi可列卡仅是可见性检查，Windows附录仅是命令/路径参考。没有运行上述脚本、修改配置缓存、安装包、构建或删除容器；真实环境仍独立验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/installation_guide/building_from_source.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING.md)（supporting）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/README.md)（supporting）

- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/infer_cases.md)（supporting）

- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/README.md)（primary）

- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/README_en.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/Dockerfile)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docker/builder.sh)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/configure)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/build.sh)（implementation）

- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md)（constraint）

- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/README_en.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/README.md)（constraint）
