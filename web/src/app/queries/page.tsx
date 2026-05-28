"use client";

import { useState } from "react";
import {
  Card,
  Input,
  Button,
  Select,
  Space,
  Switch,
  Typography,
  Spin,
  Collapse,
  Tag,
  Divider,
} from "antd";
import { SendOutlined, LinkOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { listKnowledgeBases } from "@/services/api/knowledge-bases";
import { submitQuery } from "@/services/api/queries";
import type { QueryResponse, SourceResponse } from "@/types/api";

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

export default function QueriesPage() {
  const [selectedKbId, setSelectedKbId] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [temperature, setTemperature] = useState(0.2);
  const [rerankEnabled, setRerankEnabled] = useState(false);
  const [hybridSearch, setHybridSearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);

  const { data: kbList } = useQuery({
    queryKey: ["knowledge-bases", "dropdown"],
    queryFn: () => listKnowledgeBases(1, 100),
  });

  const kbOptions =
    kbList?.data?.items.map((kb) => ({
      value: kb.id,
      label: kb.name,
    })) ?? [];

  const handleSubmit = async () => {
    if (!selectedKbId || !question.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await submitQuery({
        knowledge_base_id: selectedKbId,
        question: question.trim(),
        top_k: topK,
        temperature,
        rerank_enabled: rerankEnabled,
        hybrid_search: hybridSearch,
      });
      if (res.error) {
        setResult(null);
        setResult({
          query_id: "",
          answer: `错误: ${res.error.message}`,
          sources: [],
          usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
          latency_ms: 0,
          cache_hit: false,
        });
      } else if (res.data) {
        setResult(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="智能问答" style={{ maxWidth: 900, margin: "0 auto" }}>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Space wrap>
          <Select
            placeholder="选择知识库"
            style={{ width: 250 }}
            options={kbOptions}
            value={selectedKbId || undefined}
            onChange={(id) => setSelectedKbId(id)}
          />
          <Space>
            <Text>Top-K:</Text>
            <Select
              value={topK}
              style={{ width: 70 }}
              options={[3, 5, 10, 20].map((v) => ({ value: v, label: v }))}
              onChange={setTopK}
            />
          </Space>
          <Space>
            <Text>温度:</Text>
            <Select
              value={temperature}
              style={{ width: 80 }}
              options={[0, 0.1, 0.2, 0.5, 1.0].map((v) => ({
                value: v,
                label: v,
              }))}
              onChange={setTemperature}
            />
          </Space>
          <Space>
            <Text>重排:</Text>
            <Switch
              size="small"
              checked={rerankEnabled}
              onChange={setRerankEnabled}
            />
          </Space>
          <Space>
            <Text>混合检索:</Text>
            <Switch
              size="small"
              checked={hybridSearch}
              onChange={setHybridSearch}
            />
          </Space>
        </Space>

        <TextArea
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="输入你的问题..."
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />

        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSubmit}
          loading={loading}
          disabled={!selectedKbId || !question.trim()}
          block
        >
          提问
        </Button>

        {result && (
          <>
            <Divider />
            <Spin spinning={loading}>
              <Card size="small" title="回答" style={{ background: "#fafafa" }}>
                <Paragraph
                  style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}
                >
                  {result.answer}
                </Paragraph>
              </Card>

              <div style={{ marginTop: 12 }}>
                <Space>
                  <Tag>延迟: {result.latency_ms}ms</Tag>
                  {result.usage.total_tokens > 0 && (
                    <Tag>Token: {result.usage.total_tokens}</Tag>
                  )}
                  {result.cache_hit && <Tag color="green">缓存命中</Tag>}
                </Space>
              </div>

              {result.sources.length > 0 && (
                <Collapse
                  style={{ marginTop: 12 }}
                  items={[
                    {
                      key: "sources",
                      label: (
                        <Space>
                          <LinkOutlined />
                          来源引用 ({result.sources.length})
                        </Space>
                      ),
                      children: (
                        <div>
                          {result.sources.map((s: SourceResponse) => (
                            <Card
                              key={s.source_id}
                              size="small"
                              style={{ marginBottom: 8 }}
                            >
                              <div style={{ marginBottom: 4 }}>
                                <Tag color="blue">{s.filename}</Tag>
                                <Tag>相关度: {s.score.toFixed(4)}</Tag>
                              </div>
                              <Paragraph
                                ellipsis={{ rows: 3, expandable: true }}
                                style={{
                                  fontSize: 12,
                                  color: "#666",
                                  marginBottom: 0,
                                }}
                              >
                                {s.content}
                              </Paragraph>
                            </Card>
                          ))}
                        </div>
                      ),
                    },
                  ]}
                />
              )}
            </Spin>
          </>
        )}
      </Space>
    </Card>
  );
}
