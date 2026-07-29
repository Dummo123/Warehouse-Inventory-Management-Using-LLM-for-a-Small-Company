import React from "react";
import { Layout, Menu, Button, Typography } from "antd";
import {
  DatabaseOutlined, SwapOutlined, AppstoreOutlined,
  ShoppingCartOutlined, RollbackOutlined, ToolOutlined,
  DollarOutlined, TeamOutlined, RobotOutlined,
  LogoutOutlined, FileExcelOutlined, SendOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const { Sider, Content, Header } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: "/stock",      icon: <DatabaseOutlined />,    label: "Остатки" },
  { key: "/movements",  icon: <SwapOutlined />,         label: "Журнал движений" },
  { key: "/articles",   icon: <AppstoreOutlined />,     label: "Артикулы" },
  { key: "/purchases",  icon: <ShoppingCartOutlined />, label: "Закупки" },
  { key: "/production", icon: <ToolOutlined />,         label: "Производство" },
  { key: "/shipments",  icon: <SendOutlined />,         label: "Отгрузки" },
  { key: "/returns",    icon: <RollbackOutlined />,     label: "Возвраты" },
  { key: "/finance",    icon: <DollarOutlined />,       label: "Финансы" },
  { key: "/users",      icon: <TeamOutlined />,         label: "Участники" },
  { key: "/reports",    icon: <FileExcelOutlined />,    label: "Отчёты" },
  { key: "/assistant",  icon: <RobotOutlined />,        label: "ИИ-помощник" },
];

const PAGE_TITLES: Record<string, string> = {
  "/stock": "Остатки на складах", "/movements": "Журнал движений",
  "/articles": "Артикулы и спецификации", "/purchases": "Закупки",
  "/production": "Производство", "/shipments": "Отгрузки",
  "/returns": "Возвраты", "/finance": "Финансы",
  "/users": "Участники", "/reports": "Отчёты", "/assistant": "ИИ-помощник",
};

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signOut } = useAuth();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={210} theme="light"
        style={{ borderRight: "1px solid #f0f0f0", position: "fixed", height: "100vh", overflow: "auto" }}>
        <div style={{ padding: "16px 16px 12px", borderBottom: "1px solid #f0f0f0" }}>
          <Text strong style={{ fontSize: 15 }}>WIM</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 11 }}>SmartTherm</Text>
        </div>
        <Menu mode="inline" selectedKeys={[location.pathname]} items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, marginTop: 4, fontSize: 13 }} />
        <div style={{ padding: "12px 16px", borderTop: "1px solid #f0f0f0",
          position: "absolute", bottom: 0, width: "100%" }}>
          <Button icon={<LogoutOutlined />} type="text" block onClick={signOut}
            style={{ textAlign: "left", color: "#888", fontSize: 13 }}>
            Выйти
          </Button>
        </div>
      </Sider>
      <Layout style={{ marginLeft: 210 }}>
        <Header style={{ background: "#fff", padding: "0 24px",
          borderBottom: "1px solid #f0f0f0", height: 48, lineHeight: "48px" }}>
          <Text style={{ fontSize: 14, color: "#333" }}>
            {PAGE_TITLES[location.pathname] ?? "WIM"}
          </Text>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: "#fff", borderRadius: 8, minHeight: 400 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
