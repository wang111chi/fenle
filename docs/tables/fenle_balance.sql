create database if not exists fenle_fenqi_db;                                  
use fenle_fenqi_db;

# 分乐银行入账表
# DROP TABLE IF EXISTS fenle_balance;
 
CREATE TABLE fenle_bank(
    `bkid` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
    `account_no`     varchar(32) not null comment '账户号码',
    `account_type`   int  comment '账户',
    `state`          smallint  comment '正常/冻结',
    `bank_name`      varchar(64) not null default '' comment '银行名称-以后用于加锁',
    `bank_type`      smallint not null comment '银行4位代号',
    `true_name`      varchar(64) comment '开户姓名',  
    `bank_area`      varchar(16) comment '银行区域',
    `bank_city`      varchar(16) comment '银行城市',
    `cur_type`       smallint comment '现金类型',
    `balance`        bigint comment '账户余额',
    `day_balance`    bigint comment '昨日账户余额',
    `arrearage`      bigint default '0' COMMENT '欠款金额',
	`create_time`    datetime comment '创建时间',
    `ip`             int unsigned comment '最后修改ip',
    `memo`           varchar(128) comment '用户备注',
    `modify_time`    datetime comment '最后修改时间',
    PRIMARY KEY(`bkid`),
    UNIQUE KEY `idx_bank` (`account_no`, `bank_type`),
    index `idx_create_time` (`create_time`),
    index `idx_modify_time` (`modify_time`),
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

