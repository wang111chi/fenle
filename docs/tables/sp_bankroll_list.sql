create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分乐商户(虚拟银行)入账表
# DROP TABLE IF EXISTS sp_bankroll_list;

CREATE TABLE `sp_bankroll_list` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `list_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易单的ID号',
  `account_class` tinyint(4) NOT NULL COMMENT '账户类型B,C', 
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `bankroll_type` tinyint(4) DEFAULT NULL COMMENT '借贷类型： 1-交易 2-退款 3-结算 4-提现 5-充值',
  `sp_account_no_hash` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '卡号hash值',
  `user_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '付款者姓名',
  `sp_balance` bigint(20) NOT NULL DEFAULT '0' COMMENT '当前余额（修改后的）',
  `freezing_balance` bigint(20) NOT NULL DEFAULT '0' COMMENT '冻结余额',
  `pay_num` bigint(20) NOT NULL DEFAULT '0' COMMENT '交易金额：支付时，是指用户需要去银行扣除的金额',
  `sp_num` bigint(20) NOT NULL DEFAULT '0' COMMENT '商户所得金额',
  `delta_money` bigint(20) NOT NULL DEFAULT '0' COMMENT '账户变动金额（有正负）',
  `bank_type` int(11) NOT NULL COMMENT '银行类型',
  `cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '币种 0人民币',
  `prove` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '入账凭证',
  `memo` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `action_type` smallint(6) DEFAULT NULL COMMENT '内部之间的帐务关系，及用户资金流动的动作记录',
  `account_time` datetime DEFAULT NULL COMMENT '帐务时间',
  `product_type` tinyint(4) NOT NULL COMMENT '分期或积分',
  `modify_time` datetime NOT NULL COMMENT '最后修改时间',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `rollback_time` datetime DEFAULT NULL COMMENT '冲正时间',
  `explain` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '说明信息，商户传入商品信息等',
  `list_sign` tinyint(4) NOT NULL COMMENT '流水的标记：0 正常 1 被冲正 2 冲正',
  PRIMARY KEY (`id`),
  KEY `list_id` (`list_id`),
  KEY `sp_account_no_hash` (`sp_account_no_hash`),
  KEY `modify_time` (`modify_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
