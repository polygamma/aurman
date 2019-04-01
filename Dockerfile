# arch image with base-devel
FROM archlinux/base

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

# aurman requirements and sysupgrade
RUN sudo pacman --needed --noconfirm -Syu python reflector python-requests git python-regex expac pyalpm python-dateutil python-feedparser

# new mirrors
RUN sudo reflector --save /etc/pacman.d/mirrorlist --sort rate --age 1 --latest 10 --score 10 --number 5 --protocol http
RUN sudo pacman --noconfirm -Syu

# make use of --ask=4 and disable showing of archlinux.org news
RUN mkdir -p "/home/aurman/.config/aurman/"
RUN printf "[miscellaneous]\nuse_ask\nskip_news\nskip_new_locations" > "/home/aurman/.config/aurman/aurman_config"

# add files of the current branch
ADD . /home/aurman/aurman-git

# install aurman
WORKDIR /home/aurman/aurman-git
RUN sudo python setup.py install --optimize=1

# change working dir for tests
WORKDIR /home/aurman/aurman-git/src

# chown, chmod and set entrypoint
RUN sudo chown -R aurman:aurman /home/aurman/aurman-git/src
RUN chmod +x -R /home/aurman/aurman-git/src
ENTRYPOINT ["/home/aurman/aurman-git/src/docker_tests/execute_test.sh"]
