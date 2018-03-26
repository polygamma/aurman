# Maintainer: Jonni Westphalen <jonny.westphalen@googlemail.com>
pkgname=aurman-git
pkgver=2.9.17
pkgrel=1
pkgdesc="aurman AUR helper with almost pacman syntax"
arch=('any')
url="https://github.com/polygamma/aurman"
license=('MIT')
depends=('python' 'expac' 'python-requests' 'pyalpm' 'pacman' 'sudo' 'git' 'python-regex')
source=('aurman_sources::git+https://github.com/polygamma/aurman.git#branch=master')
md5sums=('SKIP')
conflicts=('aurman')
provides=('aurman')

pkgver() {
    cd "$srcdir/aurman_sources"

    ( set -o pipefail
    git describe --long 2>/dev/null | sed 's/\([^-]*-g\)/r\1/;s/-/./g' ||
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
    )

}

package() {
    cd "$srcdir/aurman_sources"
    python setup.py install --root="$pkgdir/" --optimize=1
    install -Dm644 ./bash.completion "$pkgdir/usr/share/bash-completion/completions/aurman"
}
