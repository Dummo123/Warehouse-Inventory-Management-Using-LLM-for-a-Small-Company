import React, { useState } from "react";
import { Card, Button, List, Typography, Space, Alert, Tag } from "antd";
import { RobotOutlined, SendOutlined } from "@ant-design/icons";

const { Text, Title } = Typography;

const PRESET_QUESTIONS = [
  { label: "Дефицит для производства", question: "Чего не хватает для производства FS_ST005 в количестве 5 штук?" },
  { label: "Закупки на месяц", question: "Что необходимо закупить в этом месяце исходя из остатков и динамики расходов?" },
  { label: "Топ продаж", question: "Какие товары продавались лучше всего за прошлый месяц?" },
  { label: "Выручка по артикулу", question: "Какова выручка по артикулу FS_ST005 за последний квартал по каналам продаж?" },
  { label: "Доступная прибыль", question: "Какая сумма доступна для реинвестирования или выплат за текущий месяц?" },
];

export default function AssistantPage() {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div style={{ maxWidth: 720 }}>
      <Alert type="info" showIcon icon={<RobotOutlined />}
        message="ИИ-помощник — в разработке (Чекпоинт #3)"
        description="Ассистент на базе Ollama (Llama 3.1 8B) + RAG будет доступен после получения доступа к серверу. Здесь показаны 5 обязательных вопросов из ТЗ."
        style={{ marginBottom: 24 }} />
      <Card title="5 обязательных вопросов по ТЗ" size="small" style={{ marginBottom: 24 }}>
        <List dataSource={PRESET_QUESTIONS} renderItem={(item) => (
          <List.Item onClick={() => setSelected(item.question)}
            style={{ cursor: "pointer", padding: "10px 12px",
              background: selected === item.question ? "#f0f5ff" : "transparent", borderRadius: 6, marginBottom: 4 }}>
            <Space direction="vertical" size={2} style={{ width: "100%" }}>
              <Tag color="blue">{item.label}</Tag>
              <Text>{item.question}</Text>
            </Space>
          </List.Item>
        )} />
      </Card>
      {selected && (
        <Card size="small">
          <Space direction="vertical" style={{ width: "100%" }}>
            <Text type="secondary" style={{ fontSize: 12 }}>Выбранный вопрос:</Text>
            <div style={{ background: "#fafafa", padding: 12, borderRadius: 6 }}><Text>{selected}</Text></div>
            <Button type="primary" icon={<SendOutlined />} disabled>Отправить (доступно в Чекпоинте #3)</Button>
          </Space>
        </Card>
      )}
      <Card title="Архитектура (план)" size="small" style={{ marginTop: 24 }}>
        <List size="small" dataSource={[
          "Вопрос на русском языке → векторизация (MiniLM-L12-v2)",
          "Qdrant ищет релевантный контекст по артикулам и BOM",
          "SQL-запрос достаёт живые данные из PostgreSQL",
          "Контекст + данные → Ollama (Llama 3.1 8B)",
          "Ответ с пометкой «Данные на: дата»",
        ]} renderItem={(item, i) => (
          <List.Item><Space><Tag>{i + 1}</Tag><Text style={{ fontSize: 13 }}>{item}</Text></Space></List.Item>
        )} />
      </Card>
    </div>
  );
}
