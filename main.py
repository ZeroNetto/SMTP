import socket
import ssl
import base64
import os
import sys
import re

# Keys - smtp server, values = port
smtps = {'smtp.yandex.ru': 465, 'smtp.mail.ru': 465, 'smtp.rambler.ru': 465}
# Keys - smtp server, values - mail on this server.
mails = {'smtp.mail.ru': 'smtptest2018@mail.ru',
         'smtp.yandex.ru': 's5mtptest2018@yandex.ru',
         'smtp.rambler.ru': 'smtptest2018@rambler.ru'}
# Please, don't try to login with this password)
password = '1937456zdfyzp'


def send_command(sock, command):
    print(command)
    print('sended: {0} bytes'.format(sock.send(command)))
    print('received: {0}'.format(sock.recv(1024).decode()))


def get_message(file_name):
    readed = ''
    try:
        with open(os.path.join('configs\\{0}'.format(file_name))) as data:
            readed = re.sub(r'(?<=\n)(\.+)(?=\n)', r'\1.', data.read())
            readed += '\n.'
    except OSError as e:
        print('Something went wrong: {0}'.format(e))
        sys.exit()
    return readed


def get_config_info(config_file_name):
    receivers = []
    theme = ''
    attachment_names = []
    attachments = {}
    counter = 0
    try:
        with open(os.path.join('configs\\{0}'.format(config_file_name))) as data:
            for line in data.readlines():
                if line == '\n':
                    counter += 1
                    continue
                if counter == 0:
                    receivers.append(line[0:len(line)-1])
                if counter == 1:
                    theme = line[0:len(line)-1]
                if counter == 2:
                    attachment_names.append(line[0:len(line)-1])
        for name in attachment_names:
            with open(os.path.join('configs\\{0}'.format(name)), 'rb') as file:
                attachments[name] = base64.b64encode(file.read())
    except OSError as e:
        print('Something went wrong: {0}'.format(e))
    return receivers, theme, attachments


def autorize(sock, server):
    login = mails[server]
    send_command(sock, bytes('EHLO {0}\n'.format(login), 'utf-8'))
    print('received: {0}'.format(sock.recv(1024).decode()))
    send_command(sock, b'AUTH LOGIN\n')
    en_login = base64.b64encode(bytes(login, 'utf-8'))
    send_command(sock, en_login+b'\n')
    en_password = base64.b64encode(bytes(password, 'utf-8'))
    send_command(sock, en_password+b'\n')


def send_message(sock, sender, message, receivers, theme, attachments):
    send_command(sock, bytes('MAIL FROM: {0}\n'.format(sender), 'utf-8'))
    for receiver in receivers:
        send_command(sock, bytes('RCPT TO: {0}\n'.format(receiver), 'utf-8'))
    send_command(sock, b'DATA\n')
    send_command(sock, get_formated_message(
            message, receiver, sender, attachments, theme))


def get_formated_message(message, receiver, sender, attachments, theme):
    attachments_info = b''
    for name in attachments.keys():
        temp = bytes('''--A4D921C2D10D7DB
Content-Type: application/octet-stream; name="{0}"
Content-transfer-encoding: base64
Content-Disposition: attachment; filename="{0}"

'''.format(name), 'utf-8')
        attachments_info += temp
        attachments_info += attachments[name] + b'\n'
    formated_message = bytes('''From: {0}
To: {1}
Subject: {2}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="A4D921C2D10D7DB"

'''.format(sender, receiver, theme), 'utf-8')
    formated_message += attachments_info + b'\n'
    formated_message += b'--A4D921C2D10D7DB\n'
    formated_message += b'Content-Type: text/plain; charset=utf-8\n'
    formated_message += b'Content-Transfer-Encoding: 8bit\n\n'
    formated_message += bytes(message, 'utf-8') + b'\n'
    formated_message += b'--A4D921C2D10D7DB--'
    return formated_message


def main():
    server = 'smtp.yandex.ru'
    message = get_message('text.txt')
    receivers, theme, attachments = get_config_info('config.txt')
    port = 465
    with socket.socket() as sock:
        try:
            sock.connect((server, port))
            sock.settimeout(3)
            sock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_SSLv23)
            autorize(sock, server)
            send_message(sock, mails[server],
                         message, receivers, theme, attachments)
            send_command(sock, b'QUIT\n')
        except OSError as e:
            print('Something went wrong: {0}'.format(e))
    print('---------------------------------------------------------')


if __name__ == "__main__":
    main()
