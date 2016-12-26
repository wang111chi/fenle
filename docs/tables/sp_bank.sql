create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 商户银行手续费配置表
# DROP TABLE IF EXISTS sp_bank;

CREATE TABLE sp_bank(
   `bkid` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
   `spid` varchar(16) not null default '' comment '商户号',
   `bank_type` int not null default 0 comment '银行类型',
   `state` int not null default 0 comment '状态 1 有效，2无效',
   `fenqi_fee_percent` varchar(255) default null comment '分期手续费,千分之',
   `jifen_fee_percent` int default null comment '积分手续费',
   `divided_term`      varchar(128)   COMMENT '分期期数6,12逗号分隔',
   `settle_type`    tinyint comment '日结与月结',
    PRIMARY KEY  (`bkid`),
    unique `idx_spid_banktype` (`spid`,`bank_type`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

