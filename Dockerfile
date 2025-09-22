FROM ubuntu:latest

# Set locale and environment
RUN apt update -y && \
    apt upgrade -y && \
    apt install locales -y && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# Install necessary packages
RUN apt install ssh wget unzip vim curl net-tools -y

# Configure SSH
RUN mkdir /run/sshd
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
RUN echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
RUN echo root:uditanshu | chpasswd

# Create startup script
RUN echo '#!/bin/bash' > /start.sh
RUN echo '/usr/sbin/sshd -D &' >> /start.sh
RUN echo 'sleep infinity' >> /start.sh
RUN chmod +x /start.sh

# Expose ports
EXPOSE 22 80 8888 8080 443 5130 5131 5132 5133 5134 5135 3306

# Start the container
CMD ["/start.sh"]
