-- 知识库系统最终版初始化脚本 (Production Ready)
-- 包含完整的表结构设计：内部ID(id/uuid)与外部ID(knowledge_no)分离
-- 创建时间: 2026-01-24

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 1. 知识资产表 (核心表)
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_asset`;
CREATE TABLE `knowledge_asset` (
  `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '内部主键ID',
  `asset_uuid`          CHAR(32) NOT NULL COMMENT '内部业务全局唯一ID (UUID Hex)',
  `knowledge_no`        VARCHAR(64) NOT NULL COMMENT '外部知识编号 (源站ID)',
  `latest_hash`         CHAR(64) NOT NULL COMMENT '最新内容哈希(SHA256)',
  `latest_oss_path`     VARCHAR(512) NOT NULL COMMENT 'OSS存储路径 (knowledge/{uuid}/{hash}.md)',
  `source_update_time`  DATETIME DEFAULT NULL COMMENT '源数据更新时间',
  `status`              VARCHAR(32) NOT NULL DEFAULT 'NEW' COMMENT '状态: NEW/INGESTED/FAILED',
  `chunks_count`        INT DEFAULT 0 COMMENT 'ES切片数量',
  `error_message`       TEXT COMMENT '最后一次失败原因',
  `retry_count`         INT DEFAULT 0 COMMENT '重试次数',
  `updated_at`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_at`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_asset_uuid` (`asset_uuid`),
  UNIQUE KEY `ux_knowledge_no` (`knowledge_no`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识资产全生命周期管理表';

-- ----------------------------
-- 2. 知识版本历史表 (审计与回溯)
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_version`;
CREATE TABLE `knowledge_version` (
  `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '版本ID',
  `asset_uuid`          CHAR(32) NOT NULL COMMENT '关联内部业务ID',
  `knowledge_no`        VARCHAR(64) NOT NULL COMMENT '冗余外部编号',
  `md_hash`             CHAR(64) NOT NULL COMMENT '内容哈希',
  `oss_path`            VARCHAR(512) NOT NULL COMMENT 'OSS存储路径',
  `source_update_time`  DATETIME DEFAULT NULL COMMENT '源数据更新时间',
  `created_at`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_asset_uuid` (`asset_uuid`),
  KEY `idx_knowledge_no` (`knowledge_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识内容变更历史表';

-- ----------------------------
-- 3. 同步游标表 (增量同步)
-- ----------------------------
DROP TABLE IF EXISTS `sync_cursor`;
CREATE TABLE `sync_cursor` (
  `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '游标ID',
  `sync_type`           VARCHAR(16) NOT NULL COMMENT '同步类型: FULL/INCR',
  `last_cursor`         VARCHAR(128) DEFAULT NULL COMMENT '游标值',
  `last_sync_time`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后同步时间',
  `sync_status`         VARCHAR(32) DEFAULT 'IDLE' COMMENT '状态',
  `total_processed`     INT DEFAULT 0,
  `total_updated`       INT DEFAULT 0,
  `total_failed`        INT DEFAULT 0,
  `error_message`       TEXT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_sync_type` (`sync_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='同步任务游标表';

-- ----------------------------
-- 4. 初始化基础数据
-- ----------------------------
INSERT INTO `sync_cursor` (`sync_type`, `last_cursor`, `last_sync_time`, `sync_status`) 
VALUES 
('FULL', NULL, NOW(), 'IDLE'),
('INCR', NULL, NOW(), 'IDLE')
ON DUPLICATE KEY UPDATE `last_sync_time` = NOW();

SET FOREIGN_KEY_CHECKS = 1;
