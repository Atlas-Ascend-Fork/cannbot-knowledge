---
type: Concept
title: SGLang 算子测试框架的精度、Profiler与CSV合同
description: 说明 check_accuracy/check_performance/make_executor 的独立基线、原地输入隔离、开关优先级、NPU
  task计时与产物边界。
tags:
- task.testing
- topic.precision
- topic.performance.analysis
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/README.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/developer_guide/contribution_guide_zh.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: constraint
created_at: '2026-11-08T11:03:53Z'
updated_at: '2026-11-08T11:03:53Z'
platforms:
- a2
- a3
- '950'
---

# SGLang 算子测试框架的精度、Profiler与CSV合同

## 工具职责

该框架经公开 `sgl_kernel_npu.operators` 接口比较实现并收集 NPU task 时间，面向 arch22/arch35，即 A2/A3、950；不是所有接口在每个平台都已验证的保证。算子测试、框架单测和真实Profiler集成分开，三者通过不能相互代替。

`check_accuracy(operator,args=(),kwargs=None,...)` 解析测试/参考实现、执行独立比较，再返回零参数 executor。Tensor/tuple/list/dict 递归比对，Tensor须同shape/dtype/device。`auto`与其具体后端别名不算独立实现；不支持的被测代际可skip，但缺实现/缺reference失败。先检查 `-rs`，不能把skip算成功样本。

默认 atol/rtol：FP32为1e-5、FP16为1e-3、BF16为5e-2，整数精确比较；可以按输出dtype覆盖。通用流程共享输入，原地或有状态算子须自行克隆/重置，避免reference污染被测输入。

## 命令开关和不执行情况

| 开关 | 语义 |
| --- | --- |
| `--impl/--impl-ref` | 默认 auto/torch_native；显式helper参数优先于测试选项。 |
| `--enable-perf=true/false` | 覆盖用例性能选择；省略采用代码配置，默认False。 |
| `--skip-acc-check=true/false` | 覆盖精度开关，默认False。 |
| `--prof-dir/--csv-path` | 指定产物位置，不负责开启性能；未给CSV路径就不写CSV。 |
| `--npu-device` | 选择可见逻辑设备；不改变导入时缓存架构。 |

精度和性能都关时算子不执行，故此类“测试通过”不提供Kernel运行证据。`extra_checks` 默认排除，显式函数路径或 `-k` 也不能绕过marker，需 `-m extra_checks` 或 `-m ""`。

## Profiler度量与所有权

`check_performance(executor,...)` 处理Profiler、pytest属性及可选CSV；warmup/active默认均5且必须为正Python整数，bool也拒绝。返回值记录 `accuracy_checked`。度量为平均每轮 **NPU task耗时之和（微秒）**，不等于端到端请求延迟或包含全部Host开销的时延。

Profiler数据保留于 `<prof_dir>/prof_<function>/<case-run>/`；CSV保留三位小数，已有列schema必须一致，变schema后换文件。串行pytest或单worker运行，同设备并发profiling/同CSV并发写入不在受支持用法内。

`make_executor` 仅绑定参数，不执行、不验证、不复制或刷新输入；`accuracy_checked=True` 只能在手工完整比较返回值及被修改存储后设置。重复性能调用必须由调用方保证状态合法。底层 `benchmark_npu` 要求新输出目录，单独调用不处理CLI、实现选择、代际skip或CSV。

## 验证入口

在上游checkout及匹配NPU环境中，可用公开接口测试的 `--skip-acc-check=false --enable-perf=false -v -s -x -rs` 先验精度，再启用性能。框架路径 `tests/python/framework` 的 `npu_integration` 才包含真实Profiler集成，其余部分边界可能被替换；这些用例不建立历史性能回归基线。本次仅阅读工具合同，未运行上游测试或采集Profiler。
