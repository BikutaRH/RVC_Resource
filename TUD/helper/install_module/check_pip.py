#!/usr/bin/python
import os

# Check pip installed or not
def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        os.system('python get-pip.py')

def main():
    import_or_install('pip')

    
if __name__ == '__main__':
    main()