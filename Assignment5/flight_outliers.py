
# coding: utf-8

# In[552]:

import pandas as pd
import numpy as np
import bs4
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
#webdriver api automates low level interactions 
from selenium.webdriver.common.keys import Keys
import re
import time
from unidecode import unidecode
from datetime import datetime
from dateutil.relativedelta import relativedelta
import matplotlib
import matplotlib.pyplot as plt
#get_ipython().magic(u'matplotlib inline')
matplotlib.style.use('ggplot')

import seaborn as sns
from dateutil.parser import parse
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import distance
from sklearn import svm
from sklearn.svm import OneClassSVM


# In[529]:

def scrape_data(start_date, from_place, to_place, city_name):
    
    driver = webdriver.Chrome()
    driver.get('https://www.google.com/flights/explore/')
       
    #define a function to input the places and perform click webpage
    def send_keys(location, xpath):
        key_input = driver.find_element_by_xpath(xpath)
        key_input.click()

        actions = ActionChains(driver)
        actions.send_keys(location)
        actions.send_keys(Keys.ENTER)
        actions.perform()
    
    #tap from_place by sending keys
    time.sleep(1)
    send_keys(from_place, '//*[@id="root"]/div[3]/div[3]/div/div[2]/div/div')
    
    #tap to_place by sending keys
    time.sleep(1)
    send_keys(to_place, '//*[@id="root"]/div[3]/div[3]/div/div[4]/div/div')
    
    #add start date(d = 2017-03-26) in the current url
    time.sleep(1)
    current_url = driver.current_url
    new_current_url = current_url[:-10]+start_date
    driver.get(new_current_url)
    print 'The Link of Google Flight:'
    print driver.current_url
    print '-----------------------------------------------------'
   
    #Scrap the Web Page
    
    #difference between find_element and find_elements
    time.sleep(3)
    results = driver.find_elements_by_class_name('LJTSM3-v-d')
    
    data = []
    i = 0
    cap_1st_letter = city_name[0].upper() + city_name[1:]
    while i < len(results):   
        ascii_city_name = unidecode(results[i].find_element_by_class_name('LJTSM3-v-c').text).split(',')[0]
        if cap_1st_letter == ascii_city_name:
            print 'Hold on please, give me some seconds :)'
            result = results[i]
            bars = result.find_elements_by_class_name('LJTSM3-w-x')
            for bar in bars:
                ActionChains(driver).move_to_element(bar).perform()
                time.sleep(0.5)    
                data.append((result.find_element_by_class_name('LJTSM3-w-k').find_elements_by_tag_name('div')[1].text.split('-')[0],
                            float(result.find_element_by_class_name('LJTSM3-w-k').find_elements_by_tag_name('div')[0].text.replace('$', '').replace(',', ''))
                            )
                           )
               
                
        i +=1
        
    #store data in the DataFrame
    data_df = pd.DataFrame(data, columns = ['Date_of_Flight', 'Price($)'])
    
    return data_df


# In[544]:

def scrape_data_90(start_date, from_place, to_place, city_name):
    start_date1 = start_date
    from_place1 = from_place
    to_place1 = to_place
    city_name1 = city_name
    
    df_60days = scrape_data(start_date1, from_place1, to_place1, city_name1)
    print 'Start Date: ', start_date
    
    current_start_date = datetime.strptime(start_date1, "%Y-%m-%d")
    start_date_after_60 = (current_start_date+ relativedelta(days=60)).strftime("%Y-%m-%d")
    start_date_after_90 = (current_start_date+ relativedelta(days=90)).strftime("%Y-%m-%d")
    print 'After 60 Days:', start_date_after_60
    print 'After 90 Days:', start_date_after_90
    
    df_30days = scrape_data(start_date_after_60, from_place, to_place, city_name)
    df_30days2 = df_30days.iloc[:30,:]
    data_df_90 = pd.concat([df_60days, df_30days2])
    data_df_90 = data_df_90.set_index([range(len(data_df_90))])
    return data_df_90


# #### Test Different scaling, eps, min_samples
# * Noise points share the same color with its belonging cluster (shortest Euclidean distance)
# * Hollow circles mean the mistake prices ( 2 std away from the cluster mean or $50 lower than the mean)
# * Refered from the plots, best parameters: eps = 0.04, min_samples = 3
# 

# In[738]:

def task_3_dbscan(flight_data):  
    
    epslions = [0.04, 0.05, 0.06]
    minimum_samples = [2,3,4]
    
    dbscan_dataframe = flight_data
    px = [x for x in dbscan_dataframe['Price($)']]
    ff = pd.DataFrame(px, columns=['Fare']).reset_index() #Add index column (index, price)
    
    #scale the values in the dates and price
    ff_values = ff.values
    min_max_scaler = preprocessing.MinMaxScaler()
    ff_scaled = min_max_scaler.fit_transform(ff_values)
    ff_scaled_df = pd.DataFrame(ff_scaled, columns=['Scaled_index', 'Scaled_price'])
    
    #Dbscan Model 
    plt.figure(figsize=(18, 18))
    count = 0
    for p in range(len(epslions)):
        for m in range(len(minimum_samples)):
            count +=1
            ax = plt.subplot(len(epslions), len(minimum_samples), count)
            plt.setp(ax, xticks=(), yticks=())

            db = DBSCAN(eps = epslions[p], min_samples= minimum_samples[m]).fit(ff_scaled_df.loc[:,['Scaled_index', 'Scaled_price']].values)  
            #Dataframe with scaled_index and Scaled_price
            pf = pd.concat([ff_scaled_df, pd.DataFrame(db.labels_, columns= ['cluster'])], axis= 1)    

            #create non-scaled price and index
            df_no_scaled = pd.concat([ff,pd.DataFrame(db.labels_, columns= ['cluster'])], axis= 1)

            noise_points = pf[pf['cluster'].isin([-1])].iloc[:,:-1]#DF: with label -1    
            noise_points['Fare'] = df_no_scaled['Fare'] # add price column    
            noise_point_indexes = noise_points.index
            
            num_clusters = len(pf.cluster.unique())-1 # exclude -1 labels

            #calculate distance of every noise points to clusters 

            min_distance_all_points = [] 
            np_cluster = []
            noise_X = []
            n = 0    
            while n < len(noise_points): 
                j = 0
                inner_loop_distance = []
                noise_point = noise_points.iloc[n][:-1]
                min_distance = 100
                
                while j < num_clusters:                        
                    cluster_mean = np.mean(pf[pf['cluster'].isin([j])], axis= 0)[:-1]# use 2 columns: index and price
                    
                    #distance between noise points and cluster mean
                    temp_distance = distance.euclidean(cluster_mean,noise_point) 
                    if min_distance > temp_distance:
                        min_distance = temp_distance
                        min_j = j                 
                    j+=1
                np_cluster.append([noise_point.values,min_j])
                
                #check 2std away from the mean        
                price_std_cluster = np.std(df_no_scaled['Fare'][df_no_scaled['cluster'].isin([min_j])])
                price_mean_cluster = np.mean(df_no_scaled['Fare'][df_no_scaled['cluster'].isin([min_j])])
                price_noise = noise_points['Fare'][noise_point_indexes[n]]

                if ((price_mean_cluster-2* price_std_cluster >price_noise )) or (price_mean_cluster - price_noise >50): 
                    min_distance_all_points.append((min_distance, noise_point_indexes[n], min_j, price_noise))

                    noise_X.append(noise_point_indexes[n])

                n+=1    
            #clusters plot
            text = ['{0}'.format(i) for i in df_no_scaled['index']]
            labels = db.labels_
            clusters = len(set(labels))
            unique_labels = set(labels)
            colors = plt.cm.Spectral(np.linspace(0,1,len(unique_labels)))
            
            for k, c in zip(unique_labels, colors):
                class_member_mask = (labels ==k)
                xy = ff_scaled_df.loc[:,['Scaled_index', 'Scaled_price']].values[class_member_mask]
                if k!= -1:
                    plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor = c, markeredgecolor='k', markersize=10, label = k)
                    plt.legend()

            for r in np_cluster:
                cloest = r[1]
                plt.plot(r[0][0], r[0][1], 'o',markerfacecolor =colors[cloest],markersize=10)
                
            for n in (noise_X):
                ab = list(ff_scaled_df.iloc[n, :])
                plt.plot(ab[0], ab[1],'wo',markersize=7)

            plt.title("Total Clusters: {}\nEPS: {};Min_samples:{}".format(clusters, epslions[p], minimum_samples[m]), fontsize=12,
                y=1.01);
            plt.savefig('task_3_dbscan.png')
     
    
    return dbscan_dataframe.loc[noise_X]

        
             


# In[758]:

def task_3_IQR(flight_data):
    dbscan_dataframe = flight_data
    price_to_plot = dbscan_dataframe['Price($)']
    q75, q25 = np.percentile(price_to_plot, [75 ,25])
    iqr = q75 - q25
    
    lower =q25 - 1.5*iqr
    upper = q75 + 1.5*iqr
    outlier = []
    n = 0
    while n < len(dbscan_dataframe):
        each = dbscan_dataframe.iloc[n,:]  #Date: each[0]; Price: each[1]
    
        if each[1] <= lower or each[1] >= upper:
             outlier.append(n)
        n+=1
    
    plt.figure(1, figsize=(6, 6))
   
    #dbscan_dataframe['Price($)'].plot.box()
    x =  dbscan_dataframe['Price($)']
    plt.boxplot(x, 0, 'gD')
    plt.xticks([1], ['Price'])

    plt.title("Box Plot of Fare");
    plt.savefig('task_3_iqr.png') #plt.savefig('task_3_dbscan.png') 
    
    if not outlier:
        print "No Outlier"
    else:
        return dbscan_dataframe.loc[outlier] 


# #### SVM
# SVM has a regularisation parameter, which makes me think about engineering the kernels, nu and gamma.
# 
# Best Parameters: nu=0.15, kernel='poly', gamma=0.05

# In[859]:

def task_3_ec(flight_data):
    dbscan_dataframe = flight_data

    px = [x for x in dbscan_dataframe['Price($)']]
    ff = pd.DataFrame(px, columns=['Fare']).reset_index() #Add index column (index, price)
    
    #scale the values in the dates and price
    ff_values = ff.values
    min_max_scaler = preprocessing.MinMaxScaler()
    ff_scaled = min_max_scaler.fit_transform(ff_values)
    ff_scaled_df = pd.DataFrame(ff_scaled, columns=['Scaled_index', 'Scaled_price'])
    
    kernels = ['linear', 'poly', 'rbf', 'sigmoid']
    nus = [0.05,0.1,0.12,0.15,0.2]

    count = 0
    for p in range(len(kernels)):
        for m in range(len(nus)):
            count +=1
    
            #SVM Model 
            x = ff_scaled_df.loc[:,['Scaled_index', 'Scaled_price']].values
            nolvety= svm.OneClassSVM(nu=nus[m], kernel=kernels[p], gamma='auto').fit(x)  
            y = nolvety.predict(x)

            plt.figure(figsize=(6, 4))
            plt.scatter(x[:, 0], x[:, 1], c=y)
            plt.xlabel("Index")
            plt.ylabel("Fare")
            plt.title("No.{} Kernel: {}; Nu:{}".format(count,kernels[p], nus[m]), fontsize=12,
                y=1.01);
            plt.savefig('task_3_ec'+str(count)+'.png');


        #average price for points with label 1  
        #Ploy with nu =0.15
    x = ff_scaled_df.loc[:,['Scaled_index', 'Scaled_price']].values
    nolvety= svm.OneClassSVM(nu=0.15, kernel='poly', gamma=0.05).fit(x)  
    y = nolvety.predict(x)
    
    pf = pd.concat([ff, pd.DataFrame(y, columns= ['cluster'])], axis= 1) 
    price_std_cluster = np.std(pf['Fare'][pf['cluster'].isin([1])])
    price_mean_cluster = np.mean(pf['Fare'][pf['cluster'].isin([1])])
    
    noise_points = pf[pf['cluster'].isin([-1])].iloc[:,:-1]#DF: with label -1
    noise_point_indexes = noise_points.index

    min_distance_all_points=[]

    n = 0
    while n < len(noise_points):
        price_noise = noise_points['Fare'][noise_point_indexes[n]]
        if ((price_mean_cluster-2* price_std_cluster >price_noise )) or (price_mean_cluster - price_noise >50): 
            min_distance_all_points.append(noise_point_indexes[n])

        n+=1
    return dbscan_dataframe.loc[min_distance_all_points]


# #### Enlarge the Coefficients of Date: 
# * x= Date, y = 20, $eps = \sqrt{x^{2} + y^{2}} ; x < eps< 2x$
# * $x < y < \sqrt{3}x $, any X value in this range would meet the requirement that difference in 5 concequtive days less than $20

# In[802]:

def task_4_dbscan(flight_data):
    dbscan_dataframe = flight_data
    coef_x_index = [12,13,14,15,16,17,18,19,20]
    
    plt.figure(figsize=(18, 18))
        
    px = [x for x in dbscan_dataframe['Price($)']]
    ff = pd.DataFrame(px, columns=['Fare']).reset_index() #Add index column (index, price)
    ff['Diffs'] = ff['Fare'].diff() #y =20
    ff['index'] = ff['index'].apply(lambda x: x*coef_x_index[0])

    #Dbscan Model 
    epsilon = np.sqrt(20**2 + coef_x_index[1]**2)
    db = DBSCAN(eps = epsilon, min_samples= 2).fit(ff.loc[:,['index','Fare']].values) #Build the Dbscan Model

    #clusters plot
    text = ['{0}'.format(i) for i in ff['index']]
    labels = db.labels_
    clusters = len(set(labels))
    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0,1,len(unique_labels)))
        
    for k, c in zip(unique_labels, colors):
        class_member_mask = (labels ==k)
        xy = ff.loc[:,['index','Fare']].values[class_member_mask]
        if k!=-1:
            plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor = c, markeredgecolor='k', markersize=14, label = k)
            plt.legend()
    plt.xlabel("Index")
    plt.ylabel("Fare")

    plt.title("Total Clusters: {}\n Index Scaled by: {}".format(clusters,coef_x_index[0]), fontsize=12,
            y=1.01);

        #5points    
    pf = pd.concat([ff, pd.DataFrame(db.labels_, columns= ['cluster'])], axis= 1) 
    num_clusters = len(pf.cluster.unique())-1
    counts = pf.groupby('cluster').size()

    h = 0 # cluster number
    df_return = pd.DataFrame()
    index_list = []
    while h <= num_clusters:
        individual =  pf[pf['cluster'].isin([h])]
        num_points_in_clusters = len(individual)

        if num_points_in_clusters >=5: #have at least 5 points in the cluster
            min_avg_price = 100**2 # initialize a large value
            v = 0 #lowest average price of 5 days
            while v+5 <= num_points_in_clusters:
                temp_ave_price = np.mean(individual['Fare'][v:v+5])
            
                if min_avg_price > temp_ave_price:
                    min_avg_price = temp_ave_price
                    min_v = v 
                v+=1
            
            for each in individual.index[min_v:min_v+5]:
                index_list.append(each)
            
            plot_cluster = individual.iloc[min_v:min_v+5,:]
            if max(plot_cluster['Fare']) - min(plot_cluster['Fare'])<=20: #difference between maximun and minimum price< 20
                plt.plot(plot_cluster.iloc[:,0], plot_cluster.iloc[:,1], 'wo',markersize=10)
                df_return = plot_cluster.append(plot_cluster, ignore_index=True)
                

        h+=1 
    return dbscan_dataframe.loc[index_list]


# In[ ]:




# In[531]:

#test 
df = scrape_data('2017-04-12', 'newyork', 'United States', 'boston')

print 'q1:', df


# In[545]:

#test
print 'q2:', scrape_data_90('2017-04-12', 'newyork', 'Scandinavia', 'Alesund')


# In[861]:

print 'q3.1:',task_3_dbscan(df)


# In[759]:

print 'q3.2:', task_3_IQR(df)


# In[860]:

print 'q3.3:',task_3_ec(df)


# In[803]:

print 'q4:',task_4_dbscan(df)

