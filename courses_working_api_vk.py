
import requests
from tqdm import tqdm
from pprint import pprint
import configparser

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
            'owner_id' : user_id,
            'album_id' : 'profile',
            'photo_sizes' : 1,
            'extended' : 1,
            'count' : count
            }
        params.update(self.params_vk)
        response = requests.get(url=url, params=params)

        dict_name_url = {}
   
        #pprint(response.json())
        #print('*************')
        #print('*************')

        pprint(response.json()['response']['items'])

        for a in response.json()['response']['items']:
            image_url = a.get('orig_photo').get('url')
            likes = a.get('likes', {}).get('count', 0)
            if image_url:
                filename = f'{likes}.jpg'
                dict_name_url[filename] = image_url

        self.create_folder_on_ya_disk('Images_VK')

        # создаем прогресс - бар и загружаем фото на Я.диск
        for filename, image_url in tqdm(dict_name_url.items(), desc="Uploading photos"):
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                upload_url = self.upload_file_to_ya_disk('Images_VK', filename)
                if upload_url:
                    with open(filename, 'rb') as f:
                        requests.put(upload_url, files={'file':f})
                    print(f"Фотография {filename} загружена успешно.")
                else:
                    print(f"Ошибка загрузки фотографии {filename}.")
            else:
                print(f"Ошибка скачивания фотографии {filename}. Статус код: {response.status_code}")
                print(response.text)

if __name__ == '__main__':
    vk_client = APIVKPhotos(access_token_vk, 749928594)
    vk_client.get_user_photos(749928594)






        

   

    

