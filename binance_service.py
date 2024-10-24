# binance_service.py

from typing import Dict, Optional, List, Any
import requests
import time
from . import binance_utils
from .config import Config

class BinanceService:
   def __init__(self, api_key: str, api_secret: str):
       self.API_KEY = api_key
       self.API_SECRET = api_secret
       self.BASE_URL = 'https://api.binance.com'
       self.session = requests.Session()
       self.session.headers.update({
           'X-MBX-APIKEY': self.API_KEY,
           'Content-Type': 'application/json'
       })

   def _send_request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                    signed: bool = False) -> Dict:
       """إرسال الطلب إلى Binance API"""
       url = f"{self.BASE_URL}{endpoint}"
       
       if signed:
           if not params:
               params = {}
           params['timestamp'] = int(time.time() * 1000)
           query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
           params['signature'] = binance_utils.create_binance_signature(
               query_string,
               self.API_SECRET
           )

       try:
           response = self.session.request(method, url, params=params)
           response.raise_for_status()
           return response.json()
       except requests.exceptions.RequestException as e:
           error_msg = binance_utils.parse_binance_error(
               e.response.json() if hasattr(e.response, 'json') else {'msg': str(e)}
           )
           raise Exception(f"Binance API error: {error_msg}")

   def get_account_info(self) -> Dict:
       """جلب معلومات الحساب"""
       return self._send_request('GET', '/api/v3/account', signed=True)

   def get_balance(self, asset: Optional[str] = None) -> Dict:
       """جلب الرصيد"""
       account = self.get_account_info()
       balances = {
           b['asset']: {
               'free': float(b['free']),
               'locked': float(b['locked'])
           }
           for b in account['balances']
           if float(b['free']) > 0 or float(b['locked']) > 0
       }
       return balances.get(asset.upper()) if asset else balances

   def create_order(self, symbol: str, side: str, order_type: str,
                   quantity: float, price: Optional[float] = None) -> Dict:
       """إنشاء أمر جديد"""
       params = binance_utils.get_order_params(
           symbol, side, order_type, quantity, price
       )
       
       if not binance_utils.validate_order_params(params):
           raise ValueError("Invalid order parameters")
           
       return self._send_request('POST', '/api/v3/order', params=params, signed=True)

   def cancel_order(self, symbol: str, order_id: int) -> Dict:
       """إلغاء أمر"""
       params = {
           'symbol': binance_utils.clean_symbol(symbol),
           'orderId': order_id
       }
       return self._send_request('DELETE', '/api/v3/order', params=params, signed=True)

   def get_open_orders(self, symbol: Optional[str] = None) -> List:
       """جلب الأوامر المفتوحة"""
       params = {}
       if symbol:
           params['symbol'] = binance_utils.clean_symbol(symbol)
       return self._send_request('GET', '/api/v3/openOrders', params=params, signed=True)

   def get_order_status(self, symbol: str, order_id: int) -> Dict:
       """جلب حالة الأمر"""
       params = {
           'symbol': binance_utils.clean_symbol(symbol),
           'orderId': order_id
       }
       return self._send_request('GET', '/api/v3/order', params=params, signed=True)

   def get_price(self, symbol: str) -> float:
       """جلب السعر الحالي"""
       params = {'symbol': binance_utils.clean_symbol(symbol)}
       response = self._send_request('GET', '/api/v3/ticker/price', params=params)
       return float(response['price'])

   def get_trade_history(self, symbol: str, limit: int = 100) -> List:
       """جلب سجل التداولات"""
       params = {
           'symbol': binance_utils.clean_symbol(symbol),
           'limit': limit
       }
       return self._send_request('GET', '/api/v3/myTrades', params=params, signed=True)

   def get_market_data(self, symbol: str, interval: str = '1d',
                      limit: int = 100) -> List:
       """جلب بيانات السوق"""
       if not binance_utils.is_valid_timeframe(interval):
           raise ValueError("Invalid timeframe")
           
       params = {
           'symbol': binance_utils.clean_symbol(symbol),
           'interval': interval,
           'limit': limit
       }
       return self._send_request('GET', '/api/v3/klines', params=params)

   def place_market_buy(self, symbol: str, quantity: float) -> Dict:
       """تنفيذ أمر شراء فوري"""
       return self.create_order(symbol, 'BUY', 'MARKET', quantity)

   def place_market_sell(self, symbol: str, quantity: float) -> Dict:
       """تنفيذ أمر بيع فوري"""
       return self.create_order(symbol, 'SELL', 'MARKET', quantity)

   def place_limit_buy(self, symbol: str, quantity: float, price: float) -> Dict:
       """تنفيذ أمر شراء محدد"""
       return self.create_order(symbol, 'BUY', 'LIMIT', quantity, price)

   def place_limit_sell(self, symbol: str, quantity: float, price: float) -> Dict:
       """تنفيذ أمر بيع محدد"""
       return self.create_order(symbol, 'SELL', 'LIMIT', quantity, price)