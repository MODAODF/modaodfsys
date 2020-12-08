# ndcodfsys
ndcodfsys is ndcodfweb service

## preparation
- GCC 7.0 the above
- 20G disk spaces

## reques
- openjdk-8-jdk, hunspell, hunspell-en-us, libgumbo-dev,libgumbo1 (Ubuntu)
- java-1.8.0-openjdk, gumbo-parser, hunspell, hunspell-en (CentOS)

## autogen
./autogen.sh

## configure
./configure --disable-dependency-tracking --with-lang="en-US zh-TW" --disable-coinmp --enable-openssl --enable-eot --enable-ext-nlpsolver --enable-ext-wiki-publisher --enable-release-build --enable-scripting-beanshell --enable-scripting-javascript --enable-atl --disable-sdremote --disable-gstreamer-1-0 --without-junit --disable-dbgutil --disable-debug --disable-sal-log --disable-symbols --with-parallelism=2 --disable-firebird-sdbc --without-system-boost --disable-gconf --without-help --enable-python=internal --enable-pdfimport --disable-odk

#### configure productinfo optional
--with-product-name="ndcodfsys" --with-userdirproduct-version="2" --with-oxo-version-minor="3" --with-oxo-version-micro="1" --with-oxo-version-patch="1" --with-aboutbox-version="R8S4"

#### configure packages optional
--with-package-format='rpm' --enable-epm
--with-package-format='deb' --enable-epm

## make
make build-nocheck
