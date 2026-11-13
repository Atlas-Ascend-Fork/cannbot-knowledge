---
{
  "type": "Runbook",
  "title": "PyPTO DYN_FUNC_DATA slab 耗尽的字段平铺候选与验证边界",
  "description": "来源移除独立 DrcoRootFuncData，把五个字段平铺到 DynFuncData，BuildDynFuncData 直接赋值以取消该对象的单独 slab 分配。已取得 Edit 落盘结果，尚无编译或设备 after；后来保留结构体的另一版重构也未验证。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# PyPTO DYN_FUNC_DATA slab 耗尽的字段平铺候选与验证边界

> 验证层级：源码修改落盘，未取得编译或设备修复后的通过结果

## 适用场景

PyPTO/tilefwk device 侧动态执行框架：合入了 aicore 解依赖（DrcoRootFuncData）commit 后，用例在 BuildDynFuncData/SlabAlloc 路径 abort；或任何『小对象复用大 ObjSize slab cache』导致的池耗尽。适用环境变量 ENABLE_AICORE_RESOLVE=true 的 aicore 解依赖分支调试。

## 触发与观测

触发：最新 aicore 解依赖 commit 下运行 test_sparse_compress_flash_attention.py 报错（原始 aicore 分支正常），device 日志报 SlabAlloc ErrCode F74001/F79001（objsize=32）。

## 探针与操作

1) 在 device debug 日志 grep SlabAlloc/usage/backtrace 定位耗尽池与调用链；2) echo 环境变量确认 ENABLE_AICORE_RESOLVE；3) 对照两个分支的 DynFuncData 结构与 BuildDynFuncData 分配点（device_task_context.cpp 中 SlabAlloc(sizeof(DrcoRootFuncData), DYN_FUNC_DATA)）。

## 机制与判别

修复工件一：

```
struct DevStartArgsBase;
struct DynFuncData {
    uint64_t exprNum;              // static
    __gm__ uint64_t* opAttrs;      // static
    __gm__ int32_t* opAtrrOffsets; // static
    __gm__ uint64_t* exprTbl;      // dyn
    __gm__ DevRawTensorDesc* rawTensorDesc;
    __gm__ uint64_t* rawTensorAddr;
    uint64_t opAttrSize;
    uint64_t rawTensorDescSize;
    uint64_t rawTensorAddrSize;
    uint64_t workspaceAddr;
    uint64_t stackWorkSpaceAddr;
    uint64_t stackWorkSpaceSize;
    __gm__ DevStartArgsBase* startArgs; // should be removed as it is global data
    __gm__ int32_t* predCount;
    __gm__ int32_t* succStaticList;
    __gm__ DevAscendFunctionDuppedStitchNode** succStitchList;
    __gm__ DevAscendFunctionOperationSuccInfo* succInfoList;
    __gm__ int* cceBinaryIndexList;
};
```

修复工件二：

```
        if (devProg_->devArgs.enableAicoreResolve) {
            DevAscendFunction* source = stitchedList[funcIdx].GetSource();
            uint32_t opSize = stitchedList[funcIdx].GetOperationSize();
            uint32_t predCountSize = opSize * sizeof(predcount_t);
            WsAllocation predAlloc = ControlFlowAllocateSlab(devProg_, predCountSize, workspace_->SlabAlloc(predCountSize, WsAicpuSlabMemType::PRED_COUNT));
            predcount_t* aicorePredCount = predAlloc.As<predcount_t>();
            DevMemcpyS(aicorePredCount, predCountSize, &stitchedList[funcIdx].GetOperationCurrPredCount(0), predCountSize);
            dyndata->predCount = reinterpret_cast<int32_t*>(aicorePredCount);
            dyndata->succStaticList = reinterpret_cast<int32_t*>(&source->GetOperationSucc(0));
            dyndata->succStitchList = &stitchedList[funcIdx].DupDataForDynFuncData()->GetStitch(0).Head();
            dyndata->succInfoList = &source->GetOperationSuccInfo(0);
            dyndata->cceBinaryIndexList = source->GetCalleeIndexAddr();
        }
```

判别：修复采用与 aicore 分支一致的方案（见来源结论）；另发现第二个遗漏：初始 ready task 未分发到 perCorePendingQueueArray 会以『卡住』形式出现（与 slab abort 不同源），需一并补齐。

## 验证信号


采用版本对应的工具信号仅为两次 `Edit applied successfully`，证明源码修改落盘，不等于构建或设备运行通过。后续“保留 DrcoRootFuncData 结构体并嵌入 DynFuncData 实例”的相反重构，在记录结束时仍处于编译验证中，不能与本版合并成一个验证闭环。

## 适用与失效边界

适用：tilefwk AICPU device 侧 slab 分配器（WsAicpuSlabMemType）+ aicore 解依赖路径。边界：slab 耗尽之外的其他后续问题（如 AICore exception）不在本卡覆盖范围；后续重构方案仍在编译验证中，结论不在本卡范围。

## 结论与证据边界


- 修复采用与 aicore 分支一致的方案：把 predCount/succStaticList/succStitchList/succInfoList/cceBinaryIndexList 直接内嵌到 DynFuncData（删除独立 DrcoRootFuncData 结构体与 drcoRootFuncData 指针），BuildDynFuncData 直接给 dyndata 字段赋值、不再单独 slabAlloc；共改 4 个文件（aikernel_device_task.h、device_task_context.cpp、dev_encode_program_ctrlflow_cache.cpp、aicore_entry_drco.h），并补上 hl 分支遗漏的首次运行时把 aicQueue/aivQueue 初始 ready task 分发到 perCorePendingQueueArray 的逻辑（否则 AICore 侧 KernelEntryDrco 取不到初始任务死循环超时）。
