import os.path
import sys

version = "2.0.2"
date = ("May", "8", "2018")
title = "DistToPath"
author = "Max Larsson"
email = "max.larsson@liu.se"
homepage = "www.liu.se/medfak/forskning/larsson-max/software"
if hasattr(sys, 'frozen'):
    if '_MEIPASS2' in os.environ: 
        path = os.environ['_MEIPASS2']
    else:
        path = sys.argv[0]
else:
    path = __file__
app_path = os.path.dirname(path)
icon = os.path.join(app_path, "disttopath.ico")
