# Maintainer: Jonni Westphalen <jonny.westphalen@googlemail.com>
pkgname=aurman
pkgver=2.21
pkgrel=1
pkgdesc="AUR helper with almost pacman syntax"
arch=('any')
url="https://github.com/polygamma/aurman"
license=('MIT')
depends=('python' 'expac' 'python-requests' 'git' 'python-regex' 'python-dateutil' 'pyalpm' 'python-feedparser' 'python-setuptools')
source=('aurman_sources::git+https://github.com/polygamma/aurman.git?signed#tag=${pkgver}')
md5sums=('SKIP')
validpgpkeys=('F3FAE51DB14A292C5C0A5535910B8C499BED531B') # Jonni Westphalen

package() {
    cd "$srcdir/aurman_sources"
    /usr/bin/python3 setup.py install --root="$pkgdir/" --optimize=1
    install -Dm644 ./bash.completion "$pkgdir/usr/share/bash-completion/completions/aurman"
    install -Dm644 ./aurman.fish "$pkgdir/usr/share/fish/vendor_completions.d/aurman.fish"
}
