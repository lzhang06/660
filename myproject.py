import os
import json
import requests
from flask import Flask, request, Response
from textblob import TextBlob
from slackclient import SlackClient
import bs4
from selenium import webdriver
import requests
import json, urllib
import datetime
import re
import time
import numpy as np

application = Flask(__name__)

# FILL THESE IN WITH YOUR INFO
my_bot_name = 'Lu_bot' #e.g. zac_bot
my_slack_username = 'lucinda' #e.g. zac.wentzell


#SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

slack_inbound_url = 'https://hooks.slack.com/services/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'

@application.route('/slack', methods=['POST'])
        

def inbound(): 
    # Adding a delay so that all bots don't answer at once (could overload the API).
    # This will randomly choose a value between 0 and 10 using a uniform distribution.
    delay = np.random.uniform(0, 10)
    time.sleep(delay)


    response = {'username': 'Lu_bot', 'icon_emoji': ':monkey_face:'}
    my_chatbot_name = 'Lu_bot'
    example_command = '&lt;I_NEED_HELP_WITH_CODING&gt;'
    weather_command = "&lt;WHAT'S_THE_WEATHER_LIKE_AT&gt;"


    #if request.form.get('token') == SLACK_WEBHOOK_SECRET:
    channel = request.form.get('channel_name')
    username = request.form.get('user_name')
    text = request.form.get('text')
    inbound_message = username + " in " + channel + " says: " + text
    
    
    
    if username in ['lucinda','zac.wentzell']:
        if text == '&lt;BOTS_RESPOND&gt;':
            response['text'] = 'Hello, my name is Lu_bot. I belong to Lu Zhang. I live at 52.41.5.156.'
        
        elif text.startswith(example_command):
            #split the command in 2 parts      
            text2 = text.split(':')[1]
            text2 = text2[1:]
            
            if '[' and ']' not in text2:
                #create json link of stack change
                text2 = text2.replace(' ', '%20')
                url1 = 'https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=activity'
                url3 = '&site=stackoverflow'
                url2 = '&q='+text2
                url_new = url1+url2+url3

                #read json file, which is a list contain dict
                json_data = requests.get(url_new).json()
                js_str = ""
                js_attachments = []
                js_dict = {}
                i=0
                while i <5 :
                    js_dict['title'] = json_data['items'][i]['title'] 
                    js_dict['title_link'] = json_data['items'][i]['link']
                    js_dict['text'] = "(" + str(json_data['items'][i]['answer_count']) +' responses'+')' 
                    date = json_data['items'][i]['creation_date']
                    js_dict['footer'] = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')[:10]
                    js_dict["color"] = "#36a64f"
                    js_attachments.append(js_dict.copy())
                    i +=1
                    
                response['attachments'] = js_attachments
                response['text'] = 'Hello, I find these on the Stake Overflow.'
            
            else:
                #pick the tags
                command_tag = re.findall('\[(.*?)\]', text2)
                #delete the blacket
                command1 = text2.replace('[', '')
                command1 = command1.replace(']', '')
                
                #create json link of stack change
                text2 = command1.replace(' ', '%20')
                url1 = 'https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=activity'
                url3 = '&site=stackoverflow'
                url2 = '&q='+text2
                url_new = url1+url2+url3

                #read json file, which is a list contain dict
                json_data = requests.get(url_new).json()
                j=0
                filter_dict = {}
                filter_attachments = []
                while j < len(json_data['items']):
                    if set(command_tag).issubset(set(json_data['items'][j]['tags'])) or command_tag[0] in (json_data['items'][j]['tags']):
                        filter_dict['title'] = json_data['items'][j]['title'] 
                        filter_dict['title_link'] = json_data['items'][j]['link']
                        filter_dict['text'] = "(" + str(json_data['items'][j]['answer_count']) +' responses'+')' 
                        date = json_data['items'][j]['creation_date']
                        filter_dict['footer'] = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')[:10]
                        filter_dict["color"] = "#36a64f"
                        filter_attachments.append(filter_dict.copy())             
                    j+=1
                        
                response['attachments'] = filter_attachments[:5]
                response['text'] = 'Hello, I find these on the Stake Overflow.'
            
        elif text.startswith(weather_command):
            #get the address from the command
            command_task4 = text.split(':')[1]
            command_address = command_task4[1:]

            #create a link of the google map api
            api_part1 = 'https://maps.googleapis.com/maps/api/geocode/json?address='
            google_api_key = '&key='+'AIzaSyCDL_WTi3Xt_HT5d6rxLjZx_1SnFEENeEU'
            command_address_api_formate = command_address.replace(' ', '+')
            url_google_map = api_part1+command_address_api_formate+google_api_key

            #laod the data
            json_data_google_map = requests.get(url_google_map).json()
            #latitute and longtitue of location
            lat_lng = json_data_google_map['results'][0]['geometry']['location']

            location_info = str(lat_lng['lat']) +","+ str(lat_lng['lng'])
            
            #api callls by geographic coordinates
            weather_api_part1 = 'https://api.darksky.net/forecast/13f4fa058a82e3219b09d78c4e232753/'
            api_exclude = '?exclude=flags'
            url_weather_api = weather_api_part1+ location_info +api_exclude
            json_data_weahter_map = requests.get(url_weather_api).json()

            #load the current data from weahter api

            description = "Description: "+ str(json_data_weahter_map['currently']['icon'])
            current_temp = "Current Temperature: "+ str(json_data_weahter_map['currently']['apparentTemperature'])+u"\u00b0"+"F"
            max_temp = "Max Temp: "+str(json_data_weahter_map['daily']['data'][0]['temperatureMax'])+u"\u00b0"+"F"
            min_temp = "Min Temp"+ str(json_data_weahter_map['daily']['data'][0]['temperatureMin'])+u"\u00b0"+"F"
            wind_speed =  "Wind Speed: "+ str(json_data_weahter_map['currently']['windSpeed'])+' m/s'
            humidity = "Humidity: " + str(json_data_weahter_map['currently']['humidity']) + "%"

            time2 = json_data_weahter_map['currently']['time']
            current_time ="Current Time: "+ str(datetime.datetime.fromtimestamp(time2).strftime('%Y-%m-%d %H:%M:%S'))

            #max_min = " ("+ "Max Temp: "+ max_temp+ ", Min Temp: "+ min_temp+")"
            detail = description+ "\n"+current_temp+"\n"+ max_temp +"\n"+min_temp +"\n"+ wind_speed +"\n"+ humidity + "\n" + current_time

            #create slack field forma
            field_list = []

            dict_current = {}
            dict_current['title'] = 'Current Weather'
            dict_current['value'] = detail
            dict_current['short'] = True
            field_list.append(dict_current)

            #weather forecast
            weahter_forecast = json_data_weahter_map['daily']['data'][1]
            forecast_summary = "Forecast:  "+ str(weahter_forecast['summary'])
            max_temp_forecast = "Max Temp:  "+ str(weahter_forecast['temperatureMax']) +u"\u00b0F"
            min_temp_forecast = "Min Temp:  "+ str(weahter_forecast['temperatureMin'])+u"\u00b0F"

            detail_forecast = forecast_summary+ "\n"+max_temp_forecast +"\n"+ min_temp_forecast


            dict_forecast = {}
            dict_forecast['title'] = 'Weather Forecast'
            dict_forecast['value'] = detail_forecast
            dict_forecast['short'] = True

            #insert the image
            image_url = 'https://maps.googleapis.com/maps/api/staticmap?center='
            image_key = '&zoom=14&size=300x300&maptype=roadmap&format=jpg&key=AIzaSyBv-aAx5aghdCSgIQpVsl0P32wBaykXtt4'
            image_url_full = image_url +location_info+ image_key

            field_list.append(dict_forecast)
            weather_dict = {}
            weather_dict['fields'] = field_list
            weather_dict['title'] = 'Weather and Forecast'
            weather_dict['text'] = "-"*90
            weather_dict['image_url'] = image_url_full
            weather_dict["color"] = "#36a64f"
            attach_list = []
            attach_list.append(weather_dict)

            response['attachments'] = attach_list

                         
            
        r = requests.post(slack_inbound_url, json=response)
   

    print inbound_message
    print request.form

    return Response(), 200


@application.route('/', methods=['GET'])
def test():
    return Response('It works!')


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=41953)


