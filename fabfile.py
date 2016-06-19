import os
import fabric
from fabric.api import *
import fabtools

mysql_db_name = 'smarty'
mysql_user_name = 'smarty'
mysql_password = '111ff111'

#
# http://bicofino.io/2014/01/16/installing-python-2-dot-7-6-on-centos-6-dot-5/
#

project_dir = '/usr/share/nginx/html/microimpuls/smarty'
env_dir = '/usr/share/nginx/html/microimpuls/env'
uwsgi_file = '/etc/microimpuls/smarty/uwsgi/smarty.uwsgi'

python27_exe = '/usr/local/bin/python2.7'
pip27_exe = '/usr/local/bin/pip2.7'
virtualenv_cmd = '/usr/local/bin/virtualenv'

@task
def dev():
    env.user = 'root'
    env.password = '321321w'
    env.hosts = ['1.2.3.4']
    env.port = '22'

def install_pre_requirements():
    fabtools.rpm.update(kernel=False)
    fabtools.rpm.install('epel-release')
    fabtools.rpm.install([
        'python-devel',
        'gcc',
        'git',
        'mysql-devel',
        'libxml2-devel',
        'libxslt-devel',
        'libjpeg',
        'libjpeg-devel',
        'zlib',
        'zlib-devel',
        'libtiff',
        'libtiff-devel',
        'freetype',
        'freetype-devel',
        'nginx',
        'nano',
    ])
    with settings(warn_only=True):
        sudo('yes | sudo rpm -Uvh http://repo.mysql.com//mysql57-community-release-el6-7.noarch.rpm')
    fabtools.rpm.install('mysql-community-server')

def setup_python27():
    fabtools.rpm.groupinstall('development tools')
    fabtools.rpm.install([
        'zlib-devel',
        'bzip2-devel',
        'openssl-devel',
        'xz-libs wget',
    ])
    with cd('/tmp'):
        # python
        run('wget http://www.python.org/ftp/python/2.7.8/Python-2.7.8.tar.xz')
        run('xz -d Python-2.7.8.tar.xz')
        run('tar -xvf Python-2.7.8.tar')
        with cd('Python-2.7.8'):
            run('./configure --prefix=/usr/local')
            run('make')
            sudo('make altinstall')
        # setuptools
        run('wget --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz')
        run('tar -xvf setuptools-1.4.2.tar.gz')
        with cd('setuptools-1.4.2'):
            sudo('%(python27)s setup.py install ' % {'python27': python27_exe})
        # pip
        sudo('curl https://bootstrap.pypa.io/get-pip.py | sudo %(python27)s -' % {'python27': python27_exe})
        # virtualenv
        sudo('%(pip27)s install virtualenv' % {'pip27': pip27_exe})



def setup_mysql():
    # to change root password:
    # mysqld_safe --skip-grant-tables

    # mysql -u root
    # UPDATE mysql.user 
    #     SET authentication_string = PASSWORD('111ff111'), password_expired = 'N'
    #     WHERE User = 'root' AND Host = 'localhost';
    # FLUSH PRIVILEGES;

    if not fabtools.service.is_running('mysqld'):
        fabtools.service.start('mysqld')
    if not fabtools.mysql.database_exists(mysql_db_name, mysql_user='root', mysql_password='111ff111'):
        fabtools.mysql.create_database(mysql_db_name, mysql_user='root', mysql_password='111ff111')

def setup_env():
    fabtools.require.python.virtualenv(
        env_dir,use_sudo=False)
    with fabtools.python.virtualenv(env_dir):
        fabtools.python.install([
            "'Django<1.8'",
            'MySQL-python==1.2.5',
            'Pillow==2.5.1',
            'argparse==1.2.1',
            'configobj==4.7.0',
            'django-replicated==1.2',
            'django-debug-toolbar==1.2.1',
            'django-simple-captcha==0.4.2',
            'mock==1.0.1',
            'names==0.3.0',
            'pymongo==2.7.2',
            'raven==5.0.0',
            'requests==2.4.1',
            'six==1.7.3',
            'sqlparse==0.1.11',
            'wsgiref==0.1.2',
            'flup',
            'python-dateutil==2.3',
            'sleekxmpp',
            'nginx_signing',
            'progress',
            'django-geoip',
            '-e git://github.com/joshmarshall/jsonrpctcp.git@67e07632279777cf9f6ebe97977ac15d3e779bc4#egg=jsonrpctcp-master'
        ], use_sudo=False)

def setup_uwsgi():
    # sudo('%(pip27)s install uwsgi' % {'pip27': pip27_exe})

    fabtools.require.files.directory('/etc/uwsgi/apps-awailable/', use_sudo=True)
    fabric.contrib.files.upload_template(
        'smarty.ini', '/etc/uwsgi/apps-awailable/smarty.ini', use_sudo=True,
        context={
            'project_dir': project_dir,
            'env_dir': env_dir,
            'uwsgi_file': uwsgi_file,
        }
    )

    fabtools.require.files.directory('/etc/microimpuls/smarty/uwsgi/', use_sudo=True)
    fabric.contrib.files.upload_template('smarty.uwsgi', uwsgi_file, use_sudo=True)

def setup_nginx():
    fabtools.require.files.directory('/var/log/nginx/microimpuls/smarty/', use_sudo=True)


    if not fabtools.service.is_running('nginx'):
        fabtools.service.start('nginx')

    with settings(warn_only=True):
        fabtools.files.remove('/etc/nginx/conf.d/default.conf', recursive=False, use_sudo=True)
    fabric.contrib.files.upload_template('smarty.conf', '/etc/nginx/conf.d/smarty.conf', use_sudo=True)
    fabtools.service.reload('nginx')



@task
def prepare():
    # install_pre_requirements()
    # setup_python27()
    # setup_env()
    # setup_mysql()
    setup_uwsgi()
    setup_nginx()