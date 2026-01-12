from setuptools import setup
from Cython.Build import cythonize

# 這裡列出我們想要保護的核心邏輯檔案
# app.py 通常留著當介面，我們保護後面的大腦就好
files_to_protect = [
    "ingestion.py",
    "retrieval.py",
    "generation.py"
]

setup(
    ext_modules = cythonize(files_to_protect, compiler_directives={'language_level': "3"})
)