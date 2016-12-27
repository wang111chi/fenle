create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 银行渠道表
# DROP TABLE IF EXISTS bank_channel;

CREATE TABLE `bank_channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bank_channel` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '银行渠道字符编号:用于配置路由表',
  `bank_type` int(11) NOT NULL COMMENT '4位的银行编号如：1001 广发信用卡 ',
  `channel` tinyint(6) NOT NULL DEFAULT '1' COMMENT '预留字段，默认1',
  `agent_bank` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '代理银行,预留字段',
  `singlepay_vmask` int(11) DEFAULT NULL COMMENT '银行实时单笔联机接口判断参数掩码',
  `bank_valitype` int(11) NOT NULL DEFAULT '0' COMMENT '银行支持的客户验证模式: (掩码模式，设置该位表示强制验证)',
  `bank_city` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '市',
  `bank_branch` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '支行名称',
  `interface_mask` smallint(6) NOT NULL DEFAULT '0' COMMENT '接口功能掩码',
  `account_type` smallint(6) NOT NULL DEFAULT '0' COMMENT '银行帐户类型支持掩码',
  `user_type` smallint(6) NOT NULL DEFAULT '0' COMMENT '对私 0x01 对公0x02',
  `interface_type` tinyint(6) NOT NULL DEFAULT '0' COMMENT '接口类型:1单笔实时型',
  `is_enable` tinyint(6) NOT NULL DEFAULT '0' COMMENT '该渠道是否可用',
  `fenqi_fee_percent` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分期手续费,万分之几',
  `jifen_fee_percent` int(11) DEFAULT NULL COMMENT '积分手续费',
  `settle_type` tinyint(4) NOT NULL COMMENT '日结与月结',
  `timeout` smallint(6) NOT NULL DEFAULT '0' COMMENT '银行承诺的超时时间',
  `rsp_time` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平均返回时间',
  `service_stime` time DEFAULT NULL COMMENT '日常服务可用开始时间(预留)',
  `service_etime` time DEFAULT NULL COMMENT '日常服务可用结束时间(预留)',
  `maintain_stime` datetime DEFAULT NULL COMMENT '银行维护升级开始时间(预留)',
  `maintain_etime` datetime DEFAULT NULL COMMENT '银行维护升级结束时间(预留)',
  `bulletion_uptime` datetime DEFAULT NULL COMMENT '发布公告时间',
  `bulletion` text COLLATE utf8mb4_unicode_ci COMMENT '公告',
  PRIMARY KEY (`id`),
  UNIQUE KEY `bank_type` (`bank_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
