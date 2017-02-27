create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 交易表
# DROP TABLE IF EXISTS trans_list;

CREATE TABLE `trans_list` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内部交易单号',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `sp_list` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户提交的交易单号',
  `sp_uid` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商户侧的用户id',
  `bank_list` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '给银行订单号',
  `bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
  `bank_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行名称:如 广东发展银行',
  `bank_area` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行所在地区',
  `bank_city` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行所在城市',
  `mobile` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '付款人手机号',
  `true_name` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '付款人姓名',
  `bankacc_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '付款人账号',
  `account_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0 信用卡',
  `bank_validcode` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行下发的验证码',
  `valid_date` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '信用卡有效期',
  `idcard_type` smallint(6) DEFAULT NULL COMMENT '证件类型',
  `idcard_no` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '证件号码',
  `pin_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信用卡cvv2',
  `div_term` int(11) DEFAULT NULL COMMENT '分期期数',
  `memo` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商户提交的备注信息',
  `attach` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商户自定义数据，伴随结果返回，包含数字字母下划线',
  `cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '币种 默认0',
  `amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '交易金额',
  `jf_deduct_money` bigint(20) NOT NULL DEFAULT '0' COMMENT '积分抵扣金额(积分+现金交易时用)',
  `fee_duty` tinyint(4) NOT NULL COMMENT '付费手续费 1商户，2用户',
  `fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '分乐收取的手续费',
  `bank_fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '银行收取的手续费',
  `bank_sms_time` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行下发短信时间',
  `bank_settle_time` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行结算时间',
  `bank_roll` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行返回的订单号',
  `refund_id` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '退款单号',
  `channel` tinyint(4) NOT NULL COMMENT '发起渠道 1 api,2商户系统，3网关，见const',
  `product` tinyint(4) NOT NULL COMMENT '产品类型，分期/积分/积分+现金/信用卡消费等，见const',
  `status` tinyint(4) NOT NULL COMMENT '状态，支付中/成功/失败等，见const',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '修改时间',
  `create_ip` int(10) unsigned DEFAULT NULL COMMENT '创建ip',
  `modify_ip` int(10) unsigned DEFAULT NULL COMMENT '修改ip',
  PRIMARY KEY (`id`),
  UNIQUE KEY `bank_list` (`bank_list`),
  UNIQUE KEY `spid_sp_list` (`spid`,`sp_list`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
