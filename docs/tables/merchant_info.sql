create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# DROP TABLE IF EXISTS merchant_info;
CREATE TABLE merchant_info (
   `spid` varchar(20) NOT NULL  PRIMARY KEY  comment '商户外部编号',
   `uid`  int unsigned  NOT NULL    comment '内部编号', 
   `agent_uid` int unsigned NOT NULL    comment '代理编号',
   `parent_uid` int unsigned NOT NULL    comment '上级商户uid', 
   `sp_name` varchar(64) NOT NULL  comment '商户名称:可以是公司名，也可以是某个缩写', 
   `fee_contract_no` int comment '结算合同编号',
   `contract_no` varchar(64) comment '业务合同编号',
   `corporation_name` varchar(64) default null comment '法人姓名',
   `corporation_credid` varchar(64) default null comment '法人身份证号码',
   `licence` varchar(64) comment '统一社会信用代码',
   `corp_address` varchar(128) default null comment '企业地址',
   `mobile` varchar(15) comment '商户联系手机号码',
   `tel` varchar(65) comment '坐机电话',
   `oper_user_id` varchar(65) comment '操作员编号，即录入该信息的操作员',
   `modify_time` datetime comment '坐机电话',
   `mer_key` varchar(64) not null default '' comment '商户密钥',
   `rsa_pub_key` text default null comment '商户提交过来的rsa公钥',
   `state` smallint not null DEFAULT 0,
   `list_state` smallint comment '物理状态  1：正常 2：作废',
   `withdraw_type` smallint DEFAULT 0,
   `memo` varchar(128) comment '备注',
   `ip` varchar(64) null default '',
   UNIQUE KEY `uid` ( `uid` )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
