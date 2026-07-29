import React, { useEffect, useState } from "react";
import {
  Table, Button, Form, Input, InputNumber, Select, Modal, message,
  Space, Alert, List, Typography,
} from "antd";
import { PlusOutlined, CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getMovements, postProduction, getArticles, getBOM, getStock } from "../api";

const { Text } = Typography;

export default function ProductionPage() {
  const [data, setData] = useState<any[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [checkResult, setCheckResult] = useState<any>(null);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const res = await getMovements({ movement_type: "production", limit: 300 });
      setData(res.data.filter((m: any) => m.quantity > 0));
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); getArticles("finished").then(r => setArticles(r.data)); }, []);

  const checkAvailability = async (code: string, qty: number) => {
    if (!code || !qty) return;
    try {
      const [bomRes, stockRes] = await Promise.all([getBOM(code), getStock({ article_type: "component" })]);
      const stockMap: Record<string, number> = {};
      stockRes.data.forEach((s: any) => { stockMap[s.article_code] = s.quantity; });
      const items = bomRes.data.map((e: any) => {
        const required = e.quantity * qty;
        const available = stockMap[e.child_code] ?? 0;
        return { ...e, required, available, ok: available >= required };
      });
      setCheckResult({ items, allOk: items.every((r: any) => r.ok) });
    } catch { setCheckResult(null); }
  };

  const onSave = async (values: Record<string, any>) => {
    setSaving(true);
    try {
      await postProduction({ finished_article_code: values.article_code, quantity: values.quantity, comment: values.comment });
      message.success("Производство выполнено");
      form.resetFields(); setCheckResult(null); setModalOpen(false); load();
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  const columns = [
    { title: "Дата", dataIndex: "movement_date", key: "date", width: 140,
      render: (v: string) => dayjs(v).format("DD.MM.YYYY HH:mm") },
    { title: "Артикул", dataIndex: "article_code", key: "code", width: 110 },
    { title: "Наименование", dataIndex: "article_name", key: "name", ellipsis: true },
    { title: "Произведено", dataIndex: "quantity", key: "qty", width: 110, align: "right" as const,
      render: (v: number) => `${v} шт` },
    { title: "Комментарий", dataIndex: "comment", key: "cmt", ellipsis: true,
      render: (v: string) => v || "—" },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />}
          onClick={() => { setCheckResult(null); form.resetFields(); setModalOpen(true); }}>
          Запустить производство
        </Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading}
        size="small" pagination={{ pageSize: 25 }} />
      <Modal title="Производство" open={modalOpen} onCancel={() => setModalOpen(false)}
        footer={null} destroyOnClose width={540}>
        <Form form={form} layout="vertical" onFinish={onSave} requiredMark={false}>
          <Form.Item label="Готовое изделие" name="article_code" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={articles.map(a => ({ value: a.code, label: `${a.code} — ${a.name}` }))}
              onChange={() => setCheckResult(null)} />
          </Form.Item>
          <Form.Item label="Количество" name="quantity" rules={[{ required: true }]}>
            <InputNumber min={1} precision={0} style={{ width: "100%" }} onChange={() => setCheckResult(null)} />
          </Form.Item>
          <Button style={{ marginBottom: 16 }} onClick={() =>
            checkAvailability(form.getFieldValue("article_code"), form.getFieldValue("quantity"))}>
            Проверить компоненты
          </Button>
          {checkResult && (
            <div style={{ marginBottom: 16 }}>
              {checkResult.allOk
                ? <Alert type="success" message="Все компоненты в наличии" showIcon style={{ marginBottom: 8 }} />
                : <Alert type="error" message="Недостаточно компонентов" showIcon style={{ marginBottom: 8 }} />}
              <List size="small" bordered dataSource={checkResult.items}
                renderItem={(item: any) => (
                  <List.Item>
                    <Space>
                      {item.ok ? <CheckCircleOutlined style={{ color: "#52c41a" }} />
                               : <CloseCircleOutlined style={{ color: "#ff4d4f" }} />}
                      <Text code>{item.child_code}</Text>
                      <Text>{item.child_name}</Text>
                    </Space>
                    <Space>
                      <Text type="secondary">нужно: {item.required}</Text>
                      <Text style={{ color: item.ok ? "#52c41a" : "#ff4d4f" }}>есть: {item.available}</Text>
                    </Space>
                  </List.Item>
                )} />
            </div>
          )}
          <Form.Item label="Комментарий" name="comment"><Input /></Form.Item>
          <Button type="primary" htmlType="submit" loading={saving} block
            disabled={checkResult && !checkResult.allOk}>Произвести</Button>
        </Form>
      </Modal>
    </div>
  );
}
