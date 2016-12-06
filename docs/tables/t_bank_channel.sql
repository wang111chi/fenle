#!/bin/sh


create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

##银行渠道表
DROP TABLE IF EXISTS t_bank_channel;
CREATE TABLE t_bank_channel (
    `Findex`                int NOT NULL AUTO_INCREMENT PRIMARY KEY ,
    `Fbank_channel`         varchar(16)               NOT NULL,
    `Fbank_type`            int                       NOT NULL,
    `Fchannel`              tinyint(6)   NOT NULL default '1' ,
    `Fagent_bank`           varchar(256)                      ,
    `Fscope`                varchar(256)                      ,
    `Fbank_valitype`        smallint     NOT NULL default '0' ,
    `Finterface_mask`       smallint     NOT NULL default '0' ,
    `Fbankacc_type`         tinyint(6)   NOT NULL default '0' ,
    `Fbankacc_attr`         tinyint(6)   NOT NULL default '0' ,
    `Fiterface_type`        tinyint(6)   NOT NULL default '0' ,
    `Fenable_flag`          tinyint(6)   NOT NULL default '0' ,
    `Ffenqi_fee`            bigint       NOT NULL default '0' COMMENT '分期成本手续费',
    `Ftimeout`              smallint     NOT NULL default '0' ,
    `Frsp_time`             varchar(32)               NOT NULL,
    `Fstandby1`             bigint                 default '0',
    `Fstandby2`             bigint                 default '0',
    `Fstandby3`             datetime              default NULL,
    `Fstandby4`             varchar(64)           default NULL,
    `Fstandby5`             varchar(256)          default NULL,

     UNIQUE KEY `idx_bank_channel` ( `Fbank_channel` ),
     KEY `idx_channel` ( `Fbank_type`, `Fchannel` )
    
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

