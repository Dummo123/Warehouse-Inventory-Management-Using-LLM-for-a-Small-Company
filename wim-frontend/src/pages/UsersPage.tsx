import React, { useEffect, useState } from "react";
import { Table, Button, Form, Input, Select, Modal, message, Space, Tag } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { getUsers, createUser } from "../api";

const ROLE_LABELS: Record<string, { label: string; color: string }> = {
  admin:    { label: "Администратор", color: "red" },
  operator: { label: "Оператор",      color: "blue" },
  viewer:   { label: "Наблюдатель",   color: "default" },
};

export default function UsersPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try { const res = await getUsers(); setData(res.data); }
    catch { }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const onSave = async (values: Record<string, any>) => {
    setSaving(true);
    try {
      await createUser(values);
      message.success("Пользователь создан");
      form.resetFields(); setModalOpen(false); load();
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  const columns = [
    { title: "Логин", dataIndex: "username", key: "username", width: 140 },
    { title: "Полное имя", dataIndex: "full_name", key: "name", ellipsis: true, render: (v: string) => v || "—" },
    { title: "Роль", dataIndex: "role", key: "role", width: 150,
      render: (v: string) => { const r = ROLE_LABELS[v] ?? { label: v, color: "default" }; return <Tag color={r.color}>{r.label}</Tag>; } },
    { title: "Баланс", dataIndex: "balance", key: "balance", width: 110, align: "right" as const,
      render: (v: number) => v ? `${v.toLocaleString("ru")} ₽` : "—" },
    { title: "Статус", dataIndex: "is_active", key: "active", width: 100,
      render: (v: boolean) => v ? <Tag color="green">Активен</Tag> : <Tag>Неактивен</Tag> },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>Добавить пользователя</Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} size="small" pagination={{ pageSize: 25 }} />
      <Modal title="Новый пользователь" open={modalOpen} onCancel={() => setModalOpen(false)} footer={null} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={onSave} requiredMark={false}>
          <Form.Item label="Логин" name="username" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item label="Полное имя" name="full_name"><Input /></Form.Item>
          <Form.Item label="Пароль" name="password" rules={[{ required: true, min: 6 }]}><Input.Password /></Form.Item>
          <Form.Item label="Роль" name="role" initialValue="operator">
            <Select options={[
              { value: "admin", label: "Администратор" },
              { value: "operator", label: "Оператор" },
              { value: "viewer", label: "Наблюдатель" },
            ]} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={saving} block>Создать</Button>
        </Form>
      </Modal>
    </div>
  );
}
