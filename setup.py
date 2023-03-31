from setuptools import setup, find_packages

setup(
    name='lucario_fs',
    version='0.1.0',
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
