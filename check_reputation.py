#!/usr/bin/env python3
"""
Скрипт для проверки репутации сайта в различных антивирусных базах
Используется для мониторинга статуса сайта после подачи заявки на удаление из черного списка
"""

import requests
import json
import time
import hashlib
import os
from datetime import datetime
from urllib.parse import urlparse

class ReputationChecker:
    def __init__(self, target_url="https://cleverdriver.ru"):
        self.target_url = target_url
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def check_virustotal(self):
        """Проверка через VirusTotal API (требует API ключ)"""
        try:
            # Для использования API нужен ключ
            # api_key = "YOUR_VIRUSTOTAL_API_KEY"
            # headers = {"x-apikey": api_key}
            # response = requests.get(f"https://www.virustotal.com/vtapi/v2/url/report", 
            #                        params={"apikey": api_key, "resource": self.target_url})
            
            # Пока используем веб-интерфейс
            print(f"🔍 Проверка VirusTotal: {self.target_url}")
            print("   Для полной проверки используйте: https://www.virustotal.com/gui/url/" + self.target_url)
            
            self.results['virustotal'] = {
                'status': 'manual_check_required',
                'url': f"https://www.virustotal.com/gui/url/{self.target_url}",
                'timestamp': self.timestamp
            }
            
        except Exception as e:
            self.results['virustotal'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.timestamp
            }
    
    def check_urlvoid(self):
        """Проверка через URLVoid"""
        try:
            print(f"🔍 Проверка URLVoid: {self.target_url}")
            
            # URLVoid не предоставляет API, но можно проверить через веб-интерфейс
            urlvoid_url = f"https://www.urlvoid.com/scan/{self.target_url.replace('https://', '').replace('http://', '')}"
            
            self.results['urlvoid'] = {
                'status': 'manual_check_required',
                'url': urlvoid_url,
                'timestamp': self.timestamp
            }
            
        except Exception as e:
            self.results['urlvoid'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.timestamp
            }
    
    def check_sucuri(self):
        """Проверка через Sucuri SiteCheck"""
        try:
            print(f"🔍 Проверка Sucuri SiteCheck: {self.target_url}")
            
            sucuri_url = f"https://sitecheck.sucuri.net/results/{self.target_url.replace('https://', '').replace('http://', '')}"
            
            self.results['sucuri'] = {
                'status': 'manual_check_required',
                'url': sucuri_url,
                'timestamp': self.timestamp
            }
            
        except Exception as e:
            self.results['sucuri'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.timestamp
            }
    
    def check_drweb(self):
        """Проверка через Dr.Web (имитация)"""
        try:
            print(f"🔍 Проверка Dr.Web: {self.target_url}")
            
            # Имитируем проверку Dr.Web
            # В реальности нужно использовать их API или веб-интерфейс
            
            self.results['drweb'] = {
                'status': 'manual_check_required',
                'url': f"https://www.drweb.com/support/",
                'timestamp': self.timestamp,
                'note': 'Используйте форму обратной связи Dr.Web для проверки статуса'
            }
            
        except Exception as e:
            self.results['drweb'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.timestamp
            }
    
    def check_ssl_certificate(self):
        """Проверка SSL сертификата"""
        try:
            print(f"🔍 Проверка SSL сертификата: {self.target_url}")
            
            response = requests.get(self.target_url, timeout=10, verify=True)
            
            if response.status_code == 200:
                self.results['ssl_certificate'] = {
                    'status': 'valid',
                    'https_enabled': True,
                    'status_code': response.status_code,
                    'timestamp': self.timestamp
                }
            else:
                self.results['ssl_certificate'] = {
                    'status': 'warning',
                    'https_enabled': True,
                    'status_code': response.status_code,
                    'timestamp': self.timestamp
                }
                
        except Exception as e:
            self.results['ssl_certificate'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.timestamp
            }
    
    def check_security_headers(self):
        """Проверка заголовков безопасности"""
        try:
            print(f"🔍 Проверка заголовков безопасности: {self.target_url}")
            
            response = requests.get(self.target_url, timeout=10)
            headers = response.headers
            
            security_headers = {
                'Content-Security-Policy': headers.get('Content-Security-Policy'),
                'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
                'X-Frame-Options': headers.get('X-Frame-Options'),
                'X-XSS-Protection': headers.get('X-XSS-Protection'),
                'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
                'Referrer-Policy': headers.get('Referrer-Policy')
            }
            
            # Подсчитываем количество установленных заголовков
            installed_headers = sum(1 for value in security_headers.values() if value is not None)
            
            self.results['security_headers'] = {
                'status': 'good' if installed_headers >= 4 else 'warning',
                'headers_found': installed_headers,
                'total_headers': len(security_headers),
                'headers': security_headers,
                'timestamp': self.timestamp
            }
            
        except Exception as e:
            self.results['security_headers'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.timestamp
            }
    
    def check_file_integrity(self):
        """Проверка целостности основных файлов"""
        try:
            print(f"🔍 Проверка целостности файлов: {self.target_url}")
            
            files_to_check = [
                '/static/theme-manager.js',
                '/'
            ]
            
            file_hashes = {}
            
            for file_path in files_to_check:
                try:
                    url = self.target_url + file_path
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        content = response.content
                        file_hash = hashlib.md5(content).hexdigest()
                        file_hashes[file_path] = {
                            'status': 'ok',
                            'md5': file_hash,
                            'size': len(content)
                        }
                    else:
                        file_hashes[file_path] = {
                            'status': 'error',
                            'error': f'HTTP {response.status_code}'
                        }
                        
                except Exception as e:
                    file_hashes[file_path] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            self.results['file_integrity'] = {
                'status': 'good' if all(f.get('status') == 'ok' for f in file_hashes.values()) else 'warning',
                'files': file_hashes,
                'timestamp': self.timestamp
            }
            
        except Exception as e:
            self.results['file_integrity'] = {
                'status': 'error',
                'error': str(e),
                'timestamp': self.timestamp
            }
    
    def run_all_checks(self):
        """Запуск всех проверок"""
        print(f"🚀 Начинаем проверку репутации сайта: {self.target_url}")
        print(f"⏰ Время проверки: {self.timestamp}")
        print("-" * 50)
        
        self.check_virustotal()
        self.check_urlvoid()
        self.check_sucuri()
        self.check_drweb()
        self.check_ssl_certificate()
        self.check_security_headers()
        self.check_file_integrity()
        
        print("-" * 50)
        print("✅ Проверка завершена")
        
        return self.results
    
    def save_results(self, filename=None):
        """Сохранение результатов в файл"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reputation_check_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Результаты сохранены в файл: {filename}")
        return filename
    
    def print_summary(self):
        """Вывод краткого отчета"""
        print("\n📊 КРАТКИЙ ОТЧЕТ:")
        print("=" * 30)
        
        for service, result in self.results.items():
            status = result.get('status', 'unknown')
            if status == 'good':
                emoji = "✅"
            elif status == 'warning':
                emoji = "⚠️"
            elif status == 'error':
                emoji = "❌"
            else:
                emoji = "🔍"
            
            print(f"{emoji} {service.upper()}: {status}")
            
            if 'url' in result:
                print(f"   🔗 {result['url']}")

def main():
    """Основная функция"""
    checker = ReputationChecker()
    results = checker.run_all_checks()
    checker.save_results()
    checker.print_summary()
    
    print(f"\n📝 Для полной проверки Dr.Web используйте:")
    print(f"   🔗 https://www.drweb.com/support/")
    print(f"   📧 virus@drweb.com")
    print(f"   📞 +7 (495) 105-94-00")

if __name__ == "__main__":
    main()
