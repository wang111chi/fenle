create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 商户银行渠道表
# DROP TABLE IF EXISTS sp_bank;

CREATE TABLE `sp_bank` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `bank_type` int(11) NOT NULL COMMENT '银行类型',
  `bank_spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '15位银行子商户号: 四位的地区号+mcc号+内部序列号',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '状态',
  `fenqi_fee_percent` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分期手续费,万分之几，json字符串，分期期数作为键',
  `jifen_fee_percent` int(11) DEFAULT NULL COMMENT '积分手续费',
  `settle_type` tinyint(4) NOT NULL COMMENT '日结与月结',
  PRIMARY KEY (`id`),
  UNIQUE KEY `spid_banktype` (`spid`,`bank_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
