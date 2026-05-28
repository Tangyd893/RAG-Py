"use client";

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Card,
  Upload,
  Button,
  Table,
  Tag,
  Space,
  message,
  Select,
} from "antd";
import {
  UploadOutlined,
  ReloadOutlined,
  ArrowLeftOutlined,
} from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listKnowledgeBases } from "@/services/api/knowledge-bases";
import { listDocumentsByKb, uploadDocument } from "@/services/api/documents";
import type { DocumentResponse } from "@/types/api";

const STATUS_COLORS: Record<string, string> = {
  uploaded: "blue",
  parsing: "orange",
  parsing_completed: "cyan",
  chunking: "orange",
  chunking_completed: "cyan",
  embedding: "orange",
  indexed: "green",
  failed: "red",
  deleted: "default",
};

const STATUS_LABELS: Record<string, string> = {
  uploaded: "已上传",
  parsing: "解析中",
  parsing_completed: "解析完成",
  chunking: "分块中",
  chunking_completed: "分块完成",
  embedding: "向量化中",
  indexed: "已索引",
  failed: "失败",
  deleted: "已删除",
};

function DocumentsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialKbId = searchParams.get("kb_id") ?? "";
  const [selectedKbId, setSelectedKbId] = useState(initialKbId);
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data: kbList } = useQuery({
    queryKey: ["knowledge-bases", "dropdown"],
    queryFn: () => listKnowledgeBases(1, 100),
  });

  const { data: docData, isLoading, refetch } = useQuery({
    queryKey: ["documents", selectedKbId, page],
    queryFn: () => listDocumentsByKb(selectedKbId, page, 20),
    enabled: !!selectedKbId,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ kbId, file }: { kbId: string; file: File }) =>
      uploadDocument(kbId, file),
    onSuccess: (res) => {
      if (res.error) {
        message.error(res.error.message);
        return;
      }
      const d = res.data;
      if (d?.duplicate) {
        message.warning("文件已存在，跳过上传");
      } else {
        message.success("上传成功，正在索引中");
      }
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: Error) => message.error(err.message),
  });

  const kbOptions =
    kbList?.data?.items.map((kb) => ({
      value: kb.id,
      label: kb.name,
    })) ?? [];

  const columns = [
    {
      title: "文件名",
      dataIndex: "filename",
      key: "filename",
      ellipsis: true,
    },
    {
      title: "类型",
      dataIndex: "content_type",
      key: "content_type",
      width: 120,
      render: (v: string) => v.split("/").pop() ?? v,
    },
    {
      title: "大小",
      dataIndex: "file_size",
      key: "file_size",
      width: 100,
      render: (v: number) => {
        if (v < 1024) return `${v}B`;
        if (v < 1024 * 1024) return `${(v / 1024).toFixed(1)}KB`;
        return `${(v / (1024 * 1024)).toFixed(1)}MB`;
      },
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (v: string) => (
        <Tag color={STATUS_COLORS[v] ?? "default"}>
          {STATUS_LABELS[v] ?? v}
        </Tag>
      ),
    },
    {
      title: "上传时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (v: string) => new Date(v).toLocaleString("zh-CN"),
    },
  ];

  const items: DocumentResponse[] = docData?.data?.items ?? [];
  const total = docData?.data?.total ?? 0;

  return (
    <Card
      title={
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => router.push("/knowledge-bases")}
            type="text"
          />
          <span>文档管理</span>
        </Space>
      }
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      }
    >
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Space wrap>
          <Select
            placeholder="选择知识库"
            style={{ width: 280 }}
            options={kbOptions}
            value={selectedKbId || undefined}
            onChange={(id) => {
              setSelectedKbId(id);
              setPage(1);
            }}
          />
          {selectedKbId && (
            <Upload
              accept=".txt,.md,.pdf,.docx"
              showUploadList={false}
              beforeUpload={(file) => {
                uploadMutation.mutate({ kbId: selectedKbId, file });
                return false;
              }}
            >
              <Button
                type="primary"
                icon={<UploadOutlined />}
                loading={uploadMutation.isPending}
              >
                上传文档
              </Button>
            </Upload>
          )}
        </Space>

        {selectedKbId && (
          <Table<DocumentResponse>
            rowKey="id"
            columns={columns}
            dataSource={items}
            loading={isLoading || uploadMutation.isPending}
            pagination={{
              current: page,
              pageSize: 20,
              total,
              onChange: (p) => setPage(p),
              showTotal: (t) => `共 ${t} 条`,
            }}
            locale={{ emptyText: "暂无文档，请上传文件" }}
          />
        )}
      </Space>
    </Card>
  );
}

export default function DocumentsPage() {
  return (
    <Suspense fallback={<Card loading />}>
      <DocumentsContent />
    </Suspense>
  );
}
