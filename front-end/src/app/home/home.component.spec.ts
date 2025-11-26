import { ComponentFixture, TestBed, fakeAsync, tick, waitForAsync } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService } from '../services/auth.service';
import { of } from 'rxjs';
import { ChatService } from '../services/chat.service';

import { Home } from './home.component';

describe('HomeComponent', () => {
  let component: Home;
  let fixture: ComponentFixture<Home>;

  beforeEach(async () => {
    const authStub: Partial<AuthService> = {
      getCurrentUser: () => of({ email: 'john.doe@example.com', firstName: 'John', lastName: 'Doe', role: 'user' } as any),
      isLoggedIn: () => true,
      login: (_e: string, _p: string) => of(true),
      logout: () => {}
    };

    const chatStub: Partial<ChatService> = {
      sendMessage: (_text: string, _email: string) => of([])
    };

    await TestBed.configureTestingModule({
      imports: [Home],
      providers: [
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authStub },
        { provide: ChatService, useValue: chatStub }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(Home);
    component = fixture.componentInstance;

    // provide a mock scrollContainer ElementRef before detectChanges
    (component as any).scrollContainer = {
      nativeElement: { scroll: jasmine.createSpy('scroll'), scrollHeight: 500 }
    };

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
  
    it('loadUser should populate user fields and initials', () => {
      component.loadUser();
      expect(component.email).toBe('john.doe@example.com');
      expect(component.name).toBe('John');
      expect(component.surname).toBe('Doe');
      expect(component.initials).toBe('JD');
      expect(component.role).toBe('user');
    });
  
    it('getSessions should fetch and set sessions', waitForAsync(async () => {
      spyOn(window as any, 'fetch').and.callFake(() =>
        Promise.resolve({ status: 200, json: () => Promise.resolve([{ id: 's1', title: 'Session 1' }]) })
      );
  
      component.getSessions();
      await fixture.whenStable();
  
      expect((window as any).fetch).toHaveBeenCalled();
      expect(component.sessions.length).toBeGreaterThan(0);
      expect(component.sessions[0].id).toBe('s1');
    }));
  
    it('loadChatHistory should load messages and set state', waitForAsync(async () => {
      const fakeData = {
        messages: [
          { sender: 'bot', content: { text: 'hello', buttons: [] }, timestamp: new Date().toISOString() }
        ],
        active: true
      };
  
      spyOn(window as any, 'fetch').and.callFake(() =>
        Promise.resolve({ json: () => Promise.resolve(fakeData) })
      );
  
      await component.loadChatHistory('s1');
      await fixture.whenStable();
  
      expect(component.messages.length).toBe(1);
      expect(component.current_session).toBe('s1');
      expect(component.conversationEnded).toBeFalse();
      expect(component.shouldScroll).toBeTrue();
    }));
  
    it('saveMessageToBackend should update current_session when session_id returned', waitForAsync(async () => {
      component.current_session = 'old';
      spyOn(window as any, 'fetch').and.callFake(() =>
        Promise.resolve({ json: () => Promise.resolve({ session_id: 'new-session' }) })
      );
  
      await component.saveMessageToBackend(component.createMessage('hi', 'user'));
      await fixture.whenStable();
  
      expect(component.current_session).toBe('new-session');
    }));
  
    it('handleBotMessage should set waiting_answer, reservationInProgress and call startLongWaiting when special text', () => {
      spyOn(component, 'startLongWaiting');
  
      const msg = component.createMessage('Perfetto, cerco subito nei documenti', 'bot');
      msg.custom = {};
      msg.buttons = [];
  
      component.handleBotMessage(msg);
  
      expect(component.waiting_answer).toBeFalse();
      expect(component.startLongWaiting).toHaveBeenCalled();
    });
  
    it('handleUserMessage should push message and start long waiting', () => {
      const before = component.messages.length;
      component.handleUserMessage(component.createMessage('ciao', 'user'));
      expect(component.messages.length).toBe(before + 1);
      expect(component.startTime).toBeGreaterThan(0);
    });
  
    it('sendMessageToChat should call ChatService and handle responses', waitForAsync(async () => {
      const chat = TestBed.inject(ChatService) as any;
      spyOn(chat, 'sendMessage').and.returnValue(of([{ text: 'bot reply', buttons: [], custom: {}, image: '' }]));
      spyOn(component, 'handleMessage');
  
      await component.sendMessageToChat('hello');
      await fixture.whenStable();
  
      expect(chat.sendMessage).toHaveBeenCalled();
      expect(component.handleMessage).toHaveBeenCalled();
    }));
  
    it('startLongWaiting and resetLongWait should set and clear timers', fakeAsync(() => {
      component.startLongWaiting(10, 5);
      tick(11);
      expect(component.long_waiting).toBeTrue();
      const beforeText = component.long_waiting_text;
      tick(5);
      expect(component.long_waiting_text).not.toBe(beforeText);
      component.resetLongWait();
      expect(component.long_waiting).toBeFalse();
    }));
  
    it('getInitialsFromEmail returns initials or empty string', () => {
      expect(component.getInitialsFromEmail('marco.rossi@example.com')).toBe('MR');
      expect(component.getInitialsFromEmail(null)).toBe('');
    });
});
