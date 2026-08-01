import React, { useEffect, useState } from "react";
import { Table, Button, Space } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import { getMovements } from "../api";

export default function ProductionPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const res = await getMovements({ movement_type: "production", limit: 300 });
      setData(res.data.filter((m: any) => m.quantity > 0));
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const columns = [
    { title: "Дата", dataIndex: "movement_date", key: "date", width: 140,
      render: (v: string) => dayjs(v).format("DD.MM.YYYY HH:mm") },
    { title: "Артикул", dataIndex: "article_code", key: "code", width: 110 },
    { title: "Наименование", dataIndex: "article_name", key: "name", ellipsis: true },
    { title: "Произведено", dataIndex: "quantity", key: "qty", width: 110, align: "right" as const,
      render: (v: number) => `${v} шт` },
    { title: "Комментарий", dataIndex: "comment", key: "cmt", ellipsis: true,
      render: (v: string) => v || "—" },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/production/new")}>
          Запустить производство
        </Button>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={data} loading={loading}
        size="small" pagination={{ pageSize: 25 }} />
    </div>
  );
}
