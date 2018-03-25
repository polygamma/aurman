# Maintainer: Jonni Westphalen <jonny.westphalen@googlemail.com>
pkgname=aurman
pkgver=2.9.16
pkgrel=1
pkgdesc="aurman AUR helper with almost pacman syntax"
arch=('any')
url="https://github.com/polygamma/aurman"
license=('MIT')
depends=('python' 'expac' 'python-requests' 'pyalpm' 'pacman' 'sudo' 'git' 'python-regex')
source=("aurman_sources::git+https://github.com/polygamma/aurman.git#tag=${pkgver}")
md5sums=('SKIP')

package() {
    cd "$srcdir/aurman_sources"
    python setup.py install --root="$pkgdir/" --optimize=1
    install -Dm644 ./bash.completion "$pkgdir/usr/share/bash-completion/completions/aurman"
}
