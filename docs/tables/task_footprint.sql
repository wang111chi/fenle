create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# �������б�
# DROP TABLE IF EXISTS task_footprint;

CREATE TABLE `task_footprint` (
`task_id` int(11) NOT NULL COMMENT '��������ID',
`task_name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '������������',
`status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '����״̬',
`modify_time` datetime NOT NULL COMMENT '����ʱ��',
PRIMARY KEY (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
