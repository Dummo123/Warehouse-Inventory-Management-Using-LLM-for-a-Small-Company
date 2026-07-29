import React, { useEffect, useState } from "react";
import { Row, Col, Statistic, DatePicker, Space, Table, Tag, Typography, Card } from "antd";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import dayjs from "dayjs";
import { getMovements } from "../api";

const { RangePicker } = DatePicker;
const { Text } = Typography;
const CHANNELS: Record<string, string> = { marketplace_1: "Ozon", marketplace_2: "Яндекс.Маркет", website: "Сайт", other: "Другое" };
const CHANNEL_COLORS: Record<string, string> = { marketplace_1: "blue", marketplace_2: "orange", website: "green", other: "default" };

export default function FinancePage() {
  const [shipments, setShipments] = useState<any[]>([]);
  const [returns, setReturns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { limit: 1000 };
      if (dateRange) { params.date_from = dateRange[0]; params.date_to = dateRange[1]; }
      const [sRes, rRes] = await Promise.all([
        getMovements({ ...params, movement_type: "shipment" }),
        getMovements({ ...params, movement_type: "return" }),
      ]);
      setShipments(sRes.data); setReturns(rRes.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [dateRange]);

  const channelMap: Record<string, any> = {};
  shipments.forEach(m => {
    const ch = m.sales_channel || "other";
    if (!channelMap[ch]) channelMap[ch] = { channel: ch, revenue: 0, returns: 0, units: 0 };
    channelMap[ch].revenue += m.quantity * (m.price_per_unit || 0);
    channelMap[ch].units += m.quantity;
  });
  returns.forEach(m => {
    const ch = m.sales_channel || "other";
    if (!channelMap[ch]) channelMap[ch] = { channel: ch, revenue: 0, returns: 0, units: 0 };
    channelMap[ch].returns += m.quantity * (m.price_per_unit || 0);
  });
  const channelStats = Object.values(channelMap).map(s => ({ ...s, net: s.revenue - s.returns }));
  const totalRevenue = channelStats.reduce((s, r) => s + r.revenue, 0);
  const totalReturns = channelStats.reduce((s, r) => s + r.returns, 0);
  const totalNet = totalRevenue - totalReturns;
  const totalUnits = channelStats.reduce((s, r) => s + r.units, 0);

  const monthlyMap: Record<string, any> = {};
  shipments.forEach(m => {
    const mo = dayjs(m.movement_date).format("MM.YYYY");
    if (!monthlyMap[mo]) monthlyMap[mo] = { month: mo, revenue: 0, returns: 0 };
    monthlyMap[mo].revenue += m.quantity * (m.price_per_unit || 0);
  });
  returns.forEach(m => {
    const mo = dayjs(m.movement_date).format("MM.YYYY");
    if (!monthlyMap[mo]) monthlyMap[mo] = { month: mo, revenue: 0, returns: 0 };
    monthlyMap[mo].returns += m.quantity * (m.price_per_unit || 0);
  });
  const trendData = Object.values(monthlyMap).sort((a, b) => a.month.localeCompare(b.month));

  const channelColumns = [
    { title: "Канал", dataIndex: "channel", key: "ch", render: (v: string) => <Tag color={CHANNEL_COLORS[v]}>{CHANNELS[v] ?? v}</Tag> },
    { title: "Продаж (шт)", dataIndex: "units", key: "units", align: "right" as const },
    { title: "Выручка", dataIndex: "revenue", key: "rev", align: "right" as const, render: (v: number) => `${Math.round(v).toLocaleString("ru")} ₽` },
    { title: "Возвраты", dataIndex: "returns", key: "ret", align: "right" as const, render: (v: number) => v > 0 ? <Text type="danger">−{Math.round(v).toLocaleString("ru")} ₽</Text> : <Text type="secondary">—</Text> },
    { title: "Чистая выручка", dataIndex: "net", key: "net", align: "right" as const, render: (v: number) => <Text strong>{Math.round(v).toLocaleString("ru")} ₽</Text> },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 20 }}>
        <RangePicker format="YYYY-MM-DD" placeholder={["Дата с", "Дата по"]}
          onChange={(_, s) => setDateRange(s[0] && s[1] ? [s[0], s[1]] : null)} />
      </Space>
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col><Statistic title="Выручка (брутто)" value={Math.round(totalRevenue)} suffix="₽" /></Col>
        <Col><Statistic title="Возвраты" value={Math.round(totalReturns)} suffix="₽" valueStyle={{ color: totalReturns > 0 ? "#ff4d4f" : "inherit" }} /></Col>
        <Col><Statistic title="Чистая выручка" value={Math.round(totalNet)} suffix="₽" valueStyle={{ color: totalNet >= 0 ? "#52c41a" : "#ff4d4f" }} /></Col>
        <Col><Statistic title="Продано (шт)" value={totalUnits} /></Col>
      </Row>
      <Card title="По каналам продаж" size="small" style={{ marginBottom: 24 }}>
        <Table rowKey="channel" columns={channelColumns} dataSource={channelStats} size="small" pagination={false} loading={loading} />
      </Card>
      {trendData.length > 1 && (
        <Card title="Динамика по месяцам" size="small">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trendData} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => `${Math.round(v).toLocaleString("ru")} ₽`} />
              <Legend />
              <Line type="monotone" dataKey="revenue" name="Выручка" stroke="#1677ff" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="returns" name="Возвраты" stroke="#ff4d4f" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}
