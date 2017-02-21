create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分乐银行账户余额变更表
# DROP TABLE IF EXISTS fenle_balance_history;

CREATE TABLE `fenle_balance_history` (
`id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID主键',
`account_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账户号码',
`account_type` int(11) NOT NULL COMMENT '1真实的银行账号：如中国银行2 虚拟账号(收入，支付都是经过第三方支付公司)，如广发银行',
`bank_type` int(11) NOT NULL COMMENT '银行4位代号',
`biz` tinyint(4) NOT NULL COMMENT '业务类型，详见const.BIZ',
`amount` bigint(20) NOT NULL COMMENT '余额增减数值，带符号，单位(分)',
`ref_int_id` bigint(20) DEFAULT NULL COMMENT '相关业务单int型外部主键',
`ref_str_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '相关业务单varchar型外部主键，例如对于交易单来说，就是交易单号',
`create_time` datetime NOT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
