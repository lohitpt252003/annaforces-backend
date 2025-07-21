import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.github_services import get_file, add_file, update_file

a = get_file('data/problems/1/problem.json')
print(add_file('file.txt', 'this is dump'))