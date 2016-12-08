create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 商户银行手续费配置表
# DROP TABLE IF EXISTS sp_bankfee;

CREATE TABLE sp_bankfee (
   `bkid` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
   `spid` varchar(16) not null default '' comment '商户号',
   `bank_type` int not null default 0 comment '银行类型',
   `state` int not null default 0 comment '状态 1 有效，2无效',
   `fee_percent` double not null default 0 comment '该银行的签约手续费,千分之',
    PRIMARY KEY  (`bkid`),
    unique `idx_spid_banktype` (`spid`,`bank_type`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
