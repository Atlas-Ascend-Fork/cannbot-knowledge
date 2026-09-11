---
type: API
title: aclrtcCompileProg
description: 编译接口，编译指定的程序。
tags:
- task.lookup
- topic.implementation.api_layer.utils_api
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/RTC/aclrtcCompileProg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
---

# aclrtcCompileProg<a name="ZH-CN_TOPIC_0000002433359052"></a>

## 功能说明<a name="section618mcpsimp"></a>

编译接口，编译指定的程序。

## 函数原型<a name="section620mcpsimp"></a>

```
aclError aclrtcCompileProg(aclrtcProg prog, int numOptions, const char **options)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  接口参数说明

<a name="table549971610414"></a>
<table><thead align="left"><tr id="row15008166418"><th class="cellrowborder" valign="top" width="17.580000000000002%" id="mcps1.2.4.1.1"><p id="p19500141674120"><a name="p19500141674120"></a><a name="p19500141674120"></a>参数名</p>
</th>
<th class="cellrowborder" valign="top" width="15.559999999999999%" id="mcps1.2.4.1.2"><p id="p092775021313"><a name="p092775021313"></a><a name="p092775021313"></a>输入/输出</p>
</th>
<th class="cellrowborder" valign="top" width="66.86%" id="mcps1.2.4.1.3"><p id="p650071616415"><a name="p650071616415"></a><a name="p650071616415"></a>描述</p>
</th>
</tr>
</thead>
<tbody><tr id="row05001016134116"><td class="cellrowborder" valign="top" width="17.580000000000002%" headers="mcps1.2.4.1.1 "><p id="p12769163425119"><a name="p12769163425119"></a><a name="p12769163425119"></a>prog</p>
</td>
<td class="cellrowborder" valign="top" width="15.559999999999999%" headers="mcps1.2.4.1.2 "><p id="p0927135021312"><a name="p0927135021312"></a><a name="p0927135021312"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="66.86%" headers="mcps1.2.4.1.3 "><p id="p1717692211109"><a name="p1717692211109"></a><a name="p1717692211109"></a>运行时编译程序的句柄。</p>
</td>
</tr>
<tr id="row13879152135218"><td class="cellrowborder" valign="top" width="17.580000000000002%" headers="mcps1.2.4.1.1 "><p id="p159984212474"><a name="p159984212474"></a><a name="p159984212474"></a>numOptions</p>
</td>
<td class="cellrowborder" valign="top" width="15.559999999999999%" headers="mcps1.2.4.1.2 "><p id="p1792775011320"><a name="p1792775011320"></a><a name="p1792775011320"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="66.86%" headers="mcps1.2.4.1.3 "><p id="p13205163764718"><a name="p13205163764718"></a><a name="p13205163764718"></a>编译选项数量。</p>
</td>
</tr>
<tr id="row57431411164719"><td class="cellrowborder" valign="top" width="17.580000000000002%" headers="mcps1.2.4.1.1 "><p id="p17431411114711"><a name="p17431411114711"></a><a name="p17431411114711"></a>options</p>
</td>
<td class="cellrowborder" valign="top" width="15.559999999999999%" headers="mcps1.2.4.1.2 "><p id="p107431119474"><a name="p107431119474"></a><a name="p107431119474"></a>输入</p>
</td>
<td class="cellrowborder" valign="top" width="66.86%" headers="mcps1.2.4.1.3 "><p id="p2743311144712"><a name="p2743311144712"></a><a name="p2743311144712"></a>编译选项数组，保存具体的编译选项（默认添加-std=c++17）。</p>
<p id="li196189152610p0"><a name="li196189152610p0"></a><a name="li196189152610p0"></a>支持的编译选项可以参考[《毕昇编译器用户指南》](https://www.hiascend.com/document/redirect/CannCommunityBiSheng)。</p>
</td>
</tr>
</tbody>
</table>

## 返回值说明<a name="section640mcpsimp"></a>

aclError为int类型变量，详细说明请参考[RTC错误码](rtc_error_code.md)。

## 约束说明<a name="section633mcpsimp"></a>

无

## 调用示例<a name="section837496171220"></a>

```
aclrtcProg prog;
const char *options[] = {"--npu-arch=dav-2201"};
int numOptions = sizeof(options) / sizeof(options[0]);
aclError result = aclrtcCompileProg(prog, numOptions, options);
```


<!-- cannbot:related:start -->
## 相关

- [编译与执行RTC](../../../guides/programming_guide/compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`explains`）：“aclrtcCompileProg：编译给定的程序，支持用户自定义编译选项”定位 RTC 编译步骤，“options 为编译选项数组（默认添加 -std=c++17）”明确选项参数及默认行为。
- [aclrtcCreateProg](aclrtc_create_prog.md)（`related`）：“通过给定参数创建编译程序实例。函数签名为 aclError aclrtcCreateProg(aclrtcProg* prog, const char* src, const char* name, int numHeaders, const char** headers, const char** includeNames)。”生产 RTC 程序句柄；“参数 prog 为运行时编译程序句柄，numOptions 为编译选项数量，options 为编译选项数组（默认添加 -std=c++17）。”说明 CompileProg 消费该句柄，形成创建后编译的生命周期链。
- [aclrtcAddNameExpr](aclrtc_add_name_expr.md)（`same_topic`）：该接口需要在aclrtcCompileProg编译接口前使用。编译接口，编译指定的程序。函数签名为 aclError aclrtcCompileProg(aclrtcProg prog, int numOptions, const char** options)。名称表达式卡规定注册时序，编译卡给出消耗同一 `aclrtcProg` 句柄的编译入口；模板 `__global__` 函数若需 lowered name，必须先注册表达式再执行编译。
<!-- cannbot:related:end -->
