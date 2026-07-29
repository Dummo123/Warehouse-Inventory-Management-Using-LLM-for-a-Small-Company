import React, { useState } from "react";
import { Button, DatePicker, Space, Card, Typography, message } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { exportExcel } from "../api";

const { RangePicker } = DatePicker;
const { Text, Title } = Typography;

export default function ReportsPage() {
  const [dates, setDates] = useState<[string, string] | null>(null);
  const [loading, setLoading] = useState(false);

  const download = async () => {
    setLoading(true);
    try {
      const res = await exportExcel(dates?.[0], dates?.[1]);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `warehouse_report_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
      message.success("Отчёт скачан");
    } catch { message.error("Ошибка при формировании отчёта"); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Card style={{ maxWidth: 480 }}>
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          <div>
            <Title level={5} style={{ margin: 0 }}>Выгрузка в Excel</Title>
            <Text type="secondary" style={{ fontSize: 13 }}>Листы: Остатки, Движения, Компоненты, Готовые изделия</Text>
          </div>
          <div>
            <Text style={{ display: "block", marginBottom: 8, fontSize: 13 }}>Период движений (необязательно):</Text>
            <RangePicker onChange={(_, s) => setDates(s[0] && s[1] ? [s[0], s[1]] : null)}
              format="YYYY-MM-DD" placeholder={["Дата с", "Дата по"]} style={{ width: "100%" }} />
          </div>
          <Button type="primary" icon={<DownloadOutlined />} loading={loading} onClick={download} block>
            Скачать отчёт
          </Button>
        </Space>
      </Card>
    </div>
  );
}
