import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn
import sqlalchemy
import requests

# Check versions
print("✅ Environment check")
print("pandas:", pd.__version__)
print("numpy:", np.__version__)
print("matplotlib:", plt.matplotlib.__version__)
print("scikit-learn:", sklearn.__version__)
print("SQLAlchemy:", sqlalchemy.__version__)
print("requests:", requests.__version__)

# Quick sanity test
df = pd.DataFrame({
    "x": np.arange(0, 10),
    "y": np.random.rand(10)
})
df.plot(x="x", y="y", title="Test Plot")
plt.show()
