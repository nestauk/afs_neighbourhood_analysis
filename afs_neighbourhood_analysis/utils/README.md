# Utilities

## Saving altair figures

The `altair_utils.py` script contains utilities to save altair chats programmatically. In summary, this involves creating a browser window with the image and saving it with selenium. 

This is how it works:

```
import altair as alt
import pandas as pd
from numpy.random import random_sample
from afs_neighbourhood_analysis.utils.altair_utils import google_chrome_driver_setup,save_altair

# Initialise the google chrome driver
d = google_chrome_driver_setup()

# Create a random dataset
data = pd.DataFrame({"x":random_sample(100),"y":random_sample(100)})

# Create a chart
ch = alt.Chart(data).mark_point(filled=True).encode(x="x",y="y",color="x")

# Save the chart (NB by default this is saved as a png and an html in the outputs/figures folder but you can change the directory with the argument 'path'
save_altair(ch,name="test",driver=d)
```

The script also contains a function to automatically rescale altair charts so that the axes are easier to read.




