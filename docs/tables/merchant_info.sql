create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# 商户信息表
# DROP TABLE IF EXISTS merchant_info;

CREATE TABLE `merchant_info` (
  `spid` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户外部编号',
  `sp_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商户名称:可以是公司名，也可以是某个缩写',
  `fee_contract_no` int(11) DEFAULT NULL COMMENT '结算合同编号',
  `contract_no` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '业务合同编号',
  `corporation_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '法人姓名',
  `corporation_credid` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '法人身份证号码',
  `licence` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '统一社会信用代码',
  `corp_address` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '企业地址',
  `sp_mobile` varchar(15) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '商户联系手机号码',
  `sp_tel` varchar(65) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '坐机电话',
  `oper_user_id` varchar(65) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作员编号，即录入该信息的操作员',
  `modify_time` datetime DEFAULT NULL COMMENT '坐机电话',
  `mer_key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '' COMMENT '商户密钥',
  `rsa_pub_key` text COLLATE utf8mb4_unicode_ci COMMENT '商户提交过来的rsa公钥',
  `status` tinyint(4) NOT NULL DEFAULT '0',
  `memo` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`spid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
