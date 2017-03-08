#!/bin/bash

# 预授权完成

# 接收标准输入：
# {
#     "id": "111111111110012017030100000013",
#     "bank_list": "20170301145608",
#     "bank_settle_time": "0301150700",
#     "pre_author_code": "096207",
#     ...
# }

input=$(cat -)

status=$(echo $input | jq '.status')
op=$(echo $input | jq '.op')
if [ "$status" == 1 -a "$op" != "" ]; then
    echo $input | jq '.'
    exit 127
fi

parent_id=$(echo $input | jq '.id' | sed -e 's/^"//' -e 's/"$//')

# 先发送验证码
echo "sleeping 5 seconds..." >&2
sleep 5

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
    echo $ret | jq '.' >&2
    exit 127
fi

bank_list=$(echo $ret | jq '.bank_list' | sed -e 's/^"//' -e 's/"$//')
bank_sms_time=$(echo $ret | jq '.bank_sms_time' | sed -e 's/^"//' -e 's/"$//')

echo "sleeping 5 seconds..." >&2
sleep 5

echo "making preauth done request..." >&2

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
         -d parent_id=$parent_id \
         http://58.67.212.197:8081/preauth/done
   )

retcode=$(echo $ret | jq '.status')

if [ $retcode -ne 0 ]; then
    echo [fail] preauth done >&2
    echo $ret | jq '. | {status: .status, message: .message, op: "preauth_done"}'
    exit 127
fi

echo $ret | jq '.trans'
