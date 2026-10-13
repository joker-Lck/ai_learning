'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, LogOut, UserPlus, Copy, CheckCircle, AlertTriangle,
  GraduationCap, School,
} from 'lucide-react';
import api from '@/lib/api';

/* ═══════════════════════════════════════════
   我的班级 — 学生侧：加入 / 查看 / 退出
   ═══════════════════════════════════════════ */
export default function MyClassView() {
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [joinCode, setJoinCode] = useState('');
  const [joining, setJoining] = useState(false);
  const [toast, setToast] = useState<{ type: 'ok' | 'err'; msg: string } | null>(null);
  const [confirmLeave, setConfirmLeave] = useState<any>(null);

  const showToast = (type: 'ok' | 'err', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 2500);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await api.myClasses();
      if (res.success) setClasses(res.data || []);
    } catch {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const join = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = joinCode.trim().toUpperCase();
    if (code.length !== 6) {
      showToast('err', '邀请码为 6 位字母数字组合');
      return;
    }
    setJoining(true);
    try {
      const res: any = await api.joinClass(code);
      if (res.success) {
        showToast('ok', res.message || '加入成功');
        setJoinCode('');
        load();
      } else {
        showToast('err', res.message || res.error || '加入失败');
      }
    } catch {
      showToast('err', '网络错误');
    }
    finally { setJoining(false); }
  };

  const leave = async (cls: any) => {
    try {
      const res: any = await api.leaveClass(cls.id);
      if (res.success) {
        showToast('ok', `已退出「${cls.name}」`);
        load();
      } else {
        showToast('err', res.message || '操作失败');
      }
    } catch {
      showToast('err', '网络错误');
    }
    finally { setConfirmLeave(null); }
  };

  return (
    <div className="space-y-5">
      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className={`px-4 py-2.5 rounded-lg text-sm flex items-center gap-2 ${
              toast.type === 'ok'
                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-400/20'
                : 'bg-red-500/15 text-red-300 border border-red-400/20'
            }`}
          >
            {toast.type === 'ok' ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 加入班级 */}
      <div className="rounded-xl border border-cyan-400/20 bg-cyan-500/5 p-5">
        <h3 className="text-white/70 text-sm font-medium flex items-center gap-2 mb-3">
          <UserPlus className="w-4 h-4 text-cyan-400" />
          加入班级
        </h3>
        <form onSubmit={join} className="flex gap-2">
          <input
            type="text"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            placeholder="输入 6 位邀请码"
            maxLength={6}
            className="flex-1 px-4 py-2.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-white text-center text-lg font-mono tracking-[0.3em] placeholder:text-white/15 placeholder:tracking-normal placeholder:font-sans placeholder:text-sm focus:border-cyan-400/40 outline-none"
          />
          <button
            type="submit"
            disabled={joining || joinCode.length !== 6}
            className="px-5 py-2.5 rounded-lg bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 text-sm font-medium disabled:opacity-30 transition-colors whitespace-nowrap"
          >
            {joining ? '加入中...' : '加入'}
          </button>
        </form>
        <p className="text-white/25 text-xs mt-2">向老师获取班级邀请码后输入即可加入</p>
      </div>

      {/* 我的班级列表 */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-white/70 text-sm font-medium flex items-center gap-2">
            <School className="w-4 h-4 text-purple-400" />
            我的班级（{classes.length}）
          </h3>
        </div>

        {loading ? (
          <div className="text-white/30 text-sm py-8 text-center">加载中...</div>
        ) : classes.length === 0 ? (
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] py-12 text-center">
            <Users className="w-10 h-10 text-white/10 mx-auto mb-3" />
            <p className="text-white/30 text-sm">尚未加入任何班级</p>
            <p className="text-white/20 text-xs mt-1">使用上方邀请码加入班级</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {classes.map((cls: any) => (
              <motion.div
                key={cls.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-purple-500/15 flex items-center justify-center">
                      <GraduationCap className="w-4 h-4 text-purple-400" />
                    </div>
                    <div>
                      <p className="text-white/70 text-sm font-medium">{cls.name}</p>
                      <p className="text-white/30 text-xs">{cls.subject || '综合'}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setConfirmLeave(cls)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs text-white/25 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                  >
                    <LogOut className="w-3 h-3" />
                    退出
                  </button>
                </div>
                <div className="space-y-1 text-xs text-white/35">
                  <p>老师: {cls.teacher_name || '-'}</p>
                  {cls.joined_at && <p>加入于: {cls.joined_at}</p>}
                  {cls.grade_level && <p>年级: {cls.grade_level}</p>}
                  {cls.semester && <p>学期: {cls.semester}</p>}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* 退出确认弹窗 */}
      <AnimatePresence>
        {confirmLeave && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setConfirmLeave(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-[#1a1a2e] rounded-xl border border-white/[0.08] p-6 max-w-sm w-full mx-4"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-amber-500/15 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="text-white font-medium">确认退出</h3>
                  <p className="text-white/40 text-xs">退出后可重新加入</p>
                </div>
              </div>
              <p className="text-white/60 text-sm mb-5">
                确定要退出班级「{confirmLeave.name}」吗？
              </p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setConfirmLeave(null)}
                  className="px-4 py-2 rounded-lg text-white/40 text-sm hover:text-white/60 hover:bg-white/[0.05] transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={() => leave(confirmLeave)}
                  className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-white text-sm transition-colors"
                >
                  确认退出
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
