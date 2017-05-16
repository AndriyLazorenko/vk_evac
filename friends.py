import csv

import vkontakte

# vk = vkontakte.API('6034923', 'IdQn7QURhX7UjgSibhPR')

# First, authenticate with app
vk = vkontakte.API(token='7e6abd6473edafccd2cf1600c073c785c3ac163f3bff505d50a3bb0e48a11a9a85da9f2ae10e7dcdd5517')


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
# get_groups()
