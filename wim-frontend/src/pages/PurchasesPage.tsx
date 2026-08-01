import React, { useEffect, useState } from "react";
import { Table, Button, Space } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import { getMovements } from "../api";

export default function PurchasesPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try { const res = await getMovements({ movement_type: "receipt", limit: 300 }); setData(res.data); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

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
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/purchases/new")}>
          Зарегистрировать поступление
        </Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading}
        size="small" pagination={{ pageSize: 25, showSizeChanger: true }} />
    </div>
  );
}
