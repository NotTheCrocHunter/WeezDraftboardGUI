from pandastable import Table
from tkinter import *
import pandas as pd


# ------------- GUI SETUP and func----------- #
def view_pd_table(df):
    window = Tk()
    window.title("Sleeper Project")
    table_frame = Frame(window)
    table_frame.pack(fill=BOTH, expand=1, side="right")
    select_frame = Frame(window)
    select_frame.pack(side="left")
    table = Table(table_frame, dataframe=df, showtoolbar=True, showstatusbar=True)
    table.autoResizeColumns()
    table.show()

    window.mainloop()


# df = pd.read_csv('../data/fpros/FantasyPros_2022_Draft_QB_Rankings.csv')

# view_pd_table(df)


