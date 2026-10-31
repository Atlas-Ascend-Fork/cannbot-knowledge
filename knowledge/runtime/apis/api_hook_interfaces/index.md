# Runtime API Hook 接口

CANN Runtime API Hook 接口：支持性能分析工具通过注入 Hook 函数的方式拦截 Runtime 接口调用，用于 Profiling 等场景。

- [aclrtApiInjectionSetFunc](aclrt_api_injection_set_func.md)：将 Runtime 接口实现指针设置为指定的 Hook 函数。
- [aclrtApiInjectionGetFunc](aclrt_api_injection_get_func.md)：获取 Runtime 接口的原始与当前函数指针。
