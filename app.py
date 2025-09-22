#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الشريط الإخباري لمنصة نائبك (نسخة مطورة)
News Ticker Service for Naebak Platform (Upgraded Version)

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

# مسارات الملفات (قابلة للتخصيص للاختبارات)
def get_data_dir():
    return app.config.get('DATA_DIR', 'data')

def get_news_file():
    return app.config.get('NEWS_FILE', os.path.join(get_data_dir(), 'news.json'))

def get_settings_file():
    return app.config.get('SETTINGS_FILE', os.path.join(get_data_dir(), 'settings.json'))

# --- دوال مساعدة --- #

def load_data(file_path, default_data=[]):
    """تحميل البيانات من ملف JSON"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default_data
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"خطأ في تحميل الملف {file_path}: {e}")
        return default_data

def save_data(file_path, data):
    """حفظ البيانات في ملف JSON"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        logger.error(f"خطأ في حفظ الملف {file_path}: {e}")
        return False

# --- نقاط النهاية (Endpoints) --- #

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة الخدمة"""
    return jsonify({
        'status': 'healthy',
        'service': 'naebak-news-service',
        'timestamp': datetime.now().isoformat()
    })

# --- إدارة الأخبار --- #

@app.route('/api/news', methods=['GET'])
def get_news():
    """الحصول على جميع الأخبار (غير المؤرشفة)"""
    status_filter = request.args.get('status')
    news = load_data(get_news_file())
    
    if status_filter:
        news = [item for item in news if item.get('status') == status_filter]
    else:
        news = [item for item in news if item.get('status') != 'archived']

    news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({'success': True, 'data': news, 'count': len(news)})

@app.route('/api/news/archived', methods=['GET'])
def get_archived_news():
    """الحصول على الأخبار المؤرشفة"""
    news = load_data(get_news_file())
    archived_news = [item for item in news if item.get('status') == 'archived']
    archived_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({'success': True, 'data': archived_news, 'count': len(archived_news)})

@app.route('/api/news', methods=['POST'])
def add_news():
    """إضافة خبر جديد"""
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'success': False, 'error': 'المحتوى مطلوب'}), 400

    news = load_data(get_news_file())
    new_item = {
        'id': len(news) + 1,
        'content': data['content'],
        'status': data.get('status', 'published'),  # published, draft, archived
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    news.append(new_item)

    if save_data(get_news_file(), news):
        return jsonify({'success': True, 'data': new_item, 'message': 'تم إضافة الخبر بنجاح'}), 201
    return jsonify({'success': False, 'error': 'فشل في حفظ الخبر'}), 500

@app.route('/api/news/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    """تحديث خبر موجود"""
    data = request.get_json()
    news = load_data(get_news_file())
    news_item = next((item for item in news if item['id'] == news_id), None)

    if not news_item:
        return jsonify({'success': False, 'error': 'الخبر غير موجود'}), 404

    if 'content' in data:
        news_item['content'] = data['content']
    if 'status' in data:
        news_item['status'] = data['status']
    
    news_item['updated_at'] = datetime.now().isoformat()

    if save_data(get_news_file(), news):
        return jsonify({'success': True, 'data': news_item, 'message': 'تم تحديث الخبر بنجاح'})
    return jsonify({'success': False, 'error': 'فشل في حفظ التحديث'}), 500

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    """حذف خبر"""
    news = load_data(get_news_file())
    original_count = len(news)
    news = [item for item in news if item['id'] != news_id]

    if len(news) == original_count:
        return jsonify({'success': False, 'error': 'الخبر غير موجود'}), 404

    if save_data(get_news_file(), news):
        return jsonify({'success': True, 'message': 'تم حذف الخبر بنجاح'})
    return jsonify({'success': False, 'error': 'فشل في حذف الخبر'}), 500

@app.route('/api/news/<int:news_id>/archive', methods=['PUT'])
def archive_news(news_id):
    """أرشفة خبر"""
    return update_news_status(news_id, 'archived')

@app.route('/api/news/<int:news_id>/unarchive', methods=['PUT'])
def unarchive_news(news_id):
    """إلغاء أرشفة خبر (إعادة نشره)"""
    return update_news_status(news_id, 'published')

def update_news_status(news_id, status):
    news = load_data(get_news_file())
    news_item = next((item for item in news if item['id'] == news_id), None)

    if not news_item:
        return jsonify({'success': False, 'error': 'الخبر غير موجود'}), 404

    news_item['status'] = status
    news_item['updated_at'] = datetime.now().isoformat()

    if save_data(get_news_file(), news):
        return jsonify({'success': True, 'data': news_item, 'message': f'تم تحديث حالة الخبر إلى {status}'})
    return jsonify({'success': False, 'error': 'فشل في تحديث حالة الخبر'}), 500

# --- إدارة الإعدادات (الألوان) --- #

@app.route('/api/settings/colors', methods=['GET'])
def get_colors():
    """الحصول على إعدادات الألوان"""
    default_colors = {
        'orange': '#FFA500',
        'green': '#008000'
    }
    settings = load_data(get_settings_file(), default_data={'colors': default_colors})
    return jsonify({'success': True, 'data': settings.get('colors', default_colors)})

@app.route('/api/settings/colors', methods=['PUT'])
def update_colors():
    """تحديث إعدادات الألوان"""
    data = request.get_json()
    if not data or ('orange' not in data and 'green' not in data):
        return jsonify({'success': False, 'error': 'يجب توفير قيم للألوان'}), 400

    settings = load_data(get_settings_file(), default_data={'colors': {}})
    if 'colors' not in settings:
        settings['colors'] = {}
        
    if 'orange' in data:
        settings['colors']['orange'] = data['orange']
    if 'green' in data:
        settings['colors']['green'] = data['green']

    if save_data(get_settings_file(), settings):
        return jsonify({'success': True, 'data': settings['colors'], 'message': 'تم تحديث الألوان بنجاح'})
    return jsonify({'success': False, 'error': 'فشل في حفظ إعدادات الألوان'}), 500

# --- نقطة نهاية للشريط الإخباري --- #

@app.route('/api/ticker', methods=['GET'])
def get_ticker_news():
    """الحصول على أخبار الشريط المتحرك (المنشورة فقط)"""
    news = load_data(get_news_file())
    ticker_news = [item for item in news if item.get('status') == 'published']
    ticker_news.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # أخذ أحدث 10 أخبار منشورة
    ticker_news = ticker_news[:10]
    
    return jsonify({'success': True, 'data': ticker_news, 'count': len(ticker_news)})


if __name__ == '__main__':
    # إنشاء مجلد البيانات إذا لم يكن موجوداً
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    
    # إنشاء بيانات تجريبية إذا لم تكن موجودة
    news_file = get_news_file()
    if not os.path.exists(news_file):
        sample_news = [
            {
                'id': 1,
                'content': 'مرحباً بكم في منصة نائبك، المنصة الشاملة للتواصل مع النواب والمرشحين.',
                'status': 'published',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'content': 'تم إطلاق ميزات جديدة في المنصة لتحسين تجربة المستخدم.',
                'status': 'published',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'id': 3,
                'content': 'خبر مؤرشف: سيتم عقد جلسة نقاشية قريباً.',
                'status': 'archived',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
        save_data(news_file, sample_news)

    settings_file = get_settings_file()
    if not os.path.exists(settings_file):
        default_settings = {
            'colors': {
                'orange': '#FF8C00', # برتقالي غامق
                'green': '#228B22'   # أخضر غابي
            }
        }
        save_data(settings_file, default_settings)

    app.run(host='0.0.0.0', port=5000, debug=True)
