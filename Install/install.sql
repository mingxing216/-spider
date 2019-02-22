-- ----------------------------
-- Table structure for ss_paper
-- ----------------------------
DROP TABLE IF EXISTS `ss_paper`;
CREATE TABLE `ss_paper` (
  `sha` varchar(50) NOT NULL,
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- Table structure for ss_paper_url
-- ----------------------------
DROP TABLE IF EXISTS `ss_paper_url`;
CREATE TABLE `ss_paper_url` (
  `url` varchar(200) NOT NULL,
  PRIMARY KEY (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- Table structure for ss_institute
-- ----------------------------
DROP TABLE IF EXISTS `ss_institute`;
CREATE TABLE `ss_institute` (
  `sha` varchar(40) NOT NULL COMMENT '网址的40位16进制SHA1摘要',
  `title` varchar(255) DEFAULT NULL COMMENT '标题',
  `cat` varchar(255) DEFAULT NULL COMMENT '分类',
  `tag` varchar(255) DEFAULT NULL COMMENT '标签',
  `clazz` varchar(255) DEFAULT NULL COMMENT '原网站_栏目名',
  `label` varchar(255) DEFAULT NULL COMMENT '原网站标签',
  `quality` int(11) DEFAULT '0' COMMENT '质量分值',
  `memo` longtext COMMENT '内容',
  `flag` char(1) DEFAULT '0' COMMENT '状态标识',
  `date_created` datetime DEFAULT NULL COMMENT '新建时间',
  `last_updated` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`sha`),
  KEY `idx_update` (`last_updated`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPRESSED COMMENT='机构';


SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for ss_magazine
-- ----------------------------
DROP TABLE IF EXISTS `ss_magazine`;
CREATE TABLE `ss_magazine` (
  `sha` varchar(40) NOT NULL COMMENT '网址的40位16进制SHA1摘要',
  `title` varchar(255) DEFAULT NULL COMMENT '标题',
  `cat` varchar(255) DEFAULT NULL COMMENT '分类',
  `tag` varchar(255) DEFAULT NULL COMMENT '标签',
  `clazz` varchar(255) DEFAULT NULL COMMENT '原网站_栏目名',
  `label` varchar(255) DEFAULT NULL COMMENT '原网站标签',
  `quality` int(11) DEFAULT '0' COMMENT '质量分值',
  `memo` longtext COMMENT '内容',
  `flag` char(1) DEFAULT '0' COMMENT '状态标识',
  `date_created` datetime DEFAULT NULL COMMENT '新建时间',
  `last_updated` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPRESSED COMMENT='期刊';


SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for ss_people
-- ----------------------------
DROP TABLE IF EXISTS `ss_people`;
CREATE TABLE `ss_people` (
  `sha` varchar(40) NOT NULL COMMENT '网址的40位16进制SHA1摘要',
  `title` varchar(255) DEFAULT NULL COMMENT '标题',
  `cat` varchar(255) DEFAULT NULL COMMENT '分类',
  `tag` varchar(255) DEFAULT NULL COMMENT '标签',
  `clazz` varchar(255) DEFAULT NULL COMMENT '原网站_栏目名',
  `label` varchar(255) DEFAULT NULL COMMENT '原网站标签',
  `quality` int(11) DEFAULT '0' COMMENT '质量分值',
  `memo` longtext COMMENT '内容',
  `flag` char(1) DEFAULT '0' COMMENT '状态标识',
  `date_created` datetime DEFAULT NULL COMMENT '新建时间',
  `last_updated` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`sha`),
  KEY `idx_update` (`last_updated`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=COMPRESSED COMMENT='人物';


-- ----------------------------
-- Table ss_innojoy_mobile
-- ----------------------------
DROP TABLE IF EXISTS `ss_innojoy_mobile`;
CREATE TABLE `ss_innojoy_mobile` (
  `mobile` bigint(20) unsigned NOT NULL,
  `date_created` datetime DEFAULT NULL,
  `del` int(11) DEFAULT NULL,
  `update_created` datetime DEFAULT NULL,
  PRIMARY KEY (`mobile`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;


-- ----------------------------
-- Table ss_innojoy_patent_url
-- ----------------------------
DROP TABLE IF EXISTS `ss_innojoy_patent_url`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ss_innojoy_patent_url` (
  `url` varchar(255) NOT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ----------------------------
-- Table structure for ss_patent_wanfang
-- ----------------------------
DROP TABLE IF EXISTS `ss_patent_wanfang`;
CREATE TABLE `ss_patent_wanfang` (
  `url` varchar(200) NOT NULL,
  `del` int(11) DEFAULT NULL,
  `country` varchar(50) NOT NULL,
  PRIMARY KEY (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;


-- ----------------------------
-- Table structure for ss_company_qicha
-- ----------------------------
DROP TABLE IF EXISTS `ss_company_qicha`;
CREATE TABLE `ss_company_qicha` (
  `sha` varchar(40) NOT NULL,
  `url` varchar(150) NOT NULL,
  `del` enum('0','1') DEFAULT '0',
  PRIMARY KEY (`sha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


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


