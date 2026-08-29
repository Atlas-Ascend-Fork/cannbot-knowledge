---
type: Guide
title: 命名转换规则对照表（附录）
description: 本文属于基础内容，介绍自定义算子工程中的命名转换规则。算子类型（OpType）通常采用大驼峰命名方式，配置中的实现文件名和Kernel入口名通常采用小写下划线命名方式。默认情况下，框架会根据OpType生成这些名称。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/appendix/naming_conversion_table.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 命名转换规则对照表

本文属于基础内容，介绍自定义算子工程中的命名转换规则。算子类型（OpType）通常采用大驼峰命名方式，配置中的实现文件名和Kernel入口名通常采用小写下划线命名方式。默认情况下，框架会根据OpType生成这些名称。
## 转换规则概述
转换发生在构建阶段。构建工具会根据已注册的OpType生成配置和相关代码；算子运行时使用已经生成的配置和符号，不会再次转换名称。
构建工具从左向右按以下规则处理字符：
1. 首字符大写转小写：首字符直接转换为小写，不插入下划线。
2. 前一个字符不是大写字母时插入下划线：当前字符是大写字母，且前一个字符是小写字母或数字时，在当前字符前插入下划线，并将当前字符转换为小写。
3. 连续大写与后续单词之间插入下划线：当前字符和前一个字符都是大写字母，但下一个字符是小写字母时，在当前字符前插入下划线，并将当前字符转换为小写。
4. 其他字符直接转换或保留：其他大写字母直接转换为小写；小写字母和数字保持不变。
构建工具还会检查OpType是否符合推荐的命名规范：首字符为大写字母，后续字符只能是字母或数字。不符合规范时会输出告警，建议使用大驼峰命名。
## 对照表
下表列出了常见算子名称的转换结果。结果以当前构建工具的实际转换结果为准。
算子类型（大驼峰）：文件名/Kernel入口名（小写下划线）：转换说明
AddCustom：add_custom：首字符转小写，Custom前插入下划线
ReduceMaxCustom：reduce_max_custom：Max和Custom前分别插入下划线
MatmulCustom：matmul_custom：Custom前插入下划线
BatchNormCustom：batch_norm_custom：Norm和Custom前分别插入下划线
Conv2DCustom：conv2_d_custom：D前是数字2，因此在D前插入下划线
SoftmaxCustom：softmax_custom：Custom前插入下划线
ReluCustom：relu_custom：Custom前插入下划线
LayerNormCustom：layer_norm_custom：Norm和Custom前分别插入下划线
SliceCustom：slice_custom：Custom前插入下划线
GatherV2Custom：gather_v2_custom：V前是小写字母，Custom前是数字2
SplitVCustom：split_v_custom：V和Custom前分别插入下划线
TransposeCustom：transpose_custom：Custom前插入下划线
OneHotCustom：one_hot_custom：Hot和Custom前分别插入下划线
TopKCustom：top_k_custom：K和Custom前分别插入下划线
## 特殊情况说明
### 连续大写字母
连续大写字母通常表示缩写。
