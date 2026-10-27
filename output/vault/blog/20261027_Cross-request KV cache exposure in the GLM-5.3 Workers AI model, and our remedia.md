---
title: "Cross-request KV cache exposure in the GLM-5.3 Workers AI model, and our remediation with SGLang"
source_url: "https://blog.cloudflare.com/kv-cache-exposure-remediation/"
platform: "Cloudflare Blog (Architecture & Security)"
author: "Kevin Flansburg"
date: 2026-10-27
type: "video-deep-synthesis"
tags:
  - 学习笔记/深度研读
  - 领域/blog
  - 网络协议
  - 边缘计算
  - 底层网络
  - 安全防御
status: "已归档"
---

# 深度研读案：Cross-request KV cache exposure in the GLM-5.3 Workers AI model, and our remediation with SGLang

> **权威来源**：[Kevin Flansburg - Cross-request KV cache exposure in the GLM-5.3 Workers AI model, and our remediation with SGLang](https://blog.cloudflare.com/kv-cache-exposure-remediation/)  
> **发布平台**：Cloudflare Blog (Architecture & Security) | **归档时间**：2026-10-27  
> **核心定位**：大厂工程演进深度剖析与工程落地实战  
> **知识密度**：★★★★★ | **规范标准**：六段式深度学习资料规范 (Mode B)

---

## 目录
1. [一、元数据与技术背景声明](#一元数据与技术背景声明)
2. [二、全景逻辑脉络与时间轴](#二全景逻辑脉络与时间轴)
3. [三、核心机理与架构全景拆解](#三核心机理与架构全景拆解)
4. [四、工业级高危盲区与反模式警示](#四工业级高危盲区与反模式警示)
5. [五、实战落地工程载荷（配置与协议）](#五实战落地工程载荷配置与协议)
6. [六、准出自检清单 (Pre-flight Checklist)](#六准出自检清单-pre-flight-checklist)

---

## 一、元数据与技术背景声明

### 1.1 核心痛点与问题意识
- **背景出处**：来自 **Cloudflare Blog (Architecture & Security)** 发布的专业技术沉淀。
- **直击工程矛盾**：本篇深度解析在实际软件工程或前沿 AI 系统中，如何打破传统设计局限，在性能、可靠性、维护成本与业务需求之间实现高阶平衡。

---

## 二、全景逻辑脉络与时间轴

```mermaid
flowchart TD
    A["一手业务痛点 / 边界挑战"] --> B["核心范式演进与理论突破"]
    B --> C["关键系统架构与时序设计"]
    C --> D["工程落地防坑与可靠性准出"]
```

---

## 三、核心机理与架构全景拆解

### 3.1 系统拓扑与核心交互时序

```mermaid
sequenceDiagram
    autonumber
    participant Caller as 调用端 / 业务源
    participant Orchestrator as 编排引擎 / 控制平面
    participant ExecutionCore as 核心处理核心 / 模型沙箱
    participant StateStore as 持久化存储 / 审计日志

    Caller->>Orchestrator: 提交标准化任务请求 (带链路 TraceID)
    Orchestrator->>ExecutionCore: 任务调度与上下文注入
    ExecutionCore->>ExecutionCore: 执行核心算法逻辑 / 多阶段状态迁移
    ExecutionCore->>StateStore: 原子状态落盘与快照持久化
    StateStore-->>Orchestrator: 回执确认
    Orchestrator-->>Caller: 交付结构化产物 / 异步完成信号
```

### 3.2 核心技术要点精要提炼

- **深度要点 1**：On September 8, 2026, we were alerted by a security researcher, Gadi Evron from Knostic, to a tenant isolation issue affecting the GLM-5.3 Workers AI model (` @cf/zai-org/glm-5.3` ) starting on August 27, 2026. We have remediated the issue, and we restored the model on September 9. We have confirmed that no other model hosted on Workers AI was affected.
- **深度要点 2**：Between August 27 and September 9, a small number of customers using the GLM 5.3 Workers AI model received responses that contained data from other customers' requests made to the same model shortly before theirs. In total, 155 responses were affected, all to prompts longer than 681,280 tokens.
- **深度要点 3**：After excluding our own testing and the researcher's, the requests we identified are consistent in timing and volume with ordinary long-context use, not with someone repeatedly exploiting the bug. We found no evidence of deliberate exploitation.
- **深度要点 4**：Today we are publishing this report alongside a post from SGLang, the open-source inference engine that we use, as a coordinated disclosure. This post describes the bug that caused this issue, our response timeline, and the subsequent hardening we have conducted on our production SGLang deployments. We also detail our continued efforts with the upstream maintainers of SGLang to address this and similar bugs.
- **深度要点 5**：GLM is a text generation model from Z.ai that is built for agentic coding workflows; it is one of the many models available through Workers AI. Gadi Evron submitted a report on September 8 through our HackerOne program stating that very long prompts sent to` @cf/zai-org/glm-5.3` on Workers AI sometimes returned text that belonged to other users' sessions. Cloudflare reproduced the issue the next morning and took the model offline within 40 minutes of declaring an incident. We then deployed a corrected configuration and a patched inference engine, and restored service the same day.
- **深度要点 6**：This specific report of cross-request KV cache exposure was the result of two overlapping issues. The first was a misconfiguration of the open-source inference engine, SGLang, used by Cloudflare. We deployed GLM 5.3 with a 1,048,576-token context window, but the KV cache pool on our prefill GPUs only had room for 681,280 tokens. We were aware of this mismatch before launch. We expected the engine to return an error for any prompt it could not process, and our long-context tests returned successful responses, so we did not believe this to be an issue.

---

## 四、工业级高危盲区与反模式警示

> [!WARNING]
> 生产环境落地中极易忽略的隐性异常边界与高危反模式：

1. **盲区一：状态漂移与不一致性风险**
   - *现象*：高并发或异常网络中断时，由于缺乏严格的原子事务保障，可能导致本地快照与中心状态发生偏离。
   - *防御*：必须引入严格的单调版本号或基于 CAS 的幂等更新控制机制。
2. **盲区二：资源枯竭与背压穿透**
   - *现象*：上游请求突增时，未受控的深层调用会击穿线程池或内存预算，引发级联雪崩。
   - *防御*：在接入层部署严格的自适应限流、主动背压 (Backpressure) 与熔断兜底。
3. **盲区三：上下文衰减与关键断点丢失**
   - *现象*：长周期异步任务执行中，由于中间日志截断导致关键审计凭证丢失。
   - *防御*：贯穿全链路 TraceID，建立不可篡改的事件审计流水线。

---

## 五、实战落地工程载荷（配置与协议）

```yaml
# Cross-request KV cache exposure in the G 生产环境可靠性编排规范
runtime_spec:
  name: "blog-cloudflare-pipeline"
  version: "v1.0.0"
  resilience:
    circuit_breaker:
      enabled: true
      failure_rate_threshold: 30
      sliding_window_size: 50
    retry_policy:
      max_attempts: 3
      exponential_backoff: true
  telemetry:
    trace_propagation: true
    metrics_interval_seconds: 10
```

---

## 六、准出自检清单 (Pre-flight Checklist)

- [ ] **架构完备性**：核心时序与数据流转是否具备端到端可观测性？
- [ ] **容灾降级**：当依赖的下游服务超时或崩溃时，是否具备明确的兜底策略？
- [ ] **幂等自愈**：重复推送相同任务时，是否能做到零副作用幂等过滤？
- [ ] **安全护栏**：凭证管理是否杜绝明文硬编码，并具备最小权限隔离？
