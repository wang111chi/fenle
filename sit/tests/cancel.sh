#!/bin/bash

# 撤消

# 接收标准输入：
# {
#     "bank_list": "20170228111959",
#     ...
# }

input=$(cat -)

status=$(echo $input | jq '.status')
op=$(echo $input | jq '.op')

if [ "$status" == 1 -a "$op" != "null" ]; then
    echo $input | jq '.'
    exit 127
fi

bank_list=$(echo $input | jq '.bank_list' | sed -e 's/^"//' -e 's/"$//')

echo "sleeping 5 seconds..." >&2
sleep 5

echo "making cancel request..." >&2

ret=$(
    curl -s \
         -d bank_list=$bank_list \
         http://58.67.212.197:8081/trans/cancel
   )

echo $ret

retcode=$(echo $ret | jq '.status')

if [ $retcode -ne 0 ]; then
    echo [fail] cancel >&2
    echo $ret | jq '. | {status: .status, message: .message, op: "cancel"}'
    exit 127
fi

echo $ret | jq '.'
