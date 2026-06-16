"""
流式输出与进度追踪服务
提供SSE实时推送和生成进度管理
"""

import json
import asyncio
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
from core.logger import info, error

# 可配置的延迟常量（秒）
STREAM_DELAY_SHORT = 0.1    # 短延迟（步骤间）
STREAM_DELAY_MEDIUM = 0.3   # 中延迟（进度更新）
STREAM_DELAY_LONG = 0.5     # 长延迟（模拟生成）


class ProgressTracker:
    """进度追踪器 - 管理任务生成进度"""
    
    def __init__(self):
        # 存储所有任务的进度 {task_id: progress_data}
        self.tasks = {}
        info("进度追踪器初始化完成")
    
    def create_task(self, task_id: str, task_type: str, user_id: int, 
                   total_steps: int = 100) -> Dict:
        """创建新任务"""
        # 定期清理过期任务
        if len(self.tasks) > 100:
            self.cleanup_old_tasks()

        task_data = {
            "task_id": task_id,
            "task_type": task_type,
            "user_id": user_id,
            "status": "pending",  # pending/running/completed/failed
            "progress": 0,  # 0-100
            "total_steps": total_steps,
            "current_step": 0,
            "steps": [],
            "message": "任务已创建",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        self.tasks[task_id] = task_data
        info(f"创建任务: {task_id}, 类型: {task_type}")
        
        return task_data
    
    def update_progress(self, task_id: str, progress: int, 
                       current_step: str = "", message: str = "") -> Dict:
        """更新任务进度"""
        if task_id not in self.tasks:
            error(f"任务不存在: {task_id}")
            return None
        
        task = self.tasks[task_id]
        task["progress"] = min(max(progress, 0), 100)
        task["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if current_step:
            task["current_step"] = current_step
            task["steps"].append({
                "step": current_step,
                "progress": progress,
                "timestamp": task["updated_at"]
            })
        
        if message:
            task["message"] = message
        
        return task
    
    def complete_task(self, task_id: str, result: Dict = None) -> Dict:
        """标记任务完成"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task["status"] = "completed"
        task["progress"] = 100
        task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task["result"] = result
        task["message"] = "任务完成"
        
        info(f"任务完成: {task_id}")
        return task
    
    def fail_task(self, task_id: str, error_message: str) -> Dict:
        """标记任务失败"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task["status"] = "failed"
        task["error"] = error_message
        task["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task["message"] = f"任务失败: {error_message}"
        
        error(f"任务失败: {task_id}, 错误: {error_message}")
        return task
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def get_user_tasks(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户的任务列表"""
        user_tasks = [
            task for task in self.tasks.values()
            if task["user_id"] == user_id
        ]
        
        # 按创建时间排序,返回最新的limit个
        user_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return user_tasks[:limit]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理过期任务"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            created_at = datetime.strptime(task["created_at"], "%Y-%m-%d %H:%M:%S")
            if created_at < cutoff_time:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            info(f"清理了 {len(tasks_to_remove)} 个过期任务")


class SSEStreamGenerator:
    """SSE流式生成器 - 实现Server-Sent Events"""
    
    def __init__(self):
        info("SSE流式生成器初始化完成")
    
    async def generate_resource_stream(self, 
                                      task_id: str,
                                      resource_type: str,
                                      subject: str,
                                      topic: str,
                                      profile: Dict) -> AsyncGenerator[str, None]:
        """
        流式生成学习资源
        
        Yields:
            SSE格式的数据
        """
        tracker = ProgressTracker()
        
        try:
            # Step 1: 创建任务
            tracker.create_task(task_id, f"generate_{resource_type}", 
                              profile.get("user_id", 0), total_steps=5)
            
            yield self._format_sse({
                "type": "progress",
                "task_id": task_id,
                "progress": 0,
                "message": "开始生成资源...",
                "step": "initializing"
            })
            
            await asyncio.sleep(STREAM_DELAY_MEDIUM)
            
            # Step 2: 分析需求
            tracker.update_progress(task_id, 20, "analyzing_requirements", "分析学习需求...")
            yield self._format_sse({
                "type": "progress",
                "task_id": task_id,
                "progress": 20,
                "message": "分析学习需求...",
                "step": "analyzing_requirements"
            })
            
            await asyncio.sleep(STREAM_DELAY_MEDIUM)
            
            # Step 3: 检索知识库
            tracker.update_progress(task_id, 40, "retrieving_knowledge", "检索相关知识...")
            yield self._format_sse({
                "type": "progress",
                "task_id": task_id,
                "progress": 40,
                "message": "检索相关知识...",
                "step": "retrieving_knowledge"
            })
            
            await asyncio.sleep(STREAM_DELAY_MEDIUM)
            
            # Step 4: 生成内容
            tracker.update_progress(task_id, 70, "generating_content", "生成内容...")
            yield self._format_sse({
                "type": "progress",
                "task_id": task_id,
                "progress": 70,
                "message": "生成内容...",
                "step": "generating_content"
            })
            
            await asyncio.sleep(STREAM_DELAY_LONG)
            
            # Step 5: 安全检查
            tracker.update_progress(task_id, 90, "safety_check", "内容安全检查...")
            yield self._format_sse({
                "type": "progress",
                "task_id": task_id,
                "progress": 90,
                "message": "内容安全检查...",
                "step": "safety_check"
            })
            
            await asyncio.sleep(STREAM_DELAY_SHORT)
            
            # Step 6: 完成
            result = {
                "resource_type": resource_type,
                "subject": subject,
                "topic": topic,
                "title": f"{topic}的{resource_type}",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            tracker.complete_task(task_id, result)
            yield self._format_sse({
                "type": "complete",
                "task_id": task_id,
                "progress": 100,
                "message": "生成完成!",
                "result": result
            })
            
        except Exception as e:
            tracker.fail_task(task_id, str(e))
            yield self._format_sse({
                "type": "error",
                "task_id": task_id,
                "error": str(e)
            })
    
    async def generate_text_stream(self, text_chunks: List[str]) -> AsyncGenerator[str, None]:
        """
        流式输出文本
        
        Args:
            text_chunks: 文本块列表
            
        Yields:
            SSE格式的文本块
        """
        for i, chunk in enumerate(text_chunks):
            yield self._format_sse({
                "type": "chunk",
                "index": i,
                "content": chunk
            })
            await asyncio.sleep(STREAM_DELAY_SHORT)
        
        yield self._format_sse({
            "type": "done",
            "message": "输出完成"
        })
    
    def _format_sse(self, data: Dict) -> str:
        """格式化SSE数据"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# 全局实例
progress_tracker = ProgressTracker()
sse_generator = SSEStreamGenerator()
