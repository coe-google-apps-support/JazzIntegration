from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
import requests
import json
from requests.auth import HTTPBasicAuth
import os
from decouple import config
import smtplib
from django.http import HttpResponse
'''
The webhook endpoint to verify the visitor's identity

Input:

{
  "event_type": "chat_started",
  "event_unique_id": "c94b73d793dc6bbe1b9cd5239c5f1e8d",
  "token": "ee867448f733d3eb2558f9641f5360e3",
  "license_id": "9281545",
  "lc_version": "2",
  ...
  
  "visitor": {
    "id": "S1556912895.c3729eb612",
    "name": "Zhipeng Chang",
    "email": "zhipeng.chang@edmonton.ca",
    "country": "Canada",
    "city": "Edmonton",
    "language": "en",
    "page_current": "https://secure.livechatinc.com/licence/9281545/v2/open_chat.cgi?groups=4&name=Zhipeng%20Chang&email=zhipeng.chang@edmonton.ca&id=107686237770712793227&token=OU5s_PzreqXtK8CoKqBiOaFnGheMTzXSibd4DSlCfjJ3KYSI-Rr3p0D9VzwPA",
    "timezone": "America/Edmonton"
  },
  "pre_chat_survey": []
}

Output:

if user verified - True
if user not verified - False and will trigger a email

'''
def MainPage(request):
    return HttpResponse("The webhook is up and running", status=200)

class VerificationHandler(APIView):

    def post(self, request, format=None):
        visitor_name = request.data["visitor"]["name"]
        visitor_email = request.data["visitor"]["email"]
        visitor_id = request.data["visitor"]["id"]
        webhook_token = request.data["token"]
        licence_number = request.data["license_id"]
        google_oauth2_url = "https://www.googleapis.com/oauth2/v3/userinfo?access_token="
        google_oauth2_idToken_url = "https://oauth2.googleapis.com/tokeninfo?id_token="
        if "custom_variables" in request.data["visitor"]:
            using_ID_Token = next((item for item in request.data["visitor"]["custom_variables"] if item["key"] == "token"), False)
        else:
            using_ID_Token = False
        try:
            if using_ID_Token != False:
                visitor_auth_token = using_ID_Token["value"]
            elif "token=" in request.data["visitor"]["page_current"]:
                visitor_auth_token = request.data["visitor"]["page_current"].split("token=")[1]
                
        except:
            livechat_visitor_details_url = "https://api.livechatinc.com/v2/visitors/%s/details"%visitor_id
            payload = {'license_id':licence_number,'token':webhook_token, 'id':'Status', 'fields[0][name]':'Verified COE User', 'fields[0][value]':'❌'}
            updated_details = requests.post(livechat_visitor_details_url, auth=HTTPBasicAuth(config('livechat_email'),config('livechat_api_key')), data=payload)
            return Response("User not verified", status=200)
    
        if using_ID_Token != False:
            response = requests.get(google_oauth2_idToken_url+visitor_auth_token)
        elif "token=" in request.data["visitor"]["page_current"]:
            response = requests.get(google_oauth2_url+visitor_auth_token)
        else:
            livechat_visitor_details_url = "https://api.livechatinc.com/v2/visitors/%s/details"%visitor_id
            payload = {'license_id':licence_number,'token':webhook_token, 'id':'Status', 'fields[0][name]':'Verified COE User', 'fields[0][value]':'❌'}
            updated_details = requests.post(livechat_visitor_details_url, auth=HTTPBasicAuth(config('livechat_email'),config('livechat_api_key')), data=payload)
            return Response("User not verified", status=200)
            
        if response.status_code==200:
            responseJSON = json.loads(response.content.decode('utf8').replace("'", '"'))
            oauth2_email = responseJSON['email']
            try:
                oauth2_domain = responseJSON['hd']
                if oauth2_domain == "edmonton.ca":
                        isCOEUser = True
                else:
                    isCOEUser = False
            except:
                isCOEUser = False
                
            livechat_visitor_details_url = "https://api.livechatinc.com/v2/visitors/%s/details"%visitor_id
            if oauth2_email == visitor_email and isCOEUser:
                payload = {'license_id':licence_number,'token':webhook_token, 'id':'Status', 'fields[0][name]':'Name', 'fields[0][value]':request.data["visitor"]["name"], 'fields[1][name]':'Email', 'fields[1][value]':oauth2_email, 'fields[2][name]':'Verified COE User', 'fields[2][value]':'✅'}
                updated_details = requests.post(livechat_visitor_details_url, auth=HTTPBasicAuth(config('livechat_email'),config('livechat_api_key')), data=payload)
                return Response("User verified", status=200)
            else:
                payload = {'license_id':licence_number,'token':webhook_token, 'id':'Status', 'fields[0][name]':'Verified COE User', 'fields[0][value]':'❌'}
                updated_details = requests.post(livechat_visitor_details_url, auth=HTTPBasicAuth(config('livechat_email'),config('livechat_api_key')), data=payload)
                #sendWarningEmail(visitor_email, visitor_name)
                return Response("User not verified", status=200)
        else:
            livechat_visitor_details_url = "https://api.livechatinc.com/v2/visitors/%s/details"%visitor_id
            payload = {'license_id':licence_number,'token':webhook_token, 'id':'Status', 'fields[0][name]':'Verified COE User', 'fields[0][value]':'❌'}
            updated_details = requests.post(livechat_visitor_details_url, auth=HTTPBasicAuth(config('livechat_email'),config('livechat_api_key')), data=payload)
            #sendWarningEmail(visitor_email, visitor_name)
            return Response("User not verified", status=200)


def sendWarningEmail(recipient, recipientName):
    Text = "Hi %s,\nThank you for using Jazz.\nBest,\nJazz Team"%recipientName
    Subject = "Thank you for using Jazz!"
    warningMessage = 'Subject: {}\n\n{}'.format(Subject, Text)
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(config('jazz_email'), config('jazz_email_password'))
        server.sendmail(config('jazz_email'), recipient, warningMessage)
        server.close()
    except:
        pass