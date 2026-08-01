import React, { useEffect, useState } from "react";
import { Card, Form, Input, InputNumber, Select, DatePicker, Button, Typography, message, Space } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { postReturn, getArticles } from "../api";

const { Title, Text } = Typography;

export default function ReturnFormPage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => { getArticles("finished").then(r => setArticles(r.data)); }, []);

  const onSave = async (values: Record<string, any>) => {
    setSaving(true);
    try {
      await postReturn({
        article_code: values.article_code, movement_type: "return",
        quantity: values.quantity, sales_channel: values.sales_channel, comment: values.comment,
        movement_date: values.movement_date ? values.movement_date.toISOString() : undefined,
      });
      message.success("Возврат зарегистрирован");
      navigate("/returns");
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate("/returns")}
        style={{ paddingLeft: 0, marginBottom: 12 }}>
        К списку возвратов
      </Button>
      <Card style={{ maxWidth: 480 }}>
        <Title level={5} style={{ marginTop: 0 }}>Возврат от клиента</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 20, fontSize: 13 }}>
          Увеличивает остаток готового изделия и фиксирует канал/дату возврата
        </Text>
        <Form form={form} layout="vertical" onFinish={onSave} requiredMark={false}>
          <Form.Item label="Изделие" name="article_code" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" options={articles.map(a => ({ value: a.code, label: `${a.code} — ${a.name}` }))} />
          </Form.Item>
          <Form.Item label="Количество" name="quantity" rules={[{ required: true }]}><InputNumber min={1} precision={0} style={{ width: "100%" }} /></Form.Item>
          <Form.Item label="Канал, откуда возврат" name="sales_channel" rules={[{ required: true }]}>
            <Select options={[{ value: "marketplace_1", label: "Ozon" }, { value: "marketplace_2", label: "Яндекс.Маркет" }, { value: "website", label: "Сайт" }, { value: "other", label: "Другое" }]} />
          </Form.Item>
          <Form.Item label="Дата возврата" name="movement_date"><DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" /></Form.Item>
          <Form.Item label="Причина / комментарий" name="comment"><Input.TextArea rows={2} /></Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={saving}>Сохранить</Button>
            <Button onClick={() => navigate("/returns")}>Отмена</Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
