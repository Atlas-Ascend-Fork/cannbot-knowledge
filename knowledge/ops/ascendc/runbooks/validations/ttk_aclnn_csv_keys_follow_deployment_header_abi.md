---
type: "Runbook"
title: aclnn CSV attributes 键用 ABI 名 hasBias
description: TTK/aclnn 用例 CSV 的 attributes 键必须用部署头 ABI 参数名（小驼峰 hasBias），不是 IR/OpDef 的 snake_case 属性名 has_bias；optional attr 显式传值不生成缺省态。
tags: [task.testing, topic.compilation, topic.implementation.api_layer.c_api]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["agnostic"]
---
# aclnn CSV attributes 键用 ABI 名 hasBias


## 现象

在验收一个对标 `aten::_thnn_fused_gru_cell_backward` 的算子的黑盒 ACLNN ST 用例（L0 44 行 / L1 515 行 / L2 49 行三份 CSV）时，逐参数比对 CSV 与 `develop/proto.md` 发现一个容易误判的两层命名差：proto.md OpDef 里的属性名是 snake_case 的 `has_bias`（`this->Attr("has_bias").AttrType(OPTIONAL).Bool(false)`），而 CSV `attributes` 列里的键是小驼峰的 `hasBias`（`{"hasBias":false}`，CSV 转义后写作 `{""hasBias"":false}`）。这不是拼写错误，而是有意的分层命名映射：aclnn 部署头 `aclnn_thnn_fused_gru_cell_grad.h` 的 ABI 参数名就是 `hasBias`。此外该 optional attr 在全部 608 行 CSV 里都显式传了 true/false，没有任何"缺省态"行。

## 适用场景

- 工程形态：黑盒 ACLNN ST 用例生成（ascendc-st-design 公共链 / TTK aclnn 模式 CSV）与验收；aclnn host 层调用代码编写。
- API 路径：OpDef `.Attr()`（IR 层）、部署头 `aclnn_xxx.h`（ABI 层）、`aclnnXxxGetWorkspaceSize(..., hasBias, ...)`、TTK aclnn CSV 的 `attributes` 列与 `scalar_dtypes` 列。
- 验证过的平台与 CANN 版本：无上板/编译实测（host 侧 CSV 静态校验）。结论属 aclnn ABI 命名约定，按定义与芯片平台无关（`platforms: [agnostic]`）；算子目标产品 Ascend 950PR / 950DT 为设计声明。CANN 版本未探测到。
- 适用粒度：`platform_wide`——凡经 TTK/aclnn CSV 表达属性、且 IR 属性名与部署头 ABI 参数名大小写风格不一致的算子（aclnn ABI 常见小驼峰参数名）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：IR 属性名与 ABI 参数名恰好一致的算子（无映射差）；Kernel 直调流程（无 aclnn ABI 层）；CSV 之外的属性表达（如 host 侧 C++ 调用直接用 ABI 名，不存在两层差）。

## 根因

aclnn 的部署头 ABI 参数名与 IR/OpDef 属性名是两层命名：IR 属性 `has_bias`（snake_case）映射到 aclnn ABI 参数 `hasBias`（小驼峰，取自部署头 `aclnn_xxx.h` 的函数签名）；TTK/aclnn 调用层按 ABI 参数名绑定 CSV attributes 键，写 IR 属性名（`has_bias`）会导致调用层无法把属性映射进 aclnn 调用。配套规则：TTK 必须显式传入的 optional attr 不生成缺省态（每行都写键值，值域须包含 proto 默认值 false），但不得因此删掉 optional tensor 本身的空指针负向场景。

## 设计决策

- 为何 CSV 用 ABI 名而不是 IR 名：CSV 是 TTK/aclnn 调用的直接输入，绑定发生在 ABI 层；设计会话把该决策连同出处写进 `00_interface_type.yaml` notes（"CSV attributes 键使用 aclnn 头文件 ABI 参数名 hasBias（部署头 aclnn_thnn_fused_gru_cell_grad.h）"）与 `01_parameter_description.md` 的 has_bias 行（"ACLNN ABI 参数名 hasBias，TTK/aclnn 调用显式传值，不生成缺省态"）。
- 备选与放弃原因：无"CSV 键沿用 IR 名"的备选讨论记录——公共 Skill 的建模规则（blackbox-designer 约定：optional attr 使用 ABI 参数名且值域包含 proto 默认值，不生成缺省态）已定死。
- 当前方案属哪档路线：recommended_fastpath（照部署头抄，无歧义）。

## 系统信息

- 工程形态：黑盒 ACLNN ST 用例验收（ascendc-st-design 产物链）。
- 相关文件清单（与事件流实际读取一一对应）：
  - `docs/<Op>/develop/proto.md`（IR 属性名 has_bias 的出处）
  - `operators/<Op>_package/tests/blackbox/design/00_interface_type.yaml`（CSV 键用 ABI 名的决策记录）
  - `operators/<Op>_package/tests/blackbox/design/01_parameter_description.md`（has_bias 参数行 + aclnn 签名）
  - `operators/<Op>_package/tests/blackbox/testcases/aclnn<Op>_l0/l1/l2_*.csv`（attributes 列实际形态）

## 完整代码

两层命名的对照（verbatim）：

proto.md OpDef——IR 属性名（snake_case）：

```cpp
this->Attr("has_bias").AttrType(OPTIONAL).Bool(false);
```

`01_parameter_description.md`——has_bias 参数行（ABI 名与显式传值规则）：

```markdown
| has_bias | bool | 输入（attr） | 可选（默认 false；ACLNN ABI 参数名 hasBias，TTK/aclnn 调用显式传值，不生成缺省态） | - | - | bool | true / false | - | - | 前向 input_bias 是否定义（aten 语义：has_bias = input_bias.defined()）；控制两路 bias 梯度输出 shape：(3H,)（true）或 (0,)（false，aten 未定义张量的实体表达，proto.md §4 定案） |
```

CSV 行——attributes 键的实际上形态（L0 用例行 verbatim，注意 CSV 内双引号转义 `{""hasBias"":false}`）：

```csv
aclnnThnnFusedGruCellGrad_L0_001,aclnnThnnFusedGruCellGrad,"((512,1077,),(512,5385,),(512,3231,),(512,3231,),(512,1077,),(0,),(0,),)","('float32','float32','float32','float32','float32','float32','float32',)","('ND','ND','ND','ND','ND','ND','ND',)",,"{""hasBias"":false}","(2,3,4,5,6,)",,,"((-1000,-10,),(nan,nan,),)",,
aclnnThnnFusedGruCellGrad_L0_002,aclnnThnnFusedGruCellGrad,"((144,2018,),(144,10090,),(144,6054,),(144,6054,),(144,2018,),(6054,),(6054,),)","('float16','float16','float16','float16','float16','float16','float16',)","('ND','ND','ND','ND','ND','ND','ND',)",,"{""hasBias"":true}","(2,3,4,5,6,)",,,"((0.01,1,),(-0.01,0.01,),)",,
```

验收脚本中解析该键的方式（按 ABI 名正则，全量行命中；verbatim）：

```python
attrs = row["attributes"]
m = re.search(r'"hasBias"\s*:\s*(true|false)', attrs)
has_bias = (m.group(1) == "true") if m else None
```

## 预防

- 生成 CSV 前先打开部署头 `aclnn_<op>.h` 抄 ABI 参数名（不是从 proto.md OpDef 抄 IR 属性名）。
- 自检脚本对 attributes 键做存在性断言：本例脚本在缺 hasBias 键时记 `hasBias attr missing` 错误——把"键用错名字"变成可机检的失败而不是静默漏配。
- optional attr 的值域必须包含 proto 默认值（false），且不生成缺省态行；同时保留 optional tensor 的空指针负向场景（EX-S6 类）。

## 验证信号

来源：同一次黑盒 ACLNN ST 用例验收会话——独立校验脚本对全部 608 行 CSV 逐行解析 attributes 并统计 hasBias 取值分布，退出码 0、零错误。

- L0 44 行 hasBias=true 20 / false 24，L1 515 行 true 262 / false 253——两文件合计 559 行全部命中 hasBias 键、零缺键（来源平台：agnostic——host 侧 CSV 静态校验；证据等级：tool_observed）。
- L2 49 行负向同样全部携带 hasBias 键，且 dtype×hasBias 在 L0 层 3×2 全交叉非零（脚本显式检查 `L0 missing dtype x hasBias combo` 无报错）（来源平台：agnostic；证据等级：tool_observed）。
- 脚本运行输出 `NO CONTRACT ERRORS`、EXIT=0（来源平台：agnostic；证据等级：tool_observed）。

## 失效边界

- 本卡断言"CSV attributes 键 = 部署头 ABI 参数名"；不同算子的部署头参数名大小写风格须逐算子核对（本例 has_bias→hasBias，不代表所有属性都机械转小驼峰）。
- 未验证场景：TTK/harness 对错误键名（如写成 has_bias）的实际报错形态——本 trace 无执行事件，未上板验证。
- 推断可迁移：凡 aclnn 部署头两段式签名的算子，该两层命名机制均成立（未验证，推断可迁移——结论按定义与芯片平台无关）。

## 坏实践

- 从 proto.md OpDef 抄 snake_case 属性名直接写进 CSV attributes（`{"has_bias":false}`），调用层无法映射。
- optional attr 只在有非默认值时才写键、生成"缺省态"行——与"TTK 必须显式传入 optional attr"的约定冲突，也会让 dtype×attr 交叉覆盖统计失真。
- 为省事删掉 optional tensor 的空指针负向场景（EX-S6 类）——显式传值不等于该 tensor 永远存在。

## 误诊

- 验收时看到 `hasBias` ≠ `has_bias` 误判为"CSV 键拼写错误/与 proto 不一致"——实际是 IR↔ABI 两层命名的有意映射（本次验收若不读设计文件 notes 很容易误打回）。


