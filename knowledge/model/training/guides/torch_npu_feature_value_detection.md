---
type: Guide
title: NPU_ASD_CONFIG：梯度特征值、冷却与 Checksum 联动
description: 说明长稳训练的异常检测、两层时间窗和三振计数，不把检测视为自动修复。
tags:
- task.debugging
- topic.precision
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/fault_diagnosis/feature_value_detection.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_CONFIG.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_SIGMA_THRESH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_UPPER_THRESH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_step.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/profiler_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_CONFIG.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_SIGMA_THRESH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_UPPER_THRESH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/fault_diagnosis/feature_value_detection.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_asd_detector.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/asd/_silent_fault_data.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/asd/_silent_fault_data.py
  role: implementation
created_at: '2026-11-09T02:56:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# NPU_ASD_CONFIG：梯度特征值、冷却与 Checksum 联动

## 版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`。NPU_ASD_CONFIG 适用 TorchNPU≥7.1；≤7.0 使用旧入口并按其版本文档处理。本卡选取A2/A3与950DT训练（950DT仅按新CONFIG证据），BF16/FP32；明确不支持 TorchAir 场景。

## 检测和日志

enable 默认 false。开启后采梯度 Tensor 的特征值，经异步线程判断、冷却抑制和三振计数报告异常。单次 grad-norm spike 的 Event/INFO 日志需 TORCH_NPU_LOGS=silent；达到三振阈值后输出 feature detection detects abnormal results 的 Warning。日志缺失先核对开关与日志级别，不直接推断没有异常。

cooldown 默认 5 分钟，窗口内多次梯度异常按同次处理；strikes_window 默认 480 分钟，strikes_num 默认 3。它们是不同窗口，不能把每个参数报警都累计成独立三振。

## Checksum 与成本

with_checksum 默认 false；三振异常后可通知各卡同步启用 matmul/Tensor.matmul 输入输出校验。一次开启持续时间复用 cooldown，checksum_cooldown 默认 180 分钟限制再次开启。两条路径都只支持 BF16/FP32，不据此覆盖 FP16/FP8。

upper_thresh1 默认 1000000、upper_thresh2 默认 100；grad_sample_interval 默认 3，减小采样间隔提高覆盖同时增加成本，来源指出性能下降可能超过 2%。还可能额外占用约 1.5GB 显存甚至引发 OOM，这些是来源提示，不是本地测量结果。

## 核验

记录检测配置、梯度 dtype、冷却后的独立事件和跨 rank Checksum 日志，再回到真实数值与硬件/训练问题定位。检测不会自行修复异常，也不保证覆盖所有静默错误。本次没有运行训练、注入异常或测量开销。

## 新旧入口的版本与优先级

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的NPU_ASD_CONFIG页还列950DT，仍限BF16/FP32训练及非TorchAir场景；本卡据此补齐950DT的新入口范围。旧NPU_ASD_ENABLE、NPU_ASD_SIGMA_THRESH、NPU_ASD_UPPER_THRESH页面明确适用于TorchNPU≤7.0，不能从主线目录中仍存在这些页面推断其文档范围自动升级到26.x。

|旧入口|旧页面含义|
|--|--|
|NPU_ASD_ENABLE|默认0关闭；1只打印异常日志不告警，2开启并告警，3还记录Device info过程数据|
|NPU_ASD_SIGMA_THRESH|相对跳变阈值二元整数对，默认100000,5000，每项≥3|
|NPU_ASD_UPPER_THRESH|绝对阈值二元整数对，默认1000000,10000，每项≥3|

旧阈值页将第一项对应一级终止/告警，第二项对应CANN日志级别0/1/2下的Warning预警，需结合旧ENABLE模式理解；不能把它与新CONFIG的冷却和三振状态机混写。默认阈值优先保留；确认波动属于正常后调大可减小误检但降低检出率，持续spike却无告警时调小可提高检出率但增加误检。旧页的val*2或跳变比例*2是该旧算法的调整示例，不是所有新检测策略的通用阈值。

主线_step.py仍保留兼容旧入口的分支：只有NPU_ASD_CONFIG完全未设置才读取NPU_ASD_ENABLE；CONFIG即使为空串或enable:false，也不会继续走旧变量。故两个入口同时留在启动环境中不是叠加检测，需先确定实际选中路径。旧分支还按底层silent-check版本选择兼容处理并提示升级，源码保留分支不等于已确认所有现代软件/产品组合支持旧协议。

## 解析与验收细节

当前CONFIG解析中的enable/with_checksum只接受小写true/false，非法值报错；cooldown、strikes_num、strikes_window、checksum_cooldown、grad_sample_interval需正整数，两个upper_thresh需整数≥3，不合法时Warning并使用默认值。不能仅凭环境字符串存在就断言每项已生效，应检查silent日志中实际启用参数。

启用时钩子安装读取环境后包装Module.__call__；配置应在初始化前明确设置，不把运行中修改os.environ视为已经重新安装检测。NPU_ASD_ENABLE页单独出现的950标签也不能覆盖其≤7.0版本限制；950DT的新CONFIG产品证据与旧变量页分别保留。本次未执行异常注入、长稳训练或显存测试。

## 开发说明补充的两级阈值含义

中英文开发页区分upper_thresh1的绝对梯度异常与upper_thresh2的疑似异常：超过第二级阈值的样本不更新历史均值，不能把两个阈值都当作独立的三振计数。checksum在开启窗口内对torch.matmul和Tensor.matmul输入输出校验，出现校验为True时记录“The result of Matmul checksum is abnormal” Warning；这与此前的梯度spike INFO及特征值Warning是不同事件。

源码/环境页的产品与版本范围仍单独成立；开发页只给BF16/FP32限制，不能仅凭本页无产品表扩展旧入口、TorchAir或其他dtype。冷却抑制避免同一次异常影响多个参数时重复计数，不表示数值错误被修复或训练状态回滚。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/fault_diagnosis/feature_value_detection.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_CONFIG.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_ENABLE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_SIGMA_THRESH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/eigenvalue_detection/NPU_ASD_UPPER_THRESH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_step.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/profiler_patches.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_CONFIG.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_ENABLE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_SIGMA_THRESH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/eigenvalue_detection/NPU_ASD_UPPER_THRESH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/fault_diagnosis/feature_value_detection.md)（constraint）

## 旧版 ASD 辅助入口与阈值数据（实现层增补）

`torch_npu/utils/_asd_detector.py` 提供 v1 框架层辅助：`set_asd_loss_scale(loss_scale)` 与 `register_asd_hook(x, weight)` 都先查 `_get_silent_check_version()`，**版本 >1 时直接 no-op 返回**（:11-24）；v1 路线下 `register_asd_hook` 仅当 `x.requires_grad` 且 `x._backward_hooks is None` 时给 Tensor 注册 `_silent_fault_detector.silent_fault_check_hook(weight)`。即在 v2/v3 算子面（见[silent_check](silent_check.md)）环境里这两个入口不再生效，调用不报错也不等于已注册检测。阈值数据侧 `torch_npu/asd/_silent_fault_data.py`：`parse_thresh` 解析逗号分隔两整数，格式非法（非两段/非数字）回退默认串，再各自抬到 min_value=3；**若第一段 ≤ 第二段也整体回退默认**（:5-16）。`get_thresh` 默认 upper="1000000,10000"、sigma="100000,5000"（与 NPU_ASD_UPPER_THRESH/NPU_ASD_SIGMA_THRESH 文档默认不同口径的旧入口）。`SilentFaultData` 持 pre/max/min 三个 NPU 上的 FP32 状态张量（±10^10 初值），`SilentFaultDataV2` 持 int64 step 与 3 元 float check 张量（:21-36）。这些状态张量是设备侧更新目标，本节只固定初始化与阈值解析。`asd_detector.py`/`silent_fault_data.py` 顶层文件为带 "This file will be discarded" 注释的再导出壳。

## 增补来源（residual P1 追加 2 条）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_asd_detector.py)（implementation）：全文 1-18。

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/asd/_silent_fault_data.py)（implementation）：全文 1-36。

## 发布 pin 对照（f3ecfe4a）

卡内涉及的 1 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 已绑定（等价/无行为差异）

- `torch_npu/asd/_silent_fault_data.py`：去空白等价（行尾空白/空行差异）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
