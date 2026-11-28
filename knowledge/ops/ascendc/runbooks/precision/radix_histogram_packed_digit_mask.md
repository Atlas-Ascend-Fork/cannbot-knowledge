---
type: Runbook
title: 基数直方图打包 digit 时同步转换有效掩码
description: 将 uint32 digit 压成 uint8 后按相同 lane 映射转换谓词，防止尾块直方图计数污染。
tags: ["task.debugging", "topic.precision", "topic.memory"]
status: draft
sources: []
created_at: "2026-11-11T03:06:30Z"
updated_at: "2026-11-11T04:13:48Z"
platforms: ["950"]
---

# 基数直方图打包 digit 时同步转换有效掩码

## 适用场景

将整数 digit 从 32 位打包到 8 位后，原有有效掩码不能自动获得相同的 lane 映射。数据与谓词必须一起转换，再交给字节粒度的直方图统计。

## 症状与记录

CANN 9.3、dav-3510 的整数 TopK 基数选择候选中，32 位 digit 经过两级打包成为字节向量，直方图侧也显式使用两级打包后的有效谓词。记录中的表达方式为 `bytes.掩码(pack(pack(active)))`，这里是结构说明，不是可直接编译的 SDK API。

## 定位与处理

1. 写出原始有效元素与打包后字节 lane 的一一对应关系，确认打包是否伴随 lane 重排。
2. 将谓词经过与数据一致的映射；不能只改变数据类型或原样复用旧掩码。
3. 用尾部无效 lane 填入与有效数据相同的热点 digit，使错误计入立即反映在桶计数中。
4. 每轮核对所有桶之和等于本轮有效候选数，随后才计算阈值桶和候选前缀。

## 验证边界

覆盖 0、1、向量边界前后及非整块长度；对照标量逐元素直方图，并检查计数类型是否容纳本轮候选数。不能把某个 tile 下 uint16 计数安全推广到任意规模。草稿：打包指令和谓词类型须按目标版本实例化验证。

相关：[整数 TopK 的类型转换与排序边界](../compilation/topk_integer_dtype_cast_sort_recipe.md)。本卡处理 digit 提取之后的计数掩码，不改变完整整数键的精确比较要求。
