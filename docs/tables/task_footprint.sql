create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 任务运行表
# DROP TABLE IF EXISTS task_footprint;

CREATE TABLE `task_footprint` (
`task_id` int(11) NOT NULL COMMENT '任务类型ID',
`task_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型名称',
`status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '任务状态',
`modify_time` datetime NOT NULL COMMENT '更新时间',
PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
