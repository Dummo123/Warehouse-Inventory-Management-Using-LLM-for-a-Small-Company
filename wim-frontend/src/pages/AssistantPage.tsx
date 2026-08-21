import React, { useState } from "react";
import { Card, Button, List, Typography, Space, Alert, Tag, Input, Spin } from "antd";
import { RobotOutlined, SendOutlined } from "@ant-design/icons";
import { askAssistant } from "../api";

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

const PRESET_QUESTIONS = [
  { label: "Дефицит для производства", question: "Чего не хватает для производства FS_ST005 в количестве 5 штук?" },
  { label: "Закупки на месяц", question: "Что необходимо закупить в этом месяце исходя из остатков и динамики расходов?" },
  { label: "Топ продаж", question: "Какие товары продавались лучше всего за прошлый месяц?" },
  { label: "Выручка по артикулу", question: "Какова выручка по артикулу FS_ST005 за последний квартал по каналам продаж?" },
  { label: "Доступная прибыль", question: "Какая сумма доступна для реинвестирования или выплат за текущий месяц?" },
];

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await askAssistant(q);
      setAnswer(res.data.answer);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Не удалось получить ответ от ассистента. Бэкенд запущен?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 720 }}>
      <Alert type="info" showIcon icon={<RobotOutlined />}
        message="Помощник"
        description="Числа в ответе всегда считаются напрямую из базы данных склада. Модель используется только для формулировки текста."
        style={{ marginBottom: 24 }} />

      <Card title="5 основных вопросов" size="small" style={{ marginBottom: 24 }}>
        <List dataSource={PRESET_QUESTIONS} renderItem={(item) => (
          <List.Item onClick={() => setQuestion(item.question)}
            style={{ cursor: "pointer", padding: "10px 12px",
              background: question === item.question ? "#f0f5ff" : "transparent", borderRadius: 6, marginBottom: 4 }}>
            <Space direction="vertical" size={2} style={{ width: "100%" }}>
              <Tag color="blue">{item.label}</Tag>
              <Text>{item.question}</Text>
            </Space>
          </List.Item>
        )} />
      </Card>

      <Card size="small">
        <Space direction="vertical" style={{ width: "100%" }} size={12}>
          <TextArea rows={3} value={question} onChange={(e) => setQuestion(e.target.value)}
            placeholder="Задайте вопрос об остатках, производстве, продажах или финансах..." />
          <Button type="primary" icon={<SendOutlined />} loading={loading}
            onClick={() => ask(question)} disabled={!question.trim()}>
            Спросить
          </Button>
          {loading && <Spin size="small" />}
          {error && <Alert type="error" message={error} showIcon />}
          {answer && (
            <div style={{ background: "#fafafa", padding: 16, borderRadius: 6 }}>
              <Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>{answer}</Paragraph>
            </div>
          )}
        </Space>
      </Card>
    </div>
  );
}