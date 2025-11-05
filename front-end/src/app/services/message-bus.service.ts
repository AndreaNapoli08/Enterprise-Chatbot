import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Message } from '../interfaces/message';

@Injectable({ providedIn: 'root' })
export class MessageBusService {
  private rasaResponseSource = new BehaviorSubject<Message | null>(null);
  rasaResponse$ = this.rasaResponseSource.asObservable();

  sendBotMessage(message: Message) {
    this.rasaResponseSource.next(message);
  }
}
