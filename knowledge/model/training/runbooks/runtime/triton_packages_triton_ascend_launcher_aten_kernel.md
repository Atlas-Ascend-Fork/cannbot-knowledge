---
{
  "type": "Runbook",
  "title": "triton-ascend 3.2.0 launcher 固定 -std=c++17 与 Torch 2.14 ATen 头的 C++20 要求冲突：CC shim 改写编译标准",
  "description": "环境：Ascend 950 容器，triton-ascend 3.2.0，PyTorch/Torch 2.14（ATen 头要求 C++20），g++ 工具链；torchtitan-npu Engram 仓库的 Triton mHC HcHead 探针。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# triton-ascend 3.2.0 launcher 固定 -std=c++17 与 Torch 2.14 ATen 头的 C++20 要求冲突：CC shim 改写编译标准

## 适用场景

- 平台范围依据：source 0 seq 944的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 环境：Ascend 950 容器，triton-ascend 3.2.0，PyTorch/Torch 2.14（ATen 头要求 C++20），g++ 工具链；torchtitan-npu Engram 仓库的 Triton mHC HcHead 探针。

## 触发与观测

- Triton HcHead 探针未进入 kernel：四个用例全部在同一预编译步骤失败，NPU 无异常——环境兼容问题而非数值失败（source 0 seq 2236）。
- 根因（source 0 seq 2236 逐字）：当前 `triton-ascend 3.2.0` 的 launcher 固定用 `-std=c++17` 编译，而 Torch 2.14 的 ATen 头已要求 C++20。

## 探针与操作

- 该 Triton 包支持用 `CC` 环境变量指定编译器，但不支持覆盖它追加的 `-std=c++17`（source 0 seq 2264）。
- 修复（不修改 site-packages 与仓库代码）：在 `/tmp` 建仅用于本次测试的 g++ shim，把 `-std=c++17` 改写为 `-std=c++20`，其余参数原样透传；用独立 Triton cache 重跑同一组探针（source 0 seq 2264）。

## 机制与判别

- 失败点在主机侧 Triton launcher 的 C++ 编译标准，不在设备执行；因此既有 AscendC 全 override 主路径不受影响（source 0 seq 2236）。
- 判别依据：四个用例同步骤失败 + 无 NPU 错误 → 编译期问题；`CC` 可换编译器但 `-std` 被硬编码 → 需要 shim 而非换编译器（source 0 seq 2236、2264）。

## 验证信号

- tool_observed：C++20 shim 生效后，Triton HcHead 的 FP32/BF16 前后向等价测试与 `aot_eager` 编译反向共 4 项全部通过（source 0 seq 2283）。
- 修后组合升级验证：24.6B 参数、5.7B Engram 表、4K 序列、EP4/FSDP4、10 步、七类生产 override + Triton HcHead 的组合测试随后启动（source 0 seq 2283）。

## 适用与失效边界

- 适用：triton-ascend 3.2.0 + Torch 2.x（ATen 需 C++20）组合下 Triton kernel 预编译失败的场景；临时绕过方案（/tmp shim + 独立 cache）。
- 失效/限制：shim 是测试级 workaround，不改上游 launcher；若 triton-ascend 后续版本放开 `-std` 覆盖或升级默认标准，本卡失效；长期方案是升级依赖而非维持 shim（source 0 seq 2236 提到的首选路径）。

## 附：断言存档

- triton-ascend 3.2.0 launcher 固定 -std=c++17 与 Torch 2.14 ATen 头 C++20 要求冲突导致 Triton kernel 预编译失败；用 CC 指向 /tmp g++ shim 改写为 -std=c++20 后 FP32/BF16 前后向等价与 aot_eager 反向 4 项测试全部通过

```text
该 Triton 包支持用 `CC` 指定编译器，但不支持覆盖它追加的 `-std=c++17`。我会在 `/tmp` 建一个仅用于本次测试的 g++ shim，把这一项改写为 `-std=c++20`，其余参数原样透传；不修改 site-packages，也不改仓库代码。
```
