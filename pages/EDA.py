import pandas as pd
import pandas_profiling
import numpy as np
import streamlit as st

from streamlit_pandas_profiling import st_profile_report

#Add minutes
def addMinutes(time, mins):
    return (pd.to_timedelta(time) + pd.Timedelta(minutes=mins))

def load_data():
    df = pd.read_csv('flight_data.csv', index_col=0)
    #Cleaning and formatting time columns
    df['dep_time'] = df.dep_time[~df.dep_time.isna()].astype(np.int64).apply('{:0>4}'.format)
    df['dep_time'] = pd.to_timedelta(df.dep_time.str[:2]+':'+df.dep_time.str[2:]+':00')



    df['arr_time'] = df.arr_time[~df.arr_time.isna()].astype(np.int64).apply('{:0>4}'.format)
    df['arr_time'] = pd.to_timedelta(df.arr_time.str[:2]+':'+df.arr_time.str[2:]+':00')


    df[['dep_time' , 'arr_time', ]] = df[['dep_time', 'arr_time', ]].apply(lambda x: pd.to_timedelta(x))

    #Arrival delay threshold is -100 mins
    arr_delay_thresh_mask = (df.arr_delay.notna() & (df.arr_delay < -100))
    df.loc[arr_delay_thresh_mask, "arr_delay"] = (1440 + df.loc[arr_delay_thresh_mask, "arr_delay"])
    
    #Replace add missing air_time
    air_time_mask = (df.dep_time.notna() & df.arr_time.notna() & df.air_time.isna())
    df.loc[air_time_mask, "air_time"] = abs((df.loc[air_time_mask, "arr_time"] - df.loc[air_time_mask, "dep_time"]).astype('timedelta64[s]')//60)
    
    # Create two columns with Ontime, Late and Cancelled status for both departure and arrival
    df.loc[df.dep_delay.isna(), "dep_status"]="Canceled"
    df.loc[df.dep_delay <= 0, "dep_status"]="OnTime"
    df.loc[df.dep_delay > 0, "dep_status"]="Late"
    df.loc[df.arr_delay.isna(), "arr_status"]="Canceled"
    df.loc[df.arr_delay <= 0, "arr_status"]="OnTime"
    df.loc[df.arr_delay > 0, "arr_status"]="Late"

    #Dropping unwanted columns
    df.drop(columns=['year','hour','minute','tailnum'], inplace=True)
    df[['month','day', 'carrier', 'origin', 'dest', 'dep_status', 'arr_status']] = df[['month','day', 'carrier', 'origin','dest', 'dep_status', 'arr_status']].apply(lambda x: x.astype('category'))
    
    return df

with st.spinner('Loading Data...'):
    df = load_data()
    st.success('Loading Data... done!')

pr = df.profile_report()

st_profile_report(pr)

