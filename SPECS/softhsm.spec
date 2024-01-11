#global prever rc1
# Rebuild configure.ac if patches do change it
%global rebuild_ac 1

Summary: Software version of a PKCS#11 Hardware Security Module
Name: softhsm
Version: 2.6.0
Release: %{?prever:0.}5%{?prever:.%{prever}}%{?dist}
License: BSD
Url: http://www.opendnssec.org/
Source: http://dist.opendnssec.org/source/%{?prever:testing/}%{name}-%{version}.tar.gz
Source1: http://dist.opendnssec.org/source/%{?prever:testing/}%{name}-%{version}.tar.gz.sig

Patch1: softhsm-2.6.1-rh1834909-exit.patch
Patch2: softhsm-2.6.1-rh1857272-negatives.patch

Group: Applications/System
BuildRequires: openssl-devel >= 1.0.1k-6, sqlite-devel >= 3.4.2, cppunit-devel
BuildRequires: gcc-c++, pkgconfig, p11-kit-devel, nss-devel

Requires(pre): shadow-utils
Requires: p11-kit, nss-tools
Requires: openssl-libs >= 1.0.1k-6

%global _hardened_build 1

%global softhsm_module "SoftHSM PKCS #11 Module"

%description
OpenDNSSEC is providing a software implementation of a generic
cryptographic device with a PKCS#11 interface, the SoftHSM. SoftHSM is
designed to meet the requirements of OpenDNSSEC, but can also work together
with other cryptographic products because of the PKCS#11 interface.

%package devel
Summary: Development package of softhsm that includes the header files
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, openssl-devel, sqlite-devel
%if 0%{?prever:!} || 0%{?rebuild_ac}
BuildRequires: autoconf, libtool, automake
%endif

%description devel
The devel package contains the libsofthsm include files

%prep
%setup -q -n %{name}-%{version}%{?prever}
%patch1 -p1
%patch2 -p1

# remove softhsm/ subdir auto-added to --libdir
sed -i "s:full_libdir/softhsm:full_libdir:g" configure
%if 0%{?prever:1} || 0%{?rebuild_ac}
sed -i 's:^full_libdir=":#full_libdir=":g' configure.ac
%endif
sed -i "s:libdir)/@PACKAGE@:libdir):" Makefile.in

sed -i 's:$full_libdir/libsofthsm2\.so:libsofthsm2\.so:g' configure

%if 0%{?prever:1} || 0%{?rebuild_ac}
sed -i 's:$full_libdir/libsofthsm2\.so:libsofthsm2\.so:g' configure.ac
%endif

%if 0%{?prever:1} || 0%{?rebuild_ac}
autoreconf -fiv
%endif

%build
%configure --libdir=%{_libdir}/pkcs11 --with-openssl=%{_prefix} --enable-ecc --disable-gost \
           --with-migrate --enable-visibility --with-p11-kit=%{_datadir}/p11-kit/modules/

make %{?_smp_mflags}
# install our copy of pk11install taken from coolkey package

%check
# skip while cppunit is broken
#make check

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm %{buildroot}/%{_sysconfdir}/softhsm2.conf.sample
rm -f %{buildroot}/%{_libdir}/pkcs11/*a
mkdir -p %{buildroot}%{_includedir}/softhsm
cp src/lib/*.h %{buildroot}%{_includedir}/softhsm
mkdir -p %{buildroot}/%{_sharedstatedir}/softhsm/tokens

# leave a softlink where softhsm-1 installed its library. Programs like
# opendnssec have that filename in their configuration file.
mkdir -p %{buildroot}/%{_libdir}/softhsm/
ln -s ../pkcs11/libsofthsm2.so %{buildroot}/%{_libdir}/softhsm/libsofthsm.so
# rhbz#1272423 NSS needs it to be in the search path too
( cd  %{buildroot}/%{_libdir} ; ln -s pkcs11/libsofthsm2.so)

%files
%config(noreplace) %{_sysconfdir}/softhsm2.conf
%{_bindir}/*
%dir %{_libdir}/softhsm
%{_libdir}/pkcs11/libsofthsm2.so
%{_libdir}/libsofthsm2.so
%{_libdir}/softhsm/libsofthsm.so
%attr(0664,root,root) %{_datadir}/p11-kit/modules/softhsm2.module
%attr(0750,ods,ods) %dir %{_sharedstatedir}/softhsm
%attr(1770,ods,ods) %dir %{_sharedstatedir}/softhsm/tokens
%doc LICENSE README.md NEWS
%{_mandir}/*/*

%files devel
%attr(0755,root,root) %dir %{_includedir}/softhsm
%{_includedir}/softhsm/*.h

%pre
getent group ods >/dev/null || groupadd -r ods
getent passwd ods >/dev/null || \
    useradd -r -g ods -d %{_sharedstatedir}/softhsm -s /sbin/nologin \
    -c "softhsm private keys owner" ods
exit 0

%post

%triggerpostun -- softhsm < 2.0.0
if [ -f /var/softhsm/slot0.db ]; then
      runuser -g ods ods -c 'softhsm2-migrate --db /var/softhsm/slot0.db --pin 1234 --slot 0' || :
fi

%changelog
* Mon Feb 15 2021 Thomas Woerner <twoerner@redhat.com> - 2.6.0-5
- Install prever devel package requirements for new negative option patch
  Related: RHBZ#1857272

* Mon Feb 15 2021 Alexander Bokovoy <abokovoy@redhat.com> - 2.6.0-4
- Fixes: rhbz#1857272 - negative option for token.mechanism not working correctly

* Thu Jun 04 2020 Alexander Bokovoy <abokovoy@redhat.com> - 2.6.0-3
- Fixes: rhbz#1834909 - softhsm use-after-free on process exit
- Synchronize the final fix with Fedora

* Thu May 14 2020 Paul Wouters <pwouters@redhat.com> - 2.6.0-2
- Fixes: rhbz#1834909 - softhsm use-after-free on process exit

* Wed Apr 01 2020 Alexander Bokovoy <abokovoy@redhat.com> - 2.6.0-1
- Fixes: rhbz#1818877 - rebase to softhsm 2.6.0+
- Fixes: rhbz#1701233 - support setting supported signature methods on the token

* Mon Feb 17 2020 Alexander Bokovoy <abokovoy@redhat.com> - 2.4.0-4
- Provide specific version libsofthsm2.so for p11-kit
- Fixes: rhbz#1727065

* Tue Feb 11 2020 Alexander Bokovoy <abokovoy@redhat.com> - 2.4.0-3
- Remove architecture-specific path from softhsm2.module definition
- Fixes: rhbz#1727065

* Fri Aug 17 2018 Alexander Bokovoy <abokovoy@redhat.com> - 2.4.0-2
- Replace PKCS11 headers by a more liberal version from p11-kit
- Fixes: rhbz#1615766

* Sat Aug 11 2018 Nikos Mavrogiannopoulos <nmav@redhat.com> - 2.4.0-1
- Updated to latest upstream release

* Tue Jul 31 2018 Alexander Bokovoy <abokovoy@redhat.com> - 2.3.0-4
- Fix crash when used as a PKCS11 library via p11-kit (#1608690)

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.3.0-3.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Feb 02 2018 Nikos Mavrogiannopoulos <nmav@redhat.com> - 2.3.0-3
- Remove softhsm2-pk11install. Software modules are to be registered with
  p11-kit as in https://fedoraproject.org/wiki/PackagingDrafts/Pkcs11Support (#1541095).

* Tue Dec 05 2017 Jakub Jelen <jjelen@redhat.com> - 2.3.0-2
- Add support for RSA-PSS from upstrem PR#335

* Tue Dec 05 2017 Jakub Jelen <jjelen@redhat.com> - 2.3.0-1
- New upstream release (#1467329)

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.2.0-2.2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.2.0-2.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Tue Jun 27 2017 Nikos Mavrogiannopoulos <nmav@redhat.com> - 2.2.0-2
- Increased the level of messages that go to syslog, thus softhsm
  will no longer write on syslog when it cannot open the shared DB (#1425135)
- Allow users in the 'ods' group to store their keys in /var/lib/softhsm/tokens/
  while at the same time disallow deleting other users' keys (using the
  sticky bit). Prevent users in the 'ods' group from writing in /var/lib/softhsm.

* Thu Jun 22 2017 Nikos Mavrogiannopoulos <nmav@redhat.com> - 2.2.0-1
- Rebased to latest upstream release

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.1.0-2.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Sep 23 2016 Paul Wouters <pwouters@redhat.com> - 2.1.0-2
- Resolves: rhbz#1378800 Module cleanup crash

* Mon May 16 2016 Paul Wouters <pwouters@redhat.com> - 2.1.0-1
- Resolves: rhbz#1244461 Updated to 2.1.0
- Resolves: rhbz#1272423 Softhsm PKCS#11 module not visible to NSS becasue it is not in the search path
- Resolves: rhbz#1177086 A marked as trusted certificate cannot be written in a softhsmv2 db
- Resolves: rhbz#1272453 - A marked as CA certificate cannot be written in a softhsmv2 db
- Removed merged in bug#162 patch
- Temporarily disable make check because cppunit is broken

* Thu Feb 25 2016 Paul Wouters <pwouters@redhat.com> - 2.0.0-2
- Resolves: rhbz#1272453 A marked as CA certificate cannot be written in a softhsmv2 db

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.0.0-1.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Sep 02 2015 Paul Wouters <pwouters@redhat.com> - 2.0.0-1
- Resolves: rhbz#1244461 Update to softhsm-2.0.0
- Resolves: rhbz#1177086 A marked as trusted certificate cannot be written in a softhsmv2 db
- Resolves: rhbz#1159827 Typo in homedir in /etc/passwd
- Added global prever to toggle snapshot vs full release build changes

* Fri Jun 26 2015 Petr Spacek <pspacek@redhat.com> - 2.0.0rc1-3
- Add dependency on OpenSSL with fixed AES wrapping support

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.0rc1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Jun 01 2015 Petr Spacek <pspacek@redhat.com> - 2.0.0rc1-1
- Rebase to latest upstream release

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 2.0.0b1-4
- Rebuilt for GCC 5 C++11 ABI change

* Tue Sep 30 2014 Paul Wouters <pwouters@redhat.com> - 2.0.0b1-3
- Add support for CKM_RSA_PKCS_OAEP key un/wrapping [Petr Spacek]
- Use OpenSSL EVP interface for AES key wrapping [Petr Spacek]
- Fix softhsm2-pk11install buid and post call
- Do not use --with-objectstore-backend-db (causes issues on i686)
- Change install directory to /usr/lib*/pkcs11/
- Install pkcs11 module file
- Use official upstream tar ball
- Create ods user to own softhsm/token files
- Enable migration tools (for softhsm-v1 installs)
- Add softlink for softhsm-v1 .so (needed for opendnssec's conf.xml)
- Require p11-kit, nss-tools, for SoftHSM PKCS #11 Module file
- Copy pk11install.c from coolkey package
- Enable hardened build
- Add upstream official source url

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri Apr 18 2014 Paul Wouters <pwouters@redhat.com> - 1.3.6-1
- Updated to 1.3.6 (rhbz#1070196)
- Provide a p11-kit module file (rhbz#1085327)

* Sun Nov 03 2013 Paul Wouters <pwouters@redhat.com> - 1.3.5-1
- Updated to 1.3.5 (rhbz#987721)

* Tue Jul 30 2013 Paul Wouters <pwouters@redhat.com> - 1.3.3-4
- Rebuilt for new botan - requires --with-botan argument

* Fri Feb 15 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jun 04 2012 Paul Wouters <pwouters@redhat.com> - 1.3.3-1
- Updated to 1.3.3

* Tue Apr 03 2012 Paul Wouters <pwouters@redhat.com> - 1.3.2-1
- Updated to 1.3.2.
- Changed user from opendnssec to ods, as used in the opendnssec package

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Oct 27 2011 Paul Wouters <paul@xelerance.com> - 1.3.0-3
- Initial Fedora package
- Do not install the .a file
- Use a separate "opendnssec" user to own /var/sofhsm

* Tue Oct 25 2011 Paul Wouters <paul@xelerance.com> - 1.3.0-2
- Fix description texts w.r.t. include files

* Wed Oct 05 2011 Paul Wouters <paul@xelerance.com> - 1.3.0-1
- Upgraded to 1.3.0

* Thu Mar  3 2011 Paul Wouters <paul@xelerance.com> - 1.2.0-1
- Initial package for Fedora 
