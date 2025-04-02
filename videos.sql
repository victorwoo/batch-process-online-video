/*
 Navicat Premium Dump SQL

 Source Server         : home.vichamp.com - smms
 Source Server Type    : MariaDB
 Source Server Version : 101106 (10.11.6-MariaDB)
 Source Host           : home.vichamp.com:3306
 Source Schema         : youtube

 Target Server Type    : MariaDB
 Target Server Version : 101106 (10.11.6-MariaDB)
 File Encoding         : 65001

 Date: 02/04/2025 16:38:18
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for videos
-- ----------------------------
DROP TABLE IF EXISTS `videos`;
CREATE TABLE `videos` (
  `id` varchar(16) NOT NULL COMMENT '视频ID（YouTube标准11位）',
  `description` text DEFAULT NULL COMMENT '视频描述（支持Emoji）',
  `tags` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '标签数组（JSON格式）' CHECK (json_valid(`tags`)),
  `channel_id` varchar(32) NOT NULL COMMENT '频道ID',
  `channel_url` varchar(512) NOT NULL COMMENT '频道URL',
  `webpage_url` varchar(512) NOT NULL COMMENT '视频页面URL',
  `channel` varchar(255) NOT NULL COMMENT '频道名称',
  `uploader` varchar(255) NOT NULL COMMENT '上传者名称',
  `uploader_id` varchar(64) NOT NULL COMMENT '上传者ID（@格式）',
  `uploader_url` varchar(512) NOT NULL COMMENT '上传者主页URL',
  `upload_date` date DEFAULT NULL COMMENT '上传日期（YYYYMMDD转换）',
  `fulltitle` varchar(512) NOT NULL COMMENT '完整标题',
  `release_date` date DEFAULT NULL COMMENT '发布日期',
  `language` varchar(16) DEFAULT 'en' COMMENT '语言代码',
  `thumbnail` varchar(512) DEFAULT NULL COMMENT '缩略图URL',
  `download_time` datetime DEFAULT NULL COMMENT '下载的时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
