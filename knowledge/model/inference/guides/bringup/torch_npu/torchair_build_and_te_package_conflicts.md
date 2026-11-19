---
type: Guide
title: TorchAir 环境排查：依赖库下载失败与 TE/Protobuf 重复描述符
description: 区分编译依赖下载与运行期 TE/CANN 配套错误，保留具体包路径和版本证据。
tags:
- task.debugging
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/faq.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/faq.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/.gitmodules
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/.gitmodules
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CMakeLists.txt
  role: implementation
created_at: '2026-11-09T03:19:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir 环境排查：依赖库下载失败与 TE/Protobuf 重复描述符

## 版本与症状

依据 TorchAir 发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的 FAQ 及整体产品范围，限定 A2/A3 的该软件栈；不是所有 Protobuf 或所有 CANN 工具的统一修复规则。本卡只给出检查步骤，不执行安装或修改环境。

## 编译阶段下载 libboundscheck 等依赖失败

先读取构建日志中的具体依赖、所需版本、获取地址和构建系统期望路径，确认本地 Git 网络访问。FAQ的离线段提到wheel软链接，但与固定源码的子模块/头文件要求存在冲突；具体核对见下文，不直接采用未确认的制品方案。

依赖同名、下载成功和版本匹配是不同条件；不要替换成任意“最新包”，也不要先修改全局 Python 环境来掩盖构建依赖缺失。按当前源码中的实际构建配置定位路径，不能照抄示例架构目录。

## 运行期 GeneratedDatabase()->Add 失败

来源案例同时出现 File already exists in database: dvpp_tensor_shape.proto 和 GeneratedDatabase()->Add(encoded_file_descriptor,size) 致命错误，最终归因于 TE 包与当前 CANN 不配套。单看 BackendCompilerFailed 的外层异常不足以推定 Converter 失败。

确认进程实际使用的 CANN 路径、Python 解释器及 TE 安装来源，找到该 CANN 携带的 te-*.whl，再按该环境的安装方式纠正配套。来源的 /usr/local/Ascend/cann/aarch64-linux/lib64 路径只是示例，其他架构、安装前缀和版本不能直接套用。

## 验收与边界

保存变更前的包版本和路径，修正后在同一解释器与同一负载重试原失败步骤。此 FAQ 不是所有重复描述符错误的穷举归因，也没有授权删除其他环境的包。本文未安装依赖、执行构建或复现报错。

- [源码提交与部署配套分别核对](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线FAQ与实际构建输入对照

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` FAQ与发布页的两种失败签名相同。两个固定提交的.gitmodules均将libboundscheck登记为third_party/secure_c源码子模块，CMake将其include目录加入头文件路径，缺失时要求恢复子模块。FAQ中的“libboundscheck whl软链接”说法不能替代这份实际构建输入；当前未确认可用于该流程的离线wheel制品，不补造pip安装或任意wheel软链步骤。

离线准备应核对所选提交的gitlink身份、源码/头文件和CMake实际路径；修改远端URL或只取同名最新仓不证明匹配。这里未执行子模块更新、下载、安装或构建。TE故障仍先核对实际CANN与其携带的TE包，特定dvpp_tensor_shape.proto重复描述符案例不能推广为所有Protobuf崩溃均来自同一原因。

主线总览涵盖A2/A3与950，本节为相应框架环境的诊断入口，不是具体NPU算子运行验证；发布FAQ仍按A2/A3配套理解。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/faq.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/faq.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/.gitmodules)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CMakeLists.txt)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/.gitmodules)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CMakeLists.txt)（implementation）
