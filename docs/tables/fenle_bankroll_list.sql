create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分乐银行入账表
# DROP TABLE IF EXISTS fenle_bankroll_list;

CREATE TABLE `fenle_bankroll_list` (
  `list_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易单号',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `fenle_account_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分乐银行帐户',
  `fenle_account_type` tinyint(4) NOT NULL COMMENT '银行帐户类型 1 真实银行户，2虚拟第三方户',
  `is_thirdpart` tinyint(4) DEFAULT '0' COMMENT '是否经过第三方支付平台',
  `pay_num` bigint(20) NOT NULL DEFAULT '0' COMMENT '实际去银行交易金额:可能是本金+分乐手续费',
  `fact_amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '银行结算给分乐的金额(实际到账金额)',
  `income_num` bigint(20) NOT NULL DEFAULT '0' COMMENT '分乐收入/提成',
  `bank_tid` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '给银行订单号',
  `bank_backid` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行返回订单号',
  `bank_type` int(11) NOT NULL COMMENT '银行类型',
  `cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '币种',
  `user_account_no_hash` varchar(65) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户卡号hash值，可以从银行卡表中索引得到',
  `user_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户姓名',
  `prove` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '记账凭证',
  `client_ip` int(10) unsigned DEFAULT NULL COMMENT '客户ip地址',
  `memo` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '记账凭证',
  `pay_front_time` datetime DEFAULT NULL COMMENT '付款前时间(相当创建订单时间)',
  `pay_time` datetime DEFAULT NULL COMMENT '付款时间（本地）',
  `account_time` datetime DEFAULT NULL COMMENT '付款时间（帐务时间）',
  `product_type` tinyint(4) NOT NULL COMMENT '分期或积分',
  `bank_time` datetime DEFAULT NULL COMMENT '银行返回的时间戳',
  `modify_time` datetime DEFAULT NULL COMMENT '最后修改时间',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `refund_time` datetime DEFAULT NULL COMMENT '退款时间',
  `refund_num` bigint(20) DEFAULT NULL COMMENT '退款金额',
  `msg_no` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '以后用于加锁',
  PRIMARY KEY (`list_id`),
  UNIQUE KEY `bank_type_bank_tid` (`bank_type`,`bank_tid`),
  KEY `user_account_no_hash` (`user_account_no_hash`),
  KEY `create_time` (`create_time`),
  KEY `modify_time` (`modify_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

