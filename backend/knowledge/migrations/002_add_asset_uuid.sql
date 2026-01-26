-- 数据库迁移脚本: 002_add_asset_uuid.sql
-- 目标: 将 knowledge_asset 表的主键从 knowledge_no 改为 id，并新增 asset_uuid

-- 1. 修改 knowledge_asset 表
-- 注意: 执行 ALTER 操作前请备份数据!

-- Step 1.1: 如果存在旧的主键 (knowledge_no), 先删除
-- MySQL 不支持 IF EXISTS DROP PRIMARY KEY, 所以这里假设主键是 knowledge_no
-- 如果报错 "Multiple primary key defined", 说明表结构已经是新的了, 可以忽略
-- ALTER TABLE knowledge_asset DROP PRIMARY KEY;

-- Step 1.2: 添加 id 列 (作为新主键)
ALTER TABLE knowledge_asset
ADD COLUMN id BIGINT AUTO_INCREMENT PRIMARY KEY FIRST;

-- Step 1.3: 添加 asset_uuid 列 (作为内部业务ID)
ALTER TABLE knowledge_asset
ADD COLUMN asset_uuid CHAR(32) NOT NULL COMMENT '内部业务ID (UUID Hex)' AFTER id;

-- Step 1.4: 为 asset_uuid 添加唯一索引
ALTER TABLE knowledge_asset
ADD UNIQUE INDEX ux_asset_uuid (asset_uuid);

-- Step 1.5: 确保 knowledge_no 仍有唯一约束 (如果之前是PK, 删了PK后需要补Unique)
ALTER TABLE knowledge_asset
ADD UNIQUE INDEX ux_knowledge_no (knowledge_no);

-- ---------------------------------------------------------

-- 2. 修改 knowledge_version 表

-- Step 2.1: 添加 asset_uuid 列
ALTER TABLE knowledge_version
ADD COLUMN asset_uuid CHAR(32) NOT NULL COMMENT '关联内部业务ID' AFTER id;

-- Step 2.2: 添加索引
ALTER TABLE knowledge_version
ADD INDEX idx_asset_uuid (asset_uuid);

-- 3. 数据回填 (Data Backfill)
-- 为现有的记录生成 asset_uuid (使用 UUID() 函数)
-- 注意: MySQL UUID() 生成带有横杠, 我们需要 Hex 格式 (去横杠)
UPDATE knowledge_asset
SET asset_uuid = REPLACE(UUID(), '-', '')
WHERE asset_uuid = '';

UPDATE knowledge_version v
JOIN knowledge_asset a ON v.knowledge_no = a.knowledge_no
SET v.asset_uuid = a.asset_uuid
WHERE v.asset_uuid = '';
