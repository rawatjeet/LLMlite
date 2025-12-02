# Top .NET Core Interview Questions — Answers

This file contains concise, interview-ready answers to the 68 questions in `tools/Top Net Questions.pdf`, with short C# examples where helpful.

---

1. **What is .NET Standard?**

.NET Standard is a specification of APIs that all .NET implementations should implement. Libraries targeting a .NET Standard version run on any runtime that implements that standard, enabling code reuse across .NET Framework, .NET (Core), Mono, Xamarin, and other runtimes.

Example: create a class library targeting `netstandard2.0` for broad compatibility.

```text
dotnet new classlib -f netstandard2.0 -n MyLib
```

---

2. **What is the .NET Framework?**

The .NET Framework is the original Windows-only implementation of .NET providing the CLR and base libraries for desktop and server applications. It's mature but platform-bound; newer development uses cross-platform .NET (formerly .NET Core).

---

3. **What is .NET Core?**

.NET Core (now unified as .NET 5+) is the cross-platform, high-performance, open-source runtime and SDK for building modern applications. It supports side-by-side versions, modular packages, and runs on Windows, Linux, and macOS.

Example:
```bash
dotnet new webapi -n MyApi
cd MyApi
dotnet run
```

---

4. **Difference between `String` and `string` in C#**

`string` is a C# alias for `System.String`. They are identical. Use `string` for the language primitive and `String` when referencing the type explicitly.

```csharp
string s = "hello";
System.String t = s;
```

---

5. **What is Generic Host in .NET Core?**

Generic Host (`Host.CreateDefaultBuilder`) is the hosting abstraction for console and background apps providing DI, configuration, logging, and lifetime management. It is the base for worker services and is used by ASP.NET Core (Web Host is a specialization).

```csharp
var host = Host.CreateDefaultBuilder(args)
    .ConfigureServices(services => services.AddHostedService<MyWorker>())
    .Build();
await host.RunAsync();
```

---

6. **Value types vs Reference types**

- Value types (structs, primitives) are stored on the stack (or inline), copied on assignment, and cannot be null unless `Nullable<T>`.
- Reference types (classes, arrays, delegates) live on the heap; assignment copies a reference. Large structs can be expensive to copy; prefer small structs and immutable patterns.

```csharp
struct Point { public int X, Y; }
class Node { public int Value; }
```

---

7. **What is IoC (DI) Container?**

A DI container (Inversion of Control) manages object creation and dependency wiring. ASP.NET Core includes a built-in container via `IServiceCollection`/`IServiceProvider` supporting constructor injection and lifetimes.

```csharp
services.AddTransient<IMailService, SmtpMailService>();
public class HomeController { public HomeController(IMailService mail) { ... } }
```

---

8. **What is MSIL?**

Microsoft Intermediate Language (MSIL or IL) is the CPU-independent instruction set produced by .NET compilers. The JIT (or AOT toolchain) turns IL into native code at runtime.

---

9. **What is .NET Standard and why do we need it?**

(See Q1) It provides a stable API surface for libraries to run across multiple .NET runtimes, enabling reuse.

---

10. **Name some CLR services**

Memory management (GC), JIT compilation, type safety verification, exception handling, interop services (P/Invoke), threading support, and security enforcement.

---

11. **What is a .NET application domain?**

An AppDomain isolates assemblies within a process. It was used for isolation and unloading in .NET Framework. .NET Core removed most AppDomain features; use separate processes or `AssemblyLoadContext` for isolation and unloading.

---

12. **What is CTS?**

Common Type System — defines how types are declared and used so different languages on .NET interoperate.

---

13. **What is CLR?**

Common Language Runtime — the execution engine providing GC, JIT compilation, type safety, and other runtime services.

---

14. **What is an unmanaged resource in .NET?**

Resources not managed by the GC (file handles, native memory, OS handles). They must be released explicitly (via `Dispose` / finalizer / safe wrappers).

```csharp
using var fs = File.OpenRead(path);
```

---

15. **Difference between `decimal`, `float`, and `double`**

- `float` (32-bit) and `double` (64-bit) are binary floating-point types — fast but subject to rounding errors.
- `decimal` (128-bit) is a decimal floating-point type with high precision for financial calculations but slower.

```csharp
double d = 0.1 + 0.2; // may show rounding artifacts
decimal m = 0.1m + 0.2m; // exact decimal arithmetic
```

---

16. **What is Boxing and Unboxing?**

Boxing: wrapping a value type as an `object` (heap allocation); Unboxing: extracting the value type back. Boxing costs allocations and should be minimized.

```csharp
int x = 42;
object o = x; // boxing
int y = (int)o; // unboxing
```

---

17. **Characteristics of .NET Core**

Cross-platform, modular (NuGet), high-performance, side-by-side runtimes, command-line tooling, container-friendly, and open-source.

---

18. **Difference between .NET Core and Mono**

Mono is an alternate runtime historically used for mobile (Xamarin) and other platforms; .NET Core (now .NET) is Microsoft's modern cross-platform runtime with performance and platform support. Mono remains relevant for specific platforms (Unity, older Xamarin stacks).

---

19. **SDK vs Runtime in .NET Core**

SDK includes compilers and tooling to build apps. Runtime only runs published apps. Install SDK when developing; runtime suffices for production if you ship compiled output.

---

20. **What replaces WCF in .NET Core?**

No direct 1:1 replacement. For HTTP APIs use ASP.NET Core (REST/gRPC). For RPC-style inter-service communication, prefer gRPC. Community projects provide some WCF-like features but full WCF is not ported.

---

21. **Benefits of Options Pattern in ASP.NET Core**

Strongly-typed configuration, easy validation, easier testing, centralization, and support for change notifications with `IOptionsMonitor<T>`.

```csharp
services.Configure<MyOptions>(Configuration.GetSection("MyOptions"));
public class Worker { public Worker(IOptions<MyOptions> opts) { ... } }
```

---

22. **How to create your own Scope for a Scoped object?**

Use `IServiceProvider.CreateScope()` when resolving scoped services outside an HTTP request (e.g., background tasks). Dispose the scope when finished.

```csharp
using (var scope = host.Services.CreateScope()) {
  var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
}
```

---

23. **DI service lifetimes (Singleton, Scoped, Transient)**

- `Singleton`: one instance for app lifetime — thread-safe required.
- `Scoped`: one instance per scope (web request) — good for `DbContext`.
- `Transient`: new instance each resolution — lightweight, stateless.

```csharp
services.AddSingleton<ISvc, Svc>();
services.AddScoped<IRepo, Repo>();
services.AddTransient<ITransform, Transform>();
```

---

24. **Correct pattern for long-running background work**

Implement `BackgroundService` or `IHostedService` and register with `AddHostedService<T>()`. Respect cancellation tokens and avoid blocking on shutdown.

```csharp
public class Worker : BackgroundService {
  protected override async Task ExecuteAsync(CancellationToken stoppingToken) {
    while (!stoppingToken.IsCancellationRequested) {
      await DoWorkAsync(stoppingToken);
    }
  }
}
```

---

25. **What about MVC in .NET Core?**

ASP.NET Core MVC supports model-view-controller pattern, routing, filters, model binding, and Razor views. Use `AddControllersWithViews()` for full MVC.

---

26. **Use of BackgroundService class**

Convenience base class for background tasks implementing `IHostedService`. Implement `ExecuteAsync` and handle cancellation.

---

27. **Difference between .NET Standard and PCL**

PCL used profiles limiting available APIs and was complex. .NET Standard is a standardized API surface across runtimes and replaced PCL as the recommended approach.

---

28. **What is JIT compiler?**

Just-In-Time compiler converts IL to native code at runtime, enabling platform portability and runtime optimizations.

---

29. **Common Language Specification (CLS)**

CLS specifies a set of rules that languages should follow to maintain interoperability (e.g., naming, type usage) across .NET languages.

---

30. **Difference between .NET Core, .NET Framework, and Xamarin**

- .NET Framework: Windows-only. 
- .NET Core/.NET: cross-platform modern runtime. 
- Xamarin: mobile runtime (iOS/Android) — now integrated via .NET MAUI in later .NET versions.

---

31. **Managed vs Unmanaged code**

Managed code runs under CLR with garbage collection and runtime services. Unmanaged code runs directly on the OS (native), requiring explicit resource management. Interop uses P/Invoke or C++/CLI.

---

32. **What is FCL?**

Framework Class Library — the set of standard libraries (System.*) used by .NET.

---

33. **What is Kestrel?**

Kestrel is the high-performance, cross-platform web server for ASP.NET Core used directly or behind a reverse proxy.

---

34. **Class Library (.NET Standard) vs (.NET Core)**

A `netstandard` class library is portable across many runtimes. A `net` (formerly `netcoreapp`) class library targets the .NET runtime and can use newer runtime-specific APIs.

---

35. **What is Explicit Compilation?**

Often refers to AOT or explicitly compiling code ahead of time instead of relying on JIT. It improves startup at the cost of some runtime optimizations.

---

36. **Catch multiple exceptions without duplication**

C# supports combined exception filters:

```csharp
try { ... }
catch (IOException or UnauthorizedAccessException ex) {
  // handle both
}
```

Or use exception filters: `catch (Exception ex) when (ex is ...)`.

---

37. **What is CoreCLR?**

CoreCLR is the runtime implementation used by .NET Core/.NET (the execution engine providing GC, JIT, etc.).

---

38. **Use of `IDisposable`**

Implement `IDisposable` to release unmanaged resources deterministically. Consumers should call `Dispose()` or use `using`/`using var` to ensure disposal.

```csharp
public class MyResource : IDisposable { public void Dispose() { /* cleanup */ } }
using var r = new MyResource();
```

---

39. **What is BCL?**

Base Class Library — core classes (`System.*`) provided by .NET that other libraries use.

---

40. **Benefits of Explicit Compilation (AOT)**

Improved startup and reduced JIT overhead; potentially fewer runtime dependencies. Trade-offs include larger binaries and less dynamic optimization.

---

41. **Difference between Task and Thread**

A `Thread` maps to an OS thread. A `Task` is an abstraction scheduled by the Task Parallel Library; `Task` represents asynchronous work and uses thread pool threads by default.

```csharp
Task.Run(() => Compute());
```

---

42. **When to use .NET Core vs .NET Standard class libraries?**

Use `.NET Standard` for libraries that must run on multiple runtimes. Use `.NET` (net6/net7 etc.) for apps/libraries targeting modern .NET and needing platform-specific APIs.

---

43. **Two deployment types for .NET Core apps**

- Framework-dependent deployment (FDD): smaller, requires runtime installed.
- Self-contained deployment (SCD): includes runtime, larger, runs without installing .NET.

Also single-file publish and AOT options exist.

---

44. **What is included in .NET Core?**

Runtime (CoreCLR), base libraries (BCL), ASP.NET Core, EF Core, CLI tools, and package-based runtime libraries.

---

45. **Difference between .NET Core and .NET Framework**

.NET Core is cross-platform, modular, and modern. .NET Framework is Windows-only and monolithic. .NET (5+) unifies these approaches into a single platform.

---

46. **Difference between gRPC and WCF**

WCF is legacy, Windows-centric with SOAP/RPC features. gRPC is modern, HTTP/2/protobuf-based, cross-platform, and supports streaming; it’s recommended for inter-service RPC.

---

47. **Why does .NET Standard library exist?**

To provide a single API contract that multiple runtimes can implement, ensuring library portability.

---

48. **Why not use Repository Pattern with EF?**

EF Core’s `DbContext` and `DbSet` already implement repository and unit-of-work patterns. Adding an extra repository layer can be redundant unless you need a distinct abstraction for testing or complex mapping.

---

49. **Should I call `Dispose()` on injected services in a Controller?**

No. The DI container manages lifetimes and disposal for services it created. Only dispose services you create manually.

---

50. **How do Async/Await tasks work in .NET?**

`async` methods return `Task`/`Task<T>` and use `await` to pause execution without blocking the thread. The compiler transforms the method into a state machine that resumes when awaited operations complete.

```csharp
public async Task<IActionResult> Get() {
  var json = await httpClient.GetStringAsync(url);
  return Ok(json);
}
```

---

51. **Difference between Roslyn and RyuJIT**

Roslyn is the compiler platform (C#/VB) that produces IL from source. RyuJIT is the runtime JIT compiler that converts IL to native code at execution time.

---

52. **IHost vs IHostBuilder vs IHostedService**

- `IHostBuilder`: builds/configures the host.
- `IHost`: the built host containing DI, logging, and services.
- `IHostedService`: interface for services started/stopped by the host (background services).

---

53. **When to use Transient vs Scoped vs Singleton**

- `Transient`: use for lightweight stateless services created per-operation.
- `Scoped`: use for per-request services (e.g., `DbContext`).
- `Singleton`: use for shared thread-safe resources (e.g., caches, configuration).

---

54. **Hosted Services vs Windows Services**

`IHostedService` is the .NET abstraction for background work. A Windows Service is an OS-level service. You can host a .NET `IHostedService` as a Windows Service using integration libraries.

---

55. **Different types of inheritance**

- Class inheritance (single for classes).
- Interface inheritance (multiple). 
- Abstract classes (partial implementation) vs interfaces (contract only).

---

56. **Difference between CIL and MSIL (IL)**

These terms are synonymous: Common Intermediate Language / Microsoft Intermediate Language — the intermediate bytecode produced by .NET compilers.

---

57. **Benefits of using JIT**

Platform independence, runtime optimizations, smaller deployments, and dynamic features like reflection and code emission.

---

58. **Explain Implicit Compilation process**

MSBuild and `dotnet build` compile source files into IL assemblies automatically during the build step. The process invokes the Roslyn compiler to produce IL, metadata, and assemblies.

---

59. **Why use JIT instead of compiling once on target?**

JIT enables runtime-specific optimizations and portability. AOT can reduce startup time but loses some runtime optimizations and dynamic capabilities.

---

60. **Differences: AppDomain, Assembly, Process, Thread**

- Process: OS-level running instance (memory space).
- Thread: execution context in a process.
- Assembly: compiled unit (DLL/EXE) containing IL and metadata.
- AppDomain: logical isolation within a process (largely deprecated in .NET Core).

---

61. **Does .NET support Multiple Inheritance?**

Classes do not support multiple inheritance. Multiple interfaces can be implemented by a class.

---

62. **Difference between Framework/Core and .NET Standard class library types**

Framework-targeted libraries are Windows-specific; `.NET Standard` libraries are portable across compatible runtimes; `.NET` (net6/net7) libraries target modern runtime features.

---

63. **How to choose the target version of .NET Standard library?**

Pick the lowest `netstandard` version that meets your API needs and is supported by the runtimes you must support. `netstandard2.0` is commonly used for wide compatibility.

---

64. **Difference among .NET Core, Portable, Standard, Compact, UWP, PCL**

- .NET Core/.NET: modern cross-platform runtime.
- Portable/PCL: older portable library profiles.
- .NET Standard: API specification for portability.
- Compact Framework: legacy embedded devices.
- UWP: Universal Windows Platform for Windows store apps.

---

65. **When to use Finalize vs Dispose?**

Use `Dispose` (IDisposable) for deterministic cleanup and `using` to ensure it’s called. Implement finalizer (`~Class`) only as a safety net for unmanaged resources; finalizers add cost — prefer `Dispose`.

---

66. **Deployment considerations for Hosted Services**

Ensure graceful shutdown via cancellation tokens, create DI scopes for scoped services, handle resource limits, add health checks, and configure restart policies in orchestrators.

---

67. **Types of JIT compilations**

Tiered compilation (baseline then optimized), normal JIT, and AOT/precompilation (ready-to-run). Historically: pre-JIT/AOT and eager JIT variants.

---

68. **Difference between Node.js async model and async/await in .NET**

Node.js uses an event loop with non-blocking I/O and a single-threaded model; asynchronous code is typically driven by callbacks/promises. .NET uses `async/await` and the thread pool: awaiting I/O releases the thread to do other work, and continuations resume on threads as scheduled. Both provide non-blocking I/O but differ on threading and runtime models.
