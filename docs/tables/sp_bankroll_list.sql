create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分乐商户(虚拟银行)入账表
# DROP TABLE IF EXISTS sp_bankroll_list;

CREATE TABLE sp_bankroll_list (
        `bkid` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
        `list_id` varchar(32) not null default '' comment '交易单的ID号',
        `spid` varchar(16) not null default '' comment '商户号',
        `type` smallint comment '借贷类型：1-入 2-出 3-冻结 4-解冻',
        `state` int not null default 0 comment '状态，不同的type，对应不同的状态：如type=1时 1支付前，1支付中，2支付成功，4支付失败 5 退款 6冲动',
        `bankacc_no_hash` varchar(64) comment '卡号hash值',
        `uname` varchar(64) comment '付款者姓名',
        `balance` bigint NOT NULL DEFAULT 0 comment '当前余额（修改后的）',
        `con` bigint NOT NULL DEFAULT 0 comment '冻结余额',
        `pay_num` bigint NOT NULL DEFAULT 0 comment '交易金额：支付时，是指用户需要去银行扣除的金额',
        `sp_num` bigint NOT NULL DEFAULT 0 comment '商户所得金额',
        `con_num` bigint NOT NULL DEFAULT 0 comment '冻结金额',
        `bank_type` smallint not null comment '银行类型',
        `curtype` smallint not null  DEFAULT 1 comment '币种 1人民币',
        `prove` varchar(32) DEFAULT null comment '入账凭证',
        `memo` varchar(128) comment '备注',
        `action_type` smallint comment '内部之间的帐务关系，及用户资金流动的动作记录',
        `modify_time_acc` datetime comment '帐务时间',
        `modify_time` datetime not null comment '最后修改时间',
        `create_time` datetime not null comment '创建时间',
        `rollback_time` datetime DEFAULT null comment '冲正时间',
        `explain` varchar(128) comment '说明信息，商户传入商品信息等',
        list_sign smallint comment '流水的标记：0 正常 1 被冲正 2 冲正',
        PRIMARY KEY  (`bkid`),
        KEY `idx_list_id` (`list_id`),
        KEY `idx_bankacc_hash` (`bankacc_no_hash`),
        KEY `idx_modify_time` (`modify_time`)
        )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
