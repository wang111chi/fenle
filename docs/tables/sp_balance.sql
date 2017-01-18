create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 商家余额表
# DROP TABLE IF EXISTS sp_balance;
 
CREATE TABLE `sp_balance` (
  `uid` int(11) NOT NULL COMMENT '商户内部编号',
  `cur_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '现金类型',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `true_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开户姓名',
  `b_balance` bigint(20) NOT NULL DEFAULT '0' COMMENT 'b账户余额',
  `c_balance` bigint(20) NOT NULL DEFAULT '0' COMMENT 'c账户余额',
  `arrears` bigint(20) NOT NULL DEFAULT '0' COMMENT '欠款金额',
  `b_freezing` bigint(20) NOT NULL DEFAULT '0' COMMENT 'b冻结余额',
  `c_freezing` bigint(20) NOT NULL DEFAULT '0' COMMENT 'c冻结余额',
  `day_balance` bigint(20) NOT NULL DEFAULT '0' COMMENT '昨日余额，每次结算并且付款成功之后，从账户 余额进行扣除',
  `min_balance` bigint(20) NOT NULL DEFAULT '0' COMMENT '用户最小余额',
  `save_time` datetime DEFAULT NULL COMMENT '最近入账日期',
  `fetch_time` datetime DEFAULT NULL COMMENT '最近出帐日期',
  `change_ip` int(10) unsigned DEFAULT NULL COMMENT '资金变更ip',
  `status` tinyint(4) DEFAULT NULL COMMENT '账户状态',
  `memo` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户备注',
  `modify_time` datetime NOT NULL COMMENT '资金变更时间',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `balance_time` datetime DEFAULT NULL COMMENT '余额变化时间',
  UNIQUE KEY `uid_cur_type` (`uid`,`cur_type`),
  KEY `create_time` (`create_time`),
  KEY `spid` (`spid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
