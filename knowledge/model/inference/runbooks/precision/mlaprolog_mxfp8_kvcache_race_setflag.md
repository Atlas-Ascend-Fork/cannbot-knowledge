---
{
  "type": "Runbook",
  "title": "MlaProlog 偶发输出误差：同步点与 flag 生命周期的静态检查",
  "description": "保留设计文档和代码中的同步点检查方法；用户报告加 SyncAll 后症状消失，但现有材料不足以裁定根因或证明 SetFlag、PipeBarrier 的完成语义。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# MlaProlog 偶发输出误差：同步点与 flag 生命周期的静态检查

## 适用场景

MlaProlog mxfp8 pertensor/pertile 的 AIC/AIV 协作路径。具体版本和平台型号未确认；需要在实际分核与数据依赖上审查同步。

## 触发与观测

用户报告 kvcache/krcache 同时偶发误差，加入 SyncAll 后症状消失。该症状来自用户陈述，不是本记录内的设备对照输出。

## 探针与操作

按设计文档列出生产者、消费者、分核维度和同步点，再检查 flag 的声明、set/wait 配对与复用生命周期。以下为原始设计/源码观测，不能直接当作新增屏障的修复配方。

设计文档/源码同步点观测（数字是读取行号）：

```text
29:a. 将核心的数量用满，防止部分核闲置。
39:2、MatmulCkvKr：将BS合轴，作为M轴，HeadSizeCkvKr为N轴，HeadSizeX为K轴，核间对HeadSizeCkvKr进行切分，分为64块
43:4、MatmulQn：将BS合轴，作为M轴，HeadSizeCkv为N轴，dimHeadSizeQc为K轴
54:1、MatmulCq计算的时候，对Hcq进行了分核，单核没有计算一个完整的token，所以在RmsNormCq计算前，
55:需要做AIC与AIV之间的同步控制（SYNC_MMCQ_NOMRCQ）
57:2、MatmulCkvKr计算的时候，也是对Hcq进行了分核，单核没有计算一个完整的token，所以在RmsNormCkv计算前，也
58:需要做AIC与AIV之间的同步控制（SYNC_MMCKVKR_NOMRCKV）
60:3、由于RmsNormCq按照行切分到不同核上，因此在做MatmulQcQr计算的时候，也需要AIV与AIC的同步控制（SYNC_NOMRCQ_MMQCQR）
62:4、由于和RopeQr的分核策略不同，因此RopeQr计算前，也需要AIC和AIV之间的同步控制（SYNC_MMQCQR_ROPEQR）
64:5、由于MatmulQcQr和MatmulQn的分核策略不同，MatmulQn依赖于MatmulQcQr的输出，因此需要做cube的全核同步（SYNC_ALL_CUBE）
66:6、Vector核运算前，需要做vector的全核同步（SYNC_ALL_VECTOR），确保数据流水搬运
94:            CrossCoreSetFlag<0x2, PIPE_FIX>(SYNC_MMCQ_NORMSCQ_FLG);      //cube与vector同步
96:            MatmulCkvKr(tokenXOffset, weightDkvKrOffset, ckvKrResOffset);
97:            CrossCoreSetFlag<0x2, PIPE_FIX>(SYNC_MMCKVKR_NORMROPE_FLG);   //cube与vector同步
99:            CrossCoreWaitFlag(SYNC_MMCQ_NORMSCQ_FLG);                    // MatmulQcQr依赖RmsNormCq的输出，需要插入CV核间同步
102:            CrossCoreSetFlag<0x2, PIPE_FIX>(SYNC_MMQCQR_ROPEQR_FLG);  //cube与vector同步
105:            // 由于MatmulQn和MatmulQcQr的分核策略不一样，MatmulQn又依赖MatmulQcQr的输出
107:            CrossCoreSetFlag<0x0, PIPE_FIX>(SYNC_ALL_CUBE_FLG);
108:            CrossCoreWaitFlag(SYNC_ALL_CUBE_FLG);
118:      CrossCoreWaitFlag(SYNC_MMCQ_NORMSCQ_FLG);        // wait MatmulCq
120:      CrossCoreSetFlag<0x0, PIPE_MTE3>(SYNC_ALL_VECTOR_FLG);
121:      CrossCoreWaitFlag(SYNC_ALL_VECTOR_FLG);
125:      // 由于RmsNormCq和MatmulQcQr的分核策略不一样，需要等所有vector上的RmsNormCq执行完成后才能启动MatmulQcQr
127:      CrossCoreSetFlag<0x0, PIPE_MTE3>(SYNC_ALL_VECTOR_FLG);
128:      CrossCoreWaitFlag(SYNC_ALL_VECTOR_FLG);
130:      CrossCoreSetFlag<0x2, PIPE_MTE3>(SYNC_MMCQ_NORMSCQ_FLG);    // 保障MatmulQcQr等RmsNormCq
133:      CrossCoreWaitFlag(SYNC_MMCKVKR_NORMROPE_FLG);           // wait MatmulCkvKr
135:      CrossCoreSetFlag<0x0, PIPE_MTE3>(SYNC_ALL_VECTOR_FLG);
136:      CrossCoreWaitFlag(SYNC_ALL_VECTOR_FLG);
137:      RmsNormRopeScatterCkvKr(tokenIndex, rmsNormCkvOffset, ropeKrOffset);
139:      CrossCoreWaitFlag(SYNC_MMQCQR_ROPEQR_FLG);        // wait MatmulQcQr
141:      CrossCoreSetFlag<0x0, PIPE_MTE3>(SYNC_ALL_VECTOR_FLG);
142:      CrossCoreWaitFlag(SYNC_ALL_VECTOR_FLG);
194:### MatmulCkvKr
209:### RMSNormCkv
211:对压缩后的$KV$矩阵按行进行RMSNorm（均方根归一化）操作。RMSNorm操作需要传入两个超参$\gamma$和$\epsilon$，对应到接口文档中的$rmsnormGammaCkv$和$rmsnormEpsilonCkv$。
```

## 机制与判别

设计材料显示 MatmulCkvKr 与后续向量阶段的分核方式和同步点需要一起核对。flag 编号复用本身不足以证明竞态；必须结合每次 set/wait 的生命周期和匹配版本接口合同判断。现有 grep 与设计文档不能证明“SetFlag 只提交、不等待完成”，也不能证明增加 PIPE_ALL 就能修复该故障。

## 验证信号

已绑定的客观材料是设计文档的同步点清单及相关实现读取。关于增加 SyncAll 的效果仅为用户报告；没有本记录内重复压测、补屏障后的通过率或完整修复结果。

## 适用与失效边界

同步竞态、flag 生命周期错误和分核依赖均为待区分方向。采用任何屏障修改前须核对平台/版本 API 语义，再做单变量设备对照和重复测试；此卡不承诺具体根因。
