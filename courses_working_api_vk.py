import requests
from tqdm import tqdm
from pprint import pprint
import configparser
import json
from datetime import datetime

config = configparser.ConfigParser()
config.read("setting.ini")
access_token_vk = config['Tokens']['access_token_vk']
access_token_ya = config['OAuth']['access_token_ya']

url_vk = 'https://api.vk.com/method/'

class APIVKPhotos:

    def __init__(self, access_token_vk, user_id, version=5.199):
        self.url_vk = 'https://api.vk.com/method/'
        self.params_vk = {
            'access_token' : access_token_vk,
            'v' : version
            }
        self.user_id = user_id


    def create_folder_on_ya_disk(self, folder_name):
        ya_disk_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {
            'Authorization' : f'OAuth {access_token_ya}'
        }
        params = {
            'path' : folder_name
        }

        response = requests.put(ya_disk_url, headers=headers, params=params)
        
        if response.status_code == 201:
            print("Папка создана успешно.")
        else:
            print(f"Ошибка создания папки. Статус код: {response.status_code}")
            print(response.text)


    def upload_file_to_ya_disk(self, file_path, file_name):
        ya_disk_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = {
            'Authorization' : f'OAuth {access_token_ya}'
        }
        params = {
            'path' : file_path + '/' + file_name,
            'overwrite': True
        }

        response = requests.get(ya_disk_url, headers=headers, params=params)
        
        if response.status_code == 200:
            upload_url = response.json()['href']
            return upload_url
        else:
            print(f"Ошибка получения ссылки для загрузки. Статус код: {response.status_code}")
            print(response.text)
            return None


    def get_user_photos(self, user_id, count=5):
        url = f'{self.url_vk}photos.get'
        params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'photo_sizes': 1,
            'extended': 1,
            'count': count
        }
        params.update(self.params_vk)
        response = requests.get(url=url, params=params)

        if response.status_code != 200:
            print(f"Ошибка при запросе к API VK. Статус код: {response.status_code}")
            print(response.text)
            return

        response_json = response.json()
        
        if 'error' in response_json:
            print("Ошибка в ответе API VK:")
            pprint(response_json['error'])
            return

        if 'response' not in response_json:
            print("Неожиданная структура ответа API VK:")
            pprint(response_json)
            return

        items = response_json['response'].get('items', [])
        if not items:
            print("Фотографии не найдены")
            return

        photos_info = []
        likes_count = {}

        for item in items:
            sizes = item.get('sizes', [])
            if not sizes:
                continue
            
            max_size = max(sizes, key=lambda x: x.get('width', 0) * x.get('height', 0))
            image_url = max_size.get('url')
            likes = item.get('likes', {}).get('count', 0)
            date = item.get('date', 0)
            
            if image_url:
                filename = f'{likes}.jpg'
                if likes in likes_count:
                    filename = f'{likes}_{datetime.fromtimestamp(date).strftime("%Y-%m-%d")}.jpg'
                likes_count[likes] = likes_count.get(likes, 0) + 1
                
                photos_info.append({
                    'file_name': filename,
                    'size': max_size.get('type'),
                    'url': image_url
                })

        self.create_folder_on_ya_disk('Images_VK')

        # Загружаем фото на Я.диск
        for photo in tqdm(photos_info, desc="Uploading photos"):
            self.upload_file_to_ya_disk_by_url('Images_VK', photo['file_name'], photo['url'])

        # Создаем JSON с информацией о фотографиях
        json_info = [{'file_name': photo['file_name'], 'size': photo['size']} for photo in photos_info]
        with open('photos_info.json', 'w') as f:
            json.dump(json_info, f, indent=2)

        print("Информация о фотографиях сохранена в файл photos_info.json")


    def upload_file_to_ya_disk_by_url(self, folder_path, file_name, url):
        ya_disk_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = {
            'Authorization': f'OAuth {access_token_ya}'
        }
        params = {
            'path': f'{folder_path}/{file_name}',
            'url': url
        }

        response = requests.post(ya_disk_url, headers=headers, params=params)
        
        if response.status_code == 202:
            print(f"Фотография {file_name} успешно загружена на Яндекс.Диск")
        else:
            print(f"Ошибка загрузки фотографии {file_name}. Статус код: {response.status_code}")
            print(response.text)

if __name__ == '__main__':
    user_id = 749928594
    vk_client = APIVKPhotos(access_token_vk, user_id)
    vk_client.get_user_photos(vk_client.user_id)