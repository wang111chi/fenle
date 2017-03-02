#!/bin/bash

# 积分加现金消费

# 接收标准输入：
# {
#     "bank_list": "20170228111959",
#     "bank_sms_time": "0228113054"
# }

input=$(cat -)
bank_list=$(echo $input | jq '.bank_list' | sed -e 's/^"//' -e 's/"$//')
bank_sms_time=$(echo $input | jq '.bank_sms_time' | sed -e 's/^"//' -e 's/"$//')

echo "sleeping 5 seconds..." >&2
sleep 5

echo "making point_cash request..." >&2

ret=$(
    curl -s \
         -d @data/bank_spid \
         -d @data/terminal_id \
         -d amount=1000 \
         -d jf_deduct_money=100 \
         -d @data/bankacc_no \
         -d @data/mobile \
         -d @data/valid_date \
         -d bank_validcode=000000 \
         -d bank_sms_time=$bank_sms_time \
         -d bank_list=$bank_list \
         http://58.67.212.197:8081/point_cash/trade
   )

retcode=$(echo $ret | jq '.status')

if [ $retcode -ne 0 ]; then
    echo [fail] point_cash >&2
    echo $ret | jq '.' >&2
    exit 127
fi

echo $ret | jq '.trans'