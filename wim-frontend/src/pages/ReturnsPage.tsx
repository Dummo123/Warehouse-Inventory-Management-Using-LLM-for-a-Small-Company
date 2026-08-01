import React, { useEffect, useState } from "react";
import { Table, Button, Space, Tag } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import { getMovements } from "../api";

const CHANNELS: Record<string, string> = { marketplace_1: "Ozon", marketplace_2: "Яндекс.Маркет", website: "Сайт", other: "Другое" };
const CHANNEL_COLORS: Record<string, string> = { marketplace_1: "blue", marketplace_2: "orange", website: "green", other: "default" };

export default function ReturnsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try { const res = await getMovements({ movement_type: "return", limit: 300 }); setData(res.data); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const columns = [
    { title: "Дата", dataIndex: "movement_date", key: "date", width: 140, render: (v: string) => dayjs(v).format("DD.MM.YYYY HH:mm") },
    { title: "Артикул", dataIndex: "article_code", key: "code", width: 110 },
    { title: "Наименование", dataIndex: "article_name", key: "name", ellipsis: true },
    { title: "Кол-во", dataIndex: "quantity", key: "qty", width: 80, align: "right" as const },
    { title: "Канал", dataIndex: "sales_channel", key: "ch", width: 140, render: (v: string) => v ? <Tag color={CHANNEL_COLORS[v]}>{CHANNELS[v] ?? v}</Tag> : "—" },
    { title: "Комментарий", dataIndex: "comment", key: "cmt", ellipsis: true, render: (v: string) => v || "—" },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/returns/new")}>Зарегистрировать возврат</Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} size="small" pagination={{ pageSize: 25 }} />
    </div>
  );
}
