import csv
import json

import vkontakte


# First, authenticate with app (see readme for reference)
with open('resources/token.json') as data_file:
    data = json.load(data_file)
token = data['token']
vk = vkontakte.API(token=token)


# Some demo functions for debug
# print vk.getServerTime()
# var = vk.get('getProfiles', uids='1,2')
# var = vk.get('friends.get', fields='name')

def write_unicode(text, charset='utf-8'):
    return text.encode(charset)


def get_friends_phones():
    """
    This method gets the friends list of the user currently authenticated using API and stores it into
    friends.csv file along with the friend's phone numbers.
    :return: 
    """
    cont = vk.get('friends.get', fields='contacts')
    f = csv.writer(open("friends.csv", "wb+"))
    f.writerow(["name", "surname", "home_phone", "mobile"])
    for c in cont:
        try:
            print c["home_phone"]
        except:
            c["home_phone"] = 'missing'
        try:
            print c["mobile_phone"]
        except:
            c["mobile_phone"] = 'missing'

        for key in c:
            if type(c[key]) != int:
                if type(c[key]) != list:
                    c[key] = write_unicode(c[key])
            print key, c[key]

        f.writerow([c["first_name"],
                    c["last_name"],
                    c["mobile_phone"],
                    c["home_phone"]])


def get_groups():
    """
    This method gets the groups list of the user currently authenticated using API and stores it into
    groups.csv file along with the groups relevance and type
    :return: 
    """
    groups = vk.get('groups.get', extended=1, fields='name')
    priority = -1
    f = csv.writer(open("groups.csv", "wb+"))
    f.writerow(["name", 'screen_name', "type", "priority"])
    for g in groups:
        priority += 1
        try:
            for key in g:
                if type(g[key]) != int:
                    if type(g[key]) != list:
                        g[key] = write_unicode(g[key])
                print key, g[key]
            f.writerow([g['name'], g['screen_name'], g['type'], priority])
        except TypeError:
            pass
            # print g, priority, '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    f.close()


# get_friends_phones()
get_groups()
