#!/bin/bash

# 退货

# 接收标准输入：
# {
#     "bank_list": "20170228111959",
#     ...
# }

input=$(cat -)
bank_list=$(echo $input | jq '.bank_list' | sed -e 's/^"//' -e 's/"$//')

echo "making refund request..." >&2

ret=$(
    curl -s \
         -d bank_list=$bank_list \
         http://58.67.212.197:8081/trans/refund
   )

retcode=$(echo $ret | jq '.status')

if [ $retcode -ne 0 ]; then
    echo [fail] refund >&2
    echo $ret | jq '.' >&2
    exit 127
fi

echo $ret | jq '.'