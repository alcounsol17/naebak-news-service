#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الشريط الإخباري لمنصة نائبك
News Ticker Service for Naebak Platform

تقنية: Flask + JSON Files
Technology: Flask + JSON Files
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# مسار ملف الأخبار
NEWS_FILE = 'data/news.json'

def load_news():
    """تحميل الأخبار من ملف JSON"""
    try:
        if os.path.exists(NEWS_FILE):
            with open(NEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"خطأ في تحميل الأخبار: {e}")
        return []

def save_news(news_data):
    """حفظ الأخبار في ملف JSON"""
    try:
        os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)
        with open(NEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"خطأ في حفظ الأخبار: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة الخدمة"""
    return jsonify({
        'status': 'healthy',
        'service': 'naebak-news-service',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/news', methods=['GET'])
def get_news():
    """الحصول على جميع الأخبار"""
    try:
        news = load_news()
        # ترتيب الأخبار حسب التاريخ (الأحدث أولاً)
        news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'data': news,
            'count': len(news)
        })
    except Exception as e:
        logger.error(f"خطأ في جلب الأخبار: {e}")
        return jsonify({
            'success': False,
            'error': 'فشل في جلب الأخبار'
        }), 500

@app.route('/api/news/active', methods=['GET'])
def get_active_news():
    """الحصول على الأخبار النشطة فقط"""
    try:
        news = load_news()
        active_news = [item for item in news if item.get('is_active', True)]
        active_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'data': active_news,
            'count': len(active_news)
        })
    except Exception as e:
        logger.error(f"خطأ في جلب الأخبار النشطة: {e}")
        return jsonify({
            'success': False,
            'error': 'فشل في جلب الأخبار النشطة'
        }), 500

@app.route('/api/news', methods=['POST'])
def add_news():
    """إضافة خبر جديد"""
    try:
        data = request.get_json()
        
        if not data or not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'error': 'العنوان والمحتوى مطلوبان'
            }), 400
        
        news = load_news()
        
        # إنشاء خبر جديد
        new_item = {
            'id': len(news) + 1,
            'title': data['title'],
            'content': data['content'],
            'priority': data.get('priority', 'normal'),  # high, normal, low
            'is_active': data.get('is_active', True),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        news.append(new_item)
        
        if save_news(news):
            return jsonify({
                'success': True,
                'data': new_item,
                'message': 'تم إضافة الخبر بنجاح'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'فشل في حفظ الخبر'
            }), 500
            
    except Exception as e:
        logger.error(f"خطأ في إضافة الخبر: {e}")
        return jsonify({
            'success': False,
            'error': 'فشل في إضافة الخبر'
        }), 500

@app.route('/api/news/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    """تحديث خبر موجود"""
    try:
        data = request.get_json()
        news = load_news()
        
        # البحث عن الخبر
        news_item = None
        for item in news:
            if item['id'] == news_id:
                news_item = item
                break
        
        if not news_item:
            return jsonify({
                'success': False,
                'error': 'الخبر غير موجود'
            }), 404
        
        # تحديث البيانات
        if 'title' in data:
            news_item['title'] = data['title']
        if 'content' in data:
            news_item['content'] = data['content']
        if 'priority' in data:
            news_item['priority'] = data['priority']
        if 'is_active' in data:
            news_item['is_active'] = data['is_active']
        
        news_item['updated_at'] = datetime.now().isoformat()
        
        if save_news(news):
            return jsonify({
                'success': True,
                'data': news_item,
                'message': 'تم تحديث الخبر بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'فشل في حفظ التحديث'
            }), 500
            
    except Exception as e:
        logger.error(f"خطأ في تحديث الخبر: {e}")
        return jsonify({
            'success': False,
            'error': 'فشل في تحديث الخبر'
        }), 500

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    """حذف خبر"""
    try:
        news = load_news()
        
        # البحث عن الخبر وحذفه
        original_count = len(news)
        news = [item for item in news if item['id'] != news_id]
        
        if len(news) == original_count:
            return jsonify({
                'success': False,
                'error': 'الخبر غير موجود'
            }), 404
        
        if save_news(news):
            return jsonify({
                'success': True,
                'message': 'تم حذف الخبر بنجاح'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'فشل في حذف الخبر'
            }), 500
            
    except Exception as e:
        logger.error(f"خطأ في حذف الخبر: {e}")
        return jsonify({
            'success': False,
            'error': 'فشل في حذف الخبر'
        }), 500

@app.route('/api/news/ticker', methods=['GET'])
def get_ticker_news():
    """الحصول على أخبار الشريط المتحرك"""
    try:
        news = load_news()
        # فلترة الأخبار النشطة والمهمة للشريط
        ticker_news = [
            item for item in news 
            if item.get('is_active', True) and item.get('priority') in ['high', 'normal']
        ]
        
        # ترتيب حسب الأولوية ثم التاريخ
        priority_order = {'high': 0, 'normal': 1, 'low': 2}
        ticker_news.sort(key=lambda x: (
            priority_order.get(x.get('priority', 'normal'), 1),
            x.get('created_at', '')
        ), reverse=True)
        
        # أخذ أول 10 أخبار للشريط
        ticker_news = ticker_news[:10]
        
        return jsonify({
            'success': True,
            'data': ticker_news,
            'count': len(ticker_news)
        })
    except Exception as e:
        logger.error(f"خطأ في جلب أخبار الشريط: {e}")
        return jsonify({
            'success': False,
            'error': 'فشل في جلب أخبار الشريط'
        }), 500

if __name__ == '__main__':
    # إنشاء مجلد البيانات إذا لم يكن موجوداً
    os.makedirs('data', exist_ok=True)
    
    # إنشاء بيانات تجريبية إذا لم تكن موجودة
    if not os.path.exists(NEWS_FILE):
        sample_news = [
            {
                'id': 1,
                'title': 'مرحباً بكم في منصة نائبك',
                'content': 'منصة نائبك هي منصة شاملة لمتابعة أداء النواب والمرشحين',
                'priority': 'high',
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'title': 'تحديث جديد على المنصة',
                'content': 'تم إضافة ميزات جديدة لتحسين تجربة المستخدم',
                'priority': 'normal',
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
        save_news(sample_news)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
