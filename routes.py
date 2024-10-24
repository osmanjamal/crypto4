# routes.py - المرحلة الأولى

from flask import (
    render_template, request, redirect, 
    url_for, flash, session, jsonify
)
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from binance_service import BinanceService
from binance_utils import validate_binance_keys
from functools import wraps
import config
import json
import pandas as pd
from datetime import datetime
import importlib

mysql = MySQL()

# وظيفة للتحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('يرجى تسجيل الدخول أولاً')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# وظائف مساعدة
def write_log(user_id, action, details):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO activity_logs (user_id, action, details, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (user_id, action, details))
    mysql.connection.commit()
    cursor.close()

def get_user_api_keys(user_id):
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT binance_key, binance_secret 
        FROM users 
        WHERE id = %s
    """, [user_id])
    user = cursor.fetchone()
    cursor.close()
    return user

def get_user_settings(user_id):
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM user_settings 
        WHERE user_id = %s
    """, [user_id])
    settings = cursor.fetchone()
    cursor.close()
    return settings

def format_number(number, decimals=8):
    try:
        return f"{float(number):.{decimals}f}"
    except:
        return "0.00"

def get_ip_address():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_address
  # routes.py - المرحلة الثانية

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM users 
            WHERE username = %s
        """, [username])
        user = cursor.fetchone()
        cursor.close()
        
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['ip_address'] = get_ip_address()
            
            # تحديث آخر تسجيل دخول
            cursor = mysql.connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET last_login = NOW() 
                WHERE id = %s
            """, [user['id']])
            mysql.connection.commit()
            cursor.close()
            
            write_log(user['id'], 'login', 'تسجيل دخول ناجح')
            return redirect(url_for('index'))
            
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    if 'user_id' in session:
        write_log(session['user_id'], 'logout', 'تسجيل خروج')
    session.clear()
    flash('تم تسجيل الخروج بنجاح')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # التحقق من IP
    if session.get('ip_address') != get_ip_address():
        session.clear()
        flash('تم اكتشاف تغيير في عنوان IP')
        return redirect(url_for('login'))
        
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            users.*, 
            user_settings.theme,
            user_settings.notifications_enabled
        FROM users 
        LEFT JOIN user_settings ON users.id = user_settings.user_id
        WHERE users.id = %s
    """, [session['user_id']])
    user_data = cursor.fetchone()
    cursor.close()
    
    return render_template('dashboard.html', user=user_data)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # تحديث الإعدادات العامة
        theme = request.form.get('theme', 'light')
        notifications = request.form.get('notifications', '0')
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO user_settings 
                (user_id, theme, notifications_enabled, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                theme = VALUES(theme),
                notifications_enabled = VALUES(notifications_enabled),
                updated_at = NOW()
        """, (session['user_id'], theme, notifications))
        mysql.connection.commit()
        cursor.close()
        
        flash('تم تحديث الإعدادات بنجاح')
        write_log(session['user_id'], 'update_settings', 'تحديث إعدادات المستخدم')
        
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM user_settings WHERE user_id = %s', [session['user_id']])
    settings = cursor.fetchone()
    cursor.close()
    
    return render_template('settings.html', settings=settings)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute('SELECT password FROM users WHERE id = %s', [session['user_id']])
        user = cursor.fetchone()
        
        if not check_password_hash(user['password'], current_password):
            flash('كلمة المرور الحالية غير صحيحة')
        elif new_password != confirm_password:
            flash('كلمتا المرور الجديدتان غير متطابقتين')
        elif len(new_password) < 8:
            flash('كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل')
        else:
            hashed_password = generate_password_hash(new_password)
            cursor.execute("""
                UPDATE users 
                SET password = %s 
                WHERE id = %s
            """, (hashed_password, session['user_id']))
            mysql.connection.commit()
            flash('تم تغيير كلمة المرور بنجاح')
            write_log(session['user_id'], 'change_password', 'تغيير كلمة المرور')
            
        cursor.close()
        
    return render_template('change_password.html')

@app.route('/activity_log')
@login_required
def activity_log():
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM activity_logs 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 100
    """, [session['user_id']])
    logs = cursor.fetchall()
    cursor.close()
    
    return render_template('activity_log.html', logs=logs)
  
  # routes.py - المرحلة الثالثة

@app.route('/binance/settings', methods=['GET', 'POST'])
@login_required
def binance_settings():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        
        if validate_binance_keys(api_key, api_secret):
            try:
                # اختبار الاتصال مع API
                test_service = BinanceService(api_key, api_secret)
                test_service.get_account_info()
                
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET binance_key = %s, 
                        binance_secret = %s,
                        binance_connected = 1,
                        binance_connected_at = NOW()
                    WHERE id = %s
                """, (api_key, api_secret, session['user_id']))
                mysql.connection.commit()
                cursor.close()
                
                write_log(session['user_id'], 'binance_connect', 'تم ربط حساب Binance بنجاح')
                flash('تم ربط حساب Binance بنجاح', 'success')
            except Exception as e:
                flash(f'خطأ في الاتصال: {str(e)}', 'error')
        else:
            flash('مفاتيح API غير صالحة', 'error')
            
    # جلب معلومات API الحالية
    cursor = mysql.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT binance_key, binance_secret, binance_connected, binance_connected_at
        FROM users WHERE id = %s
    """, [session['user_id']])
    api_data = cursor.fetchone()
    cursor.close()
    
    return render_template('binance/settings.html', api_data=api_data)

@app.route('/binance/dashboard')
@login_required
def binance_dashboard():
    user = get_user_api_keys(session['user_id'])
    
    if not user['binance_key'] or not user['binance_secret']:
        flash('يرجى إعداد مفاتيح API أولاً', 'warning')
        return redirect(url_for('binance_settings'))
        
    try:
        binance = BinanceService(user['binance_key'], user['binance_secret'])
        account_info = binance.get_account_info()
        balances = binance.get_balance()
        
        # حساب إجمالي القيمة بالدولار
        total_value = 0
        for asset, balance in balances.items():
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                if asset == 'USDT':
                    price = 1
                else:
                    try:
                        price = binance.get_price(f"{asset}USDT")
                    except:
                        price = 0
                total_value += (float(balance['free']) + float(balance['locked'])) * price
        
        # جلب آخر التداولات
        recent_trades = binance.get_trade_history('BTCUSDT', limit=5)
        
        return render_template('binance/dashboard.html',
                             account_info=account_info,
                             balances=balances,
                             total_value=total_value,
                             recent_trades=recent_trades)
                             
    except Exception as e:
        flash(f'خطأ في جلب البيانات: {str(e)}', 'error')
        return redirect(url_for('binance_settings'))

@app.route('/binance/trade', methods=['GET', 'POST'])
@login_required
def binance_trade():
    user = get_user_api_keys(session['user_id'])
    
    if not user['binance_key'] or not user['binance_secret']:
        flash('يرجى إعداد مفاتيح API أولاً', 'warning')
        return redirect(url_for('binance_settings'))
        
    try:
        binance = BinanceService(user['binance_key'], user['binance_secret'])
        
        if request.method == 'POST':
            symbol = request.form.get('symbol')
            side = request.form.get('side')
            order_type = request.form.get('type')
            quantity = float(request.form.get('quantity'))
            price = request.form.get('price')
            
            # التحقق من الرصيد قبل التنفيذ
            if side == 'buy':
                quote_asset = symbol[3:] if len(symbol) > 3 else 'USDT'
                balance = binance.get_balance(quote_asset)
                required_amount = quantity * (float(price) if price else binance.get_price(symbol))
                if required_amount > float(balance['free']):
                    flash('رصيد غير كافٍ', 'error')
                    return redirect(url_for('binance_trade'))
            else:
                base_asset = symbol[:3]
                balance = binance.get_balance(base_asset)
                if quantity > float(balance['free']):
                    flash('رصيد غير كافٍ', 'error')
                    return redirect(url_for('binance_trade'))
            
            # تنفيذ الأمر
            if order_type == 'market':
                result = binance.place_market_buy(symbol, quantity) if side == 'buy' \
                    else binance.place_market_sell(symbol, quantity)
            else:
                result = binance.place_limit_buy(symbol, quantity, float(price)) if side == 'buy' \
                    else binance.place_limit_sell(symbol, quantity, float(price))
            
            write_log(session['user_id'], 'binance_trade', 
                     f"{side} {quantity} {symbol} at {price if price else 'market price'}")
            flash('تم تنفيذ الأمر بنجاح', 'success')
            return redirect(url_for('binance_orders'))
            
        # جلب معلومات السوق للعرض
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  # يمكن تخصيصها حسب الحاجة
        market_data = {}
        for symbol in symbols:
            price = binance.get_price(symbol)
            market_data[symbol] = {
                'price': price,
                'min_qty': binance.calculate_min_quantity(price)
            }
            
        return render_template('binance/trade.html', market_data=market_data)
        
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'error')
        return redirect(url_for('binance_dashboard'))

@app.route('/binance/orders')
@login_required
def binance_orders():
    user = get_user_api_keys(session['user_id'])
    
    if not user['binance_key'] or not user['binance_secret']:
        flash('يرجى إعداد مفاتيح API أولاً', 'warning')
        return redirect(url_for('binance_settings'))
        
    try:
        binance = BinanceService(user['binance_key'], user['binance_secret'])
        open_orders = binance.get_open_orders()
        
        return render_template('binance/orders.html', orders=open_orders)
    except Exception as e:
        flash(f'خطأ في جلب الأوامر: {str(e)}', 'error')
        return redirect(url_for('binance_dashboard'))

@app.route('/binance/cancel_order', methods=['POST'])
@login_required
def cancel_binance_order():
    user = get_user_api_keys(session['user_id'])
    
    try:
        binance = BinanceService(user['binance_key'], user['binance_secret'])
        symbol = request.form.get('symbol')
        order_id = int(request.form.get('order_id'))
        
        result = binance.cancel_order(symbol, order_id)
        write_log(session['user_id'], 'cancel_order', f"Cancel order {order_id} for {symbol}")
        
        return jsonify({'status': 'success', 'message': 'تم إلغاء الأمر بنجاح'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/binance/history')
@login_required
def binance_history():
    user = get_user_api_keys(session['user_id'])
    symbol = request.args.get('symbol', 'BTCUSDT')
    
    try:
        binance = BinanceService(user['binance_key'], user['binance_secret'])
        trades = binance.get_trade_history(symbol)
        
        # حساب إحصائيات التداول
        stats = {
            'total_trades': len(trades),
            'total_volume': sum(float(trade['qty']) for trade in trades),
            'profitable_trades': len([t for t in trades if float(t['realizedPnl']) > 0]),
            'total_pnl': sum(float(trade['realizedPnl']) for trade in trades)
        }
        
        return render_template('binance/history.html', 
                             trades=trades, 
                             stats=stats,
                             symbol=symbol)
    except Exception as e:
        flash(f'خطأ في جلب السجل: {str(e)}', 'error')
        return redirect(url_for('binance_dashboard'))
      
      # routes.py - المرحلة الرابعة

@app.route('/signals', methods=['GET', 'POST'])
@login_required
def signals():
    try:
        with open('signals.json', 'r', encoding='utf-8') as f:
            trade_data = json.load(f)
        
        df = pd.DataFrame(
            trade_data,
            columns=['order_time', 'symbol', 'action', 'entry', 'qty', 'qty_type']
        )
        
        df.rename(columns={
            'order_time': 'TIME',
            'symbol': 'SYMBOL',
            'action': 'SIDE',
            'qty': 'QTY',
            'entry': 'ENTRY',
            'qty_type': 'ACCOUNT'
        }, inplace=True)
        
        df = df.sort_values(by="TIME", ascending=False)
        
        # إضافة إمكانية تنفيذ الإشارات على بايننس
        can_execute = False
        user = get_user_api_keys(session['user_id'])
        if user and user['binance_key'] and user['binance_secret']:
            can_execute = True
            
        return render_template('signals.html',
                             tables=[df.to_html(classes='data')],
                             titles=df.columns.values,
                             can_execute=can_execute)
                             
    except Exception as e:
        flash(f'خطأ في جلب الإشارات: {str(e)}', 'error')
        return render_template('signals.html', tables=[], titles=[])

@app.route('/execute_signal', methods=['POST'])
@login_required
def execute_signal():
    user = get_user_api_keys(session['user_id'])
    if not user['binance_key'] or not user['binance_secret']:
        return jsonify({'status': 'error', 'message': 'يرجى إعداد API بايننس أولاً'})
        
    try:
        data = request.json
        binance = BinanceService(user['binance_key'], user['binance_secret'])
        
        if data['side'].lower() == 'buy':
            result = binance.place_market_buy(data['symbol'], float(data['quantity']))
        else:
            result = binance.place_market_sell(data['symbol'], float(data['quantity']))
            
        write_log(session['user_id'], 'execute_signal', 
                 f"Executed signal: {data['side']} {data['quantity']} {data['symbol']}")
                 
        return jsonify({'status': 'success', 'message': 'تم تنفيذ الإشارة بنجاح'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/trades', methods=['GET'])
@login_required
def trades():
    try:
        with open('trades.json', 'r', encoding='utf-8') as f:
            trade_data = json.load(f)
            
        df = pd.DataFrame(
            trade_data,
            columns=['order_time', 'order_id', 'symbol', 'action', 'price', 'qty']
        )
        
        df.rename(columns={
            'order_time': 'TIME',
            'order_id': 'ORDER ID',
            'symbol': 'SYMBOL',
            'action': 'SIDE',
            'qty': 'QTY',
            'price': 'PRICE'
        }, inplace=True)
        
        df = df.sort_values(by="TIME", ascending=False)
        
        # إضافة معلومات بايننس إذا كانت متوفرة
        binance_trades = []
        user = get_user_api_keys(session['user_id'])
        if user['binance_key'] and user['binance_secret']:
            try:
                binance = BinanceService(user['binance_key'], user['binance_secret'])
                binance_trades = binance.get_trade_history('BTCUSDT', limit=10)
            except:
                pass
                
        return render_template('trades.html',
                             tables=[df.to_html(classes='data')],
                             titles=df.columns.values,
                             binance_trades=binance_trades)
                             
    except Exception as e:
        flash(f'خطأ في جلب التداولات: {str(e)}', 'error')
        return render_template('trades.html', tables=[], titles=[])

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def max_loss_settings():
    max_loss_value = ''
    try:
        with open('max_loss_value.txt', 'r') as f:
            max_loss_value = f.read().strip()
    except:
        pass
        
    if request.method == 'POST':
        max_loss_value = request.form.get('max_loss', '')
        try:
            with open('max_loss_value.txt', 'w') as f:
                f.write(max_loss_value)
            flash('تم تحديث قيمة الحد الأقصى للخسارة', 'success')
        except Exception as e:
            flash(f'خطأ في حفظ الإعدادات: {str(e)}', 'error')
            
    # جلب إعدادات بايننس
    user = get_user_api_keys(session['user_id'])
    binance_connected = bool(user and user['binance_key'] and user['binance_secret'])
    
    return render_template('settings.html',
                         max_loss_value=max_loss_value,
                         binance_connected=binance_connected)

@app.route('/reset_max_loss', methods=['POST'])
@login_required
def reset_max_loss():
    try:
        with open('max_loss_value.txt', 'w') as f:
            f.write('')
        flash('تم إعادة تعيين قيمة الحد الأقصى للخسارة', 'success')
    except Exception as e:
        flash(f'خطأ في إعادة التعيين: {str(e)}', 'error')
        
    return redirect(url_for('max_loss_settings'))

# Webhook للتداول التلقائي
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        # التحقق من صحة البيانات
        required_fields = ['symbol', 'side', 'quantity', 'key']
        if not all(field in data for field in required_fields):
            return jsonify({'status': 'error', 'message': 'بيانات غير مكتملة'})
            
        # التحقق من المفتاح
        if data['key'] != config.webhook_key:
            return jsonify({'status': 'error', 'message': 'مفتاح غير صالح'})
            
        # حفظ الإشارة
        signal_data = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': data['symbol'],
            'side': data['side'],
            'quantity': data['quantity']
        }
        
        try:
            with open('signals.json', 'r+') as f:
                signals = json.load(f)
                signals.append(signal_data)
                f.seek(0)
                json.dump(signals, f, indent=4)
        except:
            with open('signals.json', 'w') as f:
                json.dump([signal_data], f, indent=4)
        
        # تنفيذ على بايننس إذا كان مفعلاً
        if data.get('execute_binance'):
            # يمكن إضافة منطق لتنفيذ الأمر على حسابات بايننس المحددة
            pass
            
        return jsonify({'status': 'success', 'message': 'تم استلام الإشارة بنجاح'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# معالجة الأخطاء
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500