---
type: Guide
title: SGLang Kernel NPU 构建选择、依赖与安装身份
description: 区分 REFACTOR 和 legacy 构建入口、2201/3510 目标、原生算子选择、第三方依赖、子集 wheel 替换与加载边界。
tags:
- task.implementation
- topic.compilation
- topic.architecture
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/setup.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/build_tools/torch_wheel.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/version.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/config_git_last_commit.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/aclnn_torch_adapter/CMakeLists.txt
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/helloworld/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/helloworld/op_host/helloworld.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/helloworld/op_kernel/kernel_helloworld.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
created_at: '2026-11-08T11:03:52Z'
updated_at: '2026-11-09T17:50:00Z'
platforms:
- a2
- a3
- '950'
---

# SGLang Kernel NPU 构建选择、依赖与安装身份

## 先选择入口和目标

固定版本提供两个构建入口。根 `setup.py` 构建 REFACTOR `sgl-kernel-npu`，包含完整 Python 接口及源码，原生 AICORE/AICPU/HOST 部分按选择编译；既有 `build.sh` 仍负责 legacy、DeepEP、memory saver 和独立 attentions 包。两者参数不可混用，同一 checkout 不应并发构建。

REFACTOR 显式要求 `--arch-version 2201` 或 `3510`。前者生成 `ascend910b` 与 `ascend910_93`，对应 A2/A3；后者生成 `ascend950`，对应 950。API 中 arch22/arch35 分别对应这两个架构编号。构建目标不等于当前设备自动检测；第三方适配器仍会核对本机 `npu-smi` SoC，`--plan` 在有第三方算子时也会检测。

## 选择原生算子与产物

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
python3 setup.py --arch-version 2201 --ops apply_token_bitmask --without-third-party
python3 setup.py --arch-version 2201 --ops apply_token_bitmask --artifact run
```

示例应在上游 checkout 中执行。第一条原生构建命令生成 wheel；第二条生成供 ACLNN 安装使用的 `.run`。`--ops all` 是默认值，也可传不重复的逗号分隔 ID；未知、重复或显式不支持该架构的 ID 会失败。选择只影响原生算子，wheel 始终含完整 Python 模块；import 到接口不等于底层实现已安装。

Linux、已初始化的 CANN SDK、CMake>=3.20、C++17 是原生构建前提。wheel 还需匹配 Torch/torch_npu、Python 开发头、setuptools/wheel。CANN-only `.run` 不需 Torch；选择 HOST 的 `.run` 仍需 Torch 与 Python 开发头。AICPU 文档要求含 HCC/AICPU 开发文件的 CANN 9.2.0，不可拿 legacy 的最低版本说明代替这条条件。

HOST 以静态归档进入 `.run`，wheel 再将其和适配器链接到 `libsgl_kernel_npu.so`；仅安装 `.run` 不等于获得 HOST 的 `torch.ops` 调用入口。`-j N`/`--jobs N` 只控制构建并发，不改变运行时算子并行度。

## 第三方与清理

wheel 从 `third_party/profiles/cann-<SDK版本>/*.json` 选择固定仓库、commit、架构算子列表和构建命令；默认所有匹配 profile，可用 `--third-party` 选择或 `--without-third-party` 排除，两者互斥。显式请求不存在的 profile 报错；无匹配默认 profile 或无对应架构算子列表时跳过。`.run` 不打包第三方依赖。

`--plan --cann-version X.Y.Z` 仅预览配置，不编译或克隆依赖；实际构建检测已初始化 SDK，不接受该版本覆盖。第三方 vendor、绑定和许可证打入同一 wheel；缓存以构建指纹和校验和判定，`--make-clean` 保留第三方缓存，只清 `build/cann`、`build/torch`、`build/wheel`。切架构、算子集、Python/Torch 或 SDK 路径时应显式 clean。

## 安装身份与运行加载

最终产物在 `output/`。构建标签包含架构和 all/custom，固定包含原生算子选择的 10 位哈希，仅捆绑第三方依赖时追加 `tp_<dependency-id>` 的 10 位指纹；本页 `--without-third-party` 示例只有原生选择哈希。这些用于描述选择/依赖内容，不是源码 commit。`_build_manifest.json` 记录原生算子、执行单元和 SDK 目标。子集 wheel 相互替换，不会叠加；legacy/REFACTOR 也共享同一发行包身份。切换时显式重装并启动新进程，避免旧动态库留在进程中。

包初始化在导入 torch_npu 前将本包及第三方 vendor 放到 `ASCEND_CUSTOM_OPP_PATH`，验证必要 `libcust_opapi.so` 存在，随后加载本包 `libsgl_kernel_npu.so`。HOST-only wheel 可以没有自有 CANN vendor。不要以 Python 源码目录包含所有模块推断任一后端可调用。

legacy 的 `build.sh -a kernels` 可检测默认 SoC，无 NPU 时回退 `Ascend910_9382`；显式 `910B`、`910`/`910C`、`950` 分别选择相应目标。跨代 provider 在构建时按相对模块路径放入 wheel，冲突/缺失失败；Gemma RMSNorm 的 910 native 与 950 ACLNN 实现不靠 SGLang 运行时猜测，源码树或 editable 安装不提供其最终 provider 文件。

## 原生版本探针与发行包身份

已加载legacy原生绑定时，可用 `torch.ops.npu.sgl_kernel_npu_version()` 取得LIB_VERSION字符串，用 `torch.ops.npu.sgl_kernel_npu_print_version()` 向C stdout打印完整版本/commit行；后者返回None，不是返回完整字符串。这两个无Tensor参数的实现直接在TORCH_LIBRARY_FRAGMENT中定义。

本快照csrc/utils/version.h的版本宏固定为0.1.0，不能用它替代wheel的发行版本。完整行还包含GIT_LAST_COMMIT；根CMake通过git rev-parse HEAD成功时注入构建提交，缺失时header回退为empty。它不记录工作区dirty修改，也不能证明加载的wheel对应某个发布标签、依赖集合或当前Python源码目录。

探针属于csrc/pytorch_extensions.cpp的legacy绑定；REFACTOR从所选算子的独立Torch adapters构建库，不能承诺其总有这两个符号。核对安装身份时同时记录实际导入路径、发行包版本、REFACTOR manifest/选择集，以及存在时的原生版本输出；探针缺失或宏版本相同都不足以判断算子能力/数值兼容。本次未加载上游动态库或执行这些探针。

## legacy 教学入口的 Host 与 Device 合同

`torch.ops.npu.helloworld(x,y)` 是本树演示两个tensor相加的旧原生入口，与REFACTOR的AICPU add_example不同。legacy CMake将其Host/Device加入构建，实际Host先`empty_like(x)`，固定blockDim=8，以U32乘积计算x总元素数，再经`EXEC_KERNEL_CMD(helloworld,...)`提交。README示例中的`add_custom`不是实际Host调用名；接入时应核对真正的生成launch header与entry。

Device将x/y/z地址一律解释为half。设总长n，blockLength=floor(n/8)，tileNum=8、BUFFER_NUM=2，tileLength=floor(blockLength/16)；第b核从b*blockLength起，循环16次，依次CopyIn→Compute→CopyOut。x/y输入队列和z输出队列均深度2，数据搬入后EnQue、计算前DeQue，Add后释放输入，输出搬走后释放；名义UB数据容量为3*2*tileLength*sizeof(half)=12*tileLength字节。队列深度与调用顺序不能直接当成已测量的搬算重叠收益。

这个教学版本没有通用尾块、shape/dtype/device/contiguous检查或U32乘法溢出检查。每核只写16*tileLength个元素，总写入量为128*floor(n/128)个元素，写域为各核的前缀；n不是128的倍数时有未写元素，blockLength大于16*tileLength时还在核间留下间隙；小于128的n得到tileLength=0。任意dtype的empty_like输出不会改变Device按half读写的事实，y与x尺寸相等也没有在Host证明。即使n整除128，仍须满足真实DataCopy的长度、对齐与资源条件；不能把示例视为任意shape的生产加法。

共用`torch_helper.h`将Tensor参数转换为裸data_ptr，保留标量值，用当前NPU stream构造按值捕获converted_params的lambda并调用`ACLRT_LAUNCH_KERNEL`，最后走`OpCommand::RunOpApi`。该宏不调用contiguous，也不因捕获地址而保有Tensor对象或建立独立的完成同步；调用方/框架仍需保证输入输出至stream工作结束的生命周期。此处仅保存教学接入与静态边界，不据构建列表推断产品支持表，也未执行示例或为其声明完整Operator验证。

## 复核入口与边界

核对已安装包位置、manifest、选择集和实际 `torch.ops` 绑定，再运行对应公开接口测试。固定版本的 [apply_token_bitmask 合同](/model/inference/apis/sgl_kernel_npu/sgl_apply_token_bitmask.md) 给出无自动回退的具体例子。本文为构建 reference 蒸馏，本次未执行上游构建、安装或 NPU 测试。
