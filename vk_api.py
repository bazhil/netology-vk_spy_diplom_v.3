from urllib.parse import urlencode
import  requests
import time
from pprint import pprint
import json
import math


class User:
    """
    Описание класса
    """

    def __init__(self, token=None):
        """
        Метод инициализации класса
        :param token: уникальный токен для доступа в Вконтакте
        """
        self.friends_id = []
        self.default_token = '7b23e40ad10e08d3b7a8ec0956f2c57910c455e886b480b7d9fb59859870658c4a0b8fdc4dd494db19099'
        self.token = token or self.default_token
        self.api_version ='5.73'
        self.base_url = 'https://api.vk.com/method/'
        self.banch_count = 0

    def __find_friends(self, target_uid):
        """
        Метод поиска друзей
        :param target_uid: ID целевого пользователя в Вконтакте
        """

        params = {
            'access_token': self.token,
            'target_uid': target_uid,
            'v': self.api_version
        }

        url = self.base_url + 'friends.get'
        response = requests.get(url, params)
        if response.status_code == 200:
            self.friends_id = response.json()['response']['items']
            self.banch_count = math.ceil(len(self.friends_id) / 500)


    def __find_groups(self, target_uid):
        """
        Метод поиска групп в которых состоит пользователь
        :param target_uid: ID целевого пользователя в Вконтакте
        :return: возвращает словарь групп пользователя с ключами идентификатор группы значениями имя группы
        """
        user_groups = {}
        params = {
            'access_token': self.token,
            'user_id': target_uid,
            'v': self.api_version,
            'extended': 1
        }

        url = self.base_url + 'groups.get'
        response = requests.get(url, params)

        if response.status_code == 200:
            try:
                items_from_groups = response.json()['response']['items']
                user_groups = {item['id']: item['name'] for item in items_from_groups}
                time.sleep(0.4)
                print('.')
            except KeyError:
                pass
        return user_groups

    def __get_members(self, group_id):
        """
        Метод определяющий количество участников в группах
        :param group_id: идентификатор группы
        :return: возвращает количество участников группы с ключами
        """
        users_in_group = 0
        params = {
            'access_token': self.token,
            'group_id': group_id,
            'v': self.api_version
        }

        url = self.base_url + 'groups.getMembers'
        response = requests.get(url, params)
        if response.status_code == 200:
            try:
                users_in_group = response.json()['response']['count']
                time.sleep(0.4)
                print('.')
            except:
                pass
        return users_in_group

    def __group_analyse(self, friends_id, user_groups):
        """
        Метод анализирующий группы пользователя
        :param friends_id: список друзей пользователя
        :param user_groups: список групп пользователя
        :return: возвращает список групп пользователя в которых не состоит ни один из друзей пользователя
        """
        friend_groups = []
        for friend in friends_id:
            friend_groups += list(self.__find_groups(friend).keys())
        s = set(user_groups.keys())
        s.intersection_update(set(friend_groups))
        return s
        # return set(user_groups.keys()) - set(friend_groups)

    def get_secret_group(self):
        """
        анализируем группы и сохраняем результат в файле groups.json
        """
        group_info = []
        user_id = self.__get_user_id()
        self.__find_friends(user_id)
        groups = self.__find_groups(user_id)
        unique_groups = self.__group_analyse(self.friends_id, groups)
        for group in unique_groups:
            count = self.__get_members(group)
            group_info.append(dict(name=groups[group], gid=group, members_count=count))
        with open('groups.json', 'w', encoding='utf-8') as f:
            json.dump(group_info, f, ensure_ascii=False, indent=2)

    def __friends_in_group(self, group_id):
        """
        Метод, который ищет друзей в группе
        :param group_id: ID группы
        :return: возвращает группы в которых нет друзей
        """
        params = {
            'access_token': self.token,
            'group_id': group_id,
            'v': self.api_version,
            'filter': 'friends'
        }
        url = self.base_url + 'groups.getMembers'
        response = requests.get(url, params)
        count_from_groups = 0
        if response.status_code == 200:
            try:
                count_from_groups = response.json()['response']['count']
                print(count_from_groups)
                print(response.json()['response']['items'])
                time.sleep(0.4)
                print('.')
            except KeyError:
                pass
        return count_from_groups

    def __get_user_id(self):
        """
        Метод, который получает ID пользователя
        :return: Возвращает ID пользователя
        """
        user_id = input('Введите id целевого пользователя: ')
        if not user_id:
            print('Ошибка: не введен идентификатор')
        return user_id


    def get_unique_groups(self):
        """
        Метод который получает группы в которых нет друзей
        :return: Возвращает список групп в которых нет друзей
        """
        group_info = []
        unique_groups = []
        user_id = self.__get_user_id()
        groups = self.__find_groups(user_id)
        for group_id in groups.keys():
            friends_count = self.__friends_in_group(group_id)
            print(friends_count)
            print(group_id)
            if friends_count == 0:
                unique_groups.append(group_id)
        for group in unique_groups:
            count = self.__get_members(group)
            group_info.append(dict(name=groups[group], gid=group, members_count=count))
        with open('unique_groups.json', 'w', encoding='utf-8') as f:
            json.dump(group_info, f, ensure_ascii=False, indent=2)


    def __get_member_group(self, group_id):
        """
        Метод, который определяет, является ли пользователь участником группы
        :return: Возвращает список групп, в которых не состоит ни одного друга
        """
        count = 0
        while True:
            if count >= self.banch_count:
                break
            is_member = False

            params = {
                'access_token': self.token,
                'group_id': group_id,
                'user_ids': ','.join(str(i) for i in self.friends_id[count*500:((count+1)*500)-1]),
                'v': self.api_version,
                'extended': 1
            }
            print(params['user_ids'])
            url = self.base_url + 'groups.isMember'
            response = requests.get(url, params)
            print(response.status_code)
            if response.status_code == 200:
                print(response.json())
                try:
                    members_from_groups = response.json()['response']
                    print(members_from_groups)
                    for member in members_from_groups:
                        if member['member'] == 1:
                            is_member = True
                            break
                    time.sleep(0.4)
                    print('.')
                except KeyError:
                    print('KeyError')
                    pass
            count += 1
            if is_member:
                break
        return is_member

    def third_method(self):
        """
        Метод который определяет группы, в которых не состоит ни один из друзей пользователя
        :return: Возвращает список групп в которых не состоин ни один из друзей пользователя
        """
        user_id = self.__get_user_id()
        print(1)
        groups = self.__find_groups(user_id)
        print(2)
        self.__find_friends(user_id)
        print(3)
        unique_groups = []
        print(4)
        print(groups)
        group_info = []
        print()
        for group_id in groups.keys():
            is_member = self.__get_member_group(group_id)
            print(is_member)
            print(group_id)
            if is_member:
                unique_groups.append(group_id)
        for group in unique_groups:
            count = self.__get_members(group)
            group_info.append(dict(name=groups[group], gid=group, members_count=count))
        with open('special_groups.json', 'w', encoding='utf-8') as f:
            json.dump(group_info, f, ensure_ascii=False, indent=2)

user = User()

# Вызов первого алгоритма
# user.get_secret_group()
# Вызов второго алгоритма
# user.get_unique_groups()
# Вызов третьего алгоритма
user.third_method()


