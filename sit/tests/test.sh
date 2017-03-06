#! /bin/bash

function enter_test() {
    echo 测试$1...
    stage=$1
    sleep 5
}

function leave_test() {
    if [ $? -eq 0 ]; then
        echo $stage 成功 >> $f
    else
        echo $stage 失败 >> $f
    fi
}

function send_sms() {
    enter_test 发短信
    ./sms.sh
    leave_test
}

function layaway() {
    enter_test 分期交易
    ./sms.sh | ./layaway.sh
    leave_test
}

function cancel_layaway() {
    enter_test 分期交易撤销
    ./sms.sh | ./layaway.sh | ./cancel.sh
    leave_test
}

function consume() {
    enter_test 普通刷卡消费
    ./sms.sh | ./consume.sh
    leave_test
}

function cancel_consume() {
    enter_test 普通刷卡消费撤销
    ./sms.sh | ./consume.sh | ./cancel.sh
    leave_test
}

function point() {
    enter_test 积分交易
    ./sms.sh | ./point.sh
    leave_test
}

function cancel_point() {
    enter_test  积分交易撤销
    ./sms.sh | ./point.sh | ./cancel.sh
    leave_test
}

function point_cash() {
    enter_test  积分加现金交易
    ./sms.sh | ./point_cash.sh
    leave_test
}

function cancel_point_cash() {
    enter_test 积分加现金交易撤销
    ./sms.sh | ./point_cash.sh | ./cancel.sh
    leave_test
}

function preauth() {
    enter_test 预授权交易
    ./sms.sh | ./preauth.sh
    leave_test
}

function cancel_preauth() {
    enter_test 预授权交易撤销
    ./sms.sh | ./preauth.sh | ./cancel.sh
    leave_test
}

function preauth_done() {
    enter_test 预授权完成交易
    ./sms.sh | ./preauth.sh | ./preauth_done.sh
    leave_test
}

function cancel_preauth_done() {
    enter_test 预授权完成交易撤销
    ./sms.sh | ./preauth.sh | ./preauth_done.sh | ./cancel.sh
    leave_test
}

operations="send_sms layaway cancel_layaway consume cancel_consume \
point cancel_point point_cash cancel_point_cash preauth cancel_preauth \
preauth_done cancel_preauth_done"

while getopts o: options; do
    operations="$OPTARG"
done

eval f=\$$OPTIND
f=${f:-/dev/stdout}
echo -n >$f

for operation in $operations; do
    $operation
done
