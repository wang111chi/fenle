create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 分乐银行入账表
# DROP TABLE IF EXISTS fenle_bankroll_list;

CREATE TABLE fenle_bankroll_list (
    `list_id` varchar(32) not null comment '交易单号',
    `spid` varchar(16) not null  comment '商户号',
    `fenle_account_id` varchar(32) not null comment '分乐银行帐户',
    `fenle_account_type` smallint not null comment '银行帐户类型 1 真实银行户，2虚拟第三方户',
    `is_thirdpart` smallint default 0 comment '是否经过第三方支付平台',
    `pay_num` bigint not null default 0 comment '实际去银行交易金额:可能是本金+分乐手续费',
    `fact_amount` bigint not null default 0 comment '银行结算给分乐的金额(实际到账金额)',
    `income_num` bigint not null default 0 comment '分乐收入/提成',
    `state` smallint not null default 0 comment '账单状态:1：付款前 2：付款后',
    `sign` smallint not null default 0 comment '1-成功 2-失败 3-等待付款',
    `bank_tid` varchar(32) default '' comment '给银行订单号',
    `bank_backid` varchar(32) comment '银行返回订单号',
    `bank_type` smallint not null comment '银行类型',
    `cur_type` smallint not null default 1 comment '币种',
    `user_account_no_hash` varchar(65) comment '用户卡号hash值，可以从银行卡表中索引得到',
    `user_name` varchar(64) comment '用户姓名',
    `prove` varchar(32) comment '记账凭证',
    `client_ip` varchar(16) comment '客户ip地址',
    `memo` varchar(128) comment '记账凭证',
    `pay_front_time` datetime  comment '付款前时间(相当创建订单时间)',
    `pay_time`       datetime  comment '付款时间（本地）',
    `account_time`   datetime  comment '付款时间（帐务时间）',
    `product_type`   tinyint   NOT NULL comment '分期或积分',
	`bank_time`      datetime  comment '银行返回的时间戳',
    `modify_time`    datetime  comment '最后修改时间',
    `create_time`    datetime  comment '创建时间',
    `refund_time`    datetime  comment '退款时间',
    `refund_num`     bigint  default null comment '退款金额',
    `msg_no`         varchar(64) not null default '' comment '以后用于加锁',
    PRIMARY KEY(list_id),
    index `idx_account_no_hash`(`user_account_no_hash`),
    UNIQUE KEY `idx_bank_tid` (`bank_type`, `bank_tid`),
    index `idx_create_time` (`create_time`),
    index `idx_modify_time` (`modify_time`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

