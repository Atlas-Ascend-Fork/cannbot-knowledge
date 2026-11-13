---
{
  "type": "Runbook",
  "title": "16 rank CacheDiT 单测 SIGSEGV：私有 alias 缺 xllm_npu_test_runtime",
  "description": "16 rank CacheDiT 单测 SIGSEGV 的根因：私有 alias 裸 add_executable 绕过 cc_test 未链接 xllm_npu_test_runtime，aclInit 未执行致首个 npu:0 触碰即 -11；用 ELF 字节扫描加 ninja 链接输入判别，修复即改用公开目标。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 16 rank CacheDiT 单测 SIGSEGV：私有 alias 缺 xllm_npu_test_runtime

## 适用场景
- C++ 多 rank NPU 单测（GTest + torch_npu/ACL）出现部分 rank SIGSEGV（exit -11）、其余 rank 被 cleanup（-15）、伴随 TCPStore connection reset 的崩溃定位。
- 私有测试别名（绕过构建系统标准测试目标的 add_executable）与公开 cc_test 目标行为不一致的排查。
- 用 ELF 符号/字节扫描 + ninja 链接输入列表判别"测试二进制是否绑定了 NPU 测试运行时初始化"的方法复用。

## 触发与观测
- 触发：G3 实际 16 rank CacheDiT 单测（minimax_h3_cache_collective_test 同源 case，私有 alias minimax_h3_dense_test 运行）rank0 与 rank7 exit -11，其余 14 rank -15，无 XML 输出。
- 观测：wall_seconds=23.044；crash_summary 的 error 块：
````text
 "error": {
  "failed_exit_codes": [
   -11,
   -11
  ],
  "signals": [],
  "timeout": false
 },
````
- rank1 存活进程 stderr：TCPStore::ping connection reset by peer（c10d Utils.hpp:679），GTest 全局环境已 setup、单测运行中——连接重置是 rank0/7 崩溃的后果。

## 探针与操作
- 符号线索：私有 alias minimax_h3_dense_test（sha 2c361fae）无 init_npu_test_runtime/NpuPythonEnvironment/aclInit 符号；公开 minimax_h3_cache_collective_test（sha eb5708）包含这些符号。
- ninja 链接规则对比：公开目标链接 third_party/torch_npu_ops/triton_npu/test/CMakeFiles/xllm_npu_test_runtime.dir/.../tests/npu_test_environment.cpp.o（build.ninja 约 51794-51810 行）；alias 由 overlay 裸 add_executable 生成（约 51838 行）绕过 cc_test 的自动链接/whole-archive。
- 运行时初始化语义：tests/npu_test_environment.cpp 提供 init_npu_test_runtime()（含 ACL 初始化与 GIL 保存/恢复逻辑）。
- 字节扫描判别器：
````text
    # that lacks it (this is exactly how the private add_executable alias failed in -04). Byte-scan
    # discriminator verified against both ELFs: public target 1/9, alias 0/0; the authoritative
    # evidence is the Ninja link input list, recorded alongside.
    _elf = binary.read_bytes()
    runtime_markers = {
        marker: _elf.count(marker.encode())
        for marker in ("init_npu_test_runtime", "NpuPythonEnvironment")
    }
    if any(count == 0 for count in runtime_markers.values()):
        raise ValueError(
            "test binary is not bound to the NPU test runtime (xllm_npu_test_runtime); it would "
            "segfault instead of initializing ACL/torch_npu: " + json.dumps(runtime_markers, sort_keys=True)
        )
````
- 结果：public target 1/9、alias 0/0（init_npu_test_runtime/NpuPythonEnvironment 标记计数）。

## 机制与判别
- 机制链：alias 未链接 xllm_npu_test_runtime → init_npu_test_runtime/aclInit/_npu_init 未执行 → rank 首次触碰 torch::Device("npu:0")（create_process_group 前只设了 npu:0）即 SIGSEGV(-11)；其余 rank 经 runner Popen 清理(-15)；TCPStore connection reset 为 rank0/7 崩溃的次生后果。
- 判别：公开源码/cc_test 无缺陷（符号齐全的公开目标在同一 case 上 16D 已合格 236.266s）；问题在私有 alias 的构建方式而非测试逻辑或并行框架。
- 结论：崩溃形态：wall_seconds=23.044，rank0 与 rank7 exit_code=-11（SIGSEGV），其余 14 个 rank exit_code=-15（被 Popen 清理），非超时；rank1 存活进程 stderr 显示 TCPStore::ping connection reset by peer（c10d Utils.hpp:679），GTest 全局环境已 setup、单测运行中——连接重置是 rank0/7 崩溃的后果。
- 结论：根因确证：alias 二进制 minimax_h3_dense_test（sha 2c361fae）由 overlay 裸 add_executable 构建、绕过 cc_test，未链接 xllm_npu_test_runtime；ELF 字节扫描判别 public target 1/9、alias 0/0（init_npu_test_runtime/NpuPythonEnvironment 标记），build.ninja 链接输入列表（public 目标包含 tests/npu_test_environment.cpp.o，行 51800 附近）为权威证据——aclInit/_npu_init 未执行，rank 首个 npu:0 触碰即 -11；公开源码与 cc_test 无缺陷，修复 = 直接用已构建 public 目标 minimax_h3_cache_collective_test（sha eb5708）修改私有 runner/receipt，不改公开源码、不重编。

## 验证信号
- 客观信号：事件 99（crash_summary JSON）、事件 103（rank1 stderr TCPStore reset 栈）、事件 142（npu_test_environment.cpp 源码）、事件 152（build.ninja 公开目标链接规则含 xllm_npu_test_runtime）、事件 170（字节扫描判别器与 1/9 vs 0/0 结果）。
- 修复验证：会话结论为"正确处理使用已构建 public target 对照实际 runner 配置"；后续修改未在采用证据中完成；本轨迹内未重跑验证（禁止 NPU 复现约束）。

## 适用与失效边界
- 适用：多 rank NPU GTest 出现"个别 rank -11 + 存活 rank TCPStore reset"签名时，优先检查测试二进制是否绑定 NPU 测试运行时（ELF 标记扫描 + ninja 链接输入），再查测试逻辑。
- 失效边界：本判别只覆盖"二进制缺初始化运行时"这一成因；若符号齐全仍 SIGSEGV 则需查别处（如同 group_name/port 重复构造的 HCCL 懒加载重建问题，本轨迹 DGN02 节单独调查且机制明确 unknown）。
- 边界条件：byte-scan 判别器以标记存在性为准，ninja 链接输入列表才是权威证据；结论依赖 overlay 构建方式（裸 add_executable）与 cc_test helper 的自动链接差异。
- 相关独立发现（不并入本卡）：同组 gtest_repeat=3 场景下 iteration2 卡在首个 allreduce 的懒加载 HCCL comm 重建（同 group_name/port 同进程销毁后重建不收敛）+ npu_test_environment 单次 init/finalize 限制，内部机制 unknown；生产"一次创建终身复用 + host 侧请求重置"不受影响。
