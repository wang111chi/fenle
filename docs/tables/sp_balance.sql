create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 商户余额表
# DROP TABLE IF EXISTS sp_balance;
 
CREATE TABLE `sp_balance` (
`spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
`cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '现金类型',
`account_class` tinyint(4) NOT NULL COMMENT '账户类型B,C等，见const.ACCOUNT_CLASS',
`true_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开户姓名',
`balance` bigint(20) NOT NULL DEFAULT '0' COMMENT '账户余额',
`freezing` bigint(20) NOT NULL DEFAULT '0' COMMENT '冻结余额',
`change_ip` int(10) unsigned DEFAULT NULL COMMENT '资金变更ip',
`status` tinyint(4) DEFAULT NULL COMMENT '账户状态',
`memo` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户备注',
`create_time` datetime NOT NULL COMMENT '创建时间',
`modify_time` datetime NOT NULL COMMENT '资金变更时间',
UNIQUE KEY `spid_cur_type` (`spid`,`cur_type`,`account_class`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
