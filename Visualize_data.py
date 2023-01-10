# Version 1.2
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.subplots as sp

class Visualize_data(): #Vizualizacija dataframe-a z matplotlib
    
    def __init__(self, dataframe, time = 'Close date'):
        """
        dataframe: Pandas dataframe, resulting from Harvest_data or subsequent operations.
        time: Column name to take for x values. String.
        """
        self.data = dataframe
        
        self.data['Show date'] = self.data[time]
        
    def simple_visualize(self, *args):
        """
        Simple visalisation function.

        args: Column names for y-axis data. String.
        """
        y_axis = []
        for i in args:
            y_axis.append(i)
            
        fig = px.line(self.data, x = "Show date", y = y_axis)
        fig.show()
        return
