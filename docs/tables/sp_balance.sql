create database if not exists fenle_fenqi_db;                                  
use fenle_fenqi_db;

# 分乐银行入账表
# DROP TABLE IF EXISTS sp_balance;
 
CREATE TABLE sp_balance(
	`uid` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
    `cur_type`       smallint comment '现金类型',
    `spid`           varchar(16) comment '',
    `true_name`      varchar(64) comment '开户姓名',  
    `balance`        bigint default 0 comment '账户余额',
    `con_settle`     bigint default 0 comment '冻结',	
    `day_balance`    bigint default 0 comment '',
	`min_balance`    bigint default 0 comment '用户最小余额',
	`save_time`      datetime comment '最近入账日期',
	`fetch_time`     datetime comment '最近出帐日期',
	`change_ip`      int unsigned comment '资金变更ip',
	`state`          smallint  comment '正常/冻结',
	`memo`           varchar(128) comment '用户备注',
	`modify_time`    datetime comment '资金变更时间',
    `create_time`    datetime comment '创建时间',
    `balance_time`   datetime comment '余额变化时间',
    `arrearage`      bigint default '0' COMMENT '欠款金额',
	`standby1`       int comment '预留字段',
	`standby2`       int comment '',
	`standby3`       int comment '',
	`standby4`       int comment '',
	`standby5`       int comment '',
	`standby6`       varchar(64) comment '',
	`standby7`       varchar(64) comment '',
	`standby8`       varchar(64) comment '',
	`standby9`       varchar(64) comment '', 
	`standby10`      varchar(64) comment '',
	`standby11`      datetime(64) comment '',
	`standby12`      datetime(64) comment '',
	RIMARY KEY(`uid`, cur_type),
    index `idx_create_time` (`create_time`),
    index `idx_spid` (`spid`),
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

