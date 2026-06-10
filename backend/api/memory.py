"""
记忆系统 API 路由
提供记忆管理、查询、统计等接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
from backend.dependencies import get_current_user, require_auth
from services.memory_service import memory_service
from services.memory_extractor import memory_extractor
from core.logger import info, error

router = APIRouter(prefix="/memory", tags=["记忆系统"])


class BaseResponse:
    """统一响应格式"""
    def __init__(self, success: bool, message: str, data: Any = None):
        self.success = success
        self.message = message
        self.data = data


# ==========================================
# 短期记忆
# ==========================================

@router.get("/short-term/{session_id}")
async def get_short_term_context(
    session_id: str,
    max_tokens: int = Query(4000, ge=100, le=32000),
    user: dict = Depends(get_current_user)
):
    """获取短期记忆上下文"""
    try:
        with memory_service as ms:
            context = ms.get_short_term_context(user['id'], session_id, max_tokens)
            return {"success": True, "data": {"context": context, "count": len(context)}}
    except Exception as e:
        error(f"获取短期记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/short-term")
async def add_short_term_memory(
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """添加短期记忆"""
    try:
        session_id = data.get('session_id')
        role = data.get('role', 'user')
        content = data.get('content')
        
        if not session_id or not content:
            raise HTTPException(status_code=400, detail="缺少必要参数")
            
        with memory_service as ms:
            memory_id = ms.add_short_term(user['id'], session_id, role, content)
            return {"success": True, "data": {"memory_id": memory_id}}
    except HTTPException:
        raise
    except Exception as e:
        error(f"添加短期记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 情景记忆
# ==========================================

@router.get("/episodic/search")
async def search_episodic_memory(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """搜索情景记忆"""
    try:
        with memory_service as ms:
            results = ms.search_episodic(user['id'], query, limit)
            return {"success": True, "data": {"memories": results, "count": len(results)}}
    except Exception as e:
        error(f"搜索情景记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodic/recent")
async def get_recent_episodes(
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """获取最近的情景记忆"""
    try:
        with memory_service as ms:
            results = ms.get_recent_episodes(user['id'], limit)
            return {"success": True, "data": {"episodes": results, "count": len(results)}}
    except Exception as e:
        error(f"获取最近情景记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/episodic")
async def add_episodic_memory(
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """添加情景记忆"""
    try:
        episode_type = data.get('episode_type', 'conversation')
        title = data.get('title', '')
        summary = data.get('summary', '')
        content = data.get('content', '')
        context = data.get('context')
        emotions = data.get('emotions')
        importance = data.get('importance', 0.5)
        
        with memory_service as ms:
            memory_id = ms.add_episodic(
                user['id'], episode_type, title, summary, content, 
                context, emotions, importance
            )
            return {"success": True, "data": {"memory_id": memory_id}}
    except Exception as e:
        error(f"添加情景记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 语义记忆（事实知识）
# ==========================================

@router.get("/semantic/search")
async def search_semantic_memory(
    query: str = Query(..., min_length=1),
    fact_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """搜索语义记忆"""
    try:
        with memory_service as ms:
            results = ms.search_semantic(user['id'], query, fact_type, limit)
            return {"success": True, "data": {"facts": results, "count": len(results)}}
    except Exception as e:
        error(f"搜索语义记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic/subject/{subject}")
async def get_facts_by_subject(
    subject: str,
    user: dict = Depends(get_current_user)
):
    """获取某个主题的所有事实"""
    try:
        with memory_service as ms:
            results = ms.get_facts_by_subject(user['id'], subject)
            return {"success": True, "data": {"facts": results, "count": len(results)}}
    except Exception as e:
        error(f"获取主题事实失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semantic")
async def add_semantic_memory(
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """添加语义记忆（事实知识）"""
    try:
        fact_type = data.get('fact_type', 'knowledge')
        subject = data.get('subject')
        predicate = data.get('predicate')
        object_val = data.get('object')
        confidence = data.get('confidence', 0.8)
        source = data.get('source', '')
        
        if not subject or not predicate or not object_val:
            raise HTTPException(status_code=400, detail="缺少必要参数")
            
        with memory_service as ms:
            memory_id = ms.add_semantic(
                user['id'], fact_type, subject, predicate, object_val, confidence, source
            )
            return {"success": True, "data": {"memory_id": memory_id}}
    except HTTPException:
        raise
    except Exception as e:
        error(f"添加语义记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 实体记忆
# ==========================================

@router.get("/entity/search")
async def search_entities(
    query: str = Query(..., min_length=1),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """搜索实体"""
    try:
        with memory_service as ms:
            results = ms.search_entities(user['id'], query, entity_type, limit)
            return {"success": True, "data": {"entities": results, "count": len(results)}}
    except Exception as e:
        error(f"搜索实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_id}/relations")
async def get_entity_relations(
    entity_id: int,
    direction: str = Query('both', regex='^(in|out|both)$'),
    user: dict = Depends(get_current_user)
):
    """获取实体的关系"""
    try:
        with memory_service as ms:
            results = ms.get_entity_relations(user['id'], entity_id, direction)
            return {"success": True, "data": {"relations": results, "count": len(results)}}
    except Exception as e:
        error(f"获取实体关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_id}/graph")
async def get_entity_graph(
    entity_id: int,
    depth: int = Query(2, ge=1, le=4),
    user: dict = Depends(get_current_user)
):
    """获取实体图谱"""
    try:
        with memory_service as ms:
            graph = ms.get_entity_graph(user['id'], entity_id, depth)
            return {"success": True, "data": graph}
    except Exception as e:
        error(f"获取实体图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entity")
async def add_entity(
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """添加实体"""
    try:
        entity_type = data.get('entity_type', 'concept')
        entity_name = data.get('entity_name')
        attributes = data.get('attributes')
        description = data.get('description', '')
        entity_alias = data.get('entity_alias', '')
        importance = data.get('importance', 0.5)
        
        if not entity_name:
            raise HTTPException(status_code=400, detail="缺少实体名称")
            
        with memory_service as ms:
            entity_id = ms.add_entity(
                user['id'], entity_type, entity_name, attributes, description, entity_alias, importance
            )
            return {"success": True, "data": {"entity_id": entity_id}}
    except HTTPException:
        raise
    except Exception as e:
        error(f"添加实体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relation")
async def add_relation(
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """添加实体关系"""
    try:
        source_entity_id = data.get('source_entity_id')
        target_entity_id = data.get('target_entity_id')
        relation_type = data.get('relation_type')
        relation_label = data.get('relation_label', '')
        weight = data.get('weight', 1.0)
        context = data.get('context', '')
        
        if not source_entity_id or not target_entity_id or not relation_type:
            raise HTTPException(status_code=400, detail="缺少必要参数")
            
        with memory_service as ms:
            relation_id = ms.add_relation(
                user['id'], source_entity_id, target_entity_id,
                relation_type, relation_label, weight, context
            )
            return {"success": True, "data": {"relation_id": relation_id}}
    except HTTPException:
        raise
    except Exception as e:
        error(f"添加关系失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 遗忘与冲突
# ==========================================

@router.post("/forgetting/apply")
async def apply_forgetting_curve(
    user: dict = Depends(require_auth)
):
    """应用遗忘曲线"""
    try:
        with memory_service as ms:
            result = ms.apply_forgetting_curve(user['id'])
            return {"success": True, "data": result}
    except Exception as e:
        error(f"应用遗忘曲线失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reinforce")
async def reinforce_memory(
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """强化记忆"""
    try:
        memory_type = data.get('memory_type')
        memory_id = data.get('memory_id')
        boost = data.get('boost')
        
        if not memory_type or not memory_id:
            raise HTTPException(status_code=400, detail="缺少必要参数")
            
        with memory_service as ms:
            ms.reinforce_memory(memory_type, memory_id, user['id'], boost)
            return {"success": True, "message": "记忆已强化"}
    except HTTPException:
        raise
    except Exception as e:
        error(f"强化记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts")
async def get_pending_conflicts(
    user: dict = Depends(get_current_user)
):
    """获取待解决的冲突"""
    try:
        with memory_service as ms:
            conflicts = ms.get_pending_conflicts(user['id'])
            return {"success": True, "data": {"conflicts": conflicts, "count": len(conflicts)}}
    except Exception as e:
        error(f"获取冲突失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """解决冲突"""
    try:
        strategy = data.get('strategy')
        if strategy not in ('keep_old', 'keep_new', 'merge'):
            raise HTTPException(status_code=400, detail="无效的解决策略")
            
        with memory_service as ms:
            success = ms.resolve_conflict(conflict_id, strategy, user['id'])
            if success:
                return {"success": True, "message": "冲突已解决"}
            else:
                raise HTTPException(status_code=404, detail="冲突不存在或已解决")
    except HTTPException:
        raise
    except Exception as e:
        error(f"解决冲突失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 统计与清理
# ==========================================

@router.get("/stats")
async def get_memory_stats(
    user: dict = Depends(get_current_user)
):
    """获取记忆统计信息"""
    try:
        with memory_service as ms:
            stats = ms.get_memory_stats(user['id'])
            return {"success": True, "data": stats}
    except Exception as e:
        error(f"获取记忆统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_forgotten_memories(
    days: int = Query(30, ge=1, le=365),
    user: dict = Depends(require_auth)
):
    """清理遗忘记忆"""
    try:
        with memory_service as ms:
            deleted_count = ms.cleanup_forgotten_memories(user['id'], days)
            return {"success": True, "data": {"deleted_count": deleted_count}}
    except Exception as e:
        error(f"清理遗忘记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 记忆提取
# ==========================================

@router.post("/extract")
async def extract_memory_from_conversation(
    data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """从对话中提取记忆"""
    try:
        session_id = data.get('session_id')
        user_message = data.get('user_message')
        assistant_response = data.get('assistant_response')
        
        if not session_id or not user_message or not assistant_response:
            raise HTTPException(status_code=400, detail="缺少必要参数")
            
        from services.agent_coordinator import agent_coordinator
        kimi_client = agent_coordinator.kimi_client if hasattr(agent_coordinator, 'kimi_client') else None
        
        extractor = memory_extractor
        extractor.kimi_client = kimi_client
        
        results = extractor.extract_from_conversation(
            user['id'], session_id, user_message, assistant_response
        )
        
        return {"success": True, "data": results}
    except HTTPException:
        raise
    except Exception as e:
        error(f"提取记忆失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
