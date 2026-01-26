-- 知识库同步系统数据库表结构
-- 更新时间: 2026-01-24
-- 架构升级: 引入内部 ID (id/uuid) 与外部 ID (knowledge_no) 分离

-- 1. 知识资产表 (核心表)
CREATE TABLE IF NOT EXISTS knowledge_asset (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '内部主键ID',
    asset_uuid          CHAR(32) NOT NULL COMMENT '内部业务ID (UUID Hex)',
    knowledge_no        VARCHAR(64) NOT NULL COMMENT '外部知识编号 (源站ID)',
    latest_hash         CHAR(64) NOT NULL COMMENT '最新内容哈希(SHA256)',
    latest_oss_path     VARCHAR(512) NOT NULL COMMENT 'OSS存储路径 (Based on UUID)',
    source_update_time  DATETIME NULL COMMENT '源数据更新时间',
    status              VARCHAR(32) NOT NULL DEFAULT 'NEW' COMMENT '状态: NEW/INGESTED/FAILED',
    chunks_count        INT DEFAULT 0 COMMENT '向量化后的块数量',
    error_message       TEXT NULL COMMENT '错误信息',
    retry_count         INT DEFAULT 0 COMMENT '重试次数',
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE INDEX ux_asset_uuid (asset_uuid),
    UNIQUE INDEX ux_knowledge_no (knowledge_no),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识资产索引表';

-- 2. 历史版本表
CREATE TABLE IF NOT EXISTS knowledge_version (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '版本ID',
    asset_uuid          CHAR(32) NOT NULL COMMENT '关联内部业务ID',
    knowledge_no        VARCHAR(64) NOT NULL COMMENT '冗余外部编号(方便查询)',
    md_hash             CHAR(64) NOT NULL COMMENT '内容哈希(SHA256)',
    oss_path            VARCHAR(512) NOT NULL COMMENT 'OSS存储路径',
    source_update_time  DATETIME NULL COMMENT '源数据更新时间',
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_asset_uuid (asset_uuid),
    INDEX idx_knowledge_no (knowledge_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识版本历史表';

-- 3. 同步游标表
CREATE TABLE IF NOT EXISTS sync_cursor (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '游标ID',
    sync_type           VARCHAR(16) NOT NULL COMMENT '同步类型: FULL/INCR',
    last_cursor         VARCHAR(128) NULL COMMENT '最后同步游标',
    last_sync_time      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后同步时间',
    sync_status         VARCHAR(32) DEFAULT 'IDLE' COMMENT '同步状态',
    total_processed     INT DEFAULT 0 COMMENT '本次处理总数',
    total_updated       INT DEFAULT 0 COMMENT '本次更新数',
    total_skipped       INT DEFAULT 0 COMMENT '本次跳过数',
    total_failed        INT DEFAULT 0 COMMENT '本次失败数',
    error_message       TEXT NULL COMMENT '错误信息',
    INDEX idx_sync_type (sync_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='同步游标表';

-- 初始化游标数据
INSERT INTO sync_cursor (sync_type, last_cursor, last_sync_time, sync_status)
VALUES
    ('FULL', NULL, NOW(), 'IDLE'),
    ('INCR', NULL, NOW(), 'IDLE')
ON DUPLICATE KEY UPDATE last_sync_time = NOW();