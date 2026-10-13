'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus, Copy, RefreshCw, Users, X, Trash2, ChevronLeft,
  Lock, Unlock, Settings, UserPlus, CheckCircle, AlertTriangle,
} from 'lucide-react';
import api from '@/lib/api';

/* ═══════════════════════════════════════════
   班级管理 — 创建 / 邀请码 / 学生名单 / 移除
   ═══════════════════════════════════════════ */
export default function ClassModule() {
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedClass, setSelectedClass] = useState<any>(null);
  const [toast, setToast] = useState<{ type: 'ok' | 'err'; msg: string } | null>(null);

  const showToast = (type: 'ok' | 'err', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 2500);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await api.listClasses();
      if (res.success) setClasses(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (selectedClass) {
    return (
      <ClassDetail
        classData={selectedClass}
        onBack={() => { setSelectedClass(null); load(); }}
        onToast={showToast}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className={`px-4 py-2.5 rounded-lg text-sm flex items-center gap-2 ${
              toast.type === 'ok' ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-400/20' : 'bg-red-500/15 text-red-300 border border-red-400/20'
            }`}
          >
            {toast.type === 'ok' ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 顶部操作 */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/40">共 {classes.length} 个班级</p>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-500 hover:bg-purple-400 text-white text-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          创建班级
        </button>
      </div>

      {/* 创建表单 */}
      <AnimatePresence>
        {showCreate && (
          <CreateClassForm
            onClose={() => setShowCreate(false)}
            onCreated={() => { setShowCreate(false); load(); }}
            onToast={showToast}
          />
        )}
      </AnimatePresence>

      {/* 班级列表 */}
      {loading ? (
        <div className="text-white/30 text-sm py-12 text-center">加载中...</div>
      ) : classes.length === 0 && !showCreate ? (
        <div className="text-center py-16">
          <Users className="w-12 h-12 text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm">暂无班级</p>
          <p className="text-white/20 text-xs mt-1">点击「创建班级」开始</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {classes.map((cls: any) => (
            <ClassCard
              key={cls.id}
              data={cls}
              onClick={() => setSelectedClass(cls)}
              onToast={showToast}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ── 创建表单 ── */
function CreateClassForm({
  onClose, onCreated, onToast,
}: {
  onClose: () => void;
  onCreated: () => void;
  onToast: (type: 'ok' | 'err', msg: string) => void;
}) {
  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [gradeLevel, setGradeLevel] = useState('');
  const [semester, setSemester] = useState('');
  const [description, setDescription] = useState('');
  const [maxStudents, setMaxStudents] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { onToast('err', '请输入班级名称'); return; }
    setSubmitting(true);
    try {
      const res: any = await api.createClass({
        name: name.trim(),
        subject: subject.trim(),
        grade_level: gradeLevel.trim(),
        semester: semester.trim(),
        description: description.trim(),
        max_students: maxStudents ? parseInt(maxStudents) : null,
      });
      if (res.success) {
        onToast('ok', `班级「${name}」创建成功，邀请码: ${res.data?.invite_code}`);
        onCreated();
      } else {
        onToast('err', res.message || '创建失败');
      }
    } catch {
      onToast('err', '网络错误');
    }
    finally { setSubmitting(false); }
  };

  return (
    <motion.form
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      onSubmit={submit}
      className="rounded-xl border border-purple-400/20 bg-purple-500/5 p-5 space-y-3"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-white/70 text-sm font-medium">新建班级</h3>
        <button type="button" onClick={onClose} className="text-white/30 hover:text-white/60">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-white/35 mb-1">班级名称 *</label>
          <input
            type="text" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="如: 高一(3)班"
            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm placeholder:text-white/20 focus:border-purple-400/40 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-white/35 mb-1">学科</label>
          <input
            type="text" value={subject} onChange={(e) => setSubject(e.target.value)}
            placeholder="如: 数学"
            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm placeholder:text-white/20 focus:border-purple-400/40 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-white/35 mb-1">年级</label>
          <input
            type="text" value={gradeLevel} onChange={(e) => setGradeLevel(e.target.value)}
            placeholder="如: 高一"
            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm placeholder:text-white/20 focus:border-purple-400/40 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-white/35 mb-1">学期</label>
          <input
            type="text" value={semester} onChange={(e) => setSemester(e.target.value)}
            placeholder="如: 2026春"
            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm placeholder:text-white/20 focus:border-purple-400/40 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-white/35 mb-1">人数上限（可选）</label>
          <input
            type="number" value={maxStudents} onChange={(e) => setMaxStudents(e.target.value)}
            placeholder="不限"
            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm placeholder:text-white/20 focus:border-purple-400/40 outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-white/35 mb-1">备注</label>
          <input
            type="text" value={description} onChange={(e) => setDescription(e.target.value)}
            placeholder="选填"
            className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white text-sm placeholder:text-white/20 focus:border-purple-400/40 outline-none"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <button
          type="button" onClick={onClose}
          className="px-4 py-2 rounded-lg text-white/40 text-sm hover:text-white/60 hover:bg-white/[0.03] transition-colors"
        >
          取消
        </button>
        <button
          type="submit" disabled={submitting}
          className="px-5 py-2 rounded-lg bg-purple-500 hover:bg-purple-400 text-white text-sm disabled:opacity-40 transition-colors"
        >
          {submitting ? '创建中...' : '创建班级'}
        </button>
      </div>
    </motion.form>
  );
}

/* ── 班级卡片 ── */
function ClassCard({ data, onClick, onToast }: {
  data: any; onClick: () => void; onToast: (t: 'ok' | 'err', m: string) => void;
}) {
  return (
    <div
      onClick={onClick}
      className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-purple-400/20 hover:bg-white/[0.04] transition-all cursor-pointer"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-medium">{data.name}</h3>
        <span className={`text-[10px] px-2 py-0.5 rounded-full ${data.is_open ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-300'}`}>
          {data.is_open ? '开放加入' : '已关闭'}
        </span>
      </div>
      <div className="space-y-1.5 text-xs text-white/40">
        <p>学科: {data.subject || '未设置'}</p>
        <p>邀请码: <span className="font-mono text-cyan-300">{data.invite_code}</span></p>
        <p>学生: {data.student_count || 0} / {data.max_students || '不限'}</p>
        {data.created_at && <p className="text-white/20">创建于 {data.created_at}</p>}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   班级详情 — 邀请码 + 学生名单 + 操作
   ═══════════════════════════════════════════ */
function ClassDetail({ classData, onBack, onToast }: {
  classData: any; onBack: () => void; onToast: (t: 'ok' | 'err', m: string) => void;
}) {
  const [cls, setCls] = useState(classData);
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [confirmRemove, setConfirmRemove] = useState<any>(null);

  const loadStudents = useCallback(async () => {
    try {
      const res: any = await api.listClassStudents(cls.id);
      if (res.success) setStudents(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, [cls.id]);

  useEffect(() => { loadStudents(); }, [loadStudents]);

  const copyCode = () => {
    navigator.clipboard.writeText(cls.invite_code).then(() => {
      onToast('ok', '邀请码已复制到剪贴板');
    }).catch(() => onToast('err', '复制失败'));
  };

  const resetCode = async () => {
    try {
      const res: any = await api.resetInviteCode(cls.id);
      if (res.success) {
        setCls({ ...cls, invite_code: res.data.invite_code });
        onToast('ok', `邀请码已重置为: ${res.data.invite_code}`);
      }
    } catch { onToast('err', '重置失败'); }
  };

  const toggleOpen = async () => {
    try {
      const res: any = cls.is_open ? await api.closeClass(cls.id) : await api.openClass(cls.id);
      if (res.success) {
        setCls({ ...cls, is_open: cls.is_open ? 0 : 1 });
        onToast('ok', cls.is_open ? '已关闭入班' : '已开启入班');
      }
    } catch { onToast('err', '操作失败'); }
  };

  const removeStudent = async (student: any) => {
    try {
      const res: any = await api.removeClassStudent(cls.id, student.id);
      if (res.success) {
        setStudents(students.filter(s => s.id !== student.id));
        onToast('ok', `已移除 ${student.username}`);
      }
    } catch { onToast('err', '移除失败'); }
    finally { setConfirmRemove(null); }
  };

  return (
    <div className="space-y-5">
      {/* 返回 */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-white/40 hover:text-white text-sm transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        返回班级列表
      </button>

      {/* 邀请码面板 */}
      <div className="rounded-xl border border-cyan-400/20 bg-cyan-500/5 p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-white/70 text-sm font-medium flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-cyan-400" />
            班级邀请码
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleOpen}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                cls.is_open
                  ? 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25'
                  : 'bg-red-500/15 text-red-300 hover:bg-red-500/25'
              }`}
            >
              {cls.is_open ? <Unlock className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
              {cls.is_open ? '开放加入' : '已关闭'}
            </button>
            <button
              onClick={resetCode}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-white/[0.05] text-white/50 hover:text-white/70 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              重置
            </button>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-white/[0.05] rounded-lg px-4 py-3 text-center">
            <p className="text-2xl font-mono text-cyan-300 tracking-[0.3em]">{cls.invite_code}</p>
          </div>
          <button
            onClick={copyCode}
            className="flex items-center gap-1.5 px-4 py-3 rounded-lg bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 text-sm transition-colors"
          >
            <Copy className="w-4 h-4" />
            复制
          </button>
        </div>
        <p className="text-white/25 text-xs mt-2">学生在「我的班级」中输入此邀请码即可加入</p>
      </div>

      {/* 班级信息 */}
      <div className="grid grid-cols-4 gap-3">
        <InfoBox label="学科" value={cls.subject || '-'} />
        <InfoBox label="年级" value={cls.grade_level || '-'} />
        <InfoBox label="人数上限" value={cls.max_students || '不限'} />
        <InfoBox label="当前学生" value={students.length} />
      </div>

      {/* 学生名单 */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white/70 text-sm font-medium flex items-center gap-2">
            <Users className="w-4 h-4 text-purple-400" />
            学生名单（{students.length}）
          </h3>
        </div>

        {loading ? (
          <div className="text-white/30 text-sm py-8 text-center">加载中...</div>
        ) : students.length === 0 ? (
          <div className="text-white/30 text-sm py-8 text-center">
            暂无学生，分享邀请码让学生加入
          </div>
        ) : (
          <div className="space-y-1">
            {/* 表头 */}
            <div className="grid grid-cols-12 px-3 py-2 text-white/30 text-xs border-b border-white/[0.05]">
              <div className="col-span-4">学生</div>
              <div className="col-span-3">邮箱</div>
              <div className="col-span-3">加入时间</div>
              <div className="col-span-2 text-right">操作</div>
            </div>
            {/* 行 */}
            {students.map((s: any) => (
              <div key={s.id} className="grid grid-cols-12 px-3 py-2.5 rounded-lg hover:bg-white/[0.03] transition-colors items-center">
                <div className="col-span-4 flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-purple-500/15 flex items-center justify-center">
                    <span className="text-purple-300 text-xs">{s.username.charAt(0).toUpperCase()}</span>
                  </div>
                  <span className="text-white/70 text-sm">{s.username}</span>
                </div>
                <div className="col-span-3 text-white/30 text-xs truncate">{s.email || '-'}</div>
                <div className="col-span-3 text-white/25 text-xs">{s.joined_at?.slice(0, 10) || '-'}</div>
                <div className="col-span-2 text-right">
                  <button
                    onClick={() => setConfirmRemove(s)}
                    className="p-1.5 rounded-lg text-white/20 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                    title="移除学生"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 移除确认弹窗 */}
      <AnimatePresence>
        {confirmRemove && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setConfirmRemove(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-[#1a1a2e] rounded-xl border border-white/[0.08] p-6 max-w-sm w-full mx-4"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-500/15 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <h3 className="text-white font-medium">确认移除</h3>
                  <p className="text-white/40 text-xs">此操作不可撤销</p>
                </div>
              </div>
              <p className="text-white/60 text-sm mb-5">
                确定要将 <span className="text-white font-medium">{confirmRemove.username}</span> 从班级「{cls.name}」移除吗？
              </p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setConfirmRemove(null)}
                  className="px-4 py-2 rounded-lg text-white/40 text-sm hover:text-white/60 hover:bg-white/[0.05] transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => removeStudent(confirmRemove)}
                  className="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-400 text-white text-sm transition-colors"
                >
                  确认移除
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function InfoBox({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-white/[0.03] p-3 text-center">
      <p className="text-white/70 text-sm">{value}</p>
      <p className="text-white/30 text-[10px] mt-1">{label}</p>
    </div>
  );
}
