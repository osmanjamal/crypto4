// static/js/binance.js

class BinanceHandler {
    constructor() {
        this.baseUrl = 'wss://stream.binance.com:9443/ws';
        this.socket = null;
        this.subscriptions = new Set();
        this.callbacks = new Map();
        this.lastPrices = new Map();
    }

    // إعداد WebSocket
    connect() {
        this.socket = new WebSocket(this.baseUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.resubscribe();
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            setTimeout(() => this.connect(), 5000);
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
    }

    // معالجة الرسائل الواردة
    handleMessage(data) {
        if (data.e === 'trade') {
            this.handleTradeUpdate(data);
        } else if (data.e === 'ticker') {
            this.handleTickerUpdate(data);
        } else if (data.e === 'kline') {
            this.handleKlineUpdate(data);
        }
    }

    // الاشتراك في تحديثات السعر
    subscribeToPriceUpdates(symbol, callback) {
        const stream = `${symbol.toLowerCase()}@ticker`;
        this.subscriptions.add(stream);
        this.callbacks.set(stream, callback);

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                method: 'SUBSCRIBE',
                params: [stream],
                id: Date.now()
            }));
        }
    }

    // الاشتراك في تحديثات الشموع
    subscribeToKlines(symbol, interval, callback) {
        const stream = `${symbol.toLowerCase()}@kline_${interval}`;
        this.subscriptions.add(stream);
        this.callbacks.set(stream, callback);

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                method: 'SUBSCRIBE',
                params: [stream],
                id: Date.now()
            }));
        }
    }

    // إعادة الاشتراك (في حالة إعادة الاتصال)
    resubscribe() {
        if (this.subscriptions.size > 0) {
            this.socket.send(JSON.stringify({
                method: 'SUBSCRIBE',
                params: Array.from(this.subscriptions),
                id: Date.now()
            }));
        }
    }

    // معالجة تحديثات التداول
    handleTradeUpdate(data) {
        const callback = this.callbacks.get(`${data.s.toLowerCase()}@trade`);
        if (callback) {
            callback(data);
        }
    }

    // معالجة تحديثات السعر
    handleTickerUpdate(data) {
        const callback = this.callbacks.get(`${data.s.toLowerCase()}@ticker`);
        if (callback) {
            callback({
                symbol: data.s,
                price: data.c,
                priceChange: data.p,
                priceChangePercent: data.P,
                volume: data.v,
                high: data.h,
                low: data.l
            });
        }
    }

    // معالجة تحديثات الشموع
    handleKlineUpdate(data) {
        const callback = this.callbacks.get(`${data.s.toLowerCase()}@kline_${data.k.i}`);
        if (callback) {
            callback({
                time: data.k.t,
                open: parseFloat(data.k.o),
                high: parseFloat(data.k.h),
                low: parseFloat(data.k.l),
                close: parseFloat(data.k.c),
                volume: parseFloat(data.k.v),
                isClosed: data.k.x
            });
        }
    }

    // تنسيق الأرقام
    formatNumber(number, decimals = 8) {
        return parseFloat(number).toFixed(decimals);
    }

    // تنسيق العملة
    formatCurrency(number, decimals = 2) {
        return new Intl.NumberFormat('ar-SA', {
            style: 'currency',
            currency: 'USD'
        }).format(number);
    }

    // حساب التغير في النسبة المئوية
    calculatePercentageChange(oldValue, newValue) {
        return ((newValue - oldValue) / oldValue) * 100;
    }

    // إيقاف الاتصال
    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// دالة لإنشاء مثيل جديد
function createBinanceHandler() {
    const handler = new BinanceHandler();
    handler.connect();
    return handler;
}

// تصدير للاستخدام العام
window.BinanceHandler = BinanceHandler;
window.createBinanceHandler = createBinanceHandler;