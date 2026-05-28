"use client";

import { ReactNode, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, Layout, Menu, theme } from "antd";
import {
  DatabaseOutlined,
  FileAddOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import { useRouter, usePathname } from "next/navigation";
import zhCN from "antd/locale/zh_CN";

const { Sider, Content, Header } = Layout;

function AppLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const { token } = theme.useToken();

  const menuItems = [
    {
      key: "/knowledge-bases",
      icon: <DatabaseOutlined />,
      label: "知识库",
    },
    {
      key: "/documents",
      icon: <FileAddOutlined />,
      label: "文档管理",
    },
    {
      key: "/queries",
      icon: <MessageOutlined />,
      label: "智能问答",
    },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        style={{ borderRight: `1px solid ${token.colorBorderSecondary}` }}
      >
        <div
          style={{
            height: 48,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            fontSize: collapsed ? 14 : 16,
            color: token.colorPrimary,
          }}
        >
          {collapsed ? "RG" : "RAG-Py"}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          onClick={({ key }) => router.push(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: token.colorBgContainer,
            padding: "0 24px",
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            display: "flex",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 16, fontWeight: 600 }}>RAG 智能问答平台</span>
        </Header>
        <Content style={{ padding: 24, background: token.colorBgLayout }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 1, staleTime: 30_000 },
        },
      }),
  );

  return (
    <html lang="zh-CN">
      <body style={{ margin: 0 }}>
        <ConfigProvider theme={{ token: { colorPrimary: "#1677ff" } }} locale={zhCN}>
          <QueryClientProvider client={queryClient}>
            <AppLayout>{children}</AppLayout>
          </QueryClientProvider>
        </ConfigProvider>
      </body>
    </html>
  );
}
