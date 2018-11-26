SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for ss_paper
-- ----------------------------
DROP TABLE IF EXISTS `ss_paper`;
CREATE TABLE `ss_paper` (
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
  KEY `idx_update_time` (`last_updated`),
  KEY `idx_clazz_cat` (`clazz`,`cat`) USING BTREE,
  KEY `idx_update` (`last_updated`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='论文';


SET FOREIGN_KEY_CHECKS=0;

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