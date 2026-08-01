import React, { useEffect, useState } from "react";
import { Card, Form, Input, InputNumber, Select, DatePicker, Button, Typography, message, Space } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { postShipment, getArticles } from "../api";

const { Title, Text } = Typography;

export default function ShipmentFormPage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => { getArticles("finished").then(r => setArticles(r.data)); }, []);

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
      navigate("/shipments");
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate("/shipments")}
        style={{ paddingLeft: 0, marginBottom: 12 }}>
        К списку отгрузок
      </Button>
      <Card style={{ maxWidth: 480 }}>
        <Title level={5} style={{ marginTop: 0 }}>Отгрузка готовой продукции</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 20, fontSize: 13 }}>
          Уменьшает остаток готового изделия и фиксирует канал продаж
        </Text>
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
          <Space>
            <Button type="primary" htmlType="submit" loading={saving}>Сохранить</Button>
            <Button onClick={() => navigate("/shipments")}>Отмена</Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
