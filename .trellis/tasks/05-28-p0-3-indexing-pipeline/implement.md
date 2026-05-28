# P0-3 实施计划

按依赖顺序执行，每步完成后验证语法。

---

## Step 1: 基础设施 — 解析器 + 切分器 + 向量存储协议

- [ ] 1.1 创建 `app/infrastructure/parsing/__init__.py`
- [ ] 1.2 创建 `app/infrastructure/parsing/base.py`（DocumentParser 协议）
- [ ] 1.3 创建 `app/infrastructure/parsing/txt_parser.py`（TXT 解析器）
- [ ] 1.4 创建 `app/infrastructure/parsing/md_parser.py`（MD 解析器）
- [ ] 1.5 创建 `app/infrastructure/text_splitter/__init__.py`
- [ ] 1.6 创建 `app/infrastructure/text_splitter/splitter.py`（层级切分器）
- [ ] 1.7 创建 `app/infrastructure/vector_store/__init__.py`
- [ ] 1.8 创建 `app/infrastructure/vector_store/base.py`（VectorStore 协议 + VectorPoint）

**验证**：`python3 -m py_compile` 全部语法通过。

---

## Step 2: Provider 实现

- [ ] 2.1 创建 `app/infrastructure/vector_store/chroma_store.py`（Chroma 适配器）
- [ ] 2.2 修改 `app/infrastructure/providers/embedding/bge_provider.py`（真实 BGE 调用）

**验证**：语法编译通过。

---

## Step 3: IngestionService 编排

- [ ] 3.1 创建 `app/application/services/ingestion_service.py`
  - `index()` — 主编排方法
  - `_cleanup_previous()` — 幂等清理旧数据
  - `_phase_parse()` / `_phase_chunk()` / `_phase_embed()` / `_phase_persist()` / `_phase_finalize()`
  - 每阶段更新 document.status + job.progress
  - 异常处理：标记 failed，可重试异常 raise

**验证**：语法编译通过。

---

## Step 4: Celery 任务

- [ ] 4.1 修改 `app/tasks/celery_app.py`（从 config 读取 broker/backend）
- [ ] 4.2 创建 `app/tasks/indexing.py`（index_document 任务入口）

**验证**：语法编译通过。

---

## Step 5: 上传触发索引

- [ ] 5.1 修改 `app/application/services/document_service.py`
  - upload() 成功后调用 `index_document.delay(str(doc.id))`
  - 创建 IndexingJob 记录

**验证**：语法编译通过。

---

## Step 6: KnowledgeBase 创建时初始化 Chroma collection

- [ ] 6.1 修改 `app/application/services/knowledge_base_service.py`
  - create() 后调用 vector_store.ensure_collection()

**验证**：语法编译通过。全量 app/*.py 语法检查。

---

## 最终验证清单

- [ ] 全部新增/修改文件语法通过
- [ ] 分块器能正确处理中文文本（段落/句子/字符拆分）
- [ ] 向量写入使用稳定 vector_id（`chunk_{chunk.id}`）
- [ ] 重试清理逻辑完整（delete chunks + delete vectors）
- [ ] 文档状态正确流转各阶段
- [ ] 所有注释和文档字符串使用简体中文
