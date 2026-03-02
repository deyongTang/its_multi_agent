-- ITS 多智能体系统 - 数据库初始化脚本
-- 数据库: its_db

CREATE DATABASE IF NOT EXISTS its_db DEFAULT CHARACTER SET utf8mb4;
USE its_db;

-- 对话历史表
CREATE TABLE IF NOT EXISTS chat_messages (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id        VARCHAR(64)  NOT NULL,
    session_id     VARCHAR(64)  NOT NULL,
    seq_id         INT          NOT NULL DEFAULT 0,
    role           VARCHAR(16)  NOT NULL,   -- system / user / assistant
    content        TEXT         NOT NULL,
    is_ask_user    TINYINT      DEFAULT 0,
    pending_intent VARCHAR(64)  DEFAULT '',
    created_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_session_seq (user_id, session_id, seq_id)  -- 支持 INSERT IGNORE 增量写入
);
