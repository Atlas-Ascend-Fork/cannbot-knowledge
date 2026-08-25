---
type: API
title: RTC简介（RTC运行时编译）
description: RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。开发指导请参考RTC。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/RTC_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# RTC简介

RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。开发指导请参考RTC。
使用aclrtc接口前需要包含如下头文件：
需要链接的库文件：libacl_rtc.so。

<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：RTC intro 说明头文件和链接入口，指南则给出 Create→AddName→Compile→GetBin→load/launch→Destroy 全流程，是同一运行时编译主题的概念与执行切面。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`related`）：aclrtcCompileProg 消费已创建的 aclrtcProg，并用 --npu-arch 等选项产生目标机器码，是 RTC intro 所述运行时编译的核心执行步骤。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：《aclrtcCreateProg》处理“通过给定的参数，创建编译程序的实例。”。《RTC简介（RTC运行时编译）》明确提供“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。开发指导请参考RTC。”，其参数、调用或验证步骤直接接入RTC Kernel 创建、编译、函数获取、launch 和销毁生命周期。
- [aclrtcGetBinData](aclrtc_get_bin_data.md)（`related`）：编译后必须先查询大小并由 aclrtcGetBinData 取出 Device 二进制，才能交给 runtime load；它连接 RTC 编译与执行阶段。
- [aclrtcGetLoweredName](aclrtc_get_lowered_name.md)（`related`）：《aclrtcGetLoweredName》处理“获取已经注册的__global__函数的mangling name。”。《RTC简介（RTC运行时编译）》明确“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。开发指导请参考RTC。”，可直接用于核对RTC name expression 到 lowered symbol 的 create/compile/query/destroy 生命周期。
<!-- cannbot:related:end -->
