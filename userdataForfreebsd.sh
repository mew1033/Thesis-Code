#!/bin/sh
pw groupadd score
echo "scoringpassword" | pw useradd -n score -s /bin/csh -m -g score -d /home/score -h 0

sed -i '' 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i '' 's/#PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config

service sshd restart

sed -i '' 's/score:[^:]*/score:$1$zcKJZ902$jBr71IdeNLw86YmTXgPkr1/' /etc/master.passwd
sed -i '' 's/root::/root:$1$XlQyAlnv$mYaJ3H7Hl5zjxV9enpX2M1/' /etc/master.passwd
sed -i '' 's/ec2-user:[^:]*:/ec2-user:$1$6OBxHkyS$HnmKn5V0RcbqXUowFAmGt0/' /etc/master.passwd
#rm -rf /home/ec2-user/.ssh