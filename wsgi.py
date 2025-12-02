# WSGI Configuration - Toleo Rahisi na Imara
# Inahakikisha Python inajua wapi pa kupata app.py

import sys
import os

# Jina lako la mtumiaji (username) linabadilishwa hapa
USERNAME = 'abdon' 

# Njia ya Folda ya ImpactfulMind
# Hili linaelekeza Python kwenye /home/abdon/ImpactfulMind
project_folder = f'/home/{USERNAME}/ImpactfulMind' 

if project_folder not in sys.path:
    # Ingiza folda ya ImpactfulMind kwanza kwenye njia ya mfumo
    sys.path.insert(0, project_folder)

# Import app yetu. Sasa itafanya kazi kwa sababu njia imesajiliwa.
from app import app as application 

# Hakikisha umepiga Save baada ya kubandika code hii!
