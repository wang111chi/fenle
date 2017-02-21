create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 任务日志表
# DROP TABLE IF EXISTS task_log;

CREATE TABLE `task_log` (
`id` int(11) NOT NULL AUTO_INCREMENT,
`task_id` int(11) NOT NULL COMMENT '任务类型ID',
`task_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务类型名称',
`run_type` tinyint(4) NOT NULL COMMENT '运行类型',
`create_time` datetime NOT NULL COMMENT '创建时间',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
