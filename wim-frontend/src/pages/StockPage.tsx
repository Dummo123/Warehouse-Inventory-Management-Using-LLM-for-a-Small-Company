import React, { useEffect, useState } from "react";
import { Table, Tag, Segmented, InputNumber, Space, Typography, Statistic, Row, Col, Alert } from "antd";
import { WarningOutlined } from "@ant-design/icons";
import { getStock } from "../api";

const { Text } = Typography;
interface StockRow {
  article_code: string; article_name: string; article_type: string;
  warehouse_name: string; quantity: number; cost_price: number; total_value: number;
}

export default function StockPage() {
  const [data, setData] = useState<StockRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState("all");
  const [lowStock, setLowStock] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {};
      if (typeFilter === "component") params.article_type = "component";
      if (typeFilter === "finished") params.article_type = "finished";
      if (lowStock !== null) params.low_stock = lowStock;
      const res = await getStock(params);
      setData(res.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [typeFilter, lowStock]);

  const totalValue = data.reduce((s, r) => s + r.total_value, 0);
  const zeroCount = data.filter(r => r.quantity === 0).length;
  const lowCount = data.filter(r => r.quantity > 0 && r.quantity < 5).length;

  const columns = [
    { title: "Артикул", dataIndex: "article_code", key: "code", width: 110,
      sorter: (a: StockRow, b: StockRow) => a.article_code.localeCompare(b.article_code) },
    { title: "Наименование", dataIndex: "article_name", key: "name", ellipsis: true },
    { title: "Тип", dataIndex: "article_type", key: "type", width: 130,
      render: (v: string) => v === "finished" ? <Tag color="blue">Готовое</Tag> : <Tag>Компонент</Tag> },
    { title: "Склад", dataIndex: "warehouse_name", key: "wh", width: 200, ellipsis: true },
    { title: "Остаток", dataIndex: "quantity", key: "qty", width: 90, align: "right" as const,
      sorter: (a: StockRow, b: StockRow) => a.quantity - b.quantity,
      render: (v: number) => (
        <Text style={{ color: v === 0 ? "#ff4d4f" : v < 5 ? "#fa8c16" : "inherit", fontWeight: v === 0 ? 600 : 400 }}>
          {v} шт
        </Text>
      ) },
    { title: "Цена", dataIndex: "cost_price", key: "price", width: 100, align: "right" as const,
      render: (v: number) => v > 0 ? `${v.toLocaleString("ru")} ₽` : "—" },
    { title: "Стоимость", dataIndex: "total_value", key: "total", width: 120, align: "right" as const,
      sorter: (a: StockRow, b: StockRow) => a.total_value - b.total_value,
      render: (v: number) => v > 0 ? `${Math.round(v).toLocaleString("ru")} ₽` : "—" },
  ];

  return (
    <div>
      {zeroCount > 0 && (
        <Alert type="warning" showIcon icon={<WarningOutlined />}
          message={`${zeroCount} позиций с нулевым остатком`} style={{ marginBottom: 16 }} />
      )}
      <Row gutter={24} style={{ marginBottom: 20 }}>
        <Col><Statistic title="Позиций" value={data.length} /></Col>
        <Col><Statistic title="Стоимость склада" value={Math.round(totalValue)} suffix="₽" /></Col>
        <Col><Statistic title="Заканчивается (< 5)" value={lowCount}
          valueStyle={{ color: lowCount > 0 ? "#fa8c16" : "inherit" }} /></Col>
        <Col><Statistic title="Нулевые" value={zeroCount}
          valueStyle={{ color: zeroCount > 0 ? "#ff4d4f" : "inherit" }} /></Col>
      </Row>
      <Space style={{ marginBottom: 16 }} wrap>
        <Segmented value={typeFilter} onChange={(v) => setTypeFilter(v as string)}
          options={[
            { label: "Всё", value: "all" },
            { label: "Компоненты", value: "component" },
            { label: "Готовые изделия", value: "finished" },
          ]} />
        <Space>
          <Text type="secondary" style={{ fontSize: 13 }}>Остаток ниже:</Text>
          <InputNumber min={0} placeholder="—" value={lowStock ?? undefined}
            onChange={(v) => setLowStock(v ?? null)} style={{ width: 80 }} />
        </Space>
      </Space>
      <Table rowKey="article_code" columns={columns} dataSource={data} loading={loading}
        size="small" pagination={{ pageSize: 25, showSizeChanger: true }}
        rowClassName={(row) => row.quantity === 0 ? "row-zero" : ""} />
      <style>{`.row-zero td { background: #fff2f0 !important; }`}</style>
    </div>
  );
}
