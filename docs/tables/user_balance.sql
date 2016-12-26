create database if not exists fenle_fenqi_db;
use fenle_fenqi_db;

# DROP TABLE IF EXISTS `user_balance`;
CREATE TABLE `user_balance` (
  `tid` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `account_no` varchar(20) not null DEFAULT '' COMMENT '卡号',
  `account_type` smallint not null DEFAULT 0 COMMENT '卡种 1信用卡、2借计卡、3公司账号',
  `account_attr` smallint not null DEFAULT 0 COMMENT '1个人',
  `user_name` varchar(30) not null DEFAULT '' COMMENT '户名',
  `idcard_no` varchar(20) DEFAULT NULL COMMENT '办卡证件号',
  `idcard_no_hash` varchar(64) DEFAULT NULL COMMENT '办卡证件号md5',
  `idcard_type` varchar(20) DEFAULT NULL COMMENT '证件类型',
  `bank_type`   int       not null COMMENT '交易银行的数字编号 1001广发信用卡' ,
  `bank_name` varchar(50) DEFAULT NULL COMMENT '开户银行:中国银行，工商银行',
  `bank_sname` Varchar(16) COMMENT '银行对应英文缩写ICBC,CBC,CCBC等',
  `bank_province` varchar(64) DEFAULT NULL COMMENT '省',
  `bank_city` varchar(64) DEFAULT NULL COMMENT '市',
  `bank_branch` varchar(10) DEFAULT NULL COMMENT '支行名称',
  `account_mobile` varchar(15) DEFAULT NULL    COMMENT '银行卡预留手机号码',
  `status` smallint not null DEFAULT 0 COMMENT '状态 1：初始化 2: 验证成功 3: 注销',
  `lstate` smallint not null DEFAULT 0 COMMENT '1 正常，2冻结，3无效/删除',
  `create_time` datetime DEFAULT NULL COMMENT '记录创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '最后修改时间',
  PRIMARY KEY (`tid`),
  index idx_idcard_no(`idcard_no`),
  index idx_idcard_no_hash(`idcard_no_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
