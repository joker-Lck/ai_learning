'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Users, Plus, LogIn, LogOut, Share2, MessageSquare,
  BarChart3, Copy, Check, Loader2, Search, Star, Activity,
  ArrowRight, Database, Upload, TrendingUp, BookOpen, Trophy,
} from 'lucide-react';

interface Group {
  id: number;
  name: string;
  description: string;
  invite_code: string;
  subject: string;
  member_count: number;
  role?: string;
  created_at?: string;
}

interface GroupMember {
  user_id: number;
  role: string;
  joined_at: string;
}

interface SharedResource {
  id: number;
  resource_id: number;
  resource_type: string;
  shared_by: number;
  shared_at: string;
}

interface ActivityItem {
  id: number;
  user_id: number;
  activity_type: string;
  content: string;
  created_at: string;
}

interface MemberStats {
  user_id: number;
  role: string;
  resource_count: number;
  activity_count: number;
}

type Tab = 'groups' | 'detail' | 'create' | 'join';

export default function CollaborationModule() {
  const [tab, setTab] = useState<Tab>('groups');
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [sharedResources, setSharedResources] = useState<SharedResource[]>([]);
  const [copied, setCopied] = useState(false);
  const [memberStats, setMemberStats] = useState<MemberStats[]>([]);
  const [uploading, setUploading] = useState(false);

  // Create group form
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newSubject, setNewSubject] = useState('');

  // Join form
  const [inviteCode, setInviteCode] = useState('');

  const API = '/api/collaboration';
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : '';
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const fetchGroups = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/my-groups`, { headers });
      const data = await res.json();
      if (data.success) setGroups(data.data || []);
    } catch (e) {
      console.error('获取小组失败:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchGroups(); }, [fetchGroups]);

  const fetchGroupDetail = async (groupId: number) => {
    try {
      const res = await fetch(`${API}/group/${groupId}`, { headers });
      const data = await res.json();
      if (data.success && data.data) {
        setSelectedGroup(data.data);
        setMembers(data.data.members || []);
        setTab('detail');
        fetchActivities(groupId);
        fetchSharedResources(groupId);
        fetchLearningStats(groupId);
      }
    } catch (e) {
      console.error('获取小组详情失败:', e);
    }
  };

  const fetchActivities = async (groupId: number) => {
    try {
      const res = await fetch(`${API}/activities/${groupId}`, { headers });
      const data = await res.json();
      if (data.success) setActivities(data.data || []);
    } catch {}
  };

  const fetchSharedResources = async (groupId: number) => {
    try {
      const res = await fetch(`${API}/shared-resources/${groupId}`, { headers });
      const data = await res.json();
      if (data.success) setSharedResources(data.data || []);
    } catch {}
  };

  const fetchLearningStats = async (groupId: number) => {
    try {
      const res = await fetch(`${API}/learning-stats/${groupId}`, { headers });
      const data = await res.json();
      if (data.success) setMemberStats(data.data?.members || []);
    } catch {}
  };

  const handleUploadResource = async (file: File) => {
    if (!selectedGroup) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const uploadHeaders = { 'Authorization': `Bearer ${token}` };
      const uploadRes = await fetch('/api/agent/upload-to-rag', {
        method: 'POST', headers: uploadHeaders, body: formData,
      });
      const uploadData = await uploadRes.json();
      if (uploadData.success) {
        const results = uploadData.data?.results || [];
        const docId = results[0]?.doc_id;
        if (docId) {
          await fetch(`${API}/share-resource`, {
            method: 'POST', headers,
            body: JSON.stringify({ group_id: selectedGroup.id, resource_id: docId, resource_type: 'document' }),
          });
          fetchSharedResources(selectedGroup.id);
          fetchActivities(selectedGroup.id);
        }
      }
    } catch (e) {
      console.error('上传失败:', e);
    } finally {
      setUploading(false);
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/create-group`, {
        method: 'POST', headers,
        body: JSON.stringify({ name: newName, description: newDesc, subject: newSubject }),
      });
      const data = await res.json();
      if (data.success) {
        setNewName(''); setNewDesc(''); setNewSubject('');
        fetchGroups();
        setTab('groups');
      } else {
        alert(data.message || '创建失败');
      }
    } catch {
      alert('创建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!inviteCode.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/join-group`, {
        method: 'POST', headers,
        body: JSON.stringify({ invite_code: inviteCode.trim() }),
      });
      const data = await res.json();
      if (data.success) {
        setInviteCode('');
        fetchGroups();
        setTab('groups');
        alert(`成功加入「${data.data?.group_name || '小组'}」`);
      } else {
        alert(data.message || '加入失败');
      }
    } catch {
      alert('加入失败');
    } finally {
      setLoading(false);
    }
  };

  const handleLeave = async (groupId: number) => {
    if (!confirm('确定要退出该小组吗？')) return;
    try {
      await fetch(`${API}/leave-group`, {
        method: 'POST', headers,
        body: JSON.stringify({ group_id: groupId }),
      });
      fetchGroups();
      setTab('groups');
      setSelectedGroup(null);
    } catch {}
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const activityIcon = (type: string) => {
    switch (type) {
      case 'group_created': return <Plus className="w-4 h-4 text-green-400" />;
      case 'member_joined': return <LogIn className="w-4 h-4 text-blue-400" />;
      case 'resource_shared': return <Share2 className="w-4 h-4 text-purple-400" />;
      case 'peer_review': return <Star className="w-4 h-4 text-yellow-400" />;
      default: return <Activity className="w-4 h-4 text-white/40" />;
    }
  };

  // ── 小组列表 ──
  const renderGroups = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-white">我的学习小组</h3>
        <div className="flex gap-3">
          <button onClick={() => setTab('join')}
            className="px-4 py-2 glass text-white/70 rounded-lg hover:text-white hover:bg-white/10 flex items-center gap-2 text-sm transition-colors">
            <LogIn className="w-4 h-4" /> 加入小组
          </button>
          <button onClick={() => setTab('create')}
            className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-400 flex items-center gap-2 text-sm transition-colors">
            <Plus className="w-4 h-4" /> 创建小组
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
        </div>
      ) : groups.length === 0 ? (
        <div className="text-center py-20">
          <Users className="w-16 h-16 text-white/10 mx-auto mb-4" />
          <p className="text-white/40 text-lg mb-2">还没有加入任何小组</p>
          <p className="text-white/25 text-sm">创建或加入一个小组，和同学一起学习吧</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map(g => (
            <div key={g.id}
              className="glass rounded-xl p-5 cursor-pointer hover:border-purple-500/30 transition-all hover:scale-[1.02]"
              onClick={() => fetchGroupDetail(g.id)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Users className="w-5 h-5 text-purple-400" />
                </div>
                {g.role === 'admin' && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">组长</span>
                )}
              </div>
              <h4 className="text-white font-medium mb-1 truncate">{g.name}</h4>
              <p className="text-white/40 text-sm mb-3 line-clamp-2">{g.description || '暂无描述'}</p>
              <div className="flex items-center justify-between text-xs text-white/30">
                <span>{g.subject}</span>
                <span>{g.member_count || 0} 人</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // ── 创建小组 ──
  const renderCreate = () => (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => setTab('groups')} className="text-white/40 hover:text-white">
          <ArrowRight className="w-5 h-5 rotate-180" />
        </button>
        <h3 className="text-2xl font-bold text-white">创建学习小组</h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-white/50 mb-1.5">小组名称 *</label>
          <input value={newName} onChange={e => setNewName(e.target.value)}
            placeholder="如：机器学习学习小组"
            className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg" />
        </div>
        <div>
          <label className="block text-sm text-white/50 mb-1.5">学科</label>
          <input value={newSubject} onChange={e => setNewSubject(e.target.value)}
            placeholder="如：人工智能"
            className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg" />
        </div>
        <div>
          <label className="block text-sm text-white/50 mb-1.5">描述</label>
          <textarea value={newDesc} onChange={e => setNewDesc(e.target.value)}
            placeholder="小组介绍..."
            rows={3}
            className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg resize-none" />
        </div>
        <button onClick={handleCreate} disabled={loading || !newName.trim()}
          className="w-full py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          创建小组
        </button>
      </div>
    </div>
  );

  // ── 加入小组 ──
  const renderJoin = () => (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => setTab('groups')} className="text-white/40 hover:text-white">
          <ArrowRight className="w-5 h-5 rotate-180" />
        </button>
        <h3 className="text-2xl font-bold text-white">加入学习小组</h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-white/50 mb-1.5">邀请码</label>
          <input value={inviteCode} onChange={e => setInviteCode(e.target.value.toUpperCase())}
            placeholder="输入 8 位邀请码"
            maxLength={8}
            className="w-full px-4 py-3 glass-input text-white placeholder:text-white/20 rounded-lg text-center text-2xl tracking-[0.3em] font-mono" />
        </div>
        <button onClick={handleJoin} disabled={loading || inviteCode.length < 6}
          className="w-full py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-400 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
          加入小组
        </button>
      </div>
    </div>
  );

  // ── 小组详情 ──
  const renderDetail = () => {
    if (!selectedGroup) return null;
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-2">
          <button onClick={() => { setTab('groups'); setSelectedGroup(null); }}
            className="text-white/40 hover:text-white">
            <ArrowRight className="w-5 h-5 rotate-180" />
          </button>
          <h3 className="text-2xl font-bold text-white flex-1">{selectedGroup.name}</h3>
          <button onClick={() => handleLeave(selectedGroup.id)}
            className="px-3 py-1.5 text-sm text-red-400/70 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
            退出小组
          </button>
        </div>

        {/* 邀请码 */}
        <div className="glass rounded-xl p-4 flex items-center justify-between">
          <div>
            <span className="text-white/50 text-sm">邀请码</span>
            <span className="text-white ml-3 font-mono text-lg tracking-[0.2em]">{selectedGroup.invite_code}</span>
          </div>
          <button onClick={() => copyCode(selectedGroup.invite_code)}
            className="px-3 py-1.5 glass rounded-lg text-white/60 hover:text-white flex items-center gap-1.5 text-sm transition-colors">
            {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            {copied ? '已复制' : '复制'}
          </button>
        </div>

        {/* 成员 + 动态 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* 成员列表 */}
          <div className="glass rounded-xl p-5">
            <h4 className="text-white font-medium mb-3 flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" /> 成员 ({members.length})
            </h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {members.map((m, i) => (
                <div key={i} className="flex items-center justify-between py-1.5">
                  <span className="text-white/70 text-sm">用户 #{m.user_id}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    m.role === 'admin' ? 'bg-amber-500/20 text-amber-300' : 'bg-white/10 text-white/40'
                  }`}>
                    {m.role === 'admin' ? '组长' : '成员'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 学习动态 */}
          <div className="glass rounded-xl p-5">
            <h4 className="text-white font-medium mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" /> 学习动态
            </h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {activities.length === 0 ? (
                <p className="text-white/30 text-sm text-center py-4">暂无动态</p>
              ) : activities.map((a, i) => (
                <div key={i} className="flex items-start gap-2 py-1.5">
                  {activityIcon(a.activity_type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-white/70 text-sm truncate">{a.content}</p>
                    <p className="text-white/25 text-xs">{new Date(a.created_at).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 共享资源 */}
        <div className="glass rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-white font-medium flex items-center gap-2">
              <Share2 className="w-4 h-4 text-green-400" /> 共享资源 ({sharedResources.length})
            </h4>
            <label className="px-3 py-1.5 bg-purple-500/20 text-purple-400 rounded-lg text-sm hover:bg-purple-500/30 cursor-pointer flex items-center gap-1.5 transition-colors">
              {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              {uploading ? '上传中...' : '上传文件'}
              <input type="file" className="hidden" accept=".txt,.md,.pdf,.doc,.docx,.ppt,.pptx"
                onChange={e => { const f = e.target.files?.[0]; if (f) handleUploadResource(f); e.target.value = ''; }} />
            </label>
          </div>
          {sharedResources.length === 0 ? (
            <p className="text-white/30 text-sm text-center py-4">暂无共享资源，点击上方按钮上传</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {sharedResources.map((r, i) => (
                <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/5">
                  <Database className="w-4 h-4 text-white/30" />
                  <span className="text-white/60 text-sm">资源 #{r.resource_id}</span>
                  <span className="text-white/25 text-xs ml-auto">{r.resource_type}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 成员学习对比 */}
        {memberStats.length > 0 && (
          <div className="glass rounded-xl p-5">
            <h4 className="text-white font-medium mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-amber-400" /> 学习进度对比
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {memberStats.map((s, i) => {
                const maxRes = Math.max(...memberStats.map(m => m.resource_count), 1);
                const maxAct = Math.max(...memberStats.map(m => m.activity_count), 1);
                return (
                  <div key={i} className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                        <Users className="w-4 h-4 text-purple-400" />
                      </div>
                      <div>
                        <span className="text-white/80 text-sm font-medium">用户 #{s.user_id}</span>
                        {s.role === 'admin' && <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">组长</span>}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-white/40 flex items-center gap-1"><BookOpen className="w-3 h-3" /> 生成资源</span>
                          <span className="text-white/60">{s.resource_count}</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-white/[0.06]">
                          <div className="h-full rounded-full bg-purple-500 transition-all" style={{ width: `${(s.resource_count / maxRes) * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-white/40 flex items-center gap-1"><Activity className="w-3 h-3" /> 学习活动</span>
                          <span className="text-white/60">{s.activity_count}</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-white/[0.06]">
                          <div className="h-full rounded-full bg-cyan-500 transition-all" style={{ width: `${(s.activity_count / maxAct) * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-8">
      <h3 className="text-3xl font-bold text-white">协同学习</h3>
      {tab === 'groups' && renderGroups()}
      {tab === 'create' && renderCreate()}
      {tab === 'join' && renderJoin()}
      {tab === 'detail' && renderDetail()}
    </div>
  );
}
