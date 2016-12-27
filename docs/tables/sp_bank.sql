create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 商户银行手续费配置表
# DROP TABLE IF EXISTS sp_bank;

CREATE TABLE `sp_bank` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `bank_type` int(11) NOT NULL COMMENT '银行类型',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '状态',
  `fenqi_fee_percent` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分期手续费,千分之，json字符串，分期期数作为键',
  `jifen_fee_percent` int(11) DEFAULT NULL COMMENT '积分手续费',
  `divided_term` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分期期数6,12逗号分隔',
  `settle_type` tinyint(4) NOT NULL COMMENT '日结与月结',
  PRIMARY KEY (`id`),
  UNIQUE KEY `spid_banktype` (`spid`,`bank_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
