// static/js/chart.js

class TradingChart {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            theme: options.theme || 'light',
            interval: options.interval || '15m',
            candleLimit: options.candleLimit || 100,
            ...options
        };
 
        // الألوان حسب السمة
        this.colors = {
            light: {
                background: '#ffffff',
                text: '#333333',
                grid: '#f0f0f0',
                borderColor: '#dddddd',
                upColor: '#26a69a',
                downColor: '#ef5350',
                volumeUpColor: 'rgba(38, 166, 154, 0.3)',
                volumeDownColor: 'rgba(239, 83, 80, 0.3)'
            },
            dark: {
                background: '#131722',
                text: '#d1d4dc',
                grid: '#363c4e',
                borderColor: '#4c525e',
                upColor: '#26a69a',
                downColor: '#ef5350',
                volumeUpColor: 'rgba(38, 166, 154, 0.3)',
                volumeDownColor: 'rgba(239, 83, 80, 0.3)'
            }
        };
 
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.init();
    }
 
    init() {
        const colors = this.colors[this.options.theme];
 
        // إنشاء الرسم البياني
        this.chart = LightweightCharts.createChart(this.container, {
            layout: {
                background: { color: colors.background },
                textColor: colors.text,
            },
            grid: {
                vertLines: { color: colors.grid },
                horzLines: { color: colors.grid },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: colors.borderColor,
            },
            timeScale: {
                borderColor: colors.borderColor,
                timeVisible: true,
                secondsVisible: false
            },
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
            },
            handleScale: {
                axisPressedMouseMove: true,
                mouseWheel: true,
                pinch: true,
            },
        });
 
        // إضافة سلسلة الشموع
        this.candleSeries = this.chart.addCandlestickSeries({
            upColor: colors.upColor,
            downColor: colors.downColor,
            borderVisible: false,
            wickUpColor: colors.upColor,
            wickDownColor: colors.downColor,
        });
 
        // إضافة سلسلة الحجم
        this.volumeSeries = this.chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });
 
        // ضبط الحجم
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }
 
    // تحديث البيانات
    updateData(data) {
        if (Array.isArray(data)) {
            this.candleSeries.setData(data.map(candle => ({
                time: candle.time,
                open: candle.open,
                high: candle.high,
                low: candle.low,
                close: candle.close
            })));
 
            this.volumeSeries.setData(data.map(candle => ({
                time: candle.time,
                value: candle.volume,
                color: candle.close >= candle.open ? 
                    this.colors[this.options.theme].volumeUpColor : 
                    this.colors[this.options.theme].volumeDownColor
            })));
        }
    }
 
    // إضافة شمعة جديدة
    updateLastCandle(candle) {
        this.candleSeries.update({
            time: candle.time,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close
        });
 
        this.volumeSeries.update({
            time: candle.time,
            value: candle.volume,
            color: candle.close >= candle.open ? 
                this.colors[this.options.theme].volumeUpColor : 
                this.colors[this.options.theme].volumeDownColor
        });
    }
 
    // إضافة خط تحليل فني
    addLine(points, options = {}) {
        const lineSeries = this.chart.addLineSeries({
            color: options.color || '#2962FF',
            lineWidth: options.width || 1,
            lineStyle: options.style || 0,
            ...options
        });
        lineSeries.setData(points);
        return lineSeries;
    }
 
    // إضافة مؤشر فني
    addIndicator(type, data, options = {}) {
        let series;
        switch (type) {
            case 'ma':
                series = this.chart.addLineSeries({
                    color: options.color || '#2962FF',
                    lineWidth: options.width || 2,
                    ...options
                });
                break;
            case 'bb':
                // Bollinger Bands
                series = {
                    middle: this.chart.addLineSeries({
                        color: '#2962FF',
                        lineWidth: 1,
                    }),
                    upper: this.chart.addLineSeries({
                        color: '#26a69a',
                        lineWidth: 1,
                        lineStyle: 2,
                    }),
                    lower: this.chart.addLineSeries({
                        color: '#ef5350',
                        lineWidth: 1,
                        lineStyle: 2,
                    }),
                };
                break;
        }
        
        if (series && data) {
            if (type === 'bb') {
                series.middle.setData(data.middle);
                series.upper.setData(data.upper);
                series.lower.setData(data.lower);
            } else {
                series.setData(data);
            }
        }
        return series;
    }
 
    // تغيير الفاصل الزمني
    setTimeInterval(interval) {
        this.options.interval = interval;
        // يمكن إضافة منطق إضافي هنا
    }
 
    // تغيير السمة
    setTheme(theme) {
        if (theme in this.colors) {
            this.options.theme = theme;
            const colors = this.colors[theme];
            
            this.chart.applyOptions({
                layout: {
                    background: { color: colors.background },
                    textColor: colors.text,
                },
                grid: {
                    vertLines: { color: colors.grid },
                    horzLines: { color: colors.grid },
                },
            });
        }
    }
 
    // ضبط حجم الرسم البياني
    resize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight || 500;
        this.chart.resize(width, height);
    }
 
    // تنظيف
    destroy() {
        window.removeEventListener('resize', this.resize);
        if (this.chart) {
            this.chart.remove();
        }
    }
 }
 
 // تصدير للاستخدام العام
 window.TradingChart = TradingChart;