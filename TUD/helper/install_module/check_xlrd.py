#!/usr/bin/python
import pip
import os

# Check package installed or not
def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        os.system('pip install ' + package)

def main():
    import_or_install('xlrd')

    
if __name__ == '__main__':
    main()