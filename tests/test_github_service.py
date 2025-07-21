import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.github_services import get_file, add_file, update_file

a = get_file('data/problems/1/problem.json')
j = a[0]  # j abhi string hai
print(j)  # yeh string print karega

# Convert string to Python dict
j_dict = json.loads(j)
print(j_dict['title'])  # ab dict se 'title' le sakte ho