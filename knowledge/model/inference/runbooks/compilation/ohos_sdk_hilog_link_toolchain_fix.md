---
{
  "type": "Runbook",
  "title": "OpenHarmony SDK 交叉编译 hilog 链接失败修复（find_library + 工具链库搜索路径 + OHOS_PLATFORM 开关）",
  "description": "OpenHarmony SDK 交叉编译 harmony_acl 时出现 OH_LOG_Print 未定义引用；实际链接行缺少 hilog。联合调整库查找配置与 OHOS 平台分支后，25 个构建步骤及签名通过；未做单因素因果消融。",
  "tags": [
    "task.implementation",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# OpenHarmony SDK 交叉编译 hilog 链接失败修复（find_library + 工具链库搜索路径 + OHOS_PLATFORM 开关）
## 适用场景
在 Windows 主机上用 OpenHarmony SDK（native/llvm Clang 15.0.4，--target=aarch64-linux-ohos，lld 链接器，--no-allow-shlib-undefined 严格检查开启）交叉编译依赖鸿蒙 hilog 系统库的 C++ 项目（如 cann-recipes-harmony-infer/harmony_acl），链接最终测试可执行文件时。凡是自定义 ohos.toolchain.cmake + CMakeLists 双分支（WIN32/OHOS）组织的项目都适用。
## 触发与观测
- 在 Windows 上用 OpenHarmony SDK（Clang 15.0.4，--target=aarch64-linux-ohos）交叉编译 harmony_acl 时，链接测试可执行文件 ascendcl_ut 报 ld.lld: error: undefined reference due to --no-allow-shlib-undefined: OH_LOG_Print，符号分别由 libhiai_ascendcl.so、libneural_network_core.so、libhiai_foundation.so 引用。
失败现象：

```
FAILED: ascendcl_ut
ld.lld: error: undefined reference due to --no-allow-shlib-undefined: OH_LOG_Print
>>> referenced by libhiai_ascendcl.so
>>> referenced by libneural_network_core.so
>>> referenced by libhiai_foundation.so
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
ninja: build stopped: subcommand failed.
```

事件 351 的链接命令行中完全没有出现 hilog 库，同时 OH_LOG_Print 未定义引用来自三个预编译 .so。
## 探针与操作

`${HARMONY_WORK_ROOT}`：来源 Windows 开发工作根；请按本地 SDK 与工程布局替换，保留后缀关系。
- 实际链接命令缺少 hilog，同时配置存在库查找与平台分支两处问题；调整工具链库搜索配置并显式选择 OHOS 分支后构建通过。这是联合改动的结果，未单独证明 CMake 会因裸库名查找失败而静默丢弃库。
1. 检查 build.ninja 实际链接命令，核对实际链接行是否包含所需 hilog 库。
2. 核对 cmake 命令是否带 -DOHOS_PLATFORM=OHOS；不带时走 WIN32 分支，OHOS 分支的头文件路径与库配置整体不生效。
## 机制与判别
- 实际链接命令缺少 hilog，同时配置存在库查找与平台分支两处问题；调整工具链库搜索配置并显式选择 OHOS 分支后构建通过。这是联合改动的结果，未单独证明 CMake 会因裸库名查找失败而静默丢弃库。
- 验证：清理缓存后以 -DOHOS_PLATFORM=OHOS -DHMS_LIB_DIR=... 重新配置并 ninja，25/25 构建步骤通过，包括 libhiai_ascendcl.so / libneural_network_core.so / libhiai_foundation.so / ascendcl_ut 的链接与 SelfSign 代码签名。
重建命令：

```
cd build_ohos && rm -rf CMakeCache.txt CMakeFiles _deps *.so ascendcl_ut* .ninja_* build.ninja cmake_install.cmake lib bin && cmake -G Ninja -DCMAKE_TOOLCHAIN_FILE=../ohos.toolchain.cmake -DCMAKE_BUILD_TYPE=Release -DOHOS_PLATFORM=OHOS -DHMS_LIB_DIR="${HARMONY_WORK_ROOT}/command-line-tools/sdk/default/hms/native/sysroot/usr/lib/aarch64-linux-ohos" ../scripts && ninja
```

## 验证信号
事件 652 工具结果：25/25 构建步骤通过，包含 libhiai_foundation.so、libneural_network_core.so、libhiai_ascendcl.so 链接与 ascendcl_ut 链接，全部产物 SelfSign 签名成功（"Self-sign elf success / sign success"）。修改 CMakeLists 后增量 ninja 亦通过。
## 适用与失效边界
适用于 OpenHarmony SDK 23 + Clang 15.0.4 交叉编译场景。失效边界：设备侧（Kirin X90）NPU 驱动只提供推理能力、不含 ATC 在线编译器，aclgrphBuildModelFromFile 类用例在来源报告的设备能力范围内无法完成；新设备仍须核实 ATC 支持，不能将跳过测试计为通过；set_aipp_config 在 resnet50.om 上返回 100000，疑似模型不支持 AIPP YUV420SP 输入格式，未实机定位。设备侧用例结果为用户口述而非工具结果。

## 补充机制片段
### 机制片段
```
FAILED: ascendcl_ut
ld.lld: error: undefined reference due to --no-allow-shlib-undefined: OH_LOG_Print
>>> referenced by libhiai_ascendcl.so
>>> referenced by libneural_network_core.so
>>> referenced by libhiai_foundation.so
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
ninja: build stopped: subcommand failed.
```
### 机制片段
```
# 指定系统根目录（头文件和基础库）
set(CMAKE_SYSROOT "${OHOS_SDK}/native/sysroot")

# 为 CMake 库查找配置目标架构目录；实际链接行仍需单独检查 hilog
set(CMAKE_LIBRARY_ARCHITECTURE "aarch64-linux-ohos")
list(APPEND CMAKE_SYSTEM_LIBRARY_PATH "/usr/lib/aarch64-linux-ohos")

# 设置 find 搜索模式，与 OHOS SDK 官方 toolchain 保持一致
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
list(APPEND CMAKE_FIND_ROOT_PATH "${OHOS_SDK}/native")

# 强制 Clang 使用鸿蒙 SDK 自带的 lld 链接器
```
### 机制片段
```
# ================== 鸿蒙 (OHOS) 目标 ==================
if (OHOS_PLATFORM STREQUAL "OHOS")
    find_library(HILOG_LIB NAMES hilog_ndk.z)
    if(NOT HILOG_LIB)
        message(FATAL_ERROR "Cannot find libhilog_ndk.z.so in sysroot")
    endif()

    set(UT_TEST_NDK_DIR ../tests/ut/ndk)

    target_include_directories(hiai_ascendcl PUBLIC
        ../include
        ../src
        ../depends
        ${OHOS_INC_DIR}
        ${HMS_INC_DIR}
        ${UT_TEST_NDK_DIR}/include
    )
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D__OHOS__")
    target_link_libraries(hiai_ascendcl PUBLIC ${HILOG_LIB})
```
### 机制片段
```
cd build_ohos && rm -rf CMakeCache.txt CMakeFiles _deps *.so ascendcl_ut* .ninja_* build.ninja cmake_install.cmake lib bin && cmake -G Ninja -DCMAKE_TOOLCHAIN_FILE=../ohos.toolchain.cmake -DCMAKE_BUILD_TYPE=Release -DOHOS_PLATFORM=OHOS -DHMS_LIB_DIR="${HARMONY_WORK_ROOT}/command-line-tools/sdk/default/hms/native/sysroot/usr/lib/aarch64-linux-ohos" ../scripts && ninja
```
