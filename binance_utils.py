# binance_utils.py

from typing import Dict, Optional, List
import hmac
import hashlib
import time
from decimal import Decimal, ROUND_DOWN

def validate_binance_keys(api_key: str, api_secret: str) -> bool:
    """التحقق من صحة مفاتيح API"""
    if not api_key or not api_secret:
        return False
    if len(api_key) < 10 or len(api_secret) < 10:
        return False
    return True

def format_decimal(value: float, decimals: int = 8) -> Decimal:
    """تنسيق الأرقام العشرية للكميات والأسعار"""
    return Decimal(str(value)).quantize(Decimal('0.'+('0'*decimals)), rounding=ROUND_DOWN)

def create_binance_signature(query_string: str, secret_key: str) -> str:
    """إنشاء التوقيع لتوثيق الطلبات"""
    return hmac.new(
        secret_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def clean_symbol(symbol: str) -> str:
    """تنظيف وتنسيق رمز العملة"""
    return symbol.upper().strip()

def calculate_order_fee(amount: float, price: float, fee_rate: float = 0.001) -> float:
    """حساب رسوم الأمر"""
    return float(format_decimal(amount * price * fee_rate))

def get_order_params(symbol: str, side: str, order_type: str, quantity: float,
                    price: Optional[float] = None) -> Dict:
    """إنشاء معلمات الأمر"""
    params = {
        'symbol': clean_symbol(symbol),
        'side': side.upper(),
        'type': order_type.upper(),
        'quantity': format_decimal(quantity),
        'timestamp': int(time.time() * 1000)
    }
    
    if price and order_type.upper() != 'MARKET':
        params['price'] = format_decimal(price)
        
    return params

def validate_order_params(params: Dict) -> bool:
    """التحقق من صحة معلمات الأمر"""
    required_fields = ['symbol', 'side', 'type', 'quantity']
    
    if not all(field in params for field in required_fields):
        return False
        
    if params['side'] not in ['BUY', 'SELL']:
        return False
        
    if params['type'] not in ['LIMIT', 'MARKET', 'STOP_LOSS', 'TAKE_PROFIT']:
        return False
        
    return True

def calculate_min_quantity(price: float, min_notional: float = 10.0) -> float:
    """حساب الحد الأدنى للكمية بناءً على السعر"""
    return float(format_decimal(min_notional / price))

def parse_binance_error(error_response: Dict) -> str:
    """تحليل رسائل الخطأ من Binance"""
    if 'msg' in error_response:
        return error_response['msg']
    elif 'message' in error_response:
        return error_response['message']
    return 'Unknown error occurred'

def is_valid_timeframe(timeframe: str) -> bool:
    """التحقق من صحة الإطار الزمني"""
    valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    return timeframe in valid_timeframes

def calculate_profit_loss(entry_price: float, current_price: float, 
                        quantity: float, side: str) -> Dict:
    """حساب الربح/الخسارة"""
    if side.upper() == 'BUY':
        pl = (current_price - entry_price) * quantity
        pl_percentage = ((current_price - entry_price) / entry_price) * 100
    else:
        pl = (entry_price - current_price) * quantity
        pl_percentage = ((entry_price - current_price) / entry_price) * 100
        
    return {
        'profit_loss': float(format_decimal(pl)),
        'profit_loss_percentage': float(format_decimal(pl_percentage, 2))
    }