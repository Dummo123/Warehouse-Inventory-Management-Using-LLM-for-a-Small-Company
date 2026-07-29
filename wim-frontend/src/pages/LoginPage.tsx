import React from "react";
import { Form, Input, Button, Alert, Typography, Card } from "antd";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const { Title, Text } = Typography;

export default function LoginPage() {
  const { signIn, loading, error } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; password: string }) => {
    const ok = await signIn(values.username, values.password);
    if (ok) navigate("/stock");
  };

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center",
      minHeight: "100vh", background: "#f5f5f5" }}>
      <Card style={{ width: 360, boxShadow: "0 2px 8px rgba(0,0,0,0.08)" }}>
        <Title level={4} style={{ marginBottom: 4 }}>WIM</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 24, fontSize: 13 }}>
          Система учёта склада SmartTherm
        </Text>
        {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} showIcon />}
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item label="Логин" name="username" rules={[{ required: true, message: "Введите логин" }]}>
            <Input autoFocus />
          </Form.Item>
          <Form.Item label="Пароль" name="password" rules={[{ required: true, message: "Введите пароль" }]}>
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>Войти</Button>
        </Form>
      </Card>
    </div>
  );
}
