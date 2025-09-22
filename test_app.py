#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import json
import os
import tempfile
import shutil
from app import app

class NewsServiceTestCase(unittest.TestCase):
    """مجموعة اختبارات لخدمة الشريط الإخباري"""

    def setUp(self):
        """إعداد بيئة الاختبار"""
        self.app = app.test_client()
        self.app.testing = True
        
        # إنشاء مجلد مؤقت جديد لكل اختبار
        self.test_dir = tempfile.mkdtemp()
        
        # تحديث مسارات الملفات في التطبيق
        app.config['DATA_DIR'] = self.test_dir
        app.config['NEWS_FILE'] = os.path.join(self.test_dir, 'news.json')
        app.config['SETTINGS_FILE'] = os.path.join(self.test_dir, 'settings.json')

    def tearDown(self):
        """تنظيف بيئة الاختبار"""
        # إزالة المجلد المؤقت
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # إعادة تعيين إعدادات التطبيق
        if 'DATA_DIR' in app.config:
            del app.config['DATA_DIR']
        if 'NEWS_FILE' in app.config:
            del app.config['NEWS_FILE']
        if 'SETTINGS_FILE' in app.config:
            del app.config['SETTINGS_FILE']

    def test_01_health_check(self):
        """اختبار فحص صحة الخدمة"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_02_add_news(self):
        """اختبار إضافة خبر جديد"""
        response = self.app.post(
            '/api/news',
            data=json.dumps({'content': 'خبر تجريبي جديد'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['content'], 'خبر تجريبي جديد')

    def test_03_get_news(self):
        """اختبار الحصول على الأخبار"""
        # إضافة أخبار تجريبية
        self.app.post('/api/news', data=json.dumps({'content': 'خبر 1'}), content_type='application/json')
        self.app.post('/api/news', data=json.dumps({'content': 'خبر 2'}), content_type='application/json')
        
        response = self.app.get('/api/news')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)

    def test_04_archive_and_unarchive_news(self):
        """اختبار أرشفة وإلغاء أرشفة خبر"""
        # إضافة خبر
        post_response = self.app.post('/api/news', data=json.dumps({'content': 'خبر للأرشفة'}), content_type='application/json')
        news_id = json.loads(post_response.data)['data']['id']

        # أرشفة الخبر
        archive_response = self.app.put(f'/api/news/{news_id}/archive')
        self.assertEqual(archive_response.status_code, 200)
        archive_data = json.loads(archive_response.data)
        self.assertEqual(archive_data['data']['status'], 'archived')

        # التحقق من عدم ظهوره في الأخبار النشطة
        active_response = self.app.get('/api/news')
        active_data = json.loads(active_response.data)
        self.assertEqual(active_data['count'], 0)

        # التحقق من ظهوره في الأخبار المؤرشفة
        archived_list_response = self.app.get('/api/news/archived')
        archived_list_data = json.loads(archived_list_response.data)
        self.assertEqual(archived_list_data['count'], 1)

        # إلغاء أرشفة الخبر
        unarchive_response = self.app.put(f'/api/news/{news_id}/unarchive')
        self.assertEqual(unarchive_response.status_code, 200)
        unarchive_data = json.loads(unarchive_response.data)
        self.assertEqual(unarchive_data['data']['status'], 'published')

    def test_05_get_and_update_colors(self):
        """اختبار الحصول على وتحديث الألوان"""
        # الحصول على الألوان الافتراضية
        get_response = self.app.get('/api/settings/colors')
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.data)
        self.assertIn('orange', get_data['data'])

        # تحديث الألوان
        new_colors = {'orange': '#FF0000', 'green': '#00FF00'}
        put_response = self.app.put(
            '/api/settings/colors',
            data=json.dumps(new_colors),
            content_type='application/json'
        )
        self.assertEqual(put_response.status_code, 200)
        put_data = json.loads(put_response.data)
        self.assertEqual(put_data['data']['orange'], '#FF0000')

        # التحقق من حفظ التحديث
        get_response_after_update = self.app.get('/api/settings/colors')
        get_data_after_update = json.loads(get_response_after_update.data)
        self.assertEqual(get_data_after_update['data']['green'], '#00FF00')

    def test_06_ticker_endpoint(self):
        """اختبار نقطة نهاية الشريط الإخباري"""
        # إضافة أخبار بحالات مختلفة
        self.app.post('/api/news', data=json.dumps({'content': 'خبر منشور', 'status': 'published'}), content_type='application/json')
        self.app.post('/api/news', data=json.dumps({'content': 'خبر مسودة', 'status': 'draft'}), content_type='application/json')
        self.app.post('/api/news', data=json.dumps({'content': 'خبر مؤرشف', 'status': 'archived'}), content_type='application/json')

        response = self.app.get('/api/ticker')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['data'][0]['content'], 'خبر منشور')

    def test_07_update_news(self):
        """اختبار تحديث خبر موجود"""
        # إضافة خبر
        post_response = self.app.post('/api/news', data=json.dumps({'content': 'خبر أصلي'}), content_type='application/json')
        news_id = json.loads(post_response.data)['data']['id']

        # تحديث الخبر
        update_response = self.app.put(
            f'/api/news/{news_id}',
            data=json.dumps({'content': 'خبر محدث'}),
            content_type='application/json'
        )
        self.assertEqual(update_response.status_code, 200)
        update_data = json.loads(update_response.data)
        self.assertEqual(update_data['data']['content'], 'خبر محدث')

    def test_08_delete_news(self):
        """اختبار حذف خبر"""
        # إضافة خبر
        post_response = self.app.post('/api/news', data=json.dumps({'content': 'خبر للحذف'}), content_type='application/json')
        news_id = json.loads(post_response.data)['data']['id']

        # حذف الخبر
        delete_response = self.app.delete(f'/api/news/{news_id}')
        self.assertEqual(delete_response.status_code, 200)

        # التحقق من عدم وجود الخبر
        get_response = self.app.get('/api/news')
        get_data = json.loads(get_response.data)
        self.assertEqual(get_data['count'], 0)

if __name__ == '__main__':
    unittest.main()
