---
title: "Introducing Clairic, a new System One class of extraction models"
source_url: "https://blog.cloudflare.com/clairic-extraction-model/"
platform: "Cloudflare Blog (Architecture & Security)"
author: "Alex Reneau"
date: 2026-10-20
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

# 深度研读案：Introducing Clairic, a new System One class of extraction models

> **权威来源**：[Alex Reneau - Introducing Clairic, a new System One class of extraction models](https://blog.cloudflare.com/clairic-extraction-model/)  
> **发布平台**：Cloudflare Blog (Architecture & Security) | **归档时间**：2026-10-20  
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

- **深度要点 1**：Today, we're announcing a preview of a new class of System One-style models: extraction models. Our first one, Clairic, is available hosted on Workers AI as` @cf/cloudflare/clairic.` We intend to release the model open-weights soon. Clairic is an extraction model that is able to extract, compute, estimate, and forecast values from unstructured inputs — all at a significantly higher accuracy, faster latency, and cheaper cost than traditional LLMs.
- **深度要点 2**：When System One models were announced by TypeSafe a month ago, it took the industry by storm. As referenced by TypeSafe in their blog and defined by Daniel Kahneman’s book Thinking, Fast and Slow , a System One model should be fast and precise, which contrasts a System Two model that is capable of deliberate reasoning (like LLMs). With this, TypeSafe introduced Jev — a model that is purpose-fit for a specific use case, and priced accessibly given its niche domain. It excelled where LLMs failed, helping users make decisions based on probabilities and well-typed outputs. The introduction of Jev prompted people to start thinking about a new class of models that were not LLMs and how to integrate them into their workflows.
- **深度要点 3**：We were inspired by the concept of System One models and started thinking about other tasks where LLMs are inefficient. There are many structured-output calls going to frontier LLMs today with the same shapes again and again: What's the invoice total? When was this delivered? How many days late is it? What will this repair cost? What will traffic look like over the next 24 hours? None of these have answers you can list out in advance, which is needed for a decision model to give probabilities against. That led us to the class of models we're introducing today: System One extraction models.
- **深度要点 4**：## Introducing System One extraction models
- **深度要点 5**：Until now, every System One model has been a decision model: Jev and Clef take an input state and a list of questions and give probabilities against the inputs and your listed questions. Clairic is the first model in a new class: System One extraction models. It is still fast, typed, and cheap, but it answers with values directly extracted from the input, computed from it, or predicted beyond it.
- **深度要点 6**：Most model tasks ask for one of three kinds of output: a number, a choice from a fixed set, or open-ended text. Clairic handles the first, returning numbers with an 80% range, and also pulls typed values like names, dates and lists out of the input. Clef handles the second: it picks among options and returns a probability for each. LLMs handle the third. We call Clairic and Clef System One models because they answer in a single pass, without reasoning or generating tokens. They charge only for input and typically respond in under a second, while an LLM that reasons through the same step takes several seconds.

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
# Introducing Clairic, a new System One cl 生产环境可靠性编排规范
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
