create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 用户银行账户表
# DROP TABLE IF EXISTS `user_bank`;

CREATE TABLE `user_bank` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `bankacc_no` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '卡号',
  `account_type` tinyint(4) NOT NULL COMMENT '卡种 1信用卡、2借计卡、3公司账号',
  `true_name` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '户名',
  `idcard_no` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '办卡证件号',
  `idcard_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '证件类型',
  `bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
  `bank_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开户银行:中国银行，工商银行',
  `bank_sname` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行对应英文缩写ICBC,CBC,CCBC等',
  `bank_province` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '省',
  `bank_city` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '市',
  `bank_branch` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支行名称',
  `account_mobile` varchar(15) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行卡预留手机号码',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '状态 0：初始化 1: 验证成功 -1: 注销',
  `create_time` datetime NOT NULL COMMENT '记录创建时间',
  `modify_time` datetime NOT NULL COMMENT '最后修改时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `bank_type_account_no` (`bank_type`,`account_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
