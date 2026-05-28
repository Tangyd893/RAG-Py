"use client";

import { useState } from "react";
import {
  Button,
  Card,
  Table,
  Modal,
  Form,
  Input,
  InputNumber,
  Space,
  Tag,
  message,
} from "antd";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listKnowledgeBases, createKnowledgeBase } from "@/services/api/knowledge-bases";
import type { KBResponse, CreateKBRequest } from "@/types/api";

export default function KnowledgeBasesPage() {
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm<CreateKBRequest>();
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["knowledge-bases", page],
    queryFn: () => listKnowledgeBases(page, 20),
  });

  const createMutation = useMutation({
    mutationFn: createKnowledgeBase,
    onSuccess: (res) => {
      if (res.error) {
        message.error(res.error.message);
        return;
      }
      message.success("知识库创建成功");
      setModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ["knowledge-bases"] });
    },
    onError: (err: Error) => message.error(err.message),
  });

  const columns = [
    {
      title: "名称",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
      render: (v: string | null) => v ?? "-",
    },
    {
      title: "分块大小",
      dataIndex: "chunk_size",
      key: "chunk_size",
      width: 100,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 80,
      render: (v: string) => <Tag color={v === "active" ? "green" : "default"}>{v}</Tag>,
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (v: string) => new Date(v).toLocaleString("zh-CN"),
    },
  ];

  const items: KBResponse[] = data?.data?.items ?? [];
  const total = data?.data?.total ?? 0;

  return (
    <>
      <Card
        title="知识库管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModalOpen(true)}
            >
              新建知识库
            </Button>
          </Space>
        }
      >
        <Table<KBResponse>
          rowKey="id"
          columns={columns}
          dataSource={items}
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: 20,
            total,
            onChange: (p) => setPage(p),
            showTotal: (t) => `共 ${t} 条`,
          }}
          onRow={(record) => ({
            onClick: () => {
              window.location.href = `/documents?kb_id=${record.id}&kb_name=${encodeURIComponent(record.name)}`;
            },
            style: { cursor: "pointer" },
          })}
        />
      </Card>

      <Modal
        title="新建知识库"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => createMutation.mutate(values)}
          initialValues={{ chunk_size: 500, chunk_overlap: 50, retrieval_top_k: 5 }}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: "请输入知识库名称" }]}
          >
            <Input placeholder="输入知识库名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="输入描述（选填）" />
          </Form.Item>
          <Space>
            <Form.Item name="chunk_size" label="分块大小">
              <InputNumber min={200} max={1500} />
            </Form.Item>
            <Form.Item name="chunk_overlap" label="重叠长度">
              <InputNumber min={0} />
            </Form.Item>
            <Form.Item name="retrieval_top_k" label="检索 Top-K">
              <InputNumber min={1} max={50} />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </>
  );
}
