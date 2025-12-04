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

  private GIST_RASA_URL =
    "https://gist.githubusercontent.com/AndreaNapoli08/0b153d525eb3a45d37cafd65b32bca8c/raw/rasa_base_url.txt";

  constructor(private http: HttpClient) {}

  // 🔧 Recupera il base URL di Rasa dal Gist
  private loadRasaBaseUrl(): Observable<string | null> {
    return this.http.get(this.GIST_RASA_URL, { responseType: 'text' }).pipe(
      map(url => {
        const clean = url.trim();
        return clean.startsWith("http") ? clean : null;
      })
    );
  }

  sendMessage(message: string, email: string): Observable<RasaResponse[]> {
    return this.loadRasaBaseUrl().pipe(
      switchMap(baseUrl => {
        if (!baseUrl) {
          throw new Error("RASA base URL non disponibile.");
        }
        const parseUrl = `${baseUrl}/model/parse`;
        const webhookUrl = `${baseUrl}/webhooks/rest/webhook`;

        // 1️⃣ Chiede intent + confidence
        return this.http.post<any>(parseUrl, { text: message }).pipe(
          switchMap(parseResult => {
            const intent = parseResult.intent?.name || 'unknown';
            const confidence = parseResult.intent?.confidence ?? 0;

            // 2️⃣ Manda il messaggio
            return this.http.post<RasaResponse[]>(webhookUrl, {
              message: message,
              metadata: { email }
            }).pipe(
              // 3️⃣ Aggiunge intent e confidence ad ogni risposta bot
              map(responses =>
                responses.map(resp => ({
                  ...resp,
                  intent,
                  confidence
                }))
              )
            );
          })
        );
      })
    );
  }

}
