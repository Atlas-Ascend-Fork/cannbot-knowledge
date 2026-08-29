---
type: API
title: aclrtcDestroyProg
description: 销毁运行时编译程序的实例。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcDestroyProg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# aclrtcDestroyProg

销毁运行时编译程序实例，释放资源。函数签名为 aclError aclrtcDestroyProg(aclrtcProg* prog)。
参数 prog 为输入，指定待销毁的运行时编译程序句柄。
返回值为 aclError（int 类型），详细错误码参考 RTC 错误码文档。
调用后不应再使用已销毁的 prog 句柄。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。

<!-- cannbot:related:start -->
## 相关

- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：“参数 prog 为输出，返回运行时编译程序句柄；src 为 Ascend C Device 侧源代码字符串；name 为程序名称，默认值为 default_program。”说明句柄的创建和所有权起点；“销毁运行时编译程序实例，释放资源。函数签名为 aclError aclrtcDestroyProg(aclrtcProg* prog)。”给出对应释放动作，二者闭合资源生命周期。
<!-- cannbot:related:end -->
