create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# DROP TABLE IF EXISTS callback_url;
CREATE TABLE callback_url (
   `id` bigint NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
   `url` varchar(2000) NOT NULL COMMENT 'URL',
   `method` tinyint NOT NULL DEFAULT 0 COMMENT '请求方法 0: GET 1: POST',
   `body` text DEFAULT NULL COMMENT '请求body',
   `resp_code` int NOT NULL DEFAULT 0 COMMENT '最后一次请求响应HTTP状态码',
   `resp_body` text DEFAULT NULL COMMENT '最后一次请求响应body',
   `ip` int unsigned NOT NULL DEFAULT 0 COMMENT '请求IP',
   `mode` tinyint NOT NULL COMMENT '请求模式，一种模式对应一种配置(重试次数、间隔)',
   `call_times` smallint NOT NULL DEFAULT 0 COMMENT '调用次数',
   `create_time` datetime NOT NULL COMMENT '创建时间',
   `call_time` datetime DEFAULT NULL COMMENT '最后一次请求时间',
   `is_call_success` tinyint NOT NULL DEFAULT 0 COMMENT '最后一次请求是否成功，成功标准由业务逻辑定义',
   `status` tinyint NOT NULL DEFAULT 0 COMMENT '回调状态，据此确定是否还需要重试，详见常量配置'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
