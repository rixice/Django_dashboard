#!/bin/python3

import numpy as np
import matplotlib.pyplot as plt
import os

cpu_used = os.popen("bash /root/shell/cpu_used.sh").read()

values = np.array([100, cpu_used])
fig = plt.figure()
sub = fig.add_subplot(111)
sub.pie(values, startangle=90, colors=['white','#6495ED'])
fig.tight_layout()

plt.savefig('/root/django/mysite/kubernete/static/image/cpu.png', c = 'c', transparent=True)
