import React, { useEffect, useState } from "react";
import { Card, Form, Input, InputNumber, Select, DatePicker, Button, Typography, message, Space } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { postReceipt, getArticles } from "../api";

const { Title, Text } = Typography;

export default function PurchaseFormPage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => { getArticles("component").then(r => setArticles(r.data)); }, []);

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
      navigate("/purchases");
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate("/purchases")}
        style={{ paddingLeft: 0, marginBottom: 12 }}>
        К списку поступлений
      </Button>
      <Card style={{ maxWidth: 480 }}>
        <Title level={5} style={{ marginTop: 0 }}>Поступление комплектующих</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 20, fontSize: 13 }}>
          Увеличивает остаток выбранного компонента на складе комплектующих
        </Text>
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
          <Space>
            <Button type="primary" htmlType="submit" loading={saving}>Сохранить</Button>
            <Button onClick={() => navigate("/purchases")}>Отмена</Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
