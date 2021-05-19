'''
CONSOLE COMMAND: Add Return Date of Activity
REQUEST FOR CHANGE: 658
ISSUE: 1029
CMD: python scripts/add_return_doa.py | tee -a logs/rfc_0658_20210519T1000.log

Update Return Running Sheet entries to set Date of Activity to date added.
'''
import os
import sys
import django

proj_path = 'app'
proj_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(proj_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wildlifecompliance.settings")
django.setup()

from wildlifecompliance.components.returns.services import ReturnService

try:

    ReturnService.etl_return_sheet(True)

except Exception as e:
    print(e)
