---
type: Concept
title: Runtime Dump 配置采集与 msaccucmp 精度比对流程
description: 通过 acl.json 配置模型或单算子 Dump（dump_list/layer/dump_data=stats|tensor/dump_op_switch），kernel 直调用 aclDumpOpTensors 提交张量描述；stats 原生 CSV 做统计筛查，tensor Dump 经 msaccucmp convert 转 NPY 后与 golden file_compare 比对，输出官方相似度指标。
tags: [task.debugging, topic.precision, topic.implementation.debugging]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-data-dump/SKILL.md
    role: primary
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-data-dump/references/acl-json.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-data-dump/references/capture.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-tools/blob/aeeb3ff8f1893983f04ccb28e674d1b160610ed9/skills/tool-data-dump/references/compare.md
    role: supporting
created_at: "2026-11-05T01:20:00Z"
updated_at: "2026-11-05T01:20:00Z"
platforms: [a2, a3, "950"]
aliases: [msaccucmp, dump_data, acl.json, dump_op_switch, aclDumpOpTensors, stats]
---

# Runtime Dump 配置采集与 msaccucmp 精度比对流程

定位「哪个算子引入了精度差异」的三步流程：通过 Dump 配置导出算子输入输出数据（模型 Dump / 单算子 Dump），用 msaccucmp 将原始 Dump 转为 `.npy` 并与 golden 比对，输出余弦相似度等官方指标。AI Core Error 场景的异常算子 Dump 由运行时自动生成，用 msaicerr 解析（msaicerr 工具卡在故障诊断批次迁入）。

## 配置入口与字段

配置写在 `acl.json` 根对象的 `dump` 对象中（`model_name`、`layer`、黑名单等在 `dump_list` 条目内），经首次 `aclInit(configPath)` 生效：

- **对象**：`dump_list`（必选）列出待 Dump 的整网模型；采全部模型的全部算子用 `"dump_list": [{}]`；模型推理用 `model_name`（文件加载为不带后缀的文件名或 ATC 模型 JSON 的 `name` 字段）+ `layer`（算子名数组，支持转换前原始算子名）筛选；
- **方向与内容**：`dump_data` 取 `stats`（原生 CSV 统计）或 `tensor`（原始数据）；`dump_mode` 选 input/output/all；
- **单算子**：单算子 API/单算子模型/`<<<>>>` 直调场景建议 `"dump_list": [{}]` 并启用 `dump_op_switch`；
- **控量**：`optype_blacklist` / `opname_blacklist`（仅模型 Dump 且 `dump_level=op` 时生效，最多 100 项）按类型或名称排除指定位置（`inputn`/`outputn`）；
- 官方基础文档未列出全部可选字段，不能据其缺项认定本机不支持；实际参数以执行端配套 CANN 资料为准。

**kernel 直调的 Host 接入**：`aclInit` 启用 Dump 后，用 `aclDumpOpTensors(opType, recordName, tensors, count, 0, stream)` 在 launch 前后分别提交输入/输出张量描述（头文件 `aclnn/acl_meta.h`，与库须同一套 CANN）。原地计算、别名或缓冲复用时必须在覆盖之前采输入、之后采输出——事后构造 input 描述不能恢复旧数据。

## stats 统计筛查

原生 `dump_data=stats` 输出 CSV（Input/Output、Index、Shape、Data Type、Format + 统计列）。对已有同输入 golden 的张量计算同名统计再比较：NaN/Inf 计数不同优先核验该观察点；Max/Min 超筛查范围提示值域差异；Avg 不同提示整体偏移。

关键边界：stats 的 Max/Min/Avg/L2norm 是张量摘要，**排列、通道置换或正负误差抵消可保持统计相同**（如 `[1,2,3,4]` 与 `[4,3,2,1]` 全部统计一致但逐元素不同）——stats 用于筛查候选，不能作为精度验收依据；未发现统计差异不等于 PASS。

## 解析与比对

在执行端找到配套 CANN 的 `tools/operator_cmp/compare/msaccucmp.py`：

```bash
# 原始 Dump 转 NPY（-d 接受单个 raw、逗号分隔列表或叶目录；目录不递归）
python3 <cann-root>/tools/operator_cmp/compare/msaccucmp.py convert -d <dump文件> -out <输出目录> -t npy
# 实际数据与 golden 比对（输出余弦相似度、最大绝对误差等官方指标）
python3 <cann-root>/tools/operator_cmp/compare/msaccucmp.py file_compare -m <actual.npy> -g <golden.npy> -out <结果目录>
```

- 原始 Dump 含头信息和张量描述，不用 `numpy.fromfile` 当裸数组读；一个 raw 可转出多个 input/output NPY；
- 只有实际布局需要时才做 Format 转换（`-f`；NC1HWC0、FRACTAL_NZ 等存储布局需还原为 golden 逻辑布局，FRACTAL_NZ 还需 `-s` 真实逻辑维度）——不能任意 reshape 或试 shape 直到接近 golden；
- 配对要求同一复现请求、相同原始输入下语义对应的张量：记录请求/调用、方向、索引、文件、shape、原始 dtype、布局与有效范围；无法唯一确定就标为未匹配，不按文件顺序、时间戳或数值相似度推测对应关系；
- `file_compare` 不接收工程 atol/rtol，也不输出异常元素坐标——超差与验收按工程判据另行逐元素检查；
- 返回 0 但没有目标 NPY 仍是未完成。

## 失效边界

- BF16 等原始 dtype 官方转换后可能以另一 dtype 的 NPY 表示，报告保留原始类型及转换说明；
- stats 支持情况应通过本机生成的 CSV 核验（tensor 可用不代表 stats 可用）；
- 中间调用无参考时不能仅凭数值表现判定首个异常层；精度偏差的根因定位方法见[精度调试指南](../../ops/ascendc/guides/precision/index.md)。
