# Top .NET Core Interview Cheat Sheet — One-line answers

This cheat-sheet summarizes each question in one line for quick revision.

1. .NET Standard: API specification for library portability across runtimes.
2. .NET Framework: Windows-only legacy .NET runtime.
3. .NET Core: Cross-platform modern .NET runtime (now unified as .NET 5+).
4. `string` vs `String`: alias vs type — identical.
5. Generic Host: hosting abstraction for console/worker apps with DI.
6. Value vs Reference: value types copied; reference types point to heap.
7. IoC/DI Container: manages object creation and injection.
8. MSIL: intermediate bytecode produced by compilers.
9. .NET Standard purpose: portable API contract for libraries.
10. CLR services: GC, JIT, type safety, exception handling, interop.
11. AppDomain: isolation within a process (deprecated in .NET Core).
12. CTS: common type system for language interoperability.
13. CLR: runtime engine for managed code.
14. Unmanaged resource: resources not under GC control (files, handles).
15. decimal vs float vs double: decimal for money, float/double for speed.
16. Boxing/unboxing: value type ↔ object conversions (boxing allocates).
17. .NET Core features: cross-platform, modular, container-friendly.
18. .NET Core vs Mono: different runtimes; .NET recommended for modern use.
19. SDK vs Runtime: SDK builds apps; runtime runs apps.
20. WCF replacement: use ASP.NET Core/gRPC for modern scenarios.
21. Options Pattern: typed config and validation via `IOptions<T>`.
22. Create scope: `IServiceProvider.CreateScope()` for scoped services.
23. DI lifetimes: Singleton, Scoped, Transient — choose per use case.
24. Long-running work: implement `BackgroundService`/`IHostedService`.
25. MVC: controllers, views, model binding in ASP.NET Core.
26. BackgroundService: base class for hosted background tasks.
27. .NET Standard vs PCL: Standard replaced complex PCL profiles.
28. JIT: compiles IL to native at runtime.
29. CLS: language interoperability rules.
30. .NET Core vs Framework vs Xamarin: cross-platform vs Windows vs mobile.
31. Managed vs Unmanaged: CLR-managed vs native code.
32. FCL: Framework Class Library.
33. Kestrel: default cross-platform ASP.NET Core web server.
34. Library targets: netstandard (portable) vs net (runtime-specific).
35. Explicit compilation: AOT/ready-to-run for startup/perf.
36. Multi-exception catch: `catch (A or B ex)` or exception filters.
37. CoreCLR: the .NET runtime implementation for .NET Core/.NET.
38. IDisposable: deterministic cleanup, use `using`.
39. BCL: Base Class Library.
40. AOT benefits: faster startup, fewer JIT costs, larger binaries.
41. Task vs Thread: Task is an abstraction; thread is OS thread.
42. When to use netstandard: when targeting multiple runtimes.
43. Deployment types: framework-dependent vs self-contained.
44. .NET Core includes: runtime, BCL, ASP.NET Core, EF Core, CLI.
45. .NET Core vs Framework: cross-platform modern vs Windows legacy.
46. gRPC vs WCF: gRPC is modern HTTP/2/protobuf RPC.
47. Why .NET Standard: to enable portable libraries.
48. Repo pattern vs EF: often redundant—EF already provides UoW/Repository.
49. Dispose injected services?: No — DI manages disposal.
50. Async/Await: compiler state-machine; await yields the thread for I/O.
51. Roslyn vs RyuJIT: Roslyn compiles source → IL; RyuJIT compiles IL → native.
52. IHost vs IHostBuilder vs IHostedService: build host vs host instance vs hosted background services.
53. When to use each DI lifetime: Transient stateless, Scoped per-request, Singleton shared.
54. HostedService vs Windows Service: hosted abstraction vs OS service.
55. Inheritance types: class (single), interface (multiple), abstract classes.
56. CIL vs MSIL: same thing — the intermediate language.
57. JIT benefits: runtime optimizations and portability.
58. Implicit compilation: build/compile step producing IL (Roslyn).
59. Why JIT?: runtime optimizations and portability; AOT trades some flexibility for startup.
60. AppDomain vs Assembly vs Process vs Thread: isolation, compiled unit, OS instance, execution context.
61. Multiple inheritance: classes no, interfaces yes.
62. Framework/Core vs Standard libs: target-specific vs portable APIs.
63. Choose netstandard version: lowest that supports required runtimes and APIs.
64. Differences: core (modern), portable/PCL (legacy), standard (API contract), compact/UWP (platform-specific).
65. Finalize vs Dispose: Dispose for deterministic cleanup; finalize only as backup.
66. Hosted Services deployment notes: graceful shutdown, scopes, health checks.
67. JIT types: tiered compilation, normal JIT, AOT/precompilation.
68. Node.js async vs .NET async: event loop single-threaded model vs thread-pool + async/await; both enable non-blocking I/O but differ in threading model.

---

If you want a single-file PDF export or a condensed printable cheat-sheet (one-page), I can generate that next.
