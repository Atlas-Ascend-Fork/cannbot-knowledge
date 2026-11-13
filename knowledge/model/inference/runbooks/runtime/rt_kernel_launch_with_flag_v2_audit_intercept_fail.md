---
{
  "type": "Runbook",
  "title": "rtKernelLaunchWithFlagV2 审计 hook 的失败签名与未验证转发方案",
  "description": "来源尝试用 dlsym(RTLD_NEXT) hook V2 launch 并转发 cfg；展示的原始补丁第七参数缺 const，与该 SDK 声明不一致，不能直接采用。签名修订、审计覆盖和 cfg 转发等价性均未取得运行验证。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# rtKernelLaunchWithFlagV2 审计 hook 的失败签名与未验证转发方案


## 适用场景

用 LD_PRELOAD 审计桥拦截 kernel launch API，以证明复现运行使用了自然 tiling/cfg 的 NPU 复现工程；或任何需要 hook runtime launch 接口做取证的工作。

## 触发与观测

> （证据 ）：

> 尝试：在 launch_audit.cpp 增加 extern "C" rtKernelLaunchWithFlagV2 拦截——level==0 且 cfgReady 时转发 originalCfg（rtTaskCfgInfo_t.schemMode，等价原 aclnn 派发路径），否则透传调用方 cfg，并记录 Audit 条目。


## 探针与操作

对生成的 hoststub 二进制做反汇编，检索 rtKernelLaunch*@plt 调用点与 cfg 参数分支：`<<<b,nullptr,s>>>` 形式会走 cfg=NULL 分支直调 rtKernelLaunchWithFlagV2(stub, blocks, args, NULL, stream, 0, NULL)；对照审计桥实际 hook 的 API 名单（rtKernelLaunch/rtKernelLaunchWithFlag），确认拦截面缺口。

## 机制与判别

补丁在审计桥中增加 extern "C" rtKernelLaunchWithFlagV2 定义：dlsym(RTLD_NEXT) 取真函数，level==0 且已注册 host tiling cfg 时转发 originalCfg（rtTaskCfgInfo_t.schemMode，等价原 aclnn 派发路径），否则透传调用方 cfg，并写 Audit 记录。关键签名约束：第 7 参必须与 SDK 头文件一致为 const rtTaskCfgInfo_t*。

**失败版本，禁止按此直接应用：下列第七参数不是 const，与所用 SDK 头文件不一致。这里保留原始尝试用于解释失败；不是已验证修复。**

原始机制片段：（锚 ，服务于来源结论）：

```
 rc=forwarded?(v2?v2(stub,blocks,args,sm,stream,flags,&originalCfg):static_cast<rtError_t>(-1)):(fn?fn(stub,blocks,args,sm,stream,flags):static_cast<rtError_t>(-1));--depth;Audit("rtKernelLaunchWithFlag",stub,blocks,args?args->args:nullptr,args?args->argsSize:0,rc,level,forwarded);return rc;
}
// The cce hoststub generated for <<<blocks,nullptr,stream>>> calls rtKernelLaunchWithFlagV2
// directly with cfg=NULL (verified by disassembly of AscendKernelLaunchWithFlagV2), so the two
// hooks above never fire and no launch-audit record was produced. Intercept V2 as well and,
// when the host tiling schedule mode was registered via moe_set_original_schedule_mode, forward
// originalCfg (rtTaskCfgInfo_t.schemMode) exactly as the original aclnn dispatch path does;
// otherwise pass the caller-supplied cfg through unchanged.
extern "C" rtError_t rtKernelLaunchWithFlagV2(const void* stub,uint32_t blocks,rtArgsEx_t* args,rtSmDesc_t* sm,rtStream_t stream,uint32_t flags,rtTaskCfgInfo_t* cfg) {
 using Fn=rtError_t(*)(const void*,uint32_t,rtArgsEx_t*,rtSmDesc_t*,rtStream_t,uint32_t,rtTaskCfgInfo_t*);
 auto fn=reinterpret_cast<Fn>(dlsym(RTLD_NEXT,"rtKernelLaunchWithFlagV2"));unsigned level=depth++;bool forwarded=level==0&&cfgReady;
 rtError_t rc=fn?fn(stub,blocks,args,sm,stream,flags,forwarded?&originalCfg:cfg):static_cast<rtError_t>(-1);
 --depth;Audit("rtKernelLaunchWithFlagV2",stub,blocks,args?args->args:nullptr,args?args->argsSize:0,rc,level,forwarded);return rc;
}
```

## 验证信号


来源工具仅报告 launch_audit.cpp 的一次 Edit 已落盘。所示第七参数为非 const，和本卡核对的 SDK 声明不一致；没有对应修订后的构建、实际拦截记录或设备等价性结果。不能把 Edit 成功视为 hook 生效。

## 适用与失效边界

适用：hoststub 由 cce 生成、可能直调 V2 launch API 的场景。失效/边界：extern "C" 拦截函数的签名必须与 SDK 头文件逐参数一致（含 const），否则编译期即冲突；拦截补丁的实际效果（audit 产出、cfg 转发等价性）在本轨迹内未验证，引用时须注明。
