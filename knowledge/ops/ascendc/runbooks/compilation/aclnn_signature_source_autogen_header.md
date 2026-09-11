---
type: "Runbook"
title: aclnn 冒烟测试以 autogen 生成头为签名源
description: 多输出+属性算子的 aclnn 两段式签名以 build/autogen 生成头为事实源（输入→属性→输出 Out→ws→executor）；附完整冒烟测试。
tags: [task.testing, topic.compilation]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# aclnn 冒烟测试以 autogen 生成头为签名源


## 现象

自定义算子包（2 输入 + 1 个 bool 属性 + 5 输出）构建安装通过后，要写 `tests/aclnn` 冒烟测试验证最小调用通路。两段式 aclnn API 的参数顺序与命名**不能凭直觉拼**：属性放哪、输出参数叫什么、workspace 参数怎么排，猜错就是编译错或参数错位。实测做法是：**先构建，再读 `build/autogen/aclnn_<snake算子名>.h` 生成头**，按生成头逐参照抄。生成头给出的真实签名：

```c
__attribute__((visibility("default")))
aclnnStatus aclnnThnnFusedGruCellGradGetWorkspaceSize(
    const aclTensor *gradHy,
    const aclTensor *storage,
    bool hasBias,
    const aclTensor *gradInputGatesOut,
    const aclTensor *gradHiddenGatesOut,
    const aclTensor *gradHxOut,
    const aclTensor *gradInputBiasOut,
    const aclTensor *gradHiddenBiasOut,
    uint64_t *workspaceSize,
    aclOpExecutor **executor);

__attribute__((visibility("default")))
aclnnStatus aclnnThnnFusedGruCellGrad(
    void *workspace,
    uint64_t workspaceSize,
    aclOpExecutor *executor,
    aclrtStream stream);
```

## 适用场景

- 工程形态：算子仓（ops-registry-invoke 流程）`tests/aclnn/` 的**接口桩阶段验收**——最小调用通路冒烟（`aclnn<Op>GetWorkspaceSize` → `aclnn<Op>` → `aclrtSynchronizeStream` 全链返回 OK 即 PASS），任务验收口径明确该阶段**不做数值精度校验**（数值用例属 kernel 实现阶段，不是本卡用"放松测试"换取通过——桩阶段 kernel 本就无算法可校）。
- API 路径：`build/autogen/aclnn_<op>.{h,cpp}`（op_build 从 OpDef 生成的 API 桩）；`acl/acl.h`（aclInit/aclrtSetDevice/aclrtMalloc/aclrtMemset/aclCreateTensor/aclrtSynchronizeStream）；`tests/aclnn/CMakeLists.txt`（include/link 指向 vendors 安装树）。
- 验证过的平台与 CANN 版本：950（ascend950/arch35）+ CANN 9.0.0-beta.2。
- 适用粒度：operator_family——所有走 aclnn 两段式调用的自定义算子接口验收。
- 路线优先级：recommended_fastpath（构建 → 读生成头 → 按生成头写冒烟；dtype 覆盖 = OpDef DataType 列表逐组合）。
- 明确不适用 / 未验证：数值精度验收（本卡不含数值比对）；zero-size 张量（如 has_bias=false 的空 bias 输出）未测；非 ND 格式未测；属性为 List/必选属性的签名位置未测。

## 判别方法

签名映射规律（本例实测归纳，codegen 按 OpDef 的 INPUT→ATTR→OUTPUT 声明序展开）：

```
OpDef Input("grad_hy")        → const aclTensor *gradHy          （snake_case → camelCase）
OpDef Attr("has_bias")        → bool hasBias                     （位于全部输入之后、全部输出之前）
OpDef Output("grad_input_gates") → const aclTensor *gradInputGatesOut（输出名追加 Out 后缀）
尾参固定                       → uint64_t *workspaceSize, aclOpExecutor **executor
第二函数 aclnn<Op>            → (void *workspace, uint64_t workspaceSize, aclOpExecutor *executor, aclrtStream stream)
```

判别动作：构建后 `cat build/autogen/aclnn_<op>.h`，以生成头为唯一签名事实源；不确定时再看生成 `.cpp` 的属性透传（bool 属性经 `NnopbaseAddAttrWithDtype(&hasBias, sizeof(bool), 0, kNnopbaseBool)` 直传 executor，无额外校验）。

## 解决配方

测试骨架与流程：

1. `CHECK_ACL`/`CHECK_ACLNN` 宏包错检查（失败打印码值+位置并返回 -1）；
2. 每个 dtype 一例：按算子 Shape 契约构造 dims/strides（连续 ND 布局），`aclrtMalloc` + `aclrtMemset` 清零（桩阶段不构造数据，清零保运行确定性），`aclCreateTensor` 建描述符；
3. Phase 1：`aclnn<Op>GetWorkspaceSize(输入…, 属性, 输出…, &workspaceSize, &executor)`；`workspaceSize > 0` 才 malloc workspace；
4. Phase 2：`aclrtCreateStream` → `aclnn<Op>(workspace, workspaceSize, executor, stream)` → `aclrtSynchronizeStream`；
5. 全链 OK 打印 `[smoke] <case> PASSED`；释放全部 tensor/device 内存并销毁 stream；
6. `main`：`aclInit` → `aclrtSetDevice(0)` → 按 proto dtype 组合表逐行跑例 → `aclrtResetDevice` + `aclFinalize`。

dtype 覆盖规则：测试用例数 = OpDef `DataType({...})` 列表长度（本例 fp32/fp16/bf16 各一例，各 IO 同 dtype）。元素字节数：fp32=4，fp16/bf16=2（bf16 无 host 数据类型，按 `ACL_BF16` 枚举 + 按字节分配即可）。

配套链接顺序（`tests/aclnn/CMakeLists.txt`，vendor 安装目录置于 CANN lib64 **之前**，保证链接到本工程 run 包安装的 `libcust_opapi.so`）：

```cmake
# before（样例原序：CANN lib64 在前）
link_directories(
    ${CANN_HOME}/lib64
    ${CANN_HOME}/opp/vendors/<OpType>/op_api/lib  # libcust_opapi.so
)
## after（vendor 优先加载）
link_directories(
    ${CANN_HOME}/opp/vendors/<OpType>/op_api/lib  # libcust_opapi.so (优先加载)
    ${CANN_HOME}/lib64
)
```

`run.sh` 运行期前置：`export LD_LIBRARY_PATH=${ASCEND_OPP_PATH}/vendors/<OpType>/op_api/lib/:${LD_LIBRARY_PATH}`。

## 设计决策

- **签名事实源 = 生成头**：生成头由 op_build 从 OpDef 机械展开，属性位置/输出 `Out` 后缀等约定随版本演进，读当次产物比背文档可靠。
- **先独立预构建测试**（`tests/aclnn` 下单独 `rm -rf build && mkdir build && cd build && cmake .. && make`，已安装的 vendor 包即可支撑链接），通过后再跑官方 `./run.sh`（内部重跑全量 build.sh + 测试）——测试自身的编译错不必烧一次全量重建。
- **桩阶段零值输入**：不构造数值数据，`aclrtMemset` 清零保证运行确定性；冒烟只证明调用通路（含 tiling 执行与 kernel 启动），不证明数值正确——这两件事在验收口径里是分开的。
- **dtype 覆盖对齐 OpDef 枚举**：3 例 = DataType 列表长度 = 产出的 kernel `.o` 数，三方对账。
- 当前方案属 recommended_fastpath（接口桩阶段验收的官方口径路径）。

## 系统信息

- CANN 9.0.0-beta.2 / ascend950（arch35）；`ASCEND_OPP_PATH=$ASCEND_HOME_PATH/opp`。
- 目录布局：`operators/<Pkg>_package/tests/aclnn/{CMakeLists.txt, run.sh, test_aclnn.cpp}`；include 路径 `${CANN_HOME}/opp/vendors/<OpType>/op_api/include`（安装后的生成头）；链接 `ascendcl, nnopbase, cust_opapi`。
- 相关文件：`op_host/<op>_def.cpp`（OpDef，决定生成签名）、`build/autogen/aclnn_<op>.h`（签名事实源）、`$ASCEND_OPP_PATH/vendors/<OpType>/op_api/{include,lib}`（安装树）。

## 完整代码

`tests/aclnn/test_aclnn.cpp` 终版全文（verbatim 取自当次终版写入；2 输入/1 bool 属性/5 输出算子，fp32/fp16/bf16 三例）：

```cpp
/**
 * =============================================================================
 * <Pkg>_package/tests/aclnn/test_aclnn.cpp
 * =============================================================================
 * Role: ACLNN 接口冒烟测试（接口桩阶段）。
 *       只验证最小调用通路：aclnn<Op>GetWorkspaceSize →
 *       aclnn<Op> → aclrtSynchronizeStream 两段式调用返回 OK
 *       即 PASS，不做数值精度校验（数值用例由后续 kernel 实现阶段验收）。
 *       dtype 覆盖 = 算子原型 dtype 组合表的三行：fp32 / fp16 / bf16。
 * =============================================================================
 */

#include <cstdint>
#include <cstdio>

#include "acl/acl.h"
// 本算子 vendor 包的公共 ACLNN API 头（build 后安装于
// $ASCEND_OPP_PATH/vendors/<OpType>/op_api/include/）。
#include "aclnn_thnn_fused_gru_cell_grad.h"

#define CHECK_ACL(x)                                                          \
    do {                                                                      \
        aclError __ret = (x);                                                 \
        if (__ret != ACL_SUCCESS) {                                           \
            fprintf(stderr, "ACL error %d at %s:%d: %s\n",                    \
                    __ret, __FILE__, __LINE__, #x);                           \
            return -1;                                                        \
        }                                                                     \
    } while (0)

#define CHECK_ACLNN(x)                                                        \
    do {                                                                      \
        aclnnStatus __ret = (x);                                              \
        if (__ret != OK) {                                                    \
            fprintf(stderr, "ACLNN error %d at %s:%d: %s\n",                  \
                    __ret, __FILE__, __LINE__, #x);                           \
            return -1;                                                        \
        }                                                                     \
    } while (0)

namespace {

// 按 dtype 取元素字节数：fp32=4；fp16/bf16=2（无 aclBFloat16 类型，bf16 仅按
// ACL_BF16 枚举 + 按字节分配即可）。
size_t ElemSize(aclDataType dtype)
{
    return (dtype == ACL_FLOAT) ? 4 : 2;
}

// 最小调用通路冒烟用例：两段式 aclnn 调用全链返回 OK 即 PASS。
int RunSmokeCase(const char* caseName, aclDataType dtype)
{
    constexpr int64_t kB = 4;
    constexpr int64_t kH = 8;

    const int64_t gradHyDims[2] = {kB, kH};
    const int64_t gradHyStrides[2] = {kH, 1};
    const int64_t storageDims[2] = {kB, 5 * kH};
    const int64_t storageStrides[2] = {5 * kH, 1};
    const int64_t gatesDims[2] = {kB, 3 * kH};
    const int64_t gatesStrides[2] = {3 * kH, 1};
    const int64_t gradHxDims[2] = {kB, kH};
    const int64_t gradHxStrides[2] = {kH, 1};
    const int64_t biasDims[1] = {3 * kH};
    const int64_t biasStrides[1] = {1};

    const size_t elem = ElemSize(dtype);
    const size_t gradHyBytes = static_cast<size_t>(kB * kH) * elem;
    const size_t storageBytes = static_cast<size_t>(kB * 5 * kH) * elem;
    const size_t gatesBytes = static_cast<size_t>(kB * 3 * kH) * elem;
    const size_t gradHxBytes = static_cast<size_t>(kB * kH) * elem;
    const size_t biasBytes = static_cast<size_t>(3 * kH) * elem;

    // --- 设备内存分配（桩阶段不构造/校验数据，清零保持运行确定性） ---
    void* devGradHy = nullptr;
    void* devStorage = nullptr;
    void* devGradInputGates = nullptr;
    void* devGradHiddenGates = nullptr;
    void* devGradHx = nullptr;
    void* devGradInputBias = nullptr;
    void* devGradHiddenBias = nullptr;
    CHECK_ACL(aclrtMalloc(&devGradHy, gradHyBytes, ACL_MEM_MALLOC_HUGE_FIRST));
    CHECK_ACL(aclrtMalloc(&devStorage, storageBytes, ACL_MEM_MALLOC_HUGE_FIRST));
    CHECK_ACL(aclrtMalloc(&devGradInputGates, gatesBytes, ACL_MEM_MALLOC_HUGE_FIRST));
    CHECK_ACL(aclrtMalloc(&devGradHiddenGates, gatesBytes, ACL_MEM_MALLOC_HUGE_FIRST));
    CHECK_ACL(aclrtMalloc(&devGradHx, gradHxBytes, ACL_MEM_MALLOC_HUGE_FIRST));
    CHECK_ACL(aclrtMalloc(&devGradInputBias, biasBytes, ACL_MEM_MALLOC_HUGE_FIRST));
    CHECK_ACL(aclrtMalloc(&devGradHiddenBias, biasBytes, ACL_MEM_MALLOC_HUGE_FIRST));

    CHECK_ACL(aclrtMemset(devGradHy, gradHyBytes, 0, gradHyBytes));
    CHECK_ACL(aclrtMemset(devStorage, storageBytes, 0, storageBytes));
    CHECK_ACL(aclrtMemset(devGradInputGates, gatesBytes, 0, gatesBytes));
    CHECK_ACL(aclrtMemset(devGradHiddenGates, gatesBytes, 0, gatesBytes));
    CHECK_ACL(aclrtMemset(devGradHx, gradHxBytes, 0, gradHxBytes));
    CHECK_ACL(aclrtMemset(devGradInputBias, biasBytes, 0, biasBytes));
    CHECK_ACL(aclrtMemset(devGradHiddenBias, biasBytes, 0, biasBytes));

    // --- 创建 aclTensor 描述符（2D/1D 连续 ND 布局） ---
    aclTensor* gradHy = aclCreateTensor(gradHyDims, 2, dtype, gradHyStrides, 0,
                                        ACL_FORMAT_ND, gradHyDims, 2, devGradHy);
    aclTensor* storage = aclCreateTensor(storageDims, 2, dtype, storageStrides, 0,
                                         ACL_FORMAT_ND, storageDims, 2, devStorage);
    aclTensor* gradInputGates = aclCreateTensor(gatesDims, 2, dtype, gatesStrides, 0,
                                                ACL_FORMAT_ND, gatesDims, 2, devGradInputGates);
    aclTensor* gradHiddenGates = aclCreateTensor(gatesDims, 2, dtype, gatesStrides, 0,
                                                 ACL_FORMAT_ND, gatesDims, 2, devGradHiddenGates);
    aclTensor* gradHx = aclCreateTensor(gradHxDims, 2, dtype, gradHxStrides, 0,
                                        ACL_FORMAT_ND, gradHxDims, 2, devGradHx);
    aclTensor* gradInputBias = aclCreateTensor(biasDims, 1, dtype, biasStrides, 0,
                                               ACL_FORMAT_ND, biasDims, 1, devGradInputBias);
    aclTensor* gradHiddenBias = aclCreateTensor(biasDims, 1, dtype, biasStrides, 0,
                                                ACL_FORMAT_ND, biasDims, 1, devGradHiddenBias);

    // --- Phase 1: 查询 workspace 大小并获取 executor ---
    // 签名照抄生成头：输入(gradHy, storage) → 属性(bool hasBias) →
    // 输出×5 → workspaceSize → executor。
    uint64_t workspaceSize = 0;
    aclOpExecutor* executor = nullptr;
    CHECK_ACLNN(aclnnThnnFusedGruCellGradGetWorkspaceSize(
        gradHy, storage, true, gradInputGates, gradHiddenGates, gradHx,
        gradInputBias, gradHiddenBias, &workspaceSize, &executor));

    void* workspace = nullptr;
    if (workspaceSize > 0) {
        CHECK_ACL(aclrtMalloc(&workspace, workspaceSize, ACL_MEM_MALLOC_HUGE_FIRST));
    }

    // --- Phase 2: 下发算子并等待完成 ---
    aclrtStream stream = nullptr;
    CHECK_ACL(aclrtCreateStream(&stream));

    CHECK_ACLNN(aclnnThnnFusedGruCellGrad(workspace, workspaceSize, executor, stream));
    CHECK_ACL(aclrtSynchronizeStream(stream));

    fprintf(stdout, "[smoke] %s PASSED\n", caseName);

    // --- 清理 ---
    if (workspace != nullptr) {
        aclrtFree(workspace);
    }
    aclrtDestroyStream(stream);
    aclDestroyTensor(gradHy);
    aclDestroyTensor(storage);
    aclDestroyTensor(gradInputGates);
    aclDestroyTensor(gradHiddenGates);
    aclDestroyTensor(gradHx);
    aclDestroyTensor(gradInputBias);
    aclDestroyTensor(gradHiddenBias);
    aclrtFree(devGradHy);
    aclrtFree(devStorage);
    aclrtFree(devGradInputGates);
    aclrtFree(devGradHiddenGates);
    aclrtFree(devGradHx);
    aclrtFree(devGradInputBias);
    aclrtFree(devGradHiddenBias);
    return 0;
}

} // namespace

int main()
{
    CHECK_ACL(aclInit(nullptr));
    CHECK_ACL(aclrtSetDevice(0));

    int failed = 0;
    // dtype 覆盖 = 算子原型 dtype 组合表的三行（fp32 / fp16 / bf16）。
    if (RunSmokeCase("thnn_fused_gru_cell_grad fp32", ACL_FLOAT) != 0) {
        failed++;
    }
    if (RunSmokeCase("thnn_fused_gru_cell_grad fp16", ACL_FLOAT16) != 0) {
        failed++;
    }
    if (RunSmokeCase("thnn_fused_gru_cell_grad bf16", ACL_BF16) != 0) {
        failed++;
    }

    fprintf(stdout, "\n==== ThnnFusedGruCellGrad aclnn smoke summary: %d/3 cases PASSED ====\n",
            3 - failed);

    CHECK_ACL(aclrtResetDevice(0));
    CHECK_ACL(aclFinalize());
    return (failed == 0) ? 0 : -1;
}
```

## 预防

- 写 aclnn 测试前固定先 `cat build/autogen/aclnn_<op>.h`，参数顺序/命名逐字照抄。
- 测试文件写完先做廉价自检（异常词 grep、花括号平衡、`int main` 存在）再编译——长文件一次写入可能损坏。
- 测试用例数与 OpDef `DataType({...})` 列表长度、kernel `.o` 数三方对账。

## 验证信号

以下信号来自同一次"样例重建为接口桩"会话：按生成头签名写冒烟测试后，独立预构建与官方 run.sh 两条路径均通过。

- 独立预构建：`TEST_BUILD_EXIT=0`，`fp32/fp16/bf16` 3/3 PASSED，`TEST_RUN_EXIT=0`（来源平台：950；证据等级：tool_observed）。
- 官方 `tests/aclnn/run.sh`：`RUN_EXIT=0`、`FAILED` 计数 0、3/3 PASSED（来源平台：950；证据等级：tool_observed）。
- `nm -D libcust_opapi.so` 同时导出 `aclnnThnnFusedGruCellGrad` 与 `aclnnThnnFusedGruCellGradGetWorkspaceSize`（来源平台：950；证据等级：tool_observed）。
- `ldd` 测试可执行文件将 `libcust_opapi.so` 解析到本工程 vendor 安装目录；`objdump -T` 存在对 `GetWorkspaceSize` 的 UND 引用（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 本卡只覆盖**调用通路**冒烟，不含数值校验——不能以此证明 kernel 数值正确（数值用例属 kernel 实现阶段验收）。
- zero-size 张量（has_bias=false 的空 bias）、非 ND 格式、`workspaceSize == 0` 时仍传非空 workspace 等边界未测。
- 签名映射规律（属性位置、`Out` 后缀）由本例单个 OPTIONAL Bool 属性归纳；ListAttr/必选属性/多属性形态未验证。
- 生成头路径与内容随 CANN 版本演进——以当次构建产物为准（推断规律可迁移，未验证）。

## 坏实践

- 凭记忆或别家算子的例子拼 aclnn 签名（属性位置/输出 `Out` 后缀最易错位）——应读当次生成头。
- 长测试文件一次写完不回读自检——当次会话首写即在文件中段混入垃圾片段且尾部缺失，靠回读检查（异常词 grep、花括号平衡）才发现后整文件重写。
- 把"冒烟 3/3 PASSED"当数值正确性证据——通路与数值是两个验收维度。

## 误诊

- 曾担心生成 stub 里有 dtype/format/attr 的隐藏校验导致调用失败——展开生成 `.cpp` 确认是标准 Nnopbase 通路：张量描述透传 + bool 属性 `NnopbaseAddAttrWithDtype` 直传，无额外校验（agent 分析 + 生成码 grep 佐证）。

## 未决事项

- 无优先项。可接续：kernel 实现阶段的数值用例（host golden 构造 + 逐元素比对 + 多 shape 矩阵）与 `has_bias=false` 空 bias 分支用例。
