# Maintainer: Jonni Westphalen <jonny.westphalen@googlemail.com>
pkgname=aurman-git
pkgver=1.5
pkgrel=1
pkgdesc="aurman AUR helper"
arch=('x86_64')
url="https://github.com/polygamma/aurman"
license=('MIT')
depends=('python' 'expac' 'python-requests' 'pyalpm' 'pacman' 'sudo' 'git')
source=('aurman_sources::git+https://github.com/polygamma/aurman.git#branch=master')
md5sums=('SKIP')

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
}
