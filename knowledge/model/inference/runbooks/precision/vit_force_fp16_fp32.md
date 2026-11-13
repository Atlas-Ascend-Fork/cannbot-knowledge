---
{
  "type": "Runbook",
  "title": "ViT-L/14 视觉编码器 force_fp16 全图切换的精度门禁验证（含 fp32 基线噪声带标定）",
  "description": "M400（ViT-L/14，末级 L2 归一化输出 [1,512]）fp32 严格模式基线本身在默认 rtol=atol=1e-3 下 FAIL（max_abs=1.48e-3、cosine=0.99995、双侧 norm=1.0）；累加顺序与 L2 归一化可能解释差异，但未逐层隔离验证。据实测统计标定门禁 rtol=1e-2/atol=2e-3（用户裁定）。FORCE_16=True（ge.exec.precision_mode=force_fp16）全图 fp16 下 verify PASS：max_abs=0.00156976、cosine=0.99995029，所列误差统计量与 fp32 基线接近，不能据此证明同分布；同口径串行 avg 9.45→5.99ms（本次观测，精度模式不同非同精度对比）。",
  "tags": [
    "task.implementation",
    "topic.precision",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# ViT-L/14 视觉编码器 force_fp16 全图切换的精度门禁验证（含 fp32 基线噪声带标定）

## 适用场景

- 模型/框架：M400（ViT-L/14 视觉编码器，DINOv2-reg 风格：24 层、hidden 1024、16 头、581 token、Gemm 1024→512 + BNNeck + L2 归一化头，输出 [1,512] float32），onnx 图模式经 GE Session v2 加载。
- 平台/版本：Ascend 910B 单卡（卡 0），CANN 9.1.0（aarch64）；golden 为 CPU onnxruntime 1.31.0。
- 目标与工作负载：单卡推理 batch=1 串行（THREAD_NUM=1、circle=1000）；评估 `FORCE_16=True`（ge.exec.precision_mode=force_fp16 全图）能否过精度门禁。
- 缺失信息：fp16 收益的 batch>1 场景未测；bf16 与 HF32 路径均未验证（allow_hf32 不是 bf16 开关）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_4}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_5}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_6}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：fp32 严格模式基线 verify 在默认阈值（rtol=atol=1e-3）下 FAIL（事件 139）：

```
[FAIL] output[0] feature (float32) max_abs=0.00148179 max_rel=506.4520% expected_shape=[1, 512] actual_shape=[1, 512]
```

误差分布特征（事件 143/151）：13/512 元素 abs_err 略超 1e-3 且集中在 L2 归一化后的小数值元素（|v|≈0.02～0.1，rel 1～8%）；数值健全性检查（事件 151）：

```
ref: norm=1.000000 min=-0.1153 max=0.1240
act: norm=1.000000 min=-0.1151 max=0.1239
cosine similarity: 0.99995333
abs err: mean=3.420e-04 p50=2.931e-04 p99=1.088e-03 max=1.482e-03
elements > 1e-3: 13 / 512
elements > 2e-3: 0
```

框架默认严格 fp32（事件 147：`must_keep_origin_dtype` + `allow_hf32=0`），排除精度模式引入。

结论一（逐字）：

M400 fp32 严格模式（must_keep_origin_dtype、allow_hf32=0）基线在默认阈值 rtol=atol=1e-3 下 verify FAIL：max_abs=1.481794e-03、13/512 元素超限且集中在 L2 归一化后小数值元素（|v|≈0.02～0.1）；cosine=0.99995333、双侧 norm 均=1.0、p99=1.088e-03、无 >2e-3 元素——可能与 fp32 GEMM 累加顺序及末级 L2 归一化有关，未完成逐层根因隔离；门禁基于本例观测与业务容忍度调整（用户裁定 rtol=1e-2/atol=2e-3）。

判定依据（判别）：双侧 norm 均=1.0、cosine=0.99995、本样本 p50/p99/max 的数值及未见 >2e-3 元素、无 >2e-3 离群——与数值舍入假设相符，但不足以排除语义错误；误差集中于 L2 归一化后小数值元素（归一化放大相对误差）。门禁由用户在三个选项中裁定 atol=2e-3 + rtol=1e-2（事件 155）。

## 探针与操作

force_fp16 的实现为框架级环境变量（事件 147，main.cc 原文）：

```
${LOCAL_PATH_1}  std::string allow_hf32 = GetEnv("ENABLE_HF32", "False") == "True" ? "1" : "0";
${LOCAL_PATH_2}  std::string force_16 = GetEnv("FORCE_16", "False") == "True" ? "1" : "0";
${LOCAL_PATH_3}  if (allow_hf32 == "0") {
${LOCAL_PATH_4}    ge_init[ge::AscendString("ge.exec.precision_mode")] =
${LOCAL_PATH_5}        ge::AscendString(force_16 == "1" ? "force_fp16" : "must_keep_origin_dtype");
${LOCAL_PATH_6}  ge_init[ge::AscendString("ge.exec.allow_hf32")] = ge::AscendString(allow_hf32.c_str());
```

操作序列（事件 618/622）：
1. `FORCE_16=True bash run.sh 400 --circle 5`（确认 `precision : force_fp16 (allow_hf32=0)`）；
2. `python3 tools/verify.py 400 --rtol 0.01 --atol 0.002`（精度门禁）；
3. 独立 python 复算 cosine/分布（与基线同方法）；
4. `FORCE_16=True bash run.sh 400 --circle 1000 --debug-freq 200`（同口径性能门禁，单次）。

## 机制与判别

观测（事件 619/623）：fp16 全图 verify PASS：

```
[PASS] output[0] feature (float32) max_abs=0.00156976 max_rel=647.6260%
cosine: 0.99995029  norm_act=0.999839
abs err p50/p99/max: 2.93e-04/1.11e-03/1.57e-03
```

结论二（逐字）：

FORCE_16=True（ge.exec.precision_mode=force_fp16，全图 fp16）verify PASS：max_abs=0.00156976（较 fp32 基线 1.48e-3 仅略增），cosine=0.99995029，abs_err p50/p99/max=2.93e-04/1.11e-03/1.57e-03 与 fp32 基线统计量接近（p50=2.93e-4/p99=1.09e-3/max=1.48e-3）。

判别：fp16 的所列误差统计量与 fp32 基线接近，不能据此证明同分布（p50/p99 几乎相同、max 仅 +0.9e-4），本次样本未观测到明显新增离群/溢出特征，不能证明全域误差分布或所有输入的语义等价；门禁阈值（atol=2e-3）覆盖 fp16 噪声带。注意 norm_act=0.999839（fp32 基线为 1.000000）——fp16 舍入使 L2 归一化后的范数略偏离 1，对范数敏感的下游用法需评估。

性能观测（事件 623/630，单次运行）：

结论三（逐字）：

本次观测：FORCE_16 后同口径串行 avg 9.45→5.99ms、串行 QPS 105.8→166.8；iter2 kernel 总时长 9386→5850us/iter（四个线性 GEMM 族合计 5045.5→2289.8us）。（fp32 与 fp16 精度模式不同，非同精度对比。）

## 验证信号

- 事件 139/143：fp32 基线默认阈值 FAIL 与误差分布表（verify 工具输出）。
- 事件 151：cosine/norm/percentile 独立复算（numpy）。
- 事件 155：用户对门禁阈值的裁定（决策事件）。
- 事件 619/623：fp16 verify PASS + cosine/分布复算（Ascend 910B / CANN 9.1.0，单次）。
- 事件 630：iter2 msprof kernel 族表（FA 1342us、GEMM 族 2289.8us、LN 族 988us、Transpose 454us）。
- 事件 615：对照 iter1（fp32+FA）kernel 总时长 9386us/iter。
- 门禁回退路径已写入 `models/M400/M400_env.sh`（`FORCE_16=False` 关闭；全关回基线口径）。

## 适用与失效边界

- 适用条件：末级有 L2 归一化的检索/相似度类视觉特征输出，且业务容许 atol≈2e-3 量级误差带；fp16 前必须先标定 fp32 基线噪声带（本例 fp32 基线本身 1.48e-3，已逼近 1e-3 默认阈值——不先标定会把基线既有误差误判为 fp16 回归）。
- 失效边界：对范数严格=1 或对 <1.6e-3 绝对误差敏感的下游不可直接采用（norm_act=0.999839）；分类头/回归头等非归一化输出未验证；batch>1 场景未测。
- 通用加速承诺不成立：本例收益主要来自线性 GEMM 族（fp32 下已近 fp32 Cube Roofline ~88%，fp16 理论 ×2～4 的上限），GEMM 占比低的模型收益不同。
- bf16 与 HF32 路径均未验证；`FORCE_16` 与 `ENABLE_HF32` 组合语义以 main.cc 为准（allow_hf32=1 时 precision_mode 分支不生效）。
