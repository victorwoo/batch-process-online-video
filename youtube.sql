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

 Date: 01/04/2025 12:07:24
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for channels
-- ----------------------------
DROP TABLE IF EXISTS `channels`;
CREATE TABLE `channels` (
  `channel_id` varchar(64) NOT NULL,
  `channel_name` varchar(255) NOT NULL,
  `channel_url` varchar(512) NOT NULL,
  `uploader_name` varchar(255) DEFAULT NULL,
  `uploader_id` varchar(64) DEFAULT NULL,
  `uploader_url` varchar(512) DEFAULT NULL,
  `follower_count` int(11) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- ----------------------------
-- Table structure for tags
-- ----------------------------
DROP TABLE IF EXISTS `tags`;
CREATE TABLE `tags` (
  `tag_id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(64) NOT NULL,
  PRIMARY KEY (`tag_id`),
  UNIQUE KEY `tag_name` (`tag_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- ----------------------------
-- Table structure for video_formats
-- ----------------------------
DROP TABLE IF EXISTS `video_formats`;
CREATE TABLE `video_formats` (
  `format_id` int(11) NOT NULL AUTO_INCREMENT,
  `video_id` varchar(64) DEFAULT NULL,
  `format_code` varchar(32) DEFAULT NULL,
  `extension` varchar(16) DEFAULT NULL,
  `resolution` varchar(32) DEFAULT NULL,
  `fps` int(11) DEFAULT NULL,
  `vcodec` varchar(32) DEFAULT NULL,
  `vbr` int(11) DEFAULT NULL COMMENT '视频比特率(kbps)',
  `acodec` varchar(32) DEFAULT NULL,
  `abr` int(11) DEFAULT NULL COMMENT '音频比特率(kbps)',
  `filesize` bigint(20) DEFAULT NULL COMMENT '文件大小(字节)',
  PRIMARY KEY (`format_id`),
  KEY `video_id` (`video_id`),
  CONSTRAINT `video_formats_ibfk_1` FOREIGN KEY (`video_id`) REFERENCES `videos` (`video_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- ----------------------------
-- Table structure for video_tags
-- ----------------------------
DROP TABLE IF EXISTS `video_tags`;
CREATE TABLE `video_tags` (
  `video_id` varchar(64) NOT NULL,
  `tag_id` int(11) NOT NULL,
  PRIMARY KEY (`video_id`,`tag_id`),
  KEY `tag_id` (`tag_id`),
  CONSTRAINT `video_tags_ibfk_1` FOREIGN KEY (`video_id`) REFERENCES `videos` (`video_id`),
  CONSTRAINT `video_tags_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- ----------------------------
-- Table structure for videos
-- ----------------------------
DROP TABLE IF EXISTS `videos`;
CREATE TABLE `videos` (
  `video_id` varchar(64) NOT NULL,
  `channel_id` varchar(64) NOT NULL,
  `title` varchar(255) NOT NULL,
  `fulltitle` varchar(512) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `webpage_url` varchar(512) NOT NULL,
  `thumbnail_url` varchar(512) DEFAULT NULL,
  `duration` int(11) DEFAULT NULL COMMENT '视频时长(秒)',
  `view_count` int(11) DEFAULT 0,
  `like_count` int(11) DEFAULT 0,
  `comment_count` int(11) DEFAULT 0,
  `upload_date` date DEFAULT NULL,
  `release_date` date DEFAULT NULL,
  `language` varchar(16) DEFAULT NULL,
  `age_limit` tinyint(4) DEFAULT 0,
  `is_live` tinyint(1) DEFAULT 0,
  `was_live` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`video_id`),
  KEY `channel_id` (`channel_id`),
  CONSTRAINT `videos_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `channels` (`channel_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

SET FOREIGN_KEY_CHECKS = 1;
