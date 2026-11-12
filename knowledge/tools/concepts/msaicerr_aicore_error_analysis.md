---
type: Concept
title: msaicerr AI Core Error 分析工具的三模式命令与约束
description: msaicerr 用 -p 分析 AI Core Error 故障信息（输出 info.txt，运行内置算子样例检查环境）、-d 解析异常算子 Dump 为 .bin/.npy（输入/输出/workspace/tiling）、-dtype 做数据类型转换、-e 环境自检；仅支持本地分析、依赖 python3.7.5+、RC 形态不支持，通信与 Matmul 融合类算子暂不支持分析。
tags: [task.debugging, topic.implementation.debugging, topic.precision]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msaicerr-toolkit/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msaicerr-toolkit/references/functions-and-restrictions.md
    role: constraint
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msaicerr-toolkit/references/aicore-error-analysis.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msaicerr-toolkit/references/dump-parsing.md
    role: supporting
  - resource: https://gitcode.com/cann/cannbot-skills/blob/6b7d8fdf1f213c20f231688665879b5bffa7f9d6/tools/msaicerr-toolkit/references/dump-dtype-conversion.md
    role: supporting
created_at: "2026-11-05T02:40:00Z"
updated_at: "2026-11-05T02:40:00Z"
platforms: [a2, a3, "950"]
aliases: [msaicerr, AI Core Error, info.txt, exception_info, dump 解析]
---

# msaicerr AI Core Error 分析工具的三模式命令与约束

msaicerr 是 AI Core Error 问题定位专家（随 CANN 安装，位于 `tools/` 下，入口 `msaicerr.py`）。四种能力按入口参数区分：

| 功能 | 入口参数 | 输出 |
| --- | --- | --- |
| 分析 AI Core Error 问题 | `-p <故障信息目录>` | info.txt（按提示信息分析与定位） |
| 解析 Dump 文件 | `-d <dump 文件路径（含文件名）>` | `.bin`/`.npy`（算子输入/输出/workspace/tiling） |
| 转换 Dump 文件数据类型 | `-d` + `-dtype <目标dtype>` | `.npy`（供 numpy 直接查看） |
| 检查软硬件环境 | `-e` | 环境检查结果 |

## -p 完整分析

```bash
python3 msaicerr.py -p $HOME/aic_err_info -out $HOME/result -dev 0
```

- `-p` 必选，指定故障信息目录（asys collect 的输出或直接采集的故障信息）；前提是目录下存在 dump 文件（`dfx/data-dump`）、异常算子编译信息（`*.o` 与 `*.json`）和日志（`dfx/log/host/cann`），缺任一则无法提取 AI Core Error 信息；
- **不能进入 `-p` 指定目录或其子目录执行**，`-out` 也不能与 `-p` 相同或为其子目录，否则解析卡住或失败；`-out` 为空/无效/无写权限时报错退出；
- `-dev` 指定运行内置算子样例的 Device（默认 0）——分析时工具会运行内置算子样例检查软硬件环境是否正常；
- 终端提示 info.txt 路径，按其中提示信息分析定位。

## -d Dump 解析与 -dtype 转换

```bash
python3 msaicerr.py -d /demo/dfx/data-dump/0/exception_info.2.1.20250611171538370
python3 msaicerr.py -d <dump文件> -out <结果目录> -dtype float16
```

- 解析结果记录算子的输入、输出、workspace、tiling 信息；执行目录同级生成 `debug_info.txt` 记录工具执行日志；
- `-dtype` 转换支持 float16/bfloat16/int8 等常用类型；`debug_info.txt` 提示 `Can not read with dtype bfloat16` 时需自行安装 `bfloat16ext` 第三方库（不能换 dtype 碰运气）；
- `-dtype` 官方文档列举 13 种常用值，代码实际校验集为全部 43 个值，判读以代码校验集为准；
- AI Core Error 场景的异常算子 Dump 由运行时自动生成（`ASCEND_DUMP_SCENE` 环境变量支持轻量/普通/详细三档），导出算子输入输出、workspace、tiling，详细档还含寄存器与调用栈。

## 约束

1. **仅支持本地分析**：部署工具的环境应与日志所在环境为同一环境（跨环境拷贝分析不支持——工具会运行内置算子样例并依赖本地 CANN 环境）；
2. 依赖 **python3.7.5 及以上**；
3. **不支持 Ascend RC 形态**；
4. **暂不支持分析**以下算子的 AI Core Error 问题：MatmulAllReduce 类、MatmulAllReduceAddRmsNorm、MatmulAllReduceInplaceAddRmsNorm、AllGatherMatmul、MatmulReduceScatter、GroupedMatmulAllReduce、MemSet、NonMaxSuppressionBucketize——这些通信与 Matmul 融合类算子需转向按错误码走运行时调试、单独复现或采集更完整日志。

## 失效边界

- 本卡为命令契约与约束的蒸馏；退出码表（0/1-11/101-107）与错误类型解码属 AI Core Error 诊断工作流，见[AI Core Error 诊断工作流卡](aicore_error_diagnosis_workflow.md)与诊断向导既有卡（msaicerr dump dtype 与分析边界）。
