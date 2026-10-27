"""
SQLite → MySQL 迁移脚本

用法:
    python scripts/migrate_to_mysql.py            # 建库建表 + 导入 SQLite 数据
    python scripts/migrate_to_mysql.py --schema   # 仅建库建表
    python scripts/migrate_to_mysql.py --data     # 仅导入数据（表需已存在）
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

import pymysql

# ── 连接参数 ────────────────────────────────────────────
MYSQL = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "123456"),
    "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
}
SQLITE_DIR = Path(os.getenv("SQLITE_DB_DIR", str(BASE_DIR / "data" / "databases")))

# ── MySQL 建表语句（由 SQLite schema 转换而来） ──────────
# 规则:
#   INTEGER PRIMARY KEY AUTOINCREMENT → BIGINT AUTO_INCREMENT PRIMARY KEY
#   唯一约束里的 TEXT → VARCHAR(n)（MySQL 唯一键不能直接建在 TEXT 上）
#   JSON/正文 → LONGTEXT；短文本 → VARCHAR/TEXT
#   BLOB 向量 → LONGBLOB
#   datetime('now') → CURRENT_TIMESTAMP
#   FTS5 虚拟表 → 基表 FULLTEXT 索引

SCHEMA: dict[str, list[str]] = {
    "ai_auth": [
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            role VARCHAR(32) DEFAULT 'student',
            major VARCHAR(255),
            grade_level VARCHAR(64),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_users_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_sessions_token (token),
            KEY idx_sessions_user (user_id),
            CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS classes (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            teacher_id BIGINT NOT NULL,
            subject VARCHAR(255) DEFAULT '',
            grade_level VARCHAR(64) DEFAULT '',
            semester VARCHAR(64) DEFAULT '',
            invite_code VARCHAR(64) NOT NULL,
            is_open TINYINT DEFAULT 1,
            max_students INT DEFAULT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_classes_invite (invite_code),
            KEY idx_classes_teacher (teacher_id),
            CONSTRAINT fk_classes_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS class_students (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            class_id BIGINT NOT NULL,
            student_id BIGINT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(32) DEFAULT 'active',
            UNIQUE KEY uk_class_students (class_id, student_id),
            KEY idx_class_students_student (student_id),
            CONSTRAINT fk_class_students_class FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
            CONSTRAINT fk_class_students_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_profiles": [
        """
        CREATE TABLE IF NOT EXISTS student_profiles (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            profile_data LONGTEXT NOT NULL,
            conversation_log LONGTEXT,
            version INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_student_profiles_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS course_schedules (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            semester VARCHAR(64) NOT NULL,
            courses LONGTEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_course_schedules (user_id, semester)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS student_grades (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            semester VARCHAR(64) NOT NULL,
            course_name VARCHAR(255) NOT NULL,
            score DOUBLE,
            credits DOUBLE,
            grade_type VARCHAR(32) DEFAULT 'exam',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_student_grades_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS error_notes (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            subject VARCHAR(255) NOT NULL,
            chapter VARCHAR(255),
            question TEXT NOT NULL,
            my_answer TEXT,
            correct_answer TEXT,
            error_reason TEXT,
            tags TEXT,
            mastery INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            review_count INT DEFAULT 0,
            last_review TIMESTAMP NULL DEFAULT NULL,
            next_review TIMESTAMP NULL DEFAULT NULL,
            ease_factor DOUBLE DEFAULT 2.5,
            review_interval INT DEFAULT 1,
            KEY idx_error_notes_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS study_plans (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            semester VARCHAR(64) NOT NULL,
            plan_type VARCHAR(32) DEFAULT 'weekly',
            plan_data LONGTEXT NOT NULL,
            status VARCHAR(32) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_study_plans_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_resources": [
        """
        CREATE TABLE IF NOT EXISTS learning_resources (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            title VARCHAR(512) NOT NULL,
            resource_type VARCHAR(32) NOT NULL,
            subject VARCHAR(255),
            topic VARCHAR(255),
            difficulty_level VARCHAR(32) DEFAULT 'intermediate',
            content_data LONGTEXT NOT NULL,
            file_path VARCHAR(512),
            thumbnail_path VARCHAR(512),
            generated_by_agent VARCHAR(255),
            target_profile TEXT,
            tags TEXT,
            usage_count INT DEFAULT 0,
            rating DOUBLE DEFAULT 0,
            duration_minutes INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_learning_resources_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS resource_safety_logs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            resource_id BIGINT,
            safety_check_result TEXT NOT NULL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_resource_safety_resource (resource_id),
            CONSTRAINT fk_resource_safety_resource FOREIGN KEY (resource_id) REFERENCES learning_resources(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_paths": [
        """
        CREATE TABLE IF NOT EXISTS learning_paths (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            path_name VARCHAR(255) NOT NULL,
            description TEXT,
            path_data LONGTEXT NOT NULL,
            current_step INT DEFAULT 1,
            status VARCHAR(32) DEFAULT 'active',
            total_steps INT DEFAULT 0,
            completed_steps INT DEFAULT 0,
            estimated_hours DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_learning_paths_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS path_progress (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            path_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            step_number INT NOT NULL,
            completed_at TIMESTAMP NULL DEFAULT NULL,
            time_spent INT,
            KEY idx_path_progress_path (path_id),
            CONSTRAINT fk_path_progress_path FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_tutor": [
        """
        CREATE TABLE IF NOT EXISTS tutor_sessions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            subject VARCHAR(255),
            session_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_tutor_sessions_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS tutor_messages (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            session_id BIGINT NOT NULL,
            role VARCHAR(32) NOT NULL,
            content LONGTEXT NOT NULL,
            diagram TEXT,
            example TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_tutor_messages_session (session_id),
            CONSTRAINT fk_tutor_messages_session FOREIGN KEY (session_id) REFERENCES tutor_sessions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS tutor_knowledge_refs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            message_id BIGINT NOT NULL,
            rag_source TEXT,
            confidence_score DOUBLE,
            KEY idx_tutor_knowledge_refs_message (message_id),
            CONSTRAINT fk_tutor_knowledge_refs_message FOREIGN KEY (message_id) REFERENCES tutor_messages(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_assessments": [
        """
        CREATE TABLE IF NOT EXISTS learning_assessments (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            assessment_type VARCHAR(32) NOT NULL,
            assessment_data LONGTEXT NOT NULL,
            period_start VARCHAR(64),
            period_end VARCHAR(64),
            overall_score DOUBLE,
            improvement_suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_learning_assessments_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS assessment_dimensions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            assessment_id BIGINT NOT NULL,
            dimension_name VARCHAR(255) NOT NULL,
            score DOUBLE NOT NULL,
            max_score DOUBLE NOT NULL,
            level VARCHAR(64),
            feedback TEXT,
            KEY idx_assessment_dimensions_assessment (assessment_id),
            CONSTRAINT fk_assessment_dimensions_assessment FOREIGN KEY (assessment_id) REFERENCES learning_assessments(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_activities (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            activity_type VARCHAR(64) NOT NULL,
            metadata TEXT,
            duration_seconds INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_learning_activities_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            resource_id BIGINT,
            subject VARCHAR(255),
            topic VARCHAR(255),
            total_questions INT NOT NULL,
            correct_count INT DEFAULT 0,
            score DOUBLE DEFAULT 0,
            duration_seconds INT DEFAULT 0,
            mode VARCHAR(32) DEFAULT 'practice',
            status VARCHAR(32) DEFAULT 'in_progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL DEFAULT NULL,
            KEY idx_quiz_sessions_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_answers (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            session_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            question_index INT NOT NULL,
            question_type VARCHAR(64),
            question_text TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            user_answer TEXT,
            is_correct TINYINT DEFAULT 0,
            explanation TEXT,
            knowledge_point VARCHAR(255),
            difficulty VARCHAR(32),
            time_spent_seconds INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_quiz_answers_session (session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS question_bank (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            subject VARCHAR(255) NOT NULL,
            question_type VARCHAR(64) NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            knowledge_point VARCHAR(255),
            difficulty VARCHAR(32) DEFAULT 'medium',
            use_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS exam_papers (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            teacher_id BIGINT NOT NULL,
            title VARCHAR(255) NOT NULL,
            subject VARCHAR(255) DEFAULT '',
            grade VARCHAR(64) DEFAULT '',
            topic VARCHAR(255) DEFAULT '',
            paper_type VARCHAR(32) DEFAULT 'practice',
            total_score DOUBLE DEFAULT 100,
            duration_minutes INT DEFAULT 60,
            difficulty VARCHAR(32) DEFAULT 'medium',
            knowledge_points TEXT,
            question_source VARCHAR(32) DEFAULT 'ai',
            status VARCHAR(32) DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_exam_papers_teacher (teacher_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS exam_questions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            paper_id BIGINT NOT NULL,
            q_index INT NOT NULL,
            question_type VARCHAR(64) NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT,
            reference_answer TEXT,
            scoring_points TEXT,
            explanation TEXT,
            knowledge_point VARCHAR(255),
            difficulty VARCHAR(32) DEFAULT 'medium',
            score DOUBLE DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_exam_questions_paper (paper_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS exam_assignments (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            paper_id BIGINT NOT NULL,
            class_id BIGINT NOT NULL,
            assigned_by BIGINT NOT NULL,
            title VARCHAR(255) DEFAULT '',
            due_at TIMESTAMP NULL DEFAULT NULL,
            status VARCHAR(32) DEFAULT 'active',
            allow_late TINYINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_exam_assign_paper (paper_id),
            KEY idx_exam_assign_class (class_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS exam_submissions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            assignment_id BIGINT NOT NULL,
            paper_id BIGINT NOT NULL,
            student_id BIGINT NOT NULL,
            status VARCHAR(32) DEFAULT 'in_progress',
            objective_score DOUBLE DEFAULT 0,
            ai_score DOUBLE DEFAULT 0,
            final_score DOUBLE DEFAULT 0,
            total_score DOUBLE DEFAULT 0,
            submitted_at TIMESTAMP NULL DEFAULT NULL,
            graded_at TIMESTAMP NULL DEFAULT NULL,
            reviewed_at TIMESTAMP NULL DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_exam_sub_assign_student (assignment_id, student_id),
            KEY idx_exam_sub_student (student_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS exam_answers (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            submission_id BIGINT NOT NULL,
            question_id BIGINT NOT NULL,
            q_index INT NOT NULL,
            question_type VARCHAR(64),
            question_text TEXT,
            answer_text LONGTEXT,
            answer_image_path VARCHAR(512),
            ocr_text LONGTEXT,
            ocr_confidence DOUBLE DEFAULT 0,
            ocr_engine VARCHAR(64) DEFAULT '',
            correct_answer TEXT,
            reference_answer TEXT,
            max_score DOUBLE DEFAULT 0,
            is_correct TINYINT DEFAULT 0,
            ai_score DOUBLE DEFAULT 0,
            score DOUBLE DEFAULT 0,
            feedback TEXT,
            rag_evidence TEXT,
            knowledge_hits TEXT,
            grade_status VARCHAR(32) DEFAULT 'pending',
            teacher_score DOUBLE DEFAULT NULL,
            teacher_feedback TEXT,
            reviewed_at TIMESTAMP NULL DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_exam_answers_sub (submission_id),
            KEY idx_exam_answers_question (question_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS study_groups (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            creator_id BIGINT NOT NULL,
            invite_code VARCHAR(64) NOT NULL,
            max_members INT DEFAULT 50,
            subject VARCHAR(255) DEFAULT '综合',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_study_groups_invite (invite_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS group_members (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            role VARCHAR(32) DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_group_members (group_id, user_id),
            CONSTRAINT fk_group_members_group FOREIGN KEY (group_id) REFERENCES study_groups(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS shared_resources (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL,
            resource_id BIGINT NOT NULL,
            resource_type VARCHAR(64) DEFAULT 'document',
            shared_by BIGINT NOT NULL,
            shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_shared_resources_group (group_id),
            CONSTRAINT fk_shared_resources_group FOREIGN KEY (group_id) REFERENCES study_groups(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_activities_feed (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            activity_type VARCHAR(64) NOT NULL,
            content TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_learning_activities_feed_group (group_id),
            CONSTRAINT fk_learning_activities_feed_group FOREIGN KEY (group_id) REFERENCES study_groups(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS peer_reviews (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT NOT NULL,
            resource_id BIGINT NOT NULL,
            reviewer_id BIGINT NOT NULL,
            rating INT DEFAULT 0,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_peer_reviews_group (group_id),
            CONSTRAINT fk_peer_reviews_group FOREIGN KEY (group_id) REFERENCES study_groups(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_agents": [
        """
        CREATE TABLE IF NOT EXISTS agent_collaboration_logs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            user_id BIGINT,
            task_type VARCHAR(64) NOT NULL,
            coordinator_input LONGTEXT,
            agent_outputs LONGTEXT,
            final_result LONGTEXT,
            execution_time_ms INT,
            status VARCHAR(32) DEFAULT 'success',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            task_type VARCHAR(64) NOT NULL,
            assigned_agent VARCHAR(64),
            input_data LONGTEXT,
            output_data LONGTEXT,
            status VARCHAR(32) DEFAULT 'pending',
            progress INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_rag_knowledge": [
        """
        CREATE TABLE IF NOT EXISTS document_categories (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(255) NOT NULL,
            parent_id BIGINT,
            subject VARCHAR(255),
            sort_order INT DEFAULT 0,
            UNIQUE KEY uk_document_categories_name (category_name),
            KEY idx_document_categories_parent (parent_id),
            CONSTRAINT fk_document_categories_parent FOREIGN KEY (parent_id) REFERENCES document_categories(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(512) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            file_path VARCHAR(512),
            file_type VARCHAR(64),
            file_size BIGINT DEFAULT 0,
            document_data LONGTEXT,
            embedding LONGTEXT,
            embedding_model VARCHAR(64) DEFAULT 'spark-embedding',
            uploaded_by BIGINT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INT DEFAULT 0,
            is_public TINYINT DEFAULT 1,
            FULLTEXT KEY ft_knowledge_documents (title, subject) WITH PARSER ngram
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            doc_id BIGINT NOT NULL,
            point_name VARCHAR(255) NOT NULL,
            UNIQUE KEY uk_knowledge_points (doc_id, point_name),
            CONSTRAINT fk_knowledge_points_doc FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS document_category_relation (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            doc_id BIGINT NOT NULL,
            category_id BIGINT NOT NULL,
            UNIQUE KEY uk_document_category_relation (doc_id, category_id),
            KEY idx_document_category_relation_category (category_id),
            CONSTRAINT fk_document_category_relation_doc FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
            CONSTRAINT fk_document_category_relation_category FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS document_usage_log (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            doc_id BIGINT NOT NULL,
            user_id BIGINT,
            action_type VARCHAR(64),
            action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            search_keywords TEXT,
            KEY idx_document_usage_log_doc (doc_id),
            CONSTRAINT fk_document_usage_log_doc FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS knowledge_entity_graph (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            doc_id BIGINT,
            subject VARCHAR(255),
            entity_name VARCHAR(255) NOT NULL,
            entity_type VARCHAR(64),
            related_entities TEXT,
            embedding LONGBLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_knowledge_entity_graph_doc (doc_id),
            CONSTRAINT fk_knowledge_entity_graph_doc FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS entity_relations (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            doc_id BIGINT,
            source_entity VARCHAR(255),
            target_entity VARCHAR(255),
            relation_type VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_entity_relations_doc (doc_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
    "ai_memory": [
        """
        CREATE TABLE IF NOT EXISTS short_term_memory (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            role VARCHAR(32) NOT NULL,
            content LONGTEXT NOT NULL,
            token_count INT DEFAULT 0,
            position INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            context_window_position INT DEFAULT 0,
            KEY idx_short_term_memory_user (user_id, session_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS episodic_memory (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            episode_type VARCHAR(32) NOT NULL,
            title VARCHAR(512) NOT NULL,
            summary TEXT,
            context TEXT,
            emotions TEXT,
            participants TEXT,
            location VARCHAR(255),
            importance DOUBLE DEFAULT 0.5,
            embedding LONGBLOB,
            access_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            content LONGTEXT,
            last_accessed_at TIMESTAMP NULL DEFAULT NULL,
            KEY idx_episodic_memory_user (user_id),
            FULLTEXT KEY ft_episodic_memory_title (title) WITH PARSER ngram,
            FULLTEXT KEY ft_episodic_memory_summary (summary) WITH PARSER ngram,
            FULLTEXT KEY ft_episodic_memory_content (content) WITH PARSER ngram
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS semantic_memory (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            fact_type VARCHAR(32) NOT NULL,
            subject VARCHAR(191) NOT NULL,
            predicate VARCHAR(191) NOT NULL,
            object VARCHAR(191) NOT NULL,
            confidence DOUBLE DEFAULT 0.8,
            source VARCHAR(255) DEFAULT '',
            embedding LONGBLOB,
            access_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_verified TINYINT DEFAULT 0,
            last_accessed_at TIMESTAMP NULL DEFAULT NULL,
            UNIQUE KEY uk_semantic_memory (user_id, subject, predicate, object)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS entity_memory (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            entity_type VARCHAR(32) NOT NULL,
            entity_name VARCHAR(255) NOT NULL,
            entity_alias VARCHAR(255),
            attributes TEXT,
            description TEXT,
            importance DOUBLE DEFAULT 0.5,
            embedding LONGBLOB,
            access_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_accessed_at TIMESTAMP NULL DEFAULT NULL,
            UNIQUE KEY uk_entity_memory (user_id, entity_type, entity_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS entity_relations (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            source_entity_id BIGINT NOT NULL,
            target_entity_id BIGINT NOT NULL,
            relation_type VARCHAR(255) NOT NULL,
            weight DOUBLE DEFAULT 1.0,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            relation_label VARCHAR(255) DEFAULT '',
            last_accessed_at TIMESTAMP NULL DEFAULT NULL,
            UNIQUE KEY uk_entity_relations (user_id, source_entity_id, target_entity_id, relation_type),
            KEY idx_entity_relations_source (source_entity_id),
            KEY idx_entity_relations_target (target_entity_id),
            CONSTRAINT fk_entity_relations_source FOREIGN KEY (source_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE,
            CONSTRAINT fk_entity_relations_target FOREIGN KEY (target_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS memory_metadata (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            memory_type VARCHAR(32) NOT NULL,
            memory_id BIGINT NOT NULL,
            importance DOUBLE DEFAULT 0.5,
            decay_rate DOUBLE DEFAULT 0.01,
            access_count INT DEFAULT 0,
            last_accessed_at TIMESTAMP NULL DEFAULT NULL,
            is_forgotten TINYINT DEFAULT 0,
            forgotten_at TIMESTAMP NULL DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id BIGINT DEFAULT 0,
            reinforcement_count INT DEFAULT 0,
            UNIQUE KEY uk_memory_metadata (memory_type, memory_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS memory_access_log (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            memory_type VARCHAR(64) NOT NULL,
            memory_id BIGINT NOT NULL,
            access_type VARCHAR(32) NOT NULL,
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_memory_access_log_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS memory_conflicts (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            conflict_type VARCHAR(32) NOT NULL,
            old_memory_type VARCHAR(64),
            old_memory_id BIGINT,
            new_memory_type VARCHAR(64),
            new_memory_id BIGINT,
            resolution TEXT,
            resolved TINYINT DEFAULT 0,
            resolved_at TIMESTAMP NULL DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS profile_evaluations (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            knowledge_base DOUBLE DEFAULT 3,
            learning_goals DOUBLE DEFAULT 3,
            memory_ability DOUBLE DEFAULT 3,
            self_control DOUBLE DEFAULT 3,
            focus DOUBLE DEFAULT 3,
            learning_depth DOUBLE DEFAULT 3,
            reasoning TEXT,
            resource_count INT DEFAULT 0,
            activity_count INT DEFAULT 0,
            evaluation_source VARCHAR(32) DEFAULT 'ai',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cognitive_style DOUBLE DEFAULT 3,
            interest_areas DOUBLE DEFAULT 3,
            preferred_resources DOUBLE DEFAULT 3,
            learning_history DOUBLE DEFAULT 3,
            weak_points DOUBLE DEFAULT 3,
            learning_breadth DOUBLE DEFAULT 3,
            learning_stage DOUBLE DEFAULT 3,
            KEY idx_profile_evaluations_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS user_feedback (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            interaction_id VARCHAR(255),
            interaction_type VARCHAR(64),
            rating INT,
            helpful TINYINT DEFAULT 0,
            comment TEXT,
            original_query TEXT,
            original_answer LONGTEXT,
            processed TINYINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_user_feedback_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS learning_experiences (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            source_feedback_id BIGINT,
            user_id BIGINT,
            experience_type VARCHAR(64),
            content TEXT NOT NULL,
            confidence DOUBLE DEFAULT 0.8,
            augmented TINYINT DEFAULT 0,
            applied TINYINT DEFAULT 0,
            rag_doc_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            KEY idx_learning_experiences_feedback (source_feedback_id),
            CONSTRAINT fk_learning_experiences_feedback FOREIGN KEY (source_feedback_id) REFERENCES user_feedback(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ],
}

# 导入时跳过的表（FTS5 虚拟表 / sqlite 内部表）
SKIP_TABLES = {
    "sqlite_sequence",
    "knowledge_documents_fts",
    "episodic_memory_fts",
    "knowledge_documents_fts_config",
    "knowledge_documents_fts_data",
    "knowledge_documents_fts_docsize",
    "knowledge_documents_fts_idx",
    "episodic_memory_fts_config",
    "episodic_memory_fts_data",
    "episodic_memory_fts_docsize",
    "episodic_memory_fts_idx",
}

# 有外键依赖时的导入顺序
TABLE_ORDER = {
    "ai_auth": ["users", "sessions", "classes", "class_students"],
    "ai_profiles": ["student_profiles", "course_schedules", "student_grades", "error_notes", "study_plans"],
    "ai_resources": ["learning_resources", "resource_safety_logs"],
    "ai_paths": ["learning_paths", "path_progress"],
    "ai_tutor": ["tutor_sessions", "tutor_messages", "tutor_knowledge_refs"],
    "ai_assessments": [
        "learning_assessments",
        "assessment_dimensions",
        "learning_activities",
        "quiz_sessions",
        "quiz_answers",
        "question_bank",
        "exam_papers",
        "exam_questions",
        "exam_assignments",
        "exam_submissions",
        "exam_answers",
        "study_groups",
        "group_members",
        "shared_resources",
        "learning_activities_feed",
        "peer_reviews",
    ],
    "ai_agents": ["agent_collaboration_logs", "agent_tasks"],
    "ai_rag_knowledge": [
        "document_categories",
        "knowledge_documents",
        "knowledge_points",
        "document_category_relation",
        "document_usage_log",
        "knowledge_entity_graph",
        "entity_relations",
    ],
    "ai_memory": [
        "user_feedback",
        "short_term_memory",
        "episodic_memory",
        "semantic_memory",
        "entity_memory",
        "entity_relations",
        "memory_metadata",
        "memory_access_log",
        "memory_conflicts",
        "profile_evaluations",
        "learning_experiences",
    ],
}


def mysql_conn(database: str | None = None):
    cfg = dict(MYSQL)
    cfg["autocommit"] = False
    if database:
        cfg["database"] = database
    return pymysql.connect(**cfg)


def create_databases_and_tables(conn) -> None:
    cur = conn.cursor()
    for schema, statements in SCHEMA.items():
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cur.execute(f"USE `{schema}`")
        for ddl in statements:
            ddl = re.sub(r"\s+", " ", ddl.strip())
            cur.execute(ddl)
        conn.commit()
        print(f"[schema] {schema}: {len(statements)} tables")
    cur.close()


def sqlite_table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def migrate_data(conn) -> None:
    total_rows = 0
    for schema, tables in SCHEMA.items():
        db_file = SQLITE_DIR / f"{schema}.db"
        if not db_file.exists():
            print(f"[data]   {schema}: 源文件不存在，跳过")
            continue
        sconn = sqlite3.connect(str(db_file))
        sconn.row_factory = sqlite3.Row
        conn.cursor().execute(f"USE `{schema}`")
        conn.commit()

        for table in TABLE_ORDER.get(schema, []):
            if not sqlite_table_exists(sconn, table):
                continue
            # 关闭 FK 检查以便按任意顺序导入
            conn.cursor().execute("SET FOREIGN_KEY_CHECKS=0")
            rows = sconn.execute(f'SELECT * FROM "{table}"').fetchall()
            if not rows:
                print(f"[data]   {schema}.{table}: 0 rows")
                continue

            cols = rows[0].keys()
            col_list = ", ".join(f"`{c}`" for c in cols)
            placeholders = ", ".join(["%s"] * len(cols))
            sql = f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})"

            payload = []
            for row in rows:
                vals = []
                for c in cols:
                    v = row[c]
                    if isinstance(v, bytes):
                        vals.append(v)
                    elif v is None:
                        vals.append(None)
                    else:
                        vals.append(v)
                payload.append(tuple(vals))

            cur = conn.cursor()
            try:
                cur.executemany(sql, payload)
                conn.commit()
                # 同步自增 ID
                max_id = max((row["id"] for row in rows if row["id"] is not None), default=None)
                if max_id:
                    cur.execute(f"ALTER TABLE `{table}` AUTO_INCREMENT = %s", (int(max_id) + 1,))
                    conn.commit()
                total_rows += len(payload)
                print(f"[data]   {schema}.{table}: {len(payload)} rows")
            except Exception as e:
                conn.rollback()
                print(f"[data]   {schema}.{table}: 失败 {e}")
            finally:
                conn.cursor().execute("SET FOREIGN_KEY_CHECKS=1")
                conn.commit()
                cur.close()
        sconn.close()
    print(f"[data] 合计导入 {total_rows} 行")


def main() -> None:
    parser = argparse.ArgumentParser(description="SQLite → MySQL 迁移")
    parser.add_argument("--schema", action="store_true", help="仅建库建表")
    parser.add_argument("--data", action="store_true", help="仅导入数据")
    args = parser.parse_args()

    do_schema = args.schema or not args.data
    do_data = args.data or not args.schema

    print(f"MySQL {MYSQL['user']}@{MYSQL['host']}:{MYSQL['port']}")
    print(f"SQLite 源目录: {SQLITE_DIR}")

    conn = mysql_conn()
    try:
        if do_schema:
            create_databases_and_tables(conn)
        if do_data:
            migrate_data(conn)
        print("完成")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
