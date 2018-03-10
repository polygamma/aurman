# arch image with base-devel
FROM base/devel

# create user and set sudo priv
RUN useradd -m aurman -s /bin/bash
RUN echo 'aurman ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# switch user and workdir
USER aurman
WORKDIR /home/aurman

# multilib
RUN sudo sh -c "sed -i '/\[multilib\]/,/Include/s/^[ ]*#//' /etc/pacman.conf"

# makepkg
RUN sudo sh -c "sed -i '/MAKEFLAGS=/s/^.*$/MAKEFLAGS=\"-j\$(nproc)\"/' /etc/makepkg.conf"
RUN sudo sh -c "sed -i '/PKGEXT=/s/^.*$/PKGEXT=\".pkg.tar\"/' /etc/makepkg.conf"

# aurman
RUN sudo pacman --needed --noconfirm -Syu python expac python-requests pyalpm pacman sudo git python-regex
ADD . /home/aurman/aurman-git

# include tests
COPY src/unit_tests/docker_tests.sh /home/aurman
RUN sudo chown aurman docker_tests.sh
RUN chmod +x docker_tests.sh
ENTRYPOINT /home/aurman/docker_tests.sh
