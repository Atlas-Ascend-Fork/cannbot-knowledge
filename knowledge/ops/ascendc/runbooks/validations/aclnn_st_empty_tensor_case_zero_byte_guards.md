---
type: "Runbook"
title: aclnn ST 空张量用例接入：0 字节分配与拷贝守卫
description: 为空张量分支（B==0 或 H==0）扩展 aclnn ST 桩——manifest 放行 0 维、输入按 32B 占位分配、0 字节 memcpy 跳过；0 维 aclCreateTensor 描述符与空输出比对短路均实测可用。
tags: [task.testing, topic.implementation.memory_management, topic.implementation.api_layer.c_api]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# aclnn ST 空张量用例接入：0 字节分配与拷贝守卫


## 现象

在为 ThnnFusedGruCellGrad（对标 torch GRU Cell 反向的 NPU 算子，ops-registry-invoke 算子仓开发流程）开发空张量分支的系统测试时，遇到的问题：该算子的空张量分支进入条件是 `B == 0 或 H == 0`（grad_hy 形状 (B, H)），host TilingFunc 有空张量短路（HandleEmptyTensor 路由 tilingKey=2），但已有的 aclnn ST 测试桩是按正维度用例搭的，空张量用例根本进不了测试：

- ST 桩的 manifest 装载函数 LoadManifest 里写着 `if (c.B < 1 || c.H < 1) { err = "... B/H 须为正（空张量属 Branch-2）"; return false; }`——B==0 或 H==0 的用例在装载阶段就被拒绝；
- 输入侧设备内存按 `aclrtMalloc(&devGradHy, numGradHy * es, ...)` 原样分配——空张量用例下 `numGradHy = B * H = 0`、`numStorage = B * 5 * H = 0`，变成对 0 字节的 `aclrtMalloc`；
- 输入上载 `aclrtMemcpy(devGradHy, 0, inGradHy.data(), 0, ACL_MEMCPY_HOST_TO_DEVICE)`——空 `std::vector` 的 `data()` 可能为 nullptr，0 字节拷贝没有必要冒险。

与之对照，输出侧早在正维度无 bias 用例（bias 输出为 `(0,)`）时代就有了空张量口径：空输出按 32B 占位分配、poison 与读回对 0 字节输出跳过、比对对 0 元素短路通过。本卡记录把这套口径补齐到输入侧与 manifest 校验、使空张量用例全链路跑通真实 aclnn 调用链的完整配方。

## 适用场景（必填）

- **工程形态**：aclnn（ops-registry-invoke 算子仓开发流程；ST 走 `aclnnXxxGetWorkspaceSize → aclnnXxx` 两段式调用链，自研 manifest 驱动 C++ ST 桩）。
- **API 路径**：`aclrtMalloc` / `aclrtMemcpy` / `aclCreateTensor`（含 0 维描述符）/ aclnn 两段式调用链；ST 桩为 manifest(JSON) 驱动的自研 C++ 程序。
- **验证过的平台与 CANN 版本**：Ascend 950PR（arch35，运行时 coreNum=64、ub=253952 字节）+ CANN 9.0.0-beta.2（与 frontmatter `platforms` 严格一致）。
- **适用粒度**：`operator_family`——空张量退化的 aclnn ST 桩适配模式对带空输入合法退化的算子族同构。
- **路线优先级**：`recommended_fastpath`（接入空张量用例的最短正确路径；未见更优替代）。
- **明确不适用 / 未验证场景**：Kernel 直调（TTK）用例未在本卡验证；`aclrtMalloc` 以 0 字节单独调用是否必然报错未做 A/B 实测（32B 占位是防御性接入，见设计决策）；非 950PR 平台 / 其他 CANN 版本上 0 维 `aclCreateTensor` 的接受性未验证。

## 根因

ST 桩的输入链路与 manifest 校验假定 B、H 恒正——校验用 `< 1` 拒绝 0 维、输入侧对 0 字节 `aclrtMalloc` / `aclrtMemcpy` 未做占位与守卫，空张量用例无法进入测试。

## 解决配方

四处适配（before/after 完整代码见「完整代码」，均为事件流内逐字恢复）：

1. **manifest 校验放行 0 维**：`c.B < 1 || c.H < 1` 改为 `c.B < 0 || c.H < 0`（错误信息同步改为"须非负"）——B==0 / H==0 是算子接口合法退化，不是非法输入。
2. **输入 32B 占位分配**：`aclrtMalloc(&devGradHy, std::max(inGradHyBytes, static_cast<size_t>(32)), ...)`——与输出侧既有占位口径同款；占位不改变描述符 shape（仍是 `(0, 8)` / `(4, 0)` 这类含 0 维形状）。
3. **0 字节 memcpy 跳过**：输入上载改为 `(inGradHyBytes > 0 && aclrtMemcpy(...))` 短路守卫——两输入都为 0 字节时整条上载被跳过、`ok` 保持 true；非空输入行为不变。
4. **多套件 manifest 与退出码口径**：`main()` 增加 Branch-2 的 manifest/数据目录实参（argv[5..6]），退出码对红基线分支只要求 `stTotal2 > 0`（用例已编入）而不要求全过——测试先行阶段 kernel 未实现时回归基线不被破坏。

oracle 侧（gen_st_oracle.py / golden.py）**零改动**：`torch.empty(0, H)` / `torch.empty(B, 0)` 合成、`uniform_`、`inject`（numel==0 恒不注入）、空 batch 的 `sum(dim=0)`、空张量 `tobytes()`（0 字节文件）全部天然兼容，实测 12 个空张量用例的期望值生成全部正确。

## 设计决策

- **为何 32B 占位而不是照传 0 字节**：`aclrtMalloc` 传 0 的行为是实现定义（可能返回 null 或报错）；输出侧在正维度无 bias 用例上已验证过 32B 占位口径，输入侧直接沿用同一口径，占位字节不参与任何计算与比对。本 trace 未做"不占位"的 A/B 对照——守卫版全链路实测通过（诚实标注：占位的**必要性**是静态推理，**充分性**是实测）。
- **为何 memcpy 用短路守卫而不是依赖 0 字节拷贝的良定义性**：空 `std::vector::data()` 可返回 nullptr，`aclrtMemcpy(dst, 0, nullptr, 0, ...)` 无必要冒险；守卫后 0 字节用例的 `ok` 语义保持"上载成功"。
- **退出码为何不要求红基线分支全过**：测试先行流程下新分支 kernel 为桩、数值用例预期失败；退出码锚定"旧分支零回归 + 新分支用例已编入"（`stTotal2 > 0`），避免每次测试先行阶段 CI 假红。
- **被放弃的方案**：在 kernel 桩里临时写零让用例全过——放弃，会污染红基线信号（见同域[全空输出用例不构成红基线卡](empty_output_cases_cannot_form_red_baseline.md)）；为空张量单独写一套精简 ST 桩——放弃，与既有 manifest 驱动机制重复且丢失同链路可比性。

## 系统信息

- 工具链/环境：Ascend 950PR（arch35，coreNum=64、ub=253952）、CANN 9.0.0-beta.2、GCC 13.3.0、cmake 构建测试二进制。
- 调用链：`aclnnThnnFusedGruCellGradGetWorkspaceSize → aclnnThnnFusedGruCellGrad` 两段式；vendor 包经 build.sh 安装至 `${ASCEND_OPP_PATH}/vendors/ThnnFusedGruCellGrad/`。
- 相关文件（与事件流实际读/写一一对应，路径前缀 `/workspace/skills-dev-dev-1/plugins-official/ops-registry-invoke-glacier/`）：
  - `operators/ThnnFusedGruCellGrad_package/tests/aclnn/st_cases_branch2.json`（新建：12 条空张量用例 manifest）
  - `operators/ThnnFusedGruCellGrad_package/tests/aclnn/test_aclnn.cpp`（改造：LoadManifest 校验、RunStCase 输入分配/上载、main() 第三套件与退出码）
  - `operators/ThnnFusedGruCellGrad_package/tests/aclnn/run.sh`（改造：MANIFEST_B2、第三个 oracle 数据生成调用、test_aclnn 传参 argv[5..6]）
  - `operators/ThnnFusedGruCellGrad_package/tests/aclnn/gen_st_oracle.py`（读，零改动）
  - `docs/ThnnFusedGruCellGrad/develop/golden.py`（读，零改动——独立参考 oracle）
  - `operators/ThnnFusedGruCellGrad_package/op_kernel/arch35/thnn_fused_gru_cell_grad_empty.h`（读——empty 桩，Process 全核早退）
  - `operators/ThnnFusedGruCellGrad_package/op_host/arch35/`（读——host tiling 的空张量短路 HandleEmptyTensor：EMPTY_A 时 SetBlockDim(1) 严禁 0、usedCoreNum=0；EMPTY_R 时 4 约束切分）
  - `docs/ThnnFusedGruCellGrad/design/branches/DESIGN-BRANCH-2.md`、`docs/ThnnFusedGruCellGrad/design/Validation.md`（读——分支定义与用例矩阵）

## 完整代码

以下代码逐字取自事件流（改造前状态来自测试桩文件的完整读取；改造前后差异来自编辑事件的完整 old/new 串）。

### 1. LoadManifest 维度校验（before → after）

```cpp
// before（正维度口径，空张量用例被拒绝）：
        if (c.B < 1 || c.H < 1) {
            err = "manifest case " + c.caseId + " B/H 须为正（空张量属 Branch-2）";
            return false;
        }

// after（放行 B==0 / H==0）：
        if (c.B < 0 || c.H < 0) {
            err = "manifest case " + c.caseId + " B/H 须非负（B==0 或 H==0 属 Branch-2 empty）";
            return false;
        }
```

### 2. RunStCase 设备内存分配段（before → after）

```cpp
// before（输入按元素数原样分配，空用例即 0 字节 aclrtMalloc）：
    // 3) 设备内存（空输出 (0,) 按 32B 占位分配，描述符 shape 仍为 (0,)）
    void* devGradHy = nullptr;
    void* devStorage = nullptr;
    void* devOut[5] = {nullptr, nullptr, nullptr, nullptr, nullptr};
    const size_t outBytes[5] = {
        static_cast<size_t>(expectNum[0]) * es, static_cast<size_t>(expectNum[1]) * es,
        static_cast<size_t>(expectNum[2]) * es, static_cast<size_t>(expectNum[3]) * es,
        static_cast<size_t>(expectNum[4]) * es};
    if (aclrtMalloc(&devGradHy, static_cast<size_t>(numGradHy) * es, ACL_MEM_MALLOC_HUGE_FIRST) != ACL_SUCCESS ||
        aclrtMalloc(&devStorage, static_cast<size_t>(numStorage) * es, ACL_MEM_MALLOC_HUGE_FIRST) != ACL_SUCCESS) {

// after（输入同输出口径：32B 占位分配；字节量提为具名常量供上载守卫复用）：
    // 3) 设备内存（空输出 (0,) 按 32B 占位分配，描述符 shape 仍为 (0,)；
    //    空输入（B==0 或 H==0）同理按 32B 占位分配，0 字节 memcpy 跳过）
    void* devGradHy = nullptr;
    void* devStorage = nullptr;
    void* devOut[5] = {nullptr, nullptr, nullptr, nullptr, nullptr};
    const size_t outBytes[5] = {
        static_cast<size_t>(expectNum[0]) * es, static_cast<size_t>(expectNum[1]) * es,
        static_cast<size_t>(expectNum[2]) * es, static_cast<size_t>(expectNum[3]) * es,
        static_cast<size_t>(expectNum[4]) * es};
    const size_t inGradHyBytes = static_cast<size_t>(numGradHy) * es;
    const size_t inStorageBytes = static_cast<size_t>(numStorage) * es;
    if (aclrtMalloc(&devGradHy, std::max(inGradHyBytes, static_cast<size_t>(32)), ACL_MEM_MALLOC_HUGE_FIRST) != ACL_SUCCESS ||
        aclrtMalloc(&devStorage, std::max(inStorageBytes, static_cast<size_t>(32)), ACL_MEM_MALLOC_HUGE_FIRST) != ACL_SUCCESS) {
```

### 3. RunStCase 输入上载段（before → after）

```cpp
// before（无 0 字节守卫；空 vector 的 data() 可为 nullptr）：
        // 4) 输入上载（device 与 golden 同一份位流——两端同源）
        if (aclrtMemcpy(devGradHy, static_cast<size_t>(numGradHy) * es, inGradHy.data(),
                        static_cast<size_t>(numGradHy) * es, ACL_MEMCPY_HOST_TO_DEVICE) != ACL_SUCCESS ||
            aclrtMemcpy(devStorage, static_cast<size_t>(numStorage) * es, inStorage.data(),
                        static_cast<size_t>(numStorage) * es, ACL_MEMCPY_HOST_TO_DEVICE) != ACL_SUCCESS) {

// after（短路守卫：0 字节输入整条跳过，ok 语义不变）：
        // 4) 输入上载（device 与 golden 同一份位流——两端同源）；
        //    空输入（0 字节）跳过 memcpy
        if ((inGradHyBytes > 0 && aclrtMemcpy(devGradHy, inGradHyBytes, inGradHy.data(),
                        inGradHyBytes, ACL_MEMCPY_HOST_TO_DEVICE) != ACL_SUCCESS) ||
            (inStorageBytes > 0 && aclrtMemcpy(devStorage, inStorageBytes, inStorage.data(),
                        inStorageBytes, ACL_MEMCPY_HOST_TO_DEVICE) != ACL_SUCCESS)) {
```

### 4. 输出侧既有空张量口径（本卡未改，空张量通过链的其余环节，逐字）

```cpp
// poison 阶段：0 字节输出跳过（红基线反巧合机制对空输出天然让位）
            // 5.1 poison 输出（红基线反巧合：接口桩不写输出时保持非期望值）
            for (int k = 0; k < 5; ++k) {
                if (outBytes[k] == 0) {
                    continue;
                }
                std::vector<uint8_t> poison(outBytes[k]);
                FillPoison(poison, c.dtype);
                if (aclrtMemcpy(devOut[k], outBytes[k], poison.data(), outBytes[k],
                                ACL_MEMCPY_HOST_TO_DEVICE) != ACL_SUCCESS) {
                    res.frameworkError = true;
                    res.message = "aclrtMemcpy poison 失败";
                    ok = false;
                    break;
                }
            }

// 读回阶段：0 字节输出跳过，本地缓冲 resize(0)
// 5.5 读回五路输出
            if (ok) {
                for (int k = 0; k < 5; ++k) {
                    runOut[run][k].resize(outBytes[k]);
                    if (outBytes[k] > 0 &&
                        aclrtMemcpy(runOut[run][k].data(), outBytes[k], devOut[k], outBytes[k],
                                    ACL_MEMCPY_DEVICE_TO_HOST) != ACL_SUCCESS) {
                        res.frameworkError = true;
                        res.message = std::string("aclrtMemcpy 读回失败: ") + kStOutputNames[k];
                        ok = false;
                        break;
                    }
                }
            }

// 比对：0 元素短路通过（TTK _check_empty 同语义），结果置 empty 标记
    const size_t n = actual.size() / es;
    if (n == 0) {
        r.empty = true;  // (0,) 空张量：比对短路通过（TTK _check_empty 同语义）
        return r;
    }
```

### 5. main() 第三套件与退出码（after，逐字）

```cpp
    const char* manifestPath2 = (argc > 5) ? argv[5] : "../st_cases_branch2.json";
    const char* dataDir2 = (argc > 6) ? argv[6] : "../st_data_branch2";
    int stTotal2 = 0;
    int stPassed2 = 0;
    int stFailed2 = 0;
    int stErrors2 = 0;
    if (!RunStSuite("Branch-2", manifestPath2, dataDir2, stTotal2, stPassed2, stFailed2, stErrors2)) {
        stErrors2++;  // manifest/流级失败按 ERROR 计（exit 非 0）
        stTotal2 = (stTotal2 > 0) ? stTotal2 : 0;
    }
    // ……（summary 打印略）
    // 退出码：smoke + Branch-0/1 ST 全过 = 0；Branch-2 红基线阶段（本分支数值
    // 用例 EMPTY_R 部分失败、EMPTY_A 空张量短路通过属桩即最终语义，Branch-0/1
    // 与最小通路用例保持通过）退出码 0 属预期。
    return (smokeFailed == 0 && stTotal0 > 0 && stFailed0 == 0 && stErrors0 == 0 &&
            stTotal1 > 0 && stFailed1 == 0 && stErrors1 == 0 &&
            stTotal2 > 0) ? 0 : -1;
```

### 6. run.sh 数据生成与传参（after，逐字）

```bash
MANIFEST_B2="${SCRIPT_DIR}/st_cases_branch2.json"
# ……（每套件一次全量重生成，禁用「已存在则跳过」缓存；TORCH_DEVICE_BACKEND_AUTOLOAD=0 关 torch_npu autoload）
TORCH_DEVICE_BACKEND_AUTOLOAD=0 python3 "${SCRIPT_DIR}/gen_st_oracle.py" \
    --manifest "${MANIFEST_B2}" --out "${SCRIPT_DIR}/build/st_data_branch2" --golden "${GOLDEN}"

export LD_LIBRARY_PATH=${ASCEND_OPP_PATH}/vendors/ThnnFusedGruCellGrad/op_api/lib/:${LD_LIBRARY_PATH}
./test_aclnn "${MANIFEST_B0}" "${SCRIPT_DIR}/build/st_data" \
             "${MANIFEST_B1}" "${SCRIPT_DIR}/build/st_data_branch1" \
             "${MANIFEST_B2}" "${SCRIPT_DIR}/build/st_data_branch2"
```

## 预防

为支持空张量分支的算子搭 aclnn ST 桩时，接入空张量用例前逐项检查：

1. manifest 装载校验是否用 `< 1` 拒绝了 0 维（应 `< 0` 放行合法退化）；
2. 输入侧 `aclrtMalloc` 是否对 0 字节做了占位（对齐输出侧 `(bytes > 0) ? bytes : 32` 口径）；
3. 输入上载 `aclrtMemcpy` 是否有 `bytes > 0` 短路守卫；
4. 期望值落盘/读取对 0 字节文件是否兼容（`fseek/ftell` 得 sz=0 → `resize(0)` 直接返回 true）；
5. poison/读回/比对三处对 0 字节输出是否已跳过/短路；
6. 退出码是否会把"红基线分支的预期失败"放大成全局假红。

## 验证信号

来源：ThnnFusedGruCellGrad 空张量分支（Branch-2，tilingKey=2）aclnn ST 测试先行开发会话——空张量用例接入后的全量实机运行（vendor 包安装 + cmake 构建 + oracle 数据生成 + ST 全量执行，真实设备）。

- 测试二进制编译通过（cmake/make `Built target test_aclnn`）（来源平台：950；证据等级：tool_observed）。
- 独立 oracle 对 12 个空张量用例的期望值生成全部正确：B=0 用例输出 shape 形如 `[[0, 24], [0, 24], [0, 8], [24], [24]]`（有 bias，bias 为 24 元素）或 `[[0, 24], [0, 24], [0, 8], [0], [0]]`（无 bias）；H=0 用例 `[[4, 0], [4, 0], [4, 0], [0], [0]]`；空张量数据文件实测 0 字节、EMPTY_R 的两路 bias 期望文件各 96 字节且内容全零（来源平台：950；证据等级：tool_observed）。
- 12 个空张量用例全部经真实 aclnn 两段式调用链执行、零 frameworkError——即含 0 维的 `aclCreateTensor` 描述符被 `GetWorkspaceSize` 接受、空张量路由 tilingKey=2 成功、32B 占位分配与 0 字节 memcpy 跳过全程无错（来源平台：950；证据等级：tool_observed）。
- 全量回归不退化：smoke 1/1、Branch-0 20/20、Branch-1 11/11 全 PASS；run.sh 退出码 0（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 本配方验证于 Ascend 950PR / CANN 9.0.0-beta.2 / arch35；其他平台（950DT 等核数不同型号、a2/a3/310p）与 CANN 版本上 0 维 `aclCreateTensor` 与空张量 tiling 路由的行为未验证，推断可迁移（空张量合法退化是 aclnn 层通用语义）。
- `aclrtMalloc` 0 字节占位的**必要性**未做 A/B 实测（无失败侧证据）；若某环境实测 `aclrtMalloc(0)` 良定义，可去掉占位但无收益。
- 空张量**输出侧**需要 kernel 写入的场景（如空 batch 有 bias 的零填充）不在本卡范围——那是"空 batch 归约"卡的主题；本卡只覆盖"调用链跑通 + 空输出比对短路"。
- 非连续布局/广播输入不在支持域（本算子 spec ND/contiguous required），本卡未涉及。

## 坏实践

- 直接把空张量用例塞进按正维度搭的 ST 桩而不做输入侧守卫——0 字节 `aclrtMalloc` / `aclrtMemcpy` 行为实现定义，可能在某些 CANN 版本上报框架错误，把语义正确的用例误判为 ERROR。
- 用 manifest 校验（`< 1`）替算子接口做合法性裁决——B==0 / H==0 是算子接口层的合法退化（host TilingFunc 有专门短路路径），ST 桩无权拒绝。

## 误诊

- 会话早期曾怀疑"aclnn 框架层可能会拒绝空张量、所有用例会变成 frameworkError"——实测证伪：`GetWorkspaceSize` 接受含 0 维的描述符并正常路由空张量分支，12 用例零 frameworkError（该假设当时标注为待实测推断，实测后修正）。


