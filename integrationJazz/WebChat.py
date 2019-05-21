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

'''
The webhook endpoint to verify the visitor's identity

'''
class VerificationHandler(APIView):
    def get(self, request, format=None):
        return Response("The webhook is up and running", status=200)

