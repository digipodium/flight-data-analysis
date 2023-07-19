import streamlit as st

#Load dependencies
import pandas as pd
import numpy as np
import plotly.express as px
import ydata_profiling as pdp
import seaborn as sns


#Add minutes
def addMinutes(time, mins):
    return (pd.to_timedelta(time) + pd.Timedelta(minutes=mins))


st.cache_data()
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


with st.spinner("loading Flight dataset"):
    df = load_data()
    st.success("Flight dataset loaded successfully")

# Sidebar
st.sidebar.header('Flight Data Analysis')

isViewEnabled = st.sidebar.checkbox('Show raw data', False, key='0')
if isViewEnabled:
    st.subheader('Raw dataset')
    st.dataframe(df)

st.subheader('Busiest airport in terms of flights departure')
buzAir = df.groupby(['origin'])['origin'].count()
fig2 = px.bar(buzAir, x=buzAir.index, y=buzAir.values, color=buzAir.index, title='Busiest airport in terms of flights departure')
st.plotly_chart(fig2, use_container_width=True)

st.subheader('Busiest airport in terms of flights arrival')
buzAir = df.groupby(['dest'])['dest'].count().sort_values(ascending=False)
fig3 = px.bar(buzAir, x=buzAir.index, y=buzAir.values, color=buzAir.index, title='Busiest airport in terms of flights arrival')
st.plotly_chart(fig3, use_container_width=True)

st.subheader('Busiest day of the week in terms of flights departure')
buzDay = df.groupby(['day'])['day'].count()
fig4 = px.bar(buzDay, x=buzDay.index, y=buzDay.values, color=buzDay.index, title='Busiest day of the week in terms of flights departure')
st.plotly_chart(fig4, use_container_width=True)

st.subheader('Flights frequency across months')
buzMonth = df.groupby(['month'])['month'].count()
fig5 = px.line(buzMonth, buzMonth.index, buzMonth.values, title='Flights frequency across months')
st.plotly_chart(fig5, use_container_width=True)
st.info('Flights frequency is lowest in February which is below 25000.')

st.subheader('Departure and Arrival status')
depStatus = df.groupby('dep_status')['dep_status'].count()
arrStatus = df.groupby('arr_status')['arr_status'].count()

c1, c2 = st.columns(2)
c1.dataframe(depStatus, use_container_width=True)
c2.dataframe(arrStatus, use_container_width=True)

st.info('Out of 336776 flights, 200089(59.1%) flights in 2013 were departed on time, 128432(38.1%) were delayed and just 8255(2.5%) of flights were canceled.')

# visualize
fig6 = px.pie(depStatus, depStatus.index, depStatus.values)
fig6.update_layout(title='Departure status', title_x=0.5)
st.plotly_chart(fig6, use_container_width=True)

fig7 = px.pie(arrStatus, arrStatus.index, arrStatus.values)
fig7.update_layout(title='Arrival status', title_x=0.5)
st.plotly_chart(fig7, use_container_width=True)

st.subheader('Best and worst airport in terms of departure and arrival delay')

depAir = df.loc[df['dep_status'] == 'Late'].groupby(['origin','dep_status'])['dep_status'].count().unstack('dep_status').sort_values(by='Late', ascending=False)
st.dataframe(depAir, use_container_width=True)

arrAir = df.loc[df['arr_status'] == 'Late'].groupby(['origin','arr_status'])['arr_status'].count().unstack('arr_status')
st.dataframe(arrAir, use_container_width=True)

st.info('EWR airport has the highest number of departure delays and JFK airport has the highest number of arrival delays.')
st.info('LGA airport is best in terms of departure and arrival delay, where as EWR is worst with 5000+ delayed flights.')

# visualize
c1, c2 = st.columns(2)
fig8 = px.bar(depAir, x=depAir.index, y=depAir['Late'], color=depAir.index, title='Departure delay')
c1.plotly_chart(fig8, use_container_width=True)
fig9 = px.bar(arrAir, x=arrAir.index, y=arrAir['Late'], color=arrAir.index, title='Arrival delay')
c2.plotly_chart(fig9, use_container_width=True)

st.subheader('Best and worst airport w.r.t departure delay %')

depAirPer = df.groupby('origin')['origin'].count().reset_index(name='total')
delayedFlights = df.loc[df['dep_status'] == 'Late'].groupby(['origin','dep_status'])['dep_status'].count().unstack('dep_status')
depAirPer['late'] = delayedFlights['Late'].values
depAirPer['percentage'] = (depAirPer['late']/depAirPer['total'])*100
depAirPer.set_index('origin', inplace=True)

st.dataframe(depAirPer, use_container_width=True)
st.info('EWR airport has the highest percentage of departure delays and LGA airport has the lowest percentage of departure delays.')
# visualize
fig10 = px.bar(depAirPer, x=depAirPer.index, y=depAirPer['percentage'], color=depAirPer.index, title='Departure delay %')
st.plotly_chart(fig10, use_container_width=True)


df1 = df.copy()
temp = df.copy()

st.subheader('Best and worst carrier in terms of departure delay %')
depCarrier = df1.loc[df1['dep_status'] == 'Late'].groupby(['carrier','dep_status'])['dep_status'].count().unstack('dep_status')
depCarrier['total'] = df1.groupby(['carrier'])['carrier'].count()
depCarrier['percentage'] = (depCarrier['Late']/depCarrier['total'])*100
depCarrier.sort_values(by='percentage', ascending=False, inplace=True)

st.dataframe(depCarrier, use_container_width=True)
st.info('WN carrier has the highest percentage of departure delays and HA carrier has the lowest percentage of departure delays.')
# visualize
fig11 = px.bar(depCarrier, x=depCarrier.index, y=depCarrier['percentage'], color=depCarrier.index, title='Departure delay %')
st.plotly_chart(fig11, use_container_width=True)

st.subheader(' Departure delay across months')
depMonth = df1.loc[df1['dep_status'] == 'Late'].groupby(['month','dep_status'])['dep_status'].count().unstack('dep_status')
depMonth['total'] = df1.groupby(['month'])['month'].count()
depMonth['percentage'] = (depMonth['Late']/depMonth['total'])*100
depMonth.sort_values(by='percentage', ascending=False, inplace=True)

st.dataframe(depMonth, use_container_width=True)

# visualize
fig12 = px.bar(depMonth, x=depMonth.index, y=depMonth['percentage'], color=depMonth.index, title='Departure delay %')
st.plotly_chart(fig12, use_container_width=True)
st.info('As we can see from the above graph, flights delay is more in June, July and December months, where as September is best month to travel.')

st.subheader('Departure delay count w.r.t origin and dest')

routeDelay = df.loc[df['dep_status'] == 'Late'].groupby(['origin','dest','dep_status'])['dep_status'].count().reset_index(name='total')
routeDelay = routeDelay[routeDelay.groupby('origin')['total'].transform(max) == routeDelay['total']].sort_values('total')
st.dataframe(routeDelay, use_container_width=True)
# visualize
fig13 = px.bar(routeDelay, x=routeDelay.index, y=routeDelay['total'], color=routeDelay.index, title='Departure delay count w.r.t origin and dest')
st.plotly_chart(fig13, use_container_width=True)
st.info('JFK-LAX route had most number of flight delay in 2013.')

st.subheader('Best and worst airport in terms of number of flights canceled')
canAir = df.loc[df['dep_status'] == 'Canceled'].groupby(['origin','dep_status'])['dep_status'].count().unstack('dep_status')
st.dataframe(canAir, use_container_width=True)
# visualize
fig14 = px.bar(canAir, x=canAir.index, y=canAir['Canceled'], color=canAir.index, title='Number of flights canceled')
st.plotly_chart(fig14, use_container_width=True)
st.info('1863 flights got canceled from JFK airport in 2013, which is lowest among all')

st.subheader('Best and worst airport w.r.t flight cancellation %')
canAirPer = df.groupby('origin')['origin'].count().reset_index(name='total')
canceledFlights = df1.loc[df1['dep_status'] == 'Canceled'].groupby(['origin','dep_status'])['dep_status'].count().unstack('dep_status')
canAirPer['canceled'] = canceledFlights['Canceled'].values
canAirPer['percentage'] = (canAirPer['canceled']/canAirPer['total'])*100
canAirPer.set_index('origin', inplace=True)

st.dataframe(canAirPer, use_container_width=True)
# visualize
fig15 = px.bar(canAirPer, x=canAirPer.index, y=canAirPer['percentage'], color=canAirPer.index, title='Flight cancellation %')
st.plotly_chart(fig15, use_container_width=True)

st.subheader('Best and worst carrier w.r.t total flight canceled')
canCarrier = df.loc[df['dep_status'] == 'Canceled'].groupby(['carrier','dep_status'])['dep_status'].count().unstack('dep_status')
canCarrier['total'] = df.groupby(['carrier'])['carrier'].count()
canCarrier.sort_values(by='total', ascending=False, inplace=True)

st.dataframe(canCarrier, use_container_width=True)
st.info('UA carrier has the highest number of flight cancellation ')
st.info('AS, F9 and OO carriers are best in terms of flight cancellation.')
# visualize
fig16 = px.bar(canCarrier, x=canCarrier.index, y=canCarrier['total'], color=canCarrier.index, title='Flight cancellation count')
st.plotly_chart(fig16, use_container_width=True)

st.subheader('Flight cancellation across months')
canMonth = df.loc[df['dep_status'] == 'Canceled'].groupby(['month','dep_status'])['dep_status'].count().unstack('dep_status')
canMonth['total'] = df.groupby(['month'])['month'].count()
canMonth.sort_values(by='total', ascending=False, inplace=True)

st.dataframe(canMonth, use_container_width=True)
st.info('Flight cancellation is lowest in October and November months')

# visualize
fig17 = px.bar(canMonth, x=canMonth.index, y=canMonth['total'], color=canMonth.index, title='Flight cancellation count')
st.plotly_chart(fig17, use_container_width=True)

st.subheader("Conclusion")
st.markdown('''
    * EWR airport has the highest number of departure delays and JFK airport has the highest number of arrival delays.
    * LGA airport is best in terms of departure and arrival delay, where as EWR is worst with 5000+ delayed flights.
    * EWR airport has the highest percentage of departure delays and LGA airport has the lowest percentage of departure delays.
    * WN carrier has the highest percentage of departure delays and HA carrier has the lowest percentage of departure delays.
    * As we can see from the above graph, flights delay is more in June, July and December months, where as September is best month to travel.
    * JFK-LAX route had most number of flight delay in 2013.
    * 1863 flights got canceled from JFK airport in 2013, which is lowest among all.
    * UA carrier has the highest number of flight cancellation.
    * AS, F9 and OO carriers are best in terms of flight cancellation.
    * Flight cancellation is lowest in October and November months.
''')
