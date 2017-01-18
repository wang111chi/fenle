create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分乐银行余额表
# DROP TABLE IF EXISTS fenle_balance;

CREATE TABLE `fenle_balance` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `account_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账户号码',
  `account_type` int(11) NOT NULL COMMENT '1真实的银行账号：如中国银行2 虚拟账号(收入，支付都是经过第三方支付公司)，如广发银行',
  `bank_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '银行名称-以后用于加锁',
  `bank_type` int(11) NOT NULL COMMENT '银行4位代号',
  `true_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开户姓名',
  `bank_area` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行区域',
  `bank_city` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行城市',
  `cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '币种',
  `balance` bigint(20) NOT NULL DEFAULT '0' COMMENT '账户余额',
  `day_balance` bigint(20) NOT NULL DEFAULT '0' COMMENT '昨日账户余额',
  `arrears` bigint(20) NOT NULL DEFAULT '0' COMMENT '欠款金额',
  `ip` int(10) unsigned DEFAULT NULL COMMENT '最后修改ip',
  `memo` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户备注',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '最后修改时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `account_no_bank_type` (`account_no`,`bank_type`),
  KEY `create_time` (`create_time`),
  KEY `modify_time` (`modify_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
