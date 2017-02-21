create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分期交易表
# DROP TABLE IF EXISTS refund;

CREATE TABLE `refund` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '退款单号',
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户号',
  `list_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '交易单号',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '最后一次修改时间',
  `settle_time` datetime DEFAULT NULL COMMENT '结算时间',
  `status` tinyint(4) NOT NULL COMMENT '业务状态:见文档',
  KEY `create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
