#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.framework import get_list
from base.framework import ApiJsonErrorResponse
from base import constant as const


def settle(db, list_id):
    """
    1、只有支付成功的交易单才会结算；

    2、已经结算成功的不会重复被结算；

    3、每次只结算一笔订单。
    """
    is_ok, list_ret = get_list(
        db, list_id, const.TRANS_STATUS.PAY_SUCCESS)
    if not is_ok:
        return ApiJsonErrorResponse(list_ret)
    if list_ret['settle_time'] is not None:
        return ApiJsonErrorResponse(const.API_ERROR.REPEAT_SETTLE)
