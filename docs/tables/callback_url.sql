create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# DROP TABLE IF EXISTS callback_url;

CREATE TABLE `callback_url` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `url` varchar(2000) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'URL',
  `method` tinyint(4) NOT NULL DEFAULT '0' COMMENT '请求方法 0: GET 1: POST',
  `body` text COLLATE utf8mb4_unicode_ci COMMENT '请求body',
  `resp_code` int(11) DEFAULT NULL COMMENT '最后一次请求响应HTTP状态码',
  `resp_body` text COLLATE utf8mb4_unicode_ci COMMENT '最后一次请求响应body',
  `ip` int(10) unsigned DEFAULT NULL COMMENT '请求IP',
  `mode` tinyint(4) NOT NULL COMMENT '请求模式，一种模式对应一种配置(重试次数、间隔)',
  `retry_times` smallint(6) NOT NULL DEFAULT '0' COMMENT '重试次数',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `call_time` datetime DEFAULT NULL COMMENT '最后一次请求时间',
  `is_call_success` tinyint(4) NOT NULL DEFAULT '0' COMMENT '最后一次请求是否成功，成功标准由业务逻辑定义',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '回调状态，据此确定是否还需要重试，详见常量配置',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
