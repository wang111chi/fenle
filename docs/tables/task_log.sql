create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# ������־��
# DROP TABLE IF EXISTS task_log;

CREATE TABLE `task_log` (
`id` int(11) NOT NULL AUTO_INCREMENT,
`task_id` int(11) NOT NULL COMMENT '��������ID',
`task_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '������������',
`run_type` tinyint(4) NOT NULL COMMENT '��������',
`create_time` datetime NOT NULL COMMENT '����ʱ��',
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
