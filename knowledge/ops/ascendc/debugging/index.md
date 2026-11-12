# 算子调试

按问题域组织的 Ascend C 算子调试总纲与方法论：编译失败、Host Runtime 故障、多卡通信异常、AI Core Error 与精度偏差五个分域。各分域卡保存分诊流程与判定纪律；单点错误的实战处置见本域 runbooks 的对应 area（compilation、runtime、precision、performance），工具使用契约见工具知识域（knowledge/tools）。

- [编译调试（compile-debug）](compile/index.md)：编译失败诊断流程（首错纪律/原配方验证/版本域五态）与静态预防规则。
- [运行时调试（runtime-debug）](runtime/index.md)：Host Runtime 故障的证据纪律与错误码分流、Event/MemcpyAsync/资源生命周期专题实测边界。
