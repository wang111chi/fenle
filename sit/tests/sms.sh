#!/bin/bash

# 发送验证码
echo "sending sms code..." >&2

ret=$(
    curl -s \
         -d @data/bank_spid \
         -d @data/terminal_id \
         -d amount=100 \
         -d @data/bankacc_no \
         -d @data/mobile \
         -d @data/valid_date \
         http://58.67.212.197:8081/sms/send
   )

retcode=$(echo $ret | jq '.status')

if [ $retcode -ne 0 ]; then
    echo [fail] send sms code >&2
    echo $ret | jq '. | {status: .status, message: .message, op: "send_sms"}'
    exit 127
fi

bank_list=$(echo $ret | jq '.bank_list')
bank_sms_time=$(echo $ret | jq '.bank_sms_time')
echo $ret | jq '. | {bank_list: .bank_list, bank_sms_time: .bank_sms_time}'
