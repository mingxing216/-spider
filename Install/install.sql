CREATE TABLE `ss_zhiwang_jigou` (
  `sha` varchar(50) NOT NULL,
  `memo` longtext,
  `type` varchar(10) DEFAULT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `ss_zhiwang_lunwen` (
  `sha` varchar(50) NOT NULL,
  `memo` longtext,
  `type` varchar(10) DEFAULT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `ss_zhiwang_qikan` (
  `sha` varchar(50) NOT NULL,
  `memo` longtext,
  `type` varchar(10) DEFAULT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `ss_zhiwang_removal` (
  `sha` varchar(50) NOT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `ss_zhiwang_zuozhe` (
  `sha` varchar(50) NOT NULL,
  `memo` longtext,
  `type` varchar(10) DEFAULT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `ss_statistics` (
  `sha` varchar(50) NOT NULL,
  `create_at` datetime DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`sha`),
  KEY `create_at` (`create_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ----------------------------
-- Table structure for ss_zhiwang_zhuanli_url
-- ----------------------------
DROP TABLE IF EXISTS `ss_zhiwang_zhuanli_url`;
CREATE TABLE `ss_zhiwang_zhuanli_url` (
  `url` varchar(150) NOT NULL,
  PRIMARY KEY (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;


-- ----------------------------
-- Table structure for ss_media
-- ----------------------------
DROP TABLE IF EXISTS `ss_media`;
CREATE TABLE `ss_media` (
  `sha` varchar(40) NOT NULL,
  `type` enum('image','music','video','file') DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;


CREATE TABLE `data_number_total` (
  `sha` varchar(50) NOT NULL,
  `memo` longtext,
  `data_type` varchar(10) DEFAULT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `data_volume_day` (
  `sha` varchar(50) NOT NULL,
  `memo` longtext,
  `data_type` varchar(50) DEFAULT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `data_volume_total` (
  `sha` varchar(50) NOT NULL,
  `memo` longtext,
  `data_type` varchar(50) DEFAULT NULL,
  `create_at` datetime DEFAULT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

