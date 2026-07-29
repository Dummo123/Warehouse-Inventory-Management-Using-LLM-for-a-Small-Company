import React, { useEffect, useState } from "react";
import { Table, Select, Space, Tag, DatePicker, Typography, Tooltip, Tabs } from "antd";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RTooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";
import dayjs from "dayjs";
import { getMovements } from "../api";

const { RangePicker } = DatePicker;
const { Text } = Typography;

const TYPE_LABELS: Record<string, { label: string; color: string }> = {
  receipt:    { label: "Поступление",  color: "green" },
  shipment:   { label: "Отгрузка",     color: "blue" },
  production: { label: "Производство", color: "purple" },
  return:     { label: "Возврат",      color: "orange" },
  write_off:  { label: "Списание",     color: "red" },
};

function buildChartData(movements: any[]) {
  const byDate: Record<string, any> = {};
  movements.forEach(m => {
    const d = dayjs(m.movement_date).format("DD.MM");
    if (!byDate[d]) byDate[d] = { date: d, receipt: 0, shipment: 0, production: 0, return: 0 };
    if (m.movement_type in byDate[d]) byDate[d][m.movement_type] += m.quantity;
  });
  return Object.values(byDate).slice(-30);
}

export default function MovementsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { limit: 500 };
      if (typeFilter) params.movement_type = typeFilter;
      if (dateRange) { params.date_from = dateRange[0]; params.date_to = dateRange[1]; }
      const res = await getMovements(params);
      setData(res.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [typeFilter, dateRange]);

  const columns = [
    { title: "Дата", dataIndex: "movement_date", key: "date", width: 140,
      render: (v: string) => dayjs(v).format("DD.MM.YYYY HH:mm") },
    { title: "Артикул", dataIndex: "article_code", key: "code", width: 100 },
    { title: "Наименование", dataIndex: "article_name", key: "name", ellipsis: true },
    { title: "Тип", dataIndex: "movement_type", key: "type", width: 130,
      render: (v: string) => {
        const t = TYPE_LABELS[v] ?? { label: v, color: "default" };
        return <Tag color={t.color}>{t.label}</Tag>;
      } },
    { title: "Кол-во", dataIndex: "quantity", key: "qty", width: 80, align: "right" as const },
    { title: "Склад", dataIndex: "warehouse_name", key: "wh", width: 160, ellipsis: true },
    { title: "Комментарий", dataIndex: "comment", key: "cmt", ellipsis: true,
      render: (v: string) => v
        ? <Tooltip title={v}><Text type="secondary" style={{ fontSize: 12 }}>{v}</Text></Tooltip>
        : "—" },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <RangePicker format="YYYY-MM-DD" placeholder={["Дата с", "Дата по"]}
          onChange={(_, s) => setDateRange(s[0] && s[1] ? [s[0], s[1]] : null)} />
        <Select placeholder="Тип операции" allowClear style={{ width: 160 }}
          onChange={setTypeFilter}
          options={Object.entries(TYPE_LABELS).map(([k, v]) => ({ value: k, label: v.label }))} />
      </Space>
      <Tabs items={[
        { key: "table", label: "Журнал",
          children: (
            <Table rowKey="id" columns={columns} dataSource={data} loading={loading}
              size="small" pagination={{ pageSize: 25, showSizeChanger: true }} />
          ) },
        { key: "chart", label: "График",
          children: (
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={buildChartData(data)} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <RTooltip />
                <Legend />
                <Bar dataKey="receipt"    name="Поступления"  fill="#52c41a" radius={[2,2,0,0]} />
                <Bar dataKey="shipment"   name="Отгрузки"     fill="#1677ff" radius={[2,2,0,0]} />
                <Bar dataKey="production" name="Производство" fill="#722ed1" radius={[2,2,0,0]} />
                <Bar dataKey="return"     name="Возвраты"     fill="#fa8c16" radius={[2,2,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) },
      ]} />
    </div>
  );
}
