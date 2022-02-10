#!/bin/python3

import numpy as np
import matplotlib.pyplot as plt
import os

mem_used = os.popen("bash /root/shell/mem_free.sh").read()

values = np.array([mem_used, 100])
fig = plt.figure()
sub = fig.add_subplot(111)
sub.pie(values, startangle=90, colors=['white','#6495ED'])
fig.tight_layout()

plt.savefig('/root/django/mysite/kubernete/static/image/mem.png', c = 'c', transparent=True)
