create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 退款表
# DROP TABLE IF EXISTS settle_list;

CREATE TABLE `settle_list` (
`id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '结算单号',
`spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
`bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
`list_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易单号',
`amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '商户提交的交易金额',
`paynum` bigint(20) NOT NULL DEFAULT '0' COMMENT '实际去银行支付金额 以分为单位',
`fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '分乐收取的手续费',
`bank_fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '银行将要收的手续费',
`fee_duty` tinyint(4) NOT NULL COMMENT '付费手续费 1商户，2用户',
`create_time` datetime NOT NULL COMMENT '创建时间',
`modify_time` datetime NOT NULL COMMENT '最后一次修改时间',
`settle_time` datetime DEFAULT NULL COMMENT '结算时间',
`divided_term` int(11) NOT NULL COMMENT '分期期数6,12',
`status` tinyint(4) NOT NULL COMMENT '业务状态:见文档',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
