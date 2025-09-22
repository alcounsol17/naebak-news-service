#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import subprocess
import os
import signal

def test_news_service():
    """اختبار شامل لخدمة الشريط الإخباري"""
    
    print("🚀 بدء اختبار خدمة الشريط الإخباري...")
    
    # تشغيل الخدمة في الخلفية
    print("📡 تشغيل الخدمة...")
    process = subprocess.Popen(['python3', 'app.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    
    # انتظار تشغيل الخدمة
    time.sleep(3)
    
    base_url = "http://localhost:5000"
    
    try:
        # 1. اختبار فحص الصحة
        print("🔍 اختبار فحص صحة الخدمة...")
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("✅ فحص الصحة نجح")
        
        # 2. اختبار إضافة خبر
        print("📝 اختبار إضافة خبر جديد...")
        news_data = {'content': 'خبر تجريبي للاختبار'}
        response = requests.post(f"{base_url}/api/news", json=news_data)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] == True
        news_id = data['data']['id']
        print(f"✅ تم إضافة خبر بنجاح (ID: {news_id})")
        
        # 3. اختبار الحصول على الأخبار
        print("📋 اختبار الحصول على الأخبار...")
        response = requests.get(f"{base_url}/api/news")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert len(data['data']) >= 1
        print(f"✅ تم الحصول على {data['count']} خبر")
        
        # 4. اختبار أرشفة خبر
        print("📦 اختبار أرشفة خبر...")
        response = requests.put(f"{base_url}/api/news/{news_id}/archive")
        assert response.status_code == 200
        data = response.json()
        assert data['data']['status'] == 'archived'
        print("✅ تم أرشفة الخبر بنجاح")
        
        # 5. اختبار الأخبار المؤرشفة
        print("📚 اختبار الحصول على الأخبار المؤرشفة...")
        response = requests.get(f"{base_url}/api/news/archived")
        assert response.status_code == 200
        data = response.json()
        assert data['count'] >= 1
        print(f"✅ تم الحصول على {data['count']} خبر مؤرشف")
        
        # 6. اختبار إلغاء الأرشفة
        print("📤 اختبار إلغاء أرشفة خبر...")
        response = requests.put(f"{base_url}/api/news/{news_id}/unarchive")
        assert response.status_code == 200
        data = response.json()
        assert data['data']['status'] == 'published'
        print("✅ تم إلغاء أرشفة الخبر بنجاح")
        
        # 7. اختبار الشريط الإخباري
        print("📺 اختبار نقطة نهاية الشريط الإخباري...")
        response = requests.get(f"{base_url}/api/ticker")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        print(f"✅ الشريط الإخباري يحتوي على {data['count']} خبر")
        
        # 8. اختبار إعدادات الألوان
        print("🎨 اختبار إعدادات الألوان...")
        response = requests.get(f"{base_url}/api/settings/colors")
        assert response.status_code == 200
        data = response.json()
        assert 'orange' in data['data']
        assert 'green' in data['data']
        print("✅ تم الحصول على إعدادات الألوان")
        
        # 9. اختبار تحديث الألوان
        print("🖌️ اختبار تحديث الألوان...")
        new_colors = {'orange': '#FF6600', 'green': '#00AA00'}
        response = requests.put(f"{base_url}/api/settings/colors", json=new_colors)
        assert response.status_code == 200
        data = response.json()
        assert data['data']['orange'] == '#FF6600'
        print("✅ تم تحديث الألوان بنجاح")
        
        # 10. اختبار حذف خبر
        print("🗑️ اختبار حذف خبر...")
        response = requests.delete(f"{base_url}/api/news/{news_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        print("✅ تم حذف الخبر بنجاح")
        
        print("\n🎉 جميع الاختبارات نجحت! الخدمة تعمل بشكل صحيح.")
        
    except Exception as e:
        print(f"❌ فشل الاختبار: {e}")
        return False
    
    finally:
        # إيقاف الخدمة
        print("🛑 إيقاف الخدمة...")
        process.terminate()
        process.wait()
    
    return True

if __name__ == '__main__':
    success = test_news_service()
    exit(0 if success else 1)
