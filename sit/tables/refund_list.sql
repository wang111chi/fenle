create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 退款表
# DROP TABLE IF EXISTS refund_list;

CREATE TABLE `refund_list` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内部交易单号',
  `bank_list` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '给银行订单号',
  `trans_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原订单号',
  `bank_roll` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '银行返回的订单号',
  `bank_settle_time` varchar(32) DEFAULT NULL COMMENT '银行结算时间',
  `mode` tinyint(4) NOT NULL COMMENT '撤销还是退货，见const',
  `product` tinyint(4) NOT NULL COMMENT '产品类型，分期/积分/积分+现金/信用卡消费等，见const',
  `status` tinyint(4) NOT NULL COMMENT '状态，退款中/成功/失败等，见const',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `modify_time` datetime NOT NULL COMMENT '修改时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `bank_list` (`bank_list`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
