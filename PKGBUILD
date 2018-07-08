# Maintainer: Jonni Westphalen <jonny.westphalen@googlemail.com>
pkgname=aurman-git
pkgver=2.16.1
pkgrel=1
pkgdesc="AUR helper with almost pacman syntax"
arch=('any')
url="https://github.com/polygamma/aurman"
license=('MIT')
depends=('python' 'expac' 'python-requests' 'git' 'python-regex' 'python-dateutil' 'pyalpm')
source=('aurman_sources::git+https://github.com/polygamma/aurman.git?signed#branch=master')
md5sums=('SKIP')
validpgpkeys=('4C3CE98F9579981C21CA1EC3465022E743D71E39') # Jonni Westphalen
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
    /usr/bin/python3 setup.py install --root="$pkgdir/" --optimize=1
    install -Dm644 ./bash.completion "$pkgdir/usr/share/bash-completion/completions/aurman"
    install -Dm644 ./aurman.fish "$pkgdir/usr/share/fish/vendor_completions.d/aurman.fish"
}
