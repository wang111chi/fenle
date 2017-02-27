#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
from base64 import b64decode
import urllib
from contextlib import contextmanager, closing

from flask import make_response, render_template, redirect, request
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as sign_PKCS1_v1_5
from Crypto.Hash import SHA
from sqlalchemy.sql import text, select
from sqlalchemy import and_

import config
from base import dblogic as dbl
from base import logger
from base.db import engine, meta
from base.db import t_merchant_info
from base.db import t_trans_list
from base.db import t_sp_balance
from base import util
from base.xform import FormChecker
from base import constant as const


def _update_sp_balance(spid, account_class, balance, now,
                       cur_type=const.CUR_TYPE.RMB):
    """return a sql without execute"""
    return t_sp_balance.update().where(and_(
        t_sp_balance.c.spid == spid,
        t_sp_balance.c.cur_type == cur_type,
        t_sp_balance.c.account_class == account_class
    )).values(
        balance=t_sp_balance.c.balance + balance,
        modify_time=now)


def get_list(db, list_id, what_status=None):
    sel = select([
        t_trans_list.c.status,
        t_trans_list.c.sp_userid,
        t_trans_list.c.sp_tid,
        t_trans_list.c.paynum,
        t_trans_list.c.fee,
        t_trans_list.c.cur_type,
        t_trans_list.c.divided_term,
        t_trans_list.c.fee_duty,
        t_trans_list.c.memo,
        t_trans_list.c.money,
        t_trans_list.c.paysucc_time,
        t_trans_list.c.product_type,
        t_trans_list.c.bank_type]).where(
        t_trans_list.c.list_id == list_id)
    list_ret = db.execute(sel).first()
    if list_ret is None:
        return False, const.API_ERROR.LIST_ID_NOT_EXIST
    if what_status == const.TRANS_STATUS.PAY_SUCCESS:
        if list_ret['status'] != const.TRANS_STATUS.PAY_SUCCESS:
            return False, const.API_ERROR.LIST_STATUS_ERROR
    return True, list_ret


def get_sp_pubkey(db, spid):
    """从mysql获取商户公钥"""
    s = select([t_merchant_info.c.rsa_pub_key]).where(
        t_merchant_info.c.spid == spid)
    merchant_ret = db.execute(s).first()
    return merchant_ret['rsa_pub_key']


def general(desc):
    def deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            resp = old_handler(*args, **kwargs)

            if isinstance(resp, TempResponse):
                # 添加自定义变量
                resp.context_update(
                    const=const,
                )

            if isinstance(resp, Response):
                output = resp.output()
                if config.DEBUG:
                    logger.get("response-log").debug("u[%s] %s" % (
                        request.url, output.get_data(as_text=True)))
                return output
            return resp

        new_handler.desc = desc
        new_handler.is_handler = True
        return new_handler
    return deco


class Response(object):
    def __init__(self):
        self._ext_header = {}
        self._ext_cookie = {}

    def set_header(self, key, value):
        self._ext_header[key] = value

    def set_cookie(self, key, value, **kwargs):
        self._ext_cookie[key] = (value, kwargs)

    def output(self):
        resp = make_response(self._output())

        for k, v in self._ext_header.items():
            resp.headers[k] = v

        for k, v in self._ext_cookie.items():
            resp.set_cookie(k, v[0], **v[1])

        return resp

    def _output(self):
        return "", 404


class JsonResponse(Response):
    def __init__(self, **kwargs):
        Response.__init__(self)
        self._ext_header["Content-Type"] = "application/json"
        self._json = {} if kwargs is None else kwargs

    def _output(self):
        return util.safe_json_dumps(self._json)


class JsonOkResponse(JsonResponse):
    def __init__(self, **kwargs):
        JsonResponse.__init__(self)

        self._json = {
            "status": const.REQUEST_STATUS.SUCCESS,
            "message": u"成功",
        }
        self._json.update(kwargs)


class JsonErrorResponse(JsonResponse):
    def __init__(self, message, status=const.REQUEST_STATUS.FAIL):
        if isinstance(message, (list, tuple)):
            message = ", ".join(message)
        JsonResponse.__init__(self, status=status, message=message)


class ApiJsonErrorResponse(JsonResponse):
    def __init__(self, retcode=None, retmsg=None):
        if retmsg is None:
            retmsg = const.API_ERROR.NAMES.get(retcode, "")
        if isinstance(retmsg, (list, tuple)):
            retmsg = ", ".join(retmsg)
        JsonResponse.__init__(self, retcode=retcode, retmsg=retmsg)


class ApiJsonOkResponse(JsonResponse):
    def __init__(self, retmsg=u"成功", **kwargs):
        JsonResponse.__init__(
            self, retcode=const.REQUEST_STATUS.SUCCESS,
            retmsg=retmsg, **kwargs)


class TempResponse(Response):
    def __init__(self, template_name, **context):
        Response.__init__(self)
        self._ext_header["Content-Type"] = "text/html"
        self._template_name = template_name
        self._context = context

    def context_update(self, **kwargs):
        self._context.update(kwargs)

    def _output(self):
        return render_template(self._template_name, **self._context)


def db_conn(old_handler):
    @wraps(old_handler)
    def new_handler(*args, **kwargs):
        kwargs.update(db=engine.connect())
        return old_handler(*args, **kwargs)

    return new_handler


def form_check(settings, var_name="safe_vars", strict_error=True,
               error_handler=None, error_var="form_errors"):

    def new_deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            req_data = {}
            for k, v in settings.items():
                if v.multiple:
                    req_data[k] = request.values.getlist(k)
                else:
                    req_data[k] = request.values.get(k, None)

            checker = FormChecker(req_data, settings)
            if not checker.is_valid():
                if strict_error:
                    error_msg = [
                        v for v in checker.get_error_messages().values() if
                        v is not None
                    ]
                    if error_handler is None:
                        err_handler = JsonErrorResponse
                        return err_handler(error_msg)
                    else:
                        return error_handler(error_msg)
                else:
                    kwargs[error_var] = checker.get_error_messages()
                    return old_handler(*args, **kwargs)

            valid_data = checker.get_valid_data()
            kwargs[var_name] = valid_data

            response = old_handler(*args, **kwargs)
            if isinstance(response, TempResponse):
                response.context_update(**{var_name: valid_data})

            return response
        return new_handler
    return new_deco


def api_form_check(settings, is_encrypted=True, var_name="safe_vars"):
    def new_deco(old_handler):
        @wraps(old_handler)
        def new_handler(*args, **kwargs):
            trusted_ip = False

            ip = request.remote_addr
            logger.debug(ip)
            if ip in config.CLIENT_IP_WHITELIST:
                trusted_ip = True

            if not trusted_ip and is_encrypted:
                cipher_data = request.values.get("cipher_data", None)
                if cipher_data is None:
                    return ApiJsonErrorResponse(const.API_ERROR.DECRYPT_ERROR)

                # RSA解密
                try:
                    cipher_data = b64decode(cipher_data)
                except ValueError:
                    return ApiJsonErrorResponse(const.API_ERROR.DECRYPT_ERROR)

                fenle_private_key = RSA.importKey(config.FENLE_PRIVATE_KEY)
                cipher = PKCS1_v1_5.new(fenle_private_key)

                message = util.pkcs_decrypt(cipher, cipher_data)

                if message is None:
                    return ApiJsonErrorResponse(const.API_ERROR.DECRYPT_ERROR)

                params = urllib.parse.parse_qs(message)
            else:
                params = request.values.to_dict(flat=False)

            # 参数检查
            req_data = {}
            for k, v in settings.items():
                param = params.get(k, None)
                if v.multiple:
                    req_data[k] = [] if param is None else param
                else:
                    req_data[k] = None if param is None else param[0]

            checker = FormChecker(req_data, settings)
            if not checker.is_valid():
                error_msg = [
                    v for v in checker.get_error_messages().values() if
                    v is not None
                ]
                return ApiJsonErrorResponse(
                    const.API_ERROR.PARAM_ERROR, error_msg)

            valid_data = checker.get_valid_data()

            # 从mysql检查商户spid是否存在
            s = select([t_merchant_info.c.status,
                        t_merchant_info.c.mer_key,
                        t_merchant_info.c.rsa_pub_key]).where(
                t_merchant_info.c.spid == valid_data['spid'])
            conn = engine.connect()
            sel_result = conn.execute(s).first()
            if sel_result is None:
                return ApiJsonErrorResponse(const.API_ERROR.SPID_NOT_EXIST)
            elif sel_result['status'] == 1:  # 判断是否被封禁
                return ApiJsonErrorResponse(const.API_ERROR.MERCHANT_FORBID)

            if not trusted_ip:
                # 验签
                encode_type = valid_data["encode_type"]
                if encode_type == const.ENCODE_TYPE.MD5:
                    check_sign_valid = util.check_sign_md5(
                        sel_result.mer_key,
                        params)
                else:  # encode_type == const.ENCODE_TYPE.RSA:
                    check_sign_valid = util.check_sign_rsa(
                        sel_result.rsa_pub_key,
                        params)

                if not check_sign_valid:
                    return ApiJsonErrorResponse(const.API_ERROR.SIGN_INVALID)

            kwargs[var_name] = valid_data
            return old_handler(*args, **kwargs)

        return new_handler
    return new_deco


class Job(object):

    """A indicator to mark whether the job is finished."""

    def __init__(self):
        self._finished = False

    def is_finished(self):
        return self._finished

    def finish(self):
        self._finished = True


@contextmanager
def transaction(conn):
    """
    Automatic handle transaction COMMIT/ROLLBACK.

    You MUST call trans.finish(),
    if you want to COMMIT; Otherwise(not call or exception occurs), ROLLBACK.

    >>> with transaction(conn) as trans:
    >>>     do something...
    >>>     if xxxxx:
    >>>         # if you don't want to commit,
    >>>         # you just not call trans.finish().
    >>>         return error_page("xxxxxx")
    >>>     # if you want to commit, you call:
    >>>     trans.finish()

    @param conn: database connection
    """
    job = Job()
    trans = conn.begin()

    try:
        yield job
    except:
        trans.rollback()
        raise

    if job.is_finished():
        trans.commit()
    else:
        trans.rollback()
