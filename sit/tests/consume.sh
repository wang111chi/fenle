#!/bin/bash

# 信用卡刷卡消费

# 接收标准输入：
# {
#     "bank_list": "20170228111959",
#     "bank_sms_time": "0228113054"
# }

input=$(cat -)

status=$(echo $input | jq '.status')
op=$(echo $input | jq '.op')
if [ "$status" == 1 -a "$op" != "" ]; then
    echo $input | jq '.'
    exit 127
fi

bank_list=$(echo $input | jq '.bank_list' | sed -e 's/^"//' -e 's/"$//')
bank_sms_time=$(echo $input | jq '.bank_sms_time' | sed -e 's/^"//' -e 's/"$//')

echo "sleeping 5 seconds..." >&2
sleep 5

echo "making consume request..." >&2

ret=$(
    curl -s \
         -d @data/bank_spid \
         -d @data/terminal_id \
         -d amount=100 \
         -d @data/bankacc_no \
         -d @data/mobile \
         -d @data/valid_date \
         -d bank_validcode=000000 \
         -d bank_sms_time=$bank_sms_time \
         -d bank_list=$bank_list \
         http://58.67.212.197:8081/consume/trade
   )

retcode=$(echo $ret | jq '.status')

if [ $retcode -ne 0 ]; then
    echo [fail] consume >&2
    echo $ret | jq '. | {status: .status, message: .message, op: "consume"}'
    exit 127
fi

echo $ret | jq '.trans'
