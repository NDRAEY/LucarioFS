from setuptools import setup, find_packages
import src.lucario_fs.version as version

setup(
    name='lucario_fs',
    version='.'.join(list(map(str, version.__version__))),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points = {
        'console_scripts': [
            'mkfs.lucario = lucario_fs.utils.mkfs:premain',
            'lucariofs-ls = lucario_fs.utils.ls:premain',
            'lucariofs-read = lucario_fs.utils.read:premain',
            'lucariofs-write = lucario_fs.utils.write:premain',
            'lucariofs-info = lucario_fs.utils.info:premain',
        ]
    },
    package_data={'lucario_fs': ['utils/*']},
)
