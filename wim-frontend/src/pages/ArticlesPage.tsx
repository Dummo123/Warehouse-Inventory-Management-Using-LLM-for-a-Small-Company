import React, { useEffect, useState } from "react";
import {
  Table, Tag, Button, Modal, Form, Input, InputNumber, Select,
  Space, Drawer, List, Popconfirm, message, Segmented, Typography,
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, UnorderedListOutlined } from "@ant-design/icons";
import { getArticles, createArticle, updateArticle, deleteArticle, getBOM } from "../api";

const { Text } = Typography;
interface Article {
  id: number; code: string; name: string; article_type: string;
  unit: string; cost_price: number; responsible: string; comment: string; is_active: boolean;
}
interface BOMEntry { child_id: number; child_code: string; child_name: string; quantity: number; }

export default function ArticlesPage() {
  const [data, setData] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Article | null>(null);
  const [bomArticle, setBomArticle] = useState<Article | null>(null);
  const [bomData, setBomData] = useState<BOMEntry[]>([]);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const res = await getArticles(filter !== "all" ? filter : undefined);
      setData(res.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const openCreate = () => { setEditTarget(null); form.resetFields(); setModalOpen(true); };
  const openEdit = (row: Article) => { setEditTarget(row); form.setFieldsValue(row); setModalOpen(true); };
  const openBOM = async (row: Article) => {
    setBomArticle(row);
    const res = await getBOM(row.code);
    setBomData(res.data);
  };
  const onDelete = async (code: string) => {
    try { await deleteArticle(code); message.success("Удалено"); load(); }
    catch { message.error("Ошибка при удалении"); }
  };
  const onSave = async (values: Record<string, unknown>) => {
    try {
      if (editTarget) { await updateArticle(editTarget.code, values); message.success("Обновлено"); }
      else { await createArticle(values); message.success("Добавлено"); }
      setModalOpen(false); load();
    } catch (e: any) { message.error(e?.response?.data?.detail ?? "Ошибка"); }
  };

  const columns = [
    { title: "Артикул", dataIndex: "code", key: "code", width: 110,
      sorter: (a: Article, b: Article) => a.code.localeCompare(b.code) },
    { title: "Наименование", dataIndex: "name", key: "name", ellipsis: true },
    { title: "Тип", dataIndex: "article_type", key: "type", width: 130,
      render: (v: string) => v === "finished" ? <Tag color="blue">Готовое</Tag> : <Tag>Компонент</Tag> },
    { title: "Цена", dataIndex: "cost_price", key: "price", width: 110, align: "right" as const,
      render: (v: number) => v > 0 ? `${v.toLocaleString("ru")} ₽` : "—" },
    { title: "Ответственный", dataIndex: "responsible", key: "resp", width: 140,
      render: (v: string) => v || "—" },
    { title: "", key: "actions", width: 110,
      render: (_: unknown, row: Article) => (
        <Space>
          {row.article_type === "finished" && (
            <Button size="small" icon={<UnorderedListOutlined />} onClick={() => openBOM(row)} title="BOM" />
          )}
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(row)} />
          <Popconfirm title="Удалить?" onConfirm={() => onDelete(row.code)} okText="Да" cancelText="Нет">
            <Button size="small" icon={<DeleteOutlined />} danger />
          </Popconfirm>
        </Space>
      ) },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Segmented value={filter} onChange={(v) => setFilter(v as string)}
          options={[
            { label: "Все", value: "all" },
            { label: "Компоненты", value: "component" },
            { label: "Готовые изделия", value: "finished" },
          ]} />
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить</Button>
      </Space>
      <Table rowKey="code" columns={columns} dataSource={data} loading={loading}
        size="small" pagination={{ pageSize: 25 }} />
      <Modal title={editTarget ? "Редактировать" : "Новый артикул"}
        open={modalOpen} onCancel={() => setModalOpen(false)} footer={null} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={onSave} requiredMark={false}>
          {!editTarget && (
            <>
              <Form.Item label="Код (артикул)" name="code" rules={[{ required: true }]}>
                <Input placeholder="например 1137 или FS_ST008" />
              </Form.Item>
              <Form.Item label="Тип" name="article_type" rules={[{ required: true }]}>
                <Select options={[
                  { value: "component", label: "Компонент / Полуфабрикат" },
                  { value: "finished",  label: "Готовое изделие" },
                ]} />
              </Form.Item>
            </>
          )}
          <Form.Item label="Наименование" name="name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item label="Себестоимость (₽)" name="cost_price">
            <InputNumber min={0} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item label="Ответственный" name="responsible"><Input /></Form.Item>
          <Form.Item label="Комментарий" name="comment"><Input.TextArea rows={2} /></Form.Item>
          <Button type="primary" htmlType="submit" block>{editTarget ? "Сохранить" : "Добавить"}</Button>
        </Form>
      </Modal>
      <Drawer title={bomArticle ? `Состав: ${bomArticle.code} — ${bomArticle.name}` : ""}
        open={!!bomArticle} onClose={() => setBomArticle(null)} width={420}>
        {bomData.length === 0
          ? <Text type="secondary">Спецификация не задана</Text>
          : <List size="small" dataSource={bomData} renderItem={(item) => (
              <List.Item>
                <Space><Text code>{item.child_code}</Text><Text>{item.child_name}</Text></Space>
                <Text strong>× {item.quantity}</Text>
              </List.Item>
            )} />
        }
      </Drawer>
    </div>
  );
}
