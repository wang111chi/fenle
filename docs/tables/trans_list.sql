create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分期交易表
# DROP TABLE IF EXISTS trans_list;

CREATE TABLE `trans_list` (
  `list_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内部交易单号',
  `sp_tid` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户提交的交易单号',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `bank_tid` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '给银行订单号',
  `bank_backid` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行返回订单号',
  `request_sn` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行请求消息序列号',
  `rcd_type` smallint(6) NOT NULL DEFAULT '1' COMMENT '预留 默认1',
  `bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
  `bank_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行名称:如 广东发展银行',
  `bank_area` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行所在地区',
  `bank_city` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行所在城市',
  `user_mobile` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户手机号',
  `user_name` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '付款人姓名',
  `user_account_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易卡号',
  `user_account_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0  信用卡',
  `user_account_attr` tinyint(6) NOT NULL DEFAULT '0' COMMENT '0－个人',
  `pin_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信用卡cvv2',
  `bank_valicode` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行下发的验证码',
  `valid_period` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '信用卡有效期',
  `rsp_time` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '预期返回时间',
  `cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '币种 默认0',
  `idcard_type` smallint(6) DEFAULT NULL COMMENT '证件类型',
  `idcard_no` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '证件号码',
  `bank_channel` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行渠道名，对应t_bank_channel表',
  `channel` tinyint(4) NOT NULL COMMENT '发起渠道 1 api,2商户系统，3网关',
  `pay_type` tinyint(4) DEFAULT NULL COMMENT '支付方式 1 信用卡分期支付 2 信用积分支付',
  `trade_type` tinyint(4) NOT NULL DEFAULT '1' COMMENT '交易类型 默认1 b2c',
  `divided_term` int(11) NOT NULL COMMENT '分期期数6,12',
  `memo` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商户提交的备注信息',
  `attach` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商户自定义数据，伴随结果返回，包含数字字母下划线',
  `amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '商户提交的交易金额',
  `paynum` bigint(20) NOT NULL DEFAULT '0' COMMENT '实际去银行支付金额 以分为单位',
  `fee_duty` tinyint(4) NOT NULL COMMENT '付费手续费 1商户，2用户',
  `product_type` tinyint(4) NOT NULL COMMENT '分期或积分',
  `fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '分乐收取的手续费',
  `bank_fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '银行将要收的手续费',
  `token` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '验证token。每一步都会生成一个token',
  `valid_count` int(11) NOT NULL DEFAULT '0' COMMENT '交易验证数次',
  `sp_userid` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商户侧的用户id',
  `status` tinyint(4) NOT NULL COMMENT '业务状态:见文档',
  `lstate` tinyint(4) NOT NULL COMMENT '物理状态1 有效 2 挂起 3 作废',
  `adjust_flag` tinyint(4) NOT NULL DEFAULT '1' COMMENT '调账标志 １正常（default）2 调账 3 同步查询状态未返回 4 不补单设置失败 5 超过补单时间设置失败 6待冲正 7 冲正完成(明确知道银行原交易失败/交易不存在、交易成功但冲正也成功)',
  `interface_type` smallint(6) NOT NULL DEFAULT '1' COMMENT '接口类型(预留)默认1',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '最后一次修改时间',
  `bank_last_time` datetime DEFAULT NULL COMMENT '最后一次去银行时间',
  `paysucc_time` datetime DEFAULT NULL COMMENT '支付成功时间',
  `future_time` datetime DEFAULT NULL COMMENT '预期结果最早时间',
  `settle_time` datetime DEFAULT NULL COMMENT '结算时间',
  `bank_settle_time` datetime DEFAULT NULL COMMENT '银行结算时间',
  `explain` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '后台操作的',
  `notify_url` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '后台回调地址，不能含有&=等字符',
  `client_ip` int(10) unsigned DEFAULT NULL COMMENT '客户端ip',
  `modify_ip` int(10) unsigned DEFAULT NULL COMMENT '修改记录的ip',
  `refund_id` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '退款单号',
  `extend_spinfo` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`list_id`),
  UNIQUE KEY `spid_sptid` (`spid`,`sp_tid`),
  KEY `user_account_no_type` (`user_account_no`,`user_account_type`),
  KEY `create_time` (`create_time`),
  KEY `modify_time` (`modify_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
