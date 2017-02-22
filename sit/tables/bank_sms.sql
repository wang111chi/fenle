create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 银行下发短信表
# DROP TABLE IF EXISTS bank_sms;

CREATE TABLE `bank_sms` (
  `bank_list` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '给银行订单号',
  `bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
  `mobile` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户手机号',
  `bankacc_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易卡号',
  `valid_date` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信用卡有效期',
  `amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '交易金额',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '修改时间',
  PRIMARY KEY (`bank_list`),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
