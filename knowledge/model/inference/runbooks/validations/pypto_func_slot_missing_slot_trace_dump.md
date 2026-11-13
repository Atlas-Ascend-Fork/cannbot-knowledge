---
{
  "type": "Runbook",
  "title": "pypto 精度工具 FUNC_SLOT_MISSING 的定位：loop-carried last_state 的 35406→41394 slot 映射缺失，（SLOT_TRACE） 埋点 + TensorGraph JSON dump 三重印证",
  "description": "qwen3_next_gated_delta_rule.py 触发精度工具层 FUNC_SLOT_MISSING（flow_verifier.cpp:1687 ASSERT）。在 function.h 埋 [SLOT_TRACE] 打印重编 wheel 后，观测到 s_idx 循环首个迭代 incast[0] slot=41394 MISS、其余 8 个输入全部 HIT。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# pypto 精度工具 FUNC_SLOT_MISSING 的定位：loop-carried last_state 的 35406→41394 slot 映射缺失，（SLOT_TRACE） 埋点 + TensorGraph JSON dump 三重印证


## 适用场景

qwen3_next_gated_delta_rule.py 触发精度工具层 FUNC_SLOT_MISSING（flow_verifier.cpp:1687 ASSERT）。在 function.h 埋 [SLOT_TRACE] 打印重编 wheel 后，观测到 s_idx 循环首个迭代 incast[0] slot=41394 MISS、其余 8 个输入全部 HIT。通过 TensorGraph JSON dump 的 incast/outcast 顺序、rawshape 与源码对照，三重印证（shape [128,128] 匹配、loop-carried 模式 incast[0]/outcast[11] 同槽、outcast 位置紧跟 core_attn_out/last_state_data）确认 41394 即 last_state：其数据来源是初始输入 states（35399）经 nv_idx 函数产出 outcast slot 35406，而 slotDataViewDict_ 只注册 35406、未建立 35406→41394 映射，首个迭代读取 41394 即触发断言。中途主动纠正过一次未加证明的符号推断。

## 触发与观测

触发：ASSERT FAILED ErrCode FB100E FUNC_SLOT_MISSING（flow_verifier.cpp:1687）。探针：grep slotDataViewDict_/FUNC_SLOT_MISSING → 埋 [SLOT_TRACE] 打印并重编 wheel → 重跑采集 hiddenfunc 命中表 → python 解析 TensorGraph JSON 的 incast/outcast slot、tensor magic、rawtensors symbol/shape。观测：incast[0] slot=41394 MISS；nv_idx hiddenfunc incast [35399]/outcast [35406]；s_idx PATH1 incast[0]/outcast[11] 同为 41394、[128,128]。

## 探针与操作

关键探针与修复操作。证据角色覆盖：trigger, probe, observation, discrimination。

## 机制与判别


> 执行 models/qwen3_next/qwen3_next_gated_delta_rule.py 触发 pypto 精度工具层断言：ASSERT FAILED: ErrCode: FB100E! Enum: ControlFlowScene::FUNC_SLOT_MISSING, func ExecuteControlFlow, file flow_verifier.cpp, line 1687（libtile_fwk_interface.so FunctionInterpreter::ExecuteControlFlow 调用栈）。


> 在 framework/src/interface/interpreter 的 incast 处理处埋 [SLOT_TRACE] 打印并重编重装 wheel（pip install pypto-0.2.1 --force-reinstall --target build_out/）后，s_idx 循环 hiddenfunc 首个迭代的输入显示 incast[0] slot=41394 symbol=INCAST_SYMBOL0 (MISS)，其余 8 个输入（eye/query/key/gate/beta/tril_mask/value/mask）全部 HIT，断言随 FAIL 在同一位置抛出。


> 根因判定（三重印证 + 一次主动纠错）：incast slot 41394 是源码 s_idx 循环的 loop-carried 变量 last_state——①shape [128,128] 与 states[b_idx, nv_idx] 从 [-1,4,128,128] 的切片一致；②slot 41394 同时出现在 incast[0]（首读）与 outcast[11]（partial update），对应源码 last_state[:] = cur_state；③outcast 中 41394 后紧跟 core_attn_out(35404) 与 last_state_data(35405)，与源码三个写回顺序一致。其数据来源是初始输入 states（slot 35399）经 nv_idx hiddenfunc 产出 outcast slot 35406（OUTCAST_SYMBOL0），而精度工具的 slotDataViewDict_ 只注册了 35406、未建立 35406→41394 的映射，首个迭代读取 41394 时触发 FUNC_SLOT_MISSING。此前由编译器生成符号名直接推断 41394 身份的结论曾被主动撤回（不能凭 INCAST_SYMBOL0/OUTCAST_SYMBOL0 通用名认定）。


```
1684:                 ASSERT(ControlFlowScene::FUNC_SLOT_IO_COUNT_MISMATCH, func->GetIncast().size() == incastSlot.size());
1685:                 for (size_t i = 0; i < func->GetIncast().size(); i++) {
1686:                     int slot = incastSlot[i][0];
1687:                     ASSERT(ControlFlowScene::FUNC_SLOT_MISSING, slotDataViewDict_.count(slot));
1688:                     auto incastDataView = slotDataViewDict_[slot];
1689:                     inoutDataPair->incastDataViewList.push_back(incastDataView);
1690:                 }
```

## 验证信号

pypto 精度工具（framework/src/interface/interpreter）在含 loop-carried 变量的嵌套循环 kernel 上触发 ControlFlowScene::FUNC_SLOT_MISSING 的定位。方法：[SLOT_TRACE] 埋点打印 incast/outcast slot 命中情况 + TensorGraph JSON dump 的 incast/outcast 顺序、rawshape 与源码变量对照（shape 匹配/loop-carried 双出/位置匹配三重印证）。


## 适用与失效边界

适用：pypto 精度工具（framework/src/interface/interpreter）在含 loop-carried 变量的嵌套循环 kernel 上触发 ControlFlowScene::FUNC_SLOT_MISSING 的定位。方法：[SLOT_TRACE] 埋点打印 incast/outcast slot 命中情况 + TensorGraph JSON dump 的 incast/outcast 顺序、rawshape 与源码变量对照（shape 匹配/loop-carried 双出/位置匹配三重印证）。失效边界：结论为止损定位（slotDataViewDict_ 缺 35406→41394 映射），轨迹内未实施修复；调测打印代码的清理在轨迹末尾（'黑屏了'）尚未确认完成。
