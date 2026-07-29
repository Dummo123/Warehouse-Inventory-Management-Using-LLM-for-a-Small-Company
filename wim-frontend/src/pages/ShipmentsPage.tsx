import React, { useEffect, useState } from "react";
import { Table, Button, Form, Input, InputNumber, Select, Modal, message, Space, Tag, DatePicker } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { getMovements, postShipment, getArticles } from "../api";

const CHANNELS: Record<string, string> = { marketplace_1: "Ozon", marketplace_2: "Яндекс.Маркет", website: "Сайт", other: "Другое" };
const CHANNEL_COLORS: Record<string, string> = { marketplace_1: "blue", marketplace_2: "orange", website: "green", other: "default" };

export default function ShipmentsPage() {
  const [data, setData] = useState<any[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try { const res = await getMovements({ movement_type: "shipment", limit: 300 }); setData(res.data); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); getArticles("finished").then(r => setArticles(r.data)); }, []);

  const onSave = async (values: Record<string, any>) => {
    setSaving(true);
    try {
      await postShipment({
        article_code: values.article_code, movement_type: "shipment",
        quantity: values.quantity, price_per_unit: values.price_per_unit,
        sales_channel: values.sales_channel, comment: values.comment,
        movement_date: values.movement_date ? values.movement_date.toISOString() : undefined,
      });
      message.success("Отгрузка зарегистрирована");
      form.resetFields(); setModalOpen(false); load();
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  const columns = [
    { title: "Дата", dataIndex: "movement_date", key: "date", width: 140, render: (v: string) => dayjs(v).format("DD.MM.YYYY HH:mm") },
    { title: "Артикул", dataIndex: "article_code", key: "code", width: 110 },
    { title: "Наименование", dataIndex: "article_name", key: "name", ellipsis: true },
    { title: "Кол-во", dataIndex: "quantity", key: "qty", width: 80, align: "right" as const },
    { title: "Цена", dataIndex: "price_per_unit", key: "price", width: 100, align: "right" as const, render: (v: number) => v ? `${v.toLocaleString("ru")} ₽` : "—" },
    { title: "Выручка", key: "rev", width: 110, align: "right" as const, render: (_: unknown, row: any) => row.price_per_unit ? `${Math.round(row.quantity * row.price_per_unit).toLocaleString("ru")} ₽` : "—" },
    { title: "Канал", dataIndex: "sales_channel", key: "ch", width: 130, render: (v: string) => v ? <Tag color={CHANNEL_COLORS[v]}>{CHANNELS[v] ?? v}</Tag> : "—" },
    { title: "Комментарий", dataIndex: "comment", key: "cmt", ellipsis: true, render: (v: string) => v || "—" },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>Зарегистрировать отгрузку</Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} size="small" pagination={{ pageSize: 25, showSizeChanger: true }} />
      <Modal title="Отгрузка готовой продукции" open={modalOpen} onCancel={() => setModalOpen(false)} footer={null} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={onSave} requiredMark={false}>
          <Form.Item label="Готовое изделие" name="article_code" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={articles.map(a => ({ value: a.code, label: `${a.code} — ${a.name}` }))} />
          </Form.Item>
          <Form.Item label="Количество" name="quantity" rules={[{ required: true }]}><InputNumber min={1} precision={0} style={{ width: "100%" }} /></Form.Item>
          <Form.Item label="Цена продажи за единицу (₽)" name="price_per_unit"><InputNumber min={0} precision={2} style={{ width: "100%" }} /></Form.Item>
          <Form.Item label="Канал продаж" name="sales_channel" rules={[{ required: true }]}>
            <Select options={[{ value: "marketplace_1", label: "Ozon" }, { value: "marketplace_2", label: "Яндекс.Маркет" }, { value: "website", label: "Собственный сайт" }, { value: "other", label: "Другое" }]} />
          </Form.Item>
          <Form.Item label="Дата" name="movement_date"><DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" /></Form.Item>
          <Form.Item label="Комментарий" name="comment"><Input /></Form.Item>
          <Button type="primary" htmlType="submit" loading={saving} block>Сохранить</Button>
        </Form>
      </Modal>
    </div>
  );
}
