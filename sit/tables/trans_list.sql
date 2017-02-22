create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 交易表
# DROP TABLE IF EXISTS trans_list;

CREATE TABLE `trans_list` (
  `list_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内部交易单号',
  `sp_tid` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户提交的交易单号',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `bank_tid` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '给银行订单号',
  `bank_backid` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行返回订单号',
  `bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
  `user_mobile` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户手机号',
  `user_name` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '付款人姓名',
  `user_account_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易卡号',
  `pin_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信用卡cvv2',
  `bank_valicode` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行下发的验证码',
  `valid_period` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信用卡有效期',
  `cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '币种 默认0',
  `divided_term` int(11) NOT NULL COMMENT '分期期数6,12',
  `amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '主交易金额',
  `minor_amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '次交易金额，某些交易可能需要，比如积分+现金',
  `paynum` bigint(20) NOT NULL DEFAULT '0' COMMENT '实际去银行支付金额 以分为单位',
  `product_type` tinyint(4) NOT NULL COMMENT '分期或积分',
  `fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '分乐收取的手续费',
  `bank_fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '银行将要收的手续费',
  `status` tinyint(4) NOT NULL COMMENT '业务状态:见文档',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '最后一次修改时间',
  `paysucc_time` datetime DEFAULT NULL COMMENT '支付成功时间',
  `settle_time` datetime DEFAULT NULL COMMENT '结算时间',
  `bank_settle_time` datetime DEFAULT NULL COMMENT '银行结算时间',
  `client_ip` int(10) unsigned DEFAULT NULL COMMENT '客户端ip',
  `modify_ip` int(10) unsigned DEFAULT NULL COMMENT '修改记录的ip',
  `refund_id` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '退款单号',
  PRIMARY KEY (`list_id`),
  UNIQUE KEY `spid_sptid` (`spid`,`sp_tid`),
  KEY `user_account_no` (`user_account_no`),
  KEY `create_time` (`create_time`),
  KEY `modify_time` (`modify_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
