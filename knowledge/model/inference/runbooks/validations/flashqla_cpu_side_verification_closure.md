---
{
  "type": "Runbook",
  "title": "FlashQLA 跨机 CPU 资产核验：哈希一致与逐值一致分别报告",
  "description": "来源 CPU 短用例中，state 同时报 hashes_equal=true 和 all_values_bitwise_equal=false；zero_state 两者为 true。二者不等价，state 差异未解释前不能称逐值复现。NPU 验证被权限阻塞，没有 A3 性能结论。",
  "tags": [
    "task.testing",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": [
    "a2",
    "a3"
  ]
}
---
# FlashQLA 跨机 CPU 资产核验：哈希一致与逐值一致分别报告


## 适用场景


FlashQLA/GDN 跨机接续实验中先核对 CPU 资产与测试工具。目标机器为 A3、历史读数来自另一台 A2；不混用两个平台的性能结果。

## 触发与观测

触发：用户授权的接续调优任务（无故障）。探针：hostname/npu-smi 现场核验、fixture/oracle SHA 溯源、容器特权探测（7 种非特权暴露方式全部 aclInit Resource_Busy EL0005）、CPU 侧脚本构建。观测：短用例哈希为 true，但 state 的逐值相等为 false；脚本 bash -n/py_compile 全过；NPU 容器路径阻塞。

## 探针与操作

`${EXPERIMENT_ROOT}`为本次实验工程根，含env、validation和可写logs/oracle_verify目录；`${FIXTURE_ROOT}`为已有输入fixture资产根，含下方actual_r9a与actual_training相对路径。两者不能假定相同，执行前须在本地设置变量并确认文件可读。历史输入资产未随卡片发布；仅替换路径不构成已复现。

关键探针与修复操作。证据角色覆盖：implementation, validation。

## 机制与判别


> CPU 短用例可复现：cpu_reproduce_short_fixtures.py 重建 state(67)/zero_state(129) 两个短用例后，报告哈希一致，但 state 的逐值比较为 false——state 的 hashes_equal: true（all_values_bitwise_equal: false），zero_state 的 hashes_equal: true 且 all_values_bitwise_equal: true（exit_code 0）。


> 验证脚本就绪与边界：run_a3_paired.sh/run_a3_stress.sh/run_all_a3.sh 三个脚本 bash -n 通过，wrapper_vs_device.py/profile_components_目标机器.py/compile_cold.py/cpu_verify_assets.py/cpu_compare_oracles.py/cpu_reproduce_short_fixtures.py/verify_manifest.py/rewrite_manifest.py/env_manifest.py 九个 python 模块 py_compile 通过；本轮全部产出为 CPU/编译侧，未宣称任何 A3 性能数字（轨迹自述 NPU 测量被容器权限阻塞，历史 A2 读数未沿用为结论）。


```
cd "${EXPERIMENT_ROOT}" && bash env/cpu_env.sh validation/long_chunk_oracle.py --selftest "${FIXTURE_ROOT}/actual_r9a/state_bf16.pt" --selftest "${FIXTURE_ROOT}/actual_r9a/zero_state_bf16.pt" --fixture "${FIXTURE_ROOT}/actual_training/real_27b_64k_bf16.pt" --output "${EXPERIMENT_ROOT}/oracle_verify/real_27b_64k_bf16.rebuilt.fp64.pt" > logs/oracle_rebuild.log 2>&1; echo "exit=$?"; tail -5 logs/oracle_rebuild.log; ls -la oracle_verify
```

## 验证信号


CPU 输出中，state(67) 的 hashes_equal=true、all_values_bitwise_equal=false；zero_state(129) 两项都为 true。state 的比较字段或数值差异需要继续解释，哈希相同不能覆盖逐值不等。三个 shell 脚本 bash -n、九个 Python 模块 py_compile 通过，仅证明静态语法；FP64 oracle 的重建运行结果没有进入采用证据。

## 适用与失效边界


只确认来源报告的有限资产核验与静态检查；不称“全部可做的 CPU 验证完成”。本轮没有 NPU 成对测量，不得借用历史 A2 毫秒数或从这些信号推导 A3 数值与性能。
