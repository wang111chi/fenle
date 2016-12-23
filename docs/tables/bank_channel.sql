create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 银行渠道表
# DROP TABLE IF EXISTS bank_channel;
CREATE TABLE bank_channel (
    `index`                int NOT NULL AUTO_INCREMENT PRIMARY KEY ,
    `bank_channel`         varchar(16)               NOT NULL COMMENT '银行渠道字符编号:用于配置路由表',
    `bank_type`            int                       NOT NULL COMMENT '4位的银行编号如：1001 广发信用卡 ',
    `channel`              tinyint(6)   NOT NULL default '1' COMMENT '预留字段，默认1',
    `agent_bank`           varchar(256)                      COMMENT '代理银行,预留字段',
    `singlepay_vmask`      int                               COMMENT '银行实时单笔联机接口判断参数掩码',
    `bank_valitype`        int     NOT NULL default '0' COMMENT '银行支持的客户验证模式: (掩码模式，设置该位表示强制验证)',
    `bank_city` varchar(64) DEFAULT NULL COMMENT '市',
    `bank_branch` varchar(10) DEFAULT NULL COMMENT '支行名称',
    `interface_mask`       smallint     NOT NULL default '0' COMMENT '接口功能掩码',
    `account_type`         smallint   NOT NULL default '0' COMMENT '银行帐户类型支持掩码',
    `user_type`            smallint   NOT NULL default '0' COMMENT '对私 0x01 对公0x02',
    `interface_type`       tinyint(6)   NOT NULL default '0' COMMENT '接口类型:1单笔实时型',
    `enable_flag`          tinyint(6)   NOT NULL default '0' COMMENT '该渠道是否可用',
    `fenqi_fee`            double       NOT NULL default '0' COMMENT '分期成本手续费,千分之',
    `jf_fee`               bigint       NOT NULL default '0' COMMENT '积分交易手续费',
    `timeout`              smallint     NOT NULL default '0' COMMENT '银行承诺的超时时间',
    `rsp_time`             varchar(32)  NOT NULL COMMENT '平均返回时间',
    `service_stime`      time default null COMMENT '日常服务可用开始时间(预留)',
    `service_etime`      time default null COMMENT '日常服务可用结束时间(预留)',
    `maintain_stime`     datetime COMMENT '银行维护升级开始时间(预留)',
    `maintain_etime`     datetime COMMENT '银行维护升级结束时间(预留)',
    `bulletion_uptime`   datetime COMMENT '发布公告时间',
    `bulletion`           text comment '公告',
    `standby1`             bigint                 default '0',
    `standby2`             bigint                 default '0',
    `standby3`             datetime              default NULL,
    `standby4`             varchar(64)           default NULL,
    `standby5`             varchar(256)          default NULL,

     UNIQUE KEY `idx_bank_type` ( `bank_type`)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

