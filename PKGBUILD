# Maintainer: Jonni Westphalen <jonny.westphalen@googlemail.com>
pkgname=aurman-git
pkgver=2.9.32
pkgrel=1
pkgdesc="aurman AUR helper with almost pacman syntax"
arch=('any')
url="https://github.com/polygamma/aurman"
license=('MIT')
depends=('python' 'expac' 'python-requests' 'git' 'python-regex' 'pacman>=5.1')
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
    /usr/bin/python3 setup.py install --root="$pkgdir/" --optimize=1
    install -Dm644 ./bash.completion "$pkgdir/usr/share/bash-completion/completions/aurman"
    install -Dm644 ./aurman.fish "$pkgdir/usr/share/fish/vendor_completions.d/aurman.fish"
}
