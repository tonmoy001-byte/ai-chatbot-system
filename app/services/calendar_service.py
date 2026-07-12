from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List
import os
import logging

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

# OAuth 2.0 configuration
CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRETS", "credentials.json")
REDIRECT_URI = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://localhost:8000/calendar/callback")


class CalendarService:
    def __init__(self, credentials: Optional[Credentials] = None):
        self.service = None
        self.credentials = credentials
        if credentials:
            self._build_service()
    
    def _build_service(self):
        """Build Google Calendar service."""
        try:
            self.service = build('calendar', 'v3', credentials=self.credentials)
        except Exception as e:
            logger.error(f"Failed to build calendar service: {str(e)}")
    
    @staticmethod
    def get_authorization_url(state: str) -> str:
        """Get OAuth authorization URL."""
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state
        )
        flow.redirect_uri = REDIRECT_URI
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url
    
    @staticmethod
    def exchange_code(code: str) -> Optional[Credentials]:
        """Exchange authorization code for credentials."""
        try:
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES
            )
            flow.redirect_uri = REDIRECT_URI
            
            flow.fetch_token(code=code)
            
            return flow.credentials
        except Exception as e:
            logger.error(f"Failed to exchange code: {str(e)}")
            return None
    
    @staticmethod
    def refresh_credentials(credentials: Credentials) -> Optional[Credentials]:
        """Refresh expired credentials."""
        try:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                return credentials
            return credentials
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {str(e)}")
            return None
    
    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        duration_minutes: int = 30,
        description: str = "",
        attendee_email: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a calendar event."""
        if not self.service:
            logger.error("Calendar service not initialized")
            return None
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if location:
            event['location'] = location
        
        if attendee_email:
            event['attendees'] = [{'email': attendee_email}]
        
        try:
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            logger.info(f"Created calendar event: {created_event.get('id')}")
            return created_event
        except Exception as e:
            logger.error(f"Failed to create event: {str(e)}")
            return None
    
    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing calendar event."""
        if not self.service:
            return None
        
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
                if duration_minutes:
                    end_time = start_time + timedelta(minutes=duration_minutes)
                    event['end']['dateTime'] = end_time.isoformat()
            
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Updated calendar event: {event_id}")
            return updated_event
        except Exception as e:
            logger.error(f"Failed to update event: {str(e)}")
            return None
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event."""
        if not self.service:
            return False
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Deleted calendar event: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete event: {str(e)}")
            return False
    
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a calendar event."""
        if not self.service:
            return None
        
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return event
        except Exception as e:
            logger.error(f"Failed to get event: {str(e)}")
            return None
    
    async def list_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """List calendar events."""
        if not self.service:
            return []
        
        try:
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_datetime.isoformat() + 'Z',
                timeMax=end_datetime.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to list events: {str(e)}")
            return []
    
    async def get_available_slots(
        self,
        target_date: date,
        duration_minutes: int = 30,
        start_hour: int = 9,
        end_hour: int = 17
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a given date."""
        if not self.service:
            return []
        
        try:
            start_of_day = datetime.combine(target_date, datetime.min.time().replace(hour=start_hour))
            end_of_day = datetime.combine(target_date, datetime.min.time().replace(hour=end_hour))
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Find available slots
            available_slots = []
            current_time = start_of_day
            
            for event in events:
                event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                
                # Convert to naive datetime for comparison
                event_start_naive = event_start.replace(tzinfo=None)
                
                if current_time + timedelta(minutes=duration_minutes) <= event_start_naive:
                    available_slots.append({
                        'start_time': current_time.isoformat(),
                        'end_time': (current_time + timedelta(minutes=duration_minutes)).isoformat(),
                        'duration_minutes': duration_minutes
                    })
                
                event_end_str = event['end'].get('dateTime', event['end'].get('date'))
                event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
                event_end_naive = event_end.replace(tzinfo=None)
                
                current_time = max(current_time, event_end_naive)
            
            # Check remaining time before end of day
            if current_time + timedelta(minutes=duration_minutes) <= end_of_day:
                available_slots.append({
                    'start_time': current_time.isoformat(),
                    'end_time': (current_time + timedelta(minutes=duration_minutes)).isoformat(),
                    'duration_minutes': duration_minutes
                })
            
            return available_slots
        except Exception as e:
            logger.error(f"Failed to get available slots: {str(e)}")
            return []
    
    async def add_reminder(
        self,
        event_id: str,
        minutes_before: int = 30,
        method: str = 'popup'
    ) -> bool:
        """Add reminder to event."""
        if not self.service:
            return False
        
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': method, 'minutes': minutes_before},
                ],
            }
            
            self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Added reminder to event {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add reminder: {str(e)}")
            return False
    
    async def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming events for the next N days."""
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        return await self.list_events(start_date, end_date)
