import sys
from paver.easy import *
from paver import doctools
from paver.setuputils import setup

PYCOMPILE_CACHES = ['*.pyc', '*$py.class']

options(
        sphinx=Bunch(builddir='.build'),
)


def sphinx_builddir(options):
    return path('docs') / options.sphinx.builddir / 'html'


@task
def clean_docs(options):
    sphinx_builddir(options).rmtree()


@task
@needs('clean_docs', 'paver.doctools.html')
def html(options):
    destdir = path('Documentation')
    destdir.rmtree()
    builtdocs = sphinx_builddir(options)
    builtdocs.move(destdir)


@task
@needs('paver.doctools.html')
def qhtml(options):
    destdir = path('Documentation')
    builtdocs = sphinx_builddir(options)
    sh('rsync -az %s/ %s' % (builtdocs, destdir))


@task
def autodoc(options):
    sh('extra/release/doc4allmods celery')


@task
def verifyindex(options):
    sh('extra/release/verify-reference-index.sh')


@task
def verifyconfigref(options):
    sh('PYTHONPATH=. %s extra/release/verify_config_reference.py \
            docs/configuration.rst' % (sys.executable, ))


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors'),
])
def flake8(options):
    noerror = getattr(options, 'noerror', False)
    complexity = getattr(options, 'complexity', 22)
    sh("""flake8 --ignore=W602 celery | perl -mstrict -mwarnings -nle'
        my $ignore = m/too complex \((\d+)\)/ && $1 le %s;
        if (! $ignore) { print STDERR; our $FOUND_FLAKE = 1 }
    }{exit $FOUND_FLAKE;
        '""" % (complexity, ), ignore_error=noerror)


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors'),
])
def flakeplus(options):
    noerror = getattr(options, 'noerror', False)
    sh('flakeplus celery', ignore_error=noerror)


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors')
])
def flakes(options):
    flake8(options)
    flakeplus(options)


@task
def clean_readme(options):
    path('README').unlink_p()
    path('README.rst').unlink_p()


@task
@needs('clean_readme')
def readme(options):
    sh('%s extra/release/sphinx-to-rst.py docs/templates/readme.txt \
            > README.rst' % (sys.executable, ))


@task
def bump(options):
    sh("extra/release/bump_version.py \
            celery/__init__.py docs/includes/introduction.txt \
            --before-commit='paver readme'")

@task
@cmdopts([
    ('coverage', 'c', 'Enable coverage'),
    ('quick', 'q', 'Quick test'),
    ('verbose', 'V', 'Make more noise'),
])
def test(options):
    cmd = 'CELERY_LOADER=default nosetests'
    if getattr(options, 'coverage', False):
        cmd += ' --with-coverage3'
    if getattr(options, 'quick', False):
        cmd = 'QUICKTEST=1 SKIP_RLIMITS=1 %s' % cmd
    if getattr(options, 'verbose', False):
        cmd += ' --verbosity=2'
    sh(cmd)


@task
@cmdopts([
    ('noerror', 'E', 'Ignore errors'),
])
def pep8(options):
    noerror = getattr(options, 'noerror', False)
    return sh("""find . -name "*.py" | xargs pep8 | perl -nle'\
            print; $a=1 if $_}{exit($a)'""", ignore_error=noerror)


@task
def removepyc(options):
    sh('find . -type f -a \\( %s \\) | xargs rm' % (
        ' -o '.join("-name '%s'" % (pat, ) for pat in PYCOMPILE_CACHES), ))
    sh('find . -type d -name "__pycache__" | xargs rm -r')


@task
@needs('removepyc')
def gitclean(options):
    sh('git clean -xdn')


@task
@needs('removepyc')
def gitcleanforce(options):
    sh('git clean -xdf')


@task
@needs('flakes', 'autodoc', 'verifyindex',
       'verifyconfigref', 'test', 'gitclean')
def releaseok(options):
    pass


@task
def verify_authors(options):
    sh('git shortlog -se | cut -f2 | extra/release/attribution.py')


@task
def coreloc(options):
    sh('xargs sloccount < extra/release/core-modules.txt')


@task
def testloc(options):
    sh('sloccount celery/tests')


@task
def loc(options):
    sh('sloccount celery')