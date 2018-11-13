#!/bin/bash
set -x
exec > >(tee /var/log/user-data.log ) 2>&1

export DEBIAN_FRONTEND="noninteractive"

until $(curl --output /dev/null --silent --head --fail http://icanhazip.com); do
    sleep 5
done

apt-get update
apt-get -yq install lamp-server^
apt-get -yq install php5-mysql php5-curl
apt-get -yq install telnetd
wget 'https://ccdc-in-the-cloud-stuffs.s3.amazonaws.com/joom.tar.gz' -O /tmp/joom.tar.gz
wget 'https://ccdc-in-the-cloud-stuffs.s3.amazonaws.com/database.dmp' -O /tmp/database.dmp
wget 'https://ccdc-in-the-cloud-stuffs.s3.amazonaws.com/configuration.php' -O /var/www/configuration.php
tar xzf /tmp/joom.tar.gz -C /var/www
sync
rm -rf /var/www/installation
sync
chown www-data:www-data -R /var/www/*
sync
mysql < /tmp/database.dmp
rm -f /var/www/index.html
rm -f /tmp/database.dmp
rm -f /tmp/joom.tar.gz

sed -E -i 's/bind-address(\s*)=(\s)127\.0\.0\.1/bind-address\1=\20\.0\.0\.0/' /etc/mysql/my.cnf
service mysql restart

apt-get -yq install vsftpd
service vsftpd stop

mkdir /var/ftp

chown -hR ftp:ftp /var/ftp
chmod 555 /var/ftp
sync

mv /etc/vsftpd.conf /etc/vsftp_conf_original
sync

cat << EOF > /etc/vsftpd.conf
# Anonymous FTP Access
listen=YES
anonymous_enable=YES
no_anon_password=YES
anon_root=/var/ftp
EOF

touch /var/ftp/SCORE.txt
service vsftpd restart

sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/root:[^:]*/root:$1$XlQyAlnv$mYaJ3H7Hl5zjxV9enpX2M1/' /etc/shadow
sed -i 's/ubuntu:[^:]*/ubuntu:$1$6OBxHkyS$HnmKn5V0RcbqXUowFAmGt0/' /etc/shadow
service ssh restart

rm -rf /home/ubuntu/.ssh
rm -rf /root/.ssh
rm -rf /root/.bash_history
