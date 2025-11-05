import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, switchMap, map } from 'rxjs';

interface RasaResponse {
  sender: string;
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

  sendMessage(message: string, senderId: string = 'utente1'): Observable<RasaResponse[]> {
    // 1️⃣ Prima chiamata: chiediamo il parse (intent + confidence)
    return this.http.post<any>(this.RASA_PARSE_URL, { text: message }).pipe(
      //switchMap() serve per “concatenare” la seconda richiesta solo dopo che la prima ha restituito il suo risultato.
      switchMap(parseResult => {
        const intent = parseResult.intent?.name || 'unknown';
        const confidence = parseResult.intent?.confidence ?? 0;

        // 2️⃣ Seconda chiamata: inviamo il messaggio al webhook per la risposta
        return this.http.post<RasaResponse[]>(this.RASA_WEBHOOK_URL, {
          sender: senderId,
          message: message
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
