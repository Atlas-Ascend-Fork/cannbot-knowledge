---
type: API
title: aclrtcAddNameExpr
description: 注册指定的名称表达式，该表达式代表了一个__global__函数。 主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling
  name，在launch阶段调用对应的模板__global__函数。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcAddNameExpr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# aclrtcAddNameExpr<a name="ZH-CN_TOPIC_0000002601551137"></a>

## 功能说明<a name="section618mcpsimp"></a>

注册指定的名称表达式，该表达式代表了一个\_\_global\_\_函数。

主要用于\_\_global\_\_函数为模板函数的场景，调用本接口后，可以通过[aclrtcGetLoweredName](aclrtc_get_lowered_name.md)接口获取函数的mangling name，在launch阶段调用对应的模板\_\_global\_\_函数。

## 函数原型<a name="section620mcpsimp"></a>

```
aclError aclrtcAddNameExpr(aclrtcProg prog, const char *const nameExpression)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  接口参数说明

<a name="table10560024131915"></a>
<table><thead align="left"><tr id="row35607245197"><th class="cellrowborder" valign="top" width="17.580000000000002%" id="mcps1.2.4.1.1"><p id="p1356016243193"><a name="p1356016243193"></a><a name="p1356016243193"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="15.559999999999999%" id="mcps1.2.4.1.2"><p id="p092775021313"><a name="p092775021313"></a><a name="p092775021313"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="66.86%" id="mcps1.2.4.1.3"><p id="p20560122410195"><a name="p20560122410195"></a><a name="p20560122410195"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row15560192415195"><td class="cellrowborder" valign="top" width="17.580000000000002%" headers="mcps1.2.4.1.1 "><p id="p12769163425119"><a name="p12769163425119"></a><a name="p12769163425119"></a>prog</p>
</td>
<td class="cellrowborder" valign="top" width="15.559999999999999%" headers="mcps1.2.4.1.2 "><p id="p0927135021312"><a name="p0927135021312"></a><a name="p0927135021312"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="66.86%" headers="mcps1.2.4.1.3 "><p id="p1717692211109"><a name="p1717692211109"></a><a name="p1717692211109"></a>运行时编译程序的句柄。</p>
</td>
</tr>
<tr id="row13879152135218"><td class="cellrowborder" valign="top" width="17.580000000000002%" headers="mcps1.2.4.1.1 "><p id="p19982811135218"><a name="p19982811135218"></a><a name="p19982811135218"></a>nameExpression</p>
</td>
<td class="cellrowborder" valign="top" width="15.559999999999999%" headers="mcps1.2.4.1.2 "><p id="p1792775011320"><a name="p1792775011320"></a><a name="p1792775011320"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="66.86%" headers="mcps1.2.4.1.3 "><p id="p4268745104714"><a name="p4268745104714"></a><a name="p4268745104714"></a>一个常量表达式，通常为字符串字面量，用于指明某个__global__函数。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

aclError为int类型变量，详细说明请参考[RTC错误码](rtc_error_code.md)。

## 约束说明<a name="section633mcpsimp"></a>

该接口需要在[aclrtcCompileProg](aclrtc_compile_prog.md)编译接口前使用。

## 调用示例<a name="section837496171220"></a>

```
aclrtcProg prog;
const char* kernelNameExpr = "add_custom<float>";
aclError result = aclrtcAddNameExpr(prog, kernelNameExpr);
```


<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：“aclrtcAddNameExpr（可选）：注册需要导出的核函数名表达式”描述可选导出步骤，“该接口需要在aclrtcCompileProg编译接口前使用”给出必须满足的调用顺序。
- [aclrtcGetLoweredName](aclrtc_get_lowered_name.md)（`related`）：“使用前必须先通过aclrtcAddNameExpr注册原始名称，且两次传入的nameExpression字符串必须完全相同。”与“主要用于__global__函数为模板函数的场景，调用本接口后，可以通过aclrtcGetLoweredName接口获取函数的mangling name，在launch阶段调用对应的模板__global__函数。”分别给出双端正文事实；GetLoweredName 的前置条件是 AddNameExpr 注册完全相同的表达式，AddNameExpr 卡又明确后续由 GetLoweredName 取得 mangling name，二者形成 RTC 模板函数注册到 launch 名称查询的调用序。
- [aclrtcCompileProg](aclrtc_compile_prog.md)（`same_topic`）：该接口需要在aclrtcCompileProg编译接口前使用。编译接口，编译指定的程序。函数签名为 aclError aclrtcCompileProg(aclrtcProg prog, int numOptions, const char** options)。名称表达式卡规定注册时序，编译卡给出消耗同一 `aclrtcProg` 句柄的编译入口；模板 `__global__` 函数若需 lowered name，必须先注册表达式再执行编译。
<!-- cannbot:related:end -->
