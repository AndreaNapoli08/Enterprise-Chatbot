import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

interface RasaResponse {
  sender: string;
  text?: string;
  image?: string;
  buttons?: { title: string, payload: string }[];
  attachment?: { type: string; url: string }; 
}

@Injectable({
  providedIn: 'root'
})

export class ChatService {
  private RASA_URL = 'http://localhost:5005/webhooks/rest/webhook';

  constructor(private http: HttpClient) {}

  sendMessage(message: string, senderId: string = 'utente1'): Observable<RasaResponse[]> {
    return this.http.post<RasaResponse[]>(this.RASA_URL, {
      sender: senderId, 
      message: message
    });
  }
}
