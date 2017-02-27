create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 银行渠道表
# DROP TABLE IF EXISTS bank_channel;

CREATE TABLE `bank_channel` (
`bank_type` int(11) NOT NULL COMMENT '4位的银行编号如：1001 广发信用卡 ',
`bank_valitype` int(11) NOT NULL DEFAULT '0' COMMENT '银行支持的客户验证模式: (掩码模式，设置该位表示强制验证)',
`interface_mask` smallint(6) NOT NULL DEFAULT '0' COMMENT '接口功能掩码',
`fenqi_fee_percent` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分期手续费,万分之几',
`jifen_fee_percent` int(11) DEFAULT NULL COMMENT '积分手续费率，万分之几',
`settle_type` tinyint(4) NOT NULL COMMENT '日结与月结',
`create_time` datetime NOT NULL COMMENT '创建时间',
`modify_time` datetime NOT NULL COMMENT '最后一次修改时间',
`status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '状态',
PRIMARY KEY (`bank_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
