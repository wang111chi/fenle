create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 结算表
# DROP TABLE IF EXISTS settle_list;

CREATE TABLE `settle_list` (
`id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '结算单号',
`spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
`product` tinyint(4) NOT NULL COMMENT '产品类型，分期/积分/积分+现金/信用卡消费等，见const',
`bank_type` int(11) NOT NULL COMMENT '交易银行的数字编号 1001广发信用卡',
`present_date` date DEFAULT NULL COMMENT '对哪一天做的结算',
`amount` bigint(20) NOT NULL DEFAULT '0' COMMENT '交易金额',
`fee` bigint(20) NOT NULL DEFAULT '0' COMMENT '分乐收的手续费',
`create_time` datetime NOT NULL COMMENT '创建时间',
`status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '业务状态:见文档',
PRIMARY KEY (`id`),
UNIQUE KEY `spid_product_bank_date` (`spid`,`product`,`bank_type`,`present_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
