import React, { useEffect, useState } from "react";
import {
  Card, Form, InputNumber, Select, Input, Button, Space, Alert, List, Typography, message,
} from "antd";
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { postProduction, getArticles, getBOM, getStock } from "../api";

const { Title, Text } = Typography;

export default function ProductionFormPage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [checkResult, setCheckResult] = useState<any>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => { getArticles("finished").then(r => setArticles(r.data)); }, []);

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
      navigate("/production");
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate("/production")}
        style={{ paddingLeft: 0, marginBottom: 12 }}>
        К списку производственных операций
      </Button>
      <Card style={{ maxWidth: 560 }}>
        <Title level={5} style={{ marginTop: 0 }}>Запуск производства</Title>
        <Text type="secondary" style={{ display: "block", marginBottom: 20, fontSize: 13 }}>
          Списывает компоненты по спецификации (BOM) и оприходует готовое изделие
        </Text>
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
          <Space>
            <Button type="primary" htmlType="submit" loading={saving}
              disabled={checkResult && !checkResult.allOk}>Произвести</Button>
            <Button onClick={() => navigate("/production")}>Отмена</Button>
          </Space>
        </Form>
      </Card>
    </div>
  );
}
