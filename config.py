import configparser

# Создаем объект ConfigParser
config = configparser.ConfigParser()

# Добавляем секцию и параметры
config['email'] = {
    'email_host_user': '',
    'email_host_password': ''
}

# Записываем конфигурацию в файл
with open('email_config.ini', 'w') as configfile:
    config.write(configfile)


