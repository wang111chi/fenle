#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
input_form = {
    'name': (8 <= F_str('abc', 'default-xxx') <= 32) & 'optional',
    'age': (10 <= F_int() & 'optional' <= 100),
    'choices': ((1 <= F_int() <= 10) & 'C' & 'required'
        & (lambda v: v % 2 == 0)),
    'email': ((2 <= F_email('邮箱地址') <= 32) & 'optional' & {
            'default': '%(name)s 正确格式是: xxxx@xxx.com',
        }),
    'url': (8 <= F_str('链接', format=r'http://[\w./&?+~]+') <= 1024) & 'optional',
}

fc = FormChecker(req, input_form, err_msg_encoding='utf-8')

fc.is_valid()
fc.err_msg
fc.raw_data
fc.valid_data
"""

__all__ = [
    'F_str',
    'F_int',
    'F_float',
    'F_email',
    'F_urs',
    'F_mobile',
    'F_phone',
    'F_idnum',
    'F_datetime',
]

_default_encoding = 'utf8'
_default_messages = {
    'max': '%(name)s 的最大值为%(max)s',
    'min': '%(name)s 最小值为%(min)s',
    'max_len': '%(name)s 最大长度为%(max_len)s个字符',
    'min_len': '%(name)s 最小长度为%(min_len)s个字符',
    'blank': '%(name)s 不能为空',
    'callback': '%(name)s 输入出错了',
    'format': '%(name)s 格式有错',
    'default': '%(name)s 格式有错',
}


class Input(object):
    _type = None
    _min = None
    _max = None
    _optional = False
    _multiple = False
    _strict = False  # means empty string will treat as no input
    _attrs = ('optional', 'required', 'multiple', 'strict')

    _callbacks = (lambda v: (True, v),)
    _clean_data = None
    _raw_data = None
    _default_value = None

    _message_key = None

    def __init__(self, field_name=None, default_value=None):
        self._messages = {}
        self._messages.update(_default_messages)
        self._message_vars = {
            'name': field_name,
        }
        if default_value is not None:
            self._default_value = default_value

    @property
    def multiple(self):
        return self._multiple

    def _check(self, value):
        raise NotImplementedError('you should use sub-class for checking')

    def check_multi(self, values):
        if not values and not self._optional:
            message = self._messages.get('blank') or self._messages['default']
            message = message % self._message_vars
            return False, values, None, message

        valid_data = []
        for value in values:
            valid, origin, valid_value, message = self.check_value(value)
            if not valid:
                return False, values, None, message
            valid_data.append(valid_value)

        return True, values, valid_data, None

    def check_value(self, raw):
        valid, valid_data, message = False, None, None
        value = raw
        if value is None or (value == '' and self._strict):
            if self._default_value is not None:
                if callable(self._default_value):
                    return True, raw, self._default_value(), None
                return True, raw, self._default_value, None
            else:
                value = None

        # `None' means the client does not send the field's value,
        # this differs from empty string, although when `strict' is specified, they are the same.
        # if value:
        if value is not None:
            valid, data = self._check(value)
            if valid:
                valid, data = self._callbacks[0](data)
                if valid:
                    valid_data = data
                else:
                    message = self._messages['callback']
            else:
                message = data

        elif self._optional:
            valid = True
            valid_data = value

        # value is empty and is not optional
        else:
            message = self._messages['blank']

        if message:
            message = message % self._message_vars

        return valid, raw, valid_data, message

    def check(self, name, value):
        '''
        @param name: field name of the form
        @param value: field value
        @return: a tuple of 4 items:
            the first indicates if the value is valid
            the second is the raw data of user input
            the third is the valid data or, if not valid, is None
            the last is error message or, if valid, is None
        '''
        if self._message_vars['name'] is None:
            self._message_vars['name'] = name

        if self._multiple:
            return self.check_multi(value)
        else:
            return self.check_value(value)

    def __and__(self, setting):
        if callable(setting):
            self._callbacks = (setting,)
        elif isinstance(setting, dict):
            self._messages.update(setting)
        elif setting in self._attrs:
            value = True
            if setting == 'required':
                setting = 'optional'
                value = False

            attr = '_%s' % setting
            if hasattr(self, attr):
                setattr(self, attr, value)
        else:
            raise NameError('%s is not support' % setting)

        return self

    def __lt__(self, max_value):
        raise NotImplementedError('"<" is not supported now')

    def __gt__(self, min_value):
        raise NotImplementedError('">" is not supported now')

    def __le__(self, max_value):
        self._max = max_value
        self._message_vars['max'] = max_value
        self._message_vars['max_len'] = max_value
        return self

    def __ge__(self, min_value):
        self._min = min_value
        self._message_vars['min'] = min_value
        self._message_vars['min_len'] = min_value
        return self

    def _check_mm(self, value):
        if self._max is not None and value > self._max:
            self._message_key = 'max'
            return False
        if self._min is not None and value < self._min:
            self._message_key = 'min'
            return False
        return True


class F_float(Input):
    _strict = True

    def _check(self, value):
        try:
            value = float(value)
        except ValueError:
            return False, self._messages['default']

        if not self._check_mm(value):
            message = self._messages[self._message_key]
            return False, message

        return True, value


class F_int(Input):
    _strict = True

    def _check(self, value):
        try:
            value = int(value)
        except ValueError:
            return False, self._messages['default']

        if not self._check_mm(value):
            message = self._messages[self._message_key]
            return False, message

        return True, value


class F_str(Input):
    def __init__(self, field_name=None,
            default_value=None, format=None):
        super(F_str, self).__init__(field_name, default_value)
        self._format = format

    def _check(self, value):
        if not self._check_mm(len(value)):
            message = self._messages[self._message_key + '_len']
            return False, message

        if self._format:
            import re
            if not re.match(self._format, value):
                return False, self._messages['format']
        return True, value


class F_email(F_str):
    def _check(self, value):
        if not self._check_mm(len(value)):
            message = self._messages[self._message_key + '_len']
            return False, message
        return self.is_email(value)

    def is_email(self, value):
        import re
        email = re.compile(r"^[\w.%+-]+@(?:[A-Z0-9-]+\.)+[A-Z]{2,4}$", re.I)
        if not email.match(value):
            return False, self._messages['default']
        return True, value


class F_urs(F_email):
    _min_urs_length = 6
    _max_urs_length = 60

    def _check(self, value):
        if self._max is None:
            self._max = self._max_urs_length
            self._message_vars['max_len'] = self._max
        if self._min is None:
            self._min = self._min_urs_length
            self._message_vars['min_len'] = self._min

        if not self._check_mm(len(value)):
            message = self._messages[self._message_key + '_len']
            return False, message

        value = value.lower()
        return self.is_email(value)


class F_idnum(Input):
    def _check(self, value):
        from idnum import IsIdNum
        valid = IsIdNum(value)
        if valid:
            data = value
        else:
            data = self._messages['default']
        return valid, data


class F_phone(Input):
    def _check(self, value):
        if not self._check_mm(len(value)):
            message = self._messages[self._message_key + '_len']
            return False, message

        valid = value.replace('-', '').replace(' ', '').isdigit()
        if not valid:
            data = self._messages['default']
        else:
            data = value
        return valid, data


class F_mobile(Input):
    def _check(self, value):
        valid = (value and
                value.startswith('1') and
                value.isdigit() and
                len(value) == 11)
        if valid:
            data = value
        else:
            data = self._messages['default']
        return valid, data


class F_datetime(Input):
    def __init__(self, field_name=None,
                 default_value=None, format='%Y-%m-%d %H:%M:%S'):
        super(F_datetime, self).__init__(field_name, default_value)
        self._format = format

    def _check(self, value):
        from datetime import datetime
        from time import strptime
        try:
            return True, datetime(*strptime(value, self._format)[0:6])
        except ValueError:
            return False, self._messages['format']


# form checker
class FormChecker(object):
    def __init__(self, source, input_form, method='both'):
        """
        @param source: data source, can be object with properties GET, POST and VAR, or a dict-like object
        @param input_form: form setting
        @param method: GET or POST, or BOTH, if source is dict-like object, ignored
        @param err_msg_encoding: encoding of string of error message
        """
        self._source = source
        self._form = input_form
        self._checked = False
        self._method = method

    def check(self, source=None):
        method = self._method.upper()

        if source is None:
            # if is a dict or some others with a `get' method
            if hasattr(self._source, 'get'):
                source = self._source
            # request object
            elif method == 'GET':
                source = self._source.GET
            elif method == 'POST':
                source = self._source.POST
            else:
                source = self._source.VAR

        form = self._form

        valid_data, raw_data, messages = {}, {}, {}
        self._valid = True

        for field, checker in form.items():

            if checker.multiple and hasattr(source, 'getall'):
                value = source.getall(field)
            else:
                value = source.get(field, None)

            valid, raw_data[field], v, m = checker.check(field, value)
            if valid:
                valid_data[field] = v
            else:
                messages[field] = m

            self._valid = self._valid and valid

        self._raw_data = raw_data
        self._valid_data = valid_data
        self._messages = messages
        self._checked = True

    def is_valid(self):
        if not self._checked:
            self.check()
        return self._valid

    def get_error_messages(self):
        return self.err_msg

    @property
    def err_msg(self):
        if not self._checked:
            self.check()
        return self._messages

    def get_valid_data(self):
        return self.valid_data

    @property
    def valid_data(self):
        if not self._checked:
            self.check()
        return self._valid_data

    def get_raw_data(self):
        return self._raw_data

    @property
    def raw_data(self):
        return self._raw_data
