import json
import time
from hashlib import sha256
from urllib import parse, request


class Conf(object):
    # payment environ[SANDBOX, LIVE]
    environ = ''

    # account email
    account = ''

    # merchant name
    mch_name = ''

    # account secret key
    secret_key = ''

    # embed page js key
    embed_key = ''

    # request timeout
    timeout = 30.0

    def __init__(self, account: str, secret_key: str, environ: str = 'sandbox', mch_name: str = '', embed_key: str = "",
                 timeout: float = 30.0):
        if environ not in [Const.LIVE, Const.SANDBOX]:
            raise TypeError("environ must be one of: " + Const.LIVE + "," + Const.SANDBOX)
        if account == '':
            raise Exception("account is empty")
        if secret_key == '':
            raise Exception("secret_key is empty")
        self.account = account
        self.secret_key = secret_key
        self.environ = environ
        self.embed_key = embed_key
        self.mch_name = mch_name
        self.timeout = timeout


class Glocash(object):

    def __init__(self, account: str, secret_key: str, environ: str = 'sandbox', mch_name: str = '', embed_key: str = "",
                 timeout=30.0):
        environ = environ.lower()
        self.__conf = Conf(
            account=account,
            secret_key=secret_key,
            environ=environ if environ == 'sandbox' else Const.LIVE,
            mch_name=mch_name,
            timeout=timeout,
            embed_key=embed_key,
        )

    def pay(self, d: dict) -> dict:
        """
        Classic payment api method
        :param d:
        :return:
        """

        url = (Const.SCHEME + self.__conf.environ + '.' + Const.DOMAIN + '/gateway/payment/index')
        p = self.__prepare_param(d, self.__pay_tpl)
        self.payment_sign(self, p, self.__conf.secret_key)
        return self.post(self, url, p)

    def pay_direct(self, d: dict) -> dict:
        """
        Direct payment method, Notice: You need to apply for a PCI certification to use this payment api
        :param d:
        :return:
        """

        url = (Const.SCHEME + self.__conf.environ + '.' + Const.DOMAIN + '/gateway/payment/ccDirect')
        p = self.__prepare_param(d, self.__pay_direct_tpl)
        self.payment_sign(self, p, self.__conf.secret_key)
        return self.post(self, url, p)

    def embed(self, d) -> str:
        """
        this method make a javascript label and return, join it in your html page
        :param d:
        :return:
        """

        url = (Const.SCHEME + self.__conf.environ + '.' + Const.DOMAIN + '/public/gateway/js/embed.js')
        p = self.__prepare_param(d, self.__embed_tpl, False)
        script_js = "<script src=" + url
        for k in p:
            script_js += ' "' + k + '"="' + p[k]
        script_js += ' >'
        return script_js

    def refund(self, d: dict) -> dict:
        """
        Refund amount transaction to user
        :param d:
        :return:
        """

        url = (Const.SCHEME + self.__conf.environ + '.' + Const.DOMAIN + '/gateway/transaction/refund')
        p = self.__prepare_param(d, self.__refund_tpl)
        self.refund_sign(self, p, self.__conf.secret_key)
        return self.post(self, url, p)

    def query(self, d: dict) -> dict:
        """
        Query transaction by TNS_GCID OR REQ_INVOICE
        :param d:
        :return:
        """

        url = (Const.SCHEME + self.__conf.environ + '.' + Const.DOMAIN + '/gateway/transaction/index')
        p = self.__prepare_param(d, self.__query_tpl)
        self.query_sign(self, p, self.__conf.secret_key)
        return self.post(self, url, p)

    @staticmethod
    def sign(self, s: str) -> str:
        """
        Make sha256 sign str
        :param self:
        :param s: str
        :return: str
        """
        return sha256(s.encode()).digest().hex().lower()

    @staticmethod
    def refund_sign(self, d: dict, key: str) -> dict:
        """
        Add sign string into param d for http transaction refund action
        :param self:
        :param d: Dict, request param
        :param key: str, account key
        :return: Dict
        """

        d["REQ_SIGN"] = self.sign(self, key + d["REQ_TIMES"] + d["REQ_EMAIL"] + d["TNS_GCID"] + d["PGW_PRICE"])
        return d

    @staticmethod
    def payment_sign(self, d: dict, key: str) -> dict:
        """
        Add sign string into param d for http transaction payment action
        :param self:
        :param d: Dict, request param
        :param key: str, account key
        :return: Dict
        """

        d["REQ_SIGN"] = self.sign(self, key + d["REQ_TIMES"] + d["REQ_EMAIL"] + d["REQ_INVOICE"] + d["CUS_EMAIL"] +
                                  d["BIL_METHOD"] + d["BIL_PRICE"] + d["BIL_CURRENCY"])
        return d

    @staticmethod
    def query_sign(self, d: dict, key: str) -> dict:
        """
        Add sign string into param d for http transaction query action
        :param self:
        :param d: Dict, request param
        :param key: str, account key
        :return: Dict
        """

        d["REQ_SIGN"] = self.sign(self, key + d["REQ_TIMES"] + d["REQ_EMAIL"] + d["REQ_INVOICE"] + d["TNS_GCID"])
        return d

    @staticmethod
    def is_legal_notify(self, d: dict, key) -> bool:
        """
        Check notify data whether legal data from glocash
        :param self:
        :param d: Dict
        :param key:
        :return:
        """
        s = self.sign(self, key + d["REQ_TIMES"] + d["REQ_EMAIL"] + d["CUS_EMAIL"] + d["TNS_GCID"] + d["BIL_STATUS"] +
                      d["BIL_METHOD"] + d["PGW_PRICE"] + d["PGW_CURRENCY"])
        if s == d["REQ_SIGN"]:
            return True
        else:
            return False

    @staticmethod
    def post(self, url: str, data: dict) -> dict:
        """
        Send http post request and return dict data
        :param self:
        :param url:
        :param data:
        :return:
        """

        post_data = parse.urlencode(data).encode('ascii')
        header = {
            'User-Agent': 'python/httpclient',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }
        req = request.Request(url, data=post_data, headers=header, method='POST', unverifiable=True)
        req.timeout = self.__conf.timeout
        res = request.urlopen(req, timeout=self.__conf.timeout)
        json_str = str(res.read(), 'utf-8')
        return json.loads(json_str)

    def __prepare_param(self, d: dict, tpl: dict, f: bool = True) -> dict:
        """
        According to tpl to build param
        :param d:
        :param tpl:
        :return:
        """

        p = {}
        for k in tpl:
            v = d.get(k)
            if f and v:
                p[k] = v
            if f:
                p[k] = tpl[k]
        if 'd-emkey' in tpl:
            p["d-emkey"] = self.__conf.embed_key
            p["d-merchant"] = self.__conf.mch_name
            p["d-sandbox"] = '1' if self.__conf.environ == 'sandbox' else '0'
        else:
            p["REQ_EMAIL"] = self.__conf.account
            p["REQ_MERCHANT"] = self.__conf.mch_name
            p["REQ_TIMES"] = str(int(time.time()))
            p["REQ_SANDBOX"] = '1' if self.__conf.environ == 'sandbox' else '0'
            p["REQ_SANDBOX"] = '1' if self.__conf.environ == 'sandbox' else '0'
        return p

    __conf: Conf

    __pay_tpl = {
        "REQ_EMAIL": "",
        "REQ_MERCHANT": "",
        "REQ_SIGN": "",
        "REQ_SANDBOX": "",
        "REQ_INVOICE": "",
        "REQ_TIMES": "",
        "MCH_URLPOST": "",
        "CUS_EMAIL": "",
        "CUS_COUNTRY": "",
        "CUS_PHONE": "",
        "CUS_MOBILE": "",
        "CUS_IMUSR": "",
        "CUS_STATE": "",
        "CUS_CITY": "",
        "CUS_ADDRESS": "",
        "CUS_POSTAL": "",
        "CUS_FNAME": "",
        "CUS_LNAME": "",
        "CUS_REGISTER": "",
        "BIL_METHOD": "",
        "BIL_PRICE": "",
        "BIL_CURRENCY": "",
        "BIL_PRCCODE": "",
        "BIL_GOODSNAME": "",
        "BIL_QUANTITY": "",
        "BIL_CC3DS": "",
        "URL_SUCCESS": "",
        "URL_PENDING": "",
        "URL_FAILED": "",
        "URL_NOTIFY": "",
        "URL_LOADING": "",
        "URL_RETURN": "",
        "BIL_SELLER_EMAIL": "",
        "BIL_SELLER_URL": "",
        "BIL_SELLER_GOODSNAME": "",
        "BIL_GOODS_URL": "",
        "BIL_RAW_PRICE": "",
        "BIL_RAW_CURRENCY": "",
        "MCH_DOMAIN_KEY": "",
        "REQ_MODE": "",
        "IFS_MODE": "",
        "IFS_URL": "",
        "REC_STIME": "",
        "REC_INPRICE": "",
        "REC_PERIOD": "",
        "REC_INTERVAL": "",
        "REC_RETRIES": "",
        "BIL_TYPE": "",
        "CUSTOM_FD0": "",
        "CUSTOM_FD1": "",
        "CUSTOM_FD2": "",
        "CUSTOM_FD3": "",
        "CUSTOM_FD4": "",
        "CUSTOM_FD5": "",
        "CUSTOM_FD6": "",
        "CUSTOM_FD7": "",
    }

    __pay_direct_tpl = {
        "REQ_TIMES": "",
        "REQ_SIGN": "",
        "REQ_EMAIL": "",
        "REQ_INVOICE": "",
        "REQ_MERCHANT": "",
        "REQ_SANDBOX": "",
        "MCH_URLPOST": "",
        "CUS_EMAIL": "",
        "CUS_COUNTRY": "",
        "CUS_PHONE": "",
        "CUS_MOBILE": "",
        "CUS_IMUSR": "",
        "CUS_STATE": "",
        "CUS_CITY": "",
        "CUS_ADDRESS": "",
        "CUS_POSTAL": "",
        "CUS_FNAME": "",
        "CUS_LNAME": "",
        "CUS_REGISTER": "",
        "BIL_METHOD": "",
        "BIL_PRICE": "",
        "BIL_CURRENCY": "",
        "BIL_PRCCODE": "",
        "BIL_GOODSNAME": "",
        "BIL_QUANTITY": "",
        "BIL_GOODS_URL": "",
        "BIL_CC3DS": "",
        "BIL_IPADDR": "",
        "BIL_CCNUMBER": "",
        "BIL_CCHOLDER": "",
        "BIL_CCEXPM": "",
        "BIL_CCEXPY": "",
        "BIL_CCCVV2": "",
        "URL_SUCCESS": "",
        "URL_PENDING": "",
        "URL_FAILED": "",
        "URL_NOTIFY": "",
        "URL_LOADING": "",
        "DEV_ACCEPT": "",
        "DEV_UAGENT": "",
        "BIL_REQ_KEY": "",
        "MCH_DOMAIN_KEY": "",
        "REC_STIME": "",
        "REC_INPRICE": "",
        "REC_PERIOD": "",
        "REC_INTERVAL": "",
        "REC_RETRIES": "",
        "BIL_TYPE": "",
        "CUSTOM_FD0": "",
        "CUSTOM_FD1": "",
        "CUSTOM_FD2": "",
        "CUSTOM_FD3": "",
        "CUSTOM_FD4": "",
        "CUSTOM_FD5": "",
        "CUSTOM_FD6": "",
        "CUSTOM_FD7": "",
    }

    __refund_tpl = {
        "REQ_TIMES": "",
        "REQ_EMAIL": "",
        "TNS_GCID": "",
        "PGW_PRICE": "",
    }

    __query_tpl = {
        "REQ_TIMES": "",
        "REQ_EMAIL": "",
        "REQ_INVOICE": "",
        "TNS_GCID": "",
    }

    __embed_tpl = {
        "d-emkey": "",
        "d-invoice": "",
        "d-merchant": "",
        "d-sandbox": "",
        "d-urlpost": "",
        "d-email": "",
        "d-goodsname": "",
        "d-quantity": "",
        "d-price": "",
        "d-currency": "",
        "d-method": "",
        "d-prccode": "",
        "d-goodsurl": "",
        "d-suceess": "",
        "d-pending": "",
        "d-failed": "",
        "d-notify": "",
        "d-return": "",
        "d-custom0": "",
        "d-custom1": "",
        "d-custom2": "",
        "d-pagecomp": "",
        "d-cc3ds": "",
        "d-mode": "",
        "d-raw-price": "",
        "d-raw-currency": "",
        "d-domain-key": "",
        "d-ifs-mode": "",
        "d-ifs-url": "",
        "d-type": "",
        "d-interval": "",
        "d-period": "",
        "d-inprice": "",
        "d-stime": "",
        "d-retries": "",
    }


class Const(object):

    SANDBOX = "sandbox"

    LIVE = 'pay'

    SCHEME = 'https://'

    DOMAIN = 'glocashpayment.com'

