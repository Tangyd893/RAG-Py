# P0-4: RAG 查询链路

## 目标

实现完整 RAG 查询流水线：问题理解 → 向量检索 → Prompt 构建 → LLM 生成 → 结果持久化，返回带来源引用的回答。

## 需求

### R1: 查询接口

- `POST /api/v1/queries` — 知识库问答
  - 请求：knowledge_base_id、question、top_k（可选，默认 5）、temperature（可选，默认 0.2）
  - 响应：query_id、answer、sources（含 document_id/chunk_id/filename/score/content）、usage（token）、latency_ms、cache_hit

### R2: 检索服务（RetrievalService）

- 将用户问题转为 query embedding（BGE）
- 在指定 KB 的 Chroma collection 中检索 top_k * 3 个片段
- 按 score 过滤低分结果（score_threshold > 0）
- 返回前 top_k 个片段作为上下文

### R3: Prompt 构建器（PromptBuilder）

- 系统提示词：约束模型仅基于上下文回答
- 上下文格式：`[N] 文件：{filename}，片段：{content}`
- 回答中引用来源编号 [1]、[2]
- 上下文不足时明确说明"根据当前知识库资料无法确定"

### R4: LLM 生成服务

- 调用 MiMo LLM（配置驱动）
- 支持 system + user messages 格式
- 记录 token 用量（prompt_tokens、completion_tokens）
- 超时处理：60 秒超时

### R5: 结果持久化

- 查询完成后写入 query_logs 表（含 token 用量、延迟、状态）
- 写入 query_sources 表（含 rank、score、content、chunk_id）
- 流式接口留 P0-4 占位，后续实现

### R6: 空结果处理

- 检索无结果时：不调用 LLM，直接返回"当前知识库没有可用资料"
- LLM 回答"无法确定"时：保留该回答和 sources

## 约束

- Prompt 不暴露系统内部指令或配置
- 用户文档内容仅作为上下文，不作为系统指令
- LLM provider 调用通过抽象接口，不硬编码 MiMo
- 使用已有 ChromaVectorStore.query() 方法
- 使用已有 BgeEmbeddingProvider.embed_query() 方法

## 验收标准

- [ ] `POST /api/v1/queries` 对已索引 KB 可返回带 sources 的回答
- [ ] sources 包含 document_id、filename、score、content
- [ ] response 包含 usage（token 用量）和 latency_ms
- [ ] 空 KB 查询返回"当前知识库没有可用资料"
- [ ] query_logs 和 query_sources 表中可见查询记录
- [ ] 所有错误响应包含 error.code 和 request_id
- [ ] Prompt 正确约束模型仅基于上下文回答

## 文件落点

```
app/schemas/query.py                [新] QueryRequest/QueryResponse/SourceResponse

app/application/services/
├── rag_service.py                  [改] 重写为完整 RAG 编排
├── retrieval_service.py            [新] 向量检索服务
└── prompt_builder.py               [新] Prompt 构建器

app/infrastructure/providers/llm/
├── base.py                         [新] LLMProvider 协议
└── mimo_provider.py                [改] 真实 MiMo API 调用

app/api/v1/routes/queries.py        [新] 查询路由

app/domain/policies.py              [新] Prompt 模板和检索策略常量
```
