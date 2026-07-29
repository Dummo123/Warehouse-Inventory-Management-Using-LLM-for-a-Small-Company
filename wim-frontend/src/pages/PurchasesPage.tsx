import React, { useEffect, useState } from "react";
import { Table, Button, Form, Input, InputNumber, Select, Modal, message, Space, DatePicker } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getMovements, postReceipt, getArticles } from "../api";

export default function PurchasesPage() {
  const [data, setData] = useState<any[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try { const res = await getMovements({ movement_type: "receipt", limit: 300 }); setData(res.data); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); getArticles("component").then(r => setArticles(r.data)); }, []);

  const onSave = async (values: Record<string, any>) => {
    setSaving(true);
    try {
      await postReceipt({
        article_code: values.article_code, movement_type: "receipt",
        quantity: values.quantity, price_per_unit: values.price_per_unit,
        comment: values.comment,
        movement_date: values.movement_date ? values.movement_date.toISOString() : undefined,
      });
      message.success("Поступление зарегистрировано");
      form.resetFields(); setModalOpen(false); load();
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  const columns = [
    { title: "Дата", dataIndex: "movement_date", key: "date", width: 140,
      render: (v: string) => dayjs(v).format("DD.MM.YYYY HH:mm") },
    { title: "Артикул", dataIndex: "article_code", key: "code", width: 100 },
    { title: "Наименование", dataIndex: "article_name", key: "name", ellipsis: true },
    { title: "Кол-во", dataIndex: "quantity", key: "qty", width: 80, align: "right" as const },
    { title: "Цена за ед.", dataIndex: "price_per_unit", key: "price", width: 110, align: "right" as const,
      render: (v: number) => v ? `${v.toLocaleString("ru")} ₽` : "—" },
    { title: "Сумма", key: "total", width: 120, align: "right" as const,
      render: (_: unknown, row: any) => row.price_per_unit
        ? `${Math.round(row.quantity * row.price_per_unit).toLocaleString("ru")} ₽` : "—" },
    { title: "Комментарий", dataIndex: "comment", key: "cmt", ellipsis: true,
      render: (v: string) => v || "—" },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          Зарегистрировать поступление
        </Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading}
        size="small" pagination={{ pageSize: 25, showSizeChanger: true }} />
      <Modal title="Поступление комплектующих" open={modalOpen}
        onCancel={() => setModalOpen(false)} footer={null} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={onSave} requiredMark={false}>
          <Form.Item label="Компонент" name="article_code" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" placeholder="Выберите"
              options={articles.map(a => ({ value: a.code, label: `${a.code} — ${a.name}` }))} />
          </Form.Item>
          <Form.Item label="Количество" name="quantity" rules={[{ required: true }]}>
            <InputNumber min={0.01} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item label="Цена за единицу (₽)" name="price_per_unit">
            <InputNumber min={0} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item label="Дата" name="movement_date">
            <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
          </Form.Item>
          <Form.Item label="Комментарий" name="comment"><Input.TextArea rows={2} /></Form.Item>
          <Button type="primary" htmlType="submit" loading={saving} block>Сохранить</Button>
        </Form>
      </Modal>
    </div>
  );
}
