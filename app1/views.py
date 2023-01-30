from django.shortcuts import render
import json
# Create your views here.
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class GoogleCalendarInitView(View):

    def get(self, request, *args, **kwargs):
        
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar.events']
        )

        flow.redirect_uri = 'http://localhost:8000/rest/v1/calendar/redirect'

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
        )

        request.session['state'] = state
        return redirect(authorization_url)


class GoogleCalendarRedirectView(View):

    def get(self, request, *args, **kwargs):
        
        state = request.GET.get('state')

        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar.events'],
            state=state
        )
        flow.redirect_uri = 'http://localhost:8000/rest/v1/calendar/redirect'

        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials

        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        service = build('calendar', 'v3', credentials=credentials)
        timeMin = '2022-01-01T00:00:00-07:00'

        events_result = service.events().list(calendarId='primary', timeMin=timeMin,
                                              maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        results = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            results.append([start, event['summary']])
        results = json.dumps(results)
        return JsonResponse({
                             'data': results
                             })

