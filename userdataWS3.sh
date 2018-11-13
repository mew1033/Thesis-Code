#!/bin/bash
set -x
exec > >(tee /var/log/user-data.log ) 2>&1

until $(curl --output /dev/null --silent --head --fail http://icanhazip.com); do
    sleep 5
done

echo workstation3 > /etc/hostname

sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/root:[^:]*/root:$1$XlQyAlnv$mYaJ3H7Hl5zjxV9enpX2M1/' /etc/shadow
sed -i 's/admin:[^:]*/admin:$1$6OBxHkyS$HnmKn5V0RcbqXUowFAmGt0/' /etc/shadow
service ssh restart

rm -rf /home/admin/.ssh
rm -rf /root/.ssh
rm -rf /root/.bash_history

reboot