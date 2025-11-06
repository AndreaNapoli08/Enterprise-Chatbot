import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, switchMap, map } from 'rxjs';
import { User } from '../interfaces/user';

interface RasaResponse {
  text?: string;
  image?: string;
  custom?: { type?: string;  text?: string;  [key: string]: any; };
  buttons?: { title: string; payload: string }[];
  attachment?: { type: string; url: string; name: string, size: number, pages: number };
  intent?: string;
  confidence?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private RASA_WEBHOOK_URL = 'http://localhost:5005/webhooks/rest/webhook';
  private RASA_PARSE_URL = 'http://localhost:5005/model/parse'; //senza questo non possiamo sapere intent e confidence

  constructor(private http: HttpClient) {}

  sendMessage(message: string, email: string): Observable<RasaResponse[]> {
    // 1️⃣ Prima chiamata: chiediamo il parse (intent + confidence)
    return this.http.post<any>(this.RASA_PARSE_URL, { text: message }).pipe(
      switchMap(parseResult => {
        const intent = parseResult.intent?.name || 'unknown';
        const confidence = parseResult.intent?.confidence ?? 0;

        // 2️⃣ Seconda chiamata: inviamo il messaggio al webhook con email
        return this.http.post<RasaResponse[]>(this.RASA_WEBHOOK_URL, {
          message: message,
          metadata: { email }   // <-- qui passo l'email
        }).pipe(
          // 3️⃣ Aggiungiamo intent e confidence a ogni messaggio bot ricevuto
          map(responses => {
            return responses.map(resp => ({
              ...resp,
              intent,
              confidence
            }));
          })
        );
      })
    );
  }

}
