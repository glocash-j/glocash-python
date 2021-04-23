import time
from glocash import Glocash, Const

"""
Prepare config for glocash payment api necessary info 
"""
conf = {
    # Select environ
    'environ': Const.LIVE,
    # your account email
    'account': '2101653220@qq.com',
    # secret key for environ, notice: The live environ secret key active your account
    'secret_key': 'c2e38e7d93dbdd3efaa61028c3d27a1a2577df84fa62ae752df587b4f90b8ef7',
    # In your html page to use glocash payment fastly, need this key for javascript secret key
    'embed_key': 'UlEHFQJWClJCUQ==.QDI=',
    # The name of the merchant will be displayed on the page where the user enters the credit card
    'mch_name': 'test merchant',
    # request exec timeout
    'timeout': 30
}

glocash = Glocash(
    environ=conf['environ'],
    secret_key=conf['secret_key'],
    embed_key=conf['embed_key'],
    mch_name=conf['mch_name'],
    account=conf['account'],
    timeout=conf['timeout']
)
p = {
    "REQ_INVOICE": time.time(),
    "BIL_PRICE": "98.03",
    "BIL_CURRENCY": "USD",
    "BIL_GOODSNAME": "DEFAULT GOODS",
    "BIL_QUANTITY": "0",
    "BIL_CC3DS": "0",
    "BIL_METHOD": "C01",
    "CUS_EMAIL": "customemail@example.com",
    "CUS_COUNTRY": "US",
    "CUS_ADDRESS": "Dearborn Stree 8645 code forbidden",
    "CUS_POSTAL": "854423",
    "URL_FAILED": "http://localhost/failed",
    "URL_SUCCESS": "http://localhost/success",
    "URL_PENDING": "http://localhost/pending",
    "URL_NOTIFY": "http://localhost/notify",
    "CUSTOM_FD1": "custom field 1",
    "CUSTOM_FD2": "custom field 2",
    "CUSTOM_FD3": "custom field 3",
    "CUSTOM_FD4": "custom field 4",
    "CUSTOM_FD5": "custom field 5",
    "CUSTOM_FD6": "custom field 6",
    "CUSTOM_FD7": "custom field 7",
    "TNS_GCID": 'SDFG',
}

"""
Use classic payment, On LIVE environ, you should fix real info for BIL_GOODSNAME, URL_SUCCESS, URL_NOTIFY,CUS_EMAIL
"""
d = glocash.pay(p)
if d.get('TNS_GCID'):
    """
    Success request, you should redirect to the url value of d.get("PAYMENT_URL")
    """
    redirect_url = d.get('PAYMENT_URL')
    print(redirect_url)
    pass
else:
    """
    Request error
    """
    print(d.get('REQ_ERROR'))

"""
Use threeD safe check 
Classic threeD safe check response same as above
"""
p['BIL_CC3DS'] = 1
d = glocash.pay(p)
if d.get('TNS_GCID'):
    """
    Success request, you should redirect to the url value of d.get("URL_PAYMENT")
    """
    redirect_url = d.get('URL_PAYMENT')
    print(redirect_url)
    pass
else:
    """
    Request error
    """
    print(d.get('REQ_ERROR'))

"""
Use server to server payment(Direct payment)

"""
p["BIL_CCNUMBER"] = "4200000000000000"
p["BIL_CCHOLDER"] = "json bicker"
p["BIL_CCEXPM"] = "06"
p["BIL_CCEXPY"] = "2023"
p["BIL_CCCVV2"] = "123"
# custom user ip address
p["BIL_IPADDR"] = "56.33.69.15"
# goods detail url page
p["BIL_GOODS_URL"] = "https://goods.info.com/detail/id/1"
d = glocash.pay(p)
if d.get('URL_PAYMENT'):
    """
    You should redirect URL_PAYMENT page to complete payment 
    """
elif d.get('BIL_STATUS') != 'paid':
    """
    Transaction failed, field PGW_MESSAGE is error info
    """
    print(d.get('PGW_MESSAGE'))

"""
Query transaction
"""
d = glocash.query({'TNS_GCID': "Need TNS_GCID of glocash response"})

"""
Refund transaction
"""
d = glocash.refund({
    "TNS_GCID": "C014X13SH7B8HCMX",
    # if you want refund all,PGW_PRICE is no need
    "PGW_PRICE": "2",
})
