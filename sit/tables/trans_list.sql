create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 交易表
# DROP TABLE IF EXISTS trans_list;

CREATE TABLE `trans_list` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内部交易单号',
  `bank_list` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '给银行订单号',
  `amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '交易金额',
  `jf_deduct_money` bigint(20) NOT NULL DEFAULT '0' COMMENT '积分抵扣金额(积分+现金交易时用)',
  `bankacc_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '付款人账号',
  `mobile` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '付款人手机号',
  `valid_date` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '信用卡有效期',
  `bank_sms_time` varchar(32) NOT NULL COMMENT '银行下发短信时间',
  `bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
  `div_term` int(11) NOT NULL COMMENT '分期期数',
  `bank_validcode` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行下发的验证码',
  `bank_roll` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行返回的订单号',
  `bank_settle_time` varchar(32) DEFAULT NULL COMMENT '银行结算时间',
  `product` tinyint(4) NOT NULL COMMENT '产品类型，分期/积分/积分+现金/信用卡消费等，见const',
  `status` tinyint(4) NOT NULL COMMENT '状态，支付中/成功/失败等，见const',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '修改时间',
  `refund_id` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '退款单号',
  PRIMARY KEY (`id`),
  UNIQUE KEY `bank_list` (`bank_list`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
